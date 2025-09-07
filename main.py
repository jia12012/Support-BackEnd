# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import asr, chat, sessions, summary, postcard, dailyQ
from services.memory_store import init_db

app = FastAPI()

# ===== 啟動時初始化資料庫 =====
@app.on_event("startup")
async def startup():
    await init_db()

# ===== 加入 Router =====
app.include_router(asr.router, prefix="/asr")
app.include_router(chat.router, prefix="/chat")
app.include_router(sessions.router, prefix="/sessions")
app.include_router(summary.router, prefix="/summary", tags=["summary"])
app.include_router(postcard.router, prefix="/postcard")
app.include_router(dailyQ.router, prefix="/daily")

# ===== 設定靜態檔路徑，提供 /audio/xxxx.wav =====
BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR), html=False), name="audio")

# ===== CORS 設定（前端 Flutter / Web 都能連） =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 也可改成 ["http://localhost:8080", "http://10.0.2.2:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Main entry =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
