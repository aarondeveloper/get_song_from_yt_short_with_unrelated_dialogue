# Demucs Integration Guide

This guide explains how to integrate Demucs v4 directly into your Python code for vocal removal, instead of using subprocess calls.

## What is Demucs?

Demucs is a state-of-the-art audio source separation tool that can separate vocals from music. Demucs v4 uses a Hybrid Transformer architecture and provides excellent quality for vocal removal.

## Installation

```bash
pip install demucs
```

## Basic Integration

### Method 1: Using Demucs Python API (Recommended)

```python
import demucs.separate
from pathlib import Path

def remove_vocals_api(audio_path):
    """Remove vocals using Demucs Python API"""
    try:
        # Create output directory
        output_dir = Path("separated")
        output_dir.mkdir(exist_ok=True)
        
        # Run Demucs using the Python API
        # Equivalent to: demucs --two-stems=vocals audio.mp3
        demucs.separate.main([
            "--two-stems=vocals",  # Separate vocals from the rest
            "-o", str(output_dir),  # Output directory
            str(audio_path)        # Input audio file
        ])
        
        # Find the separated audio file
        model_name = "htdemucs"  # Default model
        audio_name = Path(audio_path).stem
        no_vocals_path = output_dir / model_name / audio_name / "no_vocals.wav"
        
        if no_vocals_path.exists():
            return no_vocals_path
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### Method 2: Using Subprocess (Fallback)

```python
import subprocess
from pathlib import Path

def remove_vocals_subprocess(audio_path):
    """Remove vocals using Demucs subprocess (fallback method)"""
    try:
        # Run Demucs command
        cmd = [
            "demucs",
            "--two-stems=vocals",
            str(audio_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Find the output file
        demucs_output = Path("separated") / "htdemucs" / Path(audio_path).stem
        no_vocals_path = demucs_output / "no_vocals.wav"
        
        if no_vocals_path.exists():
            return no_vocals_path
        else:
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None
```

### Method 3: Combined Approach (Best Practice)

```python
def remove_vocals(audio_path):
    """Remove vocals using Demucs (tries API first, then subprocess)"""
    # Try Python API first
    result = remove_vocals_api(audio_path)
    if result:
        return result
    
    # Fallback to subprocess
    print("Falling back to subprocess method...")
    return remove_vocals_subprocess(audio_path)
```

## Advanced Usage

### Custom Models

Demucs supports different models. The default is `htdemucs` (Hybrid Transformer), but you can specify others:

```python
# Use a different model
demucs.separate.main([
    "--two-stems=vocals",
    "--model", "mdx_extra_q",  # Alternative model
    "-o", str(output_dir),
    str(audio_path)
])
```

### Multiple Stems

You can separate into more than just vocals:

```python
# Separate into 4 stems: drums, bass, vocals, other
demucs.separate.main([
    "-o", str(output_dir),
    str(audio_path)
])

# This creates:
# - separated/htdemucs/audio_name/drums.wav
# - separated/htdemucs/audio_name/bass.wav
# - separated/htdemucs/audio_name/vocals.wav
# - separated/htdemucs/audio_name/other.wav
```

### GPU Acceleration

Demucs automatically uses GPU if available. You can force CPU usage:

```python
demucs.separate.main([
    "--two-stems=vocals",
    "--device", "cpu",  # Force CPU usage
    "-o", str(output_dir),
    str(audio_path)
])
```

## Integration in Our Pipeline

In our YouTube Short to Music Identification pipeline, we've integrated Demucs in two ways:

### 1. Full Automated Pipeline (`youtube_to_music_id.py`)

```python
def remove_speech_demucs_api(self, audio_path):
    """Remove speech using Demucs Python API"""
    try:
        import demucs.separate
        
        demucs_output = self.temp_dir / "separated"
        demucs_output.mkdir(exist_ok=True)
        
        demucs.separate.main([
            "--two-stems=vocals",
            "-o", str(demucs_output),
            str(audio_path)
        ])
        
        # Find output file
        model_name = "htdemucs"
        audio_name = audio_path.stem
        no_vocals_path = demucs_output / model_name / audio_name / "no_vocals.wav"
        
        if no_vocals_path.exists():
            return no_vocals_path
        else:
            return None
            
    except ImportError:
        # Auto-install if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "demucs"], check=True)
        return self.remove_speech_demucs_api(audio_path)
```

### 2. Simple Interactive Pipeline (`simple_pipeline.py`)

The simple pipeline offers users three options:
1. Manual vocal removal using web services
2. Automatic vocal removal using Demucs + ACRCloud API
3. Direct identification with original audio

## Benefits of Python API Integration

1. **Better Error Handling**: Direct exception handling instead of subprocess error codes
2. **Auto-Installation**: Can automatically install Demucs if not available
3. **Memory Efficiency**: Direct Python integration is more memory efficient
4. **Better Control**: More control over the separation process
5. **Fallback Support**: Can easily fall back to subprocess if API fails

## Performance Tips

1. **GPU Usage**: Demucs is much faster with GPU acceleration
2. **Batch Processing**: Process multiple files at once for better efficiency
3. **Model Selection**: `htdemucs` is the best quality but `mdx_extra_q` is faster
4. **Memory Management**: For large files, consider processing in chunks

## Troubleshooting

### Common Issues

1. **Import Error**: Install Demucs with `pip install demucs`
2. **CUDA Error**: Use `--device cpu` to force CPU usage
3. **Memory Error**: Process smaller audio chunks or use a smaller model
4. **Output Not Found**: Check the correct output path structure

### Debug Mode

Enable verbose output for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

demucs.separate.main([
    "--two-stems=vocals",
    "--verbose",
    "-o", str(output_dir),
    str(audio_path)
])
```

## Example Usage

See `demucs_example.py` for a complete working example:

```bash
python demucs_example.py audio.mp3
```

This will:
1. Load the audio file
2. Remove vocals using Demucs API
3. Save the instrumental version
4. Provide the path to the output file

## Integration Checklist

- [ ] Install Demucs: `pip install demucs`
- [ ] Test basic functionality with `demucs_example.py`
- [ ] Integrate into your pipeline using the API approach
- [ ] Add fallback to subprocess method
- [ ] Handle import errors and auto-installation
- [ ] Test with different audio formats and lengths
- [ ] Optimize for your specific use case

The integrated approach provides better reliability, error handling, and user experience compared to subprocess calls alone. 