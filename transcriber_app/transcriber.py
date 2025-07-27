import whisper
import numpy as np
import webrtcvad 
import queue

MODEL_SIZE = "small"
DEVICE = "cpu"

class Transcriber: 
    # Constructor to initialize the audio stream
    # - self is always the first argument in a method in a class
    def __init__(self, model_size, device):
        self.model = whisper.load_model(model_size, device=device)
        self.device = device
        
        # Parameter queue for adaptive updates
        self.parameter_queue = queue.Queue()
        self.current_aggressiveness = 3
        self.current_frame_duration_ms = 20
        self.current_max_silence_frames = 5

    def update_parameters(self, aggressiveness, frame_duration_ms, max_silence_frames):
        """
        Queue parameter updates to be applied at the next chunk boundary.
        """
        try:
            self.parameter_queue.put_nowait({
                'aggressiveness': aggressiveness,
                'frame_duration_ms': frame_duration_ms,
                'max_silence_frames': max_silence_frames
            })
            print(f"[TRANSCRIBER] Parameter update queued: Aggressiveness={aggressiveness}, "
                  f"Frame Duration={frame_duration_ms}ms, Max Silence Frames={max_silence_frames}")
        except queue.Full:
            print(f"[TRANSCRIBER] Warning: Parameter queue full, update dropped")

    def _apply_parameter_updates(self):
        """Apply any pending parameter updates."""
        try:
            while not self.parameter_queue.empty():
                new_params = self.parameter_queue.get_nowait()
                
                # Update current parameters
                self.current_aggressiveness = new_params['aggressiveness']
                self.current_frame_duration_ms = new_params['frame_duration_ms']
                self.current_max_silence_frames = new_params['max_silence_frames']
                
                print(f"[TRANSCRIBER] Parameters applied: Aggressiveness={self.current_aggressiveness}, "
                      f"Frame Duration={self.current_frame_duration_ms}ms, "
                      f"Max Silence Frames={self.current_max_silence_frames}")
                
        except queue.Empty:
            pass  # No updates to apply

    def transcribe_stream(self, audio_queue, on_transcription, on_audio_chunk, track_insider_metrics=None, 
                         aggressiveness=3, frame_duration_ms=20, max_silence_frames=5):
        """
        Transcribe audio stream with optional insider metrics tracking for adaptive chunking.
        """

        # Initialize current parameters
        self.current_aggressiveness = aggressiveness
        self.current_frame_duration_ms = frame_duration_ms
        self.current_max_silence_frames = max_silence_frames

        # Configures a VAD object with configurable aggressiveness
        vad = webrtcvad.Vad(self.current_aggressiveness)
        sample_rate = 16000         # Must match AudioStream 
        frame_size = int(sample_rate * self.current_frame_duration_ms / 1000) # Samples per frame 

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
                    if silence_counter > self.current_max_silence_frames:
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
                        
                        # Apply any pending parameter updates at chunk boundary
                        self._apply_parameter_updates()
                        
                        # Recreate VAD with new parameters if they changed
                        if hasattr(self, '_last_applied_aggressiveness') and self._last_applied_aggressiveness != self.current_aggressiveness:
                            vad = webrtcvad.Vad(self.current_aggressiveness)
                            self._last_applied_aggressiveness = self.current_aggressiveness
                            print(f"[TRANSCRIBER] VAD recreated with aggressiveness {self.current_aggressiveness}")
                        elif not hasattr(self, '_last_applied_aggressiveness'):
                            self._last_applied_aggressiveness = self.current_aggressiveness

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