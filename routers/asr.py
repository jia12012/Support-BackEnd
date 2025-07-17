from fastapi import APIRouter, UploadFile, File
from services.whisper_service import transcribe_audio
from services.llm_service import chat_with_model

router = APIRouter()

@router.post("/with-reply")
async def asr_and_reply(
    file: UploadFile = File(...)
):
    # 1. 語音轉文字
    transcribed = await transcribe_audio(file)
    user_text = transcribed["text"]

    # 2. 餵進你的模型
    reply = chat_with_model(user_text)

    # 3. 回傳文字 & 回覆
    return {
        "transcribed_text": user_text,
        "model_reply": reply
    }
