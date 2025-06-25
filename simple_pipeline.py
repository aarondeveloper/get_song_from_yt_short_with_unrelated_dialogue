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

def remove_speech_demucs(audio_path):
    """Remove vocals using local Demucs (Python API, fallback to subprocess)"""
    print("🔇 Removing vocals using local Demucs...")
    try:
        import demucs.separate
        # Use the recommended model for best quality, output as MP3
        args = [
            "--two-stems", "vocals",
            "-n", "htdemucs",
            "--mp3",  # Output as MP3 instead of WAV
            str(audio_path)
        ]
        print(f"⚡ Running: demucs {' '.join(args)}")
        demucs.separate.main(args)
        # Find the output file (Demucs creates it in separated/htdemucs/audio_name/)
        audio_name = Path(audio_path).stem
        no_vocals_path = Path("separated") / "htdemucs" / audio_name / "no_vocals.mp3"
        if no_vocals_path.exists():
            print(f"✅ Vocals removed: {no_vocals_path}")
            return no_vocals_path
        else:
            print(f"❌ Could not find {no_vocals_path}, trying subprocess fallback...")
    except Exception as e:
        print(f"⚠️  Demucs Python API failed: {e}")
        print("🔄 Trying subprocess fallback...")
    # Subprocess fallback
    try:
        import subprocess
        cmd = [
            "demucs",
            "--two-stems", "vocals",
            "-n", "htdemucs",
            "--mp3",  # Output as MP3 instead of WAV
            str(audio_path)
        ]
        print(f"⚡ Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        audio_name = Path(audio_path).stem
        no_vocals_path = Path("separated") / "htdemucs" / audio_name / "no_vocals.mp3"
        if no_vocals_path.exists():
            print(f"✅ Vocals removed: {no_vocals_path}")
            return no_vocals_path
        else:
            print(f"❌ Could not find {no_vocals_path}")
            return None
    except Exception as e:
        print(f"❌ Demucs subprocess also failed: {e}")
        return None

def remove_speech(audio_path):
    """Remove vocals using local Demucs only"""
    return remove_speech_demucs(audio_path)

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
        ("Hugging Face Demucs v4 - Best quality (recommended)", "https://huggingface.co/spaces/abidlabs/music-separation"),
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
    print("3. Download the instrumental version (no_vocals.wav)")
    print("4. Use the ACRCloud API identification option below")
    
    choice = input("\nOpen which service? (1-5, or press Enter to skip): ").strip()
    
    if choice in ['1', '2', '3', '4', '5']:
        service_url = services[int(choice) - 1][1]
        webbrowser.open(service_url)
        print(f"✅ Opened {service_url}")
        
        if choice == '1':
            print("\n💡 Hugging Face Demucs v4 Tips:")
            print("   - This uses the same Demucs v4 model we were trying to install")
            print("   - Upload your audio.mp3 file")
            print("   - Download the 'no_vocals.wav' file")
            print("   - Place it in your current directory")
            print("   - Use option 3 (ACRCloud with original audio) and manually specify the file")

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
    
    print("\n🎯 Starting automated music identification pipeline...")
    
    # Step 1: Remove vocals using local Demucs
    print("\n🔇 Step 1: Removing vocals...")
    no_vocals_path = remove_speech(audio_path)
    
    if not no_vocals_path or not no_vocals_path.exists():
        print("❌ Could not remove vocals")
        print("💡 Trying with original audio...")
        no_vocals_path = audio_path
    
    # Step 2: Identify song with ACRCloud
    print("\n🎵 Step 2: Identifying song...")
    
    if acrcloud_key and acrcloud_host:
        result = identify_with_acrcloud(no_vocals_path)
    else:
        # Ask for manual input
        print("🔑 Enter ACRCloud credentials:")
        manual_key = input("API Key: ").strip()
        manual_host = input("Host: ").strip()
        if manual_key and manual_host:
            result = identify_with_acrcloud(no_vocals_path, manual_key, manual_host)
        else:
            print("❌ No credentials provided")
            result = None
    
    if result:
        print("\n🎵 Song Information:")
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ Could not identify the song")
    
    print("\n🎉 Process completed!")
    print("\n💡 Get free ACRCloud API key from: https://www.acrcloud.com/")

if __name__ == "__main__":
    main() 