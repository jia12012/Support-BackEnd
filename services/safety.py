from llama_cpp import Llama
from services.memory_store import get_history, get_safety_score, save_safety_score
import re

# 初始化模型
llm = Llama(model_path="C:/Users/User/.lmstudio/models/imported-models/uncategorized/sentimental-analysis-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6,
            n_batch=64, verbose=False)


async def analyze_risk(user_id: str, session_id: str, user_input: str, max_new_tokens: int = 150) -> int:
    history = await get_history(user_id, session_id)
    base_score = await get_safety_score(user_id, session_id)
    prompt_parts = []
    prompt_parts.append("""Task: You are a strict and concise mental health classifier.
    You must determine two labels for each input text:
    Suicide intent (Yes/No)
    Depression severity (Mild/Moderate/Severe)

    Output rules:
    Output only the two words separated by a comma and a space.
    Do NOT output explanations, reasoning, or extra text.
    Example of valid output format: "Yes, Moderate" or "No, Mild"
    Few-shot examples:
    <|User|> I feel tired these days but I can still handle my work and daily life.
    <|Assistant|> No, Mild

    <|User|> Lately I've been sad and unmotivated, but I never thought of ending my life.
    <|Assistant|> No, Moderate

    <|User|> Sometimes I think about hurting myself, but I won’t act on it.
    <|Assistant|> Yes, Moderate
    --- End of few-shot ---
    Now classify the following:""")
    for turn in history[-3:]:
        prompt_parts.append(f"<|user|>{turn['user']}")
    prompt_parts.append(f"<|user|>{user_input.strip()}<|assistant|>")
    prompt = "".join(prompt_parts)

    output = llm(
        prompt=prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.95,
        stop=["<|user|>", "<|endoftext|>", "</|user|>", "User:"]
    )

    response = output["choices"][0]["text"].strip()
    print(f"[DEBUG] model raw output: {response}")

    # === 解析模型输出 ===
    # 例如模型输出: "Yes, Moderate"
    text_lower = response.lower()
    result_score = 0

    # 中度忧郁（Moderate）加1
    if "moderate" in text_lower:
        result_score = 1

    # 严重忧郁（Severe）加2
    if "severe" in text_lower:
        result_score = 2

    # 自杀意图（Yes）加3
    if "yes" in text_lower:
        result_score = 3

    total_score = int(base_score) + result_score
    await save_safety_score(user_id, session_id, total_score)

    print(f"[INFO] Parsed result: {response} → Score {result_score}, Total {total_score}")

    return total_score
