import threading
import time
from typing import Dict, Tuple

class AdaptiveController:
    """
    Monitors transcription metrics and provides adaptive chunking parameter adjustments.
    This controller analyzes both UI metrics and internal metrics to optimize transcription quality.
    """
    
    # Constructor 
    def __init__(self, 
                 confidence_threshold_low=0.6,
                 confidence_threshold_high=0.8,
                 silence_ratio_threshold_high=0.7,
                 silence_ratio_threshold_low=0.3,
                 wpm_threshold_fast=150,
                 wpm_threshold_slow=80):

        # Thresholds for parameter adjustment
        self.confidence_threshold_low = confidence_threshold_low
        self.confidence_threshold_high = confidence_threshold_high
        self.silence_ratio_threshold_high = silence_ratio_threshold_high
        self.silence_ratio_threshold_low = silence_ratio_threshold_low
        self.wpm_threshold_fast = wpm_threshold_fast
        self.wpm_threshold_slow = wpm_threshold_slow
        
        # Current parameter values
        self.current_aggressiveness = 3
        self.current_frame_duration_ms = 20
        self.current_max_silence_frames = 5
        
        # Parameter bounds
        self.aggressiveness_bounds = (0, 3)  # 0-3 for VAD
        self.frame_duration_bounds = (10, 30)  # 10, 20, or 30ms
        self.max_silence_frames_bounds = (1, 10)
        
        # Thread safety - only one thread can change parameters at a time
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
        confidence = insider_metrics.get('confidence', 0.5)
        silence_ratio = insider_metrics.get('silence_ratio', 0.5)
        wpm = metrics.get('wpm', 100)
        
        # Check if any metric is outside optimal ranges
        confidence_needs_adjustment = (
            confidence < self.confidence_threshold_low or 
            confidence > self.confidence_threshold_high
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
        confidence = insider_metrics.get('confidence', 0.5)
        silence_ratio = insider_metrics.get('silence_ratio', 0.5)
        wpm = metrics.get('wpm', 100)
        
        new_aggressiveness = self.current_aggressiveness
        new_frame_duration_ms = self.current_frame_duration_ms
        new_max_silence_frames = self.current_max_silence_frames
        
        # Adjust aggressiveness based on confidence and silence ratio
        if confidence < self.confidence_threshold_low:
            # Low confidence - increase aggressiveness (more sensitive to silence)
            new_aggressiveness = min(new_aggressiveness + 1, self.aggressiveness_bounds[1])
        elif confidence > self.confidence_threshold_high:
            # High confidence - decrease aggressiveness (less sensitive to silence)
            new_aggressiveness = max(new_aggressiveness - 1, self.aggressiveness_bounds[0])
        
        # Adjust max silence frames based on silence ratio
        if silence_ratio > self.silence_ratio_threshold_high:
            # Too much silence - reduce max silence frames for shorter chunks
            new_max_silence_frames = max(new_max_silence_frames - 1, self.max_silence_frames_bounds[0])
        elif silence_ratio < self.silence_ratio_threshold_low:
            # Too little silence - increase max silence frames for longer chunks
            new_max_silence_frames = min(new_max_silence_frames + 1, self.max_silence_frames_bounds[1])
        
        # Adjust frame duration based on WPM
        if wpm > self.wpm_threshold_fast:
            # Fast speech - smaller frames for precision
            new_frame_duration_ms = 10
        elif wpm < self.wpm_threshold_slow:
            # Slow speech - larger frames for efficiency
            new_frame_duration_ms = 30
        else:
            # Normal speech
            new_frame_duration_ms = 20
        
        # Return the new params as a dictionary 
        return {
            'aggressiveness': new_aggressiveness,
            'frame_duration_ms': new_frame_duration_ms,
            'max_silence_frames': new_max_silence_frames
        }
    
    def update_parameters(self, new_parameters: Dict) -> bool:
        with self.lock:
            old_aggressiveness = self.current_aggressiveness
            old_frame_duration = self.current_frame_duration_ms
            old_max_silence = self.current_max_silence_frames
            
            self.current_aggressiveness = new_parameters.get('aggressiveness', self.current_aggressiveness)
            self.current_frame_duration_ms = new_parameters.get('frame_duration_ms', self.current_frame_duration_ms)
            self.current_max_silence_frames = new_parameters.get('max_silence_frames', self.current_max_silence_frames)
            
            # Check if any parameter changed
            parameters_changed = (
                old_aggressiveness != self.current_aggressiveness or
                old_frame_duration != self.current_frame_duration_ms or
                old_max_silence != self.current_max_silence_frames
            )
            
            if parameters_changed:
                self.adjustment_count += 1
                self.last_adjustment_time = time.time()
                print(f"[ADAPTIVE] Parameters adjusted: Aggressiveness={self.current_aggressiveness}, "
                      f"Frame Duration={self.current_frame_duration_ms}ms, "
                      f"Max Silence Frames={self.current_max_silence_frames}")
            
            return parameters_changed
    
    def get_status(self) -> Dict:
        with self.lock:
            return {
                'current_aggressiveness': self.current_aggressiveness,
                'current_frame_duration_ms': self.current_frame_duration_ms,
                'current_max_silence_frames': self.current_max_silence_frames,
                'adjustment_count': self.adjustment_count,
                'last_adjustment_time': self.last_adjustment_time
            }
    
    def reset(self):
        with self.lock:
            self.current_aggressiveness = 3
            self.current_frame_duration_ms = 20
            self.current_max_silence_frames = 5
            self.adjustment_count = 0
            self.last_adjustment_time = time.time()
            print("[ADAPTIVE] Controller reset to default parameters") 