import queue 
import threading 
import time
import numpy as np 
import sounddevice as sd
from sympy.core.evalf import N
import whisper 
import librosa

# MODEL_SIZE = "small" - transcribe.py
# DEVICE = "cpu" - transcribe.py
SAMPLE_RATE = 16000
CHUNK_SEC = 3.0
WPM_WINDOW_SECONDS = 6
VOLUME_WINDOW_SECONDS = 6
PITCH_WINDOW_SECONDS = 6

BLACKHOLE_ID = 3 # Redirects output to microphone
MIC_INPUT = None
device_id = MIC_INPUT   # or MIC_INPUT

# model = whisper.load_model(MODEL_SIZE, device=DEVICE) - transcribe.py
# audio_queue = queue.Queue() - audio_steam.py

# Global variables for WPM
# accumulated = [] # Each entry is (text, timestamp) tuples - track_metrics.py
# accumulated_lock = threading.Lock()

# Global variables for Volume tracking
# all_audio_chunks = [] - track_metrics.py
# audio_chunks_lock = threading.Lock()


# Callback function that will be called for each chunk of audio
# - indata: Numpy array of shape (frames, channels) containing the audio data
# - frames: The number of frames in this chunk
# - time_info: Time info 
# - status: Error/status flags
# def callback(indata, frames, time_info, status): - audio_steam.py
#     if status: 
#         print("Mic error: ", status)
#     pcm = (indata[:, 0] * 32767).astype(np.int16) # Convert audio data (first channel) to 16-bit PCM format
#     audio_queue.put(pcm) # Put the audio data into the queue

# # Function to transcribe the audio data in real-time
# # - is called as soon as soon as the stream is started
# def stream_transcribe(): - transcribe.py
#     global accumulated 
#     chunk_samples = int(CHUNK_SEC * SAMPLE_RATE)
#     buffer = np.empty((0,), dtype=np.int16)

#     while True:
#         pcm = audio_queue.get()
#         buffer = np.concatenate((buffer, pcm))

#         if buffer.shape[0] >= chunk_samples:
#             chunk, buffer = buffer[:chunk_samples], buffer[chunk_samples:]

#             # Normalise the audio data to the range [-1, 1] for whisper model
#             audio_float = chunk.astype(np.float32) / 32767.0

#             # Add the audio data to the array for Volume tracking
#             with audio_chunks_lock:
#                 all_audio_chunks.append((audio_float, time.time()))

#             # Transcribe the audio data
#             # - returns a dictionary 
#             # - fp16=(DEVICE!="cpu") means use fp16 (half-precision) for faster inference on GPU
#             result = model.transcribe(audio_float, fp16=(DEVICE!="cpu"), language="en")

#             # Prints the value with the key "text" in the dictionary 
#             print(result["text"])
#             with accumulated_lock:
#                 accumulated.append((str(result["text"]).strip(), time.time()))

def report_pitch_stdev(window_seconds=PITCH_WINDOW_SECONDS):
    try: 
        while True: 
            time.sleep(window_seconds)
            track_pitch_stdev(window_seconds, SAMPLE_RATE)
    except Exception as e:
        print(f"Error in Pitch reporting: {e}")
        

def track_pitch_stdev(window_seconds, sr):
    now = time.time()
    with audio_chunks_lock:
        recent_chunks = [chunk for chunk, ts in all_audio_chunks if ts >= now - window_seconds]

    if not recent_chunks:
        print("Pitch Variance: No audio chunks to process")
        return 
    
    y = np.concatenate(recent_chunks)

    # f0 is fundamental frequency (pitch of the audio)
    # - frame_length is the number of samples in each frame
    # - hop_length is the number of samples to advance between frames
    # - each estimate is still made from x samples, but only slightly shifted
    f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=75, fmax=800, sr=sr, frame_length=2048, hop_length=256)

    # Confidence threshold for voiced frames
    mask = (voiced_flag) & (voiced_prob >= 0.1)
    voiced = f0[mask]

    if len(voiced) == 0:
        print("Pitch Variance: No voice audio detected")
        return 
    
        # print(f"  Frames: {len(f0)}, Voiced frames: {len(voiced)}")
    # print(f"  f₀ min/max: {voiced.min():.1f}/{voiced.max():.1f} Hz")
    # print(f"  f₀ 5th/95th pct: {np.percentile(voiced, 5):.1f}/{np.percentile(voiced,95):.1f} Hz")

    std_dev_pitch = float(np.std(voiced))
    # iqr = np.percentile(voiced, 75) - np.percentile(voiced, 25)
    print(f"Pitch Variance: {std_dev_pitch:.2f} Hz")

def track_overall_pitch_stdev(start_time, sr):
    # elapsed_time = start_time - time.time()
    with audio_chunks_lock:
        y = np.concatenate([chunk for chunk, ts in all_audio_chunks])

    f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=75, fmax=800, sr=sr, frame_length=2048, hop_length=256)

    mask = (voiced_flag) & (voiced_prob >= 0.1)
    voiced = f0[mask]

    if len(voiced) == 0:
        print("Pitch Variance: No voice audio detected")
        return 

    std_dev_pitch = float(np.std(voiced))
    print(f"Overall Pitch Variance: {std_dev_pitch:.2f} Hz")

def report_wpm(window_seconds=WPM_WINDOW_SECONDS):
    try:
        while True: 
            time.sleep(window_seconds)
            track_wpm(window_seconds)
    except Exception as e:
        print(f"Error in WPM reporting: {e}")

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
    total_words = len(all_text.split()) # .split() splits into a list of words 
    elapsed_time = (time.time() - start_time) / 60 # In minutes
    avg_wpm = total_words / elapsed_time if elapsed_time > 0 else 0 
    # print(f"Total time: {elapsed_time:.2f} minutes")
    print(f"Average WPM: {avg_wpm:.2f}")

def report_volume(window_seconds=VOLUME_WINDOW_SECONDS):
    # Periodically computes and prints the volume of recent audio.

    try:
        while True:
            time.sleep(window_seconds)
            now = time.time()
            with audio_chunks_lock:
                # Only keep chunks that are within the last window_seconds 
                recent_chunks = [chunk for chunk, ts in all_audio_chunks if ts >= now - window_seconds]

            if recent_chunks:
                recent_audio = np.concatenate(recent_chunks) # Concatenate the recent chunks into a single array 
                track_volume(recent_audio, window_seconds)
            else:
                print("[DEBUG] No recent chunks to process for volume")
    except Exception as e:
        print(f"Error in Volume reporting: {e}")

def track_volume(chunk, window_seconds):
    rms = np.sqrt(np.mean(np.square(chunk)))
    db = 20 * np.log10(rms + 1e-12) # 1e-12 avoids log(0)
    # Consider computing peak dbs 
    # print(f"Number of chunks: {len(chunk)}")
    print(f"Volume in the past {window_seconds} seconds: {db:.2f} dB")

def track_volume_average(start_time):
    """ This code is repeated in track_volume, find a way to reduce redundancy 
        - the concatenation 
        - the rms and db calculation 
        - the print statement 
    """
    with audio_chunks_lock:
        if not all_audio_chunks:
            print("No audio samples collected yet")
            return 

        # Concatenate all audio chunks into a single array
        all_audio = np.concatenate([chunk for chunk, ts in all_audio_chunks])

    rms = np.sqrt(np.mean(np.square(all_audio)))
    db = 20 * np.log10(rms + 1e-12)
    print(f"Average volume: {db:.2f} dBFS")

def main():
    
    # Start the transcription, WPM and volume reporter threads 
    # - each thread runs the target function in the background
    # - daemon=True means the thread will continue running even if the main thread exits
    threading.Thread(target=stream_transcribe, daemon=True).start()
    threading.Thread(target=report_wpm, args=(WPM_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=report_volume, args=(VOLUME_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=report_pitch_stdev, args=(PITCH_WINDOW_SECONDS,), daemon=True).start()

    # Start the audio stream
    # - callback is the function that will be called when it has captured a new chunk of audio
    # - dtype="float32" for higher precision
    # - samplerate is how many times the audio is captured per second (16000 is the default for whisper)
    # - channels is the number of audio channels (1 for mono, 2 for stereo)
    # - with keyword ensures the audio stream is closed when the block exits
    with sd.InputStream(callback=callback, dtype="float32", samplerate=SAMPLE_RATE, channels=1, device=device_id): # device=BLACKHOLE_INPUT redirects output to microphone
        source = "blackHole" if device_id == BLACKHOLE_ID else "microphone"
        print(f"Recording from {source} (Ctrl+C to stop)")
        start_time = time.time()

        try:
            while True:
                time.sleep(1) # The main thread will (idefinitely) sleep for 1 second until interrupted (Ctrl + C)
        except KeyboardInterrupt:
            print("Recording stopped.\n")
            print(f"Final transcription: \n {' '.join(text for text, ts in accumulated).strip()} \n")
            track_wpm_average(start_time)
            track_volume_average(start_time)
            track_overall_pitch_stdev(start_time, SAMPLE_RATE)
            print("\n")

if __name__ == "__main__":
    main()