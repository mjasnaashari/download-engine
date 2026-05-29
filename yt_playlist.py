#!/usr/bin/env python3
"""
yt_playlist.py — Download a full YouTube playlist via yt-dlp

Usage:
  python yt_playlist.py -u "https://youtube.com/playlist?list=..."
  python yt_playlist.py -u "https://youtube.com/playlist?list=..." -q 720p
  python yt_playlist.py -u "https://youtube.com/playlist?list=..." -q audio -o ~/Music
  python yt_playlist.py -u "https://youtube.com/playlist?list=..." --list
  python yt_playlist.py -u "https://youtube.com/playlist?list=..." --start 50 --end 60
  python yt_playlist.py -u "https://youtube.com/playlist?list=..." --start 50
"""

import argparse
import sys
import os
import signal

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run:  pip install yt-dlp")
    sys.exit(1)


# ── Ctrl+C handler ────────────────────────────────────────────────────────────

def handle_exit(sig, frame):
    print("\n\n  ✖  Cancelled.\n")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


# ── Quality map ───────────────────────────────────────────────────────────────

QUALITY_MAP = {
    "best":  "bestvideo+bestaudio/best",
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "240p":  "bestvideo[height<=240]+bestaudio/best[height<=240]",
    "worst": "worstvideo+worstaudio/worst",
    "audio": "bestaudio/best",
}


# ── Progress hook ─────────────────────────────────────────────────────────────

def make_progress_hook():
    def hook(d):
        if d["status"] == "downloading":
            total      = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed      = d.get("speed") or 0
            eta        = d.get("eta") or 0
            if total:
                pct    = downloaded / total * 100
                filled = int(30 * downloaded / total)
                bar    = "█" * filled + "░" * (30 - filled)
                spd    = f"{speed/1024/1024:.1f} MB/s" if speed else "-- MB/s"
                print(f"\r  [{bar}] {pct:5.1f}%  {spd}  ETA {eta}s   ", end="", flush=True)
            else:
                print(f"\r  Downloaded {downloaded/1024/1024:.1f} MB …", end="", flush=True)
        elif d["status"] == "finished":
            print(f"\r  ✔  Done — processing …                              ")
        elif d["status"] == "error":
            print(f"\r  ✖  Error.                                            ")
    return hook


# ── List only (no download) ───────────────────────────────────────────────────

def list_playlist(url: str) -> None:
    opts = {"quiet": True, "extract_flat": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title   = info.get("title", "Unknown Playlist")
    entries = info.get("entries", [])
    print(f"\n  Playlist : {title}")
    print(f"  Videos   : {len(entries)}\n")
    for i, e in enumerate(entries, 1):
        print(f"  {i:>3}. {e.get('title', 'Unknown')}")
        print(f"       https://youtu.be/{e.get('id', '')}")
    print()


# ── Download ──────────────────────────────────────────────────────────────────

def download_playlist(
    url: str,
    quality: str = "best",
    output_dir: str = "./downloads",
    start: int = 1,
    end: int = 0,
) -> None:
    quality = quality.lower()
    is_audio = quality == "audio"

    if quality not in QUALITY_MAP:
        print(f"Unknown quality '{quality}'. Choose from: {', '.join(QUALITY_MAP)}")
        sys.exit(1)

    fmt = QUALITY_MAP[quality]
    os.makedirs(output_dir, exist_ok=True)

    outtmpl = os.path.join(output_dir, "%(playlist_index)02d - %(title)s.%(ext)s")

    # playlist_items: "50:60" = items 50 to 60, "50:" = item 50 to end
    playlist_items = f"{start}:{end}" if end else f"{start}:"

    ydl_opts = {
        "format":              fmt,
        "outtmpl":             outtmpl,
        "merge_output_format": "mp4",
        "progress_hooks":      [make_progress_hook()],
        "ignoreerrors":        True,
        "noplaylist":          False,
        "playlist_items":      playlist_items,
    }

    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "mp3",
            "preferredquality": "192",
        }]

    range_str = f"{start} → {end}" if end else f"{start} → end"
    print(f"\n  Playlist : {url}")
    print(f"  Quality  : {quality}  →  {fmt}")
    print(f"  Range    : {range_str}")
    print(f"  Output   : {os.path.abspath(output_dir)}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"\n  ✔  All done! Saved to: {os.path.abspath(output_dir)}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="yt_playlist",
        description="Download a full YouTube playlist ordered by video name + number.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality options:
  best  2160p  1440p  1080p  720p  480p  360p  240p  worst  audio

Examples:
  python yt_playlist.py -u "URL"
  python yt_playlist.py -u "URL" -q 720p
  python yt_playlist.py -u "URL" -q audio -o ~/Music
  python yt_playlist.py -u "URL" --list
  python yt_playlist.py -u "URL" --start 50 --end 60
  python yt_playlist.py -u "URL" --start 50
""",
    )
    parser.add_argument("-u", "--url",     required=True,         help="Playlist URL (always quote it!)")
    parser.add_argument("-q", "--quality", default="best",        help="Quality (default: best)")
    parser.add_argument("-o", "--output",  default="./downloads", help="Output folder (default: ./downloads)")
    parser.add_argument("--list",          action="store_true",   help="List all videos without downloading")
    parser.add_argument("--start",         type=int, default=1,   help="Start from this item number (default: 1)")
    parser.add_argument("--end",           type=int, default=0,   help="Stop at this item number (default: until end)")

    args = parser.parse_args()

    if args.list:
        list_playlist(args.url)
    else:
        download_playlist(args.url, args.quality, args.output, args.start, args.end)


if __name__ == "__main__":
    main()
