import { updateCharts } from './charts.js';
import { isPaused } from './state.js';

function pollTranscript(transcriptBox){
    fetch('/get_live_transcript')
        .then(response => response.json())
        .then(data => {
            transcriptBox.textContent = data.transcript; 
        });
}

function updateOutOfBounds(wpm, volume, pitch) {
    const wpmBox = document.getElementById('wpm-box');
    const volumeBox = document.getElementById('volume-box');
    const pitchBox = document.getElementById('pitch-box');

    // WPM Boundaries 
    if (wpm > 240 || wpm < 80){
        wpmBox.classList.add('out-of-bounds');
    } else {
        wpmBox.classList.remove('out-of-bounds');
    }

    // Volume Boundaries 
    if (volume < -40){
        volumeBox.classList.add('out-of-bounds');
    } else {
        volumeBox.classList.remove('out-of-bounds');
    }

    // Pitch Boundaries 
    if (pitch < 5){
        pitchBox.classList.add('out-of-bounds');
    } else {
        pitchBox.classList.remove('out-of-bounds');
    }
}

function pollMetrics(wpmValue, volumeValue, pitchValue) {
    fetch('/get_live_metrics')
        .then(response => response.json())
        .then(data => {    
            // Update charts with new data only if not paused
            if (!isPaused) {
                console.log('Received metrics:', data);

                // Update all metrics 
                wpmValue.textContent = data.wpm.toFixed(2)
                volumeValue.textContent = data.volume.toFixed(2)
                pitchValue.textContent = data.pitch.toFixed(2)

                // Update charts 
                updateCharts(data.wpm, data.volume, data.pitch);
                updateOutOfBounds(data.wpm, data.volume, data.pitch);
            } else {
                console.log('Recording is paused, skipping chart update');
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
}

export { pollTranscript, pollMetrics};