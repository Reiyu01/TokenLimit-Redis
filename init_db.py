import sqlite3
conn = sqlite3.connect('token_manager.db')
cursor = conn.cursor()

cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               api_key TEXT UNIQUE,
               balance INTEGER)''')

cursor.execute('''
               CREATE TABLE IF NOT EXISTS request_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  tokens_used INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  )
               ''')

cursor.execute('INSERT OR IGNORE INTO users (id,api_key,balance) VALUES (1, "test_api_key_123", 10000)')
conn.commit()
conn.close()
print("資料庫以初始化，用戶sk-test餘額為10000")