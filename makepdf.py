import re
from pathlib import Path
import img2pdf

SRC = Path(__file__).resolve().parent / "readmewhenyouneedme"
OUT = SRC / "pdfs"
OUT.mkdir(exist_ok=True)

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}

# Collect images by their number, e.g. "7.jpg" -> 7
images = {}
for f in SRC.iterdir():
    if f.suffix.lower() in EXTS:
        m = re.search(r"\d+", f.stem)
        if m:
            images[int(m.group())] = str(f)

def make_pdf(nums, name):
    files = [images[n] for n in nums if n in images]
    missing = [n for n in nums if n not in images]
    if missing:
        print(f"  warning, missing images: {missing}")
    with open(OUT / f"{name}.pdf", "wb") as fh:
        fh.write(img2pdf.convert(files))
    print(f"Created {name}.pdf ({len(files)} images)")

# Images 1-4 -> cover and contents
make_pdf(range(1, 5), "cover and contents")

# Images 5-124 in groups of 10
# True  = name by the rest's own count: 1-10, 11-20, ... 111-120
# False = name by original image numbers: 5-14, 15-24, ... 115-124
RENUMBER = True

for start in range(5, 125, 10):
    end = min(start + 9, 124)
    nums = range(start, end + 1)
    if RENUMBER:
        name = f"{start - 4}-{end - 4}"
    else:
        name = f"{start}-{end}"
    make_pdf(nums, name)
