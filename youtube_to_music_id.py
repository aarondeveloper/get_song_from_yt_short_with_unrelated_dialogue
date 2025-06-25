#!/usr/bin/env python3
"""
YouTube Short to Music Identification Pipeline
Downloads a YouTube Short, removes speech, and identifies the music using ACRCloud API
"""

import os
import sys
import subprocess
import requests
import json
import time
from pathlib import Path
from urllib.parse import urlparse
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class YouTubeToMusicID:
    def __init__(self, acrcloud_api_key=None, acrcloud_host=None):
        # Use provided values or fall back to environment variables
        self.acrcloud_api_key = acrcloud_api_key or os.getenv('ACRCLOUD_API_KEY')
        self.acrcloud_host = acrcloud_host or os.getenv('ACRCLOUD_HOST')
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
    def download_youtube_short(self, url):
        """Download YouTube Short audio directly as MP3 using yt-dlp"""
        print(f"🎬 Downloading audio from YouTube Short: {url}")
        
        try:
            # Download audio directly as MP3
            cmd = [
                "yt-dlp",
                "-x",  # Extract audio only
                "--audio-format", "mp3",  # Convert to MP3
                "--audio-quality", "0",  # Best quality
                "-o", str(self.temp_dir / "audio.%(ext)s"),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Audio downloaded successfully")
            
            # Find the downloaded audio file
            audio_files = list(self.temp_dir.glob("audio.*"))
            if audio_files:
                return audio_files[0]
            else:
                raise FileNotFoundError("Downloaded audio file not found")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading audio: {e}")
            print(f"Error output: {e.stderr}")
            return None
    
    def extract_audio(self, video_path):
        """Extract audio from video using ffmpeg"""
        print("🎵 Extracting audio from video...")
        
        audio_path = self.temp_dir / "audio.wav"
        
        try:
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "44100",  # 44.1kHz sample rate
                "-ac", "2",  # Stereo
                "-y",  # Overwrite output file
                str(audio_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            print("✅ Audio extracted successfully")
            return audio_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error extracting audio: {e}")
            return None
    
    def remove_speech_demucs_api(self, audio_path):
        """Remove speech using Demucs Python API"""
        print("🔇 Removing speech using Demucs...")
        print("⚠️  This may take a few minutes depending on audio length...")
        
        try:
            # Import demucs
            import demucs.separate
            
            # Create output directory for Demucs
            demucs_output = self.temp_dir / "separated"
            demucs_output.mkdir(exist_ok=True)
            
            # Run Demucs using the Python API
            # This is equivalent to: demucs --two-stems=vocals audio.wav
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
                return self.remove_speech_demucs_api(audio_path)
            except subprocess.CalledProcessError:
                print("❌ Failed to install Demucs")
                return None
        except Exception as e:
            print(f"❌ Error removing speech with Demucs API: {e}")
            return None
    
    def remove_speech_subprocess(self, audio_path):
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
            demucs_output = self.temp_dir / "separated" / "htdemucs" / audio_path.stem
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
    
    def remove_speech(self, audio_path):
        """Remove speech using Demucs (tries API first, then subprocess)"""
        # Try Python API first
        result = self.remove_speech_demucs_api(audio_path)
        if result:
            return result
        
        # Fallback to subprocess
        print("🔄 Falling back to subprocess method...")
        return self.remove_speech_subprocess(audio_path)
    
    def convert_to_mp3(self, audio_path):
        """Convert audio to MP3 format for API upload"""
        print("🔄 Converting to MP3...")
        
        mp3_path = self.temp_dir / "audio.mp3"
        
        try:
            cmd = [
                "ffmpeg",
                "-i", str(audio_path),
                "-acodec", "mp3",
                "-ab", "192k",  # 192kbps bitrate
                "-y",
                str(mp3_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            print("✅ Converted to MP3 successfully")
            return mp3_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error converting to MP3: {e}")
            return None
    
    def identify_song_acrcloud(self, audio_path):
        """Identify song using ACRCloud API"""
        if not self.acrcloud_api_key or not self.acrcloud_host:
            print("⚠️  No ACRCloud API key or host provided.")
            print("💡 Set ACRCLOUD_API_KEY and ACRCLOUD_HOST in your .env file or use command line arguments")
            return None
        
        print("🎵 Identifying song with ACRCloud...")
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # ACRCloud requires specific headers and signature
            import hashlib
            import hmac
            import base64
            import time
            
            # Create signature
            timestamp = str(int(time.time()))
            http_method = "POST"
            http_uri = "/v1/identify"
            data_type = "audio"
            signature_version = "1"
            
            string_to_sign = '\n'.join([http_method, http_uri, self.acrcloud_api_key, data_type, signature_version, timestamp])
            sign = base64.b64encode(hmac.new(self.acrcloud_api_key.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()).decode('ascii')
            
            headers = {
                'access-key': self.acrcloud_api_key,
                'signature': sign,
                'signature-version': signature_version,
                'timestamp': timestamp,
                'data-type': data_type
            }
            
            files = {'sample': audio_data}
            
            url = f"https://{self.acrcloud_host}/v1/identify"
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
                    print("❌ No song match found with ACRCloud")
                    return None
            else:
                print(f"❌ ACRCloud API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error identifying song with ACRCloud: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        print("🧹 Cleaning up temporary files...")
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def run_pipeline(self, youtube_url, keep_files=False):
        """Run the complete pipeline"""
        print("🚀 Starting YouTube Short to Music Identification Pipeline")
        print("=" * 60)
        
        # Step 1: Download YouTube Short audio directly
        audio_path = self.download_youtube_short(youtube_url)
        if not audio_path:
            return False
        
        # Step 2: Remove speech
        music_path = self.remove_speech(audio_path)
        if not music_path:
            return False
        
        # Step 3: Convert to MP3 for API upload (if needed)
        mp3_path = self.convert_to_mp3(music_path)
        if not mp3_path:
            return False
        
        # Step 4: Identify song with ACRCloud
        song_info = self.identify_song_acrcloud(mp3_path)
        
        # Step 5: Cleanup (optional)
        if not keep_files:
            self.cleanup()
        else:
            print(f"📁 Files kept in: {self.temp_dir}")
        
        print("=" * 60)
        print("🎉 Pipeline completed!")
        
        return song_info

def main():
    parser = argparse.ArgumentParser(description="YouTube Short to Music Identification Pipeline")
    parser.add_argument("url", help="YouTube Short URL")
    parser.add_argument("--acrcloud-key", help="ACRCloud API key (overrides .env file)")
    parser.add_argument("--acrcloud-host", help="ACRCloud host (overrides .env file)")
    parser.add_argument("--keep-files", action="store_true", help="Keep temporary files")
    
    args = parser.parse_args()
    
    # Check if required tools are installed
    required_tools = ["yt-dlp", "ffmpeg"]
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print("❌ Missing required tools:")
        for tool in missing_tools:
            print(f"   - {tool}")
        print("\n📦 Install missing tools:")
        print("   pip install yt-dlp")
        print("   # Install ffmpeg from: https://ffmpeg.org/download.html")
        return
    
    # Initialize pipeline
    pipeline = YouTubeToMusicID(
        acrcloud_api_key=args.acrcloud_key,
        acrcloud_host=args.acrcloud_host
    )
    
    # Check if API credentials are available
    if not pipeline.acrcloud_api_key or not pipeline.acrcloud_host:
        print("❌ ACRCloud API credentials not found!")
        print("💡 Create a .env file with:")
        print("   ACRCLOUD_API_KEY=your_api_key_here")
        print("   ACRCLOUD_HOST=your_host_here")
        print("\nOr use command line arguments:")
        print("   --acrcloud-key YOUR_KEY --acrcloud-host YOUR_HOST")
        return
    
    # Run pipeline
    result = pipeline.run_pipeline(args.url, keep_files=args.keep_files)
    
    if result:
        print("\n🎵 Song Information:")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 