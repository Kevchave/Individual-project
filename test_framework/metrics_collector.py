"""
Metrics Collector for Transcription Performance Testing

This module provides latency measurement for speech-to-text transcription systems.
It measures two types of latency:

1. Processing Latency: Time from audio chunk reception to transcription completion
   - Measures core Whisper model performance
   - Start: record_chunk_start() in transcriber.py
   - End: record_chunk_end() in transcriber.py

2. Callback Latency: Time from audio chunk reception to callback completion
   - Measures processing + callback overhead (but NOT UI rendering)
   - Start: record_chunk_start() in transcriber.py  
   - End: record_chunk_callback() in main.py (on_transcription callback)
   - This represents the "backend-to-frontend" timing bottleneck

Note: True end-to-end latency (including UI rendering) would require:
- Visual analysis of screen updates
- Browser-based performance measurement
- Computer vision for text detection
- Significant additional complexity and overhead

The current approach provides valuable performance insights while maintaining
simplicity and low overhead for testing purposes.
"""

import time
import numpy as np
from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, RemoveMultipleSpaces, Strip


def split_into_words(sentences):
    """Custom function to split sentences into words"""
    if isinstance(sentences, str):
        return sentences.split()
    return [sentence.split() for sentence in sentences]

transform = Compose([
    ToLowerCase(),
    RemovePunctuation(),
    RemoveMultipleSpaces(),
    Strip(),
    split_into_words
])


class MetricsCollector:
    def __init__(self):
        self.start_time = None
        self.chunk_start_times = []  # When each chunk was received
        self.chunk_end_times = []    # When each chunk was transcribed
        self.chunk_callback_times = []  # When transcription callback completes
        self.transcripts = []
        self.ground_truth = None

    def start_test(self):
        """ Records the start time of each test run """
        self.start_time = time.time()

    # This function is called within transcriber.py
    def record_chunk_start(self):
        """ Records when audio chunk is received by transcriber """
        self.chunk_start_times.append(time.time())

    # This function is called within transcriber.py
    def record_chunk_end(self, transcript):
        """ Records when transcription is completed for a chunk """
        self.chunk_end_times.append(time.time())
        self.transcripts.append(transcript)

    def record_chunk_callback(self):
        """
        Records when transcription callback completes (callback latency measurement)
        
        Note: This measures the time from audio reception to callback completion,
        NOT true end-to-end latency including UI rendering. This represents
        processing time + callback overhead, which is often the main bottleneck
        in real applications.
        """
        self.chunk_callback_times.append(time.time())

    def calculate_latency(self):
        """
        Calculates callback latency only (single source of truth)
        
        Callback Latency: Time from audio chunk reception to callback completion
                          (includes processing + callback overhead, but NOT UI rendering)
        """
        if not self.chunk_start_times:
            return {
                'avg_callback_latency': 0,
                'p50_callback_latency': 0,
                'p90_callback_latency': 0,
                'callback_latencies': []
            }
        
        # Prefer true callback timestamps; if missing, fall back to transcription end
        callback_times = []
        if self.chunk_callback_times and len(self.chunk_callback_times) == len(self.chunk_start_times):
            for start, callback in zip(self.chunk_start_times, self.chunk_callback_times):
                callback_times.append(callback - start)
        elif self.chunk_end_times and len(self.chunk_end_times) == len(self.chunk_start_times):
            # Fallback: approximate callback as processing completion
            for start, end in zip(self.chunk_start_times, self.chunk_end_times):
                callback_times.append(end - start)
        else:
            callback_times = [0] * len(self.chunk_start_times)
        
        return {
            'avg_callback_latency': np.mean(callback_times) if callback_times else 0,
            'p50_callback_latency': np.percentile(callback_times, 50) if callback_times else 0,
            'p90_callback_latency': np.percentile(callback_times, 90) if callback_times else 0,
            'callback_latencies': callback_times
        }
    
    def get_final_transcript(self):
        """ Combines all chunks into a single transcript """
        return ' '.join(self.transcripts)
    
    def calculate_wer(self, reference_transcript):
        """ Calculate Word Error Rate against reference transcript """
        if not self.transcripts:
            return 1.0  # 100% error if no transcription
        
        predicted = self.get_final_transcript()
        
        # Calculate WER using JIWER and normalizing both transcripts 
        word_error_rate = wer(reference_transcript, predicted, 
                             reference_transform=transform, 
                             hypothesis_transform=transform)
        
        return word_error_rate