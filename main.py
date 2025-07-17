from fastapi import FastAPI
from routers import asr

app = FastAPI()
app.include_router(asr.router, prefix="/asr")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
