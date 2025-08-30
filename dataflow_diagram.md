# Live Lecture Feedback System - Data Flow Diagram

## Real-Time Data Flow

```
┌─────────────┐
│ Microphone  │
│ (16kHz)     │
└─────┬───────┘
      │ Audio Stream (float32)
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audio Stream Processing                      │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Audio Queue   │    │   Audio Queue   │                    │
│  │  (thread-safe)  │    │  (thread-safe)  │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            │ 3-second chunks      │ 3-second chunks            │
│            │ (48,000 samples)     │ (48,000 samples)           │
│            ▼                      ▼                            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Whisper       │    │   Metrics       │                    │
│  │ Transcription   │    │ Calculation     │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            │ Text Results         │ Audio Analysis             │
│            ▼                      ▼                            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Transcription   │    │ Real-time       │                    │
│  │ Buffer          │    │ Metrics         │                    │
│  │ (text, timestamp)│   │ (WPM, Volume,   │                    │
│  └─────────┬───────┘    │  Pitch)         │                    │
│            │            └─────────┬───────┘                    │
│            │                      │                            │
│            │ WPM Calculation      │                            │
│            │ (word count / time)  │                            │
│            ▼                      │                            │
│  ┌─────────────────┐              │                            │
│  │ WPM Metrics     │              │                            │
│  │ (rolling avg)   │              │                            │
│  └─────────┬───────┘              │                            │
│            │                      │                            │
└────────────┼──────────────────────┼────────────────────────────┘
             │                      │
             │ Every 2 seconds      │ Every 6 seconds
             ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend UI                             │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Live Transcript │    │ Metrics Display │                    │
│  │ (latest text)   │    │ (WPM, Volume,   │                    │
│  │                 │    │  Pitch values)  │                    │
│  └─────────────────┘    └─────────┬───────┘                    │
│                                   │                            │
│                                   │ Chart Updates              │
│                                   ▼                            │
│                        ┌─────────────────┐                    │
│                        │ Real-time       │                    │
│                        │ Charts          │                    │
│                        │ (WPM, Volume,   │                    │
│                        │  Pitch over     │                    │
│                        │  time)          │                    │
│                        └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Data Processing Flow

### 1. Audio Input Stream
```
Microphone → sounddevice.InputStream → Audio Queue
├── Continuous audio capture at 16kHz
├── Callback triggered every ~0.1 seconds
├── Convert: float32 → 16-bit PCM → audio_queue.put(pcm)
└── Thread-safe queue for buffering
```

### 2. 3-Second Chunk Processing
```
Audio Queue → Buffer Accumulation → Dual Processing Paths
├── Buffer accumulates PCM data until ≥ 48,000 samples (3 seconds)
├── Split into two processing streams:
│   ├── Path A: Whisper Transcription
│   └── Path B: Metrics Calculation
└── Each chunk processed independently
```

### 3. Whisper Transcription Path
```
Audio Chunk → Whisper Model → Text → WPM Calculation
├── Normalize: PCM → float32 [-1, 1]
├── Whisper.transcribe(audio_float, fp16=False, language="en")
├── Extract: result["text"]
├── Store: accumulated.append((text, timestamp))
├── Calculate WPM: word_count / time_window (6 seconds)
└── Update: current_wpm
```

### 4. Metrics Calculation Path
```
Audio Chunk → Audio Analysis → Real-time Metrics
├── Store: all_audio_chunks.append((audio_float, timestamp))
├── Volume Calculation (6-second window):
│   ├── RMS: √(mean(audio²))
│   └── dBFS: 20 * log₁₀(rms + 1e⁻¹²)
├── Pitch Calculation (6-second window):
│   ├── librosa.pyin(audio, fmin=75, fmax=800)
│   └── Pitch variance: std_dev(voiced_frequencies)
└── Update: current_volume, current_pitch
```

### 5. Frontend Data Delivery
```
Backend Metrics → HTTP Polling → UI Updates
├── Transcript Polling (every 2 seconds):
│   ├── GET /get_live_transcript
│   ├── Response: {"transcript": "latest text"}
│   └── Update: transcriptBox.textContent
└── Metrics Polling (every 6 seconds):
    ├── GET /get_live_metrics
    ├── Response: {"wpm": 120.5, "volume": -12.3, "pitch": 45.2}
    ├── Update metric boxes (if not paused)
    └── Update charts (if not paused)
```

## Data Types and Formats

### Audio Data Flow
```
Raw Audio → PCM → Float32 → Processing
├── Input: Microphone (16kHz, mono)
├── Intermediate: 16-bit PCM (int16)
├── Processing: float32 [-1, 1] normalized
└── Storage: (audio_float, timestamp) tuples
```

### Text Data Flow
```
Whisper Output → Text Buffer → WPM → UI
├── Raw: result["text"] (string)
├── Stored: (text, timestamp) tuples
├── WPM: word_count / time_window
└── Display: latest text or full transcript
```

### Metrics Data Flow
```
Audio Analysis → Metrics → JSON → Charts
├── Volume: float (dBFS)
├── Pitch: float (Hz variance)
├── WPM: float (words per minute)
├── API: JSON response
└── Charts: time-series data points
```

## Key Data Transformations

### Audio Processing
- **Input**: Continuous microphone stream
- **Chunking**: 3-second segments (48,000 samples)
- **Normalization**: PCM → float32 [-1, 1]
- **Storage**: Timestamped audio chunks

### Transcription Processing
- **Input**: 3-second audio chunks
- **Model**: Whisper "small" (244M parameters)
- **Output**: Text strings
- **WPM**: Rolling 6-second word count

### Metrics Processing
- **Volume**: RMS → dBFS conversion
- **Pitch**: librosa.pyin → frequency variance
- **Windows**: 6-second rolling averages
- **Updates**: Every 6 seconds

### UI Updates
- **Transcript**: Every 2 seconds (latest text)
- **Metrics**: Every 6 seconds (current values)
- **Charts**: Maximum 5 data points (30 seconds)
- **State**: Pause/resume controls data flow 