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

    def transcribe_stream(self, audio_queue, on_transcription, on_audio_chunk, track_insider_metrics=None, 
                         aggressiveness=3, frame_duration_ms=20, max_silence_frames=5):
        """
        Transcribe audio stream with optional insider metrics tracking for adaptive chunking.
        """

        # Configures a VAD object with configurable aggressiveness
        vad = webrtcvad.Vad(aggressiveness)
        sample_rate = 16000         # Must match AudioStream 
        frame_size = int(sample_rate * frame_duration_ms / 1000) # Samples per frame 

        speech_frames = []          # Store speech segments
        silence_counter = 0         # Counts consecutive silence frames 

        buffer = np.empty((0,), dtype=np.int16)     # Holds incoming audio until we have a full frame

        # Frame counting for current chunk (for insider metrics)
        chunk_silence_frames = 0
        chunk_total_frames = 0

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

                # Track frames for current chunk (for insider metrics)
                if track_insider_metrics is not None:
                    chunk_total_frames += 1
                    if not is_speech:
                        chunk_silence_frames += 1

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

                            # Calculate chunk-level metrics for insider tracking
                            if track_insider_metrics is not None:
                                # Calculate silence ratio for this chunk
                                chunk_silence_ratio = chunk_silence_frames / chunk_total_frames if chunk_total_frames > 0 else 0.0
                                track_insider_metrics.add_chunk_silence_ratio(chunk_silence_ratio)
                                
                                # Calculate confidence for this chunk
                                confidence = self._extract_confidence(result)
                                track_insider_metrics.add_confidence(confidence)
                                
                                # Reset frame counters for next chunk
                                chunk_silence_frames = 0
                                chunk_total_frames = 0

                            if on_transcription:
                                on_transcription(result["text"], segment_duration)
                      
                            # # Print summary (aligned with UI metrics timing)
                            # if track_insider_metrics is not None:
                            #     track_insider_metrics.print_summary()

                        speech_frames = []
                        silence_counter = 0

    def _extract_confidence(self, result):
        """Extract confidence score from Whisper transcription result"""
        try:
            # Whisper returns segments with confidence scores
            if "segments" in result and result["segments"]:
                # Get the average confidence across all segments
                confidences = [segment.get("avg_logprob", 0) for segment in result["segments"]]
                if confidences:
                    # Convert log probability to confidence (0-1 scale)
                    # avg_logprob is typically negative, so we need to convert it
                    avg_logprob = np.mean(confidences)
                    # Convert log probability to probability, then to confidence
                    confidence = np.exp(avg_logprob)
                    return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
            
            # Fallback: if no segments or confidence data, return a default
            return 0.5
        except Exception as e:
            print(f"Error extracting confidence: {e}")
            return 0.5