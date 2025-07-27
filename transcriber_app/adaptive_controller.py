import threading
import time
from typing import Dict, Tuple, List

class AdaptiveController:
    """
    Monitors transcription metrics and provides adaptive chunking parameter adjustments.
    This controller analyzes both UI metrics and internal metrics to optimize transcription quality.
    Uses averaging over multiple chunks to make stable decisions.
    """
    
    # Constructor - initialises adaptive controller with configurable thresholds 
    def __init__(self, 
                 confidence_threshold_low=0.4,
                 confidence_threshold_high=0.7,
                 silence_ratio_threshold_high=0.7,
                 silence_ratio_threshold_low=0.3,
                 wpm_threshold_fast=150,
                 wpm_threshold_slow=80,
                 chunk_averaging_window=5):

        # Thresholds for parameter adjustment
        self.confidence_threshold_low = confidence_threshold_low 
        self.confidence_threshold_high = confidence_threshold_high  # Keep for reference
        self.silence_ratio_threshold_high = silence_ratio_threshold_high 
        self.silence_ratio_threshold_low = silence_ratio_threshold_low 
        self.wpm_threshold_fast = wpm_threshold_fast 
        self.wpm_threshold_slow = wpm_threshold_slow 
        self.chunk_averaging_window = chunk_averaging_window 
        
        # Current parameter values
        self.current_aggressiveness = 3
        self.current_frame_duration_ms = 20
        self.current_max_silence_frames = 5
        
        # Parameter bounds
        self.aggressiveness_bounds = (0, 3)  # 0-3 for VAD 
        self.frame_duration_bounds = (10, 30)  # 10, 20, or 30ms 
        self.max_silence_frames_bounds = (1, 10) 
        
        # Averaging and timing control
        self.metrics_buffer = []  # Store metrics from last N chunks
        self.chunk_counter = 0    # Count chunks since last adjustment
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Debug info
        self.last_adjustment_time = time.time()
        self.adjustment_count = 0
    
    def get_current_parameters(self) -> Tuple[int, int, int]:
        # Get the current chunking parameters and return them as a tuple
        with self.lock:
            return (
                self.current_aggressiveness,
                self.current_frame_duration_ms,
                self.current_max_silence_frames
            )
    
    def should_adjust_parameters(self, metrics: Dict, insider_metrics: Dict) -> bool:
        # Determine if parameters should be adjusted based on averaged metrics

        with self.lock:
            # Add current metrics to buffer
            self.metrics_buffer.append({
                'metrics': metrics.copy(),
                'insider_metrics': insider_metrics.copy()
            })
            
            # Keep only last N chunks
            if len(self.metrics_buffer) > self.chunk_averaging_window:
                self.metrics_buffer.pop(0)
            
            # Increment chunk counter
            self.chunk_counter += 1
            
            # Only check every N chunks (averaging window)
            if self.chunk_counter < self.chunk_averaging_window:
                return False
            
            # Calculate averages
            avg_metrics = self._calculate_average_metrics()
            
            # Check if adjustment needed based on averages
            needs_adjustment = self._check_adjustment_needed(avg_metrics)
            
            if needs_adjustment:
                print(f"[ADAPTIVE] Averaged metrics suggest adjustment needed:")
                print(f"[ADAPTIVE] Avg WPM: {avg_metrics['wpm']:.1f}, "
                      f"Avg Confidence: {avg_metrics['confidence']:.3f}, "
                      f"Avg Silence Ratio: {avg_metrics['silence_ratio']:.3f}")
            
            return needs_adjustment
    
    def _calculate_average_metrics(self) -> Dict:
        # Calculate average metrics over the buffer window

        if not self.metrics_buffer:
            return {'wpm': 100, 'confidence': 0.5, 'silence_ratio': 0.5}
        
        # Calculate averages
        avg_wpm = sum(m['metrics']['wpm'] for m in self.metrics_buffer) / len(self.metrics_buffer)
        avg_confidence = sum(m['insider_metrics']['confidence'] for m in self.metrics_buffer) / len(self.metrics_buffer)
        avg_silence_ratio = sum(m['insider_metrics']['silence_ratio'] for m in self.metrics_buffer) / len(self.metrics_buffer)
        
        return {
            'wpm': avg_wpm,
            'confidence': avg_confidence,
            'silence_ratio': avg_silence_ratio
        }
    
    def _check_adjustment_needed(self, avg_metrics: Dict) -> bool:
        # Check if any averaged metric is outside optimal ranges

        confidence = avg_metrics['confidence']
        silence_ratio = avg_metrics['silence_ratio']
        wpm = avg_metrics['wpm']
        
        # Check if any metric is outside optimal ranges
        confidence_needs_adjustment = (
            confidence < self.confidence_threshold_low  # Only adjust if confidence is LOW
        )
        
        silence_needs_adjustment = (
            silence_ratio > self.silence_ratio_threshold_high or
            silence_ratio < self.silence_ratio_threshold_low
        )
        
        wpm_needs_adjustment = (
            wpm > self.wpm_threshold_fast or
            wpm < self.wpm_threshold_slow
        )
        
        return confidence_needs_adjustment or silence_needs_adjustment or wpm_needs_adjustment
    
    def calculate_parameter_adjustments(self, metrics: Dict, insider_metrics: Dict) -> Dict:
        # Complete priority-based adjustment: confidence > silence_ratio > wpm
        
        # Calculate averages
        avg_metrics = self._calculate_average_metrics()
        
        confidence = avg_metrics['confidence']
        silence_ratio = avg_metrics['silence_ratio']
        wpm = avg_metrics['wpm']
        
        new_aggressiveness = self.current_aggressiveness
        new_frame_duration_ms = self.current_frame_duration_ms
        new_max_silence_frames = self.current_max_silence_frames
        
        # Priority 1: Adjust aggressiveness based on confidence (most critical)
        # Low confidence - increase aggressiveness (more sensitive to silence)

        if confidence < self.confidence_threshold_low:
            new_aggressiveness = min(new_aggressiveness + 1, self.aggressiveness_bounds[1])
            print(f"[ADAPTIVE] Low confidence ({confidence:.3f}) - increasing aggressiveness to {new_aggressiveness}")
        
        # Priority 2: Adjust max silence frames based on silence ratio (medium priority)
        if silence_ratio > self.silence_ratio_threshold_high:

            # Too much silence - reduce max silence frames for shorter chunks
            new_max_silence_frames = max(new_max_silence_frames - 1, self.max_silence_frames_bounds[0])
            print(f"[ADAPTIVE] High silence ratio ({silence_ratio:.3f}) - reducing max silence frames to {new_max_silence_frames}")
        elif silence_ratio < self.silence_ratio_threshold_low:

            # Too little silence - increase max silence frames for longer chunks
            new_max_silence_frames = min(new_max_silence_frames + 1, self.max_silence_frames_bounds[1])
            print(f"[ADAPTIVE] Low silence ratio ({silence_ratio:.3f}) - increasing max silence frames to {new_max_silence_frames}")
        
        # Priority 3: Adjust frame duration based on WPM (lowest priority)
        if wpm > self.wpm_threshold_fast:
            # Fast speech - smaller frames for precision
            new_frame_duration_ms = 10
            print(f"[ADAPTIVE] Fast speech ({wpm:.1f} WPM) - using 10ms frames")
        elif wpm < self.wpm_threshold_slow:
            # Slow speech - larger frames for efficiency
            new_frame_duration_ms = 30
            print(f"[ADAPTIVE] Slow speech ({wpm:.1f} WPM) - using 30ms frames")
        else:
            # Normal speech
            new_frame_duration_ms = 20
            print(f"[ADAPTIVE] Normal speech ({wpm:.1f} WPM) - using 20ms frames")
        
        return {
            'aggressiveness': new_aggressiveness,
            'frame_duration_ms': new_frame_duration_ms,
            'max_silence_frames': new_max_silence_frames
        }
    
    def update_parameters(self, new_parameters: Dict) -> bool:
        # Update the current parameters if changes are significant enough

        with self.lock:
            old_aggressiveness = self.current_aggressiveness
            old_frame_duration = self.current_frame_duration_ms
            old_max_silence = self.current_max_silence_frames
            
            # Check if changes are significant enough
            significant_change = (
                abs(new_parameters.get('aggressiveness', old_aggressiveness) - old_aggressiveness) >= 1 or
                abs(new_parameters.get('max_silence_frames', old_max_silence) - old_max_silence) >= 1 or 
                new_parameters.get('frame_duration_ms', old_frame_duration) != old_frame_duration
            )
            
            if not significant_change:
                print(f"[ADAPTIVE] Changes not significant enough - keeping current parameters")
                return False
            
            # Apply changes
            self.current_aggressiveness = new_parameters.get('aggressiveness', self.current_aggressiveness)
            self.current_frame_duration_ms = new_parameters.get('frame_duration_ms', self.current_frame_duration_ms)
            self.current_max_silence_frames = new_parameters.get('max_silence_frames', self.current_max_silence_frames)
            
            # Reset chunk counter after adjustment
            self.chunk_counter = 0
            
            # Update statistics
            self.adjustment_count += 1
            self.last_adjustment_time = time.time()
            
            print(f"[ADAPTIVE] Parameters updated successfully:")
            print(f"[ADAPTIVE] Aggressiveness: {old_aggressiveness} → {self.current_aggressiveness}")
            print(f"[ADAPTIVE] Frame Duration: {old_frame_duration}ms → {self.current_frame_duration_ms}ms")
            print(f"[ADAPTIVE] Max Silence Frames: {old_max_silence} → {self.current_max_silence_frames}")
            
            return True
    
    def get_status(self) -> Dict:
        with self.lock:
            return {
                'current_aggressiveness': self.current_aggressiveness,
                'current_frame_duration_ms': self.current_frame_duration_ms,
                'current_max_silence_frames': self.current_max_silence_frames,
                'adjustment_count': self.adjustment_count,
                'last_adjustment_time': self.last_adjustment_time,
                'chunk_counter': self.chunk_counter,
                'buffer_size': len(self.metrics_buffer),
                'averaging_window': self.chunk_averaging_window
            }
    
    def reset(self):
        # Reset the adaptive controller to default parameters.
        with self.lock:
            self.current_aggressiveness = 3
            self.current_frame_duration_ms = 20
            self.current_max_silence_frames = 5
            self.adjustment_count = 0
            self.last_adjustment_time = time.time()
            self.chunk_counter = 0
            self.metrics_buffer.clear()
            print("[ADAPTIVE] Controller reset to default parameters") 