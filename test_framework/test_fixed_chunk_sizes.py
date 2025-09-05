#!/usr/bin/env python3
"""
Fixed Chunk Size Test

Tests fixed chunk sizes (seconds):
- 0.6, 1.0, 1.5, 2.25, 3.0, 4.0

Audio files (60 sec each):
- logic_08.10.24.mp3
- maths_03.12.24.mp3
- sse_18.10.24.mp3

Outputs: WER, average callback latency, chunks processed
Uses the virtual audio pipeline with real_time_simulation=False for speed.
"""

import os
import sys
import time
import contextlib
import io
from pathlib import Path

# Add transcriber_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metrics_collector import MetricsCollector
from transcriber_app.main import start_transcription_pipeline_with_virtual_audio, stop_transcription_pipeline
import transcriber_app.main as main_module

# Test configuration - Fixed chunk sizes
CHUNK_SIZES = [0.6, 1.0, 1.5, 2.25, 3.0, 4.0]
ITERATIONS_PER_CONFIG = 2

# Audio files (60sec versions) and corresponding transcripts
AUDIO_FILES = [
    'logic_08.10.24.mp3',
    'maths_03.12.24.mp3',
    'sse_18.10.24.mp3'
]

TRANSCRIPT_FILES = [
    'logic_08.10.24.txt',
    'maths_03.12.24.txt',
    'sse_18.10.24.txt'
]


def load_reference_transcript(transcript_file):
    """Load reference transcript from file"""
    transcript_path = Path(__file__).parent / 'transcripts' / 'edited_transcripts' / '60sec_transcripts' / transcript_file

    if not transcript_path.exists():
        print(f"Warning: Transcript file {transcript_path} not found")
        return None

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading transcript {transcript_path}: {e}")
        return None


def run_single_test(audio_file, chunk_seconds, transcript_file):
    """Run a single test with given audio file and fixed chunk size"""
    # Create metrics collector
    metrics_collector = MetricsCollector()
    metrics_collector.start_test()

    # Load reference transcript
    reference_transcript = load_reference_transcript(transcript_file)

    # Audio file path
    audio_path = Path(__file__).parent / 'audio_files' / '60sec_versions' / audio_file

    if not audio_path.exists():
        print(f"Error: Audio file {audio_path} not found")
        return None

    try:
        # Start transcription pipeline with suppressed output
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            start_transcription_pipeline_with_virtual_audio(
                audio_file_path=str(audio_path),
                metrics_collector=metrics_collector,
                real_time_simulation=False,  # Faster testing
                config={'chunk_size': float(chunk_seconds)}
            )

            # Wait for transcription to complete
            start_time = time.time()
            while main_module.transcription_thread and main_module.transcription_thread.is_alive():
                if time.time() - start_time > 120:  # 2 minute timeout
                    print("  -> Timeout after 2 minutes")
                    break
                time.sleep(0.1)

            # Stop transcription (also suppressed)
            stop_transcription_pipeline()

        # Get results
        latency_metrics = metrics_collector.calculate_latency()
        final_transcript = metrics_collector.get_final_transcript()

        # Robust latency calculation: prefer callback, fallback to end times
        start_times = metrics_collector.chunk_start_times
        callback_times = metrics_collector.chunk_callback_times
        end_times = metrics_collector.chunk_end_times
        latencies = []
        if callback_times and len(callback_times) == len(start_times):
            latencies = [cb - st for st, cb in zip(start_times, callback_times)]
        elif end_times and len(end_times) == len(start_times):
            latencies = [en - st for st, en in zip(start_times, end_times)]

        num_chunks = len(latencies) if latencies else (
            len(latency_metrics.get('callback_latencies', [])) if latency_metrics else len(metrics_collector.transcripts)
        )

        # Calculate WER
        wer_score = None
        if reference_transcript:
            wer_score = metrics_collector.calculate_wer(reference_transcript)

        # Calculate average latency
        avg_latency = (sum(latencies) / len(latencies)) if latencies else (
            latency_metrics['avg_callback_latency'] if latency_metrics else 0
        )

        return {
            'audio_file': audio_file,
            'chunk_size': chunk_seconds,
            'wer_score': wer_score,
            'avg_latency': avg_latency,
            'num_chunks': num_chunks,
            'transcript': final_transcript,
            'reference': reference_transcript
        }

    except Exception as e:
        print(f"  -> Error: {e}")
        return None


def main():
    """Main test function"""
    print("=" * 80)
    print("FIXED CHUNK SIZE TEST")
    print("=" * 80)
    print(f"Testing {len(CHUNK_SIZES)} chunk sizes on {len(AUDIO_FILES)} audio files, {ITERATIONS_PER_CONFIG} iterations each")
    print()

    results = []

    # Test each fixed chunk size on each audio file
    for chunk_seconds in CHUNK_SIZES:
        print(f"Testing chunk size = {chunk_seconds:.1f}s")
        print("-" * 80)

        # Print table header
        print(f"{'Audio File':<25} | {'Iter':<4} | {'WER':<8} | {'Latency':<10} | {'Num Chunks':<12}")
        print("-" * 80)

        for audio_file, transcript_file in zip(AUDIO_FILES, TRANSCRIPT_FILES):
            for iteration in range(1, ITERATIONS_PER_CONFIG + 1):
                result = run_single_test(audio_file, chunk_seconds, transcript_file)

                if result:
                    results.append(result)
                    wer_str = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
                    latency_str = f"{result['avg_latency']:.3f}s"
                    chunks_str = f"{result['num_chunks']}"
                    print(f"{audio_file:<25} | {iteration:<4} | {wer_str:<8} | {latency_str:<10} | {chunks_str:<12}")
                else:
                    print(f"{audio_file:<25} | {iteration:<4} | {'FAILED':<8} | {'N/A':<10} | {'N/A':<12}")

        print()

    # Print per-chunk-size summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for chunk_seconds in CHUNK_SIZES:
        chunk_results = [r for r in results if r['chunk_size'] == chunk_seconds]
        if not chunk_results:
            continue

        print(f"\nChunk Size {chunk_seconds:.1f}s:")
        print("-" * 40)
        for result in chunk_results:
            wer_str = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
            print(f"  {result['audio_file']}: WER={wer_str}, Latency={result['avg_latency']:.3f}s, Chunks={result['num_chunks']}")

    # Aggregated summary across all audios and iterations
    print("\n" + "=" * 80)
    print("AGGREGATED SUMMARY (across audios and iterations)")
    print("=" * 80)
    print(f"{'Chunk Size':<12} | {'AVG WER':<8} | {'AVG Latency':<12}")
    print("-" * 80)
    for chunk_seconds in CHUNK_SIZES:
        cr = [r for r in results if r['chunk_size'] == chunk_seconds]
        wer_vals = [r['wer_score'] for r in cr if r['wer_score'] is not None]
        lat_vals = [r['avg_latency'] for r in cr]
        avg_wer = (sum(wer_vals) / len(wer_vals)) if wer_vals else None
        avg_lat = (sum(lat_vals) / len(lat_vals)) if lat_vals else 0
        wer_str = f"{avg_wer:.3f}" if avg_wer is not None else "N/A"
        print(f"{chunk_seconds:<12.1f} | {wer_str:<8} | {avg_lat:.3f}s")

    print(f"\nTotal tests completed: {len(results)}")
    print("=" * 80)


if __name__ == "__main__":
    main() 