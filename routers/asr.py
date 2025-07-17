# routers/asr.py
from fastapi import APIRouter, UploadFile, File, Form
from services.whisper_service import transcribe_audio
from services.llm_service import chat_with_model

router = APIRouter()

@router.post("/with-reply")
async def asr_and_reply(
    file: UploadFile = File(...),
    session_id: str = Form(...)  # 加上 session_id 傳入
):
    transcribed = await transcribe_audio(file)
    user_text = transcribed["text"]
    reply = chat_with_model(user_text, session_id)

    return {
        "transcribed_text": user_text,
        "model_reply": reply
    }
