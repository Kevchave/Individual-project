#!/usr/bin/env python3
"""
Simple Example Test for Transcription Pipeline

This file tests the transcription pipeline on one audio file and displays
the final metrics including total words, WER, and average latency.
"""

import os
import sys
import time
from pathlib import Path

# Add transcriber_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metrics_collector import MetricsCollector
from audio_loader import AudioLoader
from transcriber_app.main import start_transcription_pipeline_with_virtual_audio, stop_transcription_pipeline
import transcriber_app.main as main_module

def calculate_wer_over_time(transcripts, reference_transcript, interval_words=50):
    """Calculate WER every N words"""
    if not transcripts or not reference_transcript:
        return []
    
    # Combine all transcripts
    all_words = []
    for transcript in transcripts:
        all_words.extend(transcript.split())
    
    total_words = len(all_words)
    metrics = []
    
    # Calculate interval size based on total words
    if total_words <= 500:  # Less than 5 minutes (assuming ~100 WPM)
        interval_words = max(10, total_words // 10)  # 10% of total words, minimum 10
    else:
        interval_words = 50  # Fixed 50 words for longer content
    
    print(f"Calculating WER every {interval_words} words (total: {total_words} words)")
    
    for i in range(0, total_words, interval_words):
        end_word = min(i + interval_words, total_words)
        
        # Get words up to this point
        predicted_words = all_words[:end_word]
        predicted_text = ' '.join(predicted_words)
        
        # Calculate WER for this segment
        from metrics_collector import wer, Compose, ToLowerCase, RemovePunctuation, RemoveMultipleSpaces, Strip
        
        def split_into_words(sentences):
            if isinstance(sentences, str):
                return sentences.split()
            return [sentence.split() for sentence in sentences]

        transform = Compose([
            ToLowerCase(),
            RemovePunctuation(),
            RemoveMultipleSpaces(),
            Strip(),
            split_into_words
        ])
        
        # For WER calculation, we need to compare with the same portion of reference
        # This is a simplified approach - in practice you might want more sophisticated alignment
        reference_words = reference_transcript.split()
        reference_segment = ' '.join(reference_words[:end_word])
        
        word_error_rate = wer(reference_segment, predicted_text, 
                             reference_transform=transform, 
                             hypothesis_transform=transform)
        
        metrics.append({
            'word_range': f"{i+1}-{end_word}",
            'words_processed': end_word,
            'wer': word_error_rate
        })
    
    return metrics

def run_example_test():
    """Run a simple test on one audio file"""
    
    # Configuration - Change these as needed
    AUDIO_FILE = "test_audio/medium_pace_audio.mp3"  # Hardcoded audio file
    MODEL_TYPE = "adaptive"  # Options: 'fixed', 'vad', 'adaptive'
    CONFIG = {
        'starting_aggressiveness': 2,  # Conservative: 1, Balanced: 2, Aggressive: 3
        'frame_duration_ms': 20,
        'max_silence_frames': 10,
        'description': 'Balanced start'
    }
    
    print("=" * 60)
    print("TRANSCRIPTION PIPELINE EXAMPLE TEST")
    print("=" * 60)
    print(f"Audio file: {AUDIO_FILE}")
    print(f"Model type: {MODEL_TYPE}")
    print(f"Configuration: {CONFIG['description']}")
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
    transcript_file = audio_path.with_suffix('.txt')
    if transcript_file.exists():
        with open(transcript_file, 'r') as f:
            reference_transcript = f.read().strip()
        print(f"Reference transcript loaded ({len(reference_transcript)} characters)")
    else:
        print("No reference transcript found - WER calculation disabled")
    
    try:
        # Start transcription pipeline
        print(f"\nStarting transcription...")
        start_transcription_pipeline_with_virtual_audio(
            audio_file_path=str(audio_path),
            metrics_collector=metrics_collector,
            real_time_simulation=False,  # Faster testing
            config=CONFIG
        )
        
        # Wait for transcription to complete
        print("Waiting for transcription to complete...")
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
        
        # # Calculate time-based WPM metrics
        # wpm_metrics = calculate_time_based_metrics(
        #     metrics_collector.transcripts, 
        #     metrics_collector.chunk_end_times
        # )
        
        # Calculate WER over time
        wer_over_time = []
        if reference_transcript:
            wer_over_time = calculate_wer_over_time(
                metrics_collector.transcripts, 
                reference_transcript
            )
        
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
        
        # # Display WPM over time
        # if wpm_metrics:
        #     print(f"\nWPM OVER TIME (every 5 seconds):")
        #     print("-" * 50)
        #     for metric in wpm_metrics:
        #         print(f"  {metric['interval']}: {metric['wpm']:.1f} WPM ({metric['words']} words)")
        
        # Display WER over time
        if wer_over_time:
            print(f"\nWER OVER TIME:")
            print("-" * 50)
            for metric in wer_over_time:
                print(f"  Words {metric['word_range']}: WER = {metric['wer']:.3f}")
        
        print()
        print("TRANSCRIPT:")
        print("-" * 40)
        print(final_transcript)
        print("-" * 40)
        
        if reference_transcript:
            print("\nREFERENCE TRANSCRIPT:")
            print("-" * 40)
            print(reference_transcript)
            print("-" * 40)
        
        # Detailed latency breakdown
        if latency_metrics['processing_latencies']:
            print(f"\nProcessing latencies per chunk:")
            for i, latency in enumerate(latency_metrics['processing_latencies']):
                print(f"  Chunk {i+1}: {latency:.3f}s")
        
        if latency_metrics['end_to_end_latencies']:
            print(f"\nEnd-to-end latencies per chunk:")
            for i, latency in enumerate(latency_metrics['end_to_end_latencies']):
                print(f"  Chunk {i+1}: {latency:.3f}s")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during transcription: {e}")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)

if __name__ == "__main__":
    run_example_test() 