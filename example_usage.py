#!/usr/bin/env python3
"""
Example usage of the transcription pipeline with and without insider metrics.

This demonstrates how to:
1. Run with insider metrics enabled (for adaptive chunking development)
2. Run with insider metrics disabled (for performance testing)
3. Compare the performance impact
"""

from transcriber_app.main import start_transcription_pipeline, stop_transcription_pipeline
import time
import signal
import sys

def signal_handler(sig, frame):
    print("\nStopping transcription...")
    stop_transcription_pipeline()
    sys.exit(0)

def run_with_insider_metrics():
    """Run transcription with insider metrics enabled"""
    print("=== Running with Insider Metrics Enabled ===")
    print("This will track silence ratio and confidence scores for adaptive chunking.")
    print("You should see [INSIDER METRICS] output in the terminal.")
    print()
    
    start_transcription_pipeline(enable_insider_metrics=True)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_transcription_pipeline()

def run_without_insider_metrics():
    """Run transcription without insider metrics for performance testing"""
    print("=== Running without Insider Metrics ===")
    print("This will run the core transcription without adaptive chunking metrics.")
    print("You should NOT see [INSIDER METRICS] output in the terminal.")
    print()
    
    start_transcription_pipeline(enable_insider_metrics=False)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_transcription_pipeline()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Transcription Pipeline Example")
    print("==============================")
    print()
    print("Choose an option:")
    print("1. Run with insider metrics (for adaptive chunking development)")
    print("2. Run without insider metrics (for performance testing)")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            run_with_insider_metrics()
            break
        elif choice == "2":
            run_without_insider_metrics()
            break
        elif choice == "3":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 