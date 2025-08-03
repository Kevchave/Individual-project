import numpy as np
from pydub import AudioSegment

class AudioLoader:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
    
    def load_audio(self, file_path):
        """Load audio file and convert to required format"""

        # Load the audio file using pydub.AudioSegment
        audio = AudioSegment.from_file(str(file_path))
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Resample to target sample rate
        if audio.frame_rate != self.sample_rate:
            audio = audio.set_frame_rate(self.sample_rate)
        
        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples())
        
        # Convert to float32 (normalized to [-1, 1])
        if audio.sample_width == 2:  # 16-bit
            samples = samples.astype(np.float32) / 32768.0
        else:
            samples = samples.astype(np.float32) / 32768.0
        
        return samples
    
    def convert_to_int16(self, audio_samples):
        """Convert float32 samples to int16 for transcription queue"""
        return (audio_samples * 32767).astype(np.int16) 