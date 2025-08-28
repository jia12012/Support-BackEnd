# routers/summary.py
from fastapi import APIRouter
from pydantic import BaseModel
import aiosqlite
import os

router = APIRouter()

# 依你的實際路徑調整
DB_PATH = os.getenv("DB_PATH", "chat_memory.db")

class AiSummaryOut(BaseModel):
  session_id: str
  ai_summary: str
  model: str
  created_at: str  # 格式 'YYYY-MM-DD HH:MM:SS'

@router.get("/get_ai_summary", response_model=list[AiSummaryOut])
async def get_ai_summary():
  """
  讀取 ai_summary 資料表全部資料，依 created_at DESC 排序。
  資料表欄位：session_id TEXT, ai_summary TEXT, model TEXT, created_at TEXT
  created_at 例如：'2025-08-28 06:24:55'
  """
  query = """
    SELECT session_id, ai_summary_text, model, created_at
    FROM ai_summary
    ORDER BY datetime(created_at) DESC
  """
  rows: list[AiSummaryOut] = []
  async with aiosqlite.connect(DB_PATH) as db:
    db.row_factory = aiosqlite.Row
    async with db.execute(query) as cursor:
      async for row in cursor:
        rows.append(AiSummaryOut(
          session_id=row["session_id"],
          ai_summary=row["ai_summary_text"],
          model=row["model"],
          created_at=row["created_at"],
        ))
  return rows
