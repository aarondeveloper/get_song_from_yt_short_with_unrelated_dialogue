# YouTube Short to Music Identification Pipeline

This project helps you identify songs from YouTube Shorts by downloading the video, removing speech/unrelated dialogue, and identifying the music using ACRCloud API.

## 🎯 Why This Project?

- **Better than Shazam**: ACRCloud API excels at identifying partially obscured music
- **Automatic speech removal**: Uses Demucs AI to separate vocals from music
- **Simple setup**: Only one API key needed (ACRCloud)
- **Free tier available**: ACRCloud offers free API access
- **Environment variables**: Secure API key storage using `.env` file

## 🚀 Quick Start

### Option 1: Full Automated Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (if not already installed)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html

# Create .env file with your ACRCloud credentials
echo "ACRCLOUD_ACCESS_KEY=your_access_key_here" > .env
echo "ACRCLOUD_ACCESS_SECRET=your_access_secret_here" >> .env
echo "ACRCLOUD_HOST=your_host_here" >> .env

# Run the full pipeline
python youtube_to_music_id.py "YOUR_YOUTUBE_SHORT_URL"
```

### Option 2: Simple Interactive Pipeline

```bash
# Install yt-dlp only
pip install yt-dlp

# Create .env file (optional - will prompt for credentials if not found)
echo "ACRCLOUD_ACCESS_KEY=your_access_key_here" > .env
echo "ACRCLOUD_ACCESS_SECRET=your_access_secret_here" >> .env
echo "ACRCLOUD_HOST=your_host_here" >> .env

# Run interactive script
python simple_pipeline.py
```

## 📋 Prerequisites

### Required Tools
- **yt-dlp**: YouTube downloader
- **ffmpeg**: Audio/video processing
- **demucs**: AI-powered audio separation (for full pipeline)

### API Key
- **ACRCloud**: https://www.acrcloud.com/ (Free tier available)

## 🔧 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download ffmpeg from https://ffmpeg.org/download.html and add to PATH

### 3. Get ACRCloud API Key

1. Go to https://www.acrcloud.com/
2. Sign up for a free account
3. Create a new project
4. Get your access key, access secret, and host from the project settings
5. Free tier available

### 4. Set Up Environment Variables

Create a `.env` file in the project directory:

```bash
# .env file
ACRCLOUD_ACCESS_KEY=your_acrcloud_access_key_here
ACRCLOUD_ACCESS_SECRET=your_acrcloud_access_secret_here
ACRCLOUD_HOST=your_acrcloud_host_here
```

**Example:**
```bash
ACRCLOUD_ACCESS_KEY=1234567890abcdef1234567890abcdef
ACRCLOUD_ACCESS_SECRET=abcdef1234567890abcdef1234567890
ACRCLOUD_HOST=identify-eu-west-1.acrcloud.com
```

## 🎵 Usage Examples

### Full Pipeline (using .env file)
```bash
python youtube_to_music_id.py "https://youtube.com/shorts/abc123"
```

### Full Pipeline (command line override)
```bash
python youtube_to_music_id.py "https://youtube.com/shorts/abc123" \
  --acrcloud-key YOUR_ACRCLOUD_KEY \
  --acrcloud-host identify-eu-west-1.acrcloud.com
```

### Keep Temporary Files
```bash
python youtube_to_music_id.py "URL" --keep-files
```

### Simple Interactive Mode
```bash
python simple_pipeline.py
```

## 🔄 How It Works

1. **Download**: Uses yt-dlp to download the YouTube Short
2. **Extract Audio**: Converts video to audio using ffmpeg
3. **Remove Speech**: Uses Demucs AI to separate vocals from music
4. **Convert**: Converts to MP3 format for API upload
5. **Identify**: Sends to ACRCloud API for song identification
6. **Results**: Displays song information including title, artist, album, and genre

## 🌐 Web-Based Alternatives

If you prefer manual steps or don't want to install all dependencies:

### Vocal Removal Services
- **Lalal.ai**: https://lalal.ai (High quality)
- **Moises.ai**: https://moises.ai (AI-powered)
- **VocalRemover.org**: https://vocalremover.org (Free)
- **Splitter.ai**: https://splitter.ai

### Manual Process
1. Download YouTube Short using yt-dlp
2. Extract audio using ffmpeg
3. Upload to vocal removal service
4. Download instrumental version
5. Use ACRCloud API to identify

## 📊 Why ACRCloud?

| Feature | ACRCloud | Shazam |
|---------|----------|--------|
| Free Tier | ✅ Available | ❌ Paid only |
| Obscured Music | ✅ Excellent | ❌ Poor |
| Response Time | Fast | Fast |
| Additional Data | Genre info, detailed metadata | Basic info |
| Setup Complexity | Medium | Simple |

## 🛠 Troubleshooting

### Common Issues

**"yt-dlp not found"**
```bash
pip install yt-dlp
```

**"ffmpeg not found"**
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from ffmpeg.org

**"demucs not found"**
```bash
pip install demucs
```

**API Key Errors**
- Verify your API key is correct in the `.env` file
- Check if you've exceeded free tier limits
- Ensure proper formatting (no extra spaces)
- Verify your host URL is correct

**No Song Found**
- Check if the music is clear enough after speech removal
- Try a different segment of the audio
- Verify your ACRCloud project is properly configured

### Performance Tips

- **Shorter videos**: Process faster and use less API quota
- **Clear music**: Better results when music is distinct from speech
- **Keep files**: Use `--keep-files` to inspect intermediate results

## 📁 File Structure

```
├── youtube_to_music_id.py    # Full automated pipeline
├── simple_pipeline.py        # Interactive simple pipeline
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── .env                     # Environment variables (create this)
└── temp/                    # Temporary files (created during processing)
    ├── video.mp4            # Downloaded video
    ├── audio.wav            # Extracted audio
    ├── audio.mp3            # MP3 version for API
    └── separated/           # Demucs output
        └── mdx_extra_q/
            └── audio/
                ├── vocals.wav
                └── no_vocals.wav
```

## 🔐 Environment Variables

The scripts automatically load API credentials from a `.env` file. Create this file in the project directory:

```bash
# .env file
ACRCLOUD_ACCESS_KEY=your_acrcloud_access_key_here
ACRCLOUD_ACCESS_SECRET=your_acrcloud_access_secret_here
ACRCLOUD_HOST=your_acrcloud_host_here
```

**Security Note**: Add `.env` to your `.gitignore` file to keep your API keys private.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Demucs**: Facebook Research for audio separation
- **yt-dlp**: Community-maintained YouTube downloader
- **ACRCloud**: Audio fingerprinting service 