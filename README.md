# yt-download

CLI tool to download YouTube videos/audio using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

---

## Setup (Arch Linux)

```bash
# 1. Install system dependencies
sudo pacman -S python ffmpeg git

# 2. Clone the repo
git clone https://github.com/YOUR_USERNAME/yt-download.git
cd yt-download

# 3. Create and activate virtual environment
python -m venv env
source env/bin/activate

# 4. Install Python dependency
pip install yt-dlp
```

---

## Usage

```bash
# Activate env first (every new terminal session)
source env/bin/activate

# Best quality (default)
python yt_download.py -u "https://youtu.be/VIDEO_ID"

# Specific resolution
python yt_download.py -u "https://youtu.be/VIDEO_ID" -q 1080p

# Audio only → MP3
python yt_download.py -u "https://youtu.be/VIDEO_ID" -q audio

# Custom output folder
python yt_download.py -u "https://youtu.be/VIDEO_ID" -q 720p -o ~/Videos

# List all available formats
python yt_download.py -u "https://youtu.be/VIDEO_ID" --list-formats

# Download full playlist
python yt_download.py -u "https://youtube.com/playlist?list=..." --playlist
```

**Quality options:** `best` `2160p` `1440p` `1080p` `720p` `480p` `360p` `240p` `worst` `audio`

---

## Push to GitHub

```bash
# One-time setup
git init
git remote add origin https://github.com/YOUR_USERNAME/yt-download.git

# First push
git add .
git commit -m "init"
git push -u origin main
```

---

## Project Structure

```
yt-download/
├── env/              ← virtual environment (not committed)
├── downloads/        ← default output folder (not committed)
├── yt_download.py    ← main script
├── .gitignore
└── README.md
```
