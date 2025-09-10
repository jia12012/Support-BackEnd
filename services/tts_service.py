# tts_service.py
from gtts import gTTS
from pathlib import Path
import uuid

# audio 資料夾
AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


def text_to_speech(text: str) -> str:
    """
    使用 gTTS 產生 mp3 語音
    回傳檔名
    """
    if not text.strip():
        raise ValueError("text is empty")

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = AUDIO_DIR / filename

    tts = gTTS(text=text, lang="en")
    tts.save(str(filepath))

    return filename
