#!/usr/bin/env python3
"""
Simple YouTube Short to Music Identification Pipeline
Uses web-based services and ACRCloud API for easier setup
"""

import webbrowser
import subprocess
import sys
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_yt_dlp():
    """Check if yt-dlp is installed"""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_with_yt_dlp(url):
    """Download YouTube Short audio directly as MP3 using yt-dlp"""
    print(f"🎬 Downloading audio from: {url}")
    
    try:
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio only
            "--audio-format", "mp3",  # Convert to MP3
            "--audio-quality", "0",  # Best quality
            "-o", "audio.%(ext)s",  # Output filename
            url
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ Audio download completed!")
        
        # Find the downloaded audio file
        audio_files = list(Path(".").glob("audio.*"))
        if audio_files:
            return audio_files[0]
        else:
            print("❌ Could not find downloaded audio file")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        return None

def extract_audio_with_ffmpeg(video_path):
    """Extract audio using ffmpeg"""
    print("🎵 Extracting audio...")
    
    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-acodec", "mp3",
            "-y",
            "audio.mp3"
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        print("✅ Audio extracted to audio.mp3")
        return Path("audio.mp3")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Audio extraction failed: {e}")
        return None

def remove_speech_demucs_api(audio_path):
    """Remove speech using Demucs Python API"""
    print("🔇 Removing speech using Demucs API...")
    print("⚠️  This may take a few minutes depending on audio length...")
    
    try:
        # Import demucs
        import demucs.separate
        
        # Create output directory for Demucs
        demucs_output = Path("separated")
        demucs_output.mkdir(exist_ok=True)
        
        # Run Demucs using the Python API
        # This is equivalent to: demucs --two-stems=vocals audio.mp3
        demucs.separate.main([
            "--two-stems=vocals",
            "-o", str(demucs_output),
            str(audio_path)
        ])
        
        # Find the separated audio file
        # Demucs creates output in: separated/htdemucs/audio/no_vocals.wav
        model_name = "htdemucs"  # Default model
        audio_name = audio_path.stem
        no_vocals_path = demucs_output / model_name / audio_name / "no_vocals.wav"
        
        if no_vocals_path.exists():
            print("✅ Speech removed successfully using Demucs API")
            return no_vocals_path
        else:
            print("❌ Could not find separated audio file")
            return None
            
    except ImportError:
        print("❌ Demucs not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "demucs"], check=True)
            print("✅ Demucs installed successfully")
            # Try again
            return remove_speech_demucs_api(audio_path)
        except subprocess.CalledProcessError:
            print("❌ Failed to install Demucs")
            return None
    except Exception as e:
        print(f"❌ Error removing speech with Demucs API: {e}")
        return None

def remove_speech_subprocess(audio_path):
    """Remove speech using Demucs subprocess (fallback method)"""
    print("🔇 Removing speech using Demucs subprocess...")
    print("⚠️  This may take a few minutes depending on audio length...")
    
    try:
        # Run Demucs to separate vocals and music
        cmd = [
            "demucs",
            "--two-stems=vocals",  # Separate vocals from the rest
            str(audio_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Demucs creates output in a specific directory structure
        # Look for the "no_vocals" file
        demucs_output = Path("separated") / "htdemucs" / audio_path.stem
        no_vocals_path = demucs_output / "no_vocals.wav"
        
        if no_vocals_path.exists():
            print("✅ Speech removed successfully")
            return no_vocals_path
        else:
            print("❌ Could not find separated audio file")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error removing speech: {e}")
        return None

def remove_speech(audio_path):
    """Remove speech using Demucs (tries API first, then subprocess)"""
    # Try Python API first
    result = remove_speech_demucs_api(audio_path)
    if result:
        return result
    
    # Fallback to subprocess
    print("🔄 Falling back to subprocess method...")
    return remove_speech_subprocess(audio_path)

def identify_with_acrcloud(audio_path, api_key=None, host=None):
    """Identify song using ACRCloud API"""
    # Use provided values or fall back to environment variables
    api_key = api_key or os.getenv('ACRCLOUD_API_KEY')
    host = host or os.getenv('ACRCLOUD_HOST')
    
    if not api_key or not host:
        print("❌ ACRCloud API credentials not found!")
        print("💡 Set ACRCLOUD_API_KEY and ACRCLOUD_HOST in your .env file")
        return None
    
    print("🎵 Identifying with ACRCloud...")
    
    try:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # ACRCloud signature creation
        import hashlib
        import hmac
        import base64
        import time
        
        timestamp = str(int(time.time()))
        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        
        string_to_sign = '\n'.join([http_method, http_uri, api_key, data_type, signature_version, timestamp])
        sign = base64.b64encode(hmac.new(api_key.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()).decode('ascii')
        
        headers = {
            'access-key': api_key,
            'signature': sign,
            'signature-version': signature_version,
            'timestamp': timestamp,
            'data-type': data_type
        }
        
        files = {'sample': audio_data}
        url = f"https://{host}/v1/identify"
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status', {}).get('code') == 0 and result.get('metadata', {}).get('music'):
                music = result['metadata']['music'][0]
                print("✅ Song identified with ACRCloud!")
                print(f"🎵 Title: {music.get('title', 'Unknown')}")
                print(f"👤 Artist: {music.get('artists', [{}])[0].get('name', 'Unknown')}")
                print(f"📀 Album: {music.get('album', {}).get('name', 'Unknown')}")
                print(f"🎼 Genre: {music.get('genres', [{}])[0].get('name', 'Unknown')}")
                return music
            else:
                print("❌ No match found with ACRCloud")
                return None
        else:
            print(f"❌ ACRCloud API failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ ACRCloud error: {e}")
        return None

def open_web_services():
    """Open web-based vocal removal services"""
    print("\n🌐 Opening web-based vocal removal services...")
    print("Choose one of these services to remove speech:")
    
    services = [
        ("Lalal.ai - High quality vocal removal", "https://lalal.ai"),
        ("Moises.ai - AI-powered separation", "https://moises.ai"),
        ("VocalRemover.org - Free online tool", "https://vocalremover.org"),
        ("Splitter.ai - Another good option", "https://splitter.ai")
    ]
    
    for i, (name, url) in enumerate(services, 1):
        print(f"{i}. {name}")
    
    print("\n📋 Instructions:")
    print("1. Upload your audio.mp3 file")
    print("2. Use the vocal removal tool")
    print("3. Download the instrumental version")
    print("4. Use the ACRCloud API identification option below")
    
    choice = input("\nOpen which service? (1-4, or press Enter to skip): ").strip()
    
    if choice in ['1', '2', '3', '4']:
        service_url = services[int(choice) - 1][1]
        webbrowser.open(service_url)
        print(f"✅ Opened {service_url}")

def cleanup_existing_files():
    """Delete existing MP3 files and other temporary files"""
    print("🧹 Cleaning up existing files...")
    
    # Files to delete
    files_to_delete = [
        "audio.mp3",
        "audio.wav", 
        "no_vocals.mp3",
        "no_vocals.wav",
        "video.mp4",
        "video.webm",
        "video.mkv"
    ]
    
    deleted_count = 0
    for file_name in files_to_delete:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🗑️  Deleted: {file_name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Could not delete {file_name}: {e}")
    
    # Also clean up separated folder if it exists
    separated_dir = Path("separated")
    if separated_dir.exists():
        try:
            import shutil
            shutil.rmtree(separated_dir)
            print("🗑️  Deleted: separated/ folder")
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Could not delete separated/ folder: {e}")
    
    if deleted_count > 0:
        print(f"✅ Cleaned up {deleted_count} files/folders")
    else:
        print("✅ No files to clean up")

def main():
    print("🎵 YouTube Short to Music Identification - Simple Pipeline")
    print("=" * 60)
    
    # Clean up existing files first
    cleanup_existing_files()
    print()
    
    # Get YouTube URL
    url = input("Enter YouTube Short URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    # Check if yt-dlp is available
    if not check_yt_dlp():
        print("❌ yt-dlp not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
            print("✅ yt-dlp installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install yt-dlp")
            print("💡 Install manually: pip install yt-dlp")
            return
    
    # Download audio directly
    audio_path = download_with_yt_dlp(url)
    if not audio_path:
        return
    
    print(f"\n✅ Audio downloaded to: {audio_path}")
    
    # Check if ACRCloud credentials are available
    acrcloud_key = os.getenv('ACRCLOUD_API_KEY')
    acrcloud_host = os.getenv('ACRCLOUD_HOST')
    
    if acrcloud_key and acrcloud_host:
        print(f"✅ ACRCloud credentials found in .env file")
        print(f"   Host: {acrcloud_host}")
    else:
        print("⚠️  ACRCloud credentials not found in .env file")
    
    # Ask user what they want to do
    print("\n🎯 Choose your next step:")
    print("1. Use web-based vocal removal (manual)")
    print("2. ACRCloud API - Remove vocals first, then identify")
    print("3. ACRCloud API - Identify with original audio (no vocal removal)")
    print("4. Both web services and API options")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice in ['1', '4']:
        open_web_services()
    
    if choice in ['2', '3', '4']:
        print("\n🔑 ACRCloud API Identification:")
        
        # Use credentials from .env file or ask user
        if acrcloud_key and acrcloud_host:
            use_env = input("Use credentials from .env file? (y/n): ").strip().lower()
            if use_env == 'y':
                if choice == '2':
                    # Option 2: Remove vocals first, then identify
                    print("\n🔇 Removing vocals using Demucs...")
                    
                    # Use integrated Demucs API
                    no_vocals_path = remove_speech(audio_path)
                    
                    if no_vocals_path and no_vocals_path.exists():
                        print("✅ Vocals removed successfully!")
                        
                        # Convert to MP3 for API (if needed)
                        mp3_path = Path("no_vocals.mp3")
                        convert_cmd = [
                            "ffmpeg",
                            "-i", str(no_vocals_path),
                            "-acodec", "mp3",
                            "-ab", "192k",
                            "-y",
                            str(mp3_path)
                        ]
                        
                        subprocess.run(convert_cmd, capture_output=True, check=True)
                        print("✅ Converted to MP3 for API upload")
                        
                        # Identify with ACRCloud
                        result = identify_with_acrcloud(mp3_path)
                    else:
                        print("❌ Could not remove vocals")
                        result = None
                        
                elif choice == '3':
                    # Option 3: Identify with original audio
                    result = identify_with_acrcloud(audio_path)
                else:
                    # Option 4: Both options
                    print("\n🎵 Trying both methods...")
                    
                    # First try with vocal removal
                    print("\n--- Method 1: With vocal removal ---")
                    no_vocals_path = remove_speech(audio_path)
                    
                    result1 = None
                    if no_vocals_path and no_vocals_path.exists():
                        mp3_path = Path("no_vocals.mp3")
                        convert_cmd = ["ffmpeg", "-i", str(no_vocals_path), "-acodec", "mp3", "-ab", "192k", "-y", str(mp3_path)]
                        subprocess.run(convert_cmd, capture_output=True, check=True)
                        
                        result1 = identify_with_acrcloud(mp3_path)
                        if result1:
                            print("\n🎵 Result with vocal removal:")
                            print(json.dumps(result1, indent=2))
                    
                    # Then try with original audio
                    print("\n--- Method 2: With original audio ---")
                    result2 = identify_with_acrcloud(audio_path)
                    if result2:
                        print("\n🎵 Result with original audio:")
                        print(json.dumps(result2, indent=2))
                    
                    result = result1 or result2
                    
            else:
                # Ask for manual input
                manual_key = input("Enter ACRCloud API key: ").strip()
                manual_host = input("Enter ACRCloud host: ").strip()
                if manual_key and manual_host:
                    if choice == '2':
                        print("🔇 Manual vocal removal not supported. Please use web services first.")
                        result = None
                    elif choice == '3':
                        result = identify_with_acrcloud(audio_path, manual_key, manual_host)
                    else:
                        result = identify_with_acrcloud(audio_path, manual_key, manual_host)
                else:
                    print("❌ No credentials provided")
                    result = None
        else:
            # No .env credentials, ask for manual input
            manual_key = input("Enter ACRCloud API key: ").strip()
            manual_host = input("Enter ACRCloud host: ").strip()
            if manual_key and manual_host:
                if choice == '2':
                    print("🔇 Manual vocal removal not supported. Please use web services first.")
                    result = None
                elif choice == '3':
                    result = identify_with_acrcloud(audio_path, manual_key, manual_host)
                else:
                    result = identify_with_acrcloud(audio_path, manual_key, manual_host)
            else:
                print("❌ No credentials provided")
                result = None
        
        if result:
            print("\n🎵 ACRCloud Result:")
            print(json.dumps(result, indent=2))
    
    print("\n🎉 Process completed!")
    print("\n💡 Get free ACRCloud API key from: https://www.acrcloud.com/")

if __name__ == "__main__":
    main() 