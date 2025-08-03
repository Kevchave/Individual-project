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
        self.chunk_display_times = []  # When each chunk appears on screen
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

    def record_chunk_display(self):
        """ Records when text appears on screen (end-to-end latency) """
        self.chunk_display_times.append(time.time())

    def calculate_latency(self):
        """ Calculates both processing and end-to-end latency """
        if not self.chunk_start_times or not self.chunk_end_times:
            return {'avg_processing_latency': 0, 'avg_end_to_end_latency': 0}
        
        # Calculate processing time for each chunk
        processing_times = []
        for start, end in zip(self.chunk_start_times, self.chunk_end_times):
            processing_times.append(end - start)
        
        # Calculate end-to-end time for each chunk
        end_to_end_times = []
        if self.chunk_display_times and len(self.chunk_display_times) == len(self.chunk_start_times):
            for start, display in zip(self.chunk_start_times, self.chunk_display_times):
                end_to_end_times.append(display - start)
        
        return {
            'avg_processing_latency': np.mean(processing_times),
            'avg_end_to_end_latency': np.mean(end_to_end_times) if end_to_end_times else np.mean(processing_times),
            'processing_latencies': processing_times,
            'end_to_end_latencies': end_to_end_times if end_to_end_times else processing_times
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