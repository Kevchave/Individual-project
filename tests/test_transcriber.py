import pytest 
import numpy as np 
import queue 
from transcriber_app.transcriber import Transcriber 

def test_transcriber_init_loads_model(mocker):

    # 'mocker.patch' replaces the real 'load_function' with a mock 
    # so the test wont download or load a real model 
    mock_load_model = mocker.patch("transcriber_app.transcriber.whisper.load_model")

    # 'object()' creates a new unique empty object - used as a dummy
    dummy_model = object()

    # Tells the mock to return this dummy object when called
    mock_load_model.return_value = dummy_model

    # Runs the constructor which will instead use the mocked 'load_model'
    transcriber = Transcriber(model_size="tiny", device="cpu")

    # Assert that the constructor is called with the correct params and stores it
    mock_load_model.assert_called_once_with("tiny", device="cpu")
    assert transcriber.model is dummy_model 
    assert transcriber.device == "cpu"

def test_transcriber_stream_calls_callbacks_and_model(mocker):
    # Mock Whisper model and its 'transcribe' method 
    mock_model = mocker.Mock()
    mock_model.transcribe.return_value = {"text": "hello world"}

    # Patch whisper.load_model so that transcriber returns our 'mock_model' 
    mocker.patch("transcriber_app.transcriber.whisper.load_model", return_value=mock_model)

    # Mock webrtcvad and its 'is_speech' method
    mock_vad = mocker.Mock()         
    # 'side_effect' is a built in python feature for mock pobjects 
    # its used ot set attributes on a mock
    mock_vad.is_speech.side_effect = [True, True, False, False, False, False, False, False]

    # Patch webrtcvad.Vad so that transcriber returns our 'mock model' 
    mocker.patch("transcriber_app.transcriber.webrtcvad.Vad", return_value=mock_vad)

    # Create a fake audio queue filled with chunks to match our VAD pattern 
    audio_queue = queue.Queue()
    frame_size = int(16000 * 20 / 1000)
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # speech
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # speech
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(np.ones(frame_size, dtype=np.int16))  # silence
    audio_queue.put(None)  # to break the loop

    # Create mock callback functions (so we can checl if they are called )
    on_transcription = mocker.Mock()
    on_audio_chunk = mocker.Mock()

    # Create the transcriber and run the method 
    transcriber = Transcriber(model_size="tiny", device="cpu")
    transcriber.transcribe_stream(audio_queue, on_transcription, on_audio_chunk)

    # Assert the model's transcribe method was called once with expected arguments
    mock_model.transcribe.assert_called_once()
    args, kwargs = mock_model.transcribe.call_args

    # Checks that all the correct arguments are passed 
    assert isinstance(args[0], np.ndarray)      # checks first arg is a numpy array 
    assert args[0].dtype == np.float32          # checks numpy array is correct data type
    assert kwargs['fp16'] is False              # checks fp16 is set to false 
    assert kwargs['language'] == "en"           # checks language is false

    # Assert the model's calback functions are called once with expected arguments
    on_audio_chunk.assert_called_once()

    # Retrieve the arguments from the callback functions 
    audio_args, _ = on_audio_chunk.call_args    
    audio_float, segment_duration = audio_args

    # Checks that all the correct arguments are passed 
    assert isinstance(audio_float, np.ndarray) # checks audio data sent is a numpy array 
    assert audio_float.dtype == np.float32     # checks audio sent is of type float32
    assert isinstance(segment_duration, float) # checks segment duration sent is a float

    on_transcription.assert_called_once_with("hello world", segment_duration)

def test_transcribe_stream_no_speech(mocker):
    # Mock the model and defines transcribes return value 
    mock_model = mocker.Mock()
    mock_model.transcribe.return_value = {"text": "should not be called"}

    # Patch 'whisper.load_model' so that it returns a load model 
    mocker.patch("transcriber_app.transcriber.whisper.load_model", return_value=mock_model)

    # Create a mock for VAD and set all its frames to silence
    mock_vad = mocker.Mock()
    mock_vad.is_speech.side_effect = [False] * 8

    # Patch the VAD constructor to return the mock vad
    mocker.patch("transcriber_app.transcriber.webrtcvad.Vad", return_value=mock_vad)

    # Fill the queue with silence frames and a None to stop
    frame_size = int(16000 * 20 / 1000)
    audio_queue = queue.Queue()
    for _ in range(8):
        audio_queue.put(np.zeros(frame_size, dtype=np.int16))
    audio_queue.put(None)

    # Mock callbacks
    on_transcription = mocker.Mock()
    on_audio_chunk = mocker.Mock()

    # Instantiates Transcriber with the mocked model and run the method
    transcriber = Transcriber(model_size="small", device="cpu")
    transcriber.transcribe_stream(audio_queue, on_transcription, on_audio_chunk)

    # Assert neither callback nor model was called
    on_transcription.assert_not_called()
    on_audio_chunk.assert_not_called()
    mock_model.transcribe.assert_not_called()

# -------------- stopped here --------------

def test_transcribe_stream_multiple_segments(mocker):
    # Mock the model and VAD
    mock_model = mocker.Mock()
    mock_model.transcribe.side_effect = [
        {"text": "first segment"},
        {"text": "second segment"}
    ]
    mocker.patch("transcriber_app.transcriber.whisper.load_model", return_value=mock_model)
    mock_vad = mocker.Mock()
    # Speech, speech, silence x6 (segment 1), speech, speech, silence x6 (segment 2)
    mock_vad.is_speech.side_effect = [True, True] + [False]*6 + [True, True] + [False]*6
    mocker.patch("transcriber_app.transcriber.webrtcvad.Vad", return_value=mock_vad)

    frame_size = int(16000 * 20 / 1000)
    audio_queue = queue.Queue()
    # First segment
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    for _ in range(6):
        audio_queue.put(np.zeros(frame_size, dtype=np.int16))
    # Second segment
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    for _ in range(6):
        audio_queue.put(np.zeros(frame_size, dtype=np.int16))
    audio_queue.put(None)

    on_transcription = mocker.Mock()
    on_audio_chunk = mocker.Mock()

    transcriber = Transcriber(model_size="small", device="cpu")
    transcriber.transcribe_stream(audio_queue, on_transcription, on_audio_chunk)

    # Assert model and callbacks were called twice
    assert mock_model.transcribe.call_count == 2
    assert on_audio_chunk.call_count == 2
    assert on_transcription.call_count == 2
    # Check the texts
    on_transcription.assert_any_call("first segment", pytest.approx((2*frame_size)/16000, rel=1e-2))
    on_transcription.assert_any_call("second segment", pytest.approx((2*frame_size)/16000, rel=1e-2))

def test_transcribe_stream_callback_exception(mocker):
    # Mock the model and VAD
    mock_model = mocker.Mock()
    mock_model.transcribe.return_value = {"text": "should still call"}
    mocker.patch("transcriber_app.transcriber.whisper.load_model", return_value=mock_model)
    mock_vad = mocker.Mock()
    mock_vad.is_speech.side_effect = [True, True] + [False]*6
    mocker.patch("transcriber_app.transcriber.webrtcvad.Vad", return_value=mock_vad)

    frame_size = int(16000 * 20 / 1000)
    audio_queue = queue.Queue()
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    audio_queue.put(np.ones(frame_size, dtype=np.int16))
    for _ in range(6):
        audio_queue.put(np.zeros(frame_size, dtype=np.int16))
    audio_queue.put(None)

    # on_audio_chunk raises an exception
    def on_audio_chunk(audio, duration):
        raise RuntimeError("Callback error!")
    on_transcription = mocker.Mock()

    transcriber = Transcriber(model_size="small", device="cpu")
    # The exception should propagate, so we check with pytest.raises
    with pytest.raises(RuntimeError, match="Callback error!"):
        transcriber.transcribe_stream(audio_queue, on_transcription, on_audio_chunk)
    # on_transcription should not be called because the exception interrupts the flow
    on_transcription.assert_not_called()

