# routers/app_ws.py
import asyncio
import base64
import json
from io import BytesIO
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from gtts import gTTS
import whisper
import numpy as np
import torch
from whisper.audio import load_audio, pad_or_trim, log_mel_spectrogram
from services.llm_service import chat_with_model

websocket_router = APIRouter()

whisper_model = whisper.load_model("base")
clients_audio_buffer = {}  # {client_id: [audio_bytes]}

@websocket_router.websocket("/ws/stt")
async def ws_stt(ws: WebSocket):
    await ws.accept()
    client_id = id(ws)
    clients_audio_buffer[client_id] = []

    print("INFO: connection open")

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                if data == "ping":
                    await ws.send_text("pong")
                continue

            msg_type = msg.get("type")
            if msg_type == "audio":
                audio_b64 = msg.get("data")
                audio_bytes = base64.b64decode(audio_b64)
                clients_audio_buffer[client_id].append(audio_bytes)
                await ws.send_text(json.dumps({"type": "partial", "text": "[Audio received]"}))


            elif msg_type == "flush":
                # 將累積音訊送給 Whisper
                audio_data = b"".join(clients_audio_buffer[client_id])
                clients_audio_buffer[client_id] = []
                # Whisper STT
                # 將 bytes 轉成 numpy array
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0  # wav16bit -> float32
                audio_np = pad_or_trim(audio_np)
                mel = log_mel_spectrogram(audio_np)
                options = whisper.DecodingOptions()
                result = whisper.decode(whisper_model, mel, options)
                text = result.text
                await ws.send_text(json.dumps({"type": "final", "text": text}))

                # ---- LLM ----
                model_name = msg.get("model_name", "Sunny")
                user_id = msg.get("user_id", "test_user")
                session_id = msg.get("session_id", "test_session")

                reply_text = await chat_with_model(
                    user_id=user_id,
                    session_id=session_id,
                    user_input=text,
                    model_name=model_name
                )

                await ws.send_text(json.dumps({"type": "llm", "text": reply_text}))

                # ---- TTS ----
                tts = gTTS(text=reply_text, lang="zh-tw")
                audio_io = BytesIO()
                tts.write_to_fp(audio_io)
                audio_io.seek(0)
                audio_b64 = base64.b64encode(audio_io.read()).decode("utf-8")
                await ws.send_text(json.dumps({"type": "tts", "data": audio_b64}))

    except WebSocketDisconnect:
        print("INFO: connection closed")
        clients_audio_buffer.pop(client_id, None)
