import whisper
import numpy as np
import time

MODEL_SIZE = "small"
DEVICE = "cpu"


class Transcriber: 
    # Constructor to initialize the audio stream
    # - self is always the first argument in a method in a class
    def __init__(self, model_size, device):
        self.model = whisper.load_model(model_size, device=device)
        self.device = device

    # Function to transcribe the audio data in real-time
    # - is called as soon as soon as the stream is started
    # - on_transcription and on_audio_chunk are functions, passed as arguments 
    def transcribe_stream(self, audio_queue, chunk_samples, on_transcription, on_audio_chunk):
        buffer = np.empty((0,), dtype=np.int16)

        while True:
            pcm = audio_queue.get()
            buffer = np.concatenate((buffer, pcm))

            if buffer.shape[0] >= chunk_samples:
                chunk, buffer = buffer[:chunk_samples], buffer[chunk_samples:]

                # Normalise the audio data to the range [-1, 1] for whisper model
                audio_float = chunk.astype(np.float32) / 32767.0

                # Callback for metrics (e.g., volume, pitch)
                if on_audio_chunk: # Checks whether on_audio_chunk is not None (i.e. if it exists)
                    on_audio_chunk(audio_float)

                # Transcribe the audio data
                # - returns a dictionary 
                # - fp16=(DEVICE!="cpu") means use fp16 (half-precision) for faster inference on GPU
                result = self.model.transcribe(
                    audio_float,
                    fp16=(self.device!="cpu"),
                    language="en"
                )

                # Prints the value with the key "text" in the dictionary 
                if on_transcription:
                    on_transcription(result["text"])