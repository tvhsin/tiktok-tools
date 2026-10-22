#!/usr/bin/env python3
"""
One-time downloader: 4 photo posts -> readmewhenyouneedme/part 1 ... part 4
Files are saved in post order as 1.jpg, 2.jpg, ... (original format kept)

Usage:
    python download_parts.py                      # the 4 built-in posts
    python download_parts.py --url URL            # one post -> readmewhenyouneedme/<post id>
    python download_parts.py --url URL --folder "bonus"   # custom folder name

Setup:  pip install -U "yt-dlp[default,curl-cffi]"
Needs:  cookies.txt next to this script
"""
import argparse
import re
import time
from pathlib import Path

import yt_dlp

USERNAME = "readmewhenyouneedme"
POST_IDS = [  # order = part 1, 2, 3, 4
    "7187387678357310725",
    "7187388141370625286",
    "7187388519365577990",
    "7187388727788850438",
]

ap = argparse.ArgumentParser()
ap.add_argument("--url", help="download only this post (URL or ID)")
ap.add_argument("--folder", help="folder name for --url (default: the post ID)")
args = ap.parse_args()

HERE = Path(__file__).resolve().parent
ROOT = HERE / USERNAME

ydl = yt_dlp.YoutubeDL({"cookiefile": str(HERE / "cookies.txt"),
                        "quiet": True, "no_warnings": True, "retries": 3})
ie = ydl.get_info_extractor("TikTok")
ie.set_downloader(ydl)


def get_images(pid, user):
    url = f"https://www.tiktok.com/@{user}/video/{pid}"
    for attempt in range(1, 4):
        data, status = ie._extract_web_data_and_status(url, pid)
        images = ((data or {}).get("imagePost") or {}).get("images") or []
        if status == 0 and images:
            return images
        time.sleep(5 * attempt)
    raise RuntimeError(f"no images found for {pid}")


def save_image(urls, stem):
    for u in urls:  # try mirror URLs in turn
        try:
            blob = ydl.urlopen(yt_dlp.networking.Request(
                u, headers={"Referer": "https://www.tiktok.com/"})).read()
            if not blob:
                continue
            ext = Path(u.split("?")[0]).suffix.lower().lstrip(".") or "jpg"
            ext = "jpg" if ext == "jpeg" else ext
            stem.with_suffix(f".{ext}").write_bytes(blob)
            return
        except Exception as e:
            err = e
    raise RuntimeError(f"all URLs failed ({err})")


def download(pid, folder_name, user=USERNAME):
    folder = ROOT / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    images = get_images(pid, user)
    print(f"{folder_name}: {len(images)} images")
    for n, img in enumerate(images, 1):
        if any(folder.glob(f"{n}.*")):
            continue
        save_image((img.get("imageURL") or {}).get("urlList") or [], folder / str(n))
        print(f"  {n}")
        time.sleep(0.5)


if args.url:
    pid = re.search(r"(\d{15,25})", args.url).group(1)
    user = (re.search(r"@([\w.]+)", args.url) or [None, USERNAME])[1]
    download(pid, args.folder or pid, user)
else:
    for part, pid in enumerate(POST_IDS, 1):
        download(pid, f"part {part}")
        time.sleep(5)

ydl.close()
print("Done.")
