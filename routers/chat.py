# routers/chat.py
from fastapi import APIRouter, Body
from services.llm_service import chat_with_model

router = APIRouter()

@router.post("/")
async def chat_endpoint(
    text: str = Body(..., embed=True),
    session_id: str = Body(..., embed=True)
):
    reply = await chat_with_model(text, session_id)
    return {"response": reply}
