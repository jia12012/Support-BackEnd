from fastapi import APIRouter
from pydantic import BaseModel
import services.memory_store as store

router = APIRouter(prefix="/daily", tags=["daily"])

# -------------------------
# 輸入資料模型
# -------------------------
class QuestionIn(BaseModel):
    question: str
    day_number: int

class AnswerIn(BaseModel):
    user_id: str
    question_id: int
    answer: str

# -------------------------
# API 1: 新增題目
# -------------------------
@router.post("/add_question")
async def add_question(q: QuestionIn):
    async with store.aiosqlite.connect(store.DB_PATH) as db:
        await db.execute(
            "INSERT INTO daily_questions (question, day_number) VALUES (?, ?)",
            (q.question, q.day_number)
        )
        await db.commit()
    return {"status": "success", "question": q.question, "day_number": q.day_number}

# -------------------------
# API 2: 取得今天的題目
# -------------------------
@router.get("/question/today/{user_id}")
async def get_today_question(user_id: str):
    return await store.get_today_question(user_id)

# -------------------------
# API 3: 儲存使用者回答
# -------------------------
@router.post("/answer")
async def save_answer(a: AnswerIn):
    await store.save_answer(a.user_id, a.question_id, a.answer)
    return {"status": "success", "user_id": a.user_id, "question_id": a.question_id, "answer": a.answer}

# -------------------------
# API 4: 查詢所有回答
# -------------------------
@router.get("/answers/{user_id}")
async def get_all_answers(user_id: str):
    return await store.get_all_answers(user_id)
