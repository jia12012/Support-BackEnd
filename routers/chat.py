# routers/chat.py
from fastapi import APIRouter, Body
from services.llm_service import chat_with_model
from services.memory_store import save_history

router = APIRouter()

@router.post("/")
async def chat_endpoint(
    text: str = Body(..., embed=True),
    session_id: str = Body(..., embed=True),
    model_name: str = Body(..., embed=True),
):
    reply = await chat_with_model(text, session_id, model_name)
    return {"response": reply}


@router.delete("/memory/{session_id}")
async def delete_memory(session_id: str):
    await save_history(session_id, [])  # 用空 list 覆蓋
    return {"message": f"Memory for session '{session_id}' deleted."}
