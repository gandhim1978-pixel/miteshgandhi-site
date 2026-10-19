#!/usr/bin/env python3
"""Publishing queue for reflections.

Queued pieces live in queue/ (page + any images) and are listed in
queue/queue.json with a release date. Every Tuesday at 7am UK time a GitHub
Action runs `publish`, which moves any piece whose date has arrived into the
site root, adds it to reflections.html and feed.xml (plus feed-spirit.xml for
Science and Spirit and The Inner Journey), and links the pager.

Commands:
  python3 scripts/queue.py list
  python3 scripts/queue.py add <slug> --label "Turning Points 02" [--summary "..."] [--date YYYY-MM-DD]
  python3 scripts/queue.py remove <slug>
  python3 scripts/queue.py publish [--now YYYY-MM-DDTHH:MM]
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "queue"
QUEUE_FILE = QUEUE_DIR / "queue.json"
LONDON = ZoneInfo("Europe/London")
RELEASE_HOUR = 7
TUESDAY = 1  # Monday is 0
SPIRIT_STRANDS = ("Science and Spirit", "The Inner Journey")  # also go in feed-spirit.xml


def load():
    if not QUEUE_FILE.exists():
        return []
    return json.loads(QUEUE_FILE.read_text())["items"]


def save(items):
    items.sort(key=lambda i: i["date"])
    QUEUE_FILE.write_text(json.dumps({"items": items}, indent=2, ensure_ascii=False) + "\n")


def page_name(slug):
    return f"reflection-{slug}.html"


def page_meta(path):
    text = path.read_text()
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
    title = html.unescape(re.sub(r"\s*\|\s*Mitesh Gandhi\s*$", "", title.strip()))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', text, re.S).group(1))
    return title, desc


def now_london(override=None):
    if override:
        return dt.datetime.fromisoformat(override).replace(tzinfo=LONDON)
    return dt.datetime.now(LONDON)


def next_free_tuesday(items, today):
    taken = {i["date"] for i in items}
    day = today + dt.timedelta(days=1)
    while day.weekday() != TUESDAY or day.isoformat() in taken:
        day += dt.timedelta(days=1)
    return day


def nice_date(iso):
    return dt.date.fromisoformat(iso).strftime("%a %-d %b %Y")


def cmd_list(args):
    items = load()
    if not items:
        print("Nothing scheduled.")
        return
    for i in items:
        page = QUEUE_DIR / page_name(i["slug"])
        title = page_meta(page)[0] if page.exists() else f"(missing page: {page.name})"
        print(f"{nice_date(i['date'])}, 7am  |  {i['label']}  |  {title}")


def cmd_add(args):
    items = load()
    page = QUEUE_DIR / page_name(args.slug)
    if not page.exists():
        sys.exit(f"Put the page at {page.relative_to(ROOT)} first.")
    if any(i["slug"] == args.slug for i in items):
        sys.exit(f"{args.slug} is already queued.")
    if (ROOT / page.name).exists():
        sys.exit(f"{page.name} is already live.")
    if args.date:
        date = dt.date.fromisoformat(args.date)
        if date.isoformat() in {i["date"] for i in items}:
            sys.exit(f"{nice_date(date.isoformat())} is already taken.")
    else:
        date = next_free_tuesday(items, now_london().date())
    text = page.read_text()
    files = sorted({m for m in re.findall(r'src="/([^"/]+)"', text) if (QUEUE_DIR / m).exists()})
    summary = args.summary or page_meta(page)[1]
    items.append({"slug": args.slug, "date": date.isoformat(), "label": args.label,
                  "summary": summary, "files": files})
    save(items)
    print(f"Queued {page.name} for {nice_date(date.isoformat())}, 7am.")


def cmd_remove(args):
    items = load()
    kept = [i for i in items if i["slug"] != args.slug]
    if len(kept) == len(items):
        sys.exit(f"{args.slug} is not in the queue.")
    save(kept)
    print(f"Removed {args.slug} from the queue (its files are still in queue/).")


def publish_one(item, when):
    slug, name = item["slug"], page_name(item["slug"])
    src = QUEUE_DIR / name
    title, desc = page_meta(src)

    # Previous newest piece = top of the reflections list
    listing_path = ROOT / "reflections.html"
    listing = listing_path.read_text()
    prev = re.search(r'<ul class="list">\s*<li><a href="/(reflection-[^"]+\.html)">.*?<h2>(.*?)</h2>', listing, re.S)

    # New page: pager points back to the previous piece
    text = src.read_text()
    pager = '<nav class="pager"></nav>'
    if prev:
        pager = f'<nav class="pager"><a href="/{prev.group(1)}">← {prev.group(2)}</a></nav>'
    text, n = re.subn(r'<nav class="pager">.*?</nav>', pager, text, count=1, flags=re.S)
    if not n:
        sys.exit(f"{name} has no pager nav.")
    (ROOT / name).write_text(text)
    src.unlink()
    for f in item["files"]:
        shutil.move(str(QUEUE_DIR / f), str(ROOT / f))

    # Previous page: add a "next" link if it lacks one
    if prev:
        prev_path = ROOT / prev.group(1)
        prev_text = prev_path.read_text()
        if 'class="next"' not in prev_text:
            link = f'<a class="next" href="/{name}">{html.escape(title, quote=False)} →</a>'
            prev_text = re.sub(r'(<nav class="pager">.*?)(</nav>)', lambda m: m.group(1) + link + m.group(2),
                               prev_text, count=1, flags=re.S)
            prev_path.write_text(prev_text)

    # Reflections list
    li = (f'  <li><a href="/{name}"><span class="n">{html.escape(item["label"], quote=False)}</span>'
          f'<h2>{html.escape(title, quote=False)}</h2><p>{html.escape(item["summary"], quote=False)}</p></a></li>\n')
    listing, n = re.subn(r'(<ul class="list">\n)', lambda m: m.group(1) + li, listing, count=1)
    if not n:
        sys.exit("Could not find the list in reflections.html.")
    # A new strand joins the page kicker with its first piece ("Reflection NN" is Being Seen)
    strand = re.sub(r"\s*\d+$", "", item["label"])
    kicker = re.search(r'<p class="kicker">(.*?)</p>', listing)
    if strand != "Reflection" and kicker and strand not in kicker.group(1):
        listing = listing[:kicker.end(1)] + f" · {strand}" + listing[kicker.end(1):]
    listing_path.write_text(listing)

    # Feeds: every piece goes in feed.xml; Science and Spirit and The Inner Journey also in feed-spirit.xml
    stamp = format_datetime(when)
    url = f"https://miteshgandhi.com/{name}"
    entry = ("<item>\n"
             f"<title>{html.escape(title, quote=False)}</title>\n"
             f"<link>{url}</link>\n"
             f'<guid isPermaLink="true">{url}</guid>\n'
             f"<pubDate>{stamp}</pubDate>\n"
             f"<description>{html.escape(desc, quote=False)}</description>\n"
             "</item>\n")
    add_to_feed("feed.xml", entry, stamp)
    if strand in SPIRIT_STRANDS:
        add_to_feed("feed-spirit.xml", entry, stamp)
    print(f"Published {name}: {title}")


def add_to_feed(filename, entry, stamp):
    feed_path = ROOT / filename
    feed = feed_path.read_text()
    feed, n = re.subn(r"(<!--\s*NEW ITEMS GO HERE.*?-->\n)", lambda m: m.group(1) + entry, feed, count=1)
    if not n:
        sys.exit(f"Could not find the NEW ITEMS GO HERE comment in {filename}.")
    feed = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", f"<lastBuildDate>{stamp}</lastBuildDate>", feed)
    feed_path.write_text(feed)


def cmd_publish(args):
    now = now_london(args.now)
    items = load()
    due = [i for i in items
           if dt.date.fromisoformat(i["date"]) < now.date()
           or (i["date"] == now.date().isoformat() and now.hour >= RELEASE_HOUR)]
    if not due:
        print("Nothing due.")
        return
    for item in due:
        date = dt.date.fromisoformat(item["date"])
        publish_one(item, dt.datetime(date.year, date.month, date.day, RELEASE_HOUR, tzinfo=LONDON))
    save([i for i in items if i not in due])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    a = sub.add_parser("add")
    a.add_argument("slug")
    a.add_argument("--label", required=True, help='List label, e.g. "Turning Points 02"')
    a.add_argument("--summary", help="Short teaser for reflections.html (defaults to the meta description)")
    a.add_argument("--date", help="Override the release date (YYYY-MM-DD)")
    a.set_defaults(fn=cmd_add)
    r = sub.add_parser("remove")
    r.add_argument("slug")
    r.set_defaults(fn=cmd_remove)
    pub = sub.add_parser("publish")
    pub.add_argument("--now", help="Pretend it is this UK time, for testing")
    pub.set_defaults(fn=cmd_publish)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
