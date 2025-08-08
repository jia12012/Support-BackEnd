from TTS.api import TTS

# 初始化模型（建議在啟動時只載入一次）
tts = TTS(
    model_name="tts_models/en/ljspeech/tacotron2-DDC",
    progress_bar=False,
    gpu=False  # 若有 GPU 可設為 True
)

def text_to_speech(text: str, output_path: str = "output.wav"):
    tts.tts_to_file(text=text, file_path=output_path)
    return output_path
