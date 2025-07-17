import whisper
import numpy as np
import webrtcvad
import time

MODEL_SIZE = "small"
DEVICE = "cpu"

class Transcriber: 
    # Constructor to initialize the audio stream
    # - self is always the first argument in a method in a class
    def __init__(self, model_size, device):
        self.model = whisper.load_model(model_size, device=device)
        self.device = device

    def transcribe_stream(self, audio_queue, on_transcription, on_audio_chunk):
        vad = webrtcvad.Vad(1)      # Aggressiveness: 0-3
        sample_rate = 16000         # Must match AudioStream 
        frame_duration_ms = 20      # 10, 20, or 30ms
        frame_size = int(sample_rate * frame_duration_ms / 1000) # Samples per frame 

        speech_frames = []          # Store speech segments
        silence_counter = 0         # Counts consecutive silence frames 
        max_silence_frames = 5     # Number of silent frames for a speech segment to be over 

        buffer = np.empty((0,), dtype=np.int16)     # Holds incoming audio until we have a full frame

        while True: 
            # print("Transcription loop running") DEBUGGING STATEMENT
            pcm = audio_queue.get()
            buffer = np.concatenate((buffer, pcm))

            # As long as have enough audio for a full frame, process it
            while len(buffer) >= frame_size:
                frame = buffer[:frame_size]
                buffer = buffer[frame_size:]

                frame_bytes = frame.tobytes()
                is_speech = vad.is_speech(frame_bytes, sample_rate)
                # print("VAD decision:", is_speech) DEBUGGING STATEMENT

                if is_speech: 
                    speech_frames.append(frame)
                    silence_counter = 0 
                else : 
                    silence_counter += 1
                    if silence_counter > max_silence_frames:
                        if speech_frames:
                            segment = np.concatenate(speech_frames)
                            audio_float = segment.astype(np.float32) / 32767.0
                            
                            # true audio duration in seconds:
                            segment_duration = len(segment) / sample_rate

                            if on_audio_chunk: 
                                on_audio_chunk(audio_float, segment_duration)

                            result = self.model.transcribe(
                                audio_float, 
                                fp16=(self.device != "cpu"), 
                                language="en"   
                            )

                            if on_transcription: 
                                on_transcription(result["text"], segment_duration)
                        
                        speech_frames = []
                        silence_counter = 0

    # Function to transcribe the audio data in real-time
    # - is called as soon as soon as the stream is started
    # - on_transcription and on_audio_chunk are functions, passed as arguments 
    # def transcribe_stream(self, audio_queue, chunk_samples, on_transcription, on_audio_chunk):
    #     buffer = np.empty((0,), dtype=np.int16)

    #     while True:
    #         pcm = audio_queue.get()
    #         buffer = np.concatenate((buffer, pcm))

    #         if buffer.shape[0] >= chunk_samples:
    #             chunk, buffer = buffer[:chunk_samples], buffer[chunk_samples:]

    #             # Normalise the audio data to the range [-1, 1] for whisper model
    #             audio_float = chunk.astype(np.float32) / 32767.0

    #             # Callback for metrics (e.g., volume, pitch)
    #             if on_audio_chunk: # Checks whether on_audio_chunk is not None (i.e. if it exists)
    #                 on_audio_chunk(audio_float)

    #             # Transcribe the audio data
    #             # - returns a dictionary 
    #             # - fp16=(DEVICE!="cpu") means use fp16 (half-precision) for faster inference on GPU
    #             result = self.model.transcribe(
    #                 audio_float,
    #                 fp16=(self.device!="cpu"),
    #                 language="en"
    #             )

    #             # Prints the value with the key "text" in the dictionary 
    #             if on_transcription:
    #                 on_transcription(result["text"])