#!/usr/bin/env python3
"""
Test script for ConfigManager

This demonstrates how configurations evolve through the testing phases.
"""

from config_manager import ConfigManager

def test_config_evolution():
    """Test the configuration evolution process"""
    print("=== Testing Configuration Evolution ===")
    
    config_manager = ConfigManager()
    
    # Test Phase A Round 1 initialization
    print("\n--- Phase A Round 1: Initialize from configs.py ---")
    success = config_manager.initialize_phase_a_r1('vad')
    if success:
        configs = config_manager.get_phase_configs('vad', 'phase_a_r1')
        print(f"Initialized {len(configs)} VAD configurations")
    
    # Test Phase A Round 2 evolution (would need real results data)
    print("\n--- Phase A Round 2: Top 50% selection ---")
    print("(This would require actual test results from Phase A Round 1)")
    
    # Test Phase B Round 1 evolution (would need real results data)
    print("\n--- Phase B Round 1: Best 2 fixed + 3 VAD + 3 adaptive ---")
    print("(This would require actual test results from Phase A Round 2)")
    
    # Show evolution status
    print("\n--- Configuration Evolution Status ---")
    config_manager.show_config_evolution('vad')

def test_selection_logic():
    """Test the selection logic with mock data"""
    print("\n=== Testing Selection Logic ===")
    
    config_manager = ConfigManager()
    
    # Mock results data for Phase A Round 2
    mock_results = [
        # Fixed configs
        {'config': 'FIXED (1.0s chunks)', 'wer_score': 0.12, 'processing_latency': 2.1, 'p90_processing_latency': 2.5},
        {'config': 'FIXED (2.0s chunks)', 'wer_score': 0.10, 'processing_latency': 3.2, 'p90_processing_latency': 3.8},
        {'config': 'FIXED (3.0s chunks)', 'wer_score': 0.15, 'processing_latency': 4.5, 'p90_processing_latency': 5.1},
        
        # VAD configs
        {'config': 'VAD (1/10ms/5 frames)', 'wer_score': 0.08, 'processing_latency': 1.8, 'p90_processing_latency': 2.2},
        {'config': 'VAD (2/10ms/5 frames)', 'wer_score': 0.09, 'processing_latency': 2.0, 'p90_processing_latency': 2.4},
        {'config': 'VAD (3/10ms/5 frames)', 'wer_score': 0.11, 'processing_latency': 2.3, 'p90_processing_latency': 2.7},
        {'config': 'VAD (1/15ms/5 frames)', 'wer_score': 0.10, 'processing_latency': 1.9, 'p90_processing_latency': 2.3},
        
        # Adaptive configs
        {'config': 'ADAPTIVE (1/10ms/5 frames)', 'wer_score': 0.07, 'processing_latency': 1.9, 'p90_processing_latency': 2.3},
        {'config': 'ADAPTIVE (2/10ms/5 frames)', 'wer_score': 0.08, 'processing_latency': 2.1, 'p90_processing_latency': 2.5},
        {'config': 'ADAPTIVE (3/10ms/5 frames)', 'wer_score': 0.12, 'processing_latency': 2.4, 'p90_processing_latency': 2.8},
        {'config': 'ADAPTIVE (1/15ms/5 frames)', 'wer_score': 0.09, 'processing_latency': 2.0, 'p90_processing_latency': 2.4},
    ]
    
    # Mock source configs (simulating Phase A Round 2 configs)
    mock_source_configs = [
        {'description': 'FIXED (1.0s chunks)', 'chunk_size': 1.0},
        {'description': 'FIXED (2.0s chunks)', 'chunk_size': 2.0},
        {'description': 'FIXED (3.0s chunks)', 'chunk_size': 3.0},
        {'description': 'VAD (1/10ms/5 frames)', 'aggressiveness': 1, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'VAD (2/10ms/5 frames)', 'aggressiveness': 2, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'VAD (3/10ms/5 frames)', 'aggressiveness': 3, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'VAD (1/15ms/5 frames)', 'aggressiveness': 1, 'frame_duration_ms': 15, 'max_silence_frames': 5},
        {'description': 'ADAPTIVE (1/10ms/5 frames)', 'starting_aggressiveness': 1, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'ADAPTIVE (2/10ms/5 frames)', 'starting_aggressiveness': 2, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'ADAPTIVE (3/10ms/5 frames)', 'starting_aggressiveness': 3, 'frame_duration_ms': 10, 'max_silence_frames': 5},
        {'description': 'ADAPTIVE (1/15ms/5 frames)', 'starting_aggressiveness': 1, 'frame_duration_ms': 15, 'max_silence_frames': 5},
    ]
    
    print("Mock Phase A Round 2 results:")
    for result in mock_results:
        print(f"  {result['config']}: WER={result['wer_score']:.3f}, Latency={result['processing_latency']:.1f}s")
    
    print("\nApplying Phase B Round 1 selection (best 2 fixed + 3 VAD + 3 adaptive):")
    selected_configs = config_manager._select_best_2_fixed_3_vad_adaptive(mock_results, mock_source_configs)
    
    print("\nSelected configurations for Phase B Round 1:")
    for i, config in enumerate(selected_configs, 1):
        print(f"  {i}. {config['description']}")

def test_full_pipeline():
    """Test the complete pipeline with fake results"""
    print("\n=== Testing Complete Pipeline ===")
    
    config_manager = ConfigManager()
    
    # Phase A Round 1: Initialize all configs
    print("\n--- Phase A Round 1: Initialize all configs ---")
    config_manager.initialize_phase_a_r1('combined')
    
    # Phase A Round 1: Fake results (8 fixed + 16 vad + 16 adaptive = 40 total)
    print("\n--- Phase A Round 1: Fake Results ---")
    
    # Fixed configs (8 total) - fake results with correct description format
    fixed_results = [
        {'config': 'FIXED-Sobol-1 (0.8s)', 'wer_score': 0.18, 'processing_latency': 1.5, 'p90_processing_latency': 1.8},
        {'config': 'FIXED-Sobol-2 (2.4s)', 'wer_score': 0.15, 'processing_latency': 2.1, 'p90_processing_latency': 2.5},
        {'config': 'FIXED-Sobol-3 (3.2s)', 'wer_score': 0.12, 'processing_latency': 2.8, 'p90_processing_latency': 3.2},
        {'config': 'FIXED-Sobol-4 (1.6s)', 'wer_score': 0.10, 'processing_latency': 3.5, 'p90_processing_latency': 4.0},
        {'config': 'FIXED-Sobol-5 (2.0s)', 'wer_score': 0.09, 'processing_latency': 4.2, 'p90_processing_latency': 4.8},
        {'config': 'FIXED-Sobol-6 (2.8s)', 'wer_score': 0.08, 'processing_latency': 4.8, 'p90_processing_latency': 5.5},
        {'config': 'FIXED-Sobol-7 (1.2s)', 'wer_score': 0.11, 'processing_latency': 5.5, 'p90_processing_latency': 6.2},
        {'config': 'FIXED-Sobol-8 (3.6s)', 'wer_score': 0.20, 'processing_latency': 6.0, 'p90_processing_latency': 7.0},
    ]
    
    # VAD configs (16 total) - fake results with correct description format
    vad_results = [
        {'config': 'Sobol-1: agg=0, frames=2', 'wer_score': 0.12, 'processing_latency': 1.2, 'p90_processing_latency': 1.5},
        {'config': 'Sobol-2: agg=2, frames=13', 'wer_score': 0.09, 'processing_latency': 1.4, 'p90_processing_latency': 1.7},
        {'config': 'Sobol-3: agg=1, frames=19', 'wer_score': 0.07, 'processing_latency': 1.6, 'p90_processing_latency': 1.9},
        {'config': 'Sobol-4: agg=3, frames=22', 'wer_score': 0.06, 'processing_latency': 1.8, 'p90_processing_latency': 2.1},
        {'config': 'Sobol-5: agg=0, frames=9', 'wer_score': 0.13, 'processing_latency': 1.3, 'p90_processing_latency': 1.6},
        {'config': 'Sobol-6: agg=1, frames=10', 'wer_score': 0.10, 'processing_latency': 1.5, 'p90_processing_latency': 1.8},
        {'config': 'Sobol-7: agg=2, frames=12', 'wer_score': 0.08, 'processing_latency': 1.7, 'p90_processing_latency': 2.0},
        {'config': 'Sobol-8: agg=3, frames=7', 'wer_score': 0.07, 'processing_latency': 1.9, 'p90_processing_latency': 2.2},
        {'config': 'Sobol-9: agg=0, frames=16', 'wer_score': 0.14, 'processing_latency': 1.4, 'p90_processing_latency': 1.7},
        {'config': 'Sobol-10: agg=1, frames=14', 'wer_score': 0.11, 'processing_latency': 1.6, 'p90_processing_latency': 1.9},
        {'config': 'Sobol-11: agg=2, frames=4', 'wer_score': 0.09, 'processing_latency': 1.8, 'p90_processing_latency': 2.1},
        {'config': 'Sobol-12: agg=3, frames=3', 'wer_score': 0.08, 'processing_latency': 2.0, 'p90_processing_latency': 2.3},
        {'config': 'Sobol-13: agg=0, frames=23', 'wer_score': 0.15, 'processing_latency': 1.5, 'p90_processing_latency': 1.8},
        {'config': 'Sobol-14: agg=1, frames=6', 'wer_score': 0.12, 'processing_latency': 1.7, 'p90_processing_latency': 2.0},
        {'config': 'Sobol-15: agg=2, frames=20', 'wer_score': 0.10, 'processing_latency': 1.9, 'p90_processing_latency': 2.2},
        {'config': 'Sobol-16: agg=3, frames=17', 'wer_score': 0.09, 'processing_latency': 2.1, 'p90_processing_latency': 2.4},
    ]
    
    # Adaptive configs (16 total) - fake results with correct description format
    adaptive_results = [
        {'config': 'Adaptive-Sobol-1: agg=0, frames=2', 'wer_score': 0.11, 'processing_latency': 1.1, 'p90_processing_latency': 1.4},
        {'config': 'Adaptive-Sobol-2: agg=2, frames=13', 'wer_score': 0.08, 'processing_latency': 1.3, 'p90_processing_latency': 1.6},
        {'config': 'Adaptive-Sobol-3: agg=1, frames=19', 'wer_score': 0.06, 'processing_latency': 1.5, 'p90_processing_latency': 1.8},
        {'config': 'Adaptive-Sobol-4: agg=3, frames=22', 'wer_score': 0.05, 'processing_latency': 1.7, 'p90_processing_latency': 2.0},
        {'config': 'Adaptive-Sobol-5: agg=0, frames=9', 'wer_score': 0.12, 'processing_latency': 1.2, 'p90_processing_latency': 1.5},
        {'config': 'Adaptive-Sobol-6: agg=1, frames=10', 'wer_score': 0.09, 'processing_latency': 1.4, 'p90_processing_latency': 1.7},
        {'config': 'Adaptive-Sobol-7: agg=2, frames=12', 'wer_score': 0.07, 'processing_latency': 1.6, 'p90_processing_latency': 1.9},
        {'config': 'Adaptive-Sobol-8: agg=3, frames=7', 'wer_score': 0.06, 'processing_latency': 1.8, 'p90_processing_latency': 2.1},
        {'config': 'Adaptive-Sobol-9: agg=0, frames=16', 'wer_score': 0.13, 'processing_latency': 1.3, 'p90_processing_latency': 1.6},
        {'config': 'Adaptive-Sobol-10: agg=1, frames=14', 'wer_score': 0.10, 'processing_latency': 1.5, 'p90_processing_latency': 1.8},
        {'config': 'Adaptive-Sobol-11: agg=2, frames=4', 'wer_score': 0.08, 'processing_latency': 1.7, 'p90_processing_latency': 2.0},
        {'config': 'Adaptive-Sobol-12: agg=3, frames=3', 'wer_score': 0.07, 'processing_latency': 1.9, 'p90_processing_latency': 2.2},
        {'config': 'Adaptive-Sobol-13: agg=0, frames=23', 'wer_score': 0.14, 'processing_latency': 1.4, 'p90_processing_latency': 1.7},
        {'config': 'Adaptive-Sobol-14: agg=1, frames=6', 'wer_score': 0.11, 'processing_latency': 1.6, 'p90_processing_latency': 1.9},
        {'config': 'Adaptive-Sobol-15: agg=2, frames=20', 'wer_score': 0.09, 'processing_latency': 1.8, 'p90_processing_latency': 2.1},
        {'config': 'Adaptive-Sobol-16: agg=3, frames=17', 'wer_score': 0.08, 'processing_latency': 2.0, 'p90_processing_latency': 2.3},
    ]
    
    print(f"Phase A Round 1: {len(fixed_results)} fixed + {len(vad_results)} VAD + {len(adaptive_results)} adaptive = {len(fixed_results) + len(vad_results) + len(adaptive_results)} total results")
    
    # Phase A Round 2: Select top 50% from each model type
    print("\n--- Phase A Round 2: Select top 50% from each model type ---")
    
    # Combine all results for Phase A Round 2 selection
    all_a1_results = fixed_results + vad_results + adaptive_results
    
    # Get source configs from registry
    fixed_a1_configs = config_manager.get_phase_configs('fixed', 'phase_a_r1')
    vad_a1_configs = config_manager.get_phase_configs('vad', 'phase_a_r1')
    adaptive_a1_configs = config_manager.get_phase_configs('adaptive', 'phase_a_r1')
    all_a1_configs = fixed_a1_configs + vad_a1_configs + adaptive_a1_configs
    
    # Evolve to Phase A Round 2 using combined approach
    config_manager.evolve_configs('phase_a_r1', 'phase_a_r2', 'combined', all_a1_results)
    
    # Get evolved configs
    phase_a_r2_configs = config_manager.get_phase_configs('combined', 'phase_a_r2')
    
    print(f"Phase A Round 2: {len(phase_a_r2_configs)} total configs")
    
    # Phase A Round 2: Fake results (should be 20 total)
    print("\n--- Phase A Round 2: Fake Results ---")
    
    # Generate fake results for Phase A Round 2 (slightly better than Round 1)
    phase_a_r2_results = []
    for i, config in enumerate(phase_a_r2_configs):
        desc = config['description']
        # Better WER for top 50% - ensure all get selected
        wer = 0.02 + (i % 3) * 0.01  # 0.02-0.04 (all good enough)
        latency = 1.5 + (i % 2) * 0.3  # 1.5-2.1
        
        phase_a_r2_results.append({
            'config': desc,
            'wer_score': wer,
            'processing_latency': latency,
            'p90_processing_latency': latency * 1.2
        })
    
    print(f"Phase A Round 2: {len(phase_a_r2_results)} results")
    
    # Phase B Round 1: Select best 2 fixed + 3 VAD + 3 adaptive
    print("\n--- Phase B Round 1: Select best 2 fixed + 3 VAD + 3 adaptive ---")
    
    # Use the combined approach for Phase B Round 1
    config_manager.evolve_configs('phase_a_r2', 'phase_b_r1', 'combined', phase_a_r2_results)
    
    phase_b_r1_configs = config_manager.get_phase_configs('combined', 'phase_b_r1')
    print(f"Phase B Round 1: {len(phase_b_r1_configs)} configurations selected")
    for i, config in enumerate(phase_b_r1_configs, 1):
        print(f"  {i}. {config['description']}")
    
    # Phase B Round 1: Fake results (8 total)
    print("\n--- Phase B Round 1: Fake Results ---")
    phase_b_r1_results = []
    for i, config in enumerate(phase_b_r1_configs):
        desc = config['description']
        # Even better WER for top performers
        wer = 0.02 + (i % 2) * 0.01  # 0.02-0.03
        latency = 1.5 + (i % 2) * 0.2  # 1.5-1.7
        
        phase_b_r1_results.append({
            'config': desc,
            'wer_score': wer,
            'processing_latency': latency,
            'p90_processing_latency': latency * 1.1
        })
    
    print(f"Phase B Round 1: {len(phase_b_r1_results)} results")
    
    # Phase B Round 2: Zoom search around best
    print("\n--- Phase B Round 2: Zoom search around best ---")
    
    # Find best config from Phase B Round 1
    best_config = min(phase_b_r1_results, key=lambda x: x['wer_score'])
    print(f"Best config from B1: {best_config['config']} (WER: {best_config['wer_score']:.3f})")
    
    # TODO: This will use the zoom_search.py module
    # For now, create placeholder zoom configs
    print("TODO: Zoom search will be implemented using zoom_search.py module")
    zoom_configs = []
    
    # Placeholder: Generate simple neighbor configs for demonstration
    best_desc = best_config['config']
    if 'FIXED' in best_desc:
        # Extract chunk size and create neighbors
        import re
        match = re.search(r'(\d+\.?\d*)s', best_desc)
        if match:
            chunk_size = float(match.group(1))
            zoom_configs = [
                {'description': f'FIXED ({(chunk_size-0.5):.1f}s chunks)', 'chunk_size': chunk_size-0.5},
                {'description': f'FIXED ({(chunk_size+0.5):.1f}s chunks)', 'chunk_size': chunk_size+0.5},
            ]
    elif 'VAD' in best_desc:
        # Extract parameters and create neighbors
        match = re.search(r'agg=(\d+), frames=(\d+)', best_desc)
        if match:
            agg, frames = int(match.group(1)), int(match.group(2))
            zoom_configs = [
                {'description': f'VAD (agg={agg}, frames={max(1, frames-2)})', 'aggressiveness': agg, 'frame_duration_ms': 20, 'max_silence_frames': max(1, frames-2)},
                {'description': f'VAD (agg={agg}, frames={frames+2})', 'aggressiveness': agg, 'frame_duration_ms': 20, 'max_silence_frames': frames+2},
            ]
    else:  # ADAPTIVE
        match = re.search(r'agg=(\d+), frames=(\d+)', best_desc)
        if match:
            start_agg, frames = int(match.group(1)), int(match.group(2))
            zoom_configs = [
                {'description': f'ADAPTIVE (agg={start_agg}, frames={max(1, frames-2)})', 'starting_aggressiveness': start_agg, 'frame_duration_ms': 20, 'max_silence_frames': max(1, frames-2)},
                {'description': f'ADAPTIVE (agg={start_agg}, frames={frames+2})', 'starting_aggressiveness': start_agg, 'frame_duration_ms': 20, 'max_silence_frames': frames+2},
            ]
    
    print(f"Phase B Round 2: {len(zoom_configs)} zoom configurations (placeholder)")
    for i, config in enumerate(zoom_configs, 1):
        print(f"  {i}. {config['description']}")
    
    # Phase B Round 2: Fake results
    print("\n--- Phase B Round 2: Fake Results ---")
    phase_b_r2_results = []
    for i, config in enumerate(zoom_configs):
        desc = config['description']
        # Best WER for zoom search results
        wer = 0.01 + (i % 2) * 0.005  # 0.01-0.015
        latency = 1.2 + (i % 2) * 0.1  # 1.2-1.3
        
        phase_b_r2_results.append({
            'config': desc,
            'wer_score': wer,
            'processing_latency': latency,
            'p90_processing_latency': latency * 1.05
        })
    
    print(f"Phase B Round 2: {len(phase_b_r2_results)} results")
    
    # Phase C: Select best config
    print("\n--- Phase C: Select best config ---")
    
    # Find best config from Phase B Round 2
    best_b2_config = min(phase_b_r2_results, key=lambda x: x['wer_score'])
    print(f"Best config from B2: {best_b2_config['config']} (WER: {best_b2_config['wer_score']:.3f})")
    
    # Show final evolution status
    print("\n--- Final Configuration Evolution Status ---")
    config_manager.show_config_evolution('fixed')
    config_manager.show_config_evolution('vad')
    config_manager.show_config_evolution('adaptive')

def main():
    """Run all tests"""
    print("ConfigManager Test Suite")
    print("=" * 50)
    
    test_config_evolution()
    test_selection_logic()
    test_full_pipeline()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main() 