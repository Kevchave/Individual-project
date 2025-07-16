import { initialiseTheme, currentTheme } from './theme.js';
import { initialiseCharts } from './charts.js';
// import { pollTranscript, pollMetrics } from './polling.js';
import { initialiseControls } from './controls.js';

// Main entry point: orchestrate initialization and wiring

document.addEventListener('DOMContentLoaded', () => {
    // Query all needed DOM elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    const transcriptBox = document.getElementById('transcript-box');
    const wpmValue = document.getElementById('wpm-value');
    const volumeValue = document.getElementById('volume-value');
    const pitchValue = document.getElementById('pitch-value');

    // Initialize theme and charts
    initialiseTheme();
    initialiseCharts(currentTheme);

    // Set up controls (event listeners and control logic)
    initialiseControls({
        startBtn,
        stopBtn,
        pauseResumeBtn,
        transcriptBox,
        wpmValue,
        volumeValue,
        pitchValue,
    });
});