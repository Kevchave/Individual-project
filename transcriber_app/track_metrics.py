import threading 
import numpy as np 
import librosa 
from collections import deque

class MetricsTracker: 
    # Constructor to initialize the metrics tracker
    # - self is always the first argument in a method in a class
    def __init__(self, sample_rate, window_size=10):
        # Raw data stores
        self.accumulated = [] # (text, timestamp) tuples
        self.accumulated_lock = threading.Lock()

        self.all_audio_chunks = [] # (audio_float, timestamp) tuples
        self.audio_chunks_lock = threading.Lock()
        self.sample_rate = sample_rate

        # Live metrics
        self.current_wpm = 0
        self.current_volume = 0
        self.current_pitch = 0

        # Average metrics 
        self.average_wpm = 0
        self.average_volume = 0
        self.average_pitch = 0

        # Rolling‑window histories for smoothing
        self.window_size = window_size
        self.wpm_history = deque(maxlen = window_size)
        self.vol_history = deque(maxlen = window_size)
        self.pitch_history = deque(maxlen = window_size)

    def add_transcription(self, text, duration):
        with self.accumulated_lock:
            self.accumulated.append((str(text).strip(), duration))

    def add_audio_chunk(self, audio_float, duration):
        with self.audio_chunks_lock:
            self.all_audio_chunks.append((audio_float, duration))

    def get_last_audio_chunk(self):
        with self.audio_chunks_lock:

            # Return the audio_float of the last chunk
            return self.all_audio_chunks[-1][0] if self.all_audio_chunks else None

    # ------------------------------------------------------------------------------------------------
    # Helper Functions 
    # ------------------------------------------------------------------------------------------------
    def _rms_to_db(self, samples):
        rms = np.sqrt(np.mean(np.square(samples)))
        return 20 * np.log10(rms + 1e-12)

    # ------------------------------------------------------------------------------------------------
    # WPM TRACKING
    # ------------------------------------------------------------------------------------------------
    def track_wpm(self):
        with self.accumulated_lock:
            if not self.accumulated:
                print("[DEBUG] No transcriptions to process for WPM")
                return
            text, duration = self.accumulated[-1]
        print(f"[DEBUG] \n Text: {text} \n NumWords: {len(text.split())} \n Duration: {duration}")
        wpm = len(text.split()) / (duration / 60) if duration > 0 else 0
        
        # Add 'wpm' into a deque list, then take the average
        self.wpm_history.append(wpm)
        self.current_wpm = float(np.mean(self.wpm_history))

    def track_wpm_average(self):
        with self.accumulated_lock:
            total_words = sum(len(text.split()) for text, duration in self.accumulated)
            total_duration = sum(duration for text, duration in self.accumulated)
        avg_wpm = total_words / (total_duration / 60) if total_duration > 0 else 0
        print(f"[FINAL] \n NumWords: {total_words} \n Duration: {total_duration}") 
        self.average_wpm = avg_wpm

    # ------------------------------------------------------------------------------------------------
    # VOLUME TRACKING
    # ------------------------------------------------------------------------------------------------
    def track_volume(self):
        chunk = self.get_last_audio_chunk()
        if chunk is None:
            print("[DEBUG] No audio chunk to process for VOLUME")
            return

        db = self._rms_to_db(chunk)

        # Add 'volume' into a deque list, then take the average
        self.vol_history.append(db)
        self.current_volume = float(np.mean(self.vol_history))

    def track_volume_average(self):
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
        db = self._rms_to_db(all_audio)
        self.average_volume = db
    
    # ------------------------------------------------------------------------------------------------
    # PITCH TRACKING
    # ------------------------------------------------------------------------------------------------
    def track_pitch(self):
        chunk = self.get_last_audio_chunk()
        if chunk is None:
            print("[DEBUG] No audio chunk to process for PITCH")
            return

        # f0 is fundamental frequency (pitch of the audio)
        # - pyin estimate the pitch of the audio, and the probability that the frame is voiced 
        # - frame_length is the number of samples in each frame
        # - hop_length is the number of samples to advance between frames
        # - each estimate is still made from x samples, but only slightly shifted
        f0, voiced_flag, voiced_prob = librosa.pyin(chunk, fmin=75, fmax=800, sr=self.sample_rate, frame_length=2048, hop_length=256)
        mask = (voiced_flag) & (voiced_prob >= 0.1)
        voiced = f0[mask]
        if len(voiced) == 0:
            print("Pitch Variance: No voice audio detected")
            return
        std_dev_pitch = float(np.std(voiced))

        # Add 'st_dev_pitch' into a deque list, then take the average
        self.pitch_history.append(std_dev_pitch)
        self.current_pitch = float(np.mean(self.pitch_history))

    def track_overall_pitch(self):
        with self.audio_chunks_lock:
            chunks = [chunk for chunk, _ in self.all_audio_chunks]
            if not chunks:
                return
            y = np.concatenate(chunks)
        f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=75, fmax=800, sr=self.sample_rate, frame_length=1024, hop_length=256)
        mask = (voiced_flag) & (voiced_prob >= 0.1)
        voiced = f0[mask]
        if len(voiced) == 0:
            print("Pitch Variance: No voice audio detected")
            return

        self.average_pitch = float(np.std(voiced))




    