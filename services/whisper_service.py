# whisper_service.py
import whisper
import io
import asyncio

# 只載一次模型
model = whisper.load_model("base")


async def transcribe_audio(file):
    """
    將上傳的音訊轉文字
    file: Starlette UploadFile 或 BytesIO
    """
    # 如果是 bytes
    if isinstance(file, bytes):
        audio_file = io.BytesIO(file)
    else:
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, lambda: model.transcribe(audio_file)
    )

    return {"text": result["text"]}
