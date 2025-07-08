from audio_stream import AudioStream 
from transcriber import Transcriber 
from track_metrics import MetricsTracker 
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

def main():
    audio_stream = AudioStream(SAMPLE_RATE, device_id)
    transcriber = Transcriber("small", "cpu")
    metrics = MetricsTracker(SAMPLE_RATE)
    chunk_samples = int(CHUNK_SEC * SAMPLE_RATE)

    # Start metrics reporting threads 
    # - threads allow the different functions to run concurrently without blocking each other or the main thread/program 
    threading.Thread(target=metrics.report_wpm, args=(WPM_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=metrics.report_volume, args=(VOLUME_WINDOW_SECONDS,), daemon=True).start()
    threading.Thread(target=metrics.report_pitch, args=(PITCH_WINDOW_SECONDS,), daemon=True).start()

    def on_transcription(text):
        print(text)
        metrics.add_transcription(text)

    def on_audio_chunk(audio_float):
        metrics.add_audio_chunk(audio_float)

    with audio_stream.start(): # device=BLACKHOLE_INPUT redirects output to microphone
        source = "blackHole" if device_id == BLACKHOLE_ID else "microphone"
        print(f"Recording from {source} (Ctrl+C to stop)")
        start_time = time.time()

        try:
            threading.Thread(
                target=transcriber.transcribe_stream,
                args=(audio_stream.audio_queue, chunk_samples, on_transcription, on_audio_chunk),
                daemon=True
            ).start()
            while True:
                time.sleep(1) # The main thread will (idefinitely) sleep for 1 second until interrupted (Ctrl + C)
        except KeyboardInterrupt:
            print("Recording stopped.\n")
            print(f"Final transcription: \n {' '.join(text for text, ts in metrics.accumulated).strip()} \n")
            metrics.track_wpm_average(start_time)
            metrics.track_volume_average(start_time)
            metrics.track_overall_pitch(start_time)
            print("\n")

if __name__ == "__main__":
    main()