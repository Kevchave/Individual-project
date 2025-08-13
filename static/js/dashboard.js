import { getCurrentUser, signOut, getUserSessions, getUserPreferences, saveUserPreferences, getUserProfile } from './supabase-cllient.js';

let currentUser = null;
let userProfile = null;
let userSessions = [];
let userPreferences = {};

// Initialize dashboard
async function initDashboard() {
    currentUser = await getCurrentUser();
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }

    // Load data
    await Promise.all([
        loadUserProfile(),
        loadUserSessions(),
        loadUserPreferences()
    ]);

    // Update user info (after loading profile)
    updateUserInfo();

    // Update statistics
    updateStatistics();
}

async function loadUserProfile() {
    const { data, error } = await getUserProfile();
    if (!error && data) {
        userProfile = data;
    }
}

function updateUserInfo() {
    // Use profile data from database, fallback to auth user data
    const fullName = userProfile?.full_name || currentUser.user_metadata?.full_name || '';
    const userName = fullName || currentUser.email?.split('@')[0] || 'User';
    const userInitial = userName.charAt(0).toUpperCase();
    
    document.getElementById('userName').textContent = userName;
    document.getElementById('userAvatar').textContent = userInitial;
}

async function loadUserSessions() {
    const { data, error } = await getUserSessions(10);
    if (!error && data) {
        userSessions = data;
        displaySessions();
    }
}

async function loadUserPreferences() {
    const { data, error } = await getUserPreferences();
    if (!error && data) {
        userPreferences = data;
        populateSettingsForm();
    }
}

function displaySessions() {
    const sessionsList = document.getElementById('sessionsList');
    const sessionsLoading = document.getElementById('sessionsLoading');
    const sessionsEmpty = document.getElementById('sessionsEmpty');

    if (!sessionsList || !sessionsLoading || !sessionsEmpty) return;

    sessionsLoading.style.display = 'none';

    if (userSessions.length === 0) {
        sessionsEmpty.style.display = 'block';
        return;
    }

    sessionsList.style.display = 'grid';
    sessionsList.innerHTML = userSessions.map(session => `
        <div class="session-card">
            <div class="session-header">
                <div>
                    <div class="session-title">Lecture Session</div>
                    <div class="session-date">${new Date(session.created_at).toLocaleDateString()}</div>
                </div>
            </div>
            <div class="session-metrics">
                <div class="session-metric">
                    <div class="session-metric-label">Duration</div>
                    <div class="session-metric-value">${formatDuration(session.duration || 0)}</div>
                </div>
                <div class="session-metric">
                    <div class="session-metric-label">Avg WPM</div>
                    <div class="session-metric-value">${session.avg_wpm || 0}</div>
                </div>
                <div class="session-metric">
                    <div class="session-metric-label">Avg Volume</div>
                    <div class="session-metric-value">${session.avg_volume || 0} dB</div>
                </div>
            </div>
            <div class="session-actions">
                <button class="btn btn-secondary" onclick="viewSessionDetails('${session.id}')">View Details</button>
            </div>
        </div>
    `).join('');
}

function updateStatistics() {
    if (userSessions.length === 0) return;

    const totalSessions = userSessions.length;
    const avgWPM = Math.round(userSessions.reduce((sum, s) => sum + (s.avg_wpm || 0), 0) / totalSessions);
    const totalTime = userSessions.reduce((sum, s) => sum + (s.duration || 0), 0);
    const bestSession = userSessions.reduce((best, current) => 
        (current.avg_wpm || 0) > (best.avg_wpm || 0) ? current : best
    );

    const totalSessionsEl = document.getElementById('totalSessions');
    const avgWPMEl = document.getElementById('avgWPM');
    const totalTimeEl = document.getElementById('totalTime');
    const bestSessionEl = document.getElementById('bestSession');

    if (totalSessionsEl) totalSessionsEl.textContent = totalSessions;
    if (avgWPMEl) avgWPMEl.textContent = avgWPM;
    if (totalTimeEl) totalTimeEl.textContent = formatDuration(totalTime);
    if (bestSessionEl) bestSessionEl.textContent = bestSession.avg_wpm || 0;
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

function populateSettingsForm() {
    const targetWPMEl = document.getElementById('targetWPM');
    const targetVolumeEl = document.getElementById('targetVolume');
    const preferredLayoutEl = document.getElementById('preferredLayout');
    const showMetricsEl = document.getElementById('showMetrics');

    if (targetWPMEl) targetWPMEl.value = userPreferences.target_wpm || 150;
    if (targetVolumeEl) targetVolumeEl.value = userPreferences.target_volume || -20;
    if (preferredLayoutEl) preferredLayoutEl.value = userPreferences.preferred_layout || 'default';
    if (showMetricsEl) showMetricsEl.value = userPreferences.show_metrics || 'all';
}

// Event Listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.dashboard-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.dashboard-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.dashboard-content').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            const contentId = tab.dataset.tab + 'Content';
            const contentEl = document.getElementById(contentId);
            if (contentEl) contentEl.classList.add('active');
        });
    });

    // Settings form
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const saveBtn = document.getElementById('saveSettings');
            
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.textContent = 'Saving...';
            }

            const preferences = {
                target_wpm: parseInt(document.getElementById('targetWPM')?.value || 150),
                target_volume: parseInt(document.getElementById('targetVolume')?.value || -20),
                preferred_layout: document.getElementById('preferredLayout')?.value || 'default',
                show_metrics: document.getElementById('showMetrics')?.value || 'all'
            };

            try {
                const { error } = await saveUserPreferences(preferences);
                if (!error) {
                    userPreferences = preferences;
                    alert('Settings saved successfully!');
                } else {
                    alert('Failed to save settings: ' + error.message);
                }
            } catch (err) {
                alert('An error occurred while saving settings');
            } finally {
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'Save Settings';
                }
            }
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
            
            // Update chart placeholder text (placeholder for real chart switching)
            const chartPlaceholder = document.querySelector('.chart-placeholder h4');
            const chartDescription = document.querySelector('.chart-placeholder p');
            
            if (chartPlaceholder && chartDescription) {
                switch(chartType) {
                    case 'wpm':
                        chartPlaceholder.textContent = 'Words Per Minute Over Time';
                        chartDescription.textContent = 'Real-time graph showing your speaking pace throughout the session';
                        break;
                    case 'volume':
                        chartPlaceholder.textContent = 'Volume Levels Over Time';
                        chartDescription.textContent = 'Real-time graph showing your volume variations during the session';
                        break;
                    case 'pitch':
                        chartPlaceholder.textContent = 'Pitch Variation Over Time';
                        chartDescription.textContent = 'Real-time graph showing your pitch patterns and intonation';
                        break;
                }
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

// Global function for session details (placeholder)
window.viewSessionDetails = function(sessionId) {
    alert('Session details feature coming soon!');
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initDashboard();
}); 