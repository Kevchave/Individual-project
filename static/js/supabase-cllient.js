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
    console.log('[DEBUG] saveSessionData called with:', sessionData);
    try {
        const user = await getCurrentUser()
        if (!user) throw new Error('Not authenticated')
        
        // Simplified data structure - only essential fields
        const wallClockSeconds = Math.round(
            (sessionData?.graph_data?.session_duration) ??
            ((sessionData?.session_end_time && sessionData?.session_start_time)
                ? (sessionData.session_end_time - sessionData.session_start_time)
                : sessionData.total_duration)
        );

        const insertData = {
            user_id: user.id,
            title: 'Lecture Session', // Default title
            duration_seconds: wallClockSeconds, // use full session elapsed time (includes silence)
            total_words: sessionData.total_words,
            average_wpm: sessionData.average_metrics.wpm,
            average_volume: sessionData.average_metrics.volume,
            average_pitch: sessionData.average_metrics.pitch,
            average_confidence: sessionData.average_metrics.confidence,
            average_silence_ratio: sessionData.average_metrics.silence_ratio,
            transcript: sessionData.final_transcript,
            start_time: new Date(sessionData.session_start_time * 1000).toISOString(),
            end_time: new Date(sessionData.session_end_time * 1000).toISOString()
            // Removed graph_data - now using metrics_data from session_metrics table
        };
        
        console.log('[DEBUG] Inserting session data:', JSON.stringify(insertData, null, 2));
        console.log('[DEBUG] New averages - Confidence:', sessionData.average_metrics.confidence, 'Silence Ratio:', sessionData.average_metrics.silence_ratio);
        
        const { data, error } = await supabase
            .from('lecture_sessions')
            .insert(insertData)
            .select()  // Return the inserted data so we can get the session ID
        
        if (error) {
            console.error('[DEBUG] Error inserting session data:', error);
            return { data: null, error }
        }
        
        console.log('[DEBUG] Session data inserted successfully:', data);
        
        // If session was created successfully and we have metrics data, save session metrics
        if (data && data[0] && sessionData.metrics_data) {
            console.log(`[DEBUG] Saving ${sessionData.metrics_data.length} chunks to session_metrics`);
            const metricsResult = await saveSessionMetrics(data[0].id, sessionData.metrics_data)
            if (metricsResult.error) {
                console.error('[DEBUG] Failed to save session metrics:', metricsResult.error);
            } else {
                console.log('[DEBUG] Session metrics saved successfully');
            }
        } else {
            console.log('[DEBUG] No metrics_data to save or session creation failed');
            if (!data || !data[0]) {
                console.log('[DEBUG] Session creation failed - no data returned');
            }
            if (!sessionData.metrics_data) {
                console.log('[DEBUG] No metrics_data in sessionData');
            }
        }
        
        return { data, error }
    } catch (err) {
        console.error('[DEBUG] Exception in saveSessionData:', err);
        return { data: null, error: err }
    }
}

// Save session metrics data to database
export async function saveSessionMetrics(sessionId, metricsData) {
    console.log(`[DEBUG] saveSessionMetrics called with sessionId: ${sessionId}, ${metricsData.length} chunks`);
    try {
        if (!sessionId || !metricsData || !Array.isArray(metricsData)) {
            console.error('[DEBUG] Invalid parameters:', { sessionId, metricsDataLength: metricsData?.length, isArray: Array.isArray(metricsData) });
            throw new Error('Invalid session ID or metrics data')
        }
        
        // Transform metrics data for database insertion
        // This converts our Python data structure to the database format
        const metricsToInsert = metricsData.map((metric, index) => ({
            session_id: sessionId,                    // Link to the session
            chunk_index: index + 1,                   // Order within session (1, 2, 3, etc.)
            timestamp_seconds: metric.timestamp || 0, // When this chunk occurred (relative to session start)
            wpm: metric.wpm || null,                  // Words per minute for this chunk
            volume: metric.volume || null,            // Volume in dB for this chunk
            pitch: metric.pitch || null,              // Pitch variance for this chunk
            confidence_score: metric.confidence || null,  // Transcription confidence (0-1)
            silence_ratio: metric.silence_ratio || null   // Ratio of silence in chunk (0-1)
        }))
        
        console.log(`[DEBUG] Transformed ${metricsToInsert.length} chunks for database insertion`);
        console.log('[DEBUG] Sample transformed chunk:', metricsToInsert[0]);
        
        // Insert all metrics data into the database
        const { data, error } = await supabase
            .from('session_metrics')
            .insert(metricsToInsert)
        
        if (error) {
            console.error('[DEBUG] Error inserting metrics data:', error);
        } else {
            console.log(`[DEBUG] Successfully inserted ${metricsToInsert.length} chunks to session_metrics`);
        }
        
        return { data, error }
    } catch (err) {
        console.error('[DEBUG] Exception in saveSessionMetrics:', err);
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

// Goals functions
export async function getUserGoals() {
    try {
        const user = await getCurrentUser();
        if (!user) return { data: null, error: 'Not authenticated' };

        const { data, error } = await supabase
            .from('user_goals')
            .select('*')
            .eq('user_id', user.id)
            .single();

        return { data, error };
    } catch (err) {
        return { data: null, error: err };
    }
}

export async function saveUserGoals(goals) {
    try {
        const user = await getCurrentUser();
        if (!user) throw new Error('Not authenticated');

        const payload = {
            user_id: user.id,
            target_wpm: goals.target_wpm ?? null,
            target_volume: goals.target_volume ?? null,
            target_pitch: goals.target_pitch ?? null,
            average_wpm: goals.average_wpm ?? null,
            average_volume: goals.average_volume ?? null,
            average_pitch: goals.average_pitch ?? null
        };

        const { data, error } = await supabase
            .from('user_goals')
            .upsert(payload, { onConflict: 'user_id' })
            .select()
            .single();

        return { data, error };
    } catch (err) {
        return { data: null, error: err };
    }
}

// Callback function - only called when auth state changes
export function onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(callback)
}

// Get session metrics for a specific session
export async function getSessionMetrics(sessionId) {
    try {
        // Retrieve all metrics for the given session, ordered by chunk index
        const { data, error } = await supabase
            .from('session_metrics')
            .select('*')
            .eq('session_id', sessionId)
            .order('chunk_index', { ascending: true })
        
        return { data: data || [], error }
    } catch (err) {
        return { data: [], error: err }
    }
}

// Get session metrics statistics using direct queries
export async function getSessionMetricsStats(sessionId) {
    try {
        const { data, error } = await supabase
            .from('session_metrics')
            .select('wpm, volume, pitch, confidence_score, silence_ratio')
            .eq('session_id', sessionId)
        
        if (error) return { data: null, error }
        
        if (!data || data.length === 0) {
            return { data: null, error: 'No metrics found' }
        }
        
        // Calculate averages manually - handle string to number conversion
        const stats = {
            avg_wpm: data.reduce((sum, row) => sum + (parseFloat(row.wpm) || 0), 0) / data.length,
            avg_volume: data.reduce((sum, row) => sum + (parseFloat(row.volume) || 0), 0) / data.length,
            avg_pitch: data.reduce((sum, row) => sum + (parseFloat(row.pitch) || 0), 0) / data.length,
            avg_confidence: data.reduce((sum, row) => sum + (parseFloat(row.confidence_score) || 0), 0) / data.length,
            avg_silence_ratio: data.reduce((sum, row) => sum + (parseFloat(row.silence_ratio) || 0), 0) / data.length
        }
        
        return { data: stats, error: null }
    } catch (err) {
        return { data: null, error: err }
    }
}

// Get session metrics formatted for charts (replaces graph_data)
export async function getSessionMetricsForCharts(sessionId) {
    try {
        // Get all metrics for the session, ordered by timestamp
        const { data: metrics, error } = await supabase
            .from('session_metrics')
            .select('timestamp_seconds, wpm, volume, pitch, confidence_score, silence_ratio')
            .eq('session_id', sessionId)
            .order('timestamp_seconds', { ascending: true })
        
        if (error) {
            console.error('[DEBUG] Error getting session metrics for charts:', error);
            return { data: null, error };
        }
        
        if (!metrics || metrics.length === 0) {
            console.log('[DEBUG] No metrics data found for charts');
            return { data: null, error: 'No metrics data available' };
        }
        
        // Format data for charts (similar to old graph_data format)
        const chartData = {
            wpm_data: metrics.map(m => m.wpm || 0),
            volume_data: metrics.map(m => m.volume || 0),
            pitch_data: metrics.map(m => m.pitch || 0),
            confidence_data: metrics.map(m => m.confidence_score || 0),
            silence_data: metrics.map(m => m.silence_ratio || 0),
            timestamps: metrics.map(m => m.timestamp_seconds || 0),
            total_data_points: metrics.length
        };
        
        console.log(`[DEBUG] Formatted ${metrics.length} data points for charts`);
        return { data: chartData, error: null };
        
    } catch (err) {
        console.error('[DEBUG] Exception in getSessionMetricsForCharts:', err);
        return { data: null, error: err };
    }
}