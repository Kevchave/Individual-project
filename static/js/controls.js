import { initialiseCharts, resetCharts } from './charts.js';
import { pollTranscript, pollMetrics } from './polling.js';
import { 
    startTime, setStartTime, 
    metricsMode, setMetricsMode, 
    transcriptInterval, setTranscriptInterval, 
    metricsInterval, setMetricsInterval, 
    isPaused, setIsPaused 
} from './state.js';

function updateMetricsDisplay(metricsMode) {
    if (metricsMode === "live") {
        document.getElementById('wpm-label').textContent = 'Words per Minute';
        document.getElementById('volume-label').textContent = 'Volume (dBFS)';
        document.getElementById('pitch-label').textContent = 'Pitch Variance (Hz)';
        document.getElementById('wpm-value').textContent = '0';
        document.getElementById('volume-value').textContent = '0';
        document.getElementById('pitch-value').textContent = '0';
    } else {
        document.getElementById('wpm-label').textContent = 'Average Words per Minute';
        document.getElementById('volume-label').textContent = 'Average Volume (dBFS)';
        document.getElementById('pitch-label').textContent = 'Average Pitch Variance (Hz)';
    }
}

function initialiseControls({
    startBtn, stopBtn, pauseResumeBtn,
    transcriptBox, wpmValue, volumeValue, pitchValue }) {
    
        // Start Recording
    startBtn.addEventListener('click', function() {
        if (metricsMode === "live") {
            transcriptBox.textContent = "Recording already in progress.";
            return;
        }

        if (isPaused) {
            setIsPaused(false);
            pauseResumeBtn.textContent = "Pause";
        }

        setMetricsMode("live");
        setStartTime(Date.now());
        transcriptBox.textContent = "Recording started...";

        fetch('/start_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                transcriptBox.textContent = data.status;
                updateMetricsDisplay(metricsMode);
                // This is only used if we want to poll on intervals 
                if (!transcriptInterval && !metricsInterval) {
                    setTranscriptInterval(setInterval(() => pollTranscript(transcriptBox), 2000));
                    setMetricsInterval(setInterval(() => pollMetrics(wpmValue, volumeValue, pitchValue), 6000));
                }
            })
            .catch(error => {
                transcriptBox.textContent = 'Error starting recording.';
                console.error('Error starting recording:', error);
            });
    });

    // Stop Recording
    stopBtn.addEventListener('click', function() {
        if (metricsMode != "live") {
            transcriptBox.textContent = "Recording already stopped.";
            return;
        }
        setMetricsMode("average");
        resetCharts();
        fetch('/stop_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                transcriptBox.textContent = data.status;
                updateMetricsDisplay(metricsMode);

                if (transcriptInterval) {
                    clearInterval(transcriptInterval); // JavaScript function 
                    setTranscriptInterval(null);
                }
                
                if (metricsInterval) {
                    clearInterval(metricsInterval);
                    setMetricsInterval(null);
                }
                updateMetricsDisplay(metricsMode);

                 // Fetch the final transcript and metrics 
                fetch('/get_final_transcript')
                    .then(response => response.json())
                    .then(data => {
                        transcriptBox.textContent = data.transcript || 'No transcript available.';
                    })
                    .catch(error => {
                        transcriptBox.textContent = 'Error fetching final transcript.';
                        console.error('Error fetching final transcript:', error);
                    });
                
                fetch('/get_average_metrics')
                    .then(response => response.json())
                    .then(data => {
                        wpmValue.textContent = data.average_wpm !== undefined ? data.average_wpm.toFixed(2) : 'N/A';
                        volumeValue.textContent = data.average_volume !== undefined ? data.average_volume.toFixed(2) : 'N/A';
                        pitchValue.textContent = data.average_pitch !== undefined ? data.average_pitch.toFixed(2) : 'N/A';
                    })
                    .catch(error => {
                        wpmValue.textContent = 'N/A';
                        volumeValue.textContent = 'N/A';
                        pitchValue.textContent = 'N/A';
                        console.error('Error fetching average metrics:', error);
                    });
            })
            .catch(error => {
                transcriptBox.textContent = 'Error stopping recording.';
                console.error('Error stopping recording:', error);
            });
    });

    // Pause/Resume Recording
    pauseResumeBtn.addEventListener('click', function() {
        if (metricsMode !== "live") {
            // transcriptBox.textContent = "Cannot pause/resume when not recording.";
            return;
        }
        if (!isPaused) {
            fetch('/pause_recording', { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        setIsPaused(true);
                        pauseResumeBtn.textContent = "Resume";
                    } else {
                        alert("Failed to pause recording.");
                    }
                })
                .catch(error => {
                    alert("Error pausing recording.");
                });
        } else {
            fetch('/resume_recording', { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        setIsPaused(false);
                        pauseResumeBtn.textContent = "Pause";
                    } else {
                        alert("Failed to resume recording.");
                    }
                })
                .catch(error => {
                    alert("Error resuming recording.");
                });
        }
    });
}

export { initialiseControls, updateMetricsDisplay };