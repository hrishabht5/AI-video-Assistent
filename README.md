# AI YouTube Shorts Generator

AI-powered tool to automatically generate engaging YouTube Shorts from long-form videos. Uses Gemini 2.5 Flash and Whisper to extract multiple highlights, add subtitles, and crop videos vertically with **Active Face Tracking**.

![longshorts](https://github.com/user-attachments/assets/3f5d1abf-bf3b-475f-8abf-5e253003453a)

## Features

- **🎬 Flexible Input**: Supports both YouTube URLs and local video files
- **🎤 GPU-Accelerated Transcription**: CUDA-enabled Whisper for fast speech-to-text
- **🤖 Multi-Highlight Selection**: Gemini 2.5 Flash finds up to **10 engaging segments** from a single video
- **🎯 Active Face Tracking**: Smooth, real-time face detection that keeps the speaker centered in 9:16 crops
- **📝 Auto Subtitles**: Stylized captions burned directly into the video
- **📱 Vertical Format**: Perfect 9:16 aspect ratio for TikTok/YouTube Shorts/Instagram Reels
- **🚀 Web API**: FastAPI integration for remote triggering and cloud deployment
- **🔄 Concurrent Execution**: Unique session IDs allow multiple instances to run simultaneously
- **📦 Clean Output**: Slugified filenames and automatic temp file cleanup

## ☁️ Cloud Hosting (Google Colab - FREE GPU)

For the best experience and **free NVIDIA T4 GPU** acceleration, use the Google Colab setup:

1. Open [Google Colab](https://colab.research.google.com/).
2. Upload the `Google_Colab_Setup.ipynb` file from this repository.
3. Follow the instructions in the notebook to:
   - Install dependencies automatically.
   - Run the generator with any YouTube URL.
   - Download multiple zipped shorts at once.

## Installation

### Prerequisites

- Python 3.10+
- FFmpeg with development headers
- NVIDIA GPU with CUDA support (optional, but recommended for faster transcription)
- ImageMagick (for subtitle rendering)
- OpenAI API key

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator.git
   cd AI-Youtube-Shorts-Generator
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt install -y ffmpeg libavdevice-dev libavfilter-dev libopus-dev \
     libvpx-dev pkg-config libsrtp2-dev imagemagick
   ```

3. **Fix ImageMagick security policy** (required for subtitles):
   ```bash
   sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml
   ```

4. **Create and activate virtual environment:**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API=your_openai_api_key_here
   ```

## Usage

### With YouTube URL (Interactive)
```bash
./run.sh
# Then enter YouTube URL when prompted
# You'll be able to select video resolution (5s timeout, auto-selects highest)
```

### With YouTube URL (Command-Line)
```bash
./run.sh "https://youtu.be/VIDEO_ID"
```

### With Local Video File
```bash
./run.sh "/path/to/your/video.mp4"
```

### Batch Processing Multiple URLs
Create a `urls.txt` file with one URL per line, then:

```bash
# Process all URLs sequentially with auto-approve
xargs -a urls.txt -I{} ./run.sh --auto-approve {}
```

Or without auto-approve (will prompt for each):
```bash
xargs -a urls.txt -I{} ./run.sh {}
```

## Resolution Selection

When downloading from YouTube, you'll see:
```
Available video streams:
  0. Resolution: 1080p, Size: 45.2 MB, Type: Adaptive
  1. Resolution: 720p, Size: 28.1 MB, Type: Adaptive
  2. Resolution: 480p, Size: 15.3 MB, Type: Adaptive

Select resolution number (0-2) or wait 5s for auto-select...
Auto-selecting highest quality in 5 seconds...
```

- **Enter a number** to select that resolution immediately
- **Wait 5 seconds** to auto-select highest quality (1080p)
- **Invalid input** falls back to highest quality

## How It Works

1. **Download/Load**: Fetches from YouTube or loads local file
2. **Resolution Selection**: Choose video quality (5s timeout, auto-selects highest)
3. **Extract Audio**: Converts to WAV format
4. **Transcribe**: GPU-accelerated Whisper transcription (~30s for 5min video)
5. **AI Analysis**: GPT-4o-mini selects most engaging 2-minute segment
6. **Interactive Approval**: Review selection, regenerate if needed, or auto-approve in 15s
7. **Extract Clip**: Crops selected timeframe
8. **Smart Crop**: 
   - Detects faces → static face-centered vertical crop
   - No faces → half-width screen recording with motion tracking
9. **Add Subtitles**: Burns Franklin Gothic captions with blue text/black outline
10. **Combine Audio**: Merges audio track with final video
11. **Cleanup**: Removes all temporary files

**Output**: `{video-title}_{session-id}_short.mp4` with slugified filename and unique identifier

## Interactive Workflow

After AI selects a highlight, you'll see:

```
============================================================
SELECTED SEGMENT DETAILS:
Time: 68s - 187s (119s duration)
============================================================

Options:
  [Enter/y] Approve and continue
  [r] Regenerate selection
  [n] Cancel

Auto-approving in 15 seconds if no input...
```

- Press **Enter** or **y** to approve
- Press **r** to regenerate a different selection (can repeat multiple times)
- Press **n** to cancel
- Wait 15 seconds to auto-approve (perfect for automation)

## Configuration

### Subtitle Styling
Edit `Components/Subtitles.py`:
- **Font**: Line 51 (`font='Franklin-Gothic'`)
- **Size**: Line 47 (`fontsize=80`)
- **Color**: Line 48 (`color='#2699ff'`)
- **Outline**: Lines 49-50 (`stroke_color='black'`, `stroke_width=2`)

### Highlight Selection Criteria
Edit `Components/LanguageTasks.py`:
- **Prompt**: Line 29 (adjust what's "interesting, useful, surprising, controversial, or thought-provoking")
- **Model**: Line 54 (`model="gpt-4o-mini"`)
- **Temperature**: Line 55 (`temperature=1.0`)

### Motion Tracking
Edit `Components/FaceCrop.py`:
- **Update frequency**: Line 93 (`update_interval = int(fps)`) - currently 1 shift/second
- **Smoothing**: Line 115 (`0.90 * smoothed_x + 0.10 * target_x`) - currently 90%/10%
- **Motion threshold**: Line 107 (`motion_threshold = 2.0`)

### Face Detection
Edit `Components/FaceCrop.py`:
- **Sensitivity**: Line 37 (`minNeighbors=8`) - Higher = fewer false positives
- **Minimum size**: Line 37 (`minSize=(30, 30)`) - Minimum face size in pixels

### Video Quality
Edit `Components/Subtitles.py` and `Components/FaceCrop.py`:
- **Bitrate**: Subtitles.py line 74 (`bitrate='3000k'`)
- **Preset**: Subtitles.py line 73 (`preset='medium'`)

## Output Files

Final videos are named: `{video-title}_{session-id}_short.mp4`

Example: `my-awesome-video_a1b2c3d4_short.mp4`

- **Slugified title**: Lowercase, hyphens instead of spaces
- **Session ID**: 8-character unique identifier for traceability
- **Resolution**: Matches source video height (720p → 404x720, 1080p → 607x1080)

## Concurrent Execution

Run multiple instances simultaneously:
```bash
./run.sh "https://youtu.be/VIDEO1" &
./run.sh "https://youtu.be/VIDEO2" &
./run.sh "/path/to/video3.mp4" &
```

Each instance gets a unique session ID and temporary files, preventing conflicts.

## Troubleshooting

### CUDA/GPU Issues
```bash
# Verify CUDA libraries
export LD_LIBRARY_PATH=$(find $(pwd)/venv/lib/python3.10/site-packages/nvidia -name "lib" -type d | paste -sd ":" -)
```
The `run.sh` script handles this automatically.

### No Subtitles
Ensure ImageMagick policy allows file operations:
```bash
grep 'pattern="@\*"' /etc/ImageMagick-6/policy.xml
# Should show: rights="read|write"
```

### Face Detection Issues
- Video needs visible faces in first 30 frames
- For screen recordings, automatic motion tracking applies
- Low-resolution videos may have less reliable detection

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

## Related Projects

- [AI Influencer Generator](https://github.com/SamurAIGPT/AI-Influencer-Generator)
- [Text to Video AI](https://github.com/SamurAIGPT/Text-To-Video-AI)
- [Faceless Video Generator](https://github.com/SamurAIGPT/Faceless-Video-Generator)
- [AI B-roll Generator](https://github.com/Anil-matcha/AI-B-roll)
- [No-code YouTube Shorts Generator](https://www.vadoo.tv/clip-youtube-video)

