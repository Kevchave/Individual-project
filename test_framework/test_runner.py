#!/usr/bin/env python3
"""
Simplified Test Runner for Transcription Models

To test different models:
1. Change CURRENT_MODEL below to: 'fixed', 'vad', or 'adaptive'
2. Run: python test_runner.py

This will test all parameters and audio files for the specified model.
"""

import os
import sys
import time
import json
import contextlib
import io
from pathlib import Path
from datetime import datetime

# Add transcriber_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metrics_collector import MetricsCollector
from configs import TEST_CONFIGS
from transcriber_app.main import start_transcription_pipeline_with_virtual_audio, stop_transcription_pipeline
import transcriber_app.main as main_module

# MANUAL CONFIGURATION - Change this to test different models
# Options: 'fixed', 'vad', 'adaptive'
CURRENT_MODEL = 'fixed'

class TestRunner:
    def __init__(self, test_audio_dir="test_audio", results_dir="test_results"):
        self.test_audio_dir = Path(test_audio_dir)  
        self.results_dir = Path(results_dir)        
        self.json_dir = self.results_dir / "json_results"
        self.report_dir = self.results_dir / "report_results"
        
        # Create directories
        self.results_dir.mkdir(exist_ok=True)
        self.json_dir.mkdir(exist_ok=True)
        self.report_dir.mkdir(exist_ok=True)
        
        self.results = []
        
    def find_audio_files(self):
        """Find audio files in test_audio directory"""
      
        # For quick testing - use specific file
        audio_files = [self.test_audio_dir / '10sec_medium_pace_audio.mp3']
        return audio_files
        
        # # For full testing 
        # audio_files = []
        # if not self.test_audio_dir.exists():
        #     print(f"Warning: {self.test_audio_dir} directory not found")
        #     return audio_files
        # for audio_file in self.test_audio_dir.glob("*.mp3"):
        #     audio_files.append(audio_file)
        # for audio_file in self.test_audio_dir.glob("*.wav"):
        #     audio_files.append(audio_file)
        # return audio_files
    
    def load_reference_transcript(self, audio_file):
        """Load reference transcript for WER calculation"""
        # Look for transcript in test_transcript folder
        transcript_dir = Path("test_transcript")
        transcript_file = transcript_dir / audio_file.with_suffix('.txt').name
        
        if transcript_file.exists():
            with open(transcript_file, 'r') as f:
                content = f.read().strip()
                return content
        print(f" -> Transcript not found for {audio_file.name}")
        return None
    
    def get_model_display_name(self, model_type):
        """Get display name for model type"""
        if model_type == 'fixed':
            return 'FIXED'
        elif model_type == 'vad':
            return 'FIXED VAD'
        elif model_type == 'adaptive':
            return 'ADAPTIVE VAD'
        else:
            return model_type.upper()
    
    def run_model_tests(self, model_type, num_runs_per_config=1):
        """Run tests for a specific model type with all its configurations and audio files"""
        model_display_name = self.get_model_display_name(model_type)
        
        print("\n" + ("=" * 100))
        print("Testing Session")
        print("=" * 100)
        
        # Find audio files
        audio_files = self.find_audio_files()
        if not audio_files:
            print("No audio files found. Please add audio files to test_audio/ directory")
            return
        
        # Get configurations for the specified model
        if model_type not in TEST_CONFIGS:
            print(f"Error: Model type '{model_type}' not found in TEST_CONFIGS")
            return
        
        configs = TEST_CONFIGS[model_type]
        
        # Calculate total tests
        total_tests = len(audio_files) * len(configs) * num_runs_per_config
        
        print(f"-> Testing {model_display_name} model")
        print(f"-> Testing {len(audio_files)} audio files")
        print(f"-> Testing {len(configs)} configurations")
        print(f"-> Testing {num_runs_per_config} iterations per audio per configuration")
        print(f"-> TOTAL: {total_tests} tests")
        print()
        
        current_test = 0
        
        # For each audio file
        for audio_idx, audio_file in enumerate(audio_files, 1):
            print(f"Audio {audio_idx}/{len(audio_files)} ({audio_file.name})")
            print("-" * 80)
            
            # Print table header
            print(f"| {'config/params':<35} | {'iteration':<12} | {'Processing':<12} | {'WER':<8} |")
            print("-" * 80)
            
            # For each configuration of the specified model
            for config in configs:
                # Add model type to config
                config_with_type = config.copy()
                config_with_type['model_type'] = model_type
                
                # Run test multiple times if specified
                for iteration in range(num_runs_per_config):
                    current_test += 1
                    
                    # Print row header
                    config_display = config['description']
                    print(f"| {config_display:<35} | {current_test:>2}/{total_tests:<9} |", end="")
                    
                    # Run the test
                    result = self.run_single_test(audio_file, config_with_type, current_test, total_tests)
                    self.results.append(result)
                    
                    # Print results in the same row
                    if 'error' in result:
                        print(f" {'ERROR':<12} | {'N/A':<8} |")
                    else:
                        latency = f"{result['processing_latency']:.3f}s"
                        wer = f"{result['wer_score']:.3f}" if result['wer_score'] is not None else "N/A"
                        print(f" {latency:<12} | {wer:<8} |")
                    
                    print("-" * 80)
            
            print()  # Empty line between audio files
        
        # Save results
        json_path = self.save_results(model_type)
        self.print_summary(model_display_name, total_tests, json_path)
    
    def run_single_test(self, audio_file, config, current_test, total_tests):
        """Run a single test with given audio file and configuration"""
        # Create metrics collector for this test
        metrics_collector = MetricsCollector()
        metrics_collector.start_test()
        
        try:
            # Load reference transcript for WER calculation
            reference_transcript = self.load_reference_transcript(audio_file)
            
            # Start transcription pipeline with virtual audio injection
            # Suppress ALL console output during transcription including cleanup messages
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                start_transcription_pipeline_with_virtual_audio(
                    audio_file_path=str(audio_file),
                    metrics_collector=metrics_collector,
                    real_time_simulation=False,  # Faster testing without real-time delays
                    config=config
                )
                
                # Wait for transcription to complete
                while main_module.transcription_thread and main_module.transcription_thread.is_alive():
                    time.sleep(0.1)
                
                # Stop transcription (also suppressed)
                stop_transcription_pipeline()
            
            # Get results
            latency_metrics = metrics_collector.calculate_latency()
            final_transcript = metrics_collector.get_final_transcript()
            
            # Calculate WER if reference available
            wer_score = None
            if reference_transcript:
                wer_score = metrics_collector.calculate_wer(reference_transcript)
            
            # Create result record
            result = {
                'audio_file': audio_file.name,
                'model_type': config.get('model_type', 'unknown'),
                'config': config['description'],
                'word_count': len(final_transcript.split()),
                'processing_latency': latency_metrics['avg_processing_latency'],
                'end_to_end_latency': latency_metrics['avg_end_to_end_latency'],
                'wer_score': wer_score,
                'recorded_transcript': final_transcript,
                'correct_transcript': reference_transcript
            }
            
            return result
            
        except Exception as e:
            return {
                'audio_file': audio_file.name,
                'model_type': config.get('model_type', 'unknown'),
                'config': config.get('description', 'unknown'),
                'word_count': 0,
                'processing_latency': 0,
                'end_to_end_latency': 0,
                'wer_score': None,
                'recorded_transcript': '',
                'correct_transcript': reference_transcript if reference_transcript else '',
                'error': str(e)
            }

    def save_results(self, model_type):
        """Save test results to JSON file and create readable report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_display_name = self.get_model_display_name(model_type).replace(" ", "_")
        
        json_path = self.json_dir / f"{model_display_name}_test_results_{timestamp}.json"
        report_path = self.report_dir / f"{model_display_name}_test_results_{timestamp}.txt"
        
        # Save JSON for programmatic access
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Create human-readable report
        self.create_readable_report(report_path)
        
        return json_path
    
    def create_readable_report(self, report_path):
        """Create a human-readable text report"""
        with open(report_path, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("TRANSCRIPTION TEST RESULTS REPORT\n")
            f.write("=" * 100 + "\n\n")
            
            # Group results by config and audio file
            grouped_results = {}
            for result in self.results:
                if 'error' in result:
                    continue
                    
                key = (result['config'], result['audio_file'])
                if key not in grouped_results:
                    grouped_results[key] = []
                grouped_results[key].append(result)
            
            # Write summary table
            f.write("SUMMARY TABLE\n")
            f.write("-" * 100 + "\n")
            f.write(f"{'config/params':<31} | {'audio_file':<27} | {'avg processing':<15} | {'avg WER':<10}\n")
            f.write("-" * 100 + "\n")
            
            for (config, audio_file), results in grouped_results.items():
                if not results:
                    continue
                    
                avg_latency = sum(r['processing_latency'] for r in results) / len(results)
                avg_wer = sum(r['wer_score'] for r in results if r['wer_score'] is not None) / len([r for r in results if r['wer_score'] is not None]) if any(r['wer_score'] is not None for r in results) else None
                
                latency_str = f"{avg_latency:.3f}s"
                wer_str = f"{avg_wer:.3f}" if avg_wer is not None else "N/A"
                
                f.write(f"{config:<30} | {audio_file:<25} | {latency_str:<15} | {wer_str:<10}\n")
                f.write("-" * 100 + "\n")
            
            f.write("\n\nDETAILED RESULTS\n")
            f.write("=" * 100 + "\n")
            
            # Group results by config and audio file for better organization
            grouped_results = {}
            for result in self.results:
                key = (result['config'], result['audio_file'])
                if key not in grouped_results:
                    grouped_results[key] = []
                grouped_results[key].append(result)
            
            # Write detailed results grouped by test
            for (config, audio_file), results in grouped_results.items():
                f.write(f"\nTest: {config} - {audio_file}\n")
                f.write("=" * 80 + "\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"\nIteration #{i}\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Processing Latency: {result['processing_latency']:.3f}s\n")
                    f.write(f"End-to-End Latency: {result['end_to_end_latency']:.3f}s\n")
                    f.write(f"Word Count: {result['word_count']}\n")
                    f.write(f"WER Score: {result['wer_score']:.3f}\n" if result['wer_score'] is not None else "WER Score: N/A\n")
                    
                    if result.get('recorded_transcript'):
                        f.write(f"\nRecorded Transcript:\n{result['recorded_transcript']}\n")
                    
                    if result.get('correct_transcript'):
                        f.write(f"\nReference Transcript:\n{result['correct_transcript']}\n")
                    
                    if 'error' in result:
                        f.write(f"\nERROR: {result['error']}\n")
                
                f.write("\n" + "=" * 80 + "\n")
    
    def print_summary(self, model_display_name, total_tests, json_path):
        """Print a summary of test results"""
        if not self.results:
            print("No results to summarize")
            return
        
        print("Testing Complete")
        print(f"-> Tested {model_display_name} model")
        print(f"-> {len(self.results)}/{total_tests} tests complete")
        print(f"-> Results saved to: {json_path}")
        print()
        
        print("Summary")
        print("-" * 100)
        print(f"| {'config/params':<35} | {'audio_file':<27} | {'avg processing':<15} | {'avg WER':<10} |")
        print("-" * 100)
        
        # Group results by config and audio file
        grouped_results = {}
        for result in self.results:
            if 'error' in result:
                continue
                
            key = (result['config'], result['audio_file'])
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append(result)
        
        # Calculate averages and display
        for (config, audio_file), results in grouped_results.items():
            if not results:
                continue
                
            avg_latency = sum(r['processing_latency'] for r in results) / len(results)
            avg_wer = sum(r['wer_score'] for r in results if r['wer_score'] is not None) / len([r for r in results if r['wer_score'] is not None]) if any(r['wer_score'] is not None for r in results) else None
            
            latency_str = f"{avg_latency:.3f}s"
            wer_str = f"{avg_wer:.3f}" if avg_wer is not None else "N/A"
            
            print(f"| {config:<35} | {audio_file:<25} | {latency_str:<15} | {wer_str:<10} |")
            print("-" * 100)
        
        print()

def main():
    # Create test runner
    runner = TestRunner()
    
    # Run tests for specified model_type
    runner.run_model_tests(CURRENT_MODEL, num_runs_per_config=3)

if __name__ == "__main__":
    main() 