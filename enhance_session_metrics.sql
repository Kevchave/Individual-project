-- Enhance session_metrics table with additional columns and indexes
-- Run this in your Supabase SQL editor

-- 1. Add new columns to session_metrics table
-- These columns will store the additional metrics we're collecting per chunk

-- text: Stores the actual transcribed text for each chunk
-- This allows us to see exactly what was said in each chunk
ALTER TABLE session_metrics ADD COLUMN IF NOT EXISTS text TEXT;

-- chunk_index: Stores the order of chunks within a session (1, 2, 3, etc.)
-- This helps us maintain the chronological order of chunks
ALTER TABLE session_metrics ADD COLUMN IF NOT EXISTS chunk_index INTEGER;

-- confidence_score: Stores the transcription confidence (0-1 scale)
-- Higher values mean the transcription is more reliable
ALTER TABLE session_metrics ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,3);

-- silence_ratio: Stores the ratio of silence in the chunk (0-1 scale)
-- 0 = no silence, 1 = all silence
ALTER TABLE session_metrics ADD COLUMN IF NOT EXISTS silence_ratio DECIMAL(5,3);

-- 2. Add indexes for better performance
-- Indexes help the database find data faster, especially when you have thousands of rows

-- Index on session_id: Makes queries by session very fast
-- This is the most important index since you'll query by session most often
CREATE INDEX IF NOT EXISTS idx_session_metrics_session_id ON session_metrics(session_id);

-- Composite index on session_id and timestamp: Fast time-based queries within a session
-- Useful for finding chunks within specific time ranges
CREATE INDEX IF NOT EXISTS idx_session_metrics_timestamp ON session_metrics(session_id, timestamp_seconds);

-- Composite index on session_id and chunk_index: Fast ordered retrieval of chunks
-- Useful for getting chunks in chronological order
CREATE INDEX IF NOT EXISTS idx_session_metrics_chunk_index ON session_metrics(session_id, chunk_index);

-- 3. Create a view for easy session analysis
-- This view joins session_metrics with lecture_sessions to provide a complete picture
-- You can query this view instead of writing complex JOIN queries
CREATE OR REPLACE VIEW session_metrics_analysis AS
SELECT 
    sm.*,                    -- All columns from session_metrics
    ls.title as session_title,  -- Session title from lecture_sessions
    ls.user_id,             -- User ID from lecture_sessions
    ls.created_at as session_created_at  -- When the session was created
FROM session_metrics sm
JOIN lecture_sessions ls ON sm.session_id = ls.id;

-- 4. Create a function to get session statistics
-- This function calculates summary statistics for any session
-- Returns: total chunks, average metrics, total duration, total words, etc.
CREATE OR REPLACE FUNCTION get_session_metrics_stats(session_uuid UUID)
RETURNS TABLE (
    total_chunks INTEGER,           -- How many chunks in the session
    avg_wpm DECIMAL(8,2),          -- Average words per minute
    avg_volume DECIMAL(8,2),       -- Average volume in dB
    avg_pitch DECIMAL(8,2),        -- Average pitch variance
    total_duration DECIMAL(10,3),  -- Total speaking duration
    total_words INTEGER,           -- Total words spoken
    avg_confidence DECIMAL(5,3),   -- Average transcription confidence
    avg_silence_ratio DECIMAL(5,3) -- Average silence ratio
) AS $$
BEGIN
    -- This query calculates all the statistics for the given session
    -- Explicitly cast AVG results to DECIMAL to match the return type
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_chunks,  -- Count all chunks
        AVG(wpm)::DECIMAL(8,2) as avg_wpm,                -- Average WPM across all chunks
        AVG(volume)::DECIMAL(8,2) as avg_volume,          -- Average volume across all chunks
        AVG(pitch)::DECIMAL(8,2) as avg_pitch,            -- Average pitch across all chunks
        SUM(chunk_duration)::DECIMAL(10,3) as total_duration,  -- Sum of all chunk durations
        SUM(array_length(string_to_array(COALESCE(text, ''), ' '), 1))::INTEGER as total_words,  -- Count words in all text
        AVG(confidence_score)::DECIMAL(5,3) as avg_confidence,  -- Average confidence across all chunks
        AVG(silence_ratio)::DECIMAL(5,3) as avg_silence_ratio   -- Average silence ratio across all chunks
    FROM session_metrics
    WHERE session_id = session_uuid;  -- Filter by the specific session
END;
$$ LANGUAGE plpgsql;

-- 5. Enable Row Level Security (RLS) if not already enabled
-- RLS ensures users can only access their own data
ALTER TABLE session_metrics ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policies for session_metrics
-- These policies control who can read and write session_metrics data

-- Policy for reading session_metrics: Users can only view their own data
-- This checks that the session_id belongs to a session owned by the current user
CREATE POLICY "Users can view their own session metrics" ON session_metrics
    FOR SELECT USING (
        session_id IN (
            SELECT id FROM lecture_sessions 
            WHERE user_id = auth.uid()  -- auth.uid() gets the current user's ID
        )
    );

-- Policy for inserting session_metrics: Users can only insert data for their own sessions
-- This prevents users from inserting data for other users' sessions
CREATE POLICY "Users can insert their own session metrics" ON session_metrics
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT id FROM lecture_sessions 
            WHERE user_id = auth.uid()
        )
    );

-- 7. Add comments to document the table structure
-- These comments help other developers understand what each column is for
COMMENT ON TABLE session_metrics IS 'Stores individual chunk metrics for each lecture session';
COMMENT ON COLUMN session_metrics.text IS 'Transcribed text for this chunk';
COMMENT ON COLUMN session_metrics.chunk_index IS 'Order of chunk within session (1, 2, 3, etc.)';
COMMENT ON COLUMN session_metrics.confidence_score IS 'Transcription confidence score (0-1)';
COMMENT ON COLUMN session_metrics.silence_ratio IS 'Ratio of silence in chunk (0-1)'; 