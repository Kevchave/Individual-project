import queue 
import threading 
import time
import numpy as np 
import sounddevice as sd
import whisper 

MODEL_SIZE = "small"
DEVICE = "cpu"
SAMPLE_RATE = 16000
CHUNK_SEC = 3.0


model = whisper.load_model(MODEL_SIZE, device=DEVICE)
audio_queue = queue.Queue()

# Callback function that will be called for each chunk of audio
# - indata: Numpy array of shape (frames, channels) containing the audio data
# - frames: The number of frames in this chunk
# - time_info: Time info 
# - status: Error/status flags
def callback(indata, frames, time_info, status):
    if status: 
        print("Mic error: ", status)
    pcm = (indata[:, 0] * 32767).astype(np.int16) # Convert audio data (first channel) to 16-bit PCM format
    audio_queue.put(pcm) # Put the audio data into the queue

accumulated = ""

def stream_transcribe():
    global accumulated 
    chunk_samples = int(CHUNK_SEC * SAMPLE_RATE)
    buffer = np.empty((0,), dtype=np.int16)

    while True:
        pcm = audio_queue.get()
        buffer = np.concatenate((buffer, pcm))

        if buffer.shape[0] >= chunk_samples:
            chunk, buffer = buffer[:chunk_samples], buffer[chunk_samples:]

            # Normalise the audio data to the range [-1, 1] for whisper model
            audio_float = chunk.astype(np.float32) / 32767.0

            # Transcribe the audio data
            # - returns a dictionary 
            # - fp16=(DEVICE!="cpu") means use fp16 (half-precision) for faster inference on GPU
            result = model.transcribe(audio_float, fp16=(DEVICE!="cpu"), language="en")

            # Prints the value with the key "text" in the dictionary 
            print(str(result["text"]).strip())
            accumulated += str(result["text"]).strip() + " "

def main():
    # Start the transcription thread 
    # - this thread runs the stream_transcribe function in the background
    # - daemon=True means the thread will continue running even if the main thread exits
    threading.Thread(target=stream_transcribe, daemon=True).start()

    # Start the audio stream
    # - callback is the function that will be called for each chunk of audio
    # - dtype="float32" for higher precision
    # - with keyword ensures the audio stream is closed when the block exits
    with sd.InputStream(callback=callback, dtype="float32", samplerate=SAMPLE_RATE, channels=1):
        print("Recording... (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(1) # The main thread will (idefinitely) sleep for 1 second until interrupted (Ctrl + C)
        except KeyboardInterrupt:
            print("Recording stopped")
        
        print(f"Final transcription: \n {accumulated.strip()}")

if __name__ == "__main__":
    main()