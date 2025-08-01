from .audio_stream import AudioStream
from .transcriber import Transcriber
from .track_metrics import MetricsTracker
from .track_insider_metrics import TrackInsiderMetrics
from .adaptive_controller import AdaptiveController
import threading
import time

SAMPLE_RATE = 16000
CHUNK_SEC = 1.5
WPM_WINDOW_SECONDS = 6
VOLUME_WINDOW_SECONDS = 6
PITCH_WINDOW_SECONDS = 6

# Adaptive chunking configuration
VAD_AGGRESSIVENESS = 3      # 0-3, 0=more speech, 3=more silence
FRAME_DURATION_MS = 20      # 10, 20, or 30ms
MAX_SILENCE_FRAMES = 10      # Number of consecutive silence frames to end a speech segment

BLACKHOLE_ID = 3 # Redirects output to microphone
MIC_INPUT = None
device_id = MIC_INPUT   # or MIC_INPUT

audio_stream = None
transcriber = None
metrics = None
track_insider_metrics = None  # Optional insider metrics for adaptive chunking
adaptive_controller = None    # Adaptive controller for parameter tuning
transcription_thread = None
start_time = None

# Start the full pipeline: audio, transcription, metrics
def start_transcription_pipeline(device_id=MIC_INPUT, enable_insider_metrics=True, enable_adaptive_control=True, metrics_collector=None):
    global audio_stream, transcriber, metrics, track_insider_metrics, adaptive_controller, transcription_thread, start_time

    # Clear previous data if there exists
    if metrics is not None: 
        if hasattr(metrics, 'accumulated'):
            metrics.accumulated.clear()
        if hasattr(metrics, 'all_audio_chunks'):
            metrics.all_audio_chunks.clear()
    if track_insider_metrics is not None:
        track_insider_metrics.reset()
    if adaptive_controller is not None:
        adaptive_controller.reset()
    
    transcriber = None
    metrics = None 
    track_insider_metrics = None
    adaptive_controller = None
    transcription_thread = None
    
    # Create all objects
    if audio_stream is None:
        audio_stream = AudioStream(SAMPLE_RATE, device_id)
    if transcriber is None:
        transcriber = Transcriber("small", "cpu")
    if metrics is None:
        metrics = MetricsTracker(SAMPLE_RATE)
    if enable_insider_metrics and track_insider_metrics is None:
        track_insider_metrics = TrackInsiderMetrics()
    if enable_adaptive_control and adaptive_controller is None:
        adaptive_controller = AdaptiveController()

    def run_transcription():
        if audio_stream is not None:
            audio_stream.start()
            if transcriber is not None:
                # Get current parameters from adaptive controller (or use defaults)
                if adaptive_controller is not None:
                    aggressiveness, frame_duration_ms, max_silence_frames = adaptive_controller.get_current_parameters()
                else:
                    aggressiveness, frame_duration_ms, max_silence_frames = VAD_AGGRESSIVENESS, FRAME_DURATION_MS, MAX_SILENCE_FRAMES
                
                transcriber.transcribe_stream(
                    audio_stream.audio_queue, 
                    on_transcription, 
                    on_audio_chunk, 
                    track_insider_metrics,
                    aggressiveness=aggressiveness,
                    frame_duration_ms=frame_duration_ms,
                    max_silence_frames=max_silence_frames,
                    metrics_collector=metrics_collector
                )

    # Safeguard to ensure exactly one background thread is active 
    if transcription_thread is None or not transcription_thread.is_alive():
        # Start a separate transcription thread 
        # - the transcription can now run without blocking the main thread (or program)
        transcription_thread = threading.Thread(target=run_transcription, daemon=True)
        transcription_thread.start()

# Stop the pipeline (implement as needed)
def stop_transcription_pipeline():
    global audio_stream, transcriber, metrics, track_insider_metrics, adaptive_controller, transcription_thread
    # You may need to add stop/cleanup logic to your classes
    if audio_stream is not None:
        audio_stream.stop()
        
        # Signals the transcription loop to exit
        audio_stream.audio_queue.put(None)

    if transcription_thread is not None:
        transcription_thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
        transcription_thread = None

    # Clean up stream handle
    audio_stream = None
    
    # Clear global references to help with garbage collection
    transcriber = None
    track_insider_metrics = None
    adaptive_controller = None
    
    # Note: We don't clear metrics here to preserve the transcript data
    # The metrics object will be cleaned up when the pipeline is restarted
    
    print("[CLEANUP] Transcription pipeline stopped and resources cleaned up")

def pause_transcription_pipeline():
    global audio_stream
    if audio_stream is not None: 
        audio_stream.pause()

def resume_transcription_pipeline():
    global audio_stream, transcription_thread
    if audio_stream is not None: 
        audio_stream.resume()

# Get the latest transcript
def get_current_transcript():
    global metrics
    if metrics is not None and hasattr(metrics, 'accumulated') and metrics.accumulated:
        # Return only the most recent transcription
        # - [-1] for the last tuple in the list (latest transcription)
        # - [0] for the first element of the tuple (the transcription text)
        return metrics.accumulated[-1][0]
    # Return an empty string if no transcription is available
    return ""

# Get the latest metrics
def get_current_metrics():
    global metrics
    if metrics is None:
        return {'wpm': 0, 'volume': 0, 'pitch': 0}
    return {
        'wpm': float(metrics.current_wpm),
        'volume': float(metrics.current_volume),
        'pitch': float(metrics.current_pitch)
    }

def get_final_transcript():
    global metrics
    if metrics is not None and hasattr(metrics, 'accumulated'):
        return ' '.join(text for text, ts in metrics.accumulated).strip()
    return ""

def get_average_metrics():
    global metrics

    # If we haven't initialized MetricsTracker yet, just zero‐fill.
    if metrics is None:
        return {
            'average_wpm':     0.0,
            'average_volume':  0.0,
            'average_pitch':   0.0
        }

    # Recompute the averages
    metrics.track_wpm_average()
    metrics.track_volume_average()
    metrics.track_overall_pitch()

    return {
        'average_wpm':     float(metrics.average_wpm),
        'average_volume':  float(metrics.average_volume),
        'average_pitch':   float(metrics.average_pitch)
    }

def get_adaptive_controller_status():
    """Get the current status of the adaptive controller"""
    global adaptive_controller
    if adaptive_controller is None:
        return None
    return adaptive_controller.get_status()

def main():
    # For manual testing: start the pipeline, print status, etc.
    start_transcription_pipeline()
    print("Transcription pipeline started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping pipeline...")
        stop_transcription_pipeline()
        print("Stopped.")

def on_transcription(text, segment_duration):
    global metrics, adaptive_controller, track_insider_metrics
    if metrics is not None:
        metrics.add_transcription(text, segment_duration)
        metrics.track_wpm()
        print(f"\nTranscription: {text}\n") 

        # Print UI metrics summary after WPM is updated
        metrics.print_ui_metrics_summary()
        
        # Print summary (aligned with UI metrics timing)
        if track_insider_metrics is not None:
            track_insider_metrics.print_summary()
        
        # Check if adaptive controller should adjust parameters
        if adaptive_controller is not None and track_insider_metrics is not None:
            # Get current metrics
            current_metrics = {
                'wpm': metrics.current_wpm,
                'volume': metrics.current_volume,
                'pitch': metrics.current_pitch,
                'chunk_duration': metrics.current_chunk_duration
            }
            
            insider_metrics = {
                'silence_ratio': track_insider_metrics.get_silence_ratio(),
                'confidence': track_insider_metrics.get_confidence()
            }
            
            # Check if parameters should be adjusted
            if adaptive_controller.should_adjust_parameters(current_metrics, insider_metrics):
                print(f"[ADAPTIVE] Metrics suggest parameter adjustment needed")
                print(f"[ADAPTIVE] Current metrics: WPM={current_metrics['wpm']:.1f}, "
                      f"Confidence={insider_metrics['confidence']:.3f}, "
                      f"Silence Ratio={insider_metrics['silence_ratio']:.3f}")
                
                # Calculate new parameters
                new_parameters = adaptive_controller.calculate_parameter_adjustments(current_metrics, insider_metrics)
                
                # Update parameters in adaptive controller
                if adaptive_controller.update_parameters(new_parameters):
                    print(f"[ADAPTIVE] Parameters updated successfully")
                    
                    # Send parameter updates to transcriber
                    if transcriber is not None:
                        transcriber.update_parameters(
                            new_parameters['aggressiveness'],
                            new_parameters['frame_duration_ms'],
                            new_parameters['max_silence_frames']
                        )

def on_audio_chunk(audio_float, segment_duration):
    global metrics
    if metrics is not None:
        # print("Audio chunk received, length:", len(audio_float)) DEBUGGING STATEMENT
        metrics.add_audio_chunk(audio_float, segment_duration)
        metrics.track_volume()
        metrics.track_pitch()
        # Note: UI metrics summary is printed in on_transcription to avoid duplicate output

if __name__ == "__main__":
    main()