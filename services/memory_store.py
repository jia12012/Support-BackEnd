# services/memory_store.py
import aiosqlite
import json

DB_PATH = "chat_memory.db"

# 初始化資料表
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                session_id TEXT PRIMARY KEY,
                history TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                session_id TEXT PRIMARY KEY,
                summary_text TEXT
            )
        """)

        await db.commit()

# 讀取聊天歷史
async def get_history(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT history FROM memory WHERE session_id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return []

# 儲存聊天歷史
async def save_history(session_id: str, history: list):
    history_json = json.dumps(history)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "REPLACE INTO memory (session_id, history) VALUES (?, ?)",
            (session_id, history_json)
        )
        await db.commit()

#讀取聊天摘要
async def get_summary(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT summary_text FROM summary WHERE session_id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

#儲存聊天摘要
async def save_summary(session_id: str, summary: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE summary SET summary_text = ? WHERE session_id = ?",
            (summary, session_id)
        )
        await db.commit()