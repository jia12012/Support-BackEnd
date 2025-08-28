from transformers import pipeline
import aiosqlite
from services.memory_store import get_ai_history, save_ai_summary
DB_PATH = "chat_memory.db"

# 初始化一次（建議啟動時就跑）
summarizer = pipeline("summarization", model="philschmid/bart-large-cnn-samsum")

def summarize_conversation(history: list[str]) -> str:
    """
    history: 對話內容的 list（每個元素是使用者或模型的一句話）
    """
    # 合併成一段文字
    text = " ".join(history)

    input_len = len(text.split())
    max_length = int(input_len * 0.5) # 最長約佔原文 30%
    min_length = int(input_len * 0.1)  # 最短佔原文 10%

    # T5 要求加前綴 "summarize:"
    text = "summarize: " + text

    # 呼叫本地模型摘要
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]

#
async def summarize_ai_output(session_id: str) :
    async with aiosqlite.connect(DB_PATH) as db:

        memory = await get_ai_history(session_id)
        if memory:
            ai_history = memory["history"]
            model = memory["model"]
            if len(ai_history)>3:
                ai_summary = summarize_conversation(ai_history)
                print("ai summary:", ai_summary)
                await save_ai_summary(session_id, ai_summary, model)
                print('Succesfully save ai summary!')

    return {"ok": True}

