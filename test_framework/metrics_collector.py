import time
import numpy as np
import jiwer

class MetricsCollector:
    def __init__(self):
        self.start_time = None
        self.chunk_start_times = []  # When each chunk was received
        self.chunk_end_times = []    # When each chunk was transcribed
        self.transcripts = []
        self.ground_truth = None

    def start_test(self):
        """ Records the start time of each test run """
        self.start_time = time.time()

    def record_chunk_start(self):
        """ Records when audio chunk is received by transcriber """
        self.chunk_start_times.append(time.time())

    def record_chunk_end(self, transcript):
        """ Records when transcription is completed for a chunk """
        self.chunk_end_times.append(time.time())
        self.transcripts.append(transcript)

    def calculate_latency(self):
        """ Calculates actual processing latency (input to output) """
        if not self.chunk_start_times or not self.chunk_end_times:
            return {'avg_latency': 0, 'total_time': 0}
        
        # Calculate processing time for each chunk
        processing_times = []
        for start, end in zip(self.chunk_start_times, self.chunk_end_times):
            processing_times.append(end - start)
        
        return {
            'avg_latency': np.mean(processing_times),
            # 'min_latency': np.min(processing_times),
            # 'max_latency': np.max(processing_times),
            # 'total_time': time.time() - self.start_time
        }
    
    def get_final_transcript(self):
        """ Combines all chunks into a single transcript """
        return ' '.join(self.transcripts)
    
    def calculate_wer(self, reference_transcript):
        """ Calculate Word Error Rate against reference transcript """
        if not self.transcripts:
            return 1.0  # 100% error if no transcription
        
        predicted = self.get_final_transcript()
        return jiwer.wer(reference_transcript, predicted)