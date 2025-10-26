# services/memory_store.py
import aiosqlite
import json

DB_PATH = "chat_memory.db"

# 初始化資料表
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                user_id TEXT,
                session_id TEXT,
                history TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, session_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                user_id TEXT,
                session_id TEXT,
                summary_text TEXT,
                PRIMARY KEY (user_id, session_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_summary (
                user_id TEXT,
                session_id TEXT,
                ai_summary_text TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, session_id)
            )
        """)
        # postcards
        await db.execute("""
            CREATE TABLE IF NOT EXISTS postcard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                image_path TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 題庫表：存放所有題目
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                day_number INTEGER UNIQUE
            )
        """)

        # 回答表：紀錄使用者對題目的回答
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                question_id INTEGER,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, question_id)
            )
        """)

        await db.execute("""
           CREATE TABLE IF NOT EXISTS safety_score (
                user_id TEXT,
                session_id TEXT,
                score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, session_id)
                )
           """)

        await db.commit()


#問題、日期、是否回答

# 讀取聊天歷史
async def get_history(user_id: str, session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT history FROM memory WHERE user_id = ? AND session_id = ?",
            (user_id, session_id),) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return []

# 讀取聊天歷史
async def get_ai_history(user_id: str, session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT history, model FROM memory WHERE user_id = ? AND session_id = ?", (user_id, session_id),)  as cursor:
            row = await cursor.fetchone()
            if row:
                history, model = row
                if history:
                    history = json.loads(history)
                    ai_history = [turn["bot"] for turn in history if "bot" in turn]
                    return {"history": ai_history, "model": model}
            return None

# 儲存聊天歷史
async def save_history(user_id: str, session_id: str, history: list, model: str):
    history_json = json.dumps(history)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "REPLACE INTO memory (user_id, session_id, history, model, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, session_id, history_json, model)
        )
        await db.commit()


#讀取聊天摘要
async def get_summary(user_id: str, session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT summary_text FROM summary WHERE user_id = ? AND session_id = ?",  (user_id, session_id),)  as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

#儲存聊天摘要
async def save_summary(user_id: str, session_id: str, summary: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO summary (user_id, session_id, summary_text)
            VALUES (?, ?, ?)
        """, (user_id, session_id, summary))
        await db.commit()

# 儲存總模型回覆摘要
async def save_ai_summary(user_id: str, session_id: str, summary: str, model: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO ai_summary (user_id, session_id, ai_summary_text, model, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, session_id, summary, model)
        )
        await db.commit()


# 儲存明信片（圖片路徑 + 訊息）
async def save_postcard(session_id: str, image_path: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO postcard (session_id, image_path, message)
            VALUES (?, ?, ?)
        """, (session_id, image_path, message))
        await db.commit()

# 讀取某個 session 的明信片
async def get_postcards(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, image_path, message, created_at
            FROM postcard
            WHERE session_id = ?
            ORDER BY created_at DESC
        """, (session_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "image_path": r[1], "message": r[2], "created_at": r[3]}
                for r in rows
            ]

# 取得今天的題目（根據進度）
async def get_today_question(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # 先查已回答幾題
        async with db.execute(
            "SELECT COUNT(*) FROM daily_answers WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            answered_count = row[0]

        # 下一題 = 已回答題數 + 1
        next_day_number = answered_count + 1
        async with db.execute(
            "SELECT id, question FROM daily_questions WHERE day_number = ?",
            (next_day_number,),
        ) as cursor:
            row = await cursor.fetchone()
            return {"id": row[0], "question": row[1]} if row else None


# 儲存使用者的回答
async def save_answer(user_id: str, question_id: int, answer: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO daily_answers (user_id, question_id, answer)
            VALUES (?, ?, ?)
        """, (user_id, question_id, answer))
        await db.commit()


# 查詢所有回答（用於日曆顯示）
async def get_all_answers(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT q.day_number, q.question, a.answer, a.created_at
            FROM daily_answers a
            JOIN daily_questions q ON a.question_id = q.id
            WHERE a.user_id = ?
            ORDER BY q.day_number ASC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {"day": r[0], "question": r[1], "answer": r[2], "created_at": r[3]}
                for r in rows
            ]

# 讀取分數
async def get_safety_score(user_id: str, session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT score FROM safety_score WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                score = row[0]   # 因為 SELECT 只有一欄 → 直接取 row[0]
                return score
            return 0

# 儲存聊天歷史
async def save_safety_score(user_id: str, session_id: str, score: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "REPLACE INTO safety_score (user_id, session_id, score, created_at) VALUES ( ?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, session_id, score)
        )
        await db.commit()