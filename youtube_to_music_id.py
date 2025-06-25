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
        """Download YouTube Short using yt-dlp"""
        print(f"🎬 Downloading YouTube Short: {url}")
        
        try:
            # Download video with better headers (no cookies to avoid issues)
            cmd = [
                "yt-dlp",
                "-f", "best",  # Use best available format
                "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "--no-check-certificates",  # Skip certificate verification
                "--extractor-args", "youtube:player_client=web",  # Use web client
                "-o", str(self.temp_dir / "video.%(ext)s"),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Video downloaded successfully")
            
            # Find the downloaded file
            video_files = list(self.temp_dir.glob("video.*"))
            if video_files:
                return video_files[0]
            else:
                raise FileNotFoundError("Downloaded video file not found")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading video: {e}")
            print(f"Error output: {e.stderr}")
            
            # Try alternative download method with any available format
            print("🔄 Trying alternative download method...")
            try:
                alt_cmd = [
                    "yt-dlp",
                    "-f", "worst",  # Try worst quality (most likely to work)
                    "--no-check-certificates",
                    "--extractor-args", "youtube:player_client=web",
                    "-o", str(self.temp_dir / "video.%(ext)s"),
                    url
                ]
                
                result = subprocess.run(alt_cmd, capture_output=True, text=True, check=True)
                print("✅ Video downloaded successfully with alternative method")
                
                # Find the downloaded file
                video_files = list(self.temp_dir.glob("video.*"))
                if video_files:
                    return video_files[0]
                else:
                    raise FileNotFoundError("Downloaded video file not found")
                    
            except subprocess.CalledProcessError as e2:
                print(f"❌ Alternative download also failed: {e2}")
                print(f"Error output: {e2.stderr}")
                
                # Try one more time with no format restrictions
                print("🔄 Trying with no format restrictions...")
                try:
                    final_cmd = [
                        "yt-dlp",
                        "--no-check-certificates",
                        "-o", str(self.temp_dir / "video.%(ext)s"),
                        url
                    ]
                    
                    result = subprocess.run(final_cmd, capture_output=True, text=True, check=True)
                    print("✅ Video downloaded successfully with no format restrictions")
                    
                    # Find the downloaded file
                    video_files = list(self.temp_dir.glob("video.*"))
                    if video_files:
                        return video_files[0]
                    else:
                        raise FileNotFoundError("Downloaded video file not found")
                        
                except subprocess.CalledProcessError as e3:
                    print(f"❌ All download methods failed: {e3}")
                    print(f"Error output: {e3.stderr}")
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
    
    def remove_speech(self, audio_path):
        """Remove speech using Demucs"""
        print("🔇 Removing speech using Demucs...")
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
            demucs_output = self.temp_dir / "separated" / "mdx_extra_q" / "audio"
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
        
        # Step 1: Download YouTube Short
        video_path = self.download_youtube_short(youtube_url)
        if not video_path:
            return False
        
        # Step 2: Extract audio
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return False
        
        # Step 3: Remove speech
        music_path = self.remove_speech(audio_path)
        if not music_path:
            return False
        
        # Step 4: Convert to MP3 for API upload
        mp3_path = self.convert_to_mp3(music_path)
        if not mp3_path:
            return False
        
        # Step 5: Identify song with ACRCloud
        song_info = self.identify_song_acrcloud(mp3_path)
        
        # Step 6: Cleanup (optional)
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
    required_tools = ["yt-dlp", "ffmpeg", "demucs"]
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
        print("   pip install yt-dlp demucs")
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