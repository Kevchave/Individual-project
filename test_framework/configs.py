#!/usr/bin/env python3
"""
Test Configurations for Transcription Models
"""

from sobol_config_generator import update_test_configs, print_all_configs

# Generate TEST_CONFIGS using Sobol sampling
TEST_CONFIGS = update_test_configs()

# Audio file categories for different speaking styles
AUDIO_CATEGORIES = {
    'seminar': {
        'description': 'Fast-paced, conversational (150+ WPM)',
        'expected_wpm': 150,
        'file_pattern': '*seminar*'
    },
    'lecture': {
        'description': 'Slower, structured, pauses (100-120 WPM)',
        'expected_wpm': 110,
        'file_pattern': '*lecture*'
    },
    'talk': {
        'description': 'Performative, enthusiastic (130-150 WPM)',
        'expected_wpm': 140,
        'file_pattern': '*talk*'
    }
}

def verify_sobol_configs():
    """Quick function to verify the generated configurations look good"""
    print("VERIFICATION:")
    print("=" * 40)
    
    for model_type, config_list in TEST_CONFIGS.items():
        print(f"\n{model_type.upper()} ({len(config_list)} configs):")
        
        if model_type == 'fixed':
            chunks = [float(c['chunk_size']) for c in config_list]  # Convert to regular float
            print(f"  Chunk sizes: {sorted(chunks)}")
        else:
            agg_vals = [c['aggressiveness'] for c in config_list]
            frame_vals = [c['max_silence_frames'] for c in config_list]
            print(f"  Aggressiveness: {sorted(set(agg_vals))}")
            print(f"  Max silence frames: {min(frame_vals)}-{max(frame_vals)}")
    
    print(f"\nTotal configurations:")
    print(f"  Fixed: {len(TEST_CONFIGS['fixed'])}")
    print(f"  VAD: {len(TEST_CONFIGS['vad'])}")
    print(f"  Adaptive: {len(TEST_CONFIGS['adaptive'])}")
    print(f"  TOTAL: {sum(len(configs) for configs in TEST_CONFIGS.values())}")

if __name__ == "__main__":
    verify_sobol_configs()
    
    print("\n" + "=" * 60)
    print("DETAILED CONFIGURATIONS:")
    print_all_configs()