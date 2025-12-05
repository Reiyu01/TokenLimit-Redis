import sqlite3
import redis
import time
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_db_connection():
    return sqlite3.connect('token_manager.db')

class ChatRequest(BaseModel):
    messages: list



#背景執行任務：同步餘額到資料庫
def sync_balance_to_db(user_id: int, cost: int):
    # 模擬資料庫寫入很慢 (故意停 1 秒)
    time.sleep(1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 寫入流水帳 (Log)
    cursor.execute("INSERT INTO request_logs (user_id, tokens_used) VALUES (?, ?)", (user_id, cost))
    
    # 2. 更新使用者的餘額 (確保資料庫跟 Redis 最終一致)
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (cost, user_id))
    
    conn.commit()
    conn.close()
    print(f"💾 [背景任務] 已將 User {user_id} 的消費 ({cost} tokens) 寫入資料庫")



@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,  # FastAPI 的非同步神器
    x_api_key: str = Header(...)        # 從 Header 抓 API Key
):
    # 假設這一次請求固定消耗 50 tokens
    COST = 50 

    # === 第一階段：找人 (Cache-Aside) ===
    # 先問 Redis：你知道這個 API Key 是誰嗎？
    user_id = r.get(f"apikey:{x_api_key}")

    # 如果 Redis 搖頭說不知道 (None)，我們就要辛苦一點去資料庫查
    if not user_id:
        print("⚠️ Redis 沒資料 (Cache Miss)，正在去資料庫撈...")
        conn = get_db_connection()
        # 查這個 Key 對應的 ID 和 餘額
        row = conn.execute("SELECT id, balance FROM users WHERE api_key = ?", (x_api_key,)).fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=401, detail="無效的 API Key")
        
        user_id = row[0]
        db_balance = row[1]

        # 【關鍵步驟】把查到的資料「抄寫」到 Redis，下次就不用查資料庫了
        # 設定 3600 秒 (1小時) 後過期，避免 Redis 塞滿垃圾資料
        r.set(f"apikey:{x_api_key}", user_id, ex=3600)
        r.set(f"user:{user_id}:balance", db_balance, ex=3600)
    
    # 確保 user_id 是整數
    user_id = int(user_id)

    # === 第二階段：檢查餘額 ===
    # 從 Redis 拿餘額 (這時候一定有資料了)
    current_balance = int(r.get(f"user:{user_id}:balance"))

    if current_balance < COST:
        raise HTTPException(status_code=403, detail="餘額不足，請充值")

    # === 第三階段：極速扣款 (Redis Atomic Operation) ===
    # 直接在 Redis 記憶體中扣款，速度極快，不用等硬碟
    new_balance = r.decrby(f"user:{user_id}:balance", COST)
    
    print(f"⚡ Redis 扣款成功！剩餘: {new_balance}")

    # === 第四階段：觸發背景同步 ===
    # 告訴 FastAPI：「等一下回覆完之後，幫我跑 sync_balance_to_db」
    background_tasks.add_task(sync_balance_to_db, user_id, COST)

    # === 第五階段：回傳結果 ===
    return {
        "reply": f"AI 收到你的訊息：{request.messages[0]}",
        "remaining_balance": new_balance
    }
