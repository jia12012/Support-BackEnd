# routers/sessions.py
from fastapi import APIRouter
import aiosqlite
from pydantic import BaseModel
from services.summarize import summarize_ai_output

DB_PATH = "chat_memory.db"
router = APIRouter()

@router.get("/next_id/{model}")
async def get_next_session_id(model: str):
    """
    依 memory 表中該 model 的「不同 session_id 數量」計數，
    回傳下一個可用的 session_id，例如 Sunny5 -> 下一個是 Sunny6
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # 以「不同 session_id」計數，較不會被同一會話多次寫入影響
        query = "SELECT COUNT(DISTINCT session_id) FROM memory WHERE model = ?"
        async with db.execute(query, (model,)) as cur:
            row = await cur.fetchone()
            count = row[0] if row and row[0] is not None else 0

    next_index = count + 1
    session_id = f"{model}{next_index}"
    return {"model": model, "next_index": next_index, "session_id": session_id}



class SummarizeReq(BaseModel):
    session_id: str
    # 如需也傳 model_name，可加：model_name: str

@router.post("/summarize")
async def summarize_endpoint(body: SummarizeReq):
    # 呼叫你的邏輯
    result = await summarize_ai_output(body.session_id)
    return {"ok": True, "result": result}
