# # tts_service.py
# from gtts import gTTS
# from pathlib import Path
# import uuid
#
# # audio 資料夾
# AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"
# AUDIO_DIR.mkdir(exist_ok=True)
#
#
# def text_to_speech(text: str) -> str:
#     """
#     使用 gTTS 產生 mp3 語音
#     回傳檔名
#     """
#     if not text.strip():
#         raise ValueError("text is empty")
#
#     filename = f"{uuid.uuid4().hex}.mp3"
#     filepath = AUDIO_DIR / filename
#
#     tts = gTTS(text=text, lang="en")
#     tts.save(str(filepath))
#
#     return filename

from pathlib import Path
import uuid
from TTS.api import TTS
import torch
from pydub import AudioSegment  # 需要 pip install pydub

# audio 資料夾
AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# 選擇裝置：有 GPU 用 GPU，否則 CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# 載入 Jenny 模型（只載一次，避免每次呼叫都重下載）
tts = TTS("tts_models/en/jenny/jenny").to(device)


def text_to_speech(text: str) -> str:
    """
    使用 Coqui TTS (Jenny) 產生 MP3 語音
    回傳檔名
    """
    if not text.strip():
        raise ValueError("text is empty")

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = AUDIO_DIR / filename

    # 先輸出為 wav
    wav_path = filepath.with_suffix(".wav")
    tts.tts_to_file(text=text, file_path=str(wav_path))

    # 轉成 mp3
    AudioSegment.from_wav(wav_path).export(filepath, format="mp3")

    # 刪掉 wav（選擇性）
    wav_path.unlink(missing_ok=True)

    return filename
