# routers/asr.py
from fastapi import APIRouter, UploadFile, File, Form
from services.whisper_service import transcribe_audio
from services.llm_service import chat_with_model  # 現在是 async 的

router = APIRouter()

@router.post("/with-reply")
async def asr_and_reply(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    model_name: str = Form(...),
):
    transcribed = await transcribe_audio(file)
    user_text = transcribed["text"]

    reply = await chat_with_model(
        user_input=user_text,
        session_id=session_id,
        model_name=model_name  # 傳進去
    )

    return {
        "transcribed_text": user_text,
        "model_reply": reply
    }
