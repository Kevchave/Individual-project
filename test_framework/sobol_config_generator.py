import numpy as np
from scipy.stats import qmc

def generate_sobol_configs(n_samples=16):
    """
    Generate VAD configurations using Sobol sampling.
    
    Parameters:
    - Aggressiveness: 0, 1, 2, 3 (discrete)
    - Max silence frames: 2-25 (continuous, rounded to int)
    - Frame duration: Fixed at 20ms
    
    Returns:
    - List of config dictionaries
    """
    
    # Create 2D Sobol sampler (deterministic)
    sampler = qmc.Sobol(d=2, scramble=False)
    
    # Generate samples in [0,1] range
    samples = sampler.random(n_samples)
    
    configs = []
    
    for i, sample in enumerate(samples):
        # Map first dimension to aggressiveness (0,1,2,3)
        aggressiveness = int(sample[0] * 4)  # 0.0-0.999 -> 0,1,2,3
        
        # Map second dimension to max_silence_frames (2-25)
        max_silence_frames = int(2 + sample[1] * 23)  # 2 + (0-22.999) -> 2-24
        
        config = {
            'aggressiveness': aggressiveness,
            'frame_duration_ms': 20,  # Fixed
            'max_silence_frames': max_silence_frames,
            'description': f'Sobol-{i+1}: agg={aggressiveness}, frames={max_silence_frames}'
        }
        
        configs.append(config)
    
    return configs

def generate_fixed_sobol_configs(n_samples=8):
    """
    Generate fixed chunking configurations using Sobol sampling.
    
    Parameters:
    - Chunk size: 0.8-4.0 seconds (based on natural speech research)
    
    Returns:
    - List of config dictionaries
    """
    
    # Create 1D Sobol sampler for chunk size (deterministic)
    sampler = qmc.Sobol(d=1, scramble=False)
    
    # Generate samples in [0,1] range
    samples = sampler.random(n_samples)
    
    configs = []
    
    for i, sample in enumerate(samples):
        # Map to chunk_size range (0.8-4.0s)
        chunk_size = 0.8 + sample[0] * 3.2  # 0.8 + (0 to 3.2) = 0.8 to 4.0
        chunk_size = round(chunk_size, 1)  # Round to 1 decimal place
        
        config = {
            'chunk_size': chunk_size,
            'description': f'FIXED-Sobol-{i+1} ({chunk_size}s)'
        }
        
        configs.append(config)
    
    return configs

def update_test_configs():
    """
    Update the TEST_CONFIGS dictionary with Sobol-generated configurations.
    Call this function to replace the manual configs in configs.py
    """
    
    # Generate Sobol configs for all model types
    fixed_configs = generate_fixed_sobol_configs(8)  # 8 configs (power of 2)
    vad_configs = generate_sobol_configs(16)
    adaptive_configs = generate_sobol_configs(16)  # Same params, different model usage
    
    # Add starting_aggressiveness for adaptive configs (same as aggressiveness)
    for config in adaptive_configs:
        config['starting_aggressiveness'] = config['aggressiveness']
        config['description'] = config['description'].replace('Sobol-', 'Adaptive-Sobol-')
    
    # Return updated configs
    updated_configs = {
        'fixed': fixed_configs,
        'vad': vad_configs,
        'adaptive': adaptive_configs
    }
    
    return updated_configs

def print_all_configs():
    """
    Print all generated configurations in detail, sorted for readability
    """
    configs = update_test_configs()
    
    print("DETAILED CONFIGURATION LIST")
    print("=" * 60)
    
    for model_type, config_list in configs.items():
        print(f"\n{model_type.upper()} CONFIGURATIONS ({len(config_list)} total):")
        print("-" * 40)
        
        # Sort configurations for better readability
        if model_type == 'fixed':
            # Sort by chunk_size (smallest to largest)
            sorted_configs = sorted(config_list, key=lambda x: x['chunk_size'])
        else:
            # Sort by aggressiveness first, then by max_silence_frames
            sorted_configs = sorted(config_list, key=lambda x: (x['aggressiveness'], x['max_silence_frames']))
        
        for i, config in enumerate(sorted_configs, 1):
            if model_type == 'fixed':
                print(f"{i:2d}. Chunk Size: {config['chunk_size']:4.1f}s")
            else:
                agg = config['aggressiveness']
                frames = config['max_silence_frames']
                silence_ms = frames * 20  # Convert to milliseconds
                
                if model_type == 'adaptive':
                    print(f"{i:2d}. Agg: {agg} | Frames: {frames:2d} | Silence: {silence_ms:3d}ms | Starting Agg: {config['starting_aggressiveness']}")
                else:  # VAD
                    print(f"{i:2d}. Agg: {agg} | Frames: {frames:2d} | Silence: {silence_ms:3d}ms")
    
    print(f"\nTOTAL CONFIGURATIONS: {sum(len(configs) for configs in configs.values())}")
    print("=" * 60)