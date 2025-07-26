import threading
import numpy as np
from collections import deque
import time

class TrackInsiderMetrics:
    """
    Tracks internal metrics for adaptive chunking (silence ratio and confidence scores).
    These metrics are calculated when chunks are finalized, aligned with UI metrics.
    """
    
    def __init__(self, chunk_history_size=5):
        # Rolling window histories for smoothing across chunks
        self.chunk_history_size = chunk_history_size
        self.chunk_silence_ratios = deque(maxlen=chunk_history_size)
        self.confidence_scores = deque(maxlen=chunk_history_size)
        
        # Current rolling averages
        self.current_silence_ratio = 0.0
        self.current_confidence = 0.0
        
        # Thread safety
        self.silence_lock = threading.Lock()
        self.confidence_lock = threading.Lock()
        
        # Debug info
        self.last_update_time = time.time()
    
    def add_chunk_silence_ratio(self, silence_ratio):
        """Add silence ratio from a completed chunk and update rolling average"""
        with self.silence_lock:
            self.chunk_silence_ratios.append(silence_ratio)
            self.current_silence_ratio = float(np.mean(self.chunk_silence_ratios))
    
    def add_confidence(self, confidence):
        """Add a confidence score and update rolling average"""
        with self.confidence_lock:
            self.confidence_scores.append(confidence)
            self.current_confidence = float(np.mean(self.confidence_scores))
    
    def get_silence_ratio(self):
        """Get current rolling average silence ratio"""
        return self.current_silence_ratio
    
    def get_confidence(self):
        """Get current rolling average confidence score"""
        return self.current_confidence
    
    def get_metrics_summary(self):
        """Get a summary of all internal metrics"""
        return {
            'silence_ratio': self.current_silence_ratio,
            'confidence': self.current_confidence,
            'chunk_history_size': len(self.chunk_silence_ratios),
            'confidence_history_size': len(self.confidence_scores)
        }
    
    def print_summary(self):
        """Print internal metrics summary to terminal"""
        print(f"[INSIDER METRICS] Silence Ratio: {self.current_silence_ratio:.3f} | Confidence: {self.current_confidence:.3f} | Chunks: {len(self.chunk_silence_ratios)}/{self.chunk_history_size}\n")
    
    def reset(self):
        """Reset all metrics (useful for testing or new sessions)"""
        with self.silence_lock:
            self.chunk_silence_ratios.clear()
            self.current_silence_ratio = 0.0
        
        with self.confidence_lock:
            self.confidence_scores.clear()
            self.current_confidence = 0.0
        
        self.last_update_time = time.time() 