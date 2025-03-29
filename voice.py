import whisper
import torch
def transcribe_audio(audio_file, model_size="base"):
    model = whisper.load_model("small").to("cuda").to(torch.float32)   # Load the specified model
    result = model.transcribe(audio_file)
    return result["text"]

# Try different models
print(transcribe_audio(r"C:\Users\RAJESH\OneDrive\desktop\speech.opus", model_size="small"))
