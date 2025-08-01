#!/usr/bin/env python3
"""
Test Configurations for Transcription Models
"""

# Test configurations for each model type
TEST_CONFIGS = {
    'fixed': [
        {'chunk_size': 1.0, 'description': 'Small chunks (1.0s)'},
        {'chunk_size': 1.5, 'description': 'Medium chunks (1.5s)'},
        {'chunk_size': 2.5, 'description': 'Large chunks (2.5s)'},
        {'chunk_size': 3.0, 'description': 'Very large chunks (3.0s)'}
    ],
    
    'vad': [
        {'aggressiveness': 1, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'Low aggressiveness'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'Medium aggressiveness'},
        {'aggressiveness': 3, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'High aggressiveness'},
        {'aggressiveness': 2, 'frame_duration_ms': 10, 'max_silence_frames': 10, 'description': 'Fast frames (10ms)'},
        {'aggressiveness': 2, 'frame_duration_ms': 30, 'max_silence_frames': 10, 'description': 'Slow frames (30ms)'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 5, 'description': 'Short silence tolerance'},
        {'aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 15, 'description': 'Long silence tolerance'}
    ],
    
    'adaptive': [
        {'starting_aggressiveness': 1, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'Conservative start'},
        {'starting_aggressiveness': 2, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'Balanced start'},
        {'starting_aggressiveness': 3, 'frame_duration_ms': 20, 'max_silence_frames': 10, 'description': 'Aggressive start'}
    ]
}

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