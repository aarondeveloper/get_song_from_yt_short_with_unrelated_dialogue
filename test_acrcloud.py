#!/usr/bin/env python3
"""
Enhanced ACRCloud Test Script
Tests multiple 20-second segments from separated no-vocals audio
"""

import os
import json
import sys
import base64
import hashlib
import hmac
import time
import requests
import random
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
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

def find_no_vocals_audio():
    """Find the separated no-vocals audio file"""
    # Look for the no_vocals.mp3 file in the separated directory
    no_vocals_path = Path("separated/htdemucs/audio/no_vocals.mp3")
    
    if no_vocals_path.exists():
        print(f"✅ Found no-vocals audio: {no_vocals_path}")
        return no_vocals_path
    
    # Fallback to original audio if no separated file exists
    original_audio = Path("audio.mp3")
    if original_audio.exists():
        print(f"⚠️  No separated audio found, using original: {original_audio}")
        return original_audio
    
    print("❌ No audio files found!")
    print("💡 Run the pipeline first to download and separate audio")
    return None

def test_acrcloud_rest_api():
    """Test ACRCloud REST API with separated no-vocals audio segments"""
    
    # Check credentials
    access_key = os.getenv('ACRCLOUD_ACCESS_KEY')
    access_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
    host = os.getenv('ACRCLOUD_HOST')
    
    if not all([access_key, access_secret, host]):
        print("❌ Missing ACRCloud credentials!")
        print("💡 Set these in your .env file:")
        print("   ACRCLOUD_ACCESS_KEY=your_access_key")
        print("   ACRCLOUD_ACCESS_SECRET=your_access_secret")
        print("   ACRCLOUD_HOST=your_host")
        return False
    
    print("✅ ACRCloud credentials found")
    print(f"   Host: {host}")
    print(f"   Access Key: {access_key[:8]}...")
    print(f"   Access Secret: {access_secret[:8]}...")
    
    # Find the audio file to test with
    audio_file = find_no_vocals_audio()
    if not audio_file:
        return False
    
    # Get file size and duration
    sample_bytes = os.path.getsize(str(audio_file))
    duration = get_audio_duration(audio_file)
    
    print(f"📊 File size: {sample_bytes} bytes")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    
    # Always extract multiple segments for better testing
    print("📦 Extracting multiple 20-second segments for testing...")
    
    # Calculate how many segments we can extract
    max_segments = min(5, int(duration // 20))  # Test up to 5 segments
    if max_segments < 1:
        print("❌ Audio file too short to extract segments")
        return False
        
    print(f"🎯 Will test {max_segments} 20-second segments")
    
    # Generate start times (spread evenly across the audio)
    start_times = []
    available_duration = duration - 20  # Leave room for 20-second segment
    
    if available_duration <= 0:
        print("❌ Audio file too short")
        return False
    
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
        segment_path = Path(f"test_segment_{i+1}.mp3")
        
        # Extract segment
        if not extract_audio_segment(audio_file, segment_path, start_time, 20):
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
    print("📊 TEST RESULTS SUMMARY")
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
        
        return True
    else:
        print("❌ No music identified in any segment")
        print("\n💡 This could mean:")
        print("   • The audio contains mostly speech/dialogue")
        print("   • The music is too quiet or obscured")
        print("   • The song is not in ACRCloud's database")
        print("   • The audio quality is too low")
        print("   • The vocal removal didn't work well")
        return False

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
                    
                    # Extract song information
                    song_info = {
                        'title': music.get('title', 'Unknown'),
                        'artist': music.get('artists', [{}])[0].get('name', 'Unknown'),
                        'album': music.get('album', {}).get('name', 'Unknown'),
                        'genre': music.get('genres', [{}])[0].get('name', 'Unknown'),
                        'confidence': music.get('score', 'Unknown'),
                        'segment': segment_num
                    }
                    
                    print(f"   🎵 Title: {song_info['title']}")
                    print(f"   👤 Artist: {song_info['artist']}")
                    print(f"   📀 Album: {song_info['album']}")
                    print(f"   🎼 Genre: {song_info['genre']}")
                    print(f"   🎯 Confidence: {song_info['confidence']}")
                    
                    return song_info
                else:
                    print("⚠️  No music found in this segment")
                    return None
            else:
                print(f"❌ API Error: {status.get('msg', 'Unknown error')}")
                if status.get('code') == 3014:  # Invalid signature
                    print("💡 This might be a credential issue - check your .env file")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🧪 Enhanced ACRCloud Test with No-Vocals Audio")
    print("=" * 60)
    
    success = test_acrcloud_rest_api()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed")
        print("\n💡 Troubleshooting tips:")
        print("1. Check your ACRCloud credentials in .env file")
        print("2. Verify your ACRCloud project is active")
        print("3. Run the pipeline first to download and separate audio")
        print("4. Check if the audio actually contains music")
        print("5. Try with a different YouTube Short")
        print("6. Verify your internet connection")

if __name__ == "__main__":
    main() 