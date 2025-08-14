from transformers import pipeline

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