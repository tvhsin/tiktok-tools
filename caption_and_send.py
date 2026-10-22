r"""
Embed captions at the top of images and/or send them to a Telegram group, in order.

Setup:
    pip install pillow requests

Usage (run from anywhere):
    python caption_and_send.py embed            # writes captioned images to <IMG_DIR>\captioned
    python caption_and_send.py send             # sends the captioned images to Telegram
    python caption_and_send.py send --raw       # sends ORIGINAL images with caption as Telegram caption
    python caption_and_send.py embed send       # do both in one go
    python caption_and_send.py send --album     # send in albums of 10 (12 albums for 120 images)
    python caption_and_send.py send --album --both   # embedded-text images + Telegram caption too
    python caption_and_send.py delete           # delete every message this script sent (uses sent_ids.json)
    python caption_and_send.py delete --probe   # sweep the last 150 ids (use --count N for more)
    python caption_and_send.py delete --all     # sweep every id in the chat: wipes all the bot's messages
    Optional: --start 5 --end 124   (limit the range, handy for resuming after a failure)
              --as-file             (send as document = no Telegram compression)
              --test                (embed only the first image so you can check the look)
"""
import argparse
import json
import os
import sys
import time

import requests
from PIL import Image, ImageDraw, ImageFont

# ============================== CONFIG ==============================
IMG_DIR = r"E:\Scripts\tiktok post downloader\readmewhenyouneedme"
FIRST, LAST = 5, 124                      # 5.jpg ... 124.jpg  (120 images)
CAPTIONS_FILE = os.path.join(IMG_DIR, "captions.txt")
OUT_DIR = os.path.join(IMG_DIR, "captioned")
LOG_FILE = os.path.join(OUT_DIR, "sent_ids.json")   # remembers message ids so they can be deleted
ALBUM_SIZE = 10                                     # Telegram max per album

BOT_TOKEN = "111111111:FKJSDFKDSHFJ"     # from @BotFather on telegram
CHAT_ID = "-123445667"                # your group's chat id (negative number)

# Text area at the top of the image
TOP_BOX_HEIGHT = 300
PAD_X = 50
PAD_Y = 30
MAX_FONT, MIN_FONT = 90, 28
LINE_SPACING = 1.2
TEXT_COLOR = "auto"                       # "auto", "white" or "black"

FONT_CANDIDATES = [                       # first one found is used
    r"C:\Windows\Fonts\segoeuib.ttf",     # Segoe UI Bold
    r"C:\Windows\Fonts\arialbd.ttf",      # Arial Bold
    r"C:\Windows\Fonts\calibrib.ttf",
    "arialbd.ttf",
]
# ====================================================================


def load_captions():
    with open(CAPTIONS_FILE, encoding="utf-8") as f:
        text = f.read().strip()
    # Captions separated by a line containing only --- ; otherwise one caption per line
    if "\n---\n" in text.replace("\r\n", "\n"):
        caps = [c.strip() for c in text.replace("\r\n", "\n").split("\n---\n")]
    else:
        caps = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return caps


def find_font_path():
    for p in FONT_CANDIDATES:
        try:
            ImageFont.truetype(p, 20)
            return p
        except OSError:
            continue
    sys.exit("No usable font found. Edit FONT_CANDIDATES.")


def wrap(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(" "), ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if draw.textlength(trial, font=font) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def pick_color(img):
    if TEXT_COLOR != "auto":
        return TEXT_COLOR
    top = img.crop((0, 0, img.width, TOP_BOX_HEIGHT)).convert("L")
    avg = sum(top.getdata()) / (top.width * top.height)
    return "white" if avg < 128 else "black"


def embed(path_in, path_out, caption, font_path):
    img = Image.open(path_in).convert("RGB")
    draw = ImageDraw.Draw(img)
    max_w = img.width - 2 * PAD_X
    max_h = TOP_BOX_HEIGHT - 2 * PAD_Y

    # biggest font size whose wrapped text fits inside the box
    for size in range(MAX_FONT, MIN_FONT - 1, -2):
        font = ImageFont.truetype(font_path, size)
        lines = wrap(draw, caption, font, max_w)
        line_h = int(size * LINE_SPACING)
        if line_h * len(lines) <= max_h:
            break

    fill = pick_color(img)
    outline = "black" if fill == "white" else "white"
    stroke = max(2, size // 14)
    y = PAD_Y + (max_h - line_h * len(lines)) / 2   # vertically centred in the box
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(((img.width - w) / 2, y), ln, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=outline)
        y += line_h
    img.save(path_out, quality=95)


def api(method, data=None, files=None, strict=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    while True:
        r = requests.post(url, data=data, files=files, timeout=180)
        j = r.json()
        if j.get("ok"):
            return j["result"]
        if r.status_code == 429:                       # rate limited -> wait and retry
            wait = j["parameters"]["retry_after"] + 1
            print(f"  rate limited, waiting {wait}s")
            time.sleep(wait)
            if files:                                  # file handles were consumed; caller must reopen
                raise RuntimeError("retry")
            continue
        if not strict:
            return None
        sys.exit(f"Telegram error: {j}")


def log_ids(ids):
    os.makedirs(OUT_DIR, exist_ok=True)
    old = json.load(open(LOG_FILE)) if os.path.exists(LOG_FILE) else []
    json.dump(old + ids, open(LOG_FILE, "w"))


def tg_send(path, caption, as_file):
    method, field = ("sendDocument", "document") if as_file else ("sendPhoto", "photo")
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption[:1024]
    while True:
        try:
            with open(path, "rb") as f:
                res = api(method, data, {field: f})
            log_ids([res["message_id"]])
            return
        except RuntimeError:
            continue


def tg_send_album(paths, captions, as_file):
    """Send up to 10 images as one album. Each item may carry its own caption."""
    kind = "document" if as_file else "photo"
    while True:
        handles, media, files = [], [], {}
        try:
            for i, p in enumerate(paths):
                fh = open(p, "rb")
                handles.append(fh)
                files[f"f{i}"] = fh
                item = {"type": kind, "media": f"attach://f{i}"}
                if captions and captions[i]:
                    item["caption"] = captions[i][:1024]
                media.append(item)
            res = api("sendMediaGroup",
                      {"chat_id": CHAT_ID, "media": json.dumps(media)}, files)
            log_ids([m["message_id"] for m in res])
            return
        except RuntimeError:
            continue
        finally:
            for fh in handles:
                fh.close()


def delete_ids(ids):
    for i in range(0, len(ids), 100):                  # deleteMessages accepts up to 100 ids
        # strict=False: ids that don't exist / can't be deleted are simply skipped
        api("deleteMessages", {"chat_id": CHAT_ID, "message_ids": json.dumps(ids[i:i + 100])},
            strict=False)
        if i and (i // 100) % 20 == 0:
            print(f"  swept up to id {ids[min(i + 99, len(ids) - 1)]}")
        time.sleep(0.05)
    print(f"asked Telegram to delete {len(ids)} message ids")


def delete_logged():
    if not os.path.exists(LOG_FILE):
        sys.exit("No sent_ids.json found. Use: delete --probe")
    ids = json.load(open(LOG_FILE))
    delete_ids(ids)
    os.remove(LOG_FILE)


def delete_probe(count):
    """For messages sent before logging: send a marker message, then sweep ids below it.
    count=None sweeps EVERYTHING from message id 1 up to the marker."""
    probe = api("sendMessage", {"chat_id": CHAT_ID, "text": "cleaning up..."})["message_id"]
    first = 1 if count is None else max(1, probe - count)
    delete_ids(list(range(first, probe + 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("actions", nargs="+", choices=["embed", "send", "delete"])
    ap.add_argument("--raw", action="store_true", help="send originals with Telegram captions")
    ap.add_argument("--as-file", action="store_true")
    ap.add_argument("--start", type=int, default=FIRST)
    ap.add_argument("--end", type=int, default=LAST)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--both", action="store_true",
                    help="send the captioned (embedded-text) images AND the Telegram caption")
    ap.add_argument("--album", action="store_true", help="send in albums of 10")
    ap.add_argument("--probe", action="store_true", help="delete: sweep recent ids instead of the log")
    ap.add_argument("--all", action="store_true", help="delete --probe: sweep every id in the chat")
    ap.add_argument("--count", type=int, default=150, help="delete --probe: how many recent ids to sweep")
    a = ap.parse_args()

    if "delete" in a.actions:
        if a.probe or a.all:
            if a.all and input("Sweep EVERY message id in the chat? (yes/no) ").strip() != "yes":
                sys.exit("cancelled")
            delete_probe(None if a.all else a.count)
        else:
            delete_logged()
        if "send" not in a.actions and "embed" not in a.actions:
            return

    captions = load_captions()
    expected = LAST - FIRST + 1
    if len(captions) != expected:
        sys.exit(f"Found {len(captions)} captions but {expected} images. Fix captions.txt.")

    nums = range(a.start, a.end + 1)
    if a.test:
        nums = [a.start]
    os.makedirs(OUT_DIR, exist_ok=True)

    if "embed" in a.actions:
        font_path = find_font_path()
        for n in nums:
            embed(os.path.join(IMG_DIR, f"{n}.jpg"), os.path.join(OUT_DIR, f"{n}.jpg"),
                  captions[n - FIRST], font_path)
            print(f"embedded {n}.jpg")

    if "send" in a.actions and not a.test:
        nums = list(nums)
        use_orig = a.raw and not a.both
        src = (lambda n: os.path.join(IMG_DIR, f"{n}.jpg")) if use_orig else \
              (lambda n: os.path.join(OUT_DIR, f"{n}.jpg"))
        cap = (lambda n: captions[n - FIRST]) if (a.raw or a.both) else (lambda n: None)

        if a.album:
            for i in range(0, len(nums), ALBUM_SIZE):
                chunk = nums[i:i + ALBUM_SIZE]
                tg_send_album([src(n) for n in chunk], [cap(n) for n in chunk], a.as_file)
                print(f"sent album {chunk[0]}-{chunk[-1]}")
                time.sleep(5)
        else:
            for n in nums:
                tg_send(src(n), cap(n), a.as_file)
                print(f"sent {n}.jpg")
                time.sleep(3.2)        # groups allow ~20 msgs/min


if __name__ == "__main__":
    main()
