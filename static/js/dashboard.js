// Dashboard.js
// - loads and displays user data from Supabase
// - manages the dashboard UI 
// - calculates statistics from session data 
// - handles user interactions 

// Import functions from supabase-client.js
import { getCurrentUser, getUserSessions, getUserProfile, getUserGoals, getSessionMetrics, getSessionMetricsStats, getSessionMetricsForCharts } from './supabase-cllient.js';
import { initialiseCharts } from './charts.js';
import { currentTheme } from './theme.js';
import { wpmChart, volumeChart, pitchChart } from './state.js';

// Initialise global variables to store data    
let currentUser = null;     // Current logged in user
let userProfile = null;     // User profile data 
let userSessions = [];      // Array of user's sessions
let currentFilter = 'most_recent';  // Current session filter
let filteredSessions = [];  // Sessions based on current filter
let userGoals = null;       // User goals data 

// Initialize dashboard
async function initDashboard() {

    // CHeck if user is logged in
    currentUser = await getCurrentUser();
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }

        // Load data from Supabase (name, email, past sessions, goals)
        await Promise.all([
            loadUserProfile(),
            loadUserSessions(),
            loadUserGoals()
        ]);

    // Update UI with loaded data (username and stats)
    updateUserInfo();
    
    // Initialize charts
    initialiseCharts(currentTheme);
    
    // Apply initial filter (most recent session by default)
    applyFilter();
}

async function loadUserProfile() {

    // Get user profile data from Supabase
    const { data, error } = await getUserProfile();
    if (!error && data) {
        userProfile = data;
    }
}

function updateUserInfo() {
    // Updates UI to show users name, falling back to User if no name is found
    const fullName = userProfile?.full_name || currentUser.user_metadata?.full_name || '';
    const userName = fullName || currentUser.email?.split('@')[0] || 'User';
    const userInitial = userName.charAt(0).toUpperCase();
    
    document.getElementById('userName').textContent = userName;
    document.getElementById('userAvatar').textContent = userInitial;
}

// Fetch all sessions from the database and display them in the UI
async function loadUserSessions() {
    const { data, error } = await getUserSessions(100); // Load more sessions for filtering
    if (!error && data) {
        userSessions = data;
        applyFilter();
    }
}

// Load user goals from the database
async function loadUserGoals() {
    const { data, error } = await getUserGoals();
    if (!error && data) {
        userGoals = data;
        updateGoalsDisplay();
    }
}

// Apply the current filter and update the display
function applyFilter() {
    const filterValue = document.getElementById('sessionFilter').value;
    currentFilter = filterValue;
    
    if (filterValue === 'most_recent') {
        // Show only the most recent session
        filteredSessions = userSessions.slice(0, 1);
        displayMostRecentView();
    } else {
        // Show multiple sessions based on filter
        const sessionCount = filterValue === 'all' ? userSessions.length : parseInt(filterValue);
        filteredSessions = userSessions.slice(0, sessionCount);
        displayMultipleSessionsView();
    }
    
    // Update statistics, charts, and goals
    updateStatistics();
    updateCharts();
    updateGoalsDisplay();
}

// Display view for most recent session
function displayMostRecentView() {
    if (filteredSessions.length > 0) {
        displayRecentSession(filteredSessions[0]);
        // Charts will be updated by updateCharts() called from applyFilter()
    }
}

// Display view for multiple sessions
function displayMultipleSessionsView() {
    // Update section header
    const sectionHeader = document.querySelector('.section-header h2');
    if (sectionHeader) {
        const sessionCount = filteredSessions.length;
        sectionHeader.textContent = `Last ${sessionCount} Sessions`;
    }
    
    // Update chart title
    const chartTitle = document.querySelector('.section-subheader h3');
    if (chartTitle) {
        const sessionCount = filteredSessions.length;
        chartTitle.textContent = `Performance Over ${sessionCount} Sessions`;
    }
    
    // Update session date to show range
    const sessionDate = document.querySelector('.session-date');
    if (sessionDate && filteredSessions.length > 0) {
        const firstSession = filteredSessions[filteredSessions.length - 1]; // Oldest session
        const lastSession = filteredSessions[0]; // Newest session
        const firstDate = new Date(firstSession.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const lastDate = new Date(lastSession.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        sessionDate.textContent = `${firstDate} - ${lastDate}`;
    }
    
    // Update session title
    const sessionTitle = document.querySelector('.session-title h3');
    if (sessionTitle) {
        sessionTitle.textContent = 'Multiple Sessions Overview';
    }
    
    // Update session status
    const sessionStatus = document.querySelector('.session-status');
    if (sessionStatus) {
        sessionStatus.textContent = 'Completed';
        sessionStatus.className = 'session-status completed';
    }
    
    // Update duration to show total time
    const durationValue = document.querySelector('.duration-value');
    if (durationValue) {
        const totalDuration = filteredSessions.reduce((sum, session) => sum + (session.duration_seconds || 0), 0);
        durationValue.textContent = formatDuration(totalDuration);
    }
    
    // Update metrics to show averages
    updateAverageMetrics();
}

// Update metrics to show averages across multiple sessions
function updateAverageMetrics() {
    const metricValues = document.querySelectorAll('.metric-value');
    if (metricValues.length >= 3 && filteredSessions.length > 0) {
        // Calculate averages
        const avgWPM = Math.round(filteredSessions.reduce((sum, s) => sum + (s.average_wpm || 0), 0) / filteredSessions.length);
        const avgVolume = Math.round(filteredSessions.reduce((sum, s) => sum + (s.average_volume || 0), 0) / filteredSessions.length);
        const avgPitch = (filteredSessions.reduce((sum, s) => sum + (s.average_pitch || 0), 0) / filteredSessions.length).toFixed(2);
        
        metricValues[0].textContent = avgWPM;
        metricValues[1].textContent = avgVolume + ' dB';
        metricValues[2].textContent = avgPitch;
    }
    
    // Update percentages (placeholder for now)
    const percentages = document.querySelectorAll('.metric-percentage');
    if (percentages.length >= 3) {
        percentages[0].textContent = 'Avg';
        percentages[1].textContent = 'Avg';
        percentages[2].textContent = 'Avg';
    }
}

// Update charts based on current filter
function updateCharts() {
    if (currentFilter === 'most_recent') {
        // Load detailed graph data for most recent session
        loadRecentSessionGraphData();
    } else {
        // Display aggregated data for multiple sessions
        displayAggregatedCharts();
    }
}

// Display aggregated charts for multiple sessions
function displayAggregatedCharts() {
    if (filteredSessions.length === 0) return;
    
    // Prepare data for charts
    const sessionLabels = filteredSessions.map((session, index) => {
        const date = new Date(session.created_at);
        const sessionNumber = filteredSessions.length - index; // S1, S2, S3, etc.
        return `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} (S${sessionNumber})`;
    }).reverse(); // Show oldest to newest
    
    const wpmData = filteredSessions.map(session => session.average_wpm || 0).reverse();
    const volumeData = filteredSessions.map(session => session.average_volume || 0).reverse();
    const pitchData = filteredSessions.map(session => session.average_pitch || 0).reverse();
    
    // Update x-axis title for multiple sessions
    [wpmChart, volumeChart, pitchChart].forEach(chart => {
        if (chart && chart.options?.scales?.x?.title) {
            chart.options.scales.x.title.text = 'Date';
        }
    });
    
    // Update WPM chart
    if (wpmChart) {
        wpmChart.data.labels = sessionLabels;
        wpmChart.data.datasets[0].data = wpmData;
        wpmChart.update('none');
    }
    
    // Update Volume chart
    if (volumeChart) {
        volumeChart.data.labels = sessionLabels;
        volumeChart.data.datasets[0].data = volumeData;
        volumeChart.update('none');
    }
    
    // Update Pitch chart
    if (pitchChart) {
        pitchChart.data.labels = sessionLabels;
        pitchChart.data.datasets[0].data = pitchData;
        pitchChart.update('none');
    }
}



// Fetch graph data for the most recent session
async function loadRecentSessionGraphData() {
    try {
        const response = await fetch('/get_session_data');
        if (response.ok) {
            const sessionData = await response.json();
            if (sessionData && sessionData.graph_data) {
                displaySessionGraphs(sessionData.graph_data);
            } else {
                console.log('No detailed graph data available');
            }
        } else {
            console.log('Failed to fetch session data');
        }
    } catch (error) {
        console.log('No recent session graph data available:', error);
    }
}



// Display session graph data in charts
function displaySessionGraphs(graphData) {
    const { wpm_data, volume_data, pitch_data, timestamps } = graphData;
    const relSeconds = Array.isArray(timestamps) && timestamps.length > 0
        ? timestamps.map(t => Math.max(0, Math.round(t - timestamps[0])))
        : [];
    
    // Update WPM chart
    if (wpmChart && wpm_data && wpm_data.length > 0) {
        wpmChart.data.labels = relSeconds.map(s => `${s}s`);
        wpmChart.data.datasets[0].data = wpm_data;
        wpmChart.update('none');
    }
    
    // Update Volume chart
    if (volumeChart && volume_data && volume_data.length > 0) {
        volumeChart.data.labels = relSeconds.map(s => `${s}s`);
        volumeChart.data.datasets[0].data = volume_data;
        volumeChart.update('none');
    }
    
    // Update Pitch chart
    if (pitchChart && pitch_data && pitch_data.length > 0) {
        pitchChart.data.labels = relSeconds.map(s => `${s}s`);
        pitchChart.data.datasets[0].data = pitch_data;
        pitchChart.update('none');
    }
}

// Displays the most recent session in the UI
async function displayRecentSession(sessionData) {
    // Update session title and date
    const sessionTitle = document.querySelector('.session-title h3');
    const sessionDate = document.querySelector('.session-date');
    
    if (sessionTitle) {
        sessionTitle.textContent = 'Recent Lecture Session';
    }
    
    if (sessionDate) {
        const date = new Date(sessionData.created_at);
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long',   
            day: 'numeric',  
            hour: '2-digit', 
            minute: '2-digit'
        };
        sessionDate.textContent = date.toLocaleDateString('en-US', options);
    }

    // Update duration
    const durationValue = document.querySelector('.duration-value');
    if (durationValue) {
        durationValue.textContent = formatDuration(sessionData.duration_seconds || 0);
    }

    // Update metrics
    const metricValues = document.querySelectorAll('.metric-value');
    if (metricValues.length >= 3) {
        metricValues[0].textContent = Math.round(sessionData.average_wpm || 0);
        metricValues[1].textContent = Math.round(sessionData.average_volume || 0) + ' dB';
        metricValues[2].textContent = (sessionData.average_pitch || 0).toFixed(2);
    }

    // Load chart data from session_metrics table
    if (sessionData.id) {
        console.log('[DEBUG] Loading chart data for session:', sessionData.id);
        const { data: chartData, error } = await getSessionMetricsForCharts(sessionData.id);
        
        if (error) {
            console.error('[DEBUG] Error loading chart data:', error);
            displaySessionGraphs({ wpm_data: [], volume_data: [], pitch_data: [], timestamps: [] });
        } else if (chartData) {
            console.log('[DEBUG] Chart data loaded successfully:', chartData);
            displaySessionGraphs(chartData);
        } else {
            console.log('[DEBUG] No chart data available');
            displaySessionGraphs({ wpm_data: [], volume_data: [], pitch_data: [], timestamps: [] });
        }
    }

    // Calculate percentages based on historical averages
    const percentages = document.querySelectorAll('.metric-percentage');
    if (percentages.length >= 3 && userSessions.length > 1) {
        // Calculate historical averages (excluding current session)
        const historicalSessions = userSessions.slice(1); // Exclude most recent
        const avgHistoricalWPM = historicalSessions.reduce((sum, s) => sum + (s.average_wpm || 0), 0) / historicalSessions.length;
        const avgHistoricalVolume = historicalSessions.reduce((sum, s) => sum + (s.average_volume || 0), 0) / historicalSessions.length;
        const avgHistoricalPitch = historicalSessions.reduce((sum, s) => sum + (s.average_pitch || 0), 0) / historicalSessions.length;
        
        // Calculate percentage differences
        const currentWPM = sessionData.average_wpm || 0;
        const currentVolume = sessionData.average_volume || 0;
        const currentPitch = sessionData.average_pitch || 0;
        
        percentages[0].textContent = calculatePercentage(currentWPM, avgHistoricalWPM);
        percentages[1].textContent = calculatePercentage(currentVolume, avgHistoricalVolume);
        percentages[2].textContent = calculatePercentage(currentPitch, avgHistoricalPitch);
    } else {
        // No historical data yet
        if (percentages[0]) percentages[0].textContent = 'New';
        if (percentages[1]) percentages[1].textContent = 'New';
        if (percentages[2]) percentages[2].textContent = 'New';
    }
}

// Calculate and display statistics (total sessions, total time)
function updateStatistics() {
    if (filteredSessions.length === 0) return;

    const totalSessions = filteredSessions.length;
    const totalTime = filteredSessions.reduce((sum, s) => sum + (s.duration_seconds || 0), 0); // stored DB value (seconds)

    const totalSessionsEl = document.getElementById('totalSessions');
    const totalTimeEl = document.getElementById('totalTime');

    if (totalSessionsEl) totalSessionsEl.textContent = totalSessions;
    if (totalTimeEl) totalTimeEl.textContent = formatDuration(totalTime);
}

// Converts seconds into human-readable format like "1h30m" or "1m20s".
function formatDuration(seconds) {
    const total = Math.max(0, Math.round(seconds));
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const secs = total % 60;
    
    if (hours > 0) {
        return `${hours}h${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function calculatePercentage(current, historical) {
    if (historical === 0) return 'New';
    
    const percentage = ((current - historical) / historical) * 100;
    const sign = percentage >= 0 ? '+' : '';
    const rounded = Math.round(percentage);
    
    return `${sign}${rounded}%`;
}

// Apply color coding to percentage text based on progress
function applyPercentageColor(element, progress) {
    // Remove any existing color classes
    element.classList.remove('progress-excellent', 'progress-good', 'progress-warning', 'progress-poor');
    
    // Determine color based on percentage
    let colorClass;
    if (progress >= 90) { // 0-10% away from target
        colorClass = 'progress-excellent'; // Dark green
    } else if (progress >= 75) { // 11-25% away from target
        colorClass = 'progress-good'; // Light green
    } else if (progress >= 60) { // 26-40% away from target
        colorClass = 'progress-warning'; // Orange
    } else { // More than 40% away from target
        colorClass = 'progress-poor'; // Red
    }
    
    element.classList.add(colorClass);
}

// Update goals display based on current filter and session data
function updateGoalsDisplay() {
    if (!userGoals) return;

    // Get current metrics based on filter
    let currentWPM, currentVolume, currentPitch;
    
    if (currentFilter === 'most_recent' && filteredSessions.length > 0) {
        // Use most recent session metrics
        const recentSession = filteredSessions[0];
        currentWPM = recentSession.average_wpm || 0;
        currentVolume = recentSession.average_volume || 0;
        currentPitch = recentSession.average_pitch || 0;
    } else {
        // Use average of filtered sessions
        const avgWPM = filteredSessions.reduce((sum, s) => sum + (s.average_wpm || 0), 0) / filteredSessions.length;
        const avgVolume = filteredSessions.reduce((sum, s) => sum + (s.average_volume || 0), 0) / filteredSessions.length;
        const avgPitch = filteredSessions.reduce((sum, s) => sum + (s.average_pitch || 0), 0) / filteredSessions.length;
        
        currentWPM = avgWPM || 0;
        currentVolume = avgVolume || 0;
        currentPitch = avgPitch || 0;
    }

    // Update WPM goal
    if (userGoals.target_wpm) {
        const wpmProgress = (currentWPM / userGoals.target_wpm) * 100;
        const wpmTargetEl = document.querySelector('.goal-card:nth-child(1) .goal-target');
        const wpmProgressEl = document.querySelector('.goal-card:nth-child(1) .progress-fill');
        const wpmStatusEl = document.querySelector('.goal-card:nth-child(1) .goal-status');
        
        if (wpmTargetEl) wpmTargetEl.textContent = `${userGoals.target_wpm} WPM`;
        if (wpmProgressEl) wpmProgressEl.style.width = `${Math.min(wpmProgress, 100)}%`;
        if (wpmStatusEl) {
            const currentText = `Current: ${Math.round(currentWPM)} WPM`;
            const percentageText = wpmProgress >= 100 
                ? `${Math.round(wpmProgress - 100)}% over your target`
                : `${Math.round(100 - wpmProgress)}% to your target`;
            wpmStatusEl.innerHTML = `${currentText}<br><br><span class="percentage-text">${percentageText}</span>`;
            applyPercentageColor(wpmStatusEl.querySelector('.percentage-text'), wpmProgress);
        }
    }

    // Update Volume goal
    if (userGoals.target_volume) {
        // Volume calculation with absolute values: (|current| - |target|) / |current|
        const volumeProgress = ((Math.abs(currentVolume) - Math.abs(userGoals.target_volume)) / Math.abs(currentVolume)) * 100;
        const volumeTargetEl = document.querySelector('.goal-card:nth-child(2) .goal-target');
        const volumeProgressEl = document.querySelector('.goal-card:nth-child(2) .progress-fill');
        const volumeStatusEl = document.querySelector('.goal-card:nth-child(2) .goal-status');
        
        if (volumeTargetEl) volumeTargetEl.textContent = `${userGoals.target_volume} dB`;
        if (volumeProgressEl) volumeProgressEl.style.width = `${Math.min(Math.max(volumeProgress, 0), 100)}%`;
        if (volumeStatusEl) {
            const currentText = `Current: ${Math.round(currentVolume)} dB`;
            const percentageText = volumeProgress >= 100 
                ? `${Math.round(volumeProgress - 100)}% over your target`
                : `${Math.round(100 - volumeProgress)}% to your target`;
            volumeStatusEl.innerHTML = `${currentText}<br><br><span class="percentage-text">${percentageText}</span>`;
            applyPercentageColor(volumeStatusEl.querySelector('.percentage-text'), volumeProgress);
        }
    }

    // Update Pitch goal
    if (userGoals.target_pitch) {
        const pitchProgress = (currentPitch / userGoals.target_pitch) * 100;
        const pitchTargetEl = document.querySelector('.goal-card:nth-child(3) .goal-target');
        const pitchProgressEl = document.querySelector('.goal-card:nth-child(3) .progress-fill');
        const pitchStatusEl = document.querySelector('.goal-card:nth-child(3) .goal-status');
        
        if (pitchTargetEl) pitchTargetEl.textContent = `${userGoals.target_pitch} Hz`;
        if (pitchProgressEl) pitchProgressEl.style.width = `${Math.min(pitchProgress, 100)}%`;
        if (pitchStatusEl) {
            const currentText = `Current: ${Math.round(currentPitch)} Hz`;
            const percentageText = pitchProgress >= 100 
                ? `${Math.round(pitchProgress - 100)}% over your target`
                : `${Math.round(100 - pitchProgress)}% to your target`;
            pitchStatusEl.innerHTML = `${currentText}<br><br><span class="percentage-text">${percentageText}</span>`;
            applyPercentageColor(pitchStatusEl.querySelector('.percentage-text'), pitchProgress);
        }
    }
}



// Event Listeners - sets up all interactive features - chart switching.
function setupEventListeners() {
    // Session filter functionality
    const sessionFilter = document.getElementById('sessionFilter');
    if (sessionFilter) {
        sessionFilter.addEventListener('change', () => {
            applyFilter();
        });
    }

    // Chart controls functionality
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Get the chart type
            const chartType = btn.dataset.chart;
            
            // Show the selected chart canvas and hide the others
            const wpmCanvas = document.getElementById('wpmChart');
            const volumeCanvas = document.getElementById('volumeChart');
            const pitchCanvas = document.getElementById('pitchChart');
            
            if (wpmCanvas && volumeCanvas && pitchCanvas) {
                wpmCanvas.style.display = chartType === 'wpm' ? 'block' : 'none';
                volumeCanvas.style.display = chartType === 'volume' ? 'block' : 'none';
                pitchCanvas.style.display = chartType === 'pitch' ? 'block' : 'none';
            }
        });
    });

    // Add click handler for transcript download button (placeholder)
    const transcriptBtn = document.querySelector('.session-actions-section .btn');
    if (transcriptBtn) {
        transcriptBtn.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Transcript download feature coming soon!');
        });
    }
}

// Runs when page loads 
// - sets up event listeners, then starts dashboard.
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initDashboard();
}); 