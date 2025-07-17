import whisper
import os

model = whisper.load_model("base")

async def transcribe_audio(file):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    result = model.transcribe(temp_path)
    os.remove(temp_path)
    return {"text": result["text"]}
