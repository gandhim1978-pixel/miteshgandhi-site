#!/usr/bin/env python3
"""Social preview images (1200 x 630) and Instagram images for every reflection page.

For each reflection-*.html in the site root and queue/, builds og/<slug>.jpg
from the page's first photo (or the override in SOURCES) and sets og:image,
og:image:width, og:image:height and twitter:image on the page.

- Wide photos fill the frame.
- Portrait or squarish photos are never cropped: the whole photo sits on a
  cobalt background with the kicker and title beside it, so faces stay in frame.
- Pages with no suitable photo get a cobalt title card. mitesh.jpg is never used.

It also makes ig/<slug>.jpg, 1080 wide, for the image in feed-spirit.xml
(which posts to Instagram): the article's photo uncropped, with cobalt at the
sides (or top and bottom) if it is outside Instagram's 4:5 to 1.91:1 range.

Run: python3 scripts/og_images.py   (re-run after adding or changing a piece)
"""
import html
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "og"
IG_OUT = ROOT / "ig"
IG_W = 1080
IG_TALLEST = 4 / 5  # Instagram crops anything taller than 4:5
IG_WIDEST = 1.91  # or wider than 1.91:1
FONTS = Path(__file__).resolve().parent / "fonts"
W, H = 1200, 630
COBALT_DEEP = (18, 31, 85)
FLUOR = (214, 234, 76)
PALE = (238, 241, 250)
WIDE = 1.4  # photos at least this wide fill the frame; narrower ones are shown whole

# Page slug -> photo to use instead of the page's first photo (None = title card)
SOURCES = {
    "wanted-to-disappear": "mitesh-age4.jpg",
    "stopped-performing": None,
    "first-ten-seconds": None,
    "looking-vs-seeing": None,
    "stillness": None,
}
NEVER = {"mitesh.jpg"}


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=fnt) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def draw_text(img, kicker, title, x, width, size=76):
    draw = ImageDraw.Draw(img)
    kfont = font("Figtree-SemiBold.ttf", 24)
    while True:
        tfont = font("InstrumentSerif-Regular.ttf", size)
        lines = wrap(draw, title, tfont, width)
        if len(lines) * size * 1.05 <= 380 or size <= 40:
            break
        size -= 4
    kick = kicker.upper()
    kh = 24 + 28
    th = int(len(lines) * size * 1.05)
    y = (H - kh - th - 70) // 2
    spaced_x = x
    for ch in kick:  # letter-spacing, as on the page
        draw.text((spaced_x, y), ch, font=kfont, fill=FLUOR)
        spaced_x += draw.textlength(ch, font=kfont) + 3
    y += kh
    for line in lines:
        draw.text((x, y), line, font=tfont, fill=PALE)
        y += int(size * 1.05)
    draw.text((x, y + 30), "miteshgandhi.com", font=font("Figtree-SemiBold.ttf", 22), fill=(154, 164, 201))


def build(photo, kicker, title):
    img = Image.new("RGB", (W, H), COBALT_DEEP)
    if photo is None:
        draw_text(img, kicker, title, 110, W - 220, size=104)
        return img
    src = Image.open(photo).convert("RGB")
    ratio = src.width / src.height
    if ratio >= WIDE:
        scale = max(W / src.width, H / src.height)
        src = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
        left, top = (src.width - W) // 2, (src.height - H) // 2
        return src.crop((left, top, left + W, top + H))
    pad = 40
    scale = min((H - 2 * pad) / src.height, (W * 0.5) / src.width)
    src = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    img.paste(src, (pad + 20, (H - src.height) // 2))
    text_x = pad + 20 + src.width + 60
    draw_text(img, kicker, title, text_x, W - text_x - 70)
    return img


def build_ig(photo, kicker, title):
    if photo is None:
        img = Image.new("RGB", (IG_W, round(IG_W / IG_TALLEST)), COBALT_DEEP)
        global W, H
        W, H = img.size
        try:
            draw_text(img, kicker, title, 90, IG_W - 180, size=96)
        finally:
            W, H = 1200, 630
        return img
    src = Image.open(photo).convert("RGB")
    if src.width / src.height > IG_WIDEST:
        src = src.resize((IG_W, round(src.height * IG_W / src.width)), Image.LANCZOS)
        img = Image.new("RGB", (IG_W, -(-IG_W * 100 // round(IG_WIDEST * 100))), COBALT_DEEP)
        img.paste(src, (0, (img.height - src.height) // 2))
        return img
    if src.width / src.height >= IG_TALLEST:
        return src.resize((IG_W, round(src.height * IG_W / src.width)), Image.LANCZOS)
    h = round(IG_W / IG_TALLEST)
    src = src.resize((round(src.width * h / src.height), h), Image.LANCZOS)
    img = Image.new("RGB", (IG_W, h), COBALT_DEEP)
    img.paste(src, ((IG_W - src.width) // 2, 0))
    return img


def first_photo(text):
    for name in re.findall(r'<img src="/([^"/]+)"', text):
        if name not in NEVER:
            return name
    return None


def find(name):
    for d in (ROOT, ROOT / "queue"):
        if (d / name).exists():
            return d / name
    raise SystemExit(f"Cannot find {name}")


def set_meta(text, slug):
    url = f"https://miteshgandhi.com/og/{slug}.jpg"
    text = re.sub(r'\n<meta property="og:image(:width|:height)?" content="[^"]*">', "", text)
    text = re.sub(r'\n<meta name="twitter:image" content="[^"]*">', "", text)
    tags = (f'\n<meta property="og:image" content="{url}">'
            f'\n<meta property="og:image:width" content="{W}">'
            f'\n<meta property="og:image:height" content="{H}">')
    text, n = re.subn(r'(<meta property="og:url" content="[^"]*">)', lambda m: m.group(1) + tags, text, count=1)
    if not n:
        raise SystemExit(f"{slug}: no og:url tag")
    text, n = re.subn(r'(<meta name="twitter:card" content="[^"]*">)',
                      lambda m: m.group(1) + f'\n<meta name="twitter:image" content="{url}">', text, count=1)
    if not n:
        raise SystemExit(f"{slug}: no twitter:card tag")
    return text


def main():
    OUT.mkdir(exist_ok=True)
    IG_OUT.mkdir(exist_ok=True)
    pages = sorted(ROOT.glob("reflection-*.html")) + sorted((ROOT / "queue").glob("reflection-*.html"))
    for page in pages:
        slug = page.stem.removeprefix("reflection-")
        text = page.read_text()
        kicker = html.unescape(re.search(r'<p class="kicker">(.*?)</p>', text).group(1))
        title = html.unescape(re.search(r"<h1>(.*?)</h1>", text, re.S).group(1)).strip()
        name = SOURCES[slug] if slug in SOURCES else first_photo(text)
        photo = find(name) if name else None
        build(photo, kicker, title).save(OUT / f"{slug}.jpg", quality=86, optimize=True, progressive=True)
        build_ig(photo, kicker, title).save(IG_OUT / f"{slug}.jpg", quality=88, optimize=True, progressive=True)
        page.write_text(set_meta(text, slug))
        print(f"og/{slug}.jpg  <-  {name or 'title card'}")


if __name__ == "__main__":
    main()
