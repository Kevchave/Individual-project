import pytest 
import numpy as np 
from transcriber_app.audio_stream import AudioStream

# Test initialization 
def test_init_sets_attributes():
    stream = AudioStream(sample_rate=16000, device_id=1)
    assert stream.sample_rate == 16000
    assert stream.device_id == 1
    assert stream.stream is None 
    assert hasattr(stream, 'audio_queue')

# Test callback puts PCM data in queue 
def test_callback_puts_pcm_in_queue():
    stream = AudioStream(sample_rate=16000, device_id=1)

    # Simulate float32 audio data, 2 frames 1 channel
    indata = np.array([[0.5], [-0.5]], dtype=np.float32)
    frames = 2
    time_info = None 
    status = None
    stream.callback(indata, frames, time_info, status)

    # Should have one item in queue 
    assert not stream.audio_queue.empty()
    pcm = stream.audio_queue.get()

    # Data in the queue matches expected PCM (after modulation)
    assert np.array_equal(pcm, np.array([16383, -16383], dtype=np.int16))

# Test start creates and starts InputStream
# - 'mocker' argument automatically provides a mock when running the test
def test_start_creates_and_starts_stream(mocker): 
    stream = AudioStream(sample_rate=16000, device_id=1)

    # 'mocker.patch()' temporarily replaces the class itself with a mock 
    # - so that if you test the creation of an object, it is also a mock 
    mock_input_stream = mocker.patch('sounddevice.InputStream')

    # '.return_value' uses the mock class to return a mock object of the class 
    mock_stream_instance = mock_input_stream.return_value
    stream.start()

    # 'assert_called_..' checks the mock was called exactly once with the arugments provided
    mock_input_stream.assert_called_once_with(
        callback=stream.callback, 
        dtype="float32", 
        samplerate=16000,
        channels=1, 
        device=1, 
        blocksize=480
    )
    mock_stream_instance.start.assert_called_once()
    assert stream.stream == mock_stream_instance

# Test stop closes and clears stream 
def test_stop_closes_stream(mocker):
    stream = AudioStream(sample_rate=16000, device_id=1)

    # 'mocker.mock()' creates a generic mock object 
    mock_stream = mocker.Mock()
    stream.stream = mock_stream
    stream.stop()
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()
    assert stream.stream is None

# Test pause stops active stream 
def test_pause_stops_active_stream(mocker):
    stream = AudioStream(sample_rate=16000, device_id=1)
    mock_stream = mocker.Mock()
    mock_stream.active = True 
    stream.stream = mock_stream
    stream.pause()
    mock_stream.stop.assert_called_once()


# Test resume starts inactive stream 
def test_resume_start_inactive_stream(mocker):
    stream = AudioStream(sample_rate=16000, device_id=1)
    mock_stream = mocker.Mock()
    mock_stream.active = False 
    stream.stream = mock_stream
    stream.resume()
    mock_stream.start.assert_called_once()


