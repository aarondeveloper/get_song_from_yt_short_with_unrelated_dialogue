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
    """Download YouTube Short using yt-dlp"""
    print(f"🎬 Downloading: {url}")
    
    try:
        cmd = [
            "yt-dlp",
            "-f", "b",  # Best pre-merged format (suppresses warning)
            "-o", "video.%(ext)s",
            url
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ Download completed!")
        
        # Find the downloaded file
        video_files = list(Path(".").glob("video.*"))
        if video_files:
            return video_files[0]
        else:
            print("❌ Could not find downloaded video file")
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

def main():
    print("🎵 YouTube Short to Music Identification - Simple Pipeline")
    print("=" * 60)
    
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
    
    # Download video
    video_path = download_with_yt_dlp(url)
    if not video_path:
        return
    
    # Extract audio
    audio_path = extract_audio_with_ffmpeg(video_path)
    if not audio_path:
        return
    
    print(f"\n✅ Audio extracted to: {audio_path}")
    
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
    print("2. Try ACRCloud API identification (automatic)")
    print("3. Both web services and API")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        open_web_services()
    
    if choice in ['2', '3']:
        print("\n🔑 ACRCloud API Identification:")
        
        # Use credentials from .env file or ask user
        if acrcloud_key and acrcloud_host:
            use_env = input("Use credentials from .env file? (y/n): ").strip().lower()
            if use_env == 'y':
                result = identify_with_acrcloud(audio_path)
            else:
                # Ask for manual input
                manual_key = input("Enter ACRCloud API key: ").strip()
                manual_host = input("Enter ACRCloud host: ").strip()
                if manual_key and manual_host:
                    result = identify_with_acrcloud(audio_path, manual_key, manual_host)
                else:
                    print("❌ No credentials provided")
                    result = None
        else:
            # No .env credentials, ask for manual input
            manual_key = input("Enter ACRCloud API key: ").strip()
            manual_host = input("Enter ACRCloud host: ").strip()
            if manual_key and manual_host:
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