#!/usr/bin/env python3
"""
Test script for ACRCloud REST API functionality
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

def test_acrcloud_rest_api():
    """Test ACRCloud REST API with a sample audio file"""
    
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
    
    # Check if we have an audio file to test with
    audio_files = list(Path(".").glob("*.mp3"))
    if not audio_files:
        print("❌ No MP3 files found for testing")
        print("💡 Run the pipeline first to download an audio file")
        return False
    
    test_file = audio_files[0]
    print(f"🎵 Testing with: {test_file}")
    
    # Get file size and duration
    sample_bytes = os.path.getsize(str(test_file))
    duration = get_audio_duration(test_file)
    
    print(f"📊 File size: {sample_bytes} bytes")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    
    # Check if we need to chunk the file
    if sample_bytes > 1024 * 1024 or duration > 60:  # 1MB or >60 seconds
        print("📦 File is large, extracting multiple 20-second segments...")
        
        # Calculate how many segments we can extract
        max_segments = min(2, int(duration // 20))  # Changed from 5 to 2
        if max_segments < 1:
            print("❌ Audio file too short to extract segments")
            return False
            
        print(f"🎯 Will test {max_segments} random 20-second segments")
        
        # Generate random start times (avoiding the very beginning and end)
        available_duration = duration - 20  # Leave room for 20-second segment
        if available_duration <= 0:
            print("❌ Audio file too short")
            return False
            
        # Generate random start times
        start_times = []
        for i in range(max_segments):
            start_time = random.uniform(5, available_duration - 5)  # Avoid very beginning/end
            start_times.append(start_time)
        
        # Test each segment
        for i, start_time in enumerate(start_times):
            print(f"\n🎵 Testing segment {i+1}/{max_segments} (starting at {start_time:.1f}s)...")
            
            # Create temporary segment file
            segment_path = Path(f"test_segment_{i+1}.mp3")
            
            # Extract segment
            if not extract_audio_segment(test_file, segment_path, start_time, 20):
                print(f"❌ Failed to extract segment {i+1}")
                continue
            
            # Test this segment
            success = test_single_segment(segment_path, access_key, access_secret, host)
            
            # Clean up segment file
            try:
                segment_path.unlink()
            except:
                pass
            
            if success:
                print(f"✅ Success with segment {i+1}!")
                return True
        
        print("\n❌ No segments matched")
        return False
    else:
        # File is small enough, test directly
        return test_single_segment(test_file, access_key, access_secret, host)

def test_single_segment(audio_path, access_key, access_secret, host):
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
        
        # Debug: Show signature components
        print(f"🔍 Debug - Signature components:")
        print(f"   HTTP Method: {http_method}")
        print(f"   HTTP URI: {http_uri}")
        print(f"   Access Key: {access_key}")
        print(f"   Data Type: {data_type}")
        print(f"   Signature Version: {signature_version}")
        print(f"   Timestamp: {timestamp}")
        print(f"   String to sign: {repr(string_to_sign)}")
        
        # Generate signature
        sign = base64.b64encode(
            hmac.new(access_secret.encode('ascii'), 
                    string_to_sign.encode('ascii'),
                    digestmod=hashlib.sha1).digest()
        ).decode('ascii')
        
        print(f"   Generated Signature: {sign}")
        
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
        
        print(f"📤 Uploading {sample_bytes} bytes to: {requrl}")
        
        # Make the request
        r = requests.post(requrl, files=files, data=data, timeout=30)
        r.encoding = "utf-8"
        
        print(f"📄 Response status: {r.status_code}")
        print(f"📄 Response text: {r.text}")
        
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
                    return True
                else:
                    print("⚠️  No music found in this segment")
                    return False
            else:
                print(f"❌ API Error: {status.get('msg', 'Unknown error')}")
                if status.get('code') == 3014:  # Invalid signature
                    print("💡 This might be a credential issue - check your .env file")
                    print("💡 Make sure you're using the Access Key (not Secret Key) from ACRCloud")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 ACRCloud REST API Test")
    print("=" * 40)
    
    success = test_acrcloud_rest_api()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed")
        print("\n💡 Troubleshooting tips:")
        print("1. Check your ACRCloud credentials in .env file")
        print("2. Verify your ACRCloud project is active")
        print("3. Make sure you have an MP3 file to test with")
        print("4. Check your internet connection")
        print("5. Verify the audio file is not corrupted")
        print("6. Try with a different audio file")

if __name__ == "__main__":
    main() 