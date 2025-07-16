import { updateCharts } from './charts.js';
import { isPaused } from './state.js';

function pollTranscript(transcriptBox){
    fetch('/get_live_transcript')
        .then(response => response.json())
        .then(data => {
            transcriptBox.textContent = data.transcript; 
        });
}

function pollMetrics(wpmValue, volumeValue, pitchValue) {
    fetch('/get_live_metrics')
        .then(response => response.json())
        .then(data => {    
            // Update charts with new data only if not paused
            if (!isPaused) {
                console.log('Received metrics:', data);
                wpmValue.textContent = data.wpm.toFixed(2)
                volumeValue.textContent = data.volume.toFixed(2)
                pitchValue.textContent = data.pitch.toFixed(2)
                updateCharts(data.wpm, data.volume, data.pitch);
            } else {
                console.log('Recording is paused, skipping chart update');
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
}

export { pollTranscript, pollMetrics};