// Main Application Controller
import { getCurrentUser } from './supabase-cllient.js';
import { AuthManager } from './auth.js';
import { RecordingManager } from './recording.js';

// Navigation Manager
class NavigationManager {
    constructor() {
        this.currentPage = 'home';
    }

    init() {
        this.setupNavigation();
        this.updateActiveState();
    }

    setupNavigation() {
        // Home button
        const homeBtn = document.getElementById('homeBtn');
        if (homeBtn) {
            homeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('home');
            });
        }

        // Dashboard button - let it use normal browser navigation
        const dashboardBtn = document.getElementById('dashboardBtn');
        if (dashboardBtn) {
            dashboardBtn.addEventListener('click', () => {
                // Remove preventDefault to allow normal navigation
                this.currentPage = 'dashboard';
                this.updateActiveState();
            });
        }
    }

    navigateTo(page) {
        this.currentPage = page;
        this.updateActiveState();
        
        if (page === 'home') {
            // Show recording interface - user is already authenticated
            document.getElementById('authSection').style.display = 'none';
            document.getElementById('mainContent').style.display = 'block';
        }
    }

    updateActiveState() {
        // Remove active class from all navigation buttons
        const navButtons = document.querySelectorAll('.header .btn');
        navButtons.forEach(btn => btn.classList.remove('active'));

        // Add active class to current page button
        if (this.currentPage === 'home') {
            const homeBtn = document.getElementById('homeBtn');
            if (homeBtn) homeBtn.classList.add('active');
        } else if (this.currentPage === 'dashboard') {
            const dashboardBtn = document.getElementById('dashboardBtn');
            if (dashboardBtn) dashboardBtn.classList.add('active');
        }
    }
}

export class AppController {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.authManager = new AuthManager();
        this.recordingManager = new RecordingManager();
        this.navigationManager = new NavigationManager();
    }

    async init() {
        // Initialize navigation manager
        this.navigationManager.init();
        
        // Check if we're on the dashboard page
        if (window.location.pathname === '/dashboard') {
            this.navigationManager.currentPage = 'dashboard';
            this.navigationManager.updateActiveState();
        }
        
        // Check authentication state
        await this.checkAuthState();
    }

    async checkAuthState() {
        this.currentUser = await getCurrentUser();
        this.isAuthenticated = !!this.currentUser;
        
        if (this.isAuthenticated) {
            // User is logged in
            this.showRecordingInterface();
        } else {
            // User is not logged in
            this.showAuthInterface();
        }
    }

    showAuthInterface() {
        // Show auth interface for non-authenticated users
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
        
        // Set navigation to home page
        this.navigationManager.navigateTo('home');
        
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