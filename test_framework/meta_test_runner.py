#!/usr/bin/env python3
"""
Meta Test Runner - Orchestrates the complete evaluation pipeline

This script manages the evolution of configurations through testing phases:
- Phase A Round 1: All initial configs (40 total)
- Phase A Round 2: Top 50% from A1 (20 total)
- Phase B Round 1: Best 2+3+3 from A2 (8 total)
- Phase B Round 2: Zoom search configs
- Phase C: Best config from B2

Usage:
    python meta_test_runner.py --phase phase_a_r1
    python meta_test_runner.py --phase phase_a_r2
    etc.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional

from config_manager import ConfigManager
from test_runner import TestRunner

class MetaTestRunner:
    def __init__(self, quick_testing_mode=True):
        """
        Initialize Meta Test Runner
        
        Args:
            quick_testing_mode: If True, use 10sec audio throughout for quick testing.
                               If False, use proper audio lengths (60s/180s/5min/30min) for real evaluation.
        """
        self.quick_testing_mode = quick_testing_mode
        self.config_manager = ConfigManager()
        
        # Define phase dependencies (what needs to be completed before each phase)
        self.phase_dependencies = {
            'phase_a_r1': [],  # No dependencies
            'phase_a_r2': ['phase_a_r1'],
            'phase_b_r1': ['phase_a_r2'],
            'phase_b_r2': ['phase_b_r1'],
            'phase_c': ['phase_b_r2']
        }
        
        # Define which phases get invalidated when a phase is re-run
        self.phase_invalidations = {
            'phase_a_r1': ['phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c'],
            'phase_a_r2': ['phase_b_r1', 'phase_b_r2', 'phase_c'],
            'phase_b_r1': ['phase_b_r2', 'phase_c'],
            'phase_b_r2': ['phase_c'],
            'phase_c': []
        }
    
    def clear_later_phases(self, current_phase: str):
        """Clear registry and results for phases after current_phase"""
        if current_phase not in self.phase_invalidations:
            return
        
        phases_to_clear = self.phase_invalidations[current_phase]
        
        if not phases_to_clear:
            print("✅ No later phases to clear")
            return
        
        print(f"🧹 Clearing later phases: {', '.join(phases_to_clear)}")
        
        # Clear config registry
        for phase in phases_to_clear:
            for model_type in ['fixed', 'vad', 'adaptive', 'combined']:
                config_file = Path('config_registry') / f"{model_type}_{phase}_configs.json"
                if config_file.exists():
                    config_file.unlink()
                    print(f"   📁 Removed: {config_file}")
        
        # Clear test results
        for phase in phases_to_clear:
            # Convert phase_a_r1 -> PHASEAR1, phase_b_r1 -> PHASEBR1, etc.
            phase_pattern = phase.replace('_', '').upper()
            
            # Clear JSON results
            json_files = list(Path('test_results/json_results').glob(f'*{phase_pattern}*'))
            for file in json_files:
                file.unlink()
                print(f"   📊 Removed: {file}")
            
            # Clear report results
            report_files = list(Path('test_results/report_results').glob(f'*{phase_pattern}*'))
            for file in report_files:
                file.unlink()
                print(f"   📋 Removed: {file}")
            
            # Clear CSV results
            csv_files = list(Path('test_results/csv_results').glob(f'*{phase_pattern}*'))
            for file in csv_files:
                file.unlink()
                print(f"   📈 Removed: {file}")
        
        print("✅ Later phases cleared successfully")
    
    def validate_phase_prerequisites(self, phase_name: str) -> bool:
        """Check if all prerequisite phases have been completed"""
        if phase_name not in self.phase_dependencies:
            print(f"Error: Unknown phase '{phase_name}'")
            return False
        
        required_phases = self.phase_dependencies[phase_name]
        
        for required_phase in required_phases:
            # Check if results exist for this phase
            # Convert phase_a_r1 -> PHASEAR1, phase_b_r1 -> PHASEBR1, etc.
            phase_pattern = required_phase.replace('_', '').upper()
            result_files = list(Path('test_results/json_results').glob(f'*{phase_pattern}*'))
            if not result_files:
                print(f"Error: Phase '{phase_name}' requires '{required_phase}' to be completed first")
                print(f"Missing results for: {required_phase}")
                return False
        
        print(f"✅ All prerequisites met for {phase_name}")
        return True
    
    def check_phase_invalidations(self, phase_name: str) -> List[str]:
        """Check which phases will be invalidated if we re-run this phase"""
        if phase_name not in self.phase_invalidations:
            return []
        
        invalidated_phases = self.phase_invalidations[phase_name]
        existing_invalidated = []
        
        for invalid_phase in invalidated_phases:
            # Convert phase_a_r1 -> PHASEAR1, phase_b_r1 -> PHASEBR1, etc.
            phase_pattern = invalid_phase.replace('_', '').upper()
            result_files = list(Path('test_results/json_results').glob(f'*{phase_pattern}*'))
            if result_files:
                existing_invalidated.append(invalid_phase)
        
        return existing_invalidated
    
    def run_test_runner_for_model(self, model_type: str, test_mode: str, configs=None):
        """Run test_runner.py for a specific model type"""
        import sys
        
        print(f"🔧 Running test_runner for {model_type} model...")
        sys.stdout.flush()
        
        # Import test_runner module
        import test_runner
        
        # Set audio source based on test mode and quick testing flag
        if self.quick_testing_mode:
            # Quick testing mode: Use 10sec audio throughout
            audio_source = '10sec'
            print(f"🔬 Quick testing mode: Using 10sec audio")
        else:
            # Real evaluation mode: Use proper audio lengths
            if test_mode == 'phase_a_r1':
                audio_source = '60sec'  # 60-90s clips
            elif test_mode == 'phase_a_r2':
                audio_source = '180sec'  # 180s clips
            elif test_mode in ['phase_b_r1', 'phase_b_r2']:
                audio_source = '5min'  # 5-minute clips
            elif test_mode == 'phase_c':
                audio_source = '30min'  # 30-minute clips
            else:
                audio_source = '10sec'  # fallback
            print(f"🎯 Real evaluation mode: Using {audio_source} audio")
        
        sys.stdout.flush()
        
        # Run test_runner with appropriate iterations for each phase
        # Change these numbers to adjust iterations per phase:
        # - phase_a_r1: 1 iteration (quick screening)
        # - phase_a_r2: 2 iterations (more reliable)
        # - phase_b_r1: 3 iterations (detailed evaluation)
        # - phase_b_r2: 3 iterations (zoom validation)
        # - phase_c: 5 iterations (final comparison)
        
        # For quick testing, use fewer iterations
        if self.quick_testing_mode:
            iterations = 1  # Quick testing: 1 iteration
        else:
            # Real evaluation: more iterations for important phases
            if test_mode == 'phase_c':
                iterations = 3  # Final comparison: 5 iterations
            elif test_mode in ['phase_b_r1', 'phase_b_r2']:
                iterations = 3  # Detailed phases: 3 iterations
            elif test_mode == 'phase_a_r2':
                iterations = 3  # Selection phase: 2 iterations
            else:
                iterations = 3  # Initial screening: 1 iteration
        
        results = test_runner.main(
            model_type=model_type,
            test_mode=test_mode,
            audio_source=audio_source,
            configs=configs,
            iterations=iterations
        )
        
        print(f"✅ TestRunner completed for {model_type}")
        sys.stdout.flush()
        return results
    
    def load_phase_results(self, phase_name: str) -> List[Dict]:
        """Load results from JSON files for a specific phase"""
        import json
        
        # Convert phase_a_r1 -> PHASEAR1, phase_b_r1 -> PHASEBR1, etc.
        phase_pattern = phase_name.replace('_', '').upper()
        
        # Find all result files for this phase
        result_files = list(Path('test_results/json_results').glob(f'*{phase_pattern}*'))
        
        if not result_files:
            print(f"⚠️  No result files found for {phase_name}")
            return []
        
        all_results = []
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_results.extend(data)
                    else:
                        print(f"⚠️  Unexpected format in {result_file}")
            except Exception as e:
                print(f"⚠️  Error loading {result_file}: {e}")
        
        print(f"📊 Loaded {len(all_results)} results from {len(result_files)} files")
        return all_results
    
    def run_phase_a_r1(self):
        """Run Phase A Round 1: All initial configs (40 total)"""
        print("=== Phase A Round 1: Running all initial configs ===")
        
        # Initialize all configs
        self.config_manager.initialize_phase_a_r1('combined')
        
        # Run test_runner for each model type
        model_types = ['fixed', 'vad', 'adaptive']
        all_results = []
        
        for model_type in model_types:
            print(f"\n--- Running {model_type.upper()} configs ---")
            results = self.run_test_runner_for_model(model_type, 'phase_a_r1')
            all_results.extend(results)
        
        print(f"\n✅ Phase A Round 1 completed")
        print(f"📊 Total results: {len(all_results)}")
        print("🔍 Review results before running phase_a_r2")
        
        return all_results
    
    def run_phase_a_r2(self):
        """Run Phase A Round 2: Top 50% from A1 (20 total)"""
        print("=== Phase A Round 2: Running top 50% configs ===")
        
        # Load results from Phase A Round 1
        print("📊 Loading Phase A Round 1 results...")
        results_data = self.load_phase_results('phase_a_r1')
        if not results_data:
            print("❌ No results found for Phase A Round 1")
            return None
        
        # Evolve configs using results data
        self.config_manager.evolve_configs('phase_a_r1', 'phase_a_r2', 'combined', results_data)
        
        # Get evolved configs for each model type
        model_types = ['fixed', 'vad', 'adaptive']
        all_results = []
        
        for model_type in model_types:
            configs = self.config_manager.get_phase_configs(model_type, 'phase_a_r2')
            if configs:
                print(f"\n--- Running {model_type.upper()} configs (top 50%) ---")
                print(f"📋 Testing {len(configs)} configurations")
                results = self.run_test_runner_for_model(model_type, 'phase_a_r2', configs)
                all_results.extend(results)
            else:
                print(f"⚠️  No configs found for {model_type} in phase_a_r2")
        
        print(f"\n✅ Phase A Round 2 completed")
        print(f"📊 Total results: {len(all_results)}")
        print("🔍 Review results before running phase_b_r1")
        
        return all_results
    
    def run_phase_b_r1(self):
        """Run Phase B Round 1: Best 2+3+3 from A2 (8 total)"""
        print("=== Phase B Round 1: Running best 2+3+3 configs ===")
        
        # Load results from Phase A Round 2
        print("📊 Loading Phase A Round 2 results...")
        results_data = self.load_phase_results('phase_a_r2')
        if not results_data:
            print("❌ No results found for Phase A Round 2")
            return None
        
        # Evolve configs using results data
        self.config_manager.evolve_configs('phase_a_r2', 'phase_b_r1', 'combined', results_data)
        
        # Get evolved configs for each model type
        model_types = ['fixed', 'vad', 'adaptive']
        all_results = []
        
        for model_type in model_types:
            configs = self.config_manager.get_phase_configs(model_type, 'phase_b_r1')
            if configs:
                print(f"\n--- Running {model_type.upper()} configs (best 2+3+3) ---")
                print(f"📋 Testing {len(configs)} configurations")
                results = self.run_test_runner_for_model(model_type, 'phase_b_r1', configs)
                all_results.extend(results)
            else:
                print(f"⚠️  No configs found for {model_type} in phase_b_r1")
        
        print(f"\n✅ Phase B Round 1 completed")
        print(f"📊 Total results: {len(all_results)}")
        print("🔍 Review results before running phase_b_r2")
        
        return all_results
    
    def run_phase_b_r2(self):
        """Run Phase B Round 2: Zoom search configs"""
        print("=== Phase B Round 2: Running zoom search configs ===")
        
        # Load results from Phase B Round 1
        print("📊 Loading Phase B Round 1 results...")
        results_data = self.load_phase_results('phase_b_r1')
        if not results_data:
            print("❌ No results found for Phase B Round 1")
            return None
        
        # Evolve configs using zoom search
        self.config_manager.evolve_configs('phase_b_r1', 'phase_b_r2', 'combined', results_data)
        
        # Get evolved configs for each model type
        model_types = ['fixed', 'vad', 'adaptive']
        all_results = []
        zoom_comparisons = {}
        
        for model_type in model_types:
            configs = self.config_manager.get_phase_configs(model_type, 'phase_b_r2')
            if configs:
                print(f"\n--- Running {model_type.upper()} zoom search configs ---")
                print(f"📋 Testing {len(configs)} zoom search configurations")
                results = self.run_test_runner_for_model(model_type, 'phase_b_r2', configs)
                all_results.extend(results)
                
                # Compare zoom results with original
                from zoom_search import ZoomSearch
                zoom_search = ZoomSearch()
                comparison = zoom_search.compare_zoom_results(results_data, results, model_type)
                zoom_comparisons[model_type] = comparison
            else:
                print(f"⚠️  No zoom search configs found for {model_type} in phase_b_r2")
        
        # Print zoom search comparison summary
        print(f"\n{'='*80}")
        print("🔍 ZOOM SEARCH PERFORMANCE COMPARISON")
        print(f"{'='*80}")
        
        for model_type in model_types:
            if model_type in zoom_comparisons:
                comparison = zoom_comparisons[model_type]
                print(f"\n{model_type.upper()} Model:")
                print(comparison['summary'])
        
        print(f"\n✅ Phase B Round 2 completed")
        print(f"📊 Total results: {len(all_results)}")
        print("🔍 Review results before running phase_c")
        
        return all_results
    
    def run_phase_c(self):
        """Run Phase C: Final comparison of best configs from each model"""
        print("=== Phase C: Final comparison of best configs ===")
        
        # Determine which results to use for selecting best configs
        # Check if Phase B Round 2 improved any models
        phase_b_r2_results = self.load_phase_results('phase_b_r2')
        phase_b_r1_results = self.load_phase_results('phase_b_r1')
        
        if not phase_b_r1_results:
            print("❌ No results found for Phase B Round 1")
            return None
        
        # Select best configs for each model type
        best_configs = self._select_best_configs_for_phase_c(phase_b_r1_results, phase_b_r2_results)
        

        
        if not best_configs:
            print("❌ No best configs found for Phase C")
            return None
        
        print(f"📋 Selected best configs for Phase C:")
        for model_type, config in best_configs.items():
            print(f"   {model_type.upper()}: {config.get('description', 'Unknown')}")
        
        # Run tests for each best config
        all_results = []
        
        for model_type, config in best_configs.items():
            print(f"\n--- Testing {model_type.upper()} best config ---")
            results = self.run_test_runner_for_model(model_type, 'phase_c', [config])
            all_results.extend(results)
        
        # Determine overall winner
        winner = self._determine_overall_winner(all_results)
        
        # Print final results
        print(f"\n{'='*80}")
        print("🏆 PHASE C FINAL RESULTS")
        print(f"{'='*80}")
        
        for model_type in ['fixed', 'vad', 'adaptive']:
            model_results = [r for r in all_results if r.get('model_type') == model_type]
            if model_results:
                avg_wer = sum(r['wer_score'] for r in model_results if r['wer_score'] is not None) / len(model_results)
                avg_latency = sum(r['processing_latency'] for r in model_results) / len(model_results)
                print(f"\n{model_type.upper()} Model:")
                print(f"   Config: {model_results[0].get('config', 'Unknown')}")
                print(f"   WER: {avg_wer:.3f}")
                print(f"   Avg Latency: {avg_latency:.3f}s")
        
        print(f"\n🏆 OVERALL WINNER: {winner.upper()} MODEL")
        print(f"✅ Phase C completed successfully!")
        
        return all_results
    
    def _select_best_configs_for_phase_c(self, phase_b_r1_results, phase_b_r2_results):
        """Select the best config for each model type for Phase C"""
        from zoom_search import ZoomSearch
        zoom_search = ZoomSearch()
        
        best_configs = {}
        
        for model_type in ['fixed', 'vad', 'adaptive']:
            # Get Phase B Round 1 best config
            phase_b_r1_model_results = [r for r in phase_b_r1_results if r.get('model_type') == model_type]
            if not phase_b_r1_model_results:
                continue
            
            config_averages = zoom_search._calculate_config_averages(phase_b_r1_model_results)
            if not config_averages:
                continue
            
            # Sort by WER, then by p90 latency
            config_averages.sort(key=lambda x: (
                x[1]['avg_wer'] if x[1]['avg_wer'] is not None else float('inf'),
                x[1]['avg_p90_latency']
            ))
            
            best_phase_b_r1_config_desc = config_averages[0][0]
            best_phase_b_r1_wer = config_averages[0][1]['avg_wer']
            
            # Check if Phase B Round 2 improved this model
            phase_b_r2_model_results = [r for r in phase_b_r2_results if r.get('model_type') == model_type]
            improved = False
            best_config = None
            
            if phase_b_r2_model_results:
                # Compare with zoom search results
                comparison = zoom_search.compare_zoom_results(phase_b_r1_model_results, phase_b_r2_model_results, model_type)
                improved = comparison['improved']
                
                if improved:
                    # Use zoom search config
                    best_config = zoom_search._reconstruct_config_from_result(phase_b_r2_model_results[0])
                    print(f"   ✅ {model_type.upper()}: Using improved zoom config (WER: {comparison['zoom_wer']:.3f} vs {comparison['original_wer']:.3f})")
                else:
                    # Use original best config
                    for result in phase_b_r1_model_results:
                        if result.get('config') == best_phase_b_r1_config_desc:
                            best_config = zoom_search._reconstruct_config_from_result(result)
                            break
                    print(f"   ❌ {model_type.upper()}: Using original best config (zoom worsened performance)")
            else:
                # No zoom search results, use original best
                for result in phase_b_r1_model_results:
                    if result.get('config') == best_phase_b_r1_config_desc:
                        best_config = zoom_search._reconstruct_config_from_result(result)
                        break
                print(f"   📊 {model_type.upper()}: Using original best config (no zoom search)")
            
            if best_config:
                best_configs[model_type] = best_config
        
        return best_configs
    
    def _determine_overall_winner(self, results):
        """Determine the overall winner based on WER and latency"""
        model_performance = {}
        
        for model_type in ['fixed', 'vad', 'adaptive']:
            model_results = [r for r in results if r.get('model_type') == model_type]
            if not model_results:
                continue
            
            # Calculate averages
            avg_wer = sum(r['wer_score'] for r in model_results if r['wer_score'] is not None) / len(model_results)
            avg_latency = sum(r['processing_latency'] for r in model_results) / len(model_results)
            
            model_performance[model_type] = {
                'avg_wer': avg_wer,
                'avg_latency': avg_latency
            }
        
        if not model_performance:
            return "unknown"
        
        # Find best model (lowest WER, then lowest latency as tie-breaker)
        best_model = min(model_performance.keys(), 
                        key=lambda m: (model_performance[m]['avg_wer'], model_performance[m]['avg_latency']))
        
        return best_model
    
    def run_phase(self, phase_name: str):
        """Run a specific phase with validation and automatic clearing"""
        print(f"🚀 Starting {phase_name}")
        print("=" * 50)
        
        # Check prerequisites
        if not self.validate_phase_prerequisites(phase_name):
            return False
        
        # Automatically clear later phases to ensure clean slate
        self.clear_later_phases(phase_name)
        
        # Run the phase
        if phase_name == 'phase_a_r1':
            self.run_phase_a_r1()
        elif phase_name == 'phase_a_r2':
            self.run_phase_a_r2()
        elif phase_name == 'phase_b_r1':
            self.run_phase_b_r1()
        elif phase_name == 'phase_b_r2':
            self.run_phase_b_r2()
        elif phase_name == 'phase_c':
            self.run_phase_c()
        else:
            print(f"Error: Unknown phase '{phase_name}'")
            return False
        
        return True

    def show_phase_status(self):
        """Show the current status of all phases"""
        print("📊 Current Phase Status")
        print("=" * 50)
        
        phases = ['phase_a_r1', 'phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c']
        
        for phase in phases:
            # Check if results exist
            # Convert phase_a_r1 -> PHASEAR1, phase_b_r1 -> PHASEBR1, etc.
            phase_pattern = phase.replace('_', '').upper()
            result_files = list(Path('test_results/json_results').glob(f'*{phase_pattern}*'))
            
            # Check if configs exist
            config_files = []
            for model_type in ['fixed', 'vad', 'adaptive', 'combined']:
                config_file = Path('config_registry') / f"{model_type}_{phase}_configs.json"
                if config_file.exists():
                    config_files.append(model_type)
            
            status = "✅" if result_files else "❌"
            config_status = f"Configs: {', '.join(config_files)}" if config_files else "No configs"
            
            print(f"{status} {phase}: {len(result_files)} result files | {config_status}")
        
        print("\n💡 Next steps:")
        print("   - Run: python meta_test_runner.py --phase <phase_name>")
        print("   - Status: python meta_test_runner.py --status")

def main():
    parser = argparse.ArgumentParser(description='Meta Test Runner for ASR Evaluation')
    parser.add_argument('--phase', 
                       choices=['phase_a_r1', 'phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c'],
                       help='Phase to run')
    parser.add_argument('--status', action='store_true',
                       help='Show current status of all phases')
    parser.add_argument('--quick-testing', action='store_true', default=True,
                       help='Use quick testing mode (10sec audio throughout) [default: True]')
    parser.add_argument('--real-evaluation', action='store_true',
                       help='Use real evaluation mode (proper audio lengths: 60s/180s/5min/30min)')
    
    args = parser.parse_args()
    
    # Determine testing mode
    quick_testing_mode = args.quick_testing and not args.real_evaluation
    
    # Create directories if they don't exist
    Path('test_results/json_results').mkdir(parents=True, exist_ok=True)
    Path('test_results/report_results').mkdir(parents=True, exist_ok=True)
    Path('test_results/csv_results').mkdir(parents=True, exist_ok=True)
    Path('config_registry').mkdir(exist_ok=True)
    
    # Run the meta test runner
    meta_runner = MetaTestRunner(quick_testing_mode=quick_testing_mode)
    
    if args.status:
        meta_runner.show_phase_status()
    elif args.phase:
        success = meta_runner.run_phase(args.phase)
        if success:
            print(f"\n✅ {args.phase} completed successfully!")
        else:
            print(f"\n❌ {args.phase} failed!")
    else:
        parser.print_help()
        print("\n💡 Try:")
        print("   python meta_test_runner.py --status")
        print("   python meta_test_runner.py --phase phase_a_r1")

if __name__ == "__main__":
    main() 