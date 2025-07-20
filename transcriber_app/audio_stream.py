import numpy as np
import queue
import sounddevice as sd

class AudioStream:
    # Constructor to initialize the audio stream
    # - self is always the first argument in a method in a class
    def __init__(self, sample_rate, device_id):
        self.audio_queue = queue.Queue()
        self.sample_rate = sample_rate
        self.device_id = device_id
        self.stream = None; 

    # Callback function -> called every time a chunk of audio is ready
    # - indata: Numpy array of shape (frames, channels) containing the audio data
    # - status: Error/status flags
    def callback(self, indata, frames, time_info, status):
        # print("Audio callback fired, frames:", frames) DEBUGGING STATEMENT
        if status: 
            print("Mic error: ", status)

        # Convert audio data (first channel) to 16-bit PCM format
        pcm = (indata[:, 0] * 32767).astype(np.int16) 
        
        # Put the audio data into the queue
        self.audio_queue.put(pcm) 

    def start(self):
        if self.stream is None: 
            self.stream = sd.InputStream(
                callback=self.callback, 
                dtype="float32", 
                samplerate=self.sample_rate, 
                channels=1, 
                device=self.device_id, 
                blocksize=480
            )
            self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def pause(self):
        # .active is a flag in sd.InputStream
        if self.stream is not None and self.stream.active: 

            # .stop() suspends callbacks, but doesnt close the stream object 
            self.stream.stop()

    def resume(self):
        if self.stream is not None and not self.stream.active: 

            # .start() re-enables callbacks, but doesnt re-open the device 
            self.stream.start()