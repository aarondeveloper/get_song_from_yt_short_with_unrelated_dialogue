#!/usr/bin/env python3
"""
Simple YouTube Short to Music Identification Pipeline
Uses ACRCloud API for reliable song identification
"""

import webbrowser
import subprocess
import sys
import requests
import json
import os
import base64
import hashlib
import hmac
import time
import random
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
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        print("⚠️  Could not determine audio duration, assuming 60 seconds")
        return 60.0

def extract_audio_segment(input_path, output_path, start_time, duration=20):
    """Extract a segment from audio file using ffmpeg"""
    try:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c", "copy",  # Copy without re-encoding for speed
            "-y",  # Overwrite output file
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to extract segment: {e}")
        return False

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

def identify_with_acrcloud_improved(audio_path, access_key=None, access_secret=None, host=None):
    """Identify song using enhanced ACRCloud REST API with multiple segment testing"""
    # Use provided values or fall back to environment variables
    access_key = access_key or os.getenv('ACRCLOUD_ACCESS_KEY')
    access_secret = access_secret or os.getenv('ACRCLOUD_ACCESS_SECRET')
    host = host or os.getenv('ACRCLOUD_HOST')
    
    if not access_key or not access_secret or not host:
        print("❌ ACRCloud credentials not found!")
        print("💡 Set ACRCLOUD_ACCESS_KEY, ACRCLOUD_ACCESS_SECRET, and ACRCLOUD_HOST in your .env file")
        return None
    
    print("🎵 Identifying with ACRCloud REST API...")
    print(f"📁 Using audio file: {audio_path}")
    
    # Get file size and duration
    sample_bytes = os.path.getsize(str(audio_path))
    duration = get_audio_duration(audio_path)
    
    print(f"📊 File size: {sample_bytes} bytes")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    
    # Always extract multiple segments for better testing
    print("📦 Extracting multiple 20-second segments for testing...")
    
    # Calculate how many segments we can extract
    max_segments = min(5, int(duration // 20))  # Test up to 5 segments
    if max_segments < 1:
        print("❌ Audio file too short to extract segments")
        return None
        
    print(f"🎯 Will test {max_segments} 20-second segments")
    
    # Generate start times (spread evenly across the audio)
    start_times = []
    available_duration = duration - 20  # Leave room for 20-second segment
    
    if available_duration <= 0:
        print("❌ Audio file too short")
        return None
    
    # Generate evenly spaced start times
    for i in range(max_segments):
        # Spread segments across the audio, avoiding the very beginning and end
        start_time = 5 + (i * (available_duration - 10) / max_segments)
        start_times.append(start_time)
    
    print(f"🎵 Segment start times: {[f'{t:.1f}s' for t in start_times]}")
    
    # Test each segment
    results = []
    for i, start_time in enumerate(start_times):
        print(f"\n🎵 Testing segment {i+1}/{max_segments} (starting at {start_time:.1f}s)...")
        
        # Create temporary segment file
        segment_path = Path(f"segment_{i+1}.mp3")
        
        # Extract segment
        if not extract_audio_segment(audio_path, segment_path, start_time, 20):
            print(f"❌ Failed to extract segment {i+1}")
            continue
        
        # Test this segment
        result = test_single_segment(segment_path, access_key, access_secret, host, i+1)
        
        # Clean up segment file
        try:
            segment_path.unlink()
        except:
            pass
        
        if result:
            results.append(result)
    
    # Display summary of results
    print("\n" + "="*60)
    print("📊 IDENTIFICATION RESULTS")
    print("="*60)
    
    if results:
        print(f"✅ Found {len(results)} successful matches!")
        print()
        
        # Group by song (in case multiple segments match the same song)
        unique_songs = {}
        for result in results:
            song_key = f"{result['title']}_{result['artist']}"
            if song_key not in unique_songs:
                unique_songs[song_key] = result
            else:
                # Keep the one with higher confidence
                if result['confidence'] > unique_songs[song_key]['confidence']:
                    unique_songs[song_key] = result
        
        print(f"🎵 Unique songs found: {len(unique_songs)}")
        print()
        
        for i, (song_key, song) in enumerate(unique_songs.items(), 1):
            print(f"🎵 Song {i}:")
            print(f"   Title: {song['title']}")
            print(f"   Artist: {song['artist']}")
            print(f"   Album: {song['album']}")
            print(f"   Genre: {song['genre']}")
            print(f"   Confidence: {song['confidence']}")
            print(f"   Matched in segment: {song['segment']}")
            print()
        
        # Return the best match (highest confidence)
        best_match = max(unique_songs.values(), key=lambda x: x['confidence'])
        return best_match
    else:
        print("❌ No music identified in any segment")
        print("\n💡 This could mean:")
        print("   • The audio contains mostly speech/dialogue")
        print("   • The music is too quiet or obscured")
        print("   • The song is not in ACRCloud's database")
        print("   • The audio quality is too low")
        print("   • The vocal removal didn't work well")
        return None

def test_single_segment(audio_path, access_key, access_secret, host, segment_num):
    """Test a single audio segment with ACRCloud"""
    try:
        # Build the request URL
        requrl = f"https://{host}/v1/identify"
        
        # HTTP method and URI
        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        timestamp = time.time()
        
        # Create signature string
        string_to_sign = (http_method + "\n" + http_uri + "\n" + access_key + "\n" + 
                         data_type + "\n" + signature_version + "\n" + str(timestamp))
        
        # Generate signature
        sign = base64.b64encode(
            hmac.new(access_secret.encode('ascii'), 
                    string_to_sign.encode('ascii'),
                    digestmod=hashlib.sha1).digest()
        ).decode('ascii')
        
        # Get file size
        sample_bytes = os.path.getsize(str(audio_path))
        
        # Prepare files and data for upload
        files = [
            ('sample', (audio_path.name, open(str(audio_path), 'rb'), 'audio/mpeg'))
        ]
        
        data = {
            'access_key': access_key,
            'sample_bytes': sample_bytes,
            'timestamp': str(timestamp),
            'signature': sign,
            'data_type': data_type,
            'signature_version': signature_version
        }
        
        print(f"📤 Uploading {sample_bytes} bytes to ACRCloud...")
        
        # Make the request
        r = requests.post(requrl, files=files, data=data, timeout=30)
        r.encoding = "utf-8"
        
        # Parse JSON response
        try:
            result = json.loads(r.text)
            
            # Check status
            status = result.get('status', {})
            if status.get('code') == 0:
                if result.get('metadata', {}).get('music'):
                    print("✅ SUCCESS: Song identified!")
                    music = result['metadata']['music'][0]
                    print(f"🎵 Title: {music.get('title', 'Unknown')}")
                    print(f"👤 Artist: {music.get('artists', [{}])[0].get('name', 'Unknown')}")
                    print(f"📀 Album: {music.get('album', {}).get('name', 'Unknown')}")
                    print(f"🎼 Genre: {music.get('genres', [{}])[0].get('name', 'Unknown')}")
                    print(f"🎯 Confidence: {music.get('score', 'Unknown')}")
                    return {
                        'title': music.get('title', 'Unknown'),
                        'artist': music.get('artists', [{}])[0].get('name', 'Unknown'),
                        'album': music.get('album', {}).get('name', 'Unknown'),
                        'genre': music.get('genres', [{}])[0].get('name', 'Unknown'),
                        'confidence': music.get('score', 'Unknown'),
                        'segment': segment_num
                    }
                else:
                    print("⚠️  No music found in this segment")
                    return None
            else:
                print(f"❌ API Error: {status.get('msg', 'Unknown error')}")
                if status.get('code') == 3014:  # Invalid signature
                    print("💡 This might be a credential issue - check your .env file")
                    print("💡 Make sure you're using the Access Key (not Secret Key) from ACRCloud")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

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
    print("🎵 YouTube Short to Music Identification")
    print("=" * 50)
    
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
    acrcloud_key = os.getenv('ACRCLOUD_ACCESS_KEY')
    acrcloud_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
    acrcloud_host = os.getenv('ACRCLOUD_HOST')
    
    if acrcloud_key and acrcloud_secret and acrcloud_host:
        print(f"✅ ACRCloud credentials found in .env file")
        print(f"   Host: {acrcloud_host}")
    else:
        print("⚠️  ACRCloud credentials not found in .env file")
    
    print("\n🎯 Choose your approach:")
    print("1. 🎵 Use original audio with ACRCloud")
    print("2. 🔇 Remove vocals with Demucs, then use ACRCloud")
    
    choice = input("\nEnter your choice (1-2): ").strip()
    
    if choice == "1":
        # Use original audio
        print("\n🎵 Identifying with original audio...")
        print(f"🎯 Using original audio file: {audio_path}")
        result = identify_with_acrcloud_improved(audio_path)
    
    elif choice == "2":
        # Remove vocals first
        print("\n🔇 Step 1: Removing vocals with Demucs...")
        no_vocals_path = remove_speech_demucs(audio_path)
        
        if not no_vocals_path or not no_vocals_path.exists():
            print("❌ Could not remove vocals")
            print("💡 Falling back to original audio...")
            no_vocals_path = audio_path
        
        # Identify with processed audio
        print("\n🎵 Step 2: Identifying song...")
        print(f"🎯 Using vocals-removed file: {no_vocals_path}")
        result = identify_with_acrcloud_improved(no_vocals_path)
    
    else:
        print("❌ Invalid choice")
        return
    
    # Handle results
    if result:
        print("\n🎉 SUCCESS! Song identified:")
        print("=" * 40)
        print(f"🎵 Title: {result.get('title', 'Unknown')}")
        print(f"👤 Artist: {result.get('artist', 'Unknown')}")
        print(f"📀 Album: {result.get('album', 'Unknown')}")
        print(f"🎼 Genre: {result.get('genre', 'Unknown')}")
        print(f"🎯 Confidence: {result.get('confidence', 'Unknown')}")
        print("=" * 40)
    else:
        print("\n❌ No music identified")
        print("\n💡 This could mean:")
        print("   • The audio contains mostly speech/dialogue")
        print("   • The music is too quiet or obscured")
        print("   • The song is not in ACRCloud's database")
        print("   • The audio quality is too low")
        
        print("\n🔄 Try these solutions:")
        print("   1. Try option 2 (remove vocals first)")
        print("   2. Try with a different YouTube Short")
        print("   3. Check if the audio actually contains music")
    
    print("\n🎉 Process completed!")
    print("\n💡 Get free ACRCloud API key from: https://www.acrcloud.com/")

if __name__ == "__main__":
    main() 