import queue 
import threading 
import time
import numpy as np 
import sounddevice as sd
import whisper 
import schedule

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

accumulated = [] # Each entry is (text, timestamp) tuples
accumulated_lock = threading.Lock()

# Function to transcribe the audio data in real-time
# - is called as soon as soon as the stream is started
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
            print(result["text"])
            with accumulated_lock:
                accumulated.append((str(result["text"].strip()), time.time()))

def wpm_reporter(window_seconds = 6):
    while True: 
        time.sleep(window_seconds)
        track_wpm(window_seconds)

# Function to track the words per minute (WPM)
# - can be made more effecient using deque 
# - to avoid filtering through entire list (which becomes long)
def track_wpm(window_seconds):
    now = time.time()
    with accumulated_lock:
        # Takes every text, where ts (timestamp) is within the last window_seconds 
        recent_texts = [text for text, ts in accumulated if ts >= now - window_seconds]
    text = " ".join(recent_texts)
    elapsed_time =  window_seconds / 60 # In minutes
    # num_words = len(text.split())
    # print(f"Number of words in last {window_seconds} seconds: {num_words}")
    wpm = len(text.split()) / elapsed_time if elapsed_time > 0 else 0
    print(f"WPM (last {window_seconds} seconds): {wpm:.2f}")
    # print(text)

def track_wpm_average(start_time):
    with accumulated_lock:
        all_text = " ".join(text for text, ts in accumulated)
    total_words = len(all_text.split())
    elapsed_time = (time.time() - start_time) / 60 # In minutes
    avg_wpm = total_words / elapsed_time if elapsed_time > 0 else 0 
    # print(f"Total time: {elapsed_time:.2f} minutes")
    print(f"Average WPM: {avg_wpm:.2f}")

def main():

    # Start the transcription thread 
    # - this thread runs the stream_transcribe function in the background
    # - daemon=True means the thread will continue running even if the main thread exits
    threading.Thread(target=stream_transcribe, daemon=True).start()
    
    # Start the WPM reporter thread 
    # - this thread runs the wpm_reporter function in the background
    # - args=(6,) sets window_seconds to 6, and is passed as a tuple 
    # - daemon=True means the thread will continue running even if the main thread exits
    threading.Thread(target=wpm_reporter, args=(6,), daemon=True).start()

    # Start the audio stream
    # - callback is the function that will be called for each chunk of audio
    # - dtype="float32" for higher precision
    # - with keyword ensures the audio stream is closed when the block exits
    with sd.InputStream(callback=callback, dtype="float32", samplerate=SAMPLE_RATE, channels=1):
        print("Recording... (Ctrl+C to stop)")
        start_time = time.time()
        # schedule.every(6).seconds.do(lambda: track_wpm(6)) # Schedule the track_pace function to run every 10 seconds        

        try:
            while True:
                # schedule.run_pending() # Scheduled tasks are executed 
                time.sleep(1) # The main thread will (idefinitely) sleep for 1 second until interrupted (Ctrl + C)
        except KeyboardInterrupt:
            print("Recording stopped.\n")
            print(f"Final transcription: \n {' '.join(text for text, ts in accumulated).strip()} \n")
            track_wpm_average(start_time)

if __name__ == "__main__":
    main()
