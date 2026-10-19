#!/usr/bin/env python3
"""Search tags for every public page and every queued reflection.

- <link rel="canonical"> so Google knows each page's one official address.
- A JSON-LD block (hidden labels Google reads): BlogPosting for each
  reflection (headline, description, picture, date, author), Person for the
  home page.

datePublished comes from feed.xml for released pieces and from
queue/queue.json for queued ones; scripts/queue.py sets it again on release.
Run: python3 scripts/seo.py   (scripts/og_images.py also runs it)
"""
import html
import json
import re
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://miteshgandhi.com"
MAIN_PAGES = ("index.html", "story.html", "reflections.html", "blog.html")
AUTHOR = {"@type": "Person", "name": "Mitesh Gandhi", "url": f"{SITE}/"}
PERSON = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Mitesh Gandhi",
    "url": f"{SITE}/",
    "image": f"{SITE}/mitesh.jpg",
    "jobTitle": "Independent Prescribing Optometrist",
    "worksFor": {"@type": "Optician", "name": "Clamp Optometrists",
                 "address": {"@type": "PostalAddress", "addressLocality": "Cambridge", "addressCountry": "GB"}},
    "email": "mailto:hello@miteshgandhi.com",
}


def page_url(name):
    return f"{SITE}/" if name == "index.html" else f"{SITE}/{name}"


def release_dates():
    dates = {}
    feed = (ROOT / "feed.xml").read_text()
    for name, stamp in re.findall(r"<link>[^<]*/([^/<]+\.html)</link>\s*<guid[^>]*>[^<]*</guid>\s*<pubDate>([^<]+)</pubDate>", feed):
        dates[name] = parsedate_to_datetime(stamp).date().isoformat()
    queue = ROOT / "queue" / "queue.json"
    if queue.exists():
        for item in json.loads(queue.read_text())["items"]:
            dates[f"reflection-{item['slug']}.html"] = item["date"]
    return dates


def meta(text, pattern):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def ld_block(data):
    body = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def update(path, dates):
    name = path.name
    text = path.read_text()
    url = page_url(name)
    text = re.sub(r'<link rel="canonical" href="[^"]*">\n', "", text)
    text = re.sub(r'<script type="application/ld\+json">.*?</script>\n', "", text, flags=re.S)
    text, n = re.subn(r"(<title>.*?</title>\n)", lambda m: m.group(1) + f'<link rel="canonical" href="{url}">\n', text, count=1, flags=re.S)
    if not n:
        raise SystemExit(f"{name}: no <title>")
    data = None
    if name == "index.html":
        data = dict(PERSON, description=meta(text, r'<meta name="description" content="(.*?)">'))
    elif name.startswith("reflection-"):
        data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": meta(text, r"<h1>(.*?)</h1>"),
            "description": meta(text, r'<meta name="description" content="(.*?)">'),
            "image": meta(text, r'<meta property="og:image" content="(.*?)">'),
            "url": url,
            "mainEntityOfPage": url,
            "inLanguage": "en-GB",
            "author": AUTHOR,
            "publisher": AUTHOR,
        }
        if name in dates:
            data["datePublished"] = dates[name]
        data = {k: v for k, v in data.items() if v}
    if data:
        text = text.replace("</head>", ld_block(data) + "</head>", 1)
    path.write_text(text)


def main():
    dates = release_dates()
    pages = [ROOT / p for p in MAIN_PAGES if (ROOT / p).exists()]
    pages += sorted(ROOT.glob("reflection-*.html")) + sorted((ROOT / "queue").glob("reflection-*.html"))
    for page in pages:
        update(page, dates)
    print(f"Search tags updated on {len(pages)} pages")


if __name__ == "__main__":
    main()
