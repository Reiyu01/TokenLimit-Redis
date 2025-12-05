import requests
import time

url = "http://127.0.0.1:8000/chat"
headers = {
    "x-api-key": "test_api_key_123"  # 這是我們資料庫裡那個用戶的 Key
}
data = {"message": ["Hello Redis!"]}

print("🚀 發送請求...")
start = time.time()

# 發送請求
response = requests.post(url, json=data, headers=headers)
end = time.time()

print(f"回覆狀態: {response.status_code}")
print(f"回覆內容: {response.json()}")
print(f"耗時: {end - start:.4f} 秒")
