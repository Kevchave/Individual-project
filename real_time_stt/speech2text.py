import queue 
import threading 
import time
import numpy as np 
import sounddevice as sd
import whisper 
from collections import deque

MODEL_SIZE = "small"
DEVICE = "cpu"
SAMPLE_RATE = 16000
CHUNK_SEC = 3.0
WPM_WINDOW_SECONDS = 6
VOLUME_WINDOW_SECONDS = 6

model = whisper.load_model(MODEL_SIZE, device=DEVICE)
audio_queue = queue.Queue()

audio_buffer = deque()
audio_buffer_lock = threading.Lock()

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

            with audio_buffer_lock:
                audio_buffer.append((audio_float, time.time()))

            # Transcribe the audio data
            # - returns a dictionary 
            # - fp16=(DEVICE!="cpu") means use fp16 (half-precision) for faster inference on GPU
            result = model.transcribe(audio_float, fp16=(DEVICE!="cpu"), language="en")

            # Prints the value with the key "text" in the dictionary 
            print(result["text"])
            with accumulated_lock:
                accumulated.append((str(result["text"]).strip(), time.time()))

def wpm_reporter(window_seconds=WPM_WINDOW_SECONDS):
    try:
        while True: 
            time.sleep(window_seconds)
            track_wpm(window_seconds)
    except Exception as e:
        print(f"Error in WPM reporter: {e}")

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

def volume_reporter(window_seconds=VOLUME_WINDOW_SECONDS):
    # Periodically computes and prints the volume of recent audio.
    try:
        while True:
            time.sleep(window_seconds)
            now = time.time()
            with audio_buffer_lock:
                # Only keep chunks that are within the last window_seconds 
                recent_items = [(chunk, ts) for chunk, ts in audio_buffer if ts >= now - window_seconds]
                recent_chunks = [chunk for chunk, ts in recent_items]

                # Clear the audio buffer and add the recent items (for memory efficiency)
                audio_buffer.clear()
                audio_buffer.extend(recent_items)
            if recent_chunks:
                all_audio = np.concatenate(recent_chunks)
                track_volume(all_audio, window_seconds)
            else:
                print("[DEBUG] No recent chunks to process for volume")
    except Exception as e:
        print(f"Error in volume reporter: {e}")

def track_volume(chunk, window_seconds):
    rms = np.sqrt(np.mean(np.square(chunk)))
    db = 20 * np.log10(rms + 1e-12)
    print(f"Number of chunks: {len(chunk)}")
    print(f"Volume in the past {window_seconds} seconds: {db:.2f} dB")

def main():
    
    # Start the transcription, WPM and volume reporter threads 
    # - each thread runs the target function in the background
    # - daemon=True means the thread will continue running even if the main thread exits
    threading.Thread(target=stream_transcribe, daemon=True).start()
    threading.Thread(target=wpm_reporter, args=(WPM_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=volume_reporter, args=(VOLUME_WINDOW_SECONDS,), daemon=True).start()

    # Start the audio stream
    # - callback is the function that will be called for each chunk of audio
    # - dtype="float32" for higher precision
    # - with keyword ensures the audio stream is closed when the block exits
    with sd.InputStream(callback=callback, dtype="float32", samplerate=SAMPLE_RATE, channels=1):
        print("Recording... (Ctrl+C to stop)")
        start_time = time.time()

        try:
            while True:
                time.sleep(1) # The main thread will (idefinitely) sleep for 1 second until interrupted (Ctrl + C)
        except KeyboardInterrupt:
            print("Recording stopped.\n")
            print(f"Final transcription: \n {' '.join(text for text, ts in accumulated).strip()} \n")
            track_wpm_average(start_time)

if __name__ == "__main__":
    main()