# services/tts_service.py
from __future__ import annotations

import mimetypes
import os
import tempfile
import uuid
import subprocess
from pathlib import Path
from typing import Optional

# 確保系統認得 .mp3 的 MIME（StaticFiles 會用到）
mimetypes.add_type("audio/mpeg", ".mp3")

# === 路徑設定：與 main.py 的 BASE_DIR / "audio" 對齊 ===
# 這裡的 __file__ 在 services/tts_service.py，往上兩層到專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# === 載入 TTS 模型（只載一次） ===
# 你原本的程式在檔案頂部已經有載入 TTS；這裡也可集中管理
try:
    from TTS.api import TTS
    tts = TTS(
        model_name="tts_models/en/ljspeech/tacotron2-DDC",
        progress_bar=False,
        gpu=False,  # 若有 GPU 可改 True
    )
except Exception as e:
    # 這樣如果模型載入失敗，能在啟動就看到錯誤
    raise RuntimeError(f"Failed to initialize TTS model: {e}") from e


def _ensure_ffmpeg() -> None:
    """檢查 ffmpeg 是否存在，否則丟出明確錯誤（比 MEDIA_ERROR_UNKNOWN 好找）。"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        raise RuntimeError(
            "ffmpeg not found. Please install ffmpeg and ensure it is in PATH."
        )


def text_to_speech(text: str, *, filename: Optional[str] = None) -> str:
    """
    產生語音並輸出到 audio/ 目錄，回傳檔名（給前端組 URL: /audio/{filename}）。
    - 會先輸出暫存 wav，再用 ffmpeg 轉 mp3
    - 產生唯一檔名，避免並發覆蓋/快取問題
    - 採用原子移動，避免前端讀到半檔案
    """
    if not text or not text.strip():
        raise ValueError("text is empty")

    _ensure_ffmpeg()

    # 產生唯一檔名（或使用呼叫方指定的）
    # 建議固定副檔名 .mp3，前端就不需要猜 mimeType
    safe_name = filename if filename else f"{uuid.uuid4().hex}.mp3"

    final_mp3_path = AUDIO_DIR / safe_name

    # 1) 先用 NamedTemporaryFile 寫出 WAV（位於 AUDIO_DIR，避免跨磁碟移動）
    with tempfile.NamedTemporaryFile(prefix="tts_", suffix=".wav", dir=AUDIO_DIR, delete=False) as tmp_wav:
        tmp_wav_path = Path(tmp_wav.name)

    try:
        # TTS 直接寫進暫存 wav
        tts.tts_to_file(text=text, file_path=str(tmp_wav_path))

        # 2) 再轉成 mp3（輸出到另一個暫存檔）
        with tempfile.NamedTemporaryFile(prefix="tts_", suffix=".mp3", dir=AUDIO_DIR, delete=False) as tmp_mp3:
            tmp_mp3_path = Path(tmp_mp3.name)

        # 使用 ffmpeg 轉檔；-y 覆蓋暫存檔、-qscale:a 2 ≈ 高音質
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_wav_path), "-codec:a", "libmp3lame", "-qscale:a", "2", str(tmp_mp3_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 3) 原子方式把暫存 mp3 移到最終檔案位置（避免前端讀到未完成檔）
        os.replace(tmp_mp3_path, final_mp3_path)
    finally:
        # 清掉暫存 wav & 任何殘留的 mp3 暫存檔
        try:
            if 'tmp_wav_path' in locals() and tmp_wav_path.exists():
                tmp_wav_path.unlink()
        except Exception:
            pass
        try:
            if 'tmp_mp3_path' in locals() and tmp_mp3_path.exists():
                tmp_mp3_path.unlink()
        except Exception:
            pass

    # 回傳檔名（不是絕對路徑），FastAPI 會用 /audio/{檔名} 提供
    return final_mp3_path.name


