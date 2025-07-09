import threading 
import time
import numpy as np 
import librosa 

class MetricsTracker: 
    # Constructor to initialize the metrics tracker
    # - self is always the first argument in a method in a class
    def __init__(self, sample_rate):
        self.accumulated = [] # (text, timestamp) tuples
        self.accumulated_lock = threading.Lock()
        self.all_audio_chunks = [] # (audio_float, timestamp) tuples
        self.audio_chunks_lock = threading.Lock()
        self.sample_rate = sample_rate 
        self.current_wpm = 0
        self.current_volume = 0
        self.current_pitch = 0
        self.average_wpm = 0
        self.average_volume = 0
        self.average_pitch = 0

    def add_transcription(self, text):
        with self.accumulated_lock:
            self.accumulated.append((str(text).strip(), time.time()))

    def add_audio_chunk(self, audio_float):
        with self.audio_chunks_lock:
            self.all_audio_chunks.append((audio_float, time.time()))

    # WPM TRACKING

    # def report_wpm(self, window_seconds):
    #     try:
    #         while True: 
    #             time.sleep(window_seconds)
    #             self.track_wpm(window_seconds)
    #     except Exception as e:
    #         print(f"Error in WPM reporting: {e}")

    def track_wpm(self, window_seconds):
        now = time.time()
        with self.accumulated_lock:
            # Takes every text, where ts (timestamp) is within the last window_seconds 
            recent_texts = [text for text, ts in self.accumulated if ts >= now - window_seconds]
        text = " ".join(recent_texts)
        elapsed_time =  window_seconds / 60 # In minutes
        wpm = len(text.split()) / elapsed_time if elapsed_time > 0 else 0
        self.current_wpm = wpm
        # print(f"WPM (last {window_seconds} seconds): {wpm:.2f}")

    def track_wpm_average(self, start_time):
        with self.accumulated_lock:
            all_text = " ".join(text for text, ts in self.accumulated)
        total_words = len(all_text.split()) # .split() splits into a list of words 
        elapsed_time = (time.time() - start_time) / 60 # In minutes
        avg_wpm = total_words / elapsed_time if elapsed_time > 0 else 0 
        self.average_wpm = avg_wpm
        # print(f"Elapsed time: {elapsed_time}")
        # print(f"Total words: {total_words}")
        # print(f"Average WPM: {avg_wpm:.2f}")

    # VOLUME TRACKING
        
    # def report_volume(self, window_seconds):
    #     try:
    #         while True:
    #             time.sleep(window_seconds)
    #             now = time.time()
    #             self.track_volume(window_seconds)
    #     except Exception as e:
    #         print(f"Error in Volume reporting: {e}")

    def track_volume(self, window_seconds):
        with self.audio_chunks_lock:
                # Only keep chunks that are within the last window_seconds 
                recent_chunks = [chunk for chunk, ts in self.all_audio_chunks if ts >= time.time() - window_seconds]
        if not recent_chunks:
            print("[DEBUG] No recent chunks to process for volume")
            return
        else:
            # Concatenate the recent chunks into a single array 
            recent_audio = np.concatenate(recent_chunks) 

        rms = np.sqrt(np.mean(np.square(recent_audio)))
        db = 20 * np.log10(rms + 1e-12) # 1e-12 avoids log(0)
        # Consider computing peak dbs 
        # print(f"Number of chunks: {len(chunk)}")
        self.current_volume = db
        # print(f"Volume (last{window_seconds} seconds): {db:.2f} dB")

    def track_volume_average(self, start_time):
        """ This code is repeated in track_volume, find a way to reduce redundancy 
            - the concatenation 
            - the rms and db calculation 
            - the print statement 
        """
        with self.audio_chunks_lock:
            if not self.all_audio_chunks:
                print("No audio samples collected yet")
                return 
            # Concatenate all audio chunks into a single array
            all_audio = np.concatenate([chunk for chunk, ts in self.all_audio_chunks])
        
        rms = np.sqrt(np.mean(np.square(all_audio)))
        db = 20 * np.log10(rms + 1e-12)
        self.average_volume = db
        # print(f"Average volume: {db:.2f} dBFS")
    
    # PITCH TRACKING
    
    # def report_pitch(self, window_seconds):
    #     try: 
    #         while True: 
    #             time.sleep(window_seconds)
    #             self.track_pitch(window_seconds)
    #     except Exception as e:
    #         print(f"Error in Pitch reporting: {e}")
            
    def track_pitch(self, window_seconds):
        now = time.time()
        with self.audio_chunks_lock:
            # Only keep chunks that are within the last window_seconds 
            recent_chunks = [chunk for chunk, ts in self.all_audio_chunks if ts >= now - window_seconds]

        if not recent_chunks:
            print("Pitch Variance: No audio chunks to process")
            return 
        
        y = np.concatenate(recent_chunks)

        # f0 is fundamental frequency (pitch of the audio)
        # - pyin estimate the pitch of the audio, and the probability that the frame is voiced 
        # - frame_length is the number of samples in each frame
        # - hop_length is the number of samples to advance between frames
        # - each estimate is still made from x samples, but only slightly shifted
        f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=75, fmax=800, sr=self.sample_rate, frame_length=2048, hop_length=256)

        # Confidence threshold for voiced frames
        mask = (voiced_flag) & (voiced_prob >= 0.1)
        voiced = f0[mask]

        if len(voiced) == 0:
            print("Pitch Variance: No voice audio detected")
            return 
        
        # print(f"  Frames: {len(f0)}, Voiced frames: {len(voiced)}")
        # print(f"  f₀ min/max: {voiced.min():.1f}/{voiced.max():.1f} Hz")
        # print(f"  f₀ 5th/95th pct: {np.percentile(voiced, 5):.1f}/{np.percentile(voiced,95):.1f} Hz")

        # iqr = np.percentile(voiced, 75) - np.percentile(voiced, 25)
        std_dev_pitch = float(np.std(voiced))
        self.current_pitch = std_dev_pitch
        # print(f"Pitch Variance (last {window_seconds} seconds): {std_dev_pitch:.2f} Hz")

    def track_overall_pitch(self, start_time):
        with self.audio_chunks_lock:
            y = np.concatenate([chunk for chunk, ts in self.all_audio_chunks])

        f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=75, fmax=800, sr=self.sample_rate, frame_length=2048, hop_length=256)
        mask = (voiced_flag) & (voiced_prob >= 0.1)
        voiced = f0[mask]

        if len(voiced) == 0:
            print("Pitch Variance: No voice audio detected")
            return 

        std_dev_pitch = float(np.std(voiced))
        self.average_pitch = std_dev_pitch
        # print(f"Overall Pitch Variance: {std_dev_pitch:.2f} Hz")




    