#!/usr/bin/env python3
"""Generate and publish the Bible Maps index page (/bible-maps/).

  python3 site/build_maps.py [--apply]

Lists every page in seo/map-pages.json (add new map pages there first) with its excerpt, places
and the character whose story it belongs to.
"""
import html, json, sys
from storykit import CSS, FILTER_JS, ROOT, SITE, block, characters, esc, publish, script, wp

GENERIC = {"Bible Map", "Map of the Bible", "Biblical Geography", "Bible Places", "Interactive Map",
           "Old Testament", "New Testament"}
BOOKS = {"Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
         "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
         "Ecclesiastes", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah",
         "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke",
         "John", "Acts", "Romans", "Galatians", "Hebrews", "Revelation"}

entries = json.load(open(ROOT / "seo/map-pages.json"))
ids = [e["id"] for e in entries]
code, pages = wp.request("GET", f"/wp/v2/pages?include={','.join(map(str, ids))}&per_page=100&_fields=id,title,link,status")
page = {p["id"]: p for p in pages if p["status"] == "publish"}
owner = {m["id"]: c for c in characters() for m in c.get("maps", []) if m.get("id")}


def row(e):
    p = page[e["id"]]
    c = owner.get(e["id"])
    title = html.unescape(p["title"]["rendered"])
    t = "NT" if "New Testament" in e["tags"] else "OT"
    who = [c["name"]] if c else []
    names = {n.split(",")[0].split(" (")[0] for n in who}
    places = [x for x in e["tags"] if x not in GENERIC and x not in BOOKS and x not in names and not any(x in n for n in names)]
    return {"id": e["id"], "title": title, "link": p["link"], "t": t, "who": c, "places": places, "excerpt": e.get("excerpt", "")}


def card(r):
    c = r["who"]
    story = ""
    if c:
        live = [x for x in c.get("post_rows", []) if x["status"] == "publish"]
        story = (f'<a href="{esc(live[-1]["link"])}">{esc(c["name"])}’s story</a>' if live else f'{esc(c["name"])}’s story (coming soon)')
        if c.get("profile"):
            story += f' · <a href="{esc(c["profile"]["link"])}">Profile</a>'
    search = esc(" ".join([r["title"], c["name"] if c else "", " ".join(r["places"])]).lower())
    return (f'<article class="cw-card cw-map" data-t="{r["t"]}" data-s="{search}"><div class="cw-body">'
            + (f'<span class="cw-kicker">{esc(c["name"])}</span>' if c else '<span class="cw-kicker">Bible places</span>')
            + f'<h3><a href="{esc(r["link"])}">{esc(r["title"])}</a></h3>'
            + (f'<p>{esc(r["excerpt"])}</p>' if r["excerpt"] else "")
            + (f'<p class="cw-places">{esc(" · ".join(r["places"][:6]))}</p>' if r["places"] else "")
            + (f'<p class="cw-story">{story}</p>' if story else "")
            + f'<a class="cw-btn" href="{esc(r["link"])}">Open the map</a></div></article>')


MAP_CSS = """
.cw-map{border-top:3px solid var(--ink)}
.cw-map h3 a{color:var(--ink);text-decoration:none}
.cw-map .cw-btn{align-self:flex-start;margin-top:auto;padding:7px 14px;font-size:.8em}
.cw-places{font-size:.78em!important;color:var(--muted)!important;letter-spacing:.02em}
.cw-story{font-size:.82em!important}
.cw-story a{color:var(--accent);font-weight:600}
"""


def section(rows, t, label):
    rs = sorted((r for r in rows if r["t"] == t), key=lambda r: (r["who"]["name"] if r["who"] else "~" + r["title"]).lower())
    return (f'<section class="cw-sec"><h2>{label} <span>{len(rs)} maps</span></h2><div class="cw-grid">'
            + "".join(card(r) for r in rs) + "</div></section>")


def render():
    rows = [row(e) for e in entries if e["id"] in page]
    body = (
        f'<div class="cw"><style>{CSS}{MAP_CSS}</style>'
        '<p class="cw-intro">Interactive maps of where each story happened: the cities, roads, rivers and hills behind the text. '
        'Pan, zoom and tap the markers to see what happened at each place and how far people traveled.</p>'
        '<div class="cw-bar" role="search"><button type="button" data-f="all" aria-pressed="true">All</button>'
        '<button type="button" data-f="OT" aria-pressed="false">Old Testament</button>'
        '<button type="button" data-f="NT" aria-pressed="false">New Testament</button>'
        '<input type="search" placeholder="Search by person or place" aria-label="Search Bible maps"></div>'
        + section(rows, "OT", "Old Testament") + section(rows, "NT", "New Testament") +
        '<p class="cw-empty">No map matches that search yet.</p>'
        f'<p class="cw-intro" style="margin-top:26px;font-size:.95em">Every map belongs to a story. <a href="{SITE}/bible-characters/">See all the characters</a>.</p>'
        + script(FILTER_JS) + "</div>"
    )
    print(len(rows), "maps")
    return block(body)


if __name__ == "__main__":
    publish("bible-maps", "Bible Maps", render(),
            "Interactive Bible maps for Characters Worth Following: see where each story happened, from Hebron and Shiloh to Galilee and Jerusalem.",
            "--apply" in sys.argv)
