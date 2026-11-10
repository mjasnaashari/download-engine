# yt-download

CLI toolkit to download YouTube videos, audio, and playlists using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

---

## Quick Setup

```bash
chmod +x setup.sh
./setup.sh                    # one-command: installs deps + starts PO token server
source env/bin/activate

# Download high-quality YouTube videos (1080p, 1440p, etc.)
python yt_download.py -u "URL" -q 1440p --browser brave
```

`setup.sh` handles everything: Python venv, pip packages, the PO token plugin, Deno, and ffmpeg checks. It also starts a localhost-only PO token server for 1080p+ downloads.

### Manual Setup (without setup.sh)

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install bgutil-ytdlp-pot-provider
```

**System dependencies:** `ffmpeg` and `deno`

```bash
# Ubuntu/Debian
sudo apt install ffmpeg
curl -fsSL https://deno.land/install.sh | sh

# macOS
brew install ffmpeg deno
```

### PO Token Server (for 1080p+ and age-restricted videos)

`setup.sh` starts this automatically. Manage it with these options:

```bash
./setup.sh                  # full setup + start server
./setup.sh --no-server      # setup only, don't start server
./setup.sh --start-server   # start the server only
./setup.sh --stop-server    # stop the server
./setup.sh --status         # check if server is running
```

**Security:** The server listens on `127.0.0.1:$PORT` only (localhost). It is not exposed to the network.

```bash
# Start manually (if you did manual setup):
(cd ~/bgutil-ytdlp-pot-provider/server && deno run --allow-env --allow-net --allow-ffi=. \
  --allow-read=. src/main.ts --port 4416)
```

> **Note:** yt-dlp auto-detects the server at `http://127.0.0.1:4416`.  
> If the server is not running, yt-dlp falls back to the slower Deno script mode (still works, just slower per-request).

---

## Scripts

### `yt_download.py` — Single video

```bash
python yt_download.py -u "URL"
python yt_download.py -u "URL" -q 1080p
python yt_download.py -u "URL" -q audio
python yt_download.py -u "URL" -q 720p -o ~/Videos
python yt_download.py -u "URL" --list-formats
python yt_download.py -u "URL" --browser brave        # pass auth to bypass bot blocks
python yt_download.py -u "URL" --cookies cookies.txt  # use exported cookies file
python yt_download.py -u "URL" -N 8               # 8 fragments at once (yt-dlp -N)
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
python yt_playlist.py -u "URL" --browser brave        # pass auth to bypass bot blocks
python yt_playlist.py -u "URL" --cookies cookies.txt  # use exported cookies file
python yt_playlist.py -u "URL" -N 8               # 8 fragments at once (yt-dlp -N)
```

Files saved as: `01 - Video Title.mp4`, `02 - Video Title.mp4` …

---

### `yt_list.py` — List playlist titles & URLs

```bash
python yt_list.py -u "URL"              # print to terminal
python yt_list.py -u "URL" -o list.txt  # save to file
```

Output:
```text
1.
title: Video Title
url:   https://www.youtube.com/watch?v=...
```

---

## Quality Options

| Option  | Description                         |
|---------|-------------------------------------|
| `best`  | Highest available (default)         |
| `2160p` | 4K                                  |
| `1440p` | 2K                                  |
| `1080p` | Full HD                             |
| `720p`  | HD                                  |
| `480p`  | SD                                  |
| `360p`  | Low                                 |
| `240p`  | Very low                            |
| `worst` | Lowest available                    |
| `audio` | Audio only → MP3                    |

---

## Notes

- **Age-restricted videos**: Always pass `--browser brave` (or your browser) to authenticate with YouTube cookies. Without auth, only 360p is available.
- **PO Token**: The `bgutil-ytdlp-pot-provider` plugin + server generates GVS PO Tokens needed for 1080p+ formats. `setup.sh` handles this automatically.
- **`--browser` support**: `firefox`, `chrome`, `brave`, `chromium`, `edge`
- **`-N`**: concurrent DASH/HLS fragments (yt-dlp `concurrent_fragment_downloads`). Default is `1`. Higher values only speed up fragmented formats; a single progressive file stays one connection.

---

## Project Structure

```text
yt-download/
├── env/              ← virtual environment (not committed)
├── downloads/        ← default output folder (not committed)
├── yt_download.py    ← single video
├── yt_playlist.py    ← full playlist
├── yt_list.py        ← list playlist titles & URLs
├── requirements.txt  ← Python dependencies
├── setup.sh          ← automated setup script
├── .gitignore
└── README.md
```
