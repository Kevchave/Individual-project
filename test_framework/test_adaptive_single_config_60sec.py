#!/usr/bin/env python3
"""
Adaptive Single-Config Test (60s Audios)

Runs one adaptive/VAD configuration across all 60-second audios:
- aggressiveness=2, frame_duration_ms=20, max_silence_frames=5

Outputs per audio:
- WER, average callback latency, number of chunks, average word confidence

Uses the virtual audio pipeline with real_time_simulation=False for speed.
"""

import os
import sys
import time
import contextlib
import io
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metrics_collector import MetricsCollector
from transcriber_app.main import start_transcription_pipeline_with_virtual_audio, stop_transcription_pipeline
import transcriber_app.main as main_module

@contextmanager
def suppress_pipeline_output():
    """Suppress stdout/stderr and patch print during pipeline execution."""
    import builtins as _builtins
    original_print = _builtins.print
    try:
        with open(os.devnull, 'w') as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            _builtins.print = lambda *args, **kwargs: None
            yield
    finally:
        _builtins.print = original_print

# Single adaptive configuration
CONFIGS = [
    {
        'name': 'aggr=0, frame=20ms, max_silence_frames=10',
        'aggressiveness': 0,
        'frame_duration_ms': 20,
        'max_silence_frames': 10,
    },
    {
        'name': 'aggr=2, frame=20ms, max_silence_frames=10',
        'aggressiveness': 2,
        'frame_duration_ms': 20,
        'max_silence_frames': 10,
    },
    {
        'name': 'aggr=3, frame=20ms, max_silence_frames=5',
        'aggressiveness': 3,
        'frame_duration_ms': 20,
        'max_silence_frames': 5,
    },
]

# One iteration per audio
ITERATIONS_PER_AUDIO = 1

# Audio files (60sec versions) and corresponding transcripts
AUDIO_FILES = [
    'logic_08.10.24.mp3',
    'maths_03.12.24.mp3',
    'sse_18.10.24.mp3',
    'sse_30.01.25.mp3',
    'computer_15.10.24.mp3',
]

TRANSCRIPT_FILES = [
    'logic_08.10.24.txt',
    'maths_03.12.24.txt',
    'sse_18.10.24.txt',
    'sse_30.01.25.txt',
    'computer_15.10.24.txt',
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


def compute_average_confidence(metrics_obj):
    """Compute average word confidence from MetricsTracker if available"""
    try:
        if metrics_obj is None:
            return None
        scores = getattr(metrics_obj, 'chunk_confidence_scores', None)
        if scores:
            return sum(scores) / len(scores)
        # Fallback to computed average_confidence if present
        if hasattr(metrics_obj, 'track_average_confidence'):
            metrics_obj.track_average_confidence()
            return getattr(metrics_obj, 'average_confidence', None)
    except Exception:
        pass
    return None


def run_single_test(audio_file, transcript_file, config):
    """Run a single test with given audio file and adaptive configuration"""
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
        # Start transcription pipeline with all output suppressed
        with suppress_pipeline_output():
            start_transcription_pipeline_with_virtual_audio(
                audio_file_path=str(audio_path),
                enable_insider_metrics=True,
                enable_adaptive_control=False,  # keep config fixed for fair comparison
                metrics_collector=metrics_collector,
                real_time_simulation=False,  # Faster testing
                config=config
            )

            # Wait for transcription to complete
            start_time = time.time()
            while main_module.transcription_thread and main_module.transcription_thread.is_alive():
                if time.time() - start_time > 120:  # 2 minute timeout
                    break
                time.sleep(0.1)

            # Stop transcription
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

        # Determine number of chunks
        if latencies:
            num_chunks = len(latencies)
        elif latency_metrics and latency_metrics.get('callback_latencies'):
            num_chunks = len(latency_metrics['callback_latencies'])
        else:
            # Fallback to number of confidence scores stored
            metrics_obj = getattr(main_module, 'metrics', None)
            num_chunks = len(getattr(metrics_obj, 'chunk_confidence_scores', [])) if metrics_obj is not None else 0

        # Calculate WER
        wer_score = None
        if reference_transcript:
            wer_score = metrics_collector.calculate_wer(reference_transcript)

        # Calculate average latency
        avg_latency = (sum(latencies) / len(latencies)) if latencies else (
            latency_metrics['avg_callback_latency'] if latency_metrics else 0
        )

        # Calculate average metrics from MetricsTracker (suppress their debug prints)
        with suppress_pipeline_output():
            avg_metrics = main_module.get_average_metrics()
        avg_wpm = avg_metrics.get('average_wpm')
        avg_volume = avg_metrics.get('average_volume')
        avg_pitch_var = avg_metrics.get('average_pitch')
        avg_silence = avg_metrics.get('average_silence_ratio')

        # Calculate average word confidence (prefer avg_metrics fallback to compute)
        avg_confidence = avg_metrics.get('average_confidence')
        if avg_confidence is None:
            avg_confidence = compute_average_confidence(getattr(main_module, 'metrics', None))

        return {
            'audio_file': audio_file,
            'wer_score': wer_score,
            'avg_latency': avg_latency,
            'num_chunks': num_chunks,
            'avg_confidence': avg_confidence,
            'avg_wpm': avg_wpm,
            'avg_volume': avg_volume,
            'avg_pitch_var': avg_pitch_var,
            'avg_silence': avg_silence,
            'transcript': final_transcript,
            'reference': reference_transcript
        }

    except Exception as e:
        print(f"  -> Error: {e}")
        return None


def main():
    """Main test function"""
    print("=" * 80)
    print("ADAPTIVE MULTI-CONFIG TEST (60s audios)")
    print("=" * 80)
    print(f"Testing {len(AUDIO_FILES)} audio files, {ITERATIONS_PER_AUDIO} iteration each")
    print()

    all_results = []

    for cfg in CONFIGS:
        print("-" * 80)
        print(f"Config: {cfg['name']}")
        print("-" * 80)
        # Print table header per config
        print(f"{'Audio File':<25} | {'Iter':<4} | {'WER':<8} | {'Latency':<10} | {'Num Chunks':<12} | {'AVG WPM':<8} | {'AVG Vol':<8} | {'Pitch Var':<10} | {'Silence':<8} | {'Word Conf':<10}")
        print("-" * 150)

        for audio_file, transcript_file in zip(AUDIO_FILES, TRANSCRIPT_FILES):
            for iteration in range(1, ITERATIONS_PER_AUDIO + 1):
                result = run_single_test(audio_file, transcript_file, cfg)

                if result:
                    result['config'] = cfg['name']
                    all_results.append(result)
                    wer_str = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
                    latency_str = f"{result['avg_latency']:.3f}s"
                    chunks_str = f"{result['num_chunks']}"
                    wpm_str = f"{result['avg_wpm']:.1f}" if result.get('avg_wpm') is not None else "N/A"
                    vol_str = f"{result['avg_volume']:.1f}" if result.get('avg_volume') is not None else "N/A"
                    pitch_str = f"{result['avg_pitch_var']:.2f}" if result.get('avg_pitch_var') is not None else "N/A"
                    silence_str = f"{result['avg_silence']:.3f}" if result.get('avg_silence') is not None else "N/A"
                    conf_str = f"{result['avg_confidence']:.3f}" if result['avg_confidence'] is not None else "N/A"
                    print(f"{audio_file:<25} | {iteration:<4} | {wer_str:<8} | {latency_str:<10} | {chunks_str:<12} | {wpm_str:<8} | {vol_str:<8} | {pitch_str:<10} | {silence_str:<8} | {conf_str:<10}")
                else:
                    print(f"{audio_file:<25} | {iteration:<4} | {'FAILED':<8} | {'N/A':<10} | {'N/A':<12} | {'N/A':<8} | {'N/A':<8} | {'N/A':<10} | {'N/A':<8} | {'N/A':<10}")

        print()

    # Optional aggregated summary across all configs
    if all_results:
        print("\n" + "=" * 80)
        print("AGGREGATED SUMMARY (all configs)")
        print("=" * 80)
        avg_wer_vals = [r['wer_score'] for r in all_results if r['wer_score'] is not None]
        avg_lat_vals = [r['avg_latency'] for r in all_results]
        avg_conf_vals = [r['avg_confidence'] for r in all_results if r['avg_confidence'] is not None]
        avg_wer = (sum(avg_wer_vals) / len(avg_wer_vals)) if avg_wer_vals else None
        avg_lat = (sum(avg_lat_vals) / len(avg_lat_vals)) if avg_lat_vals else 0
        avg_conf = (sum(avg_conf_vals) / len(avg_conf_vals)) if avg_conf_vals else None
        wer_str = f"{avg_wer:.3f}" if avg_wer is not None else "N/A"
        conf_str = f"{avg_conf:.3f}" if avg_conf is not None else "N/A"
        print(f"AVG WER={wer_str}, AVG Latency={avg_lat:.3f}s, AVG Word Conf={conf_str}")

    print(f"\nTotal tests completed: {len(all_results)}")
    print("=" * 80)


if __name__ == "__main__":
    main() 