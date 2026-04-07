# whisper_service.py
import whisper
import io
import asyncio

# 建議換模型 (medium 或 large-v2)
model = whisper.load_model("medium")


async def transcribe_audio(file):
    """
    將上傳的音訊轉文字 (支援中文)
    file: Starlette UploadFile 或 BytesIO
    """
    # 處理 bytes
    if isinstance(file, bytes):
        audio_file = io.BytesIO(file)
    else:
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)

    loop = asyncio.get_running_loop()

    # 強制中文辨識
    result = await loop.run_in_executor(
        None, lambda: model.transcribe(audio_file, language="zh")
    )

    return {"text": result["text"].strip()}
