import numpy as np
import queue
import sounddevice as sd

class AudioStream:
    def __init__(self, sample_rate, device_id):
        self.audio_queue = queue.Queue()
        self.sample_rate = sample_rate
        self.device_id = device_id

# Callback function that will be called for each chunk of audio
# - indata: Numpy array of shape (frames, channels) containing the audio data
# - frames: The number of frames in this chunk
# - time_info: Time info 
# - status: Error/status flags
    def callback(self, indata, frames, time_info, status):
        if status: 
            print("Mic error: ", status)
        pcm = (indata[:, 0] * 32767).astype(np.int16) # Convert audio data (first channel) to 16-bit PCM format
        self.audio_queue.put(pcm) # Put the audio data into the queue

    def start(self):
        return sd.InputStream(
            callback=self.callback, 
            dtype="float32", 
            samplerate=self.sample_rate, 
            channels=1, 
            device=self.device_id, 
        )