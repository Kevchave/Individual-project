#!/usr/bin/env python3
"""
Setup script for transcription testing environment
"""

import os
from pathlib import Path

def create_test_directories():
    """Create necessary directories for testing"""
    directories = [
        "test_audio",
        "test_results",
        "reference_transcripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_sample_transcript_template():
    """Create a template for reference transcripts"""
    template_content = """# Reference Transcript Template

This is a sample reference transcript for testing.
Replace this content with the exact words from your audio file.

Guidelines:
- Include all spoken words exactly as they appear in the audio
- Include punctuation where appropriate
- One sentence per line for easier reading
- Remove any timestamps or speaker labels

Example:
The quick brown fox jumps over the lazy dog.
This is a sample sentence for transcription testing.
"""
    
    template_path = Path("reference_transcripts/template.txt")
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    print(f"✅ Created transcript template: {template_path}")

def create_audio_file_guide():
    """Create a guide for audio file requirements"""
    guide_content = """# Audio File Requirements

## Supported Formats:
- MP3 (.mp3)
- WAV (.wav)

## File Naming Convention:
Use descriptive names that indicate the speaking style:

### Seminar Style (Fast-paced, conversational):
- seminar_lecture1.mp3
- seminar_discussion.mp3
- seminar_group.mp3

### Lecture Style (Slower, structured):
- lecture_math101.mp3
- lecture_physics.mp3
- lecture_history.mp3

### Talk Style (Performative, enthusiastic):
- talk_ted.mp3
- talk_presentation.mp3
- talk_story.mp3

## Audio Quality Requirements:
- Sample rate: Any (will be converted to 16kHz)
- Channels: Any (will be converted to mono)
- Duration: 30 seconds to 10 minutes recommended
- Quality: Clear speech, minimal background noise

## File Structure:
test_audio/
├── seminar_lecture1.mp3
├── seminar_lecture1.txt    # Reference transcript
├── lecture_math101.mp3
├── lecture_math101.txt     # Reference transcript
├── talk_ted.mp3
└── talk_ted.txt           # Reference transcript
"""
    
    guide_path = Path("test_audio/README.md")
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Created audio file guide: {guide_path}")

def check_audio_files():
    """Check if audio files are present"""
    test_audio_dir = Path("test_audio")
    
    if not test_audio_dir.exists():
        print("❌ test_audio directory not found")
        return False
    
    audio_files = list(test_audio_dir.glob("*.mp3")) + list(test_audio_dir.glob("*.wav"))
    
    if not audio_files:
        print("❌ No audio files found in test_audio/")
        print("   Please add some .mp3 or .wav files")
        return False
    
    print(f"✅ Found {len(audio_files)} audio files:")
    for audio_file in audio_files:
        print(f"   - {audio_file.name}")
    
    # Check for corresponding transcripts
    missing_transcripts = []
    for audio_file in audio_files:
        transcript_file = audio_file.with_suffix('.txt')
        if not transcript_file.exists():
            missing_transcripts.append(audio_file.name)
    
    if missing_transcripts:
        print(f"⚠️  Missing transcripts for {len(missing_transcripts)} files:")
        for filename in missing_transcripts:
            print(f"   - {filename} (needs {filename.replace('.mp3', '.txt')})")
    else:
        print("✅ All audio files have corresponding transcripts")
    
    return True

def main():
    """Main setup function"""
    print("Setting up Transcription Testing Environment")
    print("=" * 50)
    
    # Create directories
    create_test_directories()
    
    # Create guides
    create_sample_transcript_template()
    create_audio_file_guide()
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("=" * 50)
    
    print("1. Add audio files to test_audio/ directory")
    print("2. Create corresponding .txt transcript files")
    print("3. Run the test runner: python test_framework/test_runner.py")
    
    print("\nChecking current setup...")
    check_audio_files()
    
    print("\n" + "=" * 50)
    print("WHERE TO GET AUDIO FILES:")
    print("=" * 50)
    print("• University lecture recordings")
    print("• YouTube educational videos")
    print("• Record your own samples")
    print("• Use existing audio files you have")

if __name__ == "__main__":
    main() 