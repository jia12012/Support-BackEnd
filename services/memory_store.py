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
                history TEXT,
                model TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                session_id TEXT PRIMARY KEY,
                summary_text TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_summary (
                session_id TEXT PRIMARY KEY,
                ai_summary_text TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# 讀取聊天歷史
async def get_ai_history(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT history, model FROM memory WHERE session_id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                history, model = row
                if history:
                    history = json.loads(history)
                    ai_history = [turn["bot"] for turn in history if "bot" in turn]
                    return {"history": ai_history, "model": model}
            return None

# 儲存聊天歷史
async def save_history(session_id: str, history: list, model: str):
    history_json = json.dumps(history)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "REPLACE INTO memory (session_id, history, model) VALUES (?, ?, ?)",
            (session_id, history_json, model)
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
        await db.execute("""
            INSERT INTO summary (session_id, summary_text)
            VALUES (?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary_text = excluded.summary_text
        """, (session_id, summary))
        await db.commit()

# 儲存總模型回覆摘要
async def save_ai_summary(session_id: str, summary: str, model: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO ai_summary (session_id, ai_summary_text, model,created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (session_id, summary, model)
        )
        await db.commit()