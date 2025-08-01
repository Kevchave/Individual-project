#!/usr/bin/env python3
"""
Simple Test Runner - Shows how to use metrics collector with existing system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'transcriber_app'))

from audio_loader import AudioLoader
from metrics_collector import MetricsCollector
from transcriber_app.main import start_transcription_pipeline, stop_transcription_pipeline, get_final_transcript

def run_simple_test(audio_file_path, reference_transcript=None):
    """
    Run a simple test with timing and WER calculation
    """
    print(f"Starting test with audio file: {audio_file_path}")
    
    # 1. Create our test components
    audio_loader = AudioLoader()
    metrics_collector = MetricsCollector()
    
    # 2. Load the audio file
    print("Loading audio file...")
    audio_samples = audio_loader.load_audio(audio_file_path)
    print(f"Audio loaded: {len(audio_samples)} samples")
    
    # 3. Start the test
    print("Starting transcription pipeline...")
    metrics_collector.start_test()
    
    # 4. Start transcription WITH metrics collector
    start_transcription_pipeline(metrics_collector=metrics_collector)
    
    # 5. Play the audio (this would be your audio playback)
    print("Playing audio...")
    # For now, we'll just wait a bit to simulate audio playback
    import time
    time.sleep(5)  # Simulate 5 seconds of audio
    
    # 6. Stop transcription
    print("Stopping transcription...")
    stop_transcription_pipeline()
    
    # 7. Get results
    print("Collecting results...")
    latency_metrics = metrics_collector.calculate_latency()
    final_transcript = metrics_collector.get_final_transcript()
    
    # 8. Calculate WER if reference available
    wer_score = None
    if reference_transcript:
        wer_score = metrics_collector.calculate_wer(reference_transcript)
    
    # 9. Print results
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    print(f"Final transcript: {final_transcript}")
    print(f"Average latency: {latency_metrics['avg_latency']:.3f} seconds")
    print(f"Total time: {latency_metrics['total_time']:.3f} seconds")
    if wer_score is not None:
        print(f"Word Error Rate: {wer_score:.3f}")
    print("="*50)
    
    return {
        'transcript': final_transcript,
        'latency': latency_metrics,
        'wer': wer_score
    }

def example_usage():
    """
    Example of how to use the test runner
    """
    print("Simple Test Runner Example")
    print("="*30)
    
    # Example 1: Test without reference transcript
    print("\n1. Testing without reference transcript:")
    result1 = run_simple_test("test_audio/sample.mp3")
    
    # Example 2: Test with reference transcript
    print("\n2. Testing with reference transcript:")
    reference = "This is a sample transcript for testing purposes."
    result2 = run_simple_test("test_audio/sample.mp3", reference)
    
    # Example 3: Compare different configurations
    print("\n3. Testing different configurations:")
    
    # Test with different parameters (you can modify start_transcription_pipeline calls)
    # For now, we'll just show the structure
    configs = [
        {'name': 'Default', 'params': {}},
        {'name': 'High Aggressiveness', 'params': {'enable_adaptive_control': False}},
        {'name': 'Adaptive', 'params': {'enable_adaptive_control': True}}
    ]
    
    for config in configs:
        print(f"\nTesting {config['name']} configuration:")
        # In real implementation, you'd pass different parameters
        # result = run_simple_test("test_audio/sample.mp3", reference)
        print(f"  {config['name']} test completed")

if __name__ == "__main__":
    example_usage() 