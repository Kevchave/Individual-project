import { initialiseTheme, currentTheme } from './theme.js';
import { initialiseCharts } from './charts.js';
// import { pollTranscript, pollMetrics } from './polling.js';
import { initialiseControls } from './controls.js';

// Global variable to track if recording functionality is initialized
let recordingInitialized = false;

// Function to initialize recording functionality
export function initializeRecordingFunctionality() {
    if (recordingInitialized) return; // Prevent double initialization
    
    // Query all needed DOM elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const transcriptBox = document.getElementById('transcript-box');
    const wpmValue = document.getElementById('wpm-value');
    const volumeValue = document.getElementById('volume-value');
    const pitchValue = document.getElementById('pitch-value');

    // Check if all elements exist (recording interface is visible)
    if (!startBtn || !stopBtn || !transcriptBox) {
        console.log('Recording interface not ready yet');
        return;
    }

    // Initialize theme and charts
    initialiseTheme();
    initialiseCharts(currentTheme);

    // Set up controls (event listeners and control logic)
    initialiseControls({
        startBtn,
        stopBtn,
        pauseResumeBtn,
        resetBtn,
        transcriptBox,
        wpmValue,
        volumeValue,
        pitchValue,
    });

    recordingInitialized = true;
    console.log('Recording functionality initialized');
}

// Initialize theme immediately (this can be done right away)
document.addEventListener('DOMContentLoaded', () => {
    initialiseTheme();
});