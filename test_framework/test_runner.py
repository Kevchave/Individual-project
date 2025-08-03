#!/usr/bin/env python3
"""
Manual Test Runner for Transcription Models

To test different models:
1. Change CURRENT_MODEL below to: 'fixed', 'vad', or 'adaptive'
2. Modify your transcription code to use the corresponding chunking method
3. Optionally set TEST_SPECIFIC_FILE to test a specific audio file
4. Run: python test_runner.py

This will test all parameters and audio files for the specified model.
"""

import os
import sys
import time
import json
import pandas as pd
import sounddevice as sd
from pathlib import Path
from datetime import datetime

# Add transcriber_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from audio_loader import AudioLoader
from metrics_collector import MetricsCollector
from configs import TEST_CONFIGS, AUDIO_CATEGORIES
from transcriber_app.main import start_transcription_pipeline, stop_transcription_pipeline

# MANUAL CONFIGURATION - Change this to test different models
# Options: 'fixed', 'vad', 'adaptive'
CURRENT_MODEL = 'fixed'

class TestRunner:
    def __init__(self, test_audio_dir="test_audio", results_dir="test_results"):
        self.test_audio_dir = Path(test_audio_dir)  # Converts string to Path object from pathlib library 
        self.results_dir = Path(results_dir)        
        self.results_dir.mkdir(exist_ok=True)       # Creates directory if it doesn't exist
        
        self.audio_loader = AudioLoader()           # Creates instance of AudioLoader class 
        self.results = []                           # Creates empty list to store test results
        
    def find_audio_files(self):
        """Find audio files in test_audio directory"""
        # TEMPORARY: Quick test with specific file
        audio_files = [self.test_audio_dir / '10sec_medium_pace_audio.mp3']  # Change filename here
        return audio_files
        
        # # ORIGINAL CODE (commented out for quick testing)
        # audio_files = []
        # 
        # if not self.test_audio_dir.exists():
        #     print(f"Warning: {self.test_audio_dir} directory not found")
        #     return audio_files
        # 
        # # Find all audio files
        # for audio_file in self.test_audio_dir.glob("*.mp3"):  # Finds all files ending in .mp3
        #     audio_files.append(audio_file)
        # for audio_file in self.test_audio_dir.glob("*.wav"):  # Finds all files ending in .wav
        #     audio_files.append(audio_file)
        # 
        # # Filter for specific file if requested
        # if TEST_SPECIFIC_FILE is not None:
        #     filtered_files = []
        #     for audio_file in audio_files:
        #         if audio_file.name == TEST_SPECIFIC_FILE:
        #         filtered_files.append(audio_file)
        #         break
        #     
        #     if filtered_files:
        #         print(f"Testing specific file: {TEST_SPECIFIC_FILE}")
        #         return filtered_files
        #     else:
        #         print(f"Warning: File '{TEST_SPECIFIC_FILE}' not found in {self.test_audio_dir}")
        #         print(f"Available files: {[f.name for f in audio_files]}")
        #         return []
        #     
        # return audio_files
    
    def categorize_audio_file(self, audio_file):                 
        """Determine which category an audio file belongs to"""  
        filename = audio_file.name.lower()  # Get and convert filename to lowercase 
        
        if 'seminar' in filename:
            return 'seminar'
        elif 'lecture' in filename:
            return 'lecture'
        elif 'talk' in filename:
            return 'talk'
        else:
            return 'unknown'
    
    def load_reference_transcript(self, audio_file):
        """Load reference transcript for WER calculation"""
        # Look for corresponding transcript file
        transcript_file = audio_file.with_suffix('.txt')
        # # Debug statements (commented out)
        # print(f"      DEBUG: audio_file = {audio_file}")
        # print(f"      DEBUG: transcript_file = {transcript_file}")
        # print(f"      DEBUG: transcript_file.exists() = {transcript_file.exists()}")
        if transcript_file.exists():
            with open(transcript_file, 'r') as f:
                content = f.read().strip()
                # print(f"      DEBUG: Loaded transcript content: '{content}'")
                # print(f"      DEBUG: Content length: {len(content)}")
                return content
        return None
    
    def run_model_tests(self, model_type, num_runs_per_config=1):
        """Run tests for a specific model type with all its configurations and audio files"""
        print(f"Starting Tests for {model_type.upper()} Model")
        print("=" * 60)
        
        # Find audio files
        audio_files = self.find_audio_files()
        if not audio_files:
            print("No audio files found. Please add audio files to test_audio/ directory")
            return
        
        print(f"Found {len(audio_files)} audio files")
        
        # # Debug: Show all files in test_audio directory
        # print(f"All files in {self.test_audio_dir}:")
        # for file in self.test_audio_dir.iterdir():
        #     print(f"  - {file.name}")
        
        # Get configurations for the specified model
        if model_type not in TEST_CONFIGS:
            print(f"Error: Model type '{model_type}' not found in TEST_CONFIGS")
            return
        
        configs = TEST_CONFIGS[model_type]
        print(f"Testing {len(configs)} {model_type} configurations")
        
        # Calculate total tests to run
        total_tests = len(audio_files) * len(configs) * num_runs_per_config
        print(f"Total tests to run: {total_tests}")
        
        current_test = 0
        
        # For each audio file
        for audio_file in audio_files:
            category_name = self.categorize_audio_file(audio_file)
            category_info = AUDIO_CATEGORIES.get(category_name, {
                'name': category_name,
                'description': 'Unknown category'
            })
            
            print(f"\nTesting {audio_file.name} ({category_info['description']})")
            
            # For each configuration of the specified model
            for config in configs:
                # Add model type to config
                config_with_type = config.copy()
                config_with_type['model_type'] = model_type
                
                # Run test multiple times if specified
                for _ in range(num_runs_per_config):
                    current_test += 1
                    print(f"    Progress: {current_test}/{total_tests}")
                    
                    result = self.run_single_test(audio_file, config_with_type, category_info)
                    self.results.append(result)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def run_single_test(self, audio_file, config, category_info):
        """Run a single test with given audio file and configuration"""
        print(f"    Testing: {config['description']}")
        
        # Create metrics collector for this test
        metrics_collector = MetricsCollector()
        metrics_collector.start_test()
        
        try:
            # Load audio file
            audio_samples = self.audio_loader.load_audio(audio_file)
            
            # Load reference transcript for WER calculation
            reference_transcript = self.load_reference_transcript(audio_file)
            # # Debug statements (commented out)
            # if reference_transcript and reference_transcript.strip():
            #     print(f"      Found reference transcript ({len(reference_transcript)} characters)")
            # else:
            #     print(f"      No reference transcript found for {audio_file.name}")
            #     print(f"      Looking for: {audio_file.with_suffix('.txt')}")
            #     if reference_transcript is not None:
            #         print(f"      File exists but content is empty or whitespace only")
            
            # Start transcription pipeline
            start_transcription_pipeline(metrics_collector=metrics_collector)
            
            # Actually play the audio through system audio
            print(f"      Playing audio ({len(audio_samples)/16000:.1f}s)...")
            sd.play(audio_samples, 16000)
            sd.wait()  # Wait for audio to finish playing
            
            # Stop transcription
            stop_transcription_pipeline()
            
            # Get results
            latency_metrics = metrics_collector.calculate_latency()
            final_transcript = metrics_collector.get_final_transcript()
            
            # Calculate WER if reference available
            wer_score = None
            if reference_transcript:
                wer_score = metrics_collector.calculate_wer(reference_transcript)
            
            # Create simplified result record
            result = {
                'audio_file': audio_file.name,  # Just the filename, not full path
                'model_type': config.get('model_type', 'unknown'),
                'config': config['description'],  # Just the description, not full config
                'word_count': len(final_transcript.split()),
                'latency': latency_metrics['avg_latency'],  # Just the average latency
                'wer_score': wer_score,
                'recorded_transcript': final_transcript,  # What was actually transcribed
                'correct_transcript': reference_transcript  # What it should have been
            }
            
            print(f"      Completed: {result['word_count']} words, {result['latency']:.3f}s avg latency")
            if wer_score is not None:
                print(f"      WER: {wer_score:.3f}")
            return result
            
        except Exception as e:
            print(f"      Error: {e}")
            return {
                'audio_file': audio_file.name,
                'model_type': config.get('model_type', 'unknown'),
                'config': config.get('description', 'unknown'),
                'word_count': 0,
                'latency': 0,
                'wer_score': None,
                'recorded_transcript': '',
                'correct_transcript': reference_transcript if reference_transcript else '',
                'error': str(e)
            }

    def save_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_path = self.results_dir / f"test_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save as CSV
        csv_path = self.results_dir / f"test_results_{timestamp}.csv"
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv(csv_path, index=False)

        print(f"\nResults saved to:")
        print(f"  JSON: {json_path}")
        print(f"  CSV: {csv_path}")
    
    def print_summary(self):
        """Print a summary of test results"""
        if not self.results:
            print("No results to summarize")
            return
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        # Group by model type
        model_results = {}
        for result in self.results:
            model_type = result.get('model_type', 'unknown')
            if model_type not in model_results:
                model_results[model_type] = []
            model_results[model_type].append(result)
        
        # Print summary for each model
        for model_type, results in model_results.items():
            print(f"\n{model_type.upper()} Model:")
            
            # Calculate average latency
            latencies = [r['latency'] for r in results if 'error' not in r and r['latency'] is not None]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                print(f"  Average latency: {avg_latency:.3f}s")
            
            # Calculate average WER
            wer_scores = [r['wer_score'] for r in results if r.get('wer_score') is not None]
            if wer_scores:
                avg_wer = sum(wer_scores) / len(wer_scores)
                print(f"  Average WER: {avg_wer:.3f}")
            
            # Count successful tests
            successful = len([r for r in results if 'error' not in r])
            total = len(results)
            print(f"  Success rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        print(f"\nTotal tests completed: {len(self.results)}")

def main():
    """Main entry point"""
    print("Transcription Model Test Runner")
    print("=" * 40)
    print(f"Testing {CURRENT_MODEL.upper()} model")
    print("=" * 40)
    
    # Create test runner
    runner = TestRunner()
    
    # Run tests for the specified model
    runner.run_model_tests(CURRENT_MODEL, num_runs_per_config=1)
    
    print("\nTesting completed!")

if __name__ == "__main__":
    main() 