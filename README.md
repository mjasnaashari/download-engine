# yt-download

CLI toolkit to download YouTube videos, audio, and playlists using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

---

## Setup

```bash
sudo pacman -S python ffmpeg git
git clone https://github.com/mjasnaashari/download-engine
cd download-engine
python -m venv env
source env/bin/activate
python -m pip install yt-dlp requests
```

> Run `source env/bin/activate` every new terminal session.

---

## Scripts

### `yt_download.py` — Single video

```bash
python yt_download.py -u "URL"
python yt_download.py -u "URL" -q 1080p
python yt_download.py -u "URL" -q audio
python yt_download.py -u "URL" -q 720p -o ~/Videos
python yt_download.py -u "URL" --list-formats
```

---

### `yt_playlist.py` — Full playlist

```bash
python yt_playlist.py -u "URL"                        # download all (best quality)
python yt_playlist.py -u "URL" -q 720p                # specific quality
python yt_playlist.py -u "URL" -q audio -o ~/Music    # audio only → MP3
python yt_playlist.py -u "URL" --list                 # list videos, no download
python yt_playlist.py -u "URL" --start 50             # download from item 50 to end
python yt_playlist.py -u "URL" --start 50 --end 60    # download items 50 to 60
```

Files saved as: `01 - Video Title.mp4`, `02 - Video Title.mp4` …

---

### `yt_list.py` — List playlist titles & URLs

```bash
python yt_list.py -u "URL"              # print to terminal
python yt_list.py -u "URL" -o list.txt  # save to file
```

Output:
```
1.
title: Video Title
url:   https://www.youtube.com/watch?v=...

2.
title: Video Title
url:   https://www.youtube.com/watch?v=...
```

---

## Quality Options

| Option | Description |
|--------|-------------|
| `best` | Highest available (default) |
| `2160p` | 4K |
| `1440p` | 2K |
| `1080p` | Full HD |
| `720p` | HD |
| `480p` | SD |
| `360p` | Low |
| `240p` | Very low |
| `worst` | Lowest available |
| `audio` | Audio only → MP3 |

---

## Project Structure

```
yt-download/
├── env/              ← virtual environment (not committed)
├── downloads/        ← default output folder (not committed)
├── yt_download.py    ← single video
├── yt_playlist.py    ← full playlist
├── yt_list.py        ← list playlist titles & URLs
├── .gitignore
└── README.md
```

