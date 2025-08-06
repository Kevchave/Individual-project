// Main Application Controller
import { getCurrentUser } from './supabase-cllient.js';
import { AuthManager } from './auth.js';
import { RecordingManager } from './recording.js';

export class AppController {
    constructor() {
        this.currentUser = null;
        this.authManager = new AuthManager();
        this.recordingManager = new RecordingManager();
    }

    async init() {
        this.currentUser = await getCurrentUser();
        
        if (this.currentUser) {
            // User is logged in
            this.showRecordingInterface();
        } else {
            // User is not logged in
            this.showAuthInterface();
        }
    }

    showAuthInterface() {
        document.getElementById('authSection').style.display = 'block';
        document.getElementById('mainContent').style.display = 'none';
        
        // Set up auth callbacks
        this.authManager.onLogin = () => this.handleLogin();
        this.authManager.onSignup = () => this.handleSignup();
        
        // Initialize auth manager
        this.authManager.init();
    }

    async showRecordingInterface() {
        document.getElementById('authSection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        
        // Initialize recording manager
        await this.recordingManager.init(this.currentUser);
    }

    async handleLogin() {
        this.currentUser = await getCurrentUser();
        if (this.currentUser) {
            await this.showRecordingInterface();
        }
    }

    handleSignup() {
        // Handle signup success (could show success message or auto-login)
        console.log('Signup successful');
    }
}

// Initialize the app when the script loads
const app = new AppController();
app.init(); 