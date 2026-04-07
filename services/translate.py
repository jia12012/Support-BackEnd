from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# 初始化翻譯模型
translate_model_path = "C:/Users/User/PycharmProjects/Support_BackEnd/services/models/nllb"
translate_tokenizer = AutoTokenizer.from_pretrained(translate_model_path)
translate_model = AutoModelForSeq2SeqLM.from_pretrained(translate_model_path)

#翻譯函式
def translate(text, src="eng_Latn", tgt="zho_Hant"):
    # 句子切分
    def split_sentences(s):
        import re
        return re.split(r'(?<=[.!?])\s+', s.strip())

    sentences = split_sentences(text)
    translated_chunks = []

    translate_tokenizer.src_lang = src

    for sentence in sentences:
        encoded = translate_tokenizer(sentence, return_tensors="pt")

        generated = translate_model.generate(
            **encoded,
            forced_bos_token_id=translate_tokenizer.convert_tokens_to_ids(tgt),
            max_new_tokens=256,
            num_beams=5,
            length_penalty=1.3,
            repetition_penalty=1.1,
            no_repeat_ngram_size=3,
            early_stopping=False,
        )

        translated_chunks.append(
            translate_tokenizer.decode(generated[0], skip_special_tokens=True).strip()
        )

    # 合併翻譯後句子
    return " ".join(translated_chunks)