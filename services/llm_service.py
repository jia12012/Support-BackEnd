# services/llm_service.py
from llama_cpp import Llama
from services.memory_store import get_history, save_history

# 初始化四個模型
llm_models = {
    "cbt": Llama(model_path="C:/Users/User/.lmstudio/models/test/cbt-test/cbt-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=32, verbose=False),
    "sfbt": Llama(model_path="C:/Users/User/.lmstudio/models/test/sfbt-test/sfbt-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=32, verbose=False),
    "pct": Llama(model_path="C:/Users/User/.lmstudio/models/who/pct_0722/pct-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=32, verbose=False),
    "mft": Llama(model_path="C:/Users/User/.lmstudio/models/Me/family-mental-llama-7b-q4_K_M/family-mental-llama-7b-q4_K_M.gguf", n_ctx=2048, n_threads=6, n_batch=32, verbose=False),
}

async def chat_with_model(user_input: str, session_id: str,model_name: str, max_new_tokens: int = 150) -> str:
    history = await get_history(session_id)

    prompt_parts = []
    for turn in history:
        prompt_parts.append(f"<|user|>\n{turn['user']}\n<|assistant|>\n{turn['bot']}")
    prompt_parts.append(f"<|user|>\n{user_input.strip()}\n<|assistant|>\n")
    prompt = "\n".join(prompt_parts)

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
    await save_history(session_id, history[-10:])

    return reply
