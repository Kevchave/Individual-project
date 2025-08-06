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
            .from('user_preferences') // Table name
            .upsert({                 // Insert or update
                user_id: user.id,
                ...preferences,
                updated_at: new Date().toISOString()
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

// Calback function - only called when auth state changes
export function onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(callback)
}