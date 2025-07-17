# services/llm_service.py
from llama_cpp import Llama

# 建立記憶儲存：session_id -> message list
conversation_memory = {}

llm = Llama(
    model_path="C:/Users/User/.lmstudio/models/test/cbt-test/cbt-mental-llama-7b-q4_K_M.gguf",
    n_ctx=2048,
    n_threads=6,
    n_batch=32,
    verbose=False
)

def chat_with_model(user_input: str, session_id: str, max_new_tokens: int = 150) -> str:
    history = conversation_memory.get(session_id, [])

    # 整理聊天上下文
    prompt_parts = []
    for turn in history:
        prompt_parts.append(f"<|user|>\n{turn['user']}\n<|assistant|>\n{turn['bot']}")
    prompt_parts.append(f"<|user|>\n{user_input.strip()}\n<|assistant|>\n")
    prompt = "\n".join(prompt_parts)

    output = llm(
        prompt=prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.95,
        stop=["<|user|>", "<|endoftext|>"]
    )

    reply = output["choices"][0]["text"].strip()

    # 存入記憶
    history.append({"user": user_input, "bot": reply})
    conversation_memory[session_id] = history[-10:]  # 最多記 10 筆（避免 prompt 太長）

    return reply
