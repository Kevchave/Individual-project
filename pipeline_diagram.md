# Live Lecture Feedback System - High-Level Pipeline

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Web Browser (Chrome/Firefox/Safari)                                                │
│  ├── HTML Templates (Jinja2)                                                        │
│  ├── CSS Styling (main.css)                                                         │
│  └── JavaScript Modules (ES6)                                                       │
│      ├── main.js (orchestration)                                                    │
│      ├── controls.js (UI event handlers)                                            │
│      ├── polling.js (data fetching)                                                 │
│      ├── charts.js (Chart.js integration)                                           │
│      ├── state.js (shared state management)                                         │
│      └── theme.js (light/dark mode)                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │ HTTP Requests/Responses
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Flask Web Server (server.py)                                                       │
│  ├── REST API Endpoints                                                             │
│  │   ├── POST /start_recording    → start_transcription_pipeline()                 │
│  │   ├── POST /stop_recording     → stop_transcription_pipeline()                  │
│  │   ├── POST /pause_recording    → pause_transcription_pipeline()                 │
│  │   ├── POST /resume_recording   → resume_transcription_pipeline()                │
│  │   ├── GET  /get_live_transcript → get_current_transcript()                     │
│  │   ├── GET  /get_live_metrics   → get_current_metrics()                         │
│  │   ├── GET  /get_final_transcript → get_final_transcript()                      │
│  │   └── GET  /get_average_metrics → get_average_metrics()                         │
│  └── Template Rendering (Jinja2)                                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │ Function Calls
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                TRANSCRIPTION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  transcriber_app/ (Python Package)                                                  │
│  ├── main.py (Pipeline Orchestration)                                               │
│  ├── audio_stream.py (Audio Capture)                                                │
│  ├── transcriber.py (Speech-to-Text)                                                │
│  └── track_metrics.py (Real-time Analytics)                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │ Audio Data Flow
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   AUDIO LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  System Audio Input                                                                 │
│  ├── Microphone (Default Device)                                                    │
│  ├── BlackHole Audio (macOS) - Device ID 3                                         │
│  └── Custom Audio Interface                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Data Flow Pipeline

### 1. INITIALIZATION PHASE
```
User Opens Browser → Flask Serves index.html → JavaScript Initializes
├── Theme system loads from localStorage
├── Chart.js creates empty line charts (WPM, Volume, Pitch)
├── Event listeners attached to Start/Pause/Stop buttons
└── State variables initialized (isPaused=false, metricsMode="live")
```

### 2. AUDIO CAPTURE PHASE
```
User Clicks "Start Recording" → Frontend → Backend → Audio Pipeline
├── Frontend: POST /start_recording
├── Backend: start_transcription_pipeline()
│   ├── AudioStream(sample_rate=16000, device_id=None)
│   ├── Transcriber(model_size="small", device="cpu")
│   ├── MetricsTracker(sample_rate=16000)
│   └── Background threads spawned for metrics computation
└── AudioStream.start() → sounddevice.InputStream opens
```

### 3. REAL-TIME PROCESSING PHASE
```
Audio Input → Processing Pipeline → Metrics & Transcription
│
├── AUDIO CAPTURE (audio_stream.py)
│   ┌─────────────────────────────────────────────────────────┐
│   │ sounddevice.InputStream (16kHz, mono, float32)         │
│   │ ↓ callback() triggered every ~0.1s                     │
│   │ ↓ Convert to 16-bit PCM: (indata[:,0] * 32767).astype(np.int16)
│   │ ↓ Push to audio_queue (thread-safe)                    │
│   └─────────────────────────────────────────────────────────┘
│
├── TRANSCRIPTION (transcriber.py)
│   ┌─────────────────────────────────────────────────────────┐
│   │ audio_queue.get() → buffer accumulation                 │
│   │ ↓ When buffer >= chunk_samples (48,000 samples = 3s)   │
│   │ ↓ Normalize: audio_float = chunk.astype(np.float32) / 32767.0
│   │ ↓ Whisper Model: model.transcribe(audio_float, fp16=False, language="en")
│   │ ↓ Extract: result["text"]                              │
│   │ ↓ Callback: on_transcription(text)                     │
│   └─────────────────────────────────────────────────────────┘
│
└── METRICS COMPUTATION (track_metrics.py)
    ┌─────────────────────────────────────────────────────────┐
    │ Audio Chunks: on_audio_chunk(audio_float)              │
    │ ↓ Store: all_audio_chunks.append((audio_float, timestamp))
    │ ↓ Thread 1: track_volume(window_seconds=6)             │
    │ │  └── RMS calculation → dBFS conversion               │
    │ ↓ Thread 2: track_pitch(window_seconds=6)              │
    │ │  └── librosa.pyin() → pitch variance (std dev)       │
    │ └── Transcription: on_transcription(text)              │
    │    ↓ Store: accumulated.append((text, timestamp))      │
    │    ↓ Thread 3: track_wpm(window_seconds=6)             │
    │       └── Word count / time window                     │
    └─────────────────────────────────────────────────────────┘
```

### 4. FRONTEND UPDATES PHASE
```
Background Polling → Data Fetching → UI Updates
│
├── TRANSCRIPT POLLING (every 2 seconds)
│   ┌─────────────────────────────────────────────────────────┐
│   │ setInterval(() => pollTranscript(), 2000)              │
│   │ ↓ GET /get_live_transcript                             │
│   │ ↓ Response: {"transcript": "latest text"}              │
│   │ ↓ Update: transcriptBox.textContent = data.transcript  │
│   └─────────────────────────────────────────────────────────┘
│
└── METRICS POLLING (every 6 seconds)
    ┌─────────────────────────────────────────────────────────┐
    │ setInterval(() => pollMetrics(), 6000)                 │
    │ ↓ GET /get_live_metrics                                │
    │ ↓ Response: {"wpm": 120.5, "volume": -12.3, "pitch": 45.2}
    │ ↓ If !isPaused:                                        │
    │   ├── Update DOM: wpmValue.textContent = data.wpm.toFixed(2)
    │   ├── Update DOM: volumeValue.textContent = data.volume.toFixed(2)
    │   ├── Update DOM: pitchValue.textContent = data.pitch.toFixed(2)
    │   └── Update Charts: updateCharts(wpm, volume, pitch)  │
    └─────────────────────────────────────────────────────────┘
```

### 5. PAUSE/RESUME PHASE
```
User Clicks "Pause" → Audio Stream Control → UI State
│
├── PAUSE FLOW
│   ┌─────────────────────────────────────────────────────────┐
│   │ POST /pause_recording                                  │
│   │ ↓ pause_transcription_pipeline()                       │
│   │ ↓ audio_stream.pause() → stream.stop()                 │
│   │ ↓ Response: {"status": "paused"}                       │
│   │ ↓ Frontend: setIsPaused(true)                          │
│   │ ↓ Frontend: pauseResumeBtn.textContent = "Resume"      │
│   │ ↓ Polling continues but chart updates skipped         │
    └─────────────────────────────────────────────────────────┘
│
└── RESUME FLOW
    ┌─────────────────────────────────────────────────────────┐
    │ POST /resume_recording                                 │
    │ ↓ resume_transcription_pipeline()                      │
    │ ↓ audio_stream.resume() → stream.start()               │
    │ ↓ Response: {"status": "resumed"}                      │
    │ ↓ Frontend: setIsPaused(false)                         │
    │ ↓ Frontend: pauseResumeBtn.textContent = "Pause"       │
    │ ↓ Chart updates resume                                │
    └─────────────────────────────────────────────────────────┘
```

### 6. SESSION END PHASE
```
User Clicks "Stop" → Final Data Collection → Session Summary
│
├── STOPPING PIPELINE
│   ┌─────────────────────────────────────────────────────────┐
│   │ POST /stop_recording                                   │
│   │ ↓ stop_transcription_pipeline()                        │
│   │ ↓ audio_stream.stop() → stream.close()                 │
│   │ ↓ Clear polling intervals                             │
│   │ ↓ Reset charts                                         │
│   └─────────────────────────────────────────────────────────┘
│
├── FINAL DATA RETRIEVAL
│   ┌─────────────────────────────────────────────────────────┐
│   │ GET /get_final_transcript                              │
│   │ ↓ get_final_transcript()                               │
│   │ ↓ ' '.join(text for text, ts in accumulated)          │
│   │ ↓ Update: transcriptBox.textContent = full_transcript │
│   └─────────────────────────────────────────────────────────┘
│
└── AVERAGE METRICS COMPUTATION
    ┌─────────────────────────────────────────────────────────┐
    │ GET /get_average_metrics                               │
    │ ↓ get_average_metrics()                                │
    │ ↓ track_wpm_average(start_time)                        │
    │ ↓ track_volume_average(start_time)                     │
    │ ↓ track_overall_pitch(start_time)                      │
    │ ↓ Update: metric displays show averages                │
    │ ↓ Update: metricsMode = "average"                      │
    └─────────────────────────────────────────────────────────┘
```

## Key Technical Specifications

### Audio Processing
- **Sample Rate**: 16,000 Hz (Whisper standard)
- **Chunk Duration**: 3 seconds (48,000 samples)
- **Format**: 16-bit PCM → float32 [-1, 1] normalization
- **Channels**: Mono (single channel)

### Metrics Windows
- **WPM Window**: 6 seconds (rolling average)
- **Volume Window**: 6 seconds (RMS → dBFS)
- **Pitch Window**: 6 seconds (librosa.pyin variance)

### Polling Intervals
- **Transcript Updates**: Every 2 seconds
- **Metrics Updates**: Every 6 seconds
- **Chart Data Points**: Maximum 5 points (30 seconds of history)

### Model Configuration
- **Whisper Model**: "small" (244M parameters)
- **Device**: CPU (fp16=False)
- **Language**: English (en)
- **Precision**: float32

### Threading Architecture
- **Main Thread**: Flask web server
- **Audio Thread**: sounddevice callback (non-blocking)
- **Transcription Thread**: Whisper processing (daemon)
- **Metrics Threads**: 3 daemon threads for WPM/Volume/Pitch
- **Frontend**: Event-driven with setInterval polling 