#!/usr/bin/env python3
"""
yt_download.py — YouTube video/audio downloader powered by yt-dlp

Usage examples:
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ"
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" -q 1080p
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" -q best
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" -q audio -o ~/Music
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" --list-formats
"""

import argparse
import sys
import os

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run:  pip install yt-dlp")
    sys.exit(1)


# ── Progress hook ────────────────────────────────────────────────────────────

def make_progress_hook():
    """Returns a yt-dlp progress hook that prints a live progress bar."""
    def hook(d):
        if d["status"] == "downloading":
            total   = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed   = d.get("speed") or 0
            eta     = d.get("eta") or 0

            if total:
                pct = downloaded / total * 100
                bar_len = 30
                filled  = int(bar_len * downloaded / total)
                bar     = "█" * filled + "░" * (bar_len - filled)
                speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else "-- MB/s"
                eta_str   = f"{eta}s" if eta else "--"
                print(
                    f"\r  [{bar}] {pct:5.1f}%  {speed_str}  ETA {eta_str}   ",
                    end="", flush=True
                )
            else:
                mb = downloaded / 1024 / 1024
                print(f"\r  Downloaded {mb:.1f} MB …", end="", flush=True)

        elif d["status"] == "finished":
            print(f"\r  ✔  Download complete — processing file …          ")

        elif d["status"] == "error":
            print(f"\r  ✖  Error during download.                         ")

    return hook


# ── Format helpers ───────────────────────────────────────────────────────────

QUALITY_MAP = {
    # key → yt-dlp format selector
    "best":    "bestvideo+bestaudio/best",
    "2160p":   "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p":   "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p":   "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":    "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":    "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":    "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "240p":    "bestvideo[height<=240]+bestaudio/best[height<=240]",
    "worst":   "worstvideo+worstaudio/worst",
    "audio":   "bestaudio/best",          # audio-only → mp3
}


def list_formats(url: str) -> None:
    """Print all available formats for a URL."""
    ydl_opts = {"quiet": True, "no_warnings": True}
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


# ── Core download ────────────────────────────────────────────────────────────

def download(
    url: str,
    quality: str = "best",
    output_dir: str = "./downloads",
    custom_format: str = "",
    no_playlist: bool = True,
    subtitle: bool = False,
    embed_thumbnail: bool = False,
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

    # Output template: <output_dir>/<title>.<ext>
    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts: dict = {
        "format": fmt,
        "outtmpl": outtmpl,
        "progress_hooks": [make_progress_hook()],
        "no_warnings": False,
        "noplaylist": no_playlist,
        # Merge video+audio into mp4 when separate streams are chosen
        "merge_output_format": "mp4",
    }

    if is_audio_only:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    if subtitle:
        ydl_opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
        })

    if embed_thumbnail:
        ydl_opts.setdefault("postprocessors", []).append(
            {"key": "EmbedThumbnail"}
        )
        ydl_opts["writethumbnail"] = True

    print(f"\n  URL     : {url}")
    print(f"  Quality : {quality}  →  format selector: {fmt}")
    print(f"  Output  : {os.path.abspath(output_dir)}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ret = ydl.download([url])

    if ret == 0:
        print(f"\n  ✔  Saved to: {os.path.abspath(output_dir)}\n")
    else:
        print("\n  ✖  yt-dlp exited with an error.\n")
        sys.exit(ret)


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt_download",
        description="Download YouTube videos (or audio) via yt-dlp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality options:
  best    — highest available video + audio  (default)
  2160p   — up to 4K
  1440p   — up to 1440p
  1080p   — up to 1080p
  720p    — up to 720p
  480p    — up to 480p
  360p    — up to 360p
  240p    — up to 240p
  worst   — lowest available
  audio   — audio only → saved as MP3

Examples:
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ"
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" -q 1080p -o ~/Videos
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" -q audio
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" --list-formats
  python yt_download.py -u "https://youtu.be/dQw4w9WgXcQ" --format "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
""",
    )

    parser.add_argument(
        "-u", "--url",
        required=True,
        metavar="URL",
        help="YouTube video (or playlist) URL",
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        metavar="QUALITY",
        help="Quality preset (default: best). See list below.",
    )
    parser.add_argument(
        "-o", "--output",
        default="./downloads",
        metavar="DIR",
        help="Output directory (default: ./downloads)",
    )
    parser.add_argument(
        "-f", "--format",
        default="",
        metavar="FORMAT",
        help="Raw yt-dlp format selector (overrides -q)",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow downloading entire playlist (disabled by default)",
    )
    parser.add_argument(
        "--subs",
        action="store_true",
        help="Download English subtitles alongside the video",
    )
    parser.add_argument(
        "--thumbnail",
        action="store_true",
        help="Embed thumbnail into the downloaded file",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List all available formats for the URL and exit",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    if args.list_formats:
        list_formats(args.url)
        return

    download(
        url=args.url,
        quality=args.quality,
        output_dir=args.output,
        custom_format=args.format,
        no_playlist=not args.playlist,
        subtitle=args.subs,
        embed_thumbnail=args.thumbnail,
    )


if __name__ == "__main__":
    main()
