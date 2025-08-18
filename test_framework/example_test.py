#!/usr/bin/env python3
"""
Simplified Example Test for Transcription Pipeline

This file tests the transcription pipeline on one audio file and displays
the final metrics including total words, WER, and average latency.
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

def run_example_test():
    """Run a simple test on one audio file"""
    
    # Configuration - Change these as needed
    AUDIO_FILE = "test_audio/10sec_medium_pace_audio.mp3"
    MODEL_TYPE = "adaptive"
    CONFIG = {
        'starting_aggressiveness': 2,
        'frame_duration_ms': 20,
        'max_silence_frames': 10,
        'description': 'Balanced start'
    }
    
    print("=" * 60)
    print("SIMPLIFIED TRANSCRIPTION PIPELINE TEST")
    print("=" * 60)
    print(f"Audio file: {AUDIO_FILE}")
    print(f"Model type: {MODEL_TYPE}")
    print(f"Parameters: aggressiveness={CONFIG['starting_aggressiveness']}, frame_duration={CONFIG['frame_duration_ms']}ms, max_silence={CONFIG['max_silence_frames']} frames")
    print("=" * 60)
    
    # Check if audio file exists
    audio_path = Path(AUDIO_FILE)
    if not audio_path.exists():
        print(f"Error: Audio file '{AUDIO_FILE}' not found!")
        return
    
    # Create metrics collector
    metrics_collector = MetricsCollector()
    metrics_collector.start_test()
    
    # Load reference transcript for WER calculation
    reference_transcript = None
    transcript_dir = Path("test_transcript")
    transcript_file = transcript_dir / audio_path.with_suffix('.txt').name
    if transcript_file.exists():
        with open(transcript_file, 'r') as f:
            reference_transcript = f.read().strip()
        print(f"Reference transcript loaded ({len(reference_transcript)} characters)")
    else:
        print("No reference transcript found - WER calculation disabled")
    
    try:
        # Start transcription pipeline and suppress console output
        print(f"\nTranscription in progress...")
        
        # Suppress console output during transcription
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            start_transcription_pipeline_with_virtual_audio(
                audio_file_path=str(audio_path),
                metrics_collector=metrics_collector,
                real_time_simulation=False,  # Faster testing
                config=CONFIG
            )
            
            # Wait for transcription to complete
            while main_module.transcription_thread and main_module.transcription_thread.is_alive():
                time.sleep(0.1)
        
        # Stop transcription
        stop_transcription_pipeline()
        
        # Calculate metrics
        latency_metrics = metrics_collector.calculate_latency()
        final_transcript = metrics_collector.get_final_transcript()
        
        # Calculate WER if reference available
        wer_score = None
        if reference_transcript:
            wer_score = metrics_collector.calculate_wer(reference_transcript)
        
        # Display results
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        
        print(f"Audio file: {audio_path.name}")
        print(f"Model type: {MODEL_TYPE}")
        print(f"Configuration: {CONFIG['description']}")
        print()
        
        print(f"Total words transcribed: {len(final_transcript.split())}")
        print(f"Processing latency: {latency_metrics['avg_processing_latency']:.3f}s")
        print(f"End-to-end latency: {latency_metrics['avg_end_to_end_latency']:.3f}s")
        
        if wer_score is not None:
            print(f"Overall Word Error Rate (WER): {wer_score:.3f}")
        else:
            print("Word Error Rate (WER): Not calculated (no reference transcript)")
        
        print()
        print("TRANSCRIPT:")
        print("-" * 50)
        print(final_transcript)
        
        if reference_transcript:
            print()
            print("REFERENCE TRANSCRIPT:")
            print("-" * 50)
            print(reference_transcript)
        
    except Exception as e:
        print(f"Error during transcription: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_example_test() 