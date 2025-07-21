import numpy as np 
import pytest 

from transcriber_app.track_metrics import MetricsTracker

@pytest.fixture
def tracker():
    return MetricsTracker(sample_rate=16000)

# -------------------------------------------------------------------------
# WPM tests  
# -------------------------------------------------------------------------

def test_track_wpm_basic(tracker):
    tracker.add_transcription("Hello there", duration=1.0)
    tracker.track_wpm()
    assert pytest.approx(tracker.current_wpm, rel=1e-6) == 120.0 #rel for relative tolerance

def test_track_wpm_zero_duration(tracker):
    tracker.add_transcription("test", duration=0.0)
    tracker.track_wpm()
    assert tracker.current_wpm == 0.0

def test_track_wpm_no_words(tracker):
    tracker.add_transcription("", duration=2.0)
    tracker.track_wpm()
    assert tracker.current_wpm == 0.0

def test_wpm_smoothing(tracker):
    # First utterance: 180 WPM
    tracker.add_transcription("a b c", duration=1.0)  
    tracker.track_wpm()
    first = tracker.current_wpm

    # Second utterance: 90 WPM
    tracker.add_transcription("a b c", duration=2.0)
    tracker.track_wpm()
    second = tracker.current_wpm

    # The current_wpm should now be the average of [180, 90] = 135
    assert pytest.approx(second, rel=1e-6) == (first + 90) / 2

def test_average_metrics_wpm(tracker):
    # 2w / (1/60) = 120 WPM
    tracker.add_transcription("one two", duration=1.0)         
    tracker.track_wpm()
    
    # 3w / (1/60) = 180 WPM
    tracker.add_transcription("one two three", duration=1.0)   
    tracker.track_wpm()
    
    # Compute average: [120, 180] = 150
    tracker.track_wpm_average()
    assert pytest.approx(tracker.average_wpm, rel=1e-6) == 150.0

# -------------------------------------------------------------------------
# Volume tests  
# -------------------------------------------------------------------------

def test_track_volume_constant_signal(tracker):
    chunk = np.ones(16000, dtype=np.float32)
    tracker.add_audio_chunk(chunk, duration=1.0)
    tracker.track_volume()
    assert pytest.approx(tracker.current_volume, abs=1e-3) == 0.0 #abs for absolute tolerance

def test_track_volume_empty(tracker):
    tracker.track_volume()
    assert tracker.current_volume == 0.0

def test_track_volume_half_amplitude(tracker):
    # A constant 0.5 amplitude signal: RMS = 0.5 → dB = 20·log10(0.5) ≈ -6.0206
    chunk = np.ones(16000, dtype=np.float32) * 0.5
    tracker.add_audio_chunk(chunk, duration=1.0)
    tracker.track_volume()
    expected_db = 20 * np.log10(0.5)
    assert pytest.approx(tracker.current_volume, rel=1e-3) == expected_db

def test_track_volume_quarter_amplitude(tracker):
    # A constant 0.25 amplitude signal: RMS = 0.25 → dB ≈ -12.0412
    chunk = np.ones(16000, dtype=np.float32) * 0.25
    tracker.add_audio_chunk(chunk, duration=1.0)
    tracker.track_volume()
    expected_db = 20 * np.log10(0.25)
    assert pytest.approx(tracker.current_volume, rel=1e-3) == expected_db

def test_volume_smoothing(tracker):
    # dB readings of 0 and -6 dB
    chunk1 = np.ones(16000, dtype=np.float32)
    tracker.add_audio_chunk(chunk1, duration=1.0)
    tracker.track_volume()
    db1 = tracker.current_volume

    chunk2 = np.ones(16000, dtype=np.float32) * 0.5
    tracker.add_audio_chunk(chunk2, duration=1.0)
    tracker.track_volume()
    db2 = tracker.current_volume

    # Now current_volume should be average of [db1, db2]
    assert pytest.approx(db2, rel=1e-3) == (db1 + (20*np.log10(0.5))) / 2

# -------------------------------------------------------------------------
# Pitch Tests  
# -------------------------------------------------------------------------

def test_track_pitch_silence(tracker):
    silent_chunk = np.zeros(16000, dtype=np.float32)
    tracker.add_audio_chunk(silent_chunk, duration=1.0)
    tracker.track_pitch()
    assert tracker.current_pitch == 0.0

def test_track_pitch_pure_tone(tracker):
    # A 440 Hz sine wave for 1 s: pyin should detect voiced frames
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sine440 = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    tracker.add_audio_chunk(sine440, duration=1.0)
    tracker.track_pitch()

    # We should have recorded exactly one variance value
    assert len(tracker.pitch_history) == 1

    # The variance should be positive (we detected voice)
    assert tracker.current_pitch > 0.0

    # And for a near‐pure tone, it shouldn’t be huge – e.g. under 50 Hz
    assert tracker.current_pitch < 50.0

def test_pitch_smoothing(tracker):
    # Create two artificial chunks:
    sr = tracker.sample_rate
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sine440 = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    sine880 = 0.5 * np.sin(2 * np.pi * 880 * t).astype(np.float32)

    # First chunk
    tracker.add_audio_chunk(sine440, duration=1.0)
    tracker.track_pitch()
    e1 = tracker.pitch_history[-1]

    # Second chunk
    tracker.add_audio_chunk(sine880, duration=1.0)
    tracker.track_pitch()
    e2 = tracker.pitch_history[-1]

    # We should have exactly two entries
    assert len(tracker.pitch_history) == 2

    # current_pitch is the average of e1 and e2
    expected = (e1 + e2) / 2
    assert pytest.approx(tracker.current_pitch, rel=1e-6) == expected

    # Both variances should be positive (voiced detection)
    assert e1 >= 0.0
    assert e2 >= 0.0



