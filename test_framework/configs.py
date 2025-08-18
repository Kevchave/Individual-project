#!/usr/bin/env python3
"""
Simplified Test Configurations for Transcription Models
"""

# Test configurations for each model type
TEST_CONFIGS = {
    'fixed': [
        {'chunk_size': 1.0, 'description': 'FIXED (1.0s chunks)'},
        {'chunk_size': 1.5, 'description': 'FIXED (1.5s chunks)'},
        {'chunk_size': 2.5, 'description': 'FIXED (2.5s chunks)'},
        {'chunk_size': 3.0, 'description': 'FIXED (3.0s chunks)'}
    ],
    
    'vad': [
        {'aggressiveness': 1, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'FIXED VAD (1/20ms/10 frames)'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'FIXED VAD (2/20ms/10 frames)'},
        {'aggressiveness': 3, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'FIXED VAD (3/20ms/10 frames)'},
        {'aggressiveness': 2, 'frame_duration_ms': 10, 'max_silence_frames': 10, 'description': 'FIXED VAD (2/10ms/10 frames)'},
        {'aggressiveness': 2, 'frame_duration_ms': 30, 'max_silence_frames': 10, 'description': 'FIXED VAD (2/30ms/10 frames)'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 5, 'description': 'FIXED VAD (2/20ms/5 frames)'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 15, 'description': 'FIXED VAD (2/20ms/15 frames)'}
    ],
    
    'adaptive': [
        {'starting_aggressiveness': 1, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'ADAPTIVE VAD (1/20ms/10 frames)'},
        {'starting_aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'ADAPTIVE VAD (2/20ms/10 frames)'},
        {'starting_aggressiveness': 3, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'ADAPTIVE VAD (3/20ms/10 frames)'}
    ]
}