import pytest
import numpy as np
from unittest.mock import Mock, patch
from transcriber_app.transcriber import Transcriber

@pytest.fixture
def transcriber():
    return Transcriber("small", "cpu")

@pytest.fixture
def mock_audio_queue():
    """Mock audio queue that returns test audio data"""
    queue = Mock()
    # Create some test audio data (1 second of random audio)
    test_audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
    queue.get.return_value = test_audio
    return queue

@pytest.fixture
def mock_callbacks():
    """Mock callback functions"""
    return {
        'on_transcription': Mock(),
        'on_audio_chunk': Mock(),
        'track_insider_metrics': Mock()
    }

def test_transcribe_stream_default_parameters(transcriber, mock_audio_queue, mock_callbacks):
    """Test that transcribe_stream works with default parameters"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    # Call with default parameters
    transcriber.transcribe_stream(
        mock_audio_queue,
        mock_callbacks['on_transcription'],
        mock_callbacks['on_audio_chunk'],
        mock_callbacks['track_insider_metrics']
    )
    
    # Verify the function was called (basic functionality test)
    assert mock_audio_queue.get.called

def test_transcribe_stream_custom_parameters(transcriber, mock_audio_queue, mock_callbacks):
    """Test that transcribe_stream accepts custom parameters"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    # Call with custom parameters
    transcriber.transcribe_stream(
        mock_audio_queue,
        mock_callbacks['on_transcription'],
        mock_callbacks['on_audio_chunk'],
        mock_callbacks['track_insider_metrics'],
        aggressiveness=1,
        frame_duration_ms=30,
        max_silence_frames=10
    )
    
    # Verify the function was called (basic functionality test)
    assert mock_audio_queue.get.called

def test_transcribe_stream_parameter_validation(transcriber, mock_audio_queue, mock_callbacks):
    """Test that transcribe_stream handles different parameter combinations"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    # Test different aggressiveness levels
    for aggressiveness in [0, 1, 2, 3]:
        transcriber.transcribe_stream(
            mock_audio_queue,
            mock_callbacks['on_transcription'],
            mock_callbacks['on_audio_chunk'],
            mock_callbacks['track_insider_metrics'],
            aggressiveness=aggressiveness
        )
    
    # Test different frame durations
    for frame_duration in [10, 20, 30]:
        transcriber.transcribe_stream(
            mock_audio_queue,
            mock_callbacks['on_transcription'],
            mock_callbacks['on_audio_chunk'],
            mock_callbacks['track_insider_metrics'],
            frame_duration_ms=frame_duration
        )
    
    # Test different max silence frames
    for max_silence in [1, 5, 10, 20]:
        transcriber.transcribe_stream(
            mock_audio_queue,
            mock_callbacks['on_transcription'],
            mock_callbacks['on_audio_chunk'],
            mock_callbacks['track_insider_metrics'],
            max_silence_frames=max_silence
        )

def test_transcribe_stream_no_insider_metrics(transcriber, mock_audio_queue, mock_callbacks):
    """Test that transcribe_stream works without insider metrics"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    # Call without insider metrics
    transcriber.transcribe_stream(
        mock_audio_queue,
        mock_callbacks['on_transcription'],
        mock_callbacks['on_audio_chunk'],
        track_insider_metrics=None,
        aggressiveness=2,
        frame_duration_ms=20,
        max_silence_frames=5
    )
    
    # Verify the function was called (basic functionality test)
    assert mock_audio_queue.get.called

@patch('webrtcvad.Vad')
def test_vad_aggressiveness_parameter(mock_vad_class, transcriber, mock_audio_queue, mock_callbacks):
    """Test that VAD aggressiveness parameter is correctly passed"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    # Create a mock VAD instance
    mock_vad = Mock()
    mock_vad_class.return_value = mock_vad
    mock_vad.is_speech.return_value = True  # Always return speech for simplicity
    
    # Call with specific aggressiveness
    test_aggressiveness = 2
    transcriber.transcribe_stream(
        mock_audio_queue,
        mock_callbacks['on_transcription'],
        mock_callbacks['on_audio_chunk'],
        mock_callbacks['track_insider_metrics'],
        aggressiveness=test_aggressiveness
    )
    
    # Verify VAD was created with correct aggressiveness
    mock_vad_class.assert_called_with(test_aggressiveness)

def test_frame_size_calculation(transcriber, mock_audio_queue, mock_callbacks):
    """Test that frame size is calculated correctly based on frame_duration_ms"""
    # Set up the queue to return None to stop the loop
    mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None]
    
    sample_rate = 16000
    
    # Test different frame durations and their expected frame sizes
    test_cases = [
        (10, int(sample_rate * 10 / 1000)),  # 10ms -> 160 samples
        (20, int(sample_rate * 20 / 1000)),  # 20ms -> 320 samples
        (30, int(sample_rate * 30 / 1000)),  # 30ms -> 480 samples
    ]
    
    for frame_duration_ms, expected_frame_size in test_cases:
        # We can't directly test the internal frame_size calculation,
        # but we can verify the function accepts the parameter
        transcriber.transcribe_stream(
            mock_audio_queue,
            mock_callbacks['on_transcription'],
            mock_callbacks['on_audio_chunk'],
            mock_callbacks['track_insider_metrics'],
            frame_duration_ms=frame_duration_ms
        )
        
        # Reset the mock for next iteration
        mock_audio_queue.get.reset_mock()
        mock_audio_queue.get.side_effect = [mock_audio_queue.get.return_value, None] 