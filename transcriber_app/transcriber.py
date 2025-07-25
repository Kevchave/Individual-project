import whisper
import numpy as np
import webrtcvad 

MODEL_SIZE = "small"
DEVICE = "cpu"

class Transcriber: 
    # Constructor to initialize the audio stream
    # - self is always the first argument in a method in a class
    def __init__(self, model_size, device):
        self.model = whisper.load_model(model_size, device=device)
        self.device = device

    def transcribe_stream(self, audio_queue, on_transcription, on_audio_chunk):
        
        # Configures a VAD object
        vad = webrtcvad.Vad(3)      # Aggressiveness: 0-3
        sample_rate = 16000         # Must match AudioStream 
        frame_duration_ms = 20      # 10, 20, or 30ms
        frame_size = int(sample_rate * frame_duration_ms / 1000) # Samples per frame 

        speech_frames = []          # Store speech segments
        silence_counter = 0         # Counts consecutive silence frames 
        max_silence_frames = 5      # Number of silent frames for a speech segment to be over 

        buffer = np.empty((0,), dtype=np.int16)     # Holds incoming audio until we have a full frame

        while True: 
            # print("Transcription loop running") DEBUGGING STATEMENT
            pcm = audio_queue.get()

            # If the audio_stream stops, break the thread 
            if pcm is None: 
                break;

            buffer = np.concatenate((buffer, pcm))        

            # Once buffer is long enough, process it
            while len(buffer) >= frame_size:
                frame = buffer[:frame_size]
                buffer = buffer[frame_size:]

                frame_bytes = frame.tobytes()
                is_speech = vad.is_speech(frame_bytes, sample_rate)
                # print("VAD decision:", is_speech) DEBUGGING STATEMENT

                if is_speech: 
                    speech_frames.append(frame)
                    # if silence_counter > 0:
                        # print(f"[DEBUG] Resetting silence_counter from {silence_counter} to 0 (speech detected)")
                    silence_counter = 0 
                else : 
                    silence_counter += 1
                    # print(f"[DEBUG] Silence frame detected. silence_counter={silence_counter}")
                    if silence_counter > max_silence_frames:
                        if speech_frames:
                            # print(f"[DEBUG] Finalizing segment. silence_counter={silence_counter}, segment_frames={len(speech_frames)}, segment_duration={len(np.concatenate(speech_frames))/sample_rate:.2f}s")
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
                        # else:
                        #     print(f"[DEBUG] silence_counter={silence_counter} but no speech_frames to finalize.")
                        speech_frames = []
                        silence_counter = 0