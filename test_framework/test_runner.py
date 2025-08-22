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
import csv
import contextlib
import io
from pathlib import Path
from datetime import datetime
import re
import numpy as np

# Add transcriber_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metrics_collector import MetricsCollector
from configs import TEST_CONFIGS
from transcriber_app.main import start_transcription_pipeline_with_virtual_audio, stop_transcription_pipeline
import transcriber_app.main as main_module

# Change these flags at the top of test_runner.py
CURRENT_MODEL = 'vad'     # Select model: 'fixed', 'vad', 'adaptive'
AUDIO_SOURCE = '10sec'      # Select which audio set to test: '10sec', '5min', or '30min'
TEST_MODE = 'phase_a_r1'    # Select test mode for different phases: 'phase_a_r1', 'phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c'

class TestRunner:
    def __init__(self, test_audio_dir="audio_files", results_dir="test_results", audio_source=AUDIO_SOURCE, test_mode=TEST_MODE):
        self.test_audio_dir = Path(test_audio_dir)  
        self.results_dir = Path(results_dir)        
        self.json_dir = self.results_dir / "json_results"
        self.report_dir = self.results_dir / "report_results"
        self.csv_dir = self.results_dir / "csv_results"
        self.audio_source = audio_source
        self.test_mode = test_mode
        
        # Set duration limits based on test mode
        self.duration_limits = {
            'phase_a_r1': 60,    # 60 seconds
            'phase_a_r2': 180,   # 180 seconds (3 minutes)
            'phase_b_r1': None,  # Full 5-minute clips
            'phase_b_r2': None,  # Full 5-minute clips
            'phase_c': None      # Full 30-minute clips
        }
        self.max_duration = self.duration_limits.get(self.test_mode)
        
        # Create directories
        self.results_dir.mkdir(exist_ok=True)
        self.json_dir.mkdir(exist_ok=True)
        self.report_dir.mkdir(exist_ok=True)
        self.csv_dir.mkdir(exist_ok=True)
        
        self.results = []
        
    def find_audio_files(self):
        """Find audio files based on selected source in audio_files directory"""
        source = (self.audio_source or '').lower()
        if source == '10sec':
            audio_path = self.test_audio_dir / '10sec_version' / '10sec_test.mp3'
            if audio_path.exists():
                return [audio_path]
            print(f"Warning: {audio_path} not found")
            return []
        elif source == '5min':
            base_dir = self.test_audio_dir / '5min_versions'
            audio_files = []
            if not base_dir.exists():
                print(f"Warning: {base_dir} directory not found")
                return audio_files
            for pattern in ('*.mp3', '*.wav'):
                audio_files.extend(base_dir.glob(pattern))
            return audio_files
        elif source == '30min':
            base_dir = self.test_audio_dir / '30min_versions'
            audio_files = []
            if not base_dir.exists():
                print(f"Warning: {base_dir} directory not found")
                return audio_files
            for pattern in ('*.mp3', '*.wav'):
                audio_files.extend(base_dir.glob(pattern))
            return audio_files
        else:
            # Fallback to 10sec if misconfigured
            audio_path = self.test_audio_dir / '10sec_test.mp3'
            if audio_path.exists():
                return [audio_path]
            print(f"Warning: Unknown AUDIO_SOURCE '{self.audio_source}'. {audio_path} not found")
            return []

    def get_audio_source_display(self):
        mapping = {'10sec': '10sec', '5min': '5min', '30min': '30min'}
        return mapping.get((self.audio_source or '').lower(), str(self.audio_source))
    
    def load_reference_transcript(self, audio_file):
        """Load reference transcript for WER calculation"""
        # Select transcript directory based on audio source
        source = (self.audio_source or '').lower()
        if source == '5min':
            transcript_dir = Path("transcripts/edited_transcripts/5min_transcripts")
        elif source == '30min':
            transcript_dir = Path("transcripts/edited_transcripts/30min_transcripts")
        elif source == '10sec':
            transcript_dir = Path("transcripts/edited_transcripts/10sec_transcript")
        else:
            # No reference transcripts for 10-second quick tests
            print(" -> No reference transcript for 10sec tests (WER disabled)")
            return None
        
        # Map audio filename to transcript filename (assumes matching base names)
        transcript_basename = Path(audio_file).with_suffix('.txt').name
        transcript_file = transcript_dir / transcript_basename
        
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
            print("No audio files found. Please add audio files to audio_files/ directory")
            return
        
        # Get configurations for the specified model
        if model_type not in TEST_CONFIGS:
            print(f"Error: Model type '{model_type}' not found in TEST_CONFIGS")
            return
        
        configs = TEST_CONFIGS[model_type]
        
        # Sort configurations for logical execution order
        configs = self.sort_configurations(configs, model_type)
        
        # Calculate total tests
        total_tests = len(audio_files) * len(configs) * num_runs_per_config
        
        print(f"-> Testing {model_display_name} model")
        print(f"-> Testing {len(audio_files)} audio files ({self.get_audio_source_display()})")
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
        csv_path = self.save_results_csv(model_type)
        config_averages = self.calculate_config_averages()
        if config_averages:
            avg_csv_path = self.save_averages_csv(model_type, config_averages)
        else:
            avg_csv_path = None
        self.print_summary(model_display_name, total_tests, json_path, csv_path, avg_csv_path)

    def run_specific_configs(self, model_type, configs, num_runs_per_config=1):
        """Run tests for a specific model type with provided configurations"""
        import sys
        
        model_display_name = self.get_model_display_name(model_type)
        
        print("\n" + ("=" * 100))
        print("Testing Session (Specific Configs)")
        print("=" * 100)
        
        # Find audio files
        audio_files = self.find_audio_files()
        if not audio_files:
            print("No audio files found. Please add audio files to audio_files/ directory")
            return
        
        # Sort configurations for logical execution order
        configs = self.sort_configurations(configs, model_type)
        
        # Calculate total tests
        total_tests = len(audio_files) * len(configs) * num_runs_per_config
        
        print(f"-> Testing {model_display_name} model")
        print(f"-> Testing {len(audio_files)} audio files ({self.get_audio_source_display()})")
        print(f"-> Testing {len(configs)} specific configurations")
        print(f"-> Testing {num_runs_per_config} iterations per audio per configuration")
        print(f"-> TOTAL: {total_tests} tests")
        print()
        sys.stdout.flush()
        
        current_test = 0
        
        # For each audio file
        for audio_idx, audio_file in enumerate(audio_files, 1):
            print(f"Audio {audio_idx}/{len(audio_files)} ({audio_file.name})")
            print("-" * 80)
            
            # Print table header
            print(f"| {'config/params':<35} | {'iteration':<12} | {'Processing':<12} | {'WER':<8} |")
            print("-" * 80)
            sys.stdout.flush()
            
            # For each configuration
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
                    sys.stdout.flush()
                    
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
                    sys.stdout.flush()
            
            print()  # Empty line between audio files
            sys.stdout.flush()
        
        # Save results
        json_path = self.save_results(model_type)
        csv_path = self.save_results_csv(model_type)
        config_averages = self.calculate_config_averages()
        if config_averages:
            avg_csv_path = self.save_averages_csv(model_type, config_averages)
        else:
            avg_csv_path = None
        self.print_summary(model_display_name, total_tests, json_path, csv_path, avg_csv_path)
    
    def sort_configurations(self, configs, model_type):
        """Sort configurations for logical execution order"""
        if model_type == 'fixed':
            # Sort by chunk size (smaller to larger)
            return sorted(configs, key=lambda x: x['chunk_size'])
        elif model_type == 'vad':
            # Sort by aggressiveness, then frame duration, then silence frames
            return sorted(configs, key=lambda x: (
                x.get('aggressiveness', 0),
                x.get('frame_duration_ms', 0),
                x.get('max_silence_frames', 0)
            ))
        elif model_type == 'adaptive':
            # Sort by starting aggressiveness, then frame duration
            return sorted(configs, key=lambda x: (
                x.get('starting_aggressiveness', 0),
                x.get('frame_duration_ms', 0)
            ))
        else:
            return configs
    
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
                
                # Wait for transcription to complete or duration limit reached
                start_time = time.time()
                while main_module.transcription_thread and main_module.transcription_thread.is_alive():
                    if self.max_duration and (time.time() - start_time) > self.max_duration:
                        print(f" -> Stopping test after {self.max_duration}s (duration limit)")
                        break
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
                'p50_processing_latency': latency_metrics['p50_processing_latency'],
                'p90_processing_latency': latency_metrics['p90_processing_latency'],
                'end_to_end_latency': latency_metrics['avg_end_to_end_latency'],
                'p50_end_to_end_latency': latency_metrics['p50_end_to_end_latency'],
                'p90_end_to_end_latency': latency_metrics['p90_end_to_end_latency'],
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
                'p50_processing_latency': 0,
                'p90_processing_latency': 0,
                'end_to_end_latency': 0,
                'p50_end_to_end_latency': 0,
                'p90_end_to_end_latency': 0,
                'wer_score': None,
                'recorded_transcript': '',
                'correct_transcript': reference_transcript if reference_transcript else '',
                'error': str(e)
            }

    def save_results(self, model_type):
        """Save test results to JSON file and create readable report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_display_name = self.get_model_display_name(model_type).replace(" ", "_")
        phase_name = self.test_mode.replace("_", "").upper()
        
        json_path = self.json_dir / f"{model_display_name}_{phase_name}_RAW_{timestamp}.json"
        report_path = self.report_dir / f"{model_display_name}_{phase_name}_RAW_{timestamp}.txt"
        
        # Save JSON for programmatic access
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Create human-readable report
        self.create_readable_report(report_path)
        
        return json_path

    def save_results_csv(self, model_type):
        """Save test results to CSV file for easy analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_display_name = self.get_model_display_name(model_type).replace(" ", "_")
        phase_name = self.test_mode.replace("_", "").upper()
        
        csv_path = self.csv_dir / f"{model_display_name}_{phase_name}_RAW_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'config', 'audio_file', 'model_type', 'wer_score', 
                'avg_processing_latency', 'p50_processing_latency', 'p90_processing_latency',
                'avg_end_to_end_latency', 'p50_end_to_end_latency', 'p90_end_to_end_latency',
                'word_count', 'test_mode', 'audio_source'
            ])
            
            # Write data rows
            for result in self.results:
                writer.writerow([
                    result['config'],
                    result['audio_file'],
                    result['model_type'],
                    result['wer_score'] if result['wer_score'] is not None else '',
                    f"{result['processing_latency']:.6f}",
                    f"{result['p50_processing_latency']:.6f}",
                    f"{result['p90_processing_latency']:.6f}",
                    f"{result['end_to_end_latency']:.6f}",
                    f"{result['p50_end_to_end_latency']:.6f}",
                    f"{result['p90_end_to_end_latency']:.6f}",
                    result['word_count'],
                    self.test_mode,
                    self.audio_source
                ])
        
        return csv_path

    def save_averages_csv(self, model_type, config_averages):
        """Save configuration averages to separate CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_display_name = self.get_model_display_name(model_type).replace(" ", "_")
        phase_name = self.test_mode.replace("_", "").upper()
        
        avg_csv_path = self.csv_dir / f"{model_display_name}_{phase_name}_AVG_{timestamp}.csv"
        
        with open(avg_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'rank', 'config', 'avg_wer', 'avg_processing_latency', 
                'p50_processing_latency', 'p90_processing_latency',
                'avg_end_to_end_latency', 'p50_end_to_end_latency', 'p90_end_to_end_latency',
                'num_runs', 'test_mode', 'audio_source'
            ])
            
            # Write data rows
            for i, (config, metrics) in enumerate(config_averages, 1):
                writer.writerow([
                    i,
                    config,
                    f"{metrics['avg_wer']:.6f}" if metrics['avg_wer'] is not None else '',
                    f"{metrics['avg_latency']:.6f}",
                    f"{metrics['avg_p50_latency']:.6f}",
                    f"{metrics['avg_p90_latency']:.6f}",
                    f"{metrics['avg_e2e_latency']:.6f}",
                    f"{metrics['avg_p50_e2e_latency']:.6f}",
                    f"{metrics['avg_p90_e2e_latency']:.6f}",
                    metrics['num_runs'],
                    self.test_mode,
                    self.audio_source
                ])
        
        return avg_csv_path

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
    
    def print_summary(self, model_display_name, total_tests, json_path, csv_path, avg_csv_path):
        """Print a summary of test results with configuration ranking"""
        if not self.results:
            print("No results to summarize")
            return
        
        print("Testing Complete")
        print(f"-> Tested {model_display_name} model")
        print(f"-> Testing ({self.get_audio_source_display()}) audio files")
        print(f"-> Test mode: {self.test_mode}")
        print(f"-> {len(self.results)}/{total_tests} tests complete")
        print(f"-> Results saved to: {json_path}")
        print(f"-> CSV results saved to: {csv_path}")
        if avg_csv_path:
            print(f"-> Averages CSV saved to: {avg_csv_path}")
        print()
        
        # Rank configurations by their average performance
        config_averages = self.calculate_config_averages()
        if config_averages:
            print("Configuration Rankings (by average WER, then p90 latency):")
            print("-" * 100)
            print(f"| {'Rank':<4} | {'Configuration':<50} | {'Avg WER':<8} | {'Avg p90 latency':<15} | {'Avg latency':<12} |")
            print("-" * 100)
            
            for i, (config, metrics) in enumerate(config_averages, 1):
                config_name = config[:49]  # Truncate if too long
                avg_wer = f"{metrics['avg_wer']:.3f}" if metrics['avg_wer'] is not None else "N/A"
                avg_p90 = f"{metrics['avg_p90_latency']:.3f}s"
                avg_latency = f"{metrics['avg_latency']:.3f}s"
                print(f"| {i:<4} | {config_name:<50} | {avg_wer:<8} | {avg_p90:<15} | {avg_latency:<12} |")
            
            print("-" * 100)
            print()

    def calculate_config_averages(self):
        """Calculate average metrics for each configuration across all runs"""
        config_groups = {}
        
        # Group results by configuration
        for result in self.results:
            if 'error' in result:
                continue
                
            config = result['config']
            if config not in config_groups:
                config_groups[config] = []
            config_groups[config].append(result)
        
        # Calculate averages for each configuration
        config_averages = []
        for config, runs in config_groups.items():
            if not runs:
                continue
                
            # Calculate averages
            avg_wer = None
            wer_scores = [r['wer_score'] for r in runs if r['wer_score'] is not None]
            if wer_scores:
                avg_wer = sum(wer_scores) / len(wer_scores)
            
            avg_latency = sum(r['processing_latency'] for r in runs) / len(runs)
            avg_p90_latency = sum(r['p90_processing_latency'] for r in runs) / len(runs)
            avg_p50_latency = sum(r['p50_processing_latency'] for r in runs) / len(runs)
            avg_e2e_latency = sum(r['end_to_end_latency'] for r in runs) / len(runs)
            avg_p50_e2e_latency = sum(r['p50_end_to_end_latency'] for r in runs) / len(runs)
            avg_p90_e2e_latency = sum(r['p90_end_to_end_latency'] for r in runs) / len(runs)
            
            config_averages.append((config, {
                'avg_wer': avg_wer,
                'avg_latency': avg_latency,
                'avg_p90_latency': avg_p90_latency,
                'avg_p50_latency': avg_p50_latency,
                'avg_e2e_latency': avg_e2e_latency,
                'avg_p50_e2e_latency': avg_p50_e2e_latency,
                'avg_p90_e2e_latency': avg_p90_e2e_latency,
                'num_runs': len(runs)
            }))
        
        # Sort by WER, then by p90 latency
        config_averages.sort(key=lambda x: (x[1]['avg_wer'] if x[1]['avg_wer'] is not None else float('inf'), x[1]['avg_p90_latency']))
        
        return config_averages



def main(model_type=None, test_mode=None, audio_source=None, configs=None, iterations=None):
    """
    Main function for test runner
    
    Args:
        model_type: 'fixed', 'vad', or 'adaptive'
        test_mode: 'phase_a_r1', 'phase_a_r2', etc.
        audio_source: '10sec', '5min', or '30min'
        configs: List of configs to test (if None, uses all configs for model_type)
    """
    # Use provided parameters or fall back to global variables
    model_type = model_type or CURRENT_MODEL
    test_mode = test_mode or TEST_MODE
    audio_source = audio_source or AUDIO_SOURCE
    
    print(f"🚀 TestRunner: Running {model_type} model in {test_mode} mode with {audio_source} audio")
    
    # Create test runner
    runner = TestRunner(audio_source=audio_source, test_mode=test_mode)
    
    # Run tests for specified model_type
    if configs:
        # Use provided configs (for evolved phases)
        print(f"📋 Testing {len(configs)} provided configurations")
        runner.run_specific_configs(model_type, configs, num_runs_per_config=iterations or 2)
    else:
        # Use all configs for model_type (for initial phases)
        print(f"📋 Testing all configurations for {model_type}")
        runner.run_model_tests(model_type, num_runs_per_config=iterations or 1)
    
    return runner.results

if __name__ == "__main__":
    main() 