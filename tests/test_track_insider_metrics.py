import pytest
import numpy as np
from transcriber_app.track_insider_metrics import TrackInsiderMetrics

@pytest.fixture
def insider_metrics():
    return TrackInsiderMetrics(chunk_history_size=5)

# -------------------------------------------------------------------------
# Chunk-level Silence Ratio tests  
# -------------------------------------------------------------------------

def test_silence_ratio_basic(insider_metrics):
    # Add some chunk silence ratios
    insider_metrics.add_chunk_silence_ratio(0.6)  # 60% silence in chunk
    insider_metrics.add_chunk_silence_ratio(0.8)  # 80% silence in chunk
    insider_metrics.add_chunk_silence_ratio(0.4)  # 40% silence in chunk
    
    # Average of [0.6, 0.8, 0.4] = 0.6
    assert pytest.approx(insider_metrics.get_silence_ratio(), rel=1e-6) == 0.6

def test_silence_ratio_no_chunks(insider_metrics):
    assert insider_metrics.get_silence_ratio() == 0.0

def test_silence_ratio_single_chunk(insider_metrics):
    insider_metrics.add_chunk_silence_ratio(0.75)
    assert insider_metrics.get_silence_ratio() == 0.75

def test_silence_ratio_rolling_window(insider_metrics):
    # Add chunks up to history size (5)
    insider_metrics.add_chunk_silence_ratio(0.2)  # 20% silence
    insider_metrics.add_chunk_silence_ratio(0.4)  # 40% silence
    insider_metrics.add_chunk_silence_ratio(0.6)  # 60% silence
    insider_metrics.add_chunk_silence_ratio(0.8)  # 80% silence
    insider_metrics.add_chunk_silence_ratio(1.0)  # 100% silence
    
    # Average of [0.2, 0.4, 0.6, 0.8, 1.0] = 0.6
    assert pytest.approx(insider_metrics.get_silence_ratio(), rel=1e-6) == 0.6
    
    # Add one more chunk - should drop oldest (0.2)
    insider_metrics.add_chunk_silence_ratio(0.0)  # 0% silence
    
    # Average of [0.4, 0.6, 0.8, 1.0, 0.0] = 0.56
    assert pytest.approx(insider_metrics.get_silence_ratio(), rel=1e-6) == 0.56

def test_silence_ratio_edge_cases(insider_metrics):
    # Test zero silence
    insider_metrics.add_chunk_silence_ratio(0.0)
    assert insider_metrics.get_silence_ratio() == 0.0
    
    # Test all silence
    insider_metrics.add_chunk_silence_ratio(1.0)
    assert insider_metrics.get_silence_ratio() == 0.5  # Average of [0.0, 1.0]

# -------------------------------------------------------------------------
# Confidence tests  
# -------------------------------------------------------------------------

def test_confidence_basic(insider_metrics):
    insider_metrics.add_confidence(0.8)
    assert pytest.approx(insider_metrics.get_confidence(), rel=1e-6) == 0.8

def test_confidence_no_scores(insider_metrics):
    assert insider_metrics.get_confidence() == 0.0

def test_confidence_rolling_window(insider_metrics):
    # First confidence: 0.6
    insider_metrics.add_confidence(0.6)
    first = insider_metrics.get_confidence()

    # Second confidence: 0.8
    insider_metrics.add_confidence(0.8)
    second = insider_metrics.get_confidence()

    # Should be average of [0.6, 0.8] = 0.7
    assert pytest.approx(second, rel=1e-6) == 0.7

def test_confidence_multiple_scores(insider_metrics):
    insider_metrics.add_confidence(0.6)
    insider_metrics.add_confidence(0.8)
    insider_metrics.add_confidence(0.7)
    
    # Average of [0.6, 0.8, 0.7] = 0.7
    assert pytest.approx(insider_metrics.get_confidence(), rel=1e-6) == 0.7

def test_confidence_edge_cases(insider_metrics):
    # Test low confidence
    insider_metrics.add_confidence(0.1)
    assert insider_metrics.get_confidence() == 0.1
    
    # Test high confidence
    insider_metrics.add_confidence(0.9)
    assert insider_metrics.get_confidence() == 0.5  # Average of [0.1, 0.9]

# -------------------------------------------------------------------------
# Integration tests
# -------------------------------------------------------------------------

def test_both_metrics_together(insider_metrics):
    # Add chunk silence ratios
    insider_metrics.add_chunk_silence_ratio(0.6)
    insider_metrics.add_chunk_silence_ratio(0.4)
    
    # Add confidence scores
    insider_metrics.add_confidence(0.75)
    insider_metrics.add_confidence(0.85)
    
    # Silence ratio: average of [0.6, 0.4] = 0.5
    assert pytest.approx(insider_metrics.get_silence_ratio(), rel=1e-6) == 0.5
    # Confidence: average of [0.75, 0.85] = 0.8
    assert pytest.approx(insider_metrics.get_confidence(), rel=1e-6) == 0.8

def test_metrics_summary(insider_metrics):
    insider_metrics.add_chunk_silence_ratio(0.5)
    insider_metrics.add_confidence(0.8)
    
    summary = insider_metrics.get_metrics_summary()
    assert 'silence_ratio' in summary
    assert 'confidence' in summary
    assert 'chunk_history_size' in summary
    assert 'confidence_history_size' in summary
    assert summary['chunk_history_size'] == 1
    assert summary['confidence_history_size'] == 1

def test_reset(insider_metrics):
    # Add some data
    insider_metrics.add_chunk_silence_ratio(0.5)
    insider_metrics.add_confidence(0.8)
    
    # Verify data exists
    assert insider_metrics.get_silence_ratio() > 0
    assert insider_metrics.get_confidence() > 0
    
    # Reset
    insider_metrics.reset()
    
    # Verify data is cleared
    assert insider_metrics.get_silence_ratio() == 0.0
    assert insider_metrics.get_confidence() == 0.0

def test_chunk_history_size_configuration():
    # Test with different history sizes
    small_history = TrackInsiderMetrics(chunk_history_size=2)
    large_history = TrackInsiderMetrics(chunk_history_size=10)
    
    # Add data to both
    for i in range(5):
        small_history.add_chunk_silence_ratio(0.5)
        large_history.add_chunk_silence_ratio(0.5)
    
    # Small history should only keep last 2 values
    assert len(small_history.chunk_silence_ratios) == 2
    
    # Large history should keep all 5 values
    assert len(large_history.chunk_silence_ratios) == 5 