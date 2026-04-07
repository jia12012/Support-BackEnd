# routers/chat.py
from fastapi import APIRouter, Body
from services.llm_service import chat_with_model
from services.safety import analyze_risk
from services.memory_store import save_history
import aiosqlite
import asyncio
DB_PATH = "chat_memory.db"

router = APIRouter()

@router.post("/")
async def chat_endpoint(
    text: str = Body(..., embed=True),
    user_id: str = Body(..., embed=True),
    session_id: str = Body(..., embed=True),
    model_name: str = Body(..., embed=True),
):

    # 並行執行：同時讓模型生成回覆 + 安全風險分析
    reply_task = asyncio.create_task(chat_with_model(user_id, session_id, text, model_name))
    safety_task = asyncio.create_task(analyze_risk(user_id, session_id, text))

    # 等待兩個結果都完成
    reply = await reply_task
    risk_score = await safety_task

    return {"response": reply, "score": risk_score}


# 刪除聊天記錄（包含 memory / summary / ai_summary）
@router.delete("/memory/{session_id}")
async def delete_history(user_id: str ,session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # 刪除 memory
        await db.execute("DELETE FROM memory WHERE user_id = ? AND session_id = ?",(user_id, session_id))
        # 刪除 summary
        await db.execute("DELETE FROM summary WHERE user_id = ? AND session_id = ?", (user_id, session_id))
        # 刪除 ai_summary
        await db.execute("DELETE FROM ai_summary WHERE user_id = ? AND session_id = ?", (user_id, session_id))

        await db.commit()