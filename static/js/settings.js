// Settings Page Module
import { getCurrentUser, getUserPreferences, saveUserPreferences, getUserProfile, updateUserProfile, updateUserEmail, updateUserPassword, signOut, getUserGoals, saveUserGoals } from './supabase-cllient.js';

class SettingsManager {
    constructor() {
        this.currentUser = null;
        this.userPreferences = {};
        this.originalSettings = {};
    }

    async init() {
        this.currentUser = await getCurrentUser();
        
        if (!this.currentUser) {
            window.location.href = '/';
            return;
        }

        await this.loadUserInfo();
        await this.loadUserPreferences();
        await this.loadUserGoals();
        this.saveOriginalSettings();
        this.setupEventListeners();
    }

    async loadUserInfo() {
        // Load profile data from database
        const { data: profile, error } = await getUserProfile();
        
        if (error) {
            console.error('Error loading profile:', error);
        }

        // Use profile data or fallback to auth user data
        const fullName = profile?.full_name || this.currentUser.user_metadata?.full_name || '';
        const email = this.currentUser.email;

        // Update display
        const userInitial = fullName ? fullName.charAt(0).toUpperCase() : email.charAt(0).toUpperCase();
        document.getElementById('userAvatar').textContent = userInitial;
        document.getElementById('userName').textContent = fullName || email.split('@')[0];
        document.getElementById('userEmail').textContent = email;
        
        // Populate form fields
        document.getElementById('fullName').value = fullName;
        document.getElementById('email').value = email;
    }

    async loadUserPreferences() {
        const { data, error } = await getUserPreferences();
        if (!error && data) {
            this.userPreferences = data;
            this.applyUserPreferences();
        }
        this.saveOriginalSettings();
    }

    applyUserPreferences() {
        // Simple layout preferences
        document.getElementById('displayTranscript').checked = this.userPreferences.display_transcript !== false;
        document.getElementById('displayMetrics').checked = this.userPreferences.display_metrics !== false;
        document.getElementById('displayGraphs').checked = this.userPreferences.display_graphs !== false;

    }

    async loadUserGoals() {
        try {
            const { data: goals, error } = await getUserGoals();
            
            if (error) {
                console.error('Error loading goals:', error);
                return;
            }

            if (goals) {
                const wpmGoalInput = document.getElementById('wpmGoal');
                const volumeGoalInput = document.getElementById('volumeGoal');
                const pitchGoalInput = document.getElementById('pitchGoal');
                
                if (wpmGoalInput) {
                    wpmGoalInput.value = goals.target_wpm || '';
                }
                
                if (volumeGoalInput) {
                    volumeGoalInput.value = goals.target_volume || '';
                }
                
                if (pitchGoalInput) {
                    pitchGoalInput.value = goals.target_pitch || '';
                }
            }
        } catch (err) {
            console.error('Unexpected error loading goals:', err);
        }
    }

    saveOriginalSettings() {
        this.originalSettings = {
            fullName: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            newPassword: document.getElementById('newPassword').value,
            displayTranscript: document.getElementById('displayTranscript').checked,
            displayMetrics: document.getElementById('displayMetrics').checked,
            displayGraphs: document.getElementById('displayGraphs').checked,
            wpmGoal: document.getElementById('wpmGoal')?.value || '',
            volumeGoal: document.getElementById('volumeGoal')?.value || '',
            pitchGoal: document.getElementById('pitchGoal')?.value || '',
        };
    }

    setupEventListeners() {
        // Save button
        document.getElementById('saveBtn').addEventListener('click', () => {
            this.saveSettings();
        });

        // Cancel button
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.cancelChanges();
        });

        // Logout button (if exists on dashboard)
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await signOut();
                window.location.reload();
            });
        }
    }

    async saveSettings() {
        console.log('Save button clicked - starting save process');
        
        const saveBtn = document.getElementById('saveBtn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;

        try {
            // Collect profile data
            const profileData = {
                full_name: document.getElementById('fullName').value
            };

            // Collect layout preferences
            const layoutSettings = {
                display_transcript: document.getElementById('displayTranscript').checked,
                display_metrics: document.getElementById('displayMetrics').checked,
                display_graphs: document.getElementById('displayGraphs').checked,
            };

            console.log('Profile data to save:', profileData);
            console.log('Layout settings to save:', layoutSettings);

            // Save profile data
            const { data: profileResult, error: profileError } = await updateUserProfile(profileData);
            if (profileError) {
                console.error('Profile update error:', profileError);
                alert('Error updating profile: ' + profileError.message);
                return;
            }

            // Save layout preferences
            const { data: layoutResult, error: layoutError } = await saveUserPreferences(layoutSettings);
            if (layoutError) {
                console.error('Layout settings error:', layoutError);
                alert('Error saving layout settings: ' + layoutError.message);
                return;
            }

            // Handle email change if different
            const newEmail = document.getElementById('email').value;
            if (newEmail !== this.currentUser.email) {
                const { error: emailError } = await updateUserEmail(newEmail);
                if (emailError) {
                    console.error('Email update error:', emailError);
                    alert('Error updating email: ' + emailError.message);
                    return;
                }
            }

            // Handle password change if provided
            const newPassword = document.getElementById('newPassword').value;
            if (newPassword.trim() !== '') {
                const { error: passwordError } = await updateUserPassword(newPassword);
                if (passwordError) {
                    console.error('Password update error:', passwordError);
                    alert('Error updating password: ' + passwordError.message);
                    return;
                }
            }

            // Save goals
            const goalsData = {
                target_wpm: parseInt(document.getElementById('wpmGoal').value) || null,
                target_volume: parseInt(document.getElementById('volumeGoal').value) || null,
                target_pitch: parseInt(document.getElementById('pitchGoal').value) || null,
            };
            
            const { data: goalsResult, error: goalsError } = await saveUserGoals(goalsData);
            if (goalsError) {
                console.error('Goals save error:', goalsError);
                alert('Error saving goals: ' + goalsError.message);
                return;
            }

            console.log('All settings saved successfully!');
            alert('Settings saved successfully!');
            this.saveOriginalSettings();
            
            // Reload user info to reflect changes
            await this.loadUserInfo();
            
        } catch (err) {
            console.error('Unexpected error saving settings:', err);
            alert('An unexpected error occurred while saving settings.');
        } finally {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }
    }

    cancelChanges() {
        // Restore original settings
        document.getElementById('fullName').value = this.originalSettings.fullName;
        document.getElementById('email').value = this.originalSettings.email;
        document.getElementById('newPassword').value = this.originalSettings.newPassword;
        document.getElementById('displayTranscript').checked = this.originalSettings.displayTranscript;
        document.getElementById('displayMetrics').checked = this.originalSettings.displayMetrics;
        document.getElementById('displayGraphs').checked = this.originalSettings.displayGraphs;
        
        // Restore goals
        if (document.getElementById('wpmGoal')) {
            document.getElementById('wpmGoal').value = this.originalSettings.wpmGoal;
        }
        if (document.getElementById('volumeGoal')) {
            document.getElementById('volumeGoal').value = this.originalSettings.volumeGoal;
        }
        if (document.getElementById('pitchGoal')) {
            document.getElementById('pitchGoal').value = this.originalSettings.pitchGoal;
        }
    }
}

// Initialize settings when the script loads
const settingsManager = new SettingsManager();
settingsManager.init();