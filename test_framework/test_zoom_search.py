#!/usr/bin/env python3
"""
Test script for ZoomSearch module

This script tests the zoom-in search functionality to verify it works correctly
for different model types and parameter scenarios.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from zoom_search import ZoomSearch

def test_new_zoom_logic():
    """Test the new zoom search logic with clear examples"""
    print("\n=== Testing Simplified Zoom Search Logic ===")
    
    zoom_search = ZoomSearch()
    
    # Test 1: Fixed model - simple midpoint
    print("\n--- Test 1: Fixed Model ---")
    fixed_configs = [
        ("FIXED (1.2s chunks)", {'avg_wer': 0.10}),  # Best
        ("FIXED (2.4s chunks)", {'avg_wer': 0.15})   # Neighbor
    ]
    
    zoom_configs = zoom_search.run_zoom_in_search(fixed_configs, 'fixed')
    print("Generated configurations:")
    for i, config in enumerate(zoom_configs, 1):
        print(f"  {i}. {config['description']}")
    
    # Test 2: VAD model - continuous parameter (frame_duration_ms)
    print("\n--- Test 2: VAD Model (Continuous Parameter) ---")
    vad_configs = [
        ("VAD (2/10ms/5 frames)", {'avg_wer': 0.08}),   # Best
        ("VAD (2/15ms/5 frames)", {'avg_wer': 0.12}),   # Different frame_duration
        ("VAD (1/10ms/5 frames)", {'avg_wer': 0.10})    # Different aggressiveness
    ]
    
    zoom_configs = zoom_search.run_zoom_in_search(vad_configs, 'vad')
    print("Generated configurations:")
    for i, config in enumerate(zoom_configs, 1):
        print(f"  {i}. {config['description']}")
    
    # Test 3: VAD model - discrete parameter with enough difference
    print("\n--- Test 3: VAD Model (Discrete Parameter - Good Difference) ---")
    vad_configs_2 = [
        ("VAD (0/10ms/5 frames)", {'avg_wer': 0.08}),   # Best
        ("VAD (2/10ms/5 frames)", {'avg_wer': 0.12}),   # Different aggressiveness (diff=2)
        ("VAD (1/10ms/5 frames)", {'avg_wer': 0.10})    # Different aggressiveness
    ]
    
    zoom_configs = zoom_search.run_zoom_in_search(vad_configs_2, 'vad')
    print("Generated configurations:")
    for i, config in enumerate(zoom_configs, 1):
        print(f"  {i}. {config['description']}")
    
    # Test 4: Show iterative process
    print("\n--- Test 4: Iterative Process Example ---")
    print("Round 1: Test midpoint between best and neighbor")
    print("Round 2: If midpoint is better, repeat with new best")
    print("Round 3: If midpoint is worse, stop (found optimal)")
    
    # Simulate iterative process
    print("\nExample iterative process:")
    print("  Initial: VAD (1/10ms/5 frames) = 0.08 WER (best)")
    print("  Neighbor: VAD (1/15ms/5 frames) = 0.12 WER")
    print("  Test: VAD (1/12ms/5 frames) = 0.07 WER (better!)")
    print("  → Continue with VAD (1/12ms/5 frames) as new best")
    print("  Next: Test midpoint between 10ms and 12ms = 11ms")
    print("  If 11ms is worse than 12ms, stop - 12ms is optimal!")

def main():
    """Run all tests"""
    print("Testing ZoomSearch Module")
    print("=" * 50)
    
    test_new_zoom_logic()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main() 