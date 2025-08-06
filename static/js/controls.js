import { initialiseCharts, resetCharts } from './charts.js';
import { pollTranscript, pollMetrics, resetMetricColors } from './polling.js';
import { 
    startTime, setStartTime, 
    metricsMode, setMetricsMode, 
    transcriptInterval, setTranscriptInterval, 
    metricsInterval, setMetricsInterval, 
    isPaused, setIsPaused 
} from './state.js';

// Button state management functions
function updateButtonStates(isRecording, isPaused) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (isRecording) {
        // Recording is active
        startBtn.disabled = true;
        stopBtn.disabled = false;
        pauseResumeBtn.disabled = false;
        resetBtn.disabled = true;
        
        // Update pause/resume button text
        pauseResumeBtn.textContent = isPaused ? "Resume" : "Pause";
    } else {
        // Not recording
        startBtn.disabled = false;
        stopBtn.disabled = true;
        pauseResumeBtn.disabled = true;
        resetBtn.disabled = false;
        
        // Reset pause/resume button text
        pauseResumeBtn.textContent = "Pause";
    }
}

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
    startBtn, stopBtn, pauseResumeBtn, resetBtn,
    transcriptBox, wpmValue, volumeValue, pitchValue }) {
    
    // Initialize button states (not recording)
    updateButtonStates(false, false);
    
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
                updateButtonStates(true, false); // Enable recording buttons
                resetMetricColors(); // Reset colors for new recording session
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
        // Note: Removed resetCharts() call - graphs will be preserved
        fetch('/stop_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                transcriptBox.textContent = data.status;
                updateMetricsDisplay(metricsMode);
                updateButtonStates(false, false); // Disable recording buttons

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
                        updateButtonStates(true, true); // Update button states for paused state
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
                        updateButtonStates(true, false); // Update button states for resumed state
                    } else {
                        alert("Failed to resume recording.");
                    }
                })
                .catch(error => {
                    alert("Error resuming recording.");
                });
        }
    });

    // Reset Button - clears graphs and transcript, only works when not recording
    resetBtn.addEventListener('click', function() {
        if (metricsMode === "live") {
            transcriptBox.textContent = "Cannot reset while recording is in progress.";
            return;
        }
        
        // Clear the transcript
        transcriptBox.textContent = "Live transcript will appear here...";
        
        // Reset the charts
        resetCharts();
        
        // Reset metric box colors
        resetMetricColors();
        
        // Reset metrics display to live mode labels
        document.getElementById('wpm-label').textContent = 'Words per Minute';
        document.getElementById('volume-label').textContent = 'Volume (dBFS)';
        document.getElementById('pitch-label').textContent = 'Pitch Variance (Hz)';
        document.getElementById('wpm-value').textContent = '0';
        document.getElementById('volume-value').textContent = '0';
        document.getElementById('pitch-value').textContent = '0';
        
        console.log("Reset completed - graphs, transcript, and metric colors cleared");
    });
}

export { initialiseControls, updateMetricsDisplay };