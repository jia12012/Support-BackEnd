# routers/app_ws.py
import json
import base64
import asyncio
from io import BytesIO
import wave
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from gtts import gTTS
import whisper
from services.llm_service import chat_with_model
from starlette.websockets import WebSocketState
import logging

logger = logging.getLogger(__name__)

websocket_router = APIRouter()

# Whisper 載入（CPU 請關 fp16）
whisper_model = whisper.load_model("base")

# { client_id: { "chunks": [bytes, ...], "last_meta": {...} } }
clients_state = {}

# ---------- utils ----------
async def send_json_safe(ws: WebSocket, obj) -> bool:
    """
    連線存在且未關閉時才嘗試傳送；支援 dict 或 str。
    失敗時返回 False，不丟例外（避免 close 後再送造成錯誤）。
    """
    try:
        if ws.client_state != WebSocketState.CONNECTED:
            return False
        data = obj if isinstance(obj, str) else json.dumps(obj)
        await ws.send_text(data)
        return True
    except Exception as e:
        logger.debug(f"send_json_safe failed: {e}")
        return False

def _decode_wav_bytes_to_f32(wav_bytes: bytes) -> np.ndarray:
    """將單段 WAV 解析為 float32 mono [-1,1]，期望 16kHz / 16-bit。"""
    with wave.open(BytesIO(wav_bytes), 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth  = wf.getsampwidth()
        framerate  = wf.getframerate()
        n_frames   = wf.getnframes()
        frames     = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Unsupported sample width: {sampwidth*8}bit; expect 16-bit.")
    if framerate != 16000:
        raise ValueError(f"Unsupported sample rate: {framerate}; expect 16000 Hz.")

    audio_i16 = np.frombuffer(frames, dtype=np.int16)
    if n_channels > 1:
        audio_i16 = audio_i16.reshape(-1, n_channels).mean(axis=1).astype(np.int16)
    audio_f32 = (audio_i16.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
    return audio_f32

def _audio_stats(x: np.ndarray, sr: int = 16000):
    if x.size == 0:
        return 0.0, 0.0, 0.0
    dur = float(len(x) / sr)
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x**2)))
    return dur, peak, rms

def _trim_silence(x: np.ndarray, thr: float, min_len: int, sr: int = 16000):
    """
    以幅度閾值去頭尾靜音。thr 請外部根據當輪 rms 動態給定。
    min_len: 少於此長度就視為無效（樣本數）。
    """
    if x.size == 0:
        return np.array([], dtype=np.float32)
    idx = np.where(np.abs(x) > thr)[0]
    if idx.size == 0:
        return np.array([], dtype=np.float32)
    y = x[idx[0]: idx[-1] + 1]
    if len(y) < min_len:
        return np.array([], dtype=np.float32)
    return y

async def _run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

def _whisper_transcribe_en_sync(audio_f32: np.ndarray) -> str:
    """同步版：丟給 thread executor 用。"""
    result = whisper.transcribe(
        whisper_model,
        audio_f32,
        language='en',
        task='transcribe',
        fp16=False,
        condition_on_previous_text=False,
        temperature=0,
        without_timestamps=True,
        no_speech_threshold=0.4,
        logprob_threshold=-1.0,
        compression_ratio_threshold=2.4,
    )
    return (result.get("text") or "").strip()

def _synthesize_tts_to_b64(text: str, lang: str = "zh-tw") -> str:
    """同步版 gTTS → base64，丟給 thread executor 用。"""
    bio = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(bio)
    bio.seek(0)
    return base64.b64encode(bio.read()).decode("utf-8")

# ---------- core ----------
async def _process_flush(ws: WebSocket, state: dict):
    # 斷線就不要處理
    if ws.client_state != WebSocketState.CONNECTED:
        state["chunks"] = []
        return

    chunks = state.get("chunks", [])
    if not chunks:
        return

    try:
        # 1) 解析每個 WAV -> float32 mono，拼接
        pieces = [_decode_wav_bytes_to_f32(b) for b in chunks]
        audio_all = np.concatenate(pieces, axis=0) if len(pieces) > 1 else pieces[0]

        # 除錯：修剪前統計
        dur0, peak0, rms0 = _audio_stats(audio_all)
        await send_json_safe(ws, {"type": "debug", "stage": "decoded", "dur": dur0, "peak": peak0, "rms": rms0})

        # 2) 動態去頭尾靜音（門檻跟本輪 rms 成比例）
        dynamic_thr = max(0.0008, min(0.02, rms0 * 1.5))
        audio_trim = _trim_silence(audio_all, thr=dynamic_thr, min_len=int(0.12 * 16000))  # 至少 ~0.12s

        dur1, peak1, rms1 = _audio_stats(audio_trim)
        await send_json_safe(ws, {"type": "debug", "stage": "trimmed", "dur": dur1, "peak": peak1, "rms": rms1})

        # 若修剪後是空，但原始 rms 不算太低，直接跳過修剪（避免過砍）
        if audio_trim.size == 0 and rms0 > 0.0007:
            audio_proc = audio_all
            await send_json_safe(ws, {"type": "debug", "stage": "bypass_trim", "dur": dur0, "peak": peak0, "rms": rms0})
        else:
            audio_proc = audio_trim

        # 再次判斷，若仍然太短就結束本輪
        if audio_proc.size == 0:
            await send_json_safe(ws, {"type": "final", "text": ""})
            state["chunks"] = []
            return

        # 3) 自動增益（normalize 到固定峰值，避免音量太小）
        peak = float(np.max(np.abs(audio_proc)))
        if peak > 0:
            target_peak = 0.2  # 不要放太大，0.2~0.3 足夠
            gain = target_peak / peak
            audio_proc = (audio_proc * gain).clip(-1.0, 1.0)

        # 3.5) Whisper（放 executor，並把 no_speech_threshold 降到 0.2）
        def _whisper_sync(a: np.ndarray) -> str:
            return (whisper.transcribe(
                whisper_model,
                a,
                language='en',
                task='transcribe',
                fp16=False,
                condition_on_previous_text=False,
                temperature=0,
                without_timestamps=True,
                no_speech_threshold=0.2,          # ↓ 降低靜音判定門檻
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            ).get("text") or "").strip()

        text = await _run_in_thread(_whisper_sync, audio_proc)
        await send_json_safe(ws, {"type": "final", "text": text})

        if not text.strip():
            state["chunks"] = []
            return

        # 4) LLM
        meta = state.get("last_meta", {}) or {}
        model_name = meta.get("model_name", "Sunny")
        user_id    = meta.get("user_id", "test_user")
        session_id = meta.get("session_id", "test_session")

        try:
            reply_text = await chat_with_model(
                user_id=user_id,
                session_id=session_id,
                user_input=text,
                model_name=model_name,
            )
        except Exception as e:
            await send_json_safe(ws, {"type": "error", "message": f"llm_failed: {e}"})
            state["chunks"] = []
            return

        await send_json_safe(ws, {"type": "llm", "text": reply_text})

        # 5) TTS（放 executor，避免阻塞）
        try:
            audio_b64 = await _run_in_thread(_synthesize_tts_to_b64, reply_text, "en")
            await send_json_safe(ws, {"type": "tts", "data": audio_b64})
        except Exception as e:
            await send_json_safe(ws, {"type": "error", "message": f"tts_failed: {e}"})

    except Exception as e:
        # close 後可能會進到這裡；僅嘗試送，送不出去就算了
        await send_json_safe(ws, {"type": "error", "message": f"process_flush_failed: {e}"})
    finally:
        state["chunks"] = []

@websocket_router.websocket("/ws/stt")
async def ws_stt(ws: WebSocket):
    await ws.accept()
    client_id = id(ws)
    clients_state[client_id] = {"chunks": [], "last_meta": {}}
    print("INFO: connection open")

    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await send_json_safe(ws, "pong")
                continue

            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await send_json_safe(ws, {"type": "error", "message": "invalid_json"})
                continue

            msg_type = msg.get("type")
            state = clients_state[client_id]

            if msg_type == "audio":
                audio_b64 = msg.get("data", "")
                if not audio_b64:
                    await send_json_safe(ws, {"type": "error", "message": "empty_audio"})
                    continue
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                except Exception:
                    await send_json_safe(ws, {"type": "error", "message": "bad_base64"})
                    continue

                state["chunks"].append(audio_bytes)
                # 更新 meta，flush/end 沒帶一樣可用
                state["last_meta"] = {
                    "user_id":    msg.get("user_id", state["last_meta"].get("user_id")),
                    "session_id": msg.get("session_id", state["last_meta"].get("session_id")),
                    "model_name": msg.get("model_name", state["last_meta"].get("model_name")),
                }
                await send_json_safe(ws, {"type": "partial", "text": "[Audio received]"})

            elif msg_type in ("flush", "end"):
                try:
                    await _process_flush(ws, state)
                except Exception as e:
                    logger.debug(f"_process_flush error after disconnect?: {e}")
                    # 不回傳任何訊息，避免在關閉後再送

            else:
                await send_json_safe(ws, {"type": "error", "message": f"unknown_type:{msg_type}"})

    except WebSocketDisconnect:
        print("INFO: connection closed")
    finally:
        clients_state.pop(client_id, None)
