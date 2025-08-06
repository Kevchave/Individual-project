// Recording Interface Module
import { signOut, getUserPreferences } from './supabase-cllient.js';
import { initializeRecordingFunctionality } from './main.js';

export class RecordingManager {
    constructor() {
        this.currentUser = null;
        this.userPreferences = {};
    }

    async init(currentUser) {
        this.currentUser = currentUser;
        this.updateUserInfo();
        await this.loadUserPreferences();
        this.initializeUI();
        
        // Initialize recording functionality after UI is ready
        setTimeout(() => {
            initializeRecordingFunctionality();
        }, 100);
    }

    updateUserInfo() {
        const userName = this.currentUser.user_metadata?.full_name || this.currentUser.email?.split('@')[0] || 'User';
        const userInitial = userName.charAt(0).toUpperCase();
        
        document.getElementById('userAvatar').textContent = userInitial;
        document.getElementById('userGreeting').textContent = `Welcome back, ${userName}!`;
    }

    async loadUserPreferences() {
        const { data, error } = await getUserPreferences();
        if (!error && data) {
            this.userPreferences = data;
            this.applyUserPreferences();
        }
    }

    applyUserPreferences() {
        // Apply layout preferences
        const layout = this.userPreferences.preferred_layout || 'default';
        if (layout === 'compact') {
            // Collapse some sections by default
            this.toggleSection('transcriptContent', false);
            this.toggleSection('graphsContent', false);
        }
        
        // Apply metrics display preferences
        const showMetrics = this.userPreferences.show_metrics || 'all';
        if (showMetrics === 'none') {
            this.toggleSection('metricsContent', false);
        }
    }

    initializeUI() {
        // Collapsible sections
        this.setupCollapsible('controlsToggle', 'controlsContent');
        this.setupCollapsible('transcriptToggle', 'transcriptContent');
        this.setupCollapsible('metricsToggle', 'metricsContent');
        this.setupCollapsible('graphsToggle', 'graphsContent');

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await signOut();
            window.location.reload();
        });
    }

    setupCollapsible(toggleId, contentId) {
        const toggle = document.getElementById(toggleId);
        const content = document.getElementById(contentId);
        
        toggle.addEventListener('click', () => {
            const isCollapsed = content.classList.contains('collapsed');
            this.toggleSection(contentId, isCollapsed);
            toggle.textContent = isCollapsed ? '−' : '+';
        });
    }

    toggleSection(contentId, show) {
        const content = document.getElementById(contentId);
        if (show) {
            content.classList.remove('collapsed');
        } else {
            content.classList.add('collapsed');
        }
    }
} 