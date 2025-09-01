from fastapi import APIRouter
from services.memory_store import save_postcard, get_postcards

router = APIRouter()

# 新增明信片
@router.post("/postcards")
async def add_postcard(session_id: str, image_path: str, message: str):
    await save_postcard(session_id, image_path, message)
    return {"status": "success", "session_id": session_id}

# 讀取某個 session 的明信片
@router.get("/postcards/{session_id}")
async def fetch_postcards(session_id: str):
    postcards = await get_postcards(session_id)
    return postcards
