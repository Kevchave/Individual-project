// Dashboard Integration for AI Feedback
// Connects the AI feedback system to the dashboard UI

import { generateSimpleFeedback, simpleAIFeedback } from './simple-feedback.js';
import { getSessionMetrics, getSessionMetricsStats } from '../supabase-cllient.js';

// Global variables (will be set by dashboard.js)
let currentUser = null;
let userGoals = null;
let filteredSessions = [];

// Initialize AI feedback integration
export function initAIFeedback(user, goals) {
    currentUser = user;
    userGoals = goals;
    
    // Load API key from environment variables
    loadApiKey();
    
    console.log('AI Feedback initialized');
}

// Load API key from environment variables
function loadApiKey() {
    // Try to get from environment variable (for production)
    if (typeof process !== 'undefined' && process.env && process.env.GEMINI_API_KEY) {
        simpleAIFeedback.setApiKey(process.env.GEMINI_API_KEY);
        console.log('API key loaded from environment variable');
        return;
    }
    
    // For browser environment, try to get from window object or localStorage
    if (typeof window !== 'undefined') {
        // Try window object (if set by server)
        if (window.GEMINI_API_KEY) {
            simpleAIFeedback.setApiKey(window.GEMINI_API_KEY);
            console.log('API key loaded from window object');
            return;
        }
        
        // Try localStorage (for development)
        const storedKey = localStorage.getItem('GEMINI_API_KEY');
        if (storedKey) {
            simpleAIFeedback.setApiKey(storedKey);
            console.log('API key loaded from localStorage');
            return;
        }
    }
    
    console.warn('No Gemini API key found. AI feedback will not work.');
    console.warn('Set GEMINI_API_KEY environment variable or add to localStorage for development.');
}

// Update AI feedback based on current session selection
export async function updateAIFeedback() {
    if (filteredSessions.length === 0) {
        console.log('No sessions available for AI feedback');
        return;
    }

    const feedbackSection = document.querySelector('.feedback-section');
    if (!feedbackSection) {
        console.log('Feedback section not found');
        return;
    }

    try {
        // Show loading state
        showLoadingState(feedbackSection);

        // Determine if this is recent session or historical
        const isRecentSession = isMostRecentSession();
        
        // Get current session data
        const currentSession = filteredSessions[0];
        
        // Get session metrics
        const { data: metrics, error: metricsError } = await getSessionMetrics(currentSession.id);
        const { data: stats, error: statsError } = await getSessionMetricsStats(currentSession.id);
        
        if (metricsError || statsError) {
            throw new Error('Failed to retrieve session data');
        }

        // Generate AI feedback
        const result = await generateSimpleFeedback(
            currentSession, 
            { metrics, stats }, 
            userGoals, 
            isRecentSession
        );

        // Update UI with AI feedback
        updateFeedbackUI(feedbackSection, result.feedback);

    } catch (error) {
        console.error('Error updating AI feedback:', error);
        showFallbackFeedback(feedbackSection);
    }
}

// Check if current filter is "most recent session"
function isMostRecentSession() {
    const sessionFilter = document.getElementById('sessionFilter');
    return sessionFilter && sessionFilter.value === 'most_recent';
}

// Show loading state
function showLoadingState(feedbackSection) {
    const strengthsCard = feedbackSection.querySelector('.feedback-card.positive .feedback-content');
    const improvementsCard = feedbackSection.querySelector('.feedback-card.constructive .feedback-content');
    
    if (strengthsCard) {
        strengthsCard.innerHTML = '<p>🤖 AI is analyzing your session...</p>';
    }
    
    if (improvementsCard) {
        improvementsCard.innerHTML = '<p>Please wait...</p>';
    }
}

// Update the feedback UI with AI response
function updateFeedbackUI(feedbackSection, feedback) {
    const strengthsCard = feedbackSection.querySelector('.feedback-card.positive .feedback-content');
    const improvementsCard = feedbackSection.querySelector('.feedback-card.constructive .feedback-content');
    
    if (strengthsCard) {
        strengthsCard.innerHTML = `
            <p><strong> What's Working Well:</strong></p>
            <p>${feedback.positive_note}</p>
        `;
    }
    
    if (improvementsCard) {
        improvementsCard.innerHTML = `
            <p><strong> Focus on Improving:</strong></p>
            <p>${feedback.improvement_note}</p>
        `;
    }
}

// Show fallback feedback if AI fails
function showFallbackFeedback(feedbackSection) {
    const strengthsCard = feedbackSection.querySelector('.feedback-card.positive .feedback-content');
    const improvementsCard = feedbackSection.querySelector('.feedback-card.constructive .feedback-content');
    
    if (strengthsCard) {
        strengthsCard.innerHTML = '<p>You are doing really well with your pacing, keep it up!</p>';
    }
    
    if (improvementsCard) {
        improvementsCard.innerHTML = '<p>Try to maintain more consistent volume levels throughout your presentation.</p>';
    }
}

// Update sessions data (called from dashboard.js)
export function updateSessionsData(sessions) {
    filteredSessions = sessions;
}

// Check if AI feedback is configured
export function isAIConfigured() {
    return simpleAIFeedback.isConfigured();
} 