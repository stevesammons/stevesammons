#!/usr/bin/env python3
"""Give every character profile page a typographic card instead of a portrait.

Portraits belong to the posts (the short reads). Profile pages get a card from site/cards.py:
the character's name, "Bible character profile", and the testament in the footer line.

  python3 site/profile_cards.py sample          # write a few cards to site/cards/ to look at
  python3 site/profile_cards.py apply [PAGE_ID]  # all profile pages in stories.json (or one); --force remakes

For each page it backs up content and featured_media to backups/, uploads the card, sets it as the
featured image (search and social), removes the inline portrait (the page's only image), and shows
the card at the top of the page, just after the "Back to the story" card, between <!-- ss-card -->
markers so a re-run replaces it. Old portraits stay in the media library.
"""
import html, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "site"))
import wp  # noqa: E402
from cards import OUT, card  # noqa: E402

SUB = "Bible character profile"
TESTAMENT = {"OT": "Old Testament", "NT": "New Testament"}
TOP_E = "<!-- ss-back:end -->"
CARD_S, CARD_E = "<!-- ss-card -->", "<!-- /ss-card -->"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def profiles():
    chars = json.loads((ROOT / "site" / "stories.json").read_text())["characters"]
    return [(c["profile"]["id"], c) for c in chars if c.get("profile") and c["profile"].get("id")]


def headline(page_title):
    return html.unescape(page_title).replace("’", "'").strip()


def remove_portrait(raw):
    raw, n = re.subn(r"<!-- wp:image\b[^>]*-->\s*<figure\b.*?</figure>\s*<!-- /wp:image -->\s*", "", raw, flags=re.S)
    if not n:
        raw, n = re.subn(r"<img\b[^>]*>\s*", "", raw, count=1)
    return raw, n


def place_card(raw, tag):
    """Put the card just after the top back-link card (or at the top), never adding blocks to a classic page."""
    snippet = f"{CARD_S}{tag}{CARD_E}"
    if CARD_S in raw:
        return re.sub(re.escape(CARD_S) + r".*?" + re.escape(CARD_E), lambda m: snippet, raw, flags=re.S)
    classic = "<!-- wp:" not in raw
    i = raw.find(TOP_E)
    if i >= 0:
        j = i + len(TOP_E)
        close = re.match(r"\s*<!-- /wp:html -->", raw[j:])
        if close:  # the back link sits in its own Custom HTML block: add ours as the next block
            k = j + close.end()
            return raw[:k] + f"\n\n<!-- wp:html -->{snippet}<!-- /wp:html -->" + raw[k:]
        return raw[:j] + "\n" + snippet + raw[j:]
    m = re.match(r"(\s*(?:<meta[^>]*>\s*)?(?:<!-- wp:html -->\s*)?<div[^>]*>)", raw)
    if m and (classic or raw.lstrip().startswith(("<!-- wp:html", "<meta"))):
        return raw[:m.end()] + snippet + raw[m.end():]
    if classic:
        return snippet + "\n" + raw
    return f"<!-- wp:html -->{snippet}<!-- /wp:html -->\n\n" + raw


def make(pid, c, title):
    h = headline(title)
    k = TESTAMENT.get(c["t"], "")
    OUT.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")[:50]
    f = OUT / f"{slug}-profile-card.jpg"
    card(h, SUB, k, pid).save(f, quality=84, optimize=True, progressive=True)
    return h, f


def apply_one(pid, c):
    code, p = wp.request("GET", f"/wp/v2/pages/{pid}?context=edit&_fields=id,title,link,content,featured_media")
    if code != 200:
        return f"FAIL read {code}"
    (ROOT / "backups").mkdir(exist_ok=True)
    (ROOT / "backups" / f"profile-{pid}-before-card.json").write_text(json.dumps(p))
    raw = p["content"]["raw"]
    if CARD_S in raw and p["featured_media"] and "--force" not in sys.argv:
        return "ok skipped (already has its card)"
    h, f = make(pid, c, p["title"]["raw"])
    code, m = wp.request("POST", "/wp/v2/media", f.read_bytes(),
                         {"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{f.name}"'})
    if code not in (200, 201):
        return f"FAIL upload {code}"
    alt = f"{h}: {SUB}"
    wp.request("POST", f"/wp/v2/media/{m['id']}", json.dumps({"alt_text": alt, "title": alt}).encode(), {"Content-Type": "application/json"})
    tag = (f'<img class="ss-profile-card" src="{m["source_url"]}" alt="{html.escape(alt)}" width="1600" height="900" '
           'style="display:block;width:100%;height:auto;margin:0 0 24px;border-radius:4px;">')
    new = raw if CARD_S in raw else remove_portrait(raw)[0]
    new = place_card(new, tag)
    body = {"content": new, "featured_media": m["id"]}
    code, r = wp.request("POST", f"/wp/v2/pages/{pid}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    if code != 200:
        return f"FAIL save {code} {str(r)[:120]}"
    time.sleep(0.5)
    req = urllib.request.Request(p["link"] + f"?v={int(time.time())}", headers={"User-Agent": UA})
    try:
        live = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        return f"CHECK fetch {e}"
    imgs = re.findall(r"<img\b[^>]*>", live[live.find("entry-content"):] if "entry-content" in live else live)
    has_card = m["source_url"].rsplit(".", 1)[0] in live
    portraits = [x for x in imgs if "profile-card" not in x and re.search(r"uploads/", x) and "ss-rel" not in x]
    backs = live.count('class="ss-back')
    ok = has_card and backs in (0, 2)
    return ("ok" if ok else "CHECK") + f" card={has_card} back_links={backs} other_imgs={len(portraits)} media={m['id']} old={p['featured_media']}"


if __name__ == "__main__":
    items = profiles()
    if sys.argv[1:2] == ["sample"]:
        for pid, c in [x for x in items if x[1]["name"] in ("Caleb", "Shadrach, Meshach and Abednego", "Nicodemus", "James, son of Zebedee")]:
            print(make(pid, c, c["profile"].get("title") or c["name"]))
        sys.exit()
    if sys.argv[1:2] == ["apply"]:
        only = next((int(a) for a in sys.argv[2:] if a.isdigit()), None)
        results = []
        for pid, c in items:
            if only and pid != only:
                continue
            res = apply_one(pid, c)
            results.append((pid, c["name"], res))
            print(pid, c["name"], "|", res, flush=True)
        (ROOT / "backups" / "profile-cards-results.json").write_text(json.dumps(results, indent=1))
        print(sum(r[2].startswith("ok") for r in results), "of", len(results), "pages ok")
