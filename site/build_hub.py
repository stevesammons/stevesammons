#!/usr/bin/env python3
"""Generate and publish the Characters hub page (/bible-characters/).

  python3 site/stories.py              # refresh the data first
  python3 site/build_hub.py [--apply]

Each card shows the character's five parts (read, gospel quartet, podcast, profile, map). Scheduled
reflections show their month and are upgraded in the browser once the post is public.
"""
import sys
from storykit import (CSS, DEEP_DIVES, FILTER_JS, SERIES, SITE, YOUTUBE, block, characters, chips, esc,
                      publish, script)

chars = characters()


def card(c):
    name = esc(c["name"])
    pic = (f'<img src="{esc(c["img"])}" alt="Imagined portrait of {name}" loading="lazy" decoding="async" width="400" height="225">'
           if c.get("img") else f'<div class="cw-noimg" aria-hidden="true">{esc(c["name"][0])}</div>')
    rows = c.get("post_rows", [])
    live = [r for r in rows if r["status"] == "publish"]
    title = (f'<a href="{esc(live[-1]["link"])}">{name}</a>' if live else name)
    search = esc((c["name"] + " " + " ".join(r["title"] for r in rows) + (" " + c["song"]["title"] if c.get("song") else "")).lower())
    song = ' data-song="1"' if c.get("song") else ""
    lede = f'<p>{esc(c["summary"])}</p>' if c.get("summary") else ""
    if live:
        lede = f'<p><b>{esc(live[-1]["title"])}.</b> {esc(c.get("summary", ""))}</p>'
    return (f'<article class="cw-card" data-t="{c["t"]}"{song} data-s="{search}">{pic}<div class="cw-body">'
            f'<h3>{title}</h3>{lede}{chips(c)}</div></article>')


def section(t, label):
    cs = sorted((c for c in chars if c["t"] == t), key=lambda c: c["name"].lower())
    return (f'<section class="cw-sec"><h2>{label} <span>{len(cs)} people</span></h2>'
            '<div class="cw-grid">' + "".join(card(c) for c in cs) + "</div></section>")


def render():
    n_pub = sum(1 for c in chars for r in c.get("post_rows", []) if r["status"] == "publish")
    n_song = sum(1 for c in chars if c.get("song"))
    n_deep = sum(1 for c in chars if c.get("deep"))
    n_maps = len({m["link"] for c in chars for m in c.get("maps", [])})
    steps = (
        '<ol class="cw-steps">'
        '<li><b>Read</b>A short reflection, about three minutes.</li>'
        f'<li><b>Gospel Quartet</b>A gospel quartet song to remember it by. <a href="{SITE}/songs/">Songs</a></li>'
        f'<li><b>Podcast</b>The long version, 10 to 45 minutes. <a href="{DEEP_DIVES}" target="_blank" rel="noopener">Podcast</a></li>'
        '<li><b>Profile</b>Who they were, from the text itself.</li>'
        f'<li><b>Map</b>Where it happened. <a href="{SITE}/bible-maps/">Maps</a></li>'
        "</ol>"
    )
    body = (
        f'<div class="cw"><style>{CSS}</style>'
        f'<p class="cw-intro"><b>{SERIES}.</b> One person from the Bible at a time, told in five parts. Start with the short read, '
        'keep the song in your head, go deeper when you have time, then meet the person and see the place.</p>'
        + steps +
        '<div class="cw-bar" role="search"><button type="button" data-f="all" aria-pressed="true">All</button>'
        '<button type="button" data-f="OT" aria-pressed="false">Old Testament</button>'
        '<button type="button" data-f="NT" aria-pressed="false">New Testament</button>'
        f'<button type="button" data-f="song" aria-pressed="false">With a song ({n_song})</button>'
        '<input type="search" placeholder="Search by name or title" aria-label="Search Bible characters"></div>'
        + section("OT", "Old Testament") + section("NT", "New Testament") +
        '<p class="cw-empty">No one matches that search yet.</p>'
        f'<p class="cw-intro" style="margin-top:30px;font-size:.95em">{len(chars)} people · {n_pub} reflections · {n_song} songs · '
        f'{n_deep} podcast episodes · {n_maps} maps · a new story every week. <a href="{YOUTUBE}" target="_blank" rel="noopener">Songs on YouTube</a></p>'
        + script(FILTER_JS) + "</div>"
    )
    return block(body)


if __name__ == "__main__":
    content = render()
    print(len(chars), "characters")
    publish("bible-characters", "Bible Characters", content,
            "Characters Worth Following: every Bible character in five parts, a short read, a gospel quartet song, a podcast episode, a profile and an interactive map.",
            "--apply" in sys.argv)
