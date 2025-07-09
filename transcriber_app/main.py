from .audio_stream import AudioStream
from .transcriber import Transcriber
from .track_metrics import MetricsTracker
import threading
import time

SAMPLE_RATE = 16000
CHUNK_SEC = 3.0
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
    
    start_time = time.time()


    if audio_stream is None:
        audio_stream = AudioStream(SAMPLE_RATE, device_id)
    if transcriber is None:
        transcriber = Transcriber("small", "cpu")
    if metrics is None:
        metrics = MetricsTracker(SAMPLE_RATE)

    chunk_samples = int(CHUNK_SEC * SAMPLE_RATE)

    # Start metrics reporting threads 
    # - threads allow the different functions to run concurrently without blocking each other or the main thread/program 
    threading.Thread(target=metrics.track_wpm, args=(WPM_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=metrics.track_volume, args=(VOLUME_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=metrics.track_pitch, args=(PITCH_WINDOW_SECONDS,), daemon=True).start()

    def run_transcription():
        if audio_stream is not None:
            audio_stream.start()
            if transcriber is not None:
                transcriber.transcribe_stream(
                    audio_stream.audio_queue, chunk_samples, on_transcription, on_audio_chunk
                )

    if transcription_thread is None or not transcription_thread.is_alive():
        # Start the transcription process in a background thread
        globals()['transcription_thread'] = threading.Thread(target=run_transcription, daemon=True)
        globals()['transcription_thread'].start()

# Stop the pipeline (implement as needed)
def stop_transcription_pipeline():
    global audio_stream, transcriber, metrics, transcription_thread
    # You may need to add stop/cleanup logic to your classes
    if audio_stream is not None:
        audio_stream.stop()
        audio_stream = None
    # Optionally, add cleanup for transcriber and metrics if needed
    # (e.g., set to None, stop threads, etc.)

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
    if metrics is not None:
        metrics.track_wpm(WPM_WINDOW_SECONDS)
        metrics.track_volume(VOLUME_WINDOW_SECONDS)
        metrics.track_pitch(PITCH_WINDOW_SECONDS)
        return {
            'wpm': getattr(metrics, 'current_wpm', 0),
            'volume': getattr(metrics, 'current_volume', 0),
            'pitch': getattr(metrics, 'current_pitch', 0)
        }
    return {'wpm': 0, 'volume': 0, 'pitch': 0}

def get_average_metrics():
    global metrics
    if metrics is not None:
        # Call the average methods to update the attributes
        metrics.track_wpm_average(start_time)
        metrics.track_volume_average(start_time)
        metrics.track_overall_pitch(start_time)
        return {
            'average_wpm': getattr(metrics, 'average_wpm', 0),
            'average_volume': getattr(metrics, 'average_volume', 0),
            'average_pitch': getattr(metrics, 'average_pitch', 0)
        }
    return {'average_wpm': 0, 'average_volume': 0, 'average_pitch': 0}

def get_final_transcript():
    global metrics
    if metrics is not None and hasattr(metrics, 'accumulated'):
        return ' '.join(text for text, ts in metrics.accumulated).strip()
    return ""

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

def on_transcription(text):
    global metrics
    if metrics is not None:
        metrics.add_transcription(text)

def on_audio_chunk(audio_float):
    global metrics
    if metrics is not None:
        metrics.add_audio_chunk(audio_float)

if __name__ == "__main__":
    main()