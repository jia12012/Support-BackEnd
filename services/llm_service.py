# services/llm_service.py
from llama_cpp import Llama
from services.memory_store import get_history, save_history, get_summary, save_summary
from services.summarize import summarize_conversation

# 初始化四個模型
llm_models = {
    "Sunny": Llama(model_path="C:/Users/User/.lmstudio/models/test/cbt-test/cbt-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=64, verbose=False),
    "Jennie": Llama(model_path="C:/Users/User/.lmstudio/models/test/sfbt-test/sfbt-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=64, verbose=False),
    "Luka": Llama(model_path="C:/Users/User/.lmstudio/models/who/pct_0722/pct-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=64, verbose=False),
    "Rhea": Llama(model_path="C:/Users/User/.lmstudio/models/Me/family-mental-llama-7b-q4_K_M/family-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=64, verbose=False),
}

async def chat_with_model(user_input: str, session_id: str,model_name: str, max_new_tokens: int = 150) -> str:
    history = await get_history(session_id)
    summary = await get_summary(session_id)

    prompt_parts = []

    # 加入摘要
    if len(history) > 3:
      prompt_parts.append(f"<SUMMARY>{summary}</SUMMARY>")

    for turn in history[-3:] :
        prompt_parts.append(f"<|user|>{turn['user']}<|assistant|>{turn['bot']}")
    prompt_parts.append(f"<|user|>{user_input.strip()}<|assistant|>")
    prompt = "".join(prompt_parts)
    print(prompt)

    llm = llm_models[model_name]
    output = llm(
        prompt=prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.95,
        stop=["<|user|>", "<|endoftext|>"]
    )

    reply = output["choices"][0]["text"].strip()

    history.append({"user": user_input, "bot": reply})

    #進行摘要
    user_history = [turn["user"] for turn in history if "user" in turn]
    user_summary = summarize_conversation(user_history)
    print("summary: ", user_summary)

    await save_history(session_id, history, model_name)
    await save_summary(session_id, user_summary)

    return reply
