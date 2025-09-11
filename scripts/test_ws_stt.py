import asyncio
import websockets
import base64
import json
from pathlib import Path

# 設定 WebSocket URL
WS_URL = "ws://127.0.0.1:8000/ws/stt"

# 測試音檔路徑
AUDIO_FILE = "output.wav"  # 確保有一個短音檔

# 模型資訊
USER_ID = "test_user"
SESSION_ID = "test_session"
MODEL_NAME = "Sunny"

async def send_audio(ws, audio_bytes):
    """將音訊轉 base64 並送到 WebSocket"""
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    msg = json.dumps({"type": "audio", "data": audio_b64})
    await ws.send(msg)
    resp = await ws.recv()
    print("[Partial Whisper]:", resp)

async def flush_audio(ws, audio_bytes):
    """flush 送 final audio 做完整辨識 + LLM + TTS"""
    msg = json.dumps({
        "type": "flush",
        "file": base64.b64encode(audio_bytes).decode("utf-8"),
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "model_name": MODEL_NAME
    })
    await ws.send(msg)
    final_resp = await ws.recv()
    print("[Final Response]:", final_resp)
    # 嘗試解析回傳的 JSON
    try:
        data = json.loads(final_resp)
        if "tts_file" in data:
            print(f"Generated TTS file: {data['tts_file']}")
    except Exception as e:
        print("Failed to parse final response:", e)

async def test_ws():
    async with websockets.connect(WS_URL) as ws:
        print("Connected to WebSocket")

        # 1️⃣ 先測 ping/pong
        await ws.send("pong")
        print("Sent pong (ping test)")

        # 2️⃣ 讀音檔
        audio_bytes = Path(AUDIO_FILE).read_bytes()

        # 3️⃣ 發送 partial audio
        await send_audio(ws, audio_bytes)

        # 4️⃣ flush 完整辨識
        await flush_audio(ws, audio_bytes)

if __name__ == "__main__":
    asyncio.run(test_ws())
