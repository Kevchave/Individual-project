// Shared state for the app

export let wpmChart = null;
export let volumeChart = null;
export let pitchChart = null;

export let wpmData = [];
export let volumeData = [];
export let pitchData = [];
export let timeLabels = [];

export let startTime = null;
export let metricsMode = "live";
export let transcriptInterval = null;
export let metricsInterval = null;
export let isPaused = false;

// Setter functions allow reassigning of these variables from other modules
export function setWpmChart(chart) { wpmChart = chart; }
export function setVolumeChart(chart) { volumeChart = chart; }
export function setPitchChart(chart) { pitchChart = chart; }
export function setStartTime(time) { startTime = time; }
export function setMetricsMode(mode) { metricsMode = mode; }
export function setTranscriptInterval(interval) { transcriptInterval = interval; }
export function setMetricsInterval(interval) { metricsInterval = interval; }
export function setIsPaused(paused) { isPaused = paused; }
