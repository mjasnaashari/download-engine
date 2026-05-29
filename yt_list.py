#!/usr/bin/env python3
"""
yt_list.py — List all video titles and URLs from a YouTube playlist

Usage:
  python yt_list.py -u "https://youtube.com/playlist?list=..."
  python yt_list.py -u "https://youtube.com/playlist?list=..." -o list.txt
"""

import argparse
import sys

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run:  pip install yt-dlp")
    sys.exit(1)


def list_playlist(url: str, output: str = "") -> None:
    opts = {
        "quiet":        True,
        "extract_flat": True,
        "no_warnings":  True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries", [])
    lines = []

    for i, e in enumerate(entries, 1):
        title = e.get("title", "Unknown")
        url   = f"https://www.youtube.com/watch?v={e.get('id', '')}"
        lines.append(f"{i}.")
        lines.append(f"title: {title}")
        lines.append(f"url:   {url}")
        lines.append("")

    result = "\n".join(lines)
    print(result)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"  ✔  Saved to: {output}")


def main():
    parser = argparse.ArgumentParser(
        prog="yt_list",
        description="List all titles and URLs from a YouTube playlist.",
        epilog="""
Examples:
  python yt_list.py -u "https://youtube.com/playlist?list=PLxxx"
  python yt_list.py -u "https://youtube.com/playlist?list=PLxxx" -o list.txt
""",
    )
    parser.add_argument("-u", "--url",    required=True, help="Playlist URL")
    parser.add_argument("-o", "--output", default="",    help="Save output to file")

    args = parser.parse_args()
    list_playlist(args.url, args.output)


if __name__ == "__main__":
    main()
