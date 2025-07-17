from fastapi import APIRouter, Body
from services.llm_service import chat_with_model

router = APIRouter()

@router.post("/")
async def chat_endpoint(
    text: str = Body(..., embed=True)  # 使用 {"text": "你好"} 格式
):
    reply = chat_with_model(text)
    return {"response": reply}
