# scripts/view_memory.py
import sqlite3
import json
import os

# 取得 chat_memory.db 在上一層
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../chat_memory.db")

def view_all_histories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT session_id, history FROM memory")
    rows = cursor.fetchall()

    for session_id, history_json in rows:
        print(f"🧾 Session: {session_id}")
        history = json.loads(history_json)
        for i, turn in enumerate(history):
            print(f"  {i+1}. 🗣️ {turn['user']}")
            print(f"     🤖 {turn['bot']}")
        print("-" * 40)

    conn.close()

def view_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM summary")
    rows = cursor.fetchall()

    print(rows)

    conn.close()

def view_ai_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ai_summary")
    rows = cursor.fetchall()

    print(rows)

    conn.close()

def view_answer():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM daily_answers")
    rows = cursor.fetchall()

    print(rows)

    conn.close()

if __name__ == "__main__":
    print(f"🔍 使用資料庫路徑：{os.path.abspath(DB_PATH)}")
    view_all_histories()
    view_summary()
    view_ai_summary()
    view_answer()