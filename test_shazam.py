#!/usr/bin/env python3
"""
Test script to help with Shazam web interface
"""

import json
import os
import subprocess
import random
from pathlib import Path
from dotenv import load_dotenv
import webbrowser

# Load environment variables from .env file
load_dotenv()

def get_audio_duration(audio_path):
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-show_entries", "format=duration", 
            "-of", "csv=p=0", 
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return None

def extract_audio_segment(audio_path, start_time, duration=30):
    """Extract a segment from audio file using ffmpeg"""
    # Shazam works best with 10-30 seconds of clear audio
    output_path = f"shazam_segment_{start_time:.1f}s.mp3"
    
    try:
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c", "copy",  # Copy without re-encoding for speed
            "-y",  # Overwrite output file
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return Path(output_path)
    except subprocess.CalledProcessError:
        print(f"❌ Failed to extract segment starting at {start_time}s")
        return None

def open_shazam_web(audio_path=None):
    """Open Shazam web interface for drag-and-drop upload"""
    print("\n🌐 Opening Shazam web interface...")
    print("📋 Instructions:")
    print("1. Drag and drop your MP3 file to the Shazam web page")
    print("2. Wait for Shazam to analyze the audio")
    print("3. View the song identification results")
    
    # Open Shazam web interface
    shazam_url = "https://www.shazam.com/"
    webbrowser.open(shazam_url)
    print(f"✅ Opened {shazam_url}")
    
    if audio_path:
        print(f"\n📁 Your audio file is located at:")
        print(f"   {audio_path.absolute()}")
        print("\n💡 Simply drag this file to the Shazam web page!")
    
    print("\n🎯 Alternative Shazam URLs:")
    print("   • https://www.shazam.com/ (Main site)")
    print("   • https://apps.apple.com/app/shazam/id284993459 (iOS app)")
    print("   • https://play.google.com/store/apps/details?id=com.shazam.android (Android app)")

def test_shazam_web():
    """Test Shazam web interface with existing audio file"""
    print("🧪 Shazam Web Interface Test")
    print("=" * 40)
    print("✨ Simple drag-and-drop approach!")
    print()
    
    # Check if we have audio files
    separated_files = list(Path(".").glob("separated/**/no_vocals.mp3"))
    original_audio_files = list(Path(".").glob("audio.*"))
    
    if not separated_files and not original_audio_files:
        print("❌ No audio files found!")
        print("💡 Make sure you have an audio file in the current directory")
        print("💡 Or run the main pipeline first to create vocals-removed file")
        return
    
    # Show available files
    print("📁 Available audio files:")
    
    if separated_files:
        print("   🎵 Vocals-removed files (recommended):")
        for i, file_path in enumerate(separated_files, 1):
            file_size = os.path.getsize(str(file_path))
            duration = get_audio_duration(file_path)
            print(f"   {i}. {file_path.name} ({file_size:,} bytes, {duration:.1f}s)")
    
    if original_audio_files:
        print("   📝 Original audio files:")
        for i, file_path in enumerate(original_audio_files, 1):
            file_size = os.path.getsize(str(file_path))
            duration = get_audio_duration(file_path)
            print(f"   {len(separated_files) + i}. {file_path.name} ({file_size:,} bytes, {duration:.1f}s)")
    
    print("\n🎯 Choose a file to test with Shazam web:")
    print("1. Use vocals-removed file (best for music identification)")
    print("2. Use original audio file")
    print("3. Create a shorter segment (if file is too large)")
    print("4. Open Shazam web without specifying a file")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1" and separated_files:
        selected_file = separated_files[0]
        print(f"\n🎵 Using vocals-removed file: {selected_file}")
        open_shazam_web(selected_file)
    
    elif choice == "2" and original_audio_files:
        selected_file = original_audio_files[0]
        print(f"\n📝 Using original audio file: {selected_file}")
        open_shazam_web(selected_file)
    
    elif choice == "3":
        # Create a shorter segment
        if original_audio_files:
            audio_path = original_audio_files[0]
            duration = get_audio_duration(audio_path)
            
            if duration and duration > 60:
                print(f"\n📦 Creating a 30-second segment from {audio_path.name}...")
                start_time = random.uniform(10, duration - 40)  # Avoid very beginning/end
                segment_path = extract_audio_segment(audio_path, start_time, 30)
                
                if segment_path:
                    print(f"✅ Created segment: {segment_path}")
                    open_shazam_web(segment_path)
                else:
                    print("❌ Failed to create segment")
                    open_shazam_web()
            else:
                print("📦 File is already short enough, opening Shazam web...")
                open_shazam_web(audio_path)
        else:
            print("❌ No original audio file found")
            open_shazam_web()
    
    elif choice == "4":
        open_shazam_web()
    
    else:
        print("❌ Invalid choice or no files available")
        open_shazam_web()
    
    print("\n💡 Tips for better results:")
    print("   • Use vocals-removed files when possible")
    print("   • Shorter segments (10-30 seconds) work better")
    print("   • Clear music without speech works best")
    print("   • Try different segments if the first doesn't work")

if __name__ == "__main__":
    test_shazam_web()
    print("\n🎉 Test completed!")
    print("\n💡 Shazam web is free and works with any MP3 file!") 