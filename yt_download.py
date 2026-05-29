#!/usr/bin/env python3
"""
yt_download.py — YouTube video/audio downloader powered by yt-dlp

Usage:
  python yt_download.py -u "https://youtu.be/VIDEO_ID"
  python yt_download.py -u "https://youtu.be/VIDEO_ID" -q 1080p
  python yt_download.py -u "https://youtu.be/VIDEO_ID" -q audio -o ~/Music
  python yt_download.py -u "https://youtu.be/VIDEO_ID" --list-formats
  python yt_download.py -u "https://youtu.be/VIDEO_ID" --browser brave
  python yt_download.py -u "https://youtu.be/VIDEO_ID" --cookies cookies.txt
"""

import argparse
import sys
import os
import signal

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run:  python -m pip install yt-dlp")
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


# ── List formats ──────────────────────────────────────────────────────────────

def list_formats(url: str, browser: str = "", cookies: str = "") -> None:
    ydl_opts = {
        "quiet": True, 
        "no_warnings": True,
        "remote_components": ["ejs:github"]  # Added solver fix here
    }
    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)
    if cookies:
        ydl_opts["cookiefile"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    print(f"\nTitle : {info.get('title', 'Unknown')}")
    print(f"ID    : {info.get('id', '')}")
    print(f"\n{'ID':<12} {'EXT':<6} {'RES':>8}  {'FPS':>4}  {'VCODEC':<14} {'ACODEC':<14}  NOTE")
    print("─" * 80)
    for fmt in info.get("formats", []):
        fid    = fmt.get("format_id", "")
        ext    = fmt.get("ext", "")
        height = fmt.get("height")
        res    = f"{height}p" if height else "audio"
        fps    = fmt.get("fps") or ""
        vcodec = (fmt.get("vcodec") or "none")[:14]
        acodec = (fmt.get("acodec") or "none")[:14]
        note   = fmt.get("format_note", "")
        print(f"{fid:<12} {ext:<6} {res:>8}  {str(fps):>4}  {vcodec:<14} {acodec:<14}  {note}")
    print()


# ── Download ──────────────────────────────────────────────────────────────────

def download(
    url: str,
    quality: str = "best",
    output_dir: str = "./downloads",
    custom_format: str = "",
    no_playlist: bool = True,
    subtitle: bool = False,
    embed_thumbnail: bool = False,
    browser: str = "",
    cookies: str = "",
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    quality = quality.lower()
    is_audio_only = quality == "audio"

    if custom_format:
        fmt = custom_format
    elif quality in QUALITY_MAP:
        fmt = QUALITY_MAP[quality]
    else:
        print(f"Unknown quality '{quality}'. Choose from: {', '.join(QUALITY_MAP)}")
        sys.exit(1)

    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format":              fmt,
        "outtmpl":             outtmpl,
        "progress_hooks":      [make_progress_hook()],
        "no_warnings":         False,
        "noplaylist":          no_playlist,
        "merge_output_format": "mp4",
        "remote_components":   ["ejs:github"],  # Added solver fix here
    }

    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)
    if cookies:
        ydl_opts["cookiefile"] = cookies

    if is_audio_only:
        ydl_opts["postprocessors"] = [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "mp3",
            "preferredquality": "192",
        }]

    if subtitle:
        ydl_opts.update({
            "writesubtitles":    True,
            "writeautomaticsub": True,
            "subtitleslangs":    ["en"],
        })

    if embed_thumbnail:
        ydl_opts.setdefault("postprocessors", []).append({"key": "EmbedThumbnail"})
        ydl_opts["writethumbnail"] = True

    auth_str = f"browser:{browser}" if browser else (f"file:{cookies}" if cookies else "none")

    print(f"\n  URL     : {url}")
    print(f"  Quality : {quality}  →  {fmt}")
    print(f"  Auth    : {auth_str}")
    print(f"  Output  : {os.path.abspath(output_dir)}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ret = ydl.download([url])

    if ret == 0:
        print(f"\n  ✔  Saved to: {os.path.abspath(output_dir)}\n")
    else:
        print("\n  ✖  yt-dlp exited with an error.\n")
        sys.exit(ret)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="yt_download",
        description="Download YouTube videos or audio via yt-dlp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality options:
  best  2160p  1440p  1080p  720p  480p  360p  240p  worst  audio

Browser options (fixes "sign in to confirm" bot error):
  firefox  chrome  brave  chromium  edge

Examples:
  python yt_download.py -u "URL"
  python yt_download.py -u "URL" -q 1080p
  python yt_download.py -u "URL" -q audio
  python yt_download.py -u "URL" -q 720p -o ~/Videos
  python yt_download.py -u "URL" --list-formats
  python yt_download.py -u "URL" --browser brave
  python yt_download.py -u "URL" --browser brave -q 1080p
  python yt_download.py -u "URL" --cookies cookies.txt
""",
    )
    parser.add_argument("-u", "--url",          required=True,         help="Video URL")
    parser.add_argument("-q", "--quality",      default="best",        help="Quality (default: best)")
    parser.add_argument("-o", "--output",       default="./downloads", help="Output folder (default: ./downloads)")
    parser.add_argument("-f", "--format",       default="",            help="Raw yt-dlp format selector (overrides -q)")
    parser.add_argument("--playlist",           action="store_true",   help="Allow downloading entire playlist")
    parser.add_argument("--subs",               action="store_true",   help="Download English subtitles")
    parser.add_argument("--thumbnail",          action="store_true",   help="Embed thumbnail into file")
    parser.add_argument("--list-formats",       action="store_true",   help="List all available formats and exit")
    parser.add_argument("--browser",            default="",            help="Use cookies from browser: brave, firefox, chrome, chromium")
    parser.add_argument("--cookies",            default="",            help="Path to cookies.txt file")

    args = parser.parse_args()

    if args.list_formats:
        list_formats(args.url, args.browser, args.cookies)
        return

    download(
        url=args.url,
        quality=args.quality,
        output_dir=args.output,
        custom_format=args.format,
        no_playlist=not args.playlist,
        subtitle=args.subs,
        embed_thumbnail=args.thumbnail,
        browser=args.browser,
        cookies=args.cookies,
    )


if __name__ == "__main__":
    main()
