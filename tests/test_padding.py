import pytest
import numpy as np
from transcriber_app.transcriber import Transcriber

@pytest.fixture
def transcriber():
    return Transcriber("small", "cpu", pre_padding_seconds=0.2, post_padding_seconds=0.3)

def test_padding_basic(transcriber):
    """Test basic padding functionality"""
    # Create a test audio chunk (1 second of audio)
    sample_rate = 16000
    test_audio = np.random.rand(sample_rate).astype(np.float32)
    
    # Apply padding
    padded_audio = transcriber.apply_silence_padding(test_audio, sample_rate)
    
    # Check total length
    expected_length = sample_rate + (0.2 * sample_rate) + (0.3 * sample_rate)
    assert len(padded_audio) == int(expected_length)
    
    # Check that original audio is in the middle
    pre_pad_length = int(0.2 * sample_rate)
    assert np.array_equal(padded_audio[pre_pad_length:pre_pad_length + sample_rate], test_audio)

def test_padding_silence_values(transcriber):
    """Test that padding is actually silence (zeros)"""
    sample_rate = 16000
    test_audio = np.random.rand(sample_rate).astype(np.float32)
    
    padded_audio = transcriber.apply_silence_padding(test_audio, sample_rate)
    
    pre_pad_length = int(0.2 * sample_rate)
    post_pad_length = int(0.3 * sample_rate)
    
    # Check pre-padding is silence
    pre_pad = padded_audio[:pre_pad_length]
    assert np.all(pre_pad == 0.0)
    
    # Check post-padding is silence
    post_pad = padded_audio[-post_pad_length:]
    assert np.all(post_pad == 0.0)

def test_padding_different_sizes(transcriber):
    """Test padding with different audio chunk sizes"""
    sample_rate = 16000
    
    # Test with short audio
    short_audio = np.random.rand(1000).astype(np.float32)
    padded_short = transcriber.apply_silence_padding(short_audio, sample_rate)
    expected_short_length = 1000 + int(0.2 * sample_rate) + int(0.3 * sample_rate)
    assert len(padded_short) == expected_short_length
    
    # Test with long audio
    long_audio = np.random.rand(5000).astype(np.float32)
    padded_long = transcriber.apply_silence_padding(long_audio, sample_rate)
    expected_long_length = 5000 + int(0.2 * sample_rate) + int(0.3 * sample_rate)
    assert len(padded_long) == expected_long_length

def test_padding_different_dtypes(transcriber):
    """Test padding preserves data type"""
    sample_rate = 16000
    
    # Test with float32
    audio_float32 = np.random.rand(1000).astype(np.float32)
    padded_float32 = transcriber.apply_silence_padding(audio_float32, sample_rate)
    assert padded_float32.dtype == np.float32
    
    # Test with float64
    audio_float64 = np.random.rand(1000).astype(np.float64)
    padded_float64 = transcriber.apply_silence_padding(audio_float64, sample_rate)
    assert padded_float64.dtype == np.float64

def test_padding_zero_padding(transcriber):
    """Test with zero padding values"""
    zero_padding_transcriber = Transcriber("small", "cpu", pre_padding_seconds=0.0, post_padding_seconds=0.0)
    
    sample_rate = 16000
    test_audio = np.random.rand(sample_rate).astype(np.float32)
    
    padded_audio = zero_padding_transcriber.apply_silence_padding(test_audio, sample_rate)
    
    # Should be identical to original
    assert len(padded_audio) == len(test_audio)
    assert np.array_equal(padded_audio, test_audio)

def test_padding_custom_sample_rate(transcriber):
    """Test padding with different sample rates"""
    sample_rate = 8000  # Different sample rate
    test_audio = np.random.rand(sample_rate).astype(np.float32)
    
    padded_audio = transcriber.apply_silence_padding(test_audio, sample_rate)
    
    # Check padding lengths are correct for this sample rate
    pre_pad_length = int(0.2 * sample_rate)
    post_pad_length = int(0.3 * sample_rate)
    
    assert len(padded_audio) == sample_rate + pre_pad_length + post_pad_length
    assert np.all(padded_audio[:pre_pad_length] == 0.0)
    assert np.all(padded_audio[-post_pad_length:] == 0.0) 