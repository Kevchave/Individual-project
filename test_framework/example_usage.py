#!/usr/bin/env python3
"""
Example usage of the integrated zoom search functionality

This shows how Phase B Round 2 reads results from Round 1 and performs zoom search.
"""

from test_runner import TestRunner

def example_phase_b_workflow():
    """Example of the complete Phase B workflow"""
    
    print("=== Phase B Complete Workflow Example ===")
    print("This demonstrates the two-step process:")
    print("1. Phase B Round 1: Test all configurations from configs.py")
    print("2. Phase B Round 2: Read Round 1 results, perform zoom search")
    print()
    
    # Step 1: Phase B Round 1
    print("STEP 1: Phase B Round 1")
    print("-" * 50)
    print("Running initial configuration tests...")
    
    runner_r1 = TestRunner(
        audio_source='10sec',      # Use 10sec audio for faster testing
        test_mode='phase_b_r1'     # Initial tests
    )
    
    # Run initial tests for VAD model
    runner_r1.run_model_tests('vad', num_runs_per_config=2)
    
    print("\nPhase B Round 1 complete!")
    print("Results saved with '_phase_b_r1_' prefix")
    print()
    
    # Step 2: Phase B Round 2
    print("STEP 2: Phase B Round 2")
    print("-" * 50)
    print("Reading Round 1 results and performing zoom search...")
    
    runner_r2 = TestRunner(
        audio_source='10sec',      # Same audio source
        test_mode='phase_b_r2'     # This triggers reading Round 1 results
    )
    
    # Run zoom search (automatically reads Round 1 results)
    runner_r2.run_model_tests('vad', num_runs_per_config=2)
    
    print("\nPhase B Round 2 complete!")
    print("Results saved with '_phase_b_r2_' prefix")

def example_manual_zoom_search():
    """Example of manually running zoom search after Phase B Round 1"""
    
    print("=== Manual Zoom Search Example ===")
    print("This shows how to manually run zoom search after Phase B Round 1")
    print()
    
    # First, run Phase B Round 1
    runner = TestRunner(
        audio_source='10sec',
        test_mode='phase_b_r1'     # No automatic zoom search
    )
    
    # Run initial tests
    runner.run_model_tests('vad', num_runs_per_config=2)
    
    # Now manually run zoom search
    print("\n" + "="*50)
    print("MANUAL ZOOM SEARCH")
    print("="*50)
    
    zoom_configs = runner.run_zoom_in_search('vad')
    
    if zoom_configs:
        print(f"\nGenerated {len(zoom_configs)} zoom configurations:")
        for i, config in enumerate(zoom_configs, 1):
            print(f"  {i}. {config['description']}")
        
        # You could now manually test these configurations
        print("\nYou can now test these configurations manually or")
        print("run them through the test runner.")
    else:
        print("No zoom configurations generated.")

if __name__ == "__main__":
    print("Phase B Workflow Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # example_phase_b_workflow()     # Complete Phase B workflow
    # example_manual_zoom_search()   # Manual zoom search
    
    print("\nTo run examples, uncomment the desired function call above.")
    print("\nRecommended workflow:")
    print("1. Set TEST_MODE = 'phase_b_r1' in test_runner.py")
    print("2. Run: python test_runner.py")
    print("3. Set TEST_MODE = 'phase_b_r2' in test_runner.py")
    print("4. Run: python test_runner.py")
    print("5. Round 2 will automatically read Round 1 results and perform zoom search")
    print()
    print("Output files:")
    print("- Round 1: VAD_phase_b_r1_RAW_timestamp.json/csv")
    print("- Round 2: VAD_phase_b_r2_ZOOM_timestamp.json/csv (zoom-only)")
    print("- Round 2: VAD_phase_b_r2_COMBINED_timestamp.json/csv (all results)") 