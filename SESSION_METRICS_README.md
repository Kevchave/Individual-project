# Session Metrics Storage System

This document explains the implementation of the session metrics storage system that stores detailed chunk-by-chunk data from your lecture sessions.

## Overview

The system stores individual chunk metrics in the `session_metrics` table, where each row represents one chunk from a lecture session. Multiple chunks from the same session share the same `session_id` but have unique `id` values.

## Database Structure

### Enhanced session_metrics Table

```sql
-- Current columns (existing)
id                    -- Primary Key
session_id            -- Foreign Key to lecture_sessions
timestamp_seconds     -- When this chunk occurred
wpm                   -- Words per minute
volume                -- Volume in dB
pitch                 -- Pitch variance
chunk_duration        -- Duration of this chunk
created_at            -- When this record was created

-- New columns (added)
text                  -- Transcribed text for this chunk
chunk_index           -- Order within session (1, 2, 3, etc.)
confidence_score      -- Transcription confidence (0-1)
silence_ratio         -- Ratio of silence in chunk (0-1)
```

### How It Works

```
Session 1 (abc-123): 500 chunks → 500 rows with session_id = 'abc-123'
Session 2 (def-456): 1000 chunks → 1000 rows with session_id = 'def-456'
Session 3 (ghi-789): 300 chunks → 300 rows with session_id = 'ghi-789'
```

Each chunk has a unique `id` but chunks from the same session share the same `session_id`.

## Setup Instructions

### 1. Run the Database Enhancement Script

Execute `enhance_session_metrics.sql` in your Supabase SQL editor:

```sql
-- This will add the new columns and indexes
-- See enhance_session_metrics.sql for the complete script
```

### 2. Verify the Changes

After running the script, your table should have:
- All original columns plus the new ones
- Indexes for efficient querying
- Row Level Security policies
- Helper functions and views

## Data Flow

### 1. During Recording
- Python `MetricsTracker` collects chunk data in memory
- Each chunk includes text, duration, and metrics

### 2. Session End
- Chunk data is formatted for database storage
- Each chunk becomes a row in `session_metrics`

### 3. Save to Database
- JavaScript saves session summary to `lecture_sessions`
- Then saves individual chunks to `session_metrics`

### 4. Retrieve for Analysis
- Load chunks by `session_id` for detailed analysis

## Usage Examples

### Save Session Data (Automatic)
The system automatically saves metrics data when a session ends.

### Load Metrics for Analysis
```javascript
import { getSessionMetrics } from './supabase-cllient.js';
import { analyzeSessionMetrics } from './metrics-analysis.js';

// Get all chunks for a session
const { data: metrics, error } = await getSessionMetrics(sessionId);

// Analyze metrics for insights
const { data: analysis, error } = await analyzeSessionMetrics(sessionId);
```

### Find Problematic Chunks
```javascript
import { findProblematicChunks } from './metrics-analysis.js';

const problematic = findProblematicChunks(metrics, {
    maxWpm: 150,
    minVolume: -20,
    maxDuration: 10,
    minConfidence: 0.7
});
```

## Database Queries

### Get All Chunks for a Session
```sql
SELECT * FROM session_metrics 
WHERE session_id = 'your-session-id' 
ORDER BY chunk_index;
```

### Get Session Statistics
```sql
SELECT * FROM get_session_metrics_stats('your-session-id');
```

### Find High WPM Chunks
```sql
SELECT chunk_index, text, wpm 
FROM session_metrics 
WHERE session_id = 'your-session-id' 
AND wpm > 150 
ORDER BY wpm DESC;
```

### Get Sessions with Chunk Count
```sql
SELECT ls.*, COUNT(sm.id) as chunk_count
FROM lecture_sessions ls
LEFT JOIN session_metrics sm ON ls.id = sm.session_id
WHERE ls.user_id = auth.uid()
GROUP BY ls.id
ORDER BY ls.created_at DESC;
```

### Analyze Performance Trends
```sql
-- Get WPM trend across chunks
SELECT 
    chunk_index,
    wpm,
    LAG(wpm) OVER (ORDER BY chunk_index) as prev_wpm,
    wpm - LAG(wpm) OVER (ORDER BY chunk_index) as wpm_change
FROM session_metrics 
WHERE session_id = 'your-session-id'
ORDER BY chunk_index;
```

## Benefits

1. **Persistent Storage**: Metrics data survives page refreshes and new sessions
2. **Detailed Analysis**: Analyze performance at the chunk level
3. **Historical Comparison**: Compare chunks across different sessions
4. **Advanced Insights**: Identify patterns and problematic areas
5. **Scalable**: Efficient database structure with proper indexing
6. **Secure**: Row Level Security ensures data privacy

## Performance Considerations

### Indexes
- `session_id`: Fast queries by session
- `(session_id, timestamp_seconds)`: Time-based queries
- `(session_id, chunk_index)`: Ordered retrieval

### Data Volume
- Typical session: 50-200 chunks
- Each chunk: ~200 bytes
- 1000 sessions: ~100MB of metrics data

## Troubleshooting

### Common Issues

1. **Metrics not saving**: Check if `sessionData.metrics_data` exists
2. **Missing text**: Ensure transcription is working properly
3. **Database errors**: Verify the schema has been applied
4. **Slow queries**: Check if indexes are created

### Debug Steps

1. Check browser console for JavaScript errors
2. Verify Supabase table structure
3. Test with a simple session
4. Check RLS policies if access is denied

## Future Enhancements

Potential improvements:
- Real-time metrics analysis during recording
- Advanced filtering and search capabilities
- Chunk-level goal setting and tracking
- Export functionality for detailed reports
- Integration with external analysis tools
- Machine learning insights based on historical data 