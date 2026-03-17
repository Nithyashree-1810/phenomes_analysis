def transcribe_audio(model, audio_path):

    result = model.transcribe(
        str(audio_path),
        language="en",
        fp16=False
    )

    return result["text"].strip()