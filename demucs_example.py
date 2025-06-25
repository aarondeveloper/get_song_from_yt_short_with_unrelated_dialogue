#!/usr/bin/env python3
"""
Simple example of using Demucs Python API for vocal removal
"""

import sys
from pathlib import Path

def remove_vocals_with_demucs_api(input_audio_path):
    """
    Remove vocals from audio using Demucs Python API
    
    Args:
        input_audio_path (str or Path): Path to input audio file
        
    Returns:
        Path: Path to the separated audio file (no_vocals.wav)
    """
    print(f"🎵 Processing: {input_audio_path}")
    
    try:
        # Import demucs
        import demucs.separate
        
        # Create output directory
        output_dir = Path("separated")
        output_dir.mkdir(exist_ok=True)
        
        print("🔇 Separating vocals using Demucs...")
        print("⚠️  This may take a few minutes depending on audio length...")
        
        # Run Demucs using the Python API
        # This is equivalent to: demucs --two-stems=vocals input_audio.mp3
        demucs.separate.main([
            "--two-stems=vocals",  # Separate vocals from the rest
            "-o", str(output_dir),  # Output directory
            str(input_audio_path)   # Input audio file
        ])
        
        # Find the separated audio file
        # Demucs creates output in: separated/htdemucs/audio_name/no_vocals.wav
        model_name = "htdemucs"  # Default model
        audio_name = Path(input_audio_path).stem
        no_vocals_path = output_dir / model_name / audio_name / "no_vocals.wav"
        
        if no_vocals_path.exists():
            print(f"✅ Vocals removed successfully!")
            print(f"📁 Output file: {no_vocals_path}")
            return no_vocals_path
        else:
            print("❌ Could not find separated audio file")
            return None
            
    except ImportError:
        print("❌ Demucs not installed. Installing...")
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "demucs"], check=True)
            print("✅ Demucs installed successfully")
            # Try again
            return remove_vocals_with_demucs_api(input_audio_path)
        except subprocess.CalledProcessError:
            print("❌ Failed to install Demucs")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Example usage"""
    print("🎵 Demucs Python API Example")
    print("=" * 40)
    
    # Check if audio file is provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        # Default to audio.mp3 if it exists
        audio_file = "audio.mp3"
        if not Path(audio_file).exists():
            print("❌ No audio file provided and audio.mp3 not found")
            print("💡 Usage: python demucs_example.py <audio_file>")
            print("💡 Or place an audio file named 'audio.mp3' in the current directory")
            return
    
    # Check if file exists
    if not Path(audio_file).exists():
        print(f"❌ File not found: {audio_file}")
        return
    
    # Remove vocals
    result = remove_vocals_with_demucs_api(audio_file)
    
    if result:
        print(f"\n🎉 Success! Vocals removed from {audio_file}")
        print(f"📁 Instrumental version saved to: {result}")
        print("\n💡 You can now use this file for music identification!")
    else:
        print("\n❌ Failed to remove vocals")

if __name__ == "__main__":
    main() 