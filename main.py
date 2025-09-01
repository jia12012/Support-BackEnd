# main.py
from fastapi import FastAPI
from routers import asr, chat, sessions, summary
from services.memory_store import init_db
from routers import postcard
from routers import dailyQ

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(asr.router, prefix="/asr")
app.include_router(chat.router, prefix="/chat")
app.include_router(sessions.router, prefix="/sessions")
app.include_router(summary.router, prefix="/summary", tags=["summary" ])
app.include_router(postcard.router,prefix="/postcard")
app.include_router(dailyQ.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
