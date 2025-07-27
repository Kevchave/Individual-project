import pytest
from transcriber_app.adaptive_controller import AdaptiveController

def test_adaptive_controller_init():
    """Test that AdaptiveController initializes with correct default values"""
    controller = AdaptiveController()
    
    # Check default parameters
    aggressiveness, frame_duration_ms, max_silence_frames = controller.get_current_parameters()
    assert aggressiveness == 3
    assert frame_duration_ms == 20
    assert max_silence_frames == 5
    
    # Check default thresholds
    assert controller.confidence_threshold_low == 0.6
    assert controller.confidence_threshold_high == 0.8
    assert controller.silence_ratio_threshold_high == 0.7
    assert controller.silence_ratio_threshold_low == 0.3
    assert controller.wpm_threshold_fast == 150
    assert controller.wpm_threshold_slow == 80
    
    # Check averaging window
    assert controller.chunk_averaging_window == 5
    assert len(controller.metrics_buffer) == 0
    assert controller.chunk_counter == 0

def test_should_adjust_parameters_low_confidence():
    """Test that should_adjust_parameters returns True when confidence is too low"""
    controller = AdaptiveController()
    
    # Test with low confidence for 5 chunks
    metrics = {'wpm': 100, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.4}  # Below 0.6 threshold
    
    # First 4 chunks should return False (not enough data)
    for i in range(4):
        should_adjust = controller.should_adjust_parameters(metrics, insider_metrics)
        assert should_adjust == False
        assert controller.chunk_counter == i + 1
    
    # 5th chunk should return True (enough data and low confidence)
    should_adjust = controller.should_adjust_parameters(metrics, insider_metrics)
    assert should_adjust == True

def test_should_adjust_parameters_normal_confidence():
    """Test that should_adjust_parameters returns False when confidence is normal"""
    controller = AdaptiveController()
    
    # Test with normal confidence for 5 chunks
    metrics = {'wpm': 100, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.7}  # Between 0.6 and 0.8
    
    # All chunks should return False (normal confidence)
    for i in range(5):
        should_adjust = controller.should_adjust_parameters(metrics, insider_metrics)
        assert should_adjust == False

def test_calculate_parameter_adjustments_low_confidence():
    """Test that low confidence increases aggressiveness"""
    controller = AdaptiveController()
    
    # Start with default parameters
    assert controller.get_current_parameters() == (3, 20, 5)
    
    # Fill buffer with low confidence data
    metrics = {'wpm': 100, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.4}
    
    for _ in range(5):
        controller.metrics_buffer.append({
            'metrics': metrics,
            'insider_metrics': insider_metrics
        })
    
    new_parameters = controller.calculate_parameter_adjustments(metrics, insider_metrics)
    
    # Should increase aggressiveness (but stay within bounds)
    assert new_parameters['aggressiveness'] == 3  # Already at max, can't increase
    assert new_parameters['frame_duration_ms'] == 20  # Normal WPM, no change
    assert new_parameters['max_silence_frames'] == 5  # Normal silence ratio, no change

def test_calculate_parameter_adjustments_high_wpm():
    """Test that high WPM reduces frame duration"""
    controller = AdaptiveController()
    
    # Fill buffer with high WPM data
    metrics = {'wpm': 200, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}  # Above 150 threshold
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.7}
    
    for _ in range(5):
        controller.metrics_buffer.append({
            'metrics': metrics,
            'insider_metrics': insider_metrics
        })
    
    new_parameters = controller.calculate_parameter_adjustments(metrics, insider_metrics)
    
    # Should use smaller frame duration for fast speech
    assert new_parameters['frame_duration_ms'] == 10
    assert new_parameters['aggressiveness'] == 3  # Normal confidence, no change
    assert new_parameters['max_silence_frames'] == 5  # Normal silence ratio, no change

def test_calculate_parameter_adjustments_low_wpm():
    """Test that low WPM increases frame duration"""
    controller = AdaptiveController()
    
    # Fill buffer with low WPM data
    metrics = {'wpm': 50, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}  # Below 80 threshold
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.7}
    
    for _ in range(5):
        controller.metrics_buffer.append({
            'metrics': metrics,
            'insider_metrics': insider_metrics
        })
    
    new_parameters = controller.calculate_parameter_adjustments(metrics, insider_metrics)
    
    # Should use larger frame duration for slow speech
    assert new_parameters['frame_duration_ms'] == 30
    assert new_parameters['aggressiveness'] == 3  # Normal confidence, no change
    assert new_parameters['max_silence_frames'] == 5  # Normal silence ratio, no change

def test_update_parameters():
    """Test that update_parameters correctly updates current values"""
    controller = AdaptiveController()
    
    # Start with defaults
    assert controller.get_current_parameters() == (3, 20, 5)
    
    # Update with new parameters
    new_parameters = {
        'aggressiveness': 2,
        'frame_duration_ms': 30,
        'max_silence_frames': 8
    }
    
    # Update should return True (parameters changed)
    changed = controller.update_parameters(new_parameters)
    assert changed == True
    
    # Check that parameters were updated
    assert controller.get_current_parameters() == (2, 30, 8)
    
    # Check that chunk counter was reset
    assert controller.chunk_counter == 0

def test_update_parameters_no_change():
    """Test that update_parameters returns False when no change is made"""
    controller = AdaptiveController()
    
    # Start with defaults
    assert controller.get_current_parameters() == (3, 20, 5)
    
    # Try to update with same values
    new_parameters = {
        'aggressiveness': 3,
        'frame_duration_ms': 20,
        'max_silence_frames': 5
    }
    
    # Update should return False (no change)
    changed = controller.update_parameters(new_parameters)
    assert changed == False

def test_update_parameters_insignificant_change():
    """Test that update_parameters returns False for insignificant changes"""
    controller = AdaptiveController()
    
    # Start with defaults
    assert controller.get_current_parameters() == (3, 20, 5)
    
    # Try to update with insignificant change (max_silence_frames only +1)
    new_parameters = {
        'aggressiveness': 3,  # No change
        'frame_duration_ms': 20,  # No change
        'max_silence_frames': 6  # Only +1, not significant enough
    }
    
    # Update should return False (insignificant change)
    changed = controller.update_parameters(new_parameters)
    assert changed == False

def test_get_status():
    """Test that get_status returns correct information"""
    controller = AdaptiveController()
    
    status = controller.get_status()
    
    assert 'current_aggressiveness' in status
    assert 'current_frame_duration_ms' in status
    assert 'current_max_silence_frames' in status
    assert 'adjustment_count' in status
    assert 'last_adjustment_time' in status
    assert 'chunk_counter' in status
    assert 'buffer_size' in status
    assert 'averaging_window' in status
    
    assert status['current_aggressiveness'] == 3
    assert status['current_frame_duration_ms'] == 20
    assert status['current_max_silence_frames'] == 5
    assert status['adjustment_count'] == 0
    assert status['chunk_counter'] == 0
    assert status['buffer_size'] == 0
    assert status['averaging_window'] == 5

def test_reset():
    """Test that reset returns controller to default parameters"""
    controller = AdaptiveController()
    
    # Change some parameters
    controller.update_parameters({
        'aggressiveness': 1,
        'frame_duration_ms': 10,
        'max_silence_frames': 3
    })
    
    # Add some data to buffer
    metrics = {'wpm': 100, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.7}
    controller.metrics_buffer.append({'metrics': metrics, 'insider_metrics': insider_metrics})
    controller.chunk_counter = 3
    
    # Verify they changed
    assert controller.get_current_parameters() == (1, 10, 3)
    assert len(controller.metrics_buffer) == 1
    assert controller.chunk_counter == 3
    
    # Reset
    controller.reset()
    
    # Should be back to defaults
    assert controller.get_current_parameters() == (3, 20, 5)
    assert controller.get_status()['adjustment_count'] == 0
    assert len(controller.metrics_buffer) == 0
    assert controller.chunk_counter == 0

def test_averaging_window_behavior():
    """Test that averaging window correctly limits buffer size"""
    controller = AdaptiveController(chunk_averaging_window=3)
    
    metrics = {'wpm': 100, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}
    insider_metrics = {'silence_ratio': 0.5, 'confidence': 0.7}
    
    # Add 5 chunks to a 3-chunk window
    for i in range(5):
        controller.should_adjust_parameters(metrics, insider_metrics)
    
    # Buffer should only contain last 3 chunks
    assert len(controller.metrics_buffer) == 3
    assert controller.chunk_counter == 5

def test_priority_based_adjustments():
    """Test that adjustments follow priority order: confidence > silence_ratio > wpm"""
    controller = AdaptiveController()
    
    # Fill buffer with data that would trigger all three adjustments
    metrics = {'wpm': 200, 'volume': -20, 'pitch': 150, 'chunk_duration': 2.0}  # High WPM
    insider_metrics = {'silence_ratio': 0.8, 'confidence': 0.4}  # High silence, low confidence
    
    for _ in range(5):
        controller.metrics_buffer.append({
            'metrics': metrics,
            'insider_metrics': insider_metrics
        })
    
    new_parameters = controller.calculate_parameter_adjustments(metrics, insider_metrics)
    
    # All three should be adjusted
    assert new_parameters['aggressiveness'] == 3  # Low confidence should increase (but already at max)
    assert new_parameters['max_silence_frames'] == 4  # High silence ratio should decrease
    assert new_parameters['frame_duration_ms'] == 10  # High WPM should use smaller frames 