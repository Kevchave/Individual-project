from .audio_stream import AudioStream
from .transcriber import Transcriber
from .track_metrics import MetricsTracker
import threading
import time

SAMPLE_RATE = 16000
CHUNK_SEC = 1.5
WPM_WINDOW_SECONDS = 6
VOLUME_WINDOW_SECONDS = 6
PITCH_WINDOW_SECONDS = 6

BLACKHOLE_ID = 3 # Redirects output to microphone
MIC_INPUT = None
device_id = MIC_INPUT   # or MIC_INPUT

audio_stream = None
transcriber = None
metrics = None
transcription_thread = None
start_time = None

# Start the full pipeline: audio, transcription, metrics
def start_transcription_pipeline(device_id=MIC_INPUT):
    global audio_stream, transcriber, metrics, transcription_thread, start_time

    # Clear previous data if there exists
    if metrics is not None: 
        if hasattr(metrics, 'accumulated'):
            metrics.accumulated.clear()
        if hasattr(metrics, 'all_audio_chunks'):
            metrics.all_audio_chunks.clear()
    transcriber = None
    metrics = None 
    transcription_thread = None
    
    # start_time = time.time()

    # Create all objects
    if audio_stream is None:
        audio_stream = AudioStream(SAMPLE_RATE, device_id)
    if transcriber is None:
        transcriber = Transcriber("small", "cpu")
    if metrics is None:
        metrics = MetricsTracker(SAMPLE_RATE)

    def run_transcription():
        if audio_stream is not None:
            audio_stream.start()
            if transcriber is not None:
                transcriber.transcribe_stream(audio_stream.audio_queue, on_transcription, on_audio_chunk)

    # Safeguard to ensure exactly one background thread is active 
    if transcription_thread is None or not transcription_thread.is_alive():

        # Start a separate transcription thread 
        # - the transcription can now run without blocking the main thread (or program)
        transcription_thread = threading.Thread(target=run_transcription, daemon=True)
        transcription_thread.start()

# Stop the pipeline (implement as needed)
def stop_transcription_pipeline():
    global audio_stream, transcriber, metrics, transcription_thread
    # You may need to add stop/cleanup logic to your classes
    if audio_stream is not None:
        audio_stream.stop()
        
        # Signals the transcription loop to exit
        audio_stream.audio_queue.put(None)

    if transcription_thread is not None:
        transcription_thread.join()
        transcription_thread = None

    # Clean up stream handle
    audio_stream = None

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

    # If we haven’t initialized MetricsTracker yet, just zero‐fill.
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
    global metrics
    if metrics is not None:
        # print(f"Transcription: {text} has been added") DEBUGGING STATEMENT
        metrics.add_transcription(text, segment_duration)
        metrics.track_wpm()

def on_audio_chunk(audio_float, segment_duration):
    global metrics
    if metrics is not None:
        # print("Audio chunk received, length:", len(audio_float)) DEBUGGING STATEMENT
        metrics.add_audio_chunk(audio_float, segment_duration)
        metrics.track_volume()
        metrics.track_pitch()

if __name__ == "__main__":
    main()