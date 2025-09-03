#!/usr/bin/env python3
"""
Simple VAD Aggressiveness Test

Tests VAD parameters:
- Aggressiveness: 0, 1, 2, 3
- Frame duration: 20ms (fixed)
- Max silence frames: 10 (fixed)

Audio files:
- logic_08.10.24.mp3
- maths_03.12.24.mp3  
- sse_18.10.24.mp3
- sse_30.01.25.mp3

Outputs: WER, average latency, chunks processed
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

# Test configuration - Fixed VAD model with specific parameters
VAD_CONFIGS = [
    {'aggressiveness': 0, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'model_type': 'vad', 'description': 'Agg=0, 20ms, 10frames'},
    {'aggressiveness': 1, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'model_type': 'vad', 'description': 'Agg=1, 20ms, 10frames'},
    {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'model_type': 'vad', 'description': 'Agg=2, 20ms, 10frames'},
    {'aggressiveness': 3, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'model_type': 'vad', 'description': 'Agg=3, 20ms, 10frames'},
]

# Audio files and transcripts
AUDIO_FILES = [
    'logic_08.10.24.mp3',
    'maths_03.12.24.mp3', 
    'sse_18.10.24.mp3',
    'sse_30.01.25.mp3'
]

TRANSCRIPT_FILES = [
    'logic_08.10.24.txt',
    'maths_03.12.24.txt',
    'sse_18.10.24.txt', 
    'sse_30.01.25.txt'
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

def run_single_test(audio_file, config, transcript_file):
    """Run a single test with given audio file and VAD configuration"""
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
                config=config
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
        num_chunks = len(latency_metrics.get('callback_latencies', [])) if latency_metrics else len(metrics_collector.transcripts)
        
        # Calculate WER
        wer_score = None
        if reference_transcript:
            wer_score = metrics_collector.calculate_wer(reference_transcript)
        
        # Calculate average latency
        avg_latency = latency_metrics['avg_callback_latency'] if latency_metrics else 0
        
        return {
            'audio_file': audio_file,
            'config': config['description'],
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
    print("VAD AGGRESSIVENESS TEST")
    print("=" * 80)
    print(f"Testing {len(VAD_CONFIGS)} VAD configurations on {len(AUDIO_FILES)} audio files")
    print()
    
    results = []
    
    # Test each VAD configuration on each audio file
    for config in VAD_CONFIGS:
        print(f"Testing config #{config['aggressiveness']+1} (Agg={config['aggressiveness']}, {config['frame_duration_ms']}ms, {config['max_silence_frames']} frames)")
        print("-" * 80)
        
        # Print table header
        print(f"{'Audio File':<25} | {'WER':<8} | {'Latency':<10} | {'Num Chunks':<12}")
        print("-" * 80)
        
        for audio_file, transcript_file in zip(AUDIO_FILES, TRANSCRIPT_FILES):
            result = run_single_test(audio_file, config, transcript_file)
            
            if result:
                results.append(result)
                # Format the output in table format
                wer_str = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
                latency_str = f"{result['avg_latency']:.3f}s"
                chunks_str = f"{result['num_chunks']}"
                print(f"{audio_file:<25} | {wer_str:<8} | {latency_str:<10} | {chunks_str:<12}")
            else:
                print(f"{audio_file:<25} | {'FAILED':<8} | {'N/A':<10} | {'N/A':<12}")
        
        print()
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for config in VAD_CONFIGS:
        config_results = [r for r in results if r['config'] == config['description']]
        if not config_results:
            continue
            
        print(f"\n{config['description']}:")
        print("-" * 40)
        
        for result in config_results:
            wer_str = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
            print(f"  {result['audio_file']}: WER={wer_str}, Latency={result['avg_latency']:.3f}s, Chunks={result['num_chunks']}")
    
    print(f"\nTotal tests completed: {len(results)}")
    print("=" * 80)

if __name__ == "__main__":
    main() 