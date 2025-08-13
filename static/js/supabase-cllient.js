// Download the Supabase JS library and provides access to createClient function 
// - this contains many predefined functions we use below to interact with the client
import { createClient } from 'https://cdn.skypack.dev/@supabase/supabase-js@2'

// Stores Supabase project's web address and access key
const SUPABASE_URL = 'https://henmmlvnilndbunlecnl.supabase.co'  
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhlbm1tbHZuaWxuZGJ1bmxlY25sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzNTM5MjUsImV4cCI6MjA2OTkyOTkyNX0.cHiSOjNaYAyjAXMgn_dZs-HQ_YV3WTbBM5BdMhsxWT0'  // Get from Supabase dashboard

// Create a client to interact with Supabase using createClient
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Authentication functions 
export async function signUp(email, password, metadata = {}) {
    try {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata
            }
        })
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function signIn(email, password) {
    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        })
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function signOut() {
    try {
        const { error } = await supabase.auth.signOut()
        return { error }
    } catch (err) {
        return { error: err }
    }
}

export async function getCurrentUser() {
    try {
        const { data: { user } } = await supabase.auth.getUser()
        return user
    } catch (err) {
        console.error('Error getting current user:', err)
        return null
    }
}

export async function getCurrentSession() {
    try {
        const { data: { session } } = await supabase.auth.getSession()
        return session
    } catch (err) {
        console.error('Error getting session:', err)
        return null
    }
}

// Database helper functions
export async function saveUserPreferences(preferences) {
    try {
        const user = await getCurrentUser()
        if (!user) throw new Error('Not authenticated')
        
        const { data, error } = await supabase
            .from('user_preferences')
            .upsert({
                user_id: user.id,
                ...preferences,
                updated_at: new Date().toISOString()
            }, {
                onConflict: 'user_id'  // Specify the conflict resolution column
            })
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function getUserPreferences() {
    try {
        const user = await getCurrentUser()
        if (!user) return { data: null, error: 'Not authenticated' }
        
        const { data, error } = await supabase
            .from('user_preferences')
            .select('*')              // Select all columns
            .eq('user_id', user.id)   // Filter by user_id
            .single()                 // Get a single row
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function getUserProfile() {
    try {
        const user = await getCurrentUser()
        if (!user) return { data: null, error: 'Not authenticated' }
        
        const { data, error } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', user.id)
            .single()
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function updateUserProfile(profileData) {
    try {
        const user = await getCurrentUser()
        if (!user) throw new Error('Not authenticated')
        
        const { data, error } = await supabase
            .from('profiles')
            .upsert({
                id: user.id,
                ...profileData,
                updated_at: new Date().toISOString()
            }, {
                onConflict: 'id'
            })
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function updateUserEmail(newEmail) {
    try {
        const { data, error } = await supabase.auth.updateUser({
            email: newEmail
        })
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function updateUserPassword(newPassword) {
    try {
        const { data, error } = await supabase.auth.updateUser({
            password: newPassword
        })
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

export async function getUserSessions(limit = 50) {
    try {
        const user = await getCurrentUser()
        if (!user) return { data: [], error: 'Not authenticated' }
        
        const { data, error } = await supabase
            .from('lecture_sessions')
            .select('*')
            .eq('user_id', user.id)
            .order('created_at', { ascending: false })
            .limit(limit)
        
        return { data: data || [], error }
    } catch (err) {
        return { data: [], error: err }
    }
}

// Save session data to database
export async function saveSessionData(sessionData) {
    try {
        const user = await getCurrentUser()
        if (!user) throw new Error('Not authenticated')
        
        // Simplified data structure - only essential fields
        const insertData = {
            user_id: user.id,
            title: 'Lecture Session', // Default title
            duration_seconds: Math.round(sessionData.total_duration), // Convert to integer
            total_words: sessionData.total_words,
            average_wpm: sessionData.average_metrics.wpm,
            average_volume: sessionData.average_metrics.volume,
            average_pitch: sessionData.average_metrics.pitch,
            transcript: sessionData.final_transcript,
            start_time: new Date(sessionData.session_start_time * 1000).toISOString(),
            end_time: new Date(sessionData.session_end_time * 1000).toISOString()
        };
        
        // console.log('[DEBUG] Inserting data:', JSON.stringify(insertData, null, 2));
        
        const { data, error } = await supabase
            .from('lecture_sessions')
            .insert(insertData)
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

// Get most recent session for dashboard
export async function getMostRecentSession() {
    try {
        const user = await getCurrentUser()
        if (!user) return { data: null, error: 'Not authenticated' }
        
        const { data, error } = await supabase
            .from('lecture_sessions')
            .select('*')
            .eq('user_id', user.id)
            .order('created_at', { ascending: false })
            .limit(1)
            .single()
        
        return { data, error }
    } catch (err) {
        return { data: null, error: err }
    }
}

// Calback function - only called when auth state changes
export function onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(callback)
}