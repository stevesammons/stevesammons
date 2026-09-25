#!/usr/bin/env python3
"""Build site/stories.json: every Bible character with the five parts of their story.

  1 Read       the short reflection post (Old Testament / New Testament categories)
  2 Gospel Quartet  the gospel quartet song on YouTube (@CharactersWorthFollowing)
  3 Podcast    the long-form podcast episode on Substack (sammons.substack.com)
  4 Profile    the character profile page
  5 Map        the interactive Bible map page(s)

  python3 site/stories.py          # refresh posts, songs and deep dives, report anything unmatched
  python3 site/stories.py --seed   # one-off: rebuild the character list from the live hub page

stories.json is committed. Character names, testament, summary, portrait, profile and map links
are curated there; posts, songs and deep dives are refreshed on every run. A new post is attached
to the character whose profile page it links to; otherwise it is reported and can be added by hand
("posts": [id]). Songs match on the name in the video title ("Title | Name Gospel Quartet Song"),
deep dives on the Substack post's tags, title or subtitle; the newest wins. Add "pinned": true to a
character's "song" or "deep" to keep it, and "aliases": [...] to match other spellings.
"""
import html, json, re, sys, urllib.parse as up, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp  # noqa: E402

OUT = ROOT / "site" / "stories.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
CHANNEL_ID = "UCuXn2l6fvPZCFTWCxkLr_pA"
SUBSTACK = "https://sammons.substack.com"
MAP_TAG = 1727


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    return urllib.request.urlopen(req, timeout=60).read()


def all_items(path):
    out, page = [], 1
    while True:
        code, d = wp.request("GET", f"{path}&per_page=100&page={page}")
        if code != 200 or not d:
            break
        out += d
        if len(d) < 100:
            break
        page += 1
    return out


def norm(s):
    s = html.unescape(s).lower().replace("&", " and ").replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z' ]", " ", s)).strip()


def keys(c):
    """Names a character can be matched on: full name, name before a comma or qualifier, aliases."""
    n = c["name"]
    out = {norm(n), norm(re.split(r",| the | of | son | \(", n)[0])}
    out |= {norm(a) for a in c.get("aliases", [])}
    return {k for k in out if len(k) > 2}


def load_site():
    code, cats = wp.request("GET", "/wp/v2/categories?slug=old-testament,new-testament&_fields=id,slug")
    t_of = {c["id"]: ("OT" if c["slug"] == "old-testament" else "NT") for c in cats}
    posts = all_items(f"/wp/v2/posts?categories={','.join(map(str, t_of))}&status=publish,future"
                      "&context=edit&_fields=id,title,status,date,link,slug,categories,content")
    pages = all_items("/wp/v2/pages?status=publish&context=edit&_fields=id,title,link,tags")
    return t_of, posts, pages


def post_row(p):
    link = p["link"] if p["status"] == "publish" else ""
    return {"id": p["id"], "title": html.unescape(p["title"]["raw"]), "status": p["status"],
            "date": p["date"][:10], "link": link}


def seed():
    """Rebuild the curated character list from the published hub page (the only copy of that data)."""
    t_of, posts, pages = load_site()
    by_link = {p["link"].rstrip("/"): p for p in posts}
    page_by_link = {p["link"].rstrip("/"): p for p in pages}
    code, hub = wp.request("GET", "/wp/v2/pages?slug=bible-characters&context=edit&_fields=content")
    raw = hub[0]["content"]["raw"]
    chars = []
    for a in re.findall(r'<article class="bc-card".*?</article>', raw, re.S):
        c = {"name": html.unescape(re.search(r"<h3>(.*?)</h3>", a).group(1)),
             "t": re.search(r'data-t="(\w+)"', a).group(1)}
        m = re.search(r'<img src="([^"]+)"', a)
        c["img"] = m.group(1) if m else None
        m = re.search(r"</h3><p>(.*?)</p>", a)
        c["summary"] = html.unescape(m.group(1)) if m else ""
        ids = [by_link[h.rstrip("/")]["id"] for h in re.findall(r'class="bc-read" href="([^"]+)"', a) if h.rstrip("/") in by_link]
        ids += [int(x) for x in re.findall(r'data-post="(\d+)"', a)]
        c["posts"] = ids
        c["profile"], c["maps"] = None, []
        for href, label in re.findall(r'<a href="([^"]+)">(Profile|Map|Place)</a>', a):
            pg = page_by_link.get(href.rstrip("/"))
            title = html.unescape(pg["title"]["raw"]) if pg else label
            if label == "Profile":
                c["profile"] = {"id": pg and pg["id"], "title": title, "link": href}
            else:
                c["maps"].append({"id": pg and pg["id"], "title": title, "link": href})
        chars.append(c)
    OUT.write_text(json.dumps({"characters": chars}, indent=1, ensure_ascii=False) + "\n")
    print(len(chars), "characters seeded from the hub")


def songs():
    """Every upload on the channel (RSS shows the latest 15; the uploads playlist page shows up to 100)."""
    found = {}
    try:
        s = get(f"https://www.youtube.com/playlist?list=UU{CHANNEL_ID[2:]}").decode("utf-8", "replace")
        d = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", s, re.S).group(1))

        def walk(o):
            if isinstance(o, dict):
                if "lockupViewModel" in o:
                    lv = o["lockupViewModel"]
                    t = lv["metadata"]["lockupMetadataViewModel"]["title"]["content"]
                    found.setdefault(lv["contentId"], {"id": lv["contentId"], "title": t})
                if "playlistVideoRenderer" in o:
                    r = o["playlistVideoRenderer"]
                    found.setdefault(r["videoId"], {"id": r["videoId"], "title": r["title"]["runs"][0]["text"]})
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
    except Exception as e:  # fall back to RSS alone
        print("uploads page not readable:", e)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    feed = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"))
    for e in feed.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        row = found.setdefault(vid, {"id": vid, "title": e.find("a:title", ns).text})
        row["date"] = e.find("a:published", ns).text[:10]
    out = []
    for v in found.values():
        m = re.match(r"(.+?)\s*\|\s*(.+?)\s+Gospel Quartet Song", html.unescape(v["title"]))
        if m:
            out.append({**v, "song": m.group(1).strip(), "who": m.group(2).strip()})
    return out


def deep_dives():
    rows, off = [], 0
    while True:
        batch = json.loads(get(f"{SUBSTACK}/api/v1/archive?sort=new&limit=50&offset={off}"))
        rows += batch
        if len(batch) < 50:
            break
        off += 50
    out = []
    for r in rows:
        if r.get("type") != "podcast":
            continue
        out.append({"url": f"{SUBSTACK}/p/{r['slug']}", "title": r["title"], "subtitle": r.get("subtitle") or "",
                    "minutes": round((r.get("podcast_duration") or 0) / 60), "date": r["post_date"][:10],
                    "tags": [t["name"] for t in r.get("postTags") or []],
                    # free episodes only: the audio plays in the post's podcast player
                    "audio": r.get("podcast_url") if r.get("audience") == "everyone" else None})
    return out


def match(chars, text_fields):
    """Characters whose name appears in any of the text fields (longest name wins)."""
    hits = []
    for c in chars:
        for k in keys(c):
            for f in text_fields:
                if re.search(rf"(^|\s){re.escape(k)}($|\s|')", norm(f)):
                    hits.append((len(k), c))
    hits.sort(key=lambda x: -x[0])
    return hits[0][1] if hits else None


def refresh():
    data = json.loads(OUT.read_text())
    chars = data["characters"]
    t_of, posts, pages = load_site()
    page_by_id = {p["id"]: p for p in pages}
    page_by_path = {up.urlparse(p["link"]).path.rstrip("/"): p for p in pages}
    by_post = {pid: c for c in chars for pid in c["posts"]}
    by_profile = {c["profile"]["id"]: c for c in chars if c.get("profile") and c["profile"].get("id")}
    rows = {}
    unassigned = []
    for p in posts:
        rows[p["id"]] = post_row(p)
        if p["id"] in by_post:
            continue
        linked = []
        for href in re.findall(r'href="([^"]+)"', p["content"]["raw"]):
            u = up.urlparse(href)
            if u.netloc and "stevesammons.com" not in u.netloc:
                continue
            pg = page_by_path.get(u.path.rstrip("/"))
            if pg:
                linked.append(pg)
        owner = next((by_profile[pg["id"]] for pg in linked if pg["id"] in by_profile), None)
        if owner:
            owner["posts"].append(p["id"])
            by_post[p["id"]] = owner
            print("attached post", p["id"], rows[p["id"]]["title"], "->", owner["name"])
        else:
            unassigned.append((p["id"], rows[p["id"]]["title"], [html.unescape(x["title"]["raw"]) for x in linked]))
    for c in chars:
        c["posts"] = [pid for pid in c["posts"] if pid in rows]
        c["post_rows"] = sorted((rows[pid] for pid in c["posts"]), key=lambda r: r["date"])
        for ref in [c.get("profile")] + c.get("maps", []):
            if ref and ref.get("id") in page_by_id:
                ref["link"] = page_by_id[ref["id"]]["link"]

    # Newest first: the first song and deep dive found for a character wins, unless one is pinned.
    unmatched, seen = [], set()
    for s in songs():
        c = match(chars, [s["who"]])
        if not c:
            unmatched.append(("song", s["title"]))
        elif ("song", c["name"]) not in seen and not (c.get("song") or {}).get("pinned"):
            seen.add(("song", c["name"]))
            c["song"] = {"id": s["id"], "title": s["song"], "url": f"https://www.youtube.com/watch?v={s['id']}"}
    dives = deep_dives()
    for d in dives:
        c = match(chars, d["tags"]) or match(chars, [d["subtitle"], d["title"]])
        if not c:
            unmatched.append(("deep dive", d["title"]))
        elif ("deep", c["name"]) not in seen and not (c.get("deep") or {}).get("pinned"):
            seen.add(("deep", c["name"]))
            c["deep"] = {k: d[k] for k in ("url", "title", "minutes", "date")}
    audio = {d["url"]: d["audio"] for d in dives}
    for c in chars:  # pinned episodes too
        if c.get("deep"):
            if audio.get(c["deep"]["url"]):
                c["deep"]["audio"] = audio[c["deep"]["url"]]
            else:
                c["deep"].pop("audio", None)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    n = lambda k: sum(1 for c in chars if c.get(k))
    print(f"{len(chars)} characters; {sum(len(c['posts']) for c in chars)} posts; {n('song')} songs; "
          f"{n('deep')} deep dives; {n('profile')} profiles; {sum(1 for c in chars if c['maps'])} with maps")
    for pid, title, linked in unassigned:
        print("UNASSIGNED post", pid, title, "links to:", linked)
    for kind, title in unmatched:
        print("UNMATCHED", kind, title)


def load():
    return json.loads(OUT.read_text())["characters"]


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed()
    refresh()
