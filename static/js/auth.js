// Authentication Module
import { signIn, signUp } from './supabase-cllient.js';

export class AuthManager {
    constructor() {
        this.onLogin = null;
        this.onSignup = null;
    }

    init() {
        this.setupTabSwitching();
        this.setupLoginForm();
        this.setupSignupForm();
    }

    setupTabSwitching() {
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and forms
                document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding form
                tab.classList.add('active');
                const formId = tab.dataset.tab + 'Form';
                document.getElementById(formId).classList.add('active');
                
                // Clear error messages
                document.querySelectorAll('.error-message, .success-message').forEach(msg => {
                    msg.style.display = 'none';
                    msg.textContent = '';
                });
            });
        });
    }

    setupLoginForm() {
        const form = document.getElementById('loginForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const loginBtn = document.getElementById('loginBtn');
            const errorDiv = document.getElementById('loginError');

            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            errorDiv.style.display = 'none';

            try {
                const { data, error } = await signIn(email, password);
                
                if (error) {
                    errorDiv.textContent = error.message || 'Login failed';
                    errorDiv.style.display = 'block';
                } else {
                    // Call the login callback
                    if (this.onLogin) {
                        this.onLogin();
                    }
                }
            } catch (err) {
                errorDiv.textContent = 'An unexpected error occurred';
                errorDiv.style.display = 'block';
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }
        });
    }

    setupSignupForm() {
        const form = document.getElementById('signupForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('signupName').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const confirmPassword = document.getElementById('signupConfirmPassword').value;
            const signupBtn = document.getElementById('signupBtn');
            const errorDiv = document.getElementById('signupError');
            const successDiv = document.getElementById('signupSuccess');

            // Validate passwords match
            if (password !== confirmPassword) {
                errorDiv.textContent = 'Passwords do not match';
                errorDiv.style.display = 'block';
                return;
            }

            signupBtn.disabled = true;
            signupBtn.textContent = 'Creating account...';
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            try {
                const { data, error } = await signUp(email, password, { full_name: name });
                
                if (error) {
                    errorDiv.textContent = error.message || 'Sign up failed';
                    errorDiv.style.display = 'block';
                } else {
                    successDiv.textContent = 'Account created successfully! Please check your email to verify your account.';
                    successDiv.style.display = 'block';
                    form.reset();
                    
                    // Call the signup callback
                    if (this.onSignup) {
                        this.onSignup();
                    }
                }
            } catch (err) {
                errorDiv.textContent = 'An unexpected error occurred';
                errorDiv.style.display = 'block';
            } finally {
                signupBtn.disabled = false;
                signupBtn.textContent = 'Sign Up';
            }
        });
    }
} 