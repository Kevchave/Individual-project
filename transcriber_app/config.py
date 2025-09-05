import os

# Backend configuration with environment variable overrides

# Audio
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
CHUNK_SEC = float(os.getenv("CHUNK_SEC", 2))

# Metrics windows (seconds)
WPM_WINDOW_SECONDS = int(os.getenv("WPM_WINDOW_SECONDS", 20))
VOLUME_WINDOW_SECONDS = int(os.getenv("VOLUME_WINDOW_SECONDS", 20))
PITCH_WINDOW_SECONDS = int(os.getenv("PITCH_WINDOW_SECONDS", 20))

# Devices
BLACKHOLE_ID = int(os.getenv("BLACKHOLE_ID", 3))
MIC_INPUT = os.getenv("MIC_INPUT") 