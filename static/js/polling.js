import { updateCharts } from './charts.js';
import { isPaused } from './state.js';

function pollTranscript(transcriptBox){
    fetch('/get_live_transcript')
        .then(response => response.json())
        .then(data => {
            transcriptBox.textContent = data.transcript; 
        });
}

function updateOutOfBounds(wpm, volume, pitch, dataPointsCount) {
    const wpmBox = document.getElementById('wpm-box');
    const volumeBox = document.getElementById('volume-box');
    const pitchBox = document.getElementById('pitch-box');

    // Skip bounds checking if we don't have enough data points (less than 5)
    if (dataPointsCount < 5) {
        wpmBox.classList.remove('out-of-bounds');
        volumeBox.classList.remove('out-of-bounds');
        pitchBox.classList.remove('out-of-bounds');
        return;
    }

    // WPM Boundaries 
    if (wpm > 200 || wpm < 100) {
        wpmBox.classList.add('out-of-bounds');
    } else {
        wpmBox.classList.remove('out-of-bounds');
    }

    // Volume Boundaries  
    if (volume < -50) {
        volumeBox.classList.add('out-of-bounds');
    } else {
        volumeBox.classList.remove('out-of-bounds');
    }

    // Pitch Boundaries
    if (pitch < 10) {
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
                updateOutOfBounds(data.wpm, data.volume, data.pitch, data.sample_count || 0);
            } else {
                console.log('Recording is paused, skipping chart update');
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
}

export { pollTranscript, pollMetrics };