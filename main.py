# main.py
from fastapi import FastAPI
from routers import asr, chat, sessions
from services.memory_store import init_db

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(asr.router, prefix="/asr")
app.include_router(chat.router, prefix="/chat")
app.include_router(sessions.router, prefix="/sessions")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
