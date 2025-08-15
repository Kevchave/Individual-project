import threading 
import numpy as np 
import librosa 
from collections import deque
import time

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

        # Session timing
        self.session_start_time = None
        self.session_end_time = None

        # Live metrics
        self.current_wpm = 0
        self.current_volume = 0
        self.current_pitch = 0
        self.current_chunk_duration = 0

        # Average metrics 
        self.average_wpm = 0
        self.average_volume = 0
        self.average_pitch = 0

        # Rolling‑window histories for smoothing
        self.window_size = window_size
        self.wpm_history = deque(maxlen = window_size)
        self.vol_history = deque(maxlen = window_size)
        self.pitch_history = deque(maxlen = window_size)
        self.chunk_duration_history = deque(maxlen=window_size)

        # Polled metrics for dashboard graphs (matches live experience)
        self.polled_wpm_history = []
        self.polled_volume_history = []
        self.polled_pitch_history = []
        self.polled_timestamps = []
        self.polled_data_lock = threading.Lock()

        # Insider metrics for database storage (chunk-level data)
        # These store the confidence and silence ratio for each individual chunk
        # This is separate from the rolling averages used for adaptive control
        self.chunk_confidence_scores = []  # List of confidence scores (one per chunk)
        self.chunk_silence_ratios = []     # List of silence ratios (one per chunk)
        self.insider_metrics_lock = threading.Lock()  # Thread safety for insider metrics

    # ------------------- Chunk Duration Tracking -------------------
    def track_chunk_duration(self, duration):
        self.chunk_duration_history.append(duration)
        self.current_chunk_duration = float(np.mean(self.chunk_duration_history))

    # ------------------- Session Timing -------------------
    def start_session(self):
        """Mark the start of a recording session"""
        self.session_start_time = time.time()
        print(f"[SESSION] Started at {self.session_start_time}")

    def end_session(self):
        """Mark the end of a recording session"""
        self.session_end_time = time.time()
        print(f"[SESSION] Ended at {self.session_end_time}")

    def get_session_duration(self):
        """Get the total session duration in seconds"""
        if self.session_start_time is None:
            return 0
        end_time = self.session_end_time if self.session_end_time else time.time()
        return end_time - self.session_start_time

    # ------------------- Text Tracking -------------------
    def add_transcription(self, text, duration):
        with self.accumulated_lock:
            self.accumulated.append((str(text).strip(), duration))
        self.track_chunk_duration(duration)

    # ------------------- Audio Tracking -------------------
    def add_audio_chunk(self, audio_float, duration):
        with self.audio_chunks_lock:
            self.all_audio_chunks.append((audio_float, duration))

    def get_last_audio_chunk(self):
        with self.audio_chunks_lock:

            # Return the audio_float of the last chunk
            return self.all_audio_chunks[-1][0] if self.all_audio_chunks else None

    # ------------------- Insider Metrics Storage -------------------
    def add_chunk_insider_metrics(self, silence_ratio, confidence):
        """
        Store insider metrics for database storage.
        This method is called from the transcriber for each chunk.
        
        Args:
            silence_ratio (float): Ratio of silence in the chunk (0-1)
            confidence (float): Transcription confidence score (0-1)
        """
        with self.insider_metrics_lock:
            # Store the silence ratio for this chunk
            # This will be saved to the database at session end
            self.chunk_silence_ratios.append(float(silence_ratio))
            
            # Store the confidence score for this chunk
            # This will be saved to the database at session end
            self.chunk_confidence_scores.append(float(confidence))
            
            print(f"[INSIDER STORAGE] Stored chunk metrics: silence_ratio={silence_ratio:.3f}, confidence={confidence:.3f}")
            print(f"[INSIDER STORAGE] Total stored: {len(self.chunk_silence_ratios)} silence ratios, {len(self.chunk_confidence_scores)} confidence scores")

    # ------------------------------------------------------------------------------------------------
    # Helper Functions 
    # ------------------------------------------------------------------------------------------------
    def _rms_to_db(self, samples):
        rms = np.sqrt(np.mean(np.square(samples)))
        return 20 * np.log10(rms + 1e-12)


    # ------------------- WPM Tracking -------------------
    def track_wpm(self):
        with self.accumulated_lock:
            if not self.accumulated:
                print("[DEBUG] No transcriptions to process for WPM")
                return
            text, duration = self.accumulated[-1]
        # print(f"[DEBUG] \n Text: {text} \n NumWords: {len(text.split())} \n Duration: {duration}")
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

    # ------------------- Volume Tracking -------------------
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
    
    # ------------------- Pitch Tracking -------------------
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

    # ------------------- Debug/Terminal Output -------------------
    def print_ui_metrics_summary(self):
        """Print UI metrics summary to terminal"""
        print(f"[UI METRICS] WPM: {self.current_wpm:.2f} | Volume: {self.current_volume:.2f} dB | Pitch: {self.current_pitch:.2f} Hz | Chunk Duration: {self.current_chunk_duration:.2f}s")

    # ------------------- Polled Metrics Storage -------------------
    def store_polled_metrics(self):
        """Store current smoothed metrics for dashboard graphs (called during polling)"""
        with self.polled_data_lock:
            print(f"[DEBUG] Storing polled metrics - WPM: {self.current_wpm:.2f}, Volume: {self.current_volume:.2f}, Pitch: {self.current_pitch:.2f}")
            self.polled_wpm_history.append(float(self.current_wpm))
            self.polled_volume_history.append(float(self.current_volume))
            self.polled_pitch_history.append(float(self.current_pitch))
            self.polled_timestamps.append(time.time())
            print(f"[DEBUG] Polled data stored. Total points: {len(self.polled_wpm_history)}")
            print(f"[DEBUG] Timestamps: {[f'{t:.1f}' for t in self.polled_timestamps]}")



    def get_polled_graph_data(self):
        """Return polled metrics data for dashboard graphs (matches live experience exactly)"""
        with self.polled_data_lock:
            if not self.polled_timestamps:
                return {
                    'wpm_data': [],
                    'volume_data': [],
                    'pitch_data': [],
                    'timestamps': [],
                    'session_duration': float(self.get_session_duration()),
                    'total_data_points': 0
                }
            
            # Convert timestamps to relative seconds from session start
            start_time = self.polled_timestamps[0] if self.polled_timestamps else 0
            relative_timestamps = [float(t - start_time) for t in self.polled_timestamps]
            
            return {
                'wpm_data': [float(x) for x in self.polled_wpm_history],
                'volume_data': [float(x) for x in self.polled_volume_history],
                'pitch_data': [float(x) for x in self.polled_pitch_history],
                'timestamps': relative_timestamps,
                'session_duration': float(self.get_session_duration()),
                'total_data_points': len(self.polled_wpm_history)
            }

    def get_session_summary(self):
        """Return complete session data for database storage"""
        print("[DEBUG] get_session_summary() called")
        
        # Calculate final averages
        self.track_wpm_average()
        self.track_volume_average()
        self.track_overall_pitch()
        
        # Get metrics data for storage
        metrics_data = self.get_metrics_data_for_storage()
        print(f"[DEBUG] get_metrics_data_for_storage returned {len(metrics_data)} chunks")
        
        session_summary = {
            'session_start_time': self.session_start_time,
            'session_end_time': self.session_end_time,
            'total_duration': float(sum(duration for _, duration in self.accumulated)),
            'total_words': int(sum(len(text.split()) for text, _ in self.accumulated)),
            'final_transcript': ' '.join(text for text, _ in self.accumulated),
            'average_metrics': {
                'wpm': float(self.average_wpm),
                'volume': float(self.average_volume),
                'pitch': float(self.average_pitch)
            },
            'graph_data': self.get_polled_graph_data(),
            'metrics_data': metrics_data
        }
        
        print(f"[DEBUG] Session summary created with keys: {list(session_summary.keys())}")
        print(f"[DEBUG] metrics_data in summary: {len(session_summary['metrics_data'])} chunks")
        
        return session_summary

    def get_metrics_data_for_storage(self):
        """Return metrics data formatted for database storage"""
        print("[DEBUG] get_metrics_data_for_storage() called")
        
        metrics_data = []
        
        print(f"[DEBUG] polled_wpm_history: {len(self.polled_wpm_history)}")
        print(f"[DEBUG] polled_volume_history: {len(self.polled_volume_history)}")
        print(f"[DEBUG] polled_pitch_history: {len(self.polled_pitch_history)}")
        print(f"[DEBUG] polled_timestamps: {len(self.polled_timestamps)}")
        print(f"[DEBUG] accumulated chunks: {len(self.accumulated)}")
        print(f"[DEBUG] chunk_confidence_scores: {len(self.chunk_confidence_scores)}")
        print(f"[DEBUG] chunk_silence_ratios: {len(self.chunk_silence_ratios)}")
        
        # Check if we have enough polled data
        if len(self.polled_timestamps) < 2:
            print("[DEBUG] WARNING: Very few polled data points. Session might be too short.")
            print("[DEBUG] Consider using chunk-level data for short sessions.")
        
        # Use chunk-level data if we have insider metrics available
        # This gives us text, confidence scores, and silence ratios
        if len(self.accumulated) > 0 and len(self.chunk_confidence_scores) > 0:
            print("[DEBUG] Using chunk-level data with insider metrics")
            session_start = self.session_start_time or 0
            cumulative_time = 0
            
            for i, (text, duration) in enumerate(self.accumulated):
                metric = {
                    'text': text,
                    'duration': float(duration),
                    'timestamp': float(cumulative_time),
                    'wpm': None,  # Will be filled from polled data if available
                    'volume': None,  # Will be filled from polled data if available
                    'pitch': None,  # Will be filled from polled data if available
                    'confidence': float(self.chunk_confidence_scores[i]) if i < len(self.chunk_confidence_scores) else None,
                    'silence_ratio': float(self.chunk_silence_ratios[i]) if i < len(self.chunk_silence_ratios) else None
                }
                
                # Try to match with polled metrics data for WPM, volume, pitch
                if i < len(self.polled_wpm_history):
                    metric['wpm'] = float(self.polled_wpm_history[i])
                if i < len(self.polled_volume_history):
                    metric['volume'] = float(self.polled_volume_history[i])
                if i < len(self.polled_pitch_history):
                    metric['pitch'] = float(self.polled_pitch_history[i])
                
                metrics_data.append(metric)
                cumulative_time += duration
                
        else:
            print("[DEBUG] Using polled data (no insider metrics available)")
            # Use polled data (rolling averages) instead of chunk-level data
            # This makes metrics_data similar to graph_data but in database table format
            for i in range(len(self.polled_timestamps)):
                metric = {
                    'text': '',  # No text for polled data points
                    'duration': 0,  # No duration for polled data points
                    'timestamp': float(self.polled_timestamps[i] - self.polled_timestamps[0]) if self.polled_timestamps else 0,
                    'wpm': float(self.polled_wpm_history[i]) if i < len(self.polled_wpm_history) else None,
                    'volume': float(self.polled_volume_history[i]) if i < len(self.polled_volume_history) else None,
                    'pitch': float(self.polled_pitch_history[i]) if i < len(self.polled_pitch_history) else None,
                    'confidence': None,  # Not available in polled data
                    'silence_ratio': None  # Not available in polled data
                }
                
                metrics_data.append(metric)
        
        print(f"[DEBUG] Created {len(metrics_data)} metric entries")
        if len(metrics_data) > 0:
            print(f"[DEBUG] Sample metric entry: {metrics_data[0]}")
            if len(metrics_data) > 1:
                print(f"[DEBUG] Last metric entry: {metrics_data[-1]}")
        
        return metrics_data

    def reset_session_data(self):
        """Reset all session data (useful for new sessions)"""
        with self.polled_data_lock:
            self.polled_wpm_history.clear()
            self.polled_volume_history.clear()
            self.polled_pitch_history.clear()
            self.polled_timestamps.clear()
        
        # Clear insider metrics data for new session
        with self.insider_metrics_lock:
            self.chunk_confidence_scores.clear()
            self.chunk_silence_ratios.clear()
        
        self.session_start_time = None
        self.session_end_time = None
        print("[SESSION] Session data reset")