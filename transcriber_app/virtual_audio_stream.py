import numpy as np
import queue
import threading
import time
from pathlib import Path

class VirtualAudioStream:
    """
    Virtual audio stream that injects pre-recorded audio into the transcription pipeline.
    Mimics the AudioStream interface but feeds audio from a file instead of microphone.
    """
    
    def __init__(self, sample_rate=16000):
        self.audio_queue = queue.Queue()
        self.sample_rate = sample_rate
        self.stream = None
        self.audio_thread = None
        self.is_playing = False
        self.audio_data = None
        self.chunk_size = 480  # Same as original AudioStream blocksize
        
    def load_audio_file(self, audio_file_path):
        """Load audio file and prepare it for streaming"""
        import soundfile as sf
        
        # Load audio file
        audio_data, file_sample_rate = sf.read(audio_file_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
        
        # Resample if necessary
        if file_sample_rate != self.sample_rate:
            from scipy import signal
            audio_data = signal.resample(audio_data, 
                                       int(len(audio_data) * self.sample_rate / file_sample_rate))
        
        # Convert to 16-bit PCM format (same as original AudioStream)
        self.audio_data = (audio_data * 32767).astype(np.int16)
        
        print(f"Loaded audio: {len(self.audio_data)} samples, {len(self.audio_data)/self.sample_rate:.2f}s")
        return self.audio_data
    
    def _stream_audio(self):
        """Internal method to stream audio chunks in a separate thread"""
        if self.audio_data is None:
            print("No audio data loaded")
            return
            
        position = 0
        while self.is_playing and position < len(self.audio_data):
            # Get next chunk
            end_position = min(position + self.chunk_size, len(self.audio_data))
            chunk = self.audio_data[position:end_position]
            
            # Pad with zeros if chunk is smaller than expected
            if len(chunk) < self.chunk_size:
                chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)), 'constant')
            
            # Put chunk in queue (same interface as AudioStream)
            self.audio_queue.put(chunk)
            
            position = end_position
            
            # Simulate real-time streaming (optional - can be disabled for faster testing)
            time.sleep(len(chunk) / self.sample_rate)
        
        # Signal end of stream
        self.audio_queue.put(None)
        print("Virtual audio stream finished")
    
    def start(self):
        """Start streaming audio (mimics AudioStream.start())"""
        if self.audio_data is None:
            raise ValueError("No audio data loaded. Call load_audio_file() first.")
        
        if not self.is_playing:
            self.is_playing = True
            self.audio_thread = threading.Thread(target=self._stream_audio, daemon=True)
            self.audio_thread.start()
            print("Virtual audio stream started")
    
    def stop(self):
        """Stop streaming audio (mimics AudioStream.stop())"""
        self.is_playing = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)
        print("Virtual audio stream stopped")
    
    def pause(self):
        """Pause streaming (mimics AudioStream.pause())"""
        self.is_playing = False
        print("Virtual audio stream paused")
    
    def resume(self):
        """Resume streaming (mimics AudioStream.resume())"""
        if self.audio_data is not None and not self.is_playing:
            self.start()
    
    def get_remaining_audio_duration(self):
        """Get remaining audio duration in seconds"""
        if self.audio_data is None:
            return 0
        return len(self.audio_data) / self.sample_rate 