# miteshgandhi.com: guide for Claude

This is Mitesh Gandhi's personal website. Mitesh is an Independent Prescribing optometrist and owner of Clamp Optometrists, Cambridge. He is busy and not technical: keep explanations short and plain, and do the technical work yourself.

## Purpose of the site

Help thoughtful readers get to know Mitesh's story, trust him and follow his writing, and, for those who are curious, offer a gentle invitation to experience Sahaja Yoga meditation (always free).

## The three strands of reflections

| Strand | Kicker on page | What it does for the reader |
| --- | --- | --- |
| Being Seen | Being Seen · Reflection NN | "He cares about people." |
| Turning Points | Turning Points · NN | "He's been where I am, and turned it around." |
| Science and Spirit | Science and Spirit · NN | "How does he see the world like that?" |

## Voice

- Warm, humble, reflective. Never boastful.
- Spend most of the piece in the struggle; let success arrive briefly.
- "We" for wins, "I" for mistakes. Credit the people who helped.
- Short paragraphs, rhythm, pauses. Start in the middle of a moment.
- One metaphor per piece, ideally drawn from the eye.
- Spirituality is felt, not preached: one or two gentle lines.
- End with a single reflective question as the closing paragraph.
- British English.

## Firm lines

- Check with Mitesh before writing about family, health or difficult past events.
- Never present meditation as a medical cure.
- Science and Spirit pieces are reflections, not clinical claims.
- No patient-identifiable details or images.
- Never invent facts. If a detail is unknown, ask Mitesh.

## How to add a new reflection (publishing queue)

New pieces are never published straight away. They go into a queue and a GitHub Action (.github/workflows/publish-queue.yml) publishes them every Tuesday at 7am UK time, one per week.

1. Copy an existing reflection page (e.g. reflection-mountain.html) as the template; keep styling identical.
2. Save it as queue/reflection-<short-slug>.html. Update title, meta description, og tags, kicker, h1 and article body. Leave the pager as `<nav class="pager"></nav>`: the publish script fills it in and adds a "next" link to the previous piece.
3. Images go in queue/ with clear names (referenced as src="/name.jpg"), inside a div with class "photo", with good alt text. Captions in italic cobalt, never faint grey. They move to the site root on release.
4. Write a 60 to 100 word "petal" version for feed-spirit.xml: a one-line hook, a short scene, the turning point, a one-line moral and the piece's closing question, each as its own paragraph, using only facts from the article. Skip it for pieces in SPIRIT_FEED_SKIP.
5. Run `python3 scripts/queue.py add <short-slug> --label "<list label>" --summary "<short teaser>" --petal "<petal, paragraphs separated by \n\n>"`. The label is what reflections.html shows (e.g. "Turning Points 02", "Science and Spirit 02", "Reflection 07" for Being Seen); count queued pieces when numbering. It takes the next free Tuesday automatically; `--date YYYY-MM-DD` overrides.
6. Run `python3 scripts/og_images.py`. It makes the page's 1200 x 630 social preview image (og/<slug>.jpg) from its photo and sets og:image, og:image:width, og:image:height and twitter:image. Portrait photos go whole on cobalt so faces stay in frame. Never use mitesh.jpg; prefer Mitesh's own photos over Pexels where they fit (set them in SOURCES in the script).
7. Do not edit reflections.html, feed.xml or feed-spirit.xml by hand; the script does that on release (feed-spirit.xml carries every new piece, as its petal, except those listed in SPIRIT_FEED_SKIP in scripts/queue.py; the full article stays on the website).
8. Show Mitesh a short summary, including the release date, and ask before saving. When he approves, save directly to main so the Action can see it.

When Mitesh asks "what's scheduled?", run `python3 scripts/queue.py list` and show him the dates and titles in plain words. `python3 scripts/queue.py remove <slug>` takes a piece out; to move a date, edit queue/queue.json.

Queued pages are hidden from visitors by _redirects until release. To publish early, run the "Publish queued reflections" Action by hand on GitHub after changing the piece's date to today.

## Contact

hello@miteshgandhi.com
