// This ensures the JS code only runs once the HTML is fully loaded 
document.addEventListener('DOMContentLoaded', function(){
    // Get references to the HTML elements 
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const transcriptBox = document.getElementById('transcript-box');
    const wpmValue = document.getElementById('wpm-value');
    const volumeValue = document.getElementById('volume-value');
    const pitchValue = document.getElementById('pitch-value');

    let metricsMode = "live"
    let transcriptInterval = null;
    let metricsInterval = null;
    let isPaused = false;

    function pollTranscript(){
        fetch('/get_live_transcript')
        .then(response => response.json())
        .then(data => {
            transcriptBox.textContent = data.transcript; 
        });
    }

    function pollMetrics() {
        fetch('/get_live_metrics')
        .then(response => response.json())
        .then(data => {
            wpmValue.textContent = data.wpm.toFixed(2)
            volumeValue.textContent = data.volume.toFixed(2)
            pitchValue.textContent = data.pitch.toFixed(2)
        });
    }

    function togglePauseResume() {
        const btn = document.getElementById('pauseResumeBtn');
        if (!isPaused) {
            pauseRecording();
        } else {
            resumeRecording(); 
        }
    }

    function updateMetricsDisplay() {
        if (metricsMode === "live") {
            // Update the labels
            document.getElementById('wpm-label').textContent = 'Words per Minute';
            document.getElementById('volume-label').textContent = 'Volume (dBFS)';
            document.getElementById('pitch-label').textContent = 'Pitch Variance (Hz)';
        } else {
            // Update the labels
            document.getElementById('wpm-label').textContent = 'Average Words per Minute';
            document.getElementById('volume-label').textContent = 'Average Volume (dBFS)';
            document.getElementById('pitch-label').textContent = 'Average Pitch Variance (Hz)';
        }
    }

    function pauseRecording(){
        fetch('/pause_recording', {method: 'POST'})
        .then(response => {
            if (response.ok) {
                isPaused = true; 
                document.getElementById('pauseResumeBtn').textContent = "Resume";
            } else {
                alert ("Failed to pause recording.");
            }
        })
        .catch(error => {
            console.error("Error pausing:", error);
            alert("Error pausing recording.");
        });
    }

    function resumeRecording(){
        fetch('/resume_recording', {method: 'POST'})
        .then(response => {
            if (response.ok) {
                isPaused = false; 
                document.getElementById('pauseResumeBtn').textContent = "Pause"
            } else {
                alert("Failed to resume recording.");
            }
        })
        .catch(error => {
            console.error("Error resuming:", error);
            alert("Error resuming recording.");
        });
    }

    // Add a click event listener to the Start Recording button 
    // - structure wise, the function can be deigined separately for clarity and modularity
    startBtn.addEventListener('click', function(){
        metricsMode = "live"
        updateMetricsDisplay();

        // Sends a POST request to Flask backend after a click to /start_recording
        // - use fetch to communicate with the Flask backend 
        // - method can be GET, POST, PUT, DELETE, etc. 
    
        fetch('/start_recording', {method: 'POST'})

        // Wait for Flask response and parse it as JSON 
        .then(response => response.json())

        // Update the transcript box with the status from the Flask response 
        .then(data => {
            transcriptBox.textContent = data.status;
            if (!transcriptInterval && !metricsInterval) {
                // Poll for updates every 3 seconds 
                transcriptInterval = setInterval(pollTranscript, 1500);
                metricsInterval = setInterval(pollMetrics, 6000);
            }
        })

        // If there's an error, update the transcript box with an error message 
        .catch(error => {transcriptBox.textContent = 'Error starting recording.';
            console.error('Error starting recording:', error);
        });
    });

    if (stopBtn) {
        stopBtn.addEventListener('click', function(){
            metricsMode = "average"
            updateMetricsDisplay();

            fetch('/stop_recording', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                transcriptBox.textContent = data.status;
                if (transcriptInterval) {
                    clearInterval(transcriptInterval);
                    transcriptInterval = null;
                }
                if (metricsInterval) {
                    clearInterval(metricsInterval);
                    metricsInterval = null;
                }
                // Fetch the final transcript and metrics 
                fetch('/get_final_transcript')
                .then(response => response.json())
                .then(data => {
                    transcriptBox.textContent = data.transcript; 
                });

                fetch('/get_average_metrics')
                .then(response => response.json())
                .then(data => {
                    // Update the values 
                    wpmValue.textContent = data.average_wpm.toFixed(2);
                    volumeValue.textContent = data.average_volume.toFixed(2);
                    pitchValue.textContent = data.average_pitch.toFixed(2);
                });
            })
            .catch(error => {
                transcriptBox.textContent = 'Error stopping recording.';
                console.error('Error stopping recording:', error);
            });
        });
    }

    document.getElementById('pauseResumeBtn').addEventListener('click', togglePauseResume);

    // Maybe add a non existent route error handling 
    // If JS requests non-existent route
    // fetch('/nonexistent_route')
    // .then(response => {
    // if (!response.ok) {
    //     console.log('Error:', response.status); // 404
    // }
    // });
});
