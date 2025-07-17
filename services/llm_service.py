from llama_cpp import Llama

llm = Llama(
    model_path="C:/Users/User/.lmstudio/models/test/cbt-test/cbt-mental-llama-7b-q4_K_M.gguf",
    n_ctx=2048,
    n_threads=6,
    n_batch=32,
    verbose=False
)

def chat_with_model(user_input: str, max_new_tokens: int = 150) -> str:
    # 加上 MentaLLaMA chat prompt 模板
    prompt = f"<|user|>\n{user_input.strip()}\n<|assistant|>\n"

    output = llm(
        prompt=prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.95,
        stop=["<|user|>", "<|endoftext|>"]
    )

    # 去掉 prompt 部分，只取模型回應
    reply = output["choices"][0]["text"].strip()
    return reply
