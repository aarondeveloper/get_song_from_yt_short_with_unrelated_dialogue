# 🎵 YouTube Short to Music Identification Pipeline

A powerful tool to download YouTube Shorts, remove speech/dialogue, and identify background music using advanced audio recognition APIs.

## 🌟 Features

- **YouTube Short Download**: Direct audio extraction using yt-dlp
- **Vocal Removal**: Advanced AI-powered speech separation using Demucs v4
- **Music Identification**: Reliable song recognition using ACRCloud API
- **Multiple Segment Testing**: Tests up to 5 audio segments for better accuracy
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Easy Setup**: Simple installation and configuration

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (3.9+ recommended)
- **Git** (for cloning the repository)
- **Internet connection** (for downloads and API calls)

### API Requirements
- **ACRCloud Account**: Free tier available at [acrcloud.com](https://www.acrcloud.com/)

## 🚀 Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/youtube-short-music-finder.git
cd youtube-short-music-finder
```

### Step 2: Install Python Dependencies

The project uses several Python packages that are automatically installed via `requirements.txt`:

```bash
pip install -r requirements.txt
```

#### What's in requirements.txt?

The `requirements.txt` file contains all the necessary Python packages:

- **`yt-dlp`**: Advanced YouTube downloader for extracting audio from YouTube Shorts
- **`demucs`**: AI-powered audio separation model for removing vocals from music
- **`requests`**: HTTP library for making API calls to ACRCloud
- **`python-dotenv`**: Loads environment variables from `.env` file for secure API key storage
- **`pyacrcloud`**: Official ACRCloud Python SDK for music recognition

#### Manual Installation (Alternative)

If you prefer to install packages individually:

```bash
pip install yt-dlp demucs requests python-dotenv pyacrcloud
```

### Step 3: Set Up ACRCloud API

1. **Create ACRCloud Account**
   - Go to [acrcloud.com](https://www.acrcloud.com/)
   - Sign up for a free account
   - Verify your email

2. **Create a Project**
   - Log into your ACRCloud dashboard
   - Click "Create Project"
   - Choose "Audio Recognition" project type
   - Give it a name (e.g., "YouTube Music Finder")

3. **Get API Credentials**
   - In your project dashboard, go to "API Keys"
   - Copy the following information:
     - **Access Key** (not Secret Key)
     - **Access Secret**
     - **Host** (e.g., `identify-eu-west-1.acrcloud.com`)

4. **Create Environment File**
   ```bash
   # Create .env file in the project directory
   touch .env
   ```

   Add your credentials to `.env`:
   ```env
   ACRCLOUD_ACCESS_KEY=your_access_key_here
   ACRCLOUD_ACCESS_SECRET=your_access_secret_here
   ACRCLOUD_HOST=your_host_here
   ```

   **Example:**
   ```env
   ACRCLOUD_ACCESS_KEY=1234567890abcdef
   ACRCLOUD_ACCESS_SECRET=abcdef1234567890
   ACRCLOUD_HOST=identify-eu-west-1.acrcloud.com
   ```

## 🧠 Understanding Demucs

### What is Demucs?

**Demucs** is a state-of-the-art audio source separation model developed by Facebook Research. It uses deep learning to separate different audio sources from a mixed recording.

### Why Use Demucs for Music Identification?

1. **Speech Interference**: YouTube Shorts often contain speech/dialogue that can interfere with music recognition
2. **Better Accuracy**: Removing vocals improves the chances of identifying background music
3. **Advanced AI**: Uses the latest transformer-based architecture for superior separation quality

### Demucs v4 Features

- **Hybrid Transformer Architecture**: Combines CNN and transformer models
- **Multi-Source Separation**: Can separate vocals, drums, bass, and other instruments
- **High Quality Output**: Produces studio-quality separated audio
- **Fast Processing**: Optimized for quick processing of short audio clips

### How Demucs Works in This Pipeline

1. **Input**: Mixed audio from YouTube Short (music + speech)
2. **Processing**: Demucs analyzes the audio and identifies different sources
3. **Output**: Two separate files:
   - `vocals.mp3`: Isolated speech/dialogue
   - `no_vocals.mp3`: Background music without speech

## 🎯 How to Use the Software

### Quick Start

1. **Run the Simple Pipeline**
   ```bash
   python simple_pipeline.py
   ```

2. **Enter YouTube Short URL**
   ```
   Enter YouTube Short URL: https://youtube.com/shorts/...
   ```

3. **Choose Processing Option**
   ```
   🎯 Choose your approach:
   1. 🎵 Use original audio with ACRCloud
   2. 🔇 Remove vocals with Demucs, then use ACRCloud
   ```

4. **Wait for Results**
   - The system will download the audio
   - Optionally remove vocals (if chosen)
   - Test multiple 20-second segments
   - Display identification results

### Detailed Workflow

#### Step 1: Audio Download
- **Tool**: yt-dlp
- **Process**: Downloads audio directly as MP3 from YouTube Short
- **Output**: `audio.mp3` file

#### Step 2: Vocal Removal (Optional)
- **Tool**: Demucs v4 with Hybrid Transformer
- **Process**: Separates vocals from background music
- **Output**: `separated/htdemucs/audio/no_vocals.mp3`

#### Step 3: Music Identification
- **Tool**: ACRCloud REST API
- **Process**: Tests 5 segments of 20 seconds each
- **Output**: Song information with confidence scores

### Example Output

```
🎵 YouTube Short to Music Identification
==================================================

🎬 Downloading audio from: https://youtube.com/shorts/...
✅ Audio download completed!

🔇 Step 1: Removing vocals with Demucs...
✅ Vocals removed: separated/htdemucs/audio/no_vocals.mp3

🎵 Step 2: Identifying song...
📦 Extracting multiple 20-second segments for testing...
🎯 Will test 5 20-second segments
🎵 Segment start times: ['5.0s', '15.0s', '25.0s', '35.0s', '45.0s']

🎵 Testing segment 1/5 (starting at 5.0s)...
📤 Uploading 1234567 bytes to ACRCloud...
✅ SUCCESS: Song identified!
   🎵 Title: Bohemian Rhapsody
   👤 Artist: Queen
   📀 Album: A Night at the Opera
   🎼 Genre: Rock
   🎯 Confidence: 95.2

============================================================
📊 IDENTIFICATION RESULTS
============================================================
✅ Found 3 successful matches!

🎵 Unique songs found: 1

🎵 Song 1:
   Title: Bohemian Rhapsody
   Artist: Queen
   Album: A Night at the Opera
   Genre: Rock
   Confidence: 95.2
   Matched in segment: 1

🎉 SUCCESS! Song identified:
========================================
🎵 Title: Bohemian Rhapsody
👤 Artist: Queen
📀 Album: A Night at the Opera
🎼 Genre: Rock
🎯 Confidence: 95.2
========================================
```

## 🔧 Advanced Usage

### Testing ACRCloud API

Test your API setup with the enhanced test script:

```bash
python test_acrcloud.py
```

This will:
- Use the separated no-vocals audio
- Test multiple segments
- Show detailed results
- Help troubleshoot API issues

### Manual Demucs Processing

If you want to process audio files manually:

```bash
python demucs_example.py
```

### Batch Processing

For processing multiple YouTube Shorts:

1. Create a text file with URLs (one per line)
2. Modify the pipeline to read from the file
3. Process each URL automatically

## 🛠️ Troubleshooting

### Common Issues

#### "yt-dlp not found"
```bash
# Install yt-dlp
pip install yt-dlp

# Or update existing installation
pip install --upgrade yt-dlp
```

#### "ACRCloud credentials not found"
- Check your `.env` file exists
- Verify credentials are correct
- Ensure no extra spaces in the `.env` file

#### "No music identified"
- Try option 2 (remove vocals first)
- Check if the audio actually contains music
- Try with a different YouTube Short
- Verify your ACRCloud project is active

#### "Demucs failed to remove vocals"
- Ensure you have enough disk space
- Check if the audio file is corrupted
- Try with a shorter audio clip

### Performance Tips

1. **Use SSD Storage**: Demucs processing is faster on SSDs
2. **Close Other Applications**: Free up RAM for better performance
3. **Shorter Clips**: Process shorter YouTube Shorts for faster results
4. **Good Internet**: Faster downloads and API calls

## 📁 File Structure

```
youtube-short-music-finder/
├── simple_pipeline.py          # Main pipeline script
├── test_acrcloud.py           # ACRCloud testing script
├── demucs_example.py          # Demucs usage example
├── requirements.txt           # Python dependencies
├── .env                      # API credentials (create this)
├── README.md                 # This file
├── audio.mp3                 # Downloaded audio (generated)
└── separated/                # Demucs output (generated)
    └── htdemucs/
        └── audio/
            ├── no_vocals.mp3  # Background music
            └── vocals.mp3     # Isolated speech
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Demucs**: Facebook Research for the audio separation model
- **ACRCloud**: For the music recognition API
- **yt-dlp**: For YouTube downloading capabilities

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Include your operating system and error messages

---

**Happy Music Finding! 🎵** 