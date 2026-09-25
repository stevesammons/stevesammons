#!/usr/bin/env python3
"""Let readers play the Substack companion podcast on the post instead of leaving the site.

  python3 podcast-player/apply.py ID [ID ...] [--apply]
  python3 podcast-player/apply.py --all [--apply]     # every published or scheduled post/page

For each sammons.substack.com/p/<slug> link in a post, the episode is looked up on Substack.
Public podcast episodes are written into the post together with player.js, as one Custom HTML
block (a base64 data: script, so the site's content filters can't mangle it). Links to episodes
that aren't out on Substack yet stay plain links; re-running after they go out adds them.
Only the content changes (status and schedule are untouched), and a post is only saved when its
player block would change. Each post is backed up to backups/ first. Without --apply: dry run.
"""
import base64, json, re, sys, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import wp  # noqa: E402

START, END = "<!-- ss-pod:start -->", "<!-- ss-pod:end -->"
PUB = "https://sammons.substack.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
LINK = re.compile(r'href="https?://sammons\.substack\.com/p/([A-Za-z0-9_-]+)')
_cache = {}


def episode(slug):
    """Public podcast episode for a Substack slug, or (None, reason)."""
    if slug in _cache:
        return _cache[slug]
    req = urllib.request.Request(f"{PUB}/api/v1/posts/{slug}", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        res = (None, "not published on Substack yet" if e.code == 404 else f"Substack HTTP {e.code}")
    except Exception as e:  # network trouble: leave the post as it is
        res = (None, f"lookup failed: {e}")
    else:
        if d.get("type") != "podcast" or not d.get("podcast_url"):
            res = (None, "not a podcast episode")
        elif d.get("audience") != "everyone":
            res = (None, f"audience is {d.get('audience')}, not public")
        else:
            res = ({"src": d["podcast_url"], "title": d.get("title") or slug,
                    "dur": round(d.get("podcast_duration") or 0),
                    "img": d.get("podcast_episode_image_url") or d.get("cover_image") or "",
                    "url": d.get("canonical_url") or f"{PUB}/p/{slug}"}, "")
    _cache[slug] = res
    return res


def strip(raw):
    return re.sub(r"\s*<!-- wp:html -->" + re.escape(START) + r".*?" + re.escape(END) + r"<!-- /wp:html -->",
                  "", raw, flags=re.S)


def block(eps):
    js = "window.SS_POD_EPS=" + json.dumps(eps, sort_keys=True) + ";\n" + (HERE / "player.js").read_text()
    b64 = base64.b64encode(js.encode()).decode()
    return f'<!-- wp:html -->{START}<script src="data:text/javascript;base64,{b64}"></script>{END}<!-- /wp:html -->'


def get(post_id):
    fields = "?context=edit&_fields=id,title,link,status,date,content"
    code, post = wp.request("GET", f"/wp/v2/posts/{post_id}{fields}")
    if code == 404:
        code, post = wp.request("GET", f"/wp/v2/pages/{post_id}{fields}")
        return code, post, "pages"
    return code, post, "posts"


def run(post_id, apply):
    code, post, kind = get(post_id)
    if code != 200:
        print(f"{post_id}: could not read: HTTP {code}")
        return False
    raw = post["content"]["raw"]
    label = f"{post_id} {post['title']['raw']!r} ({post['status']} {post['date'][:10]})"
    slugs = list(dict.fromkeys(LINK.findall(strip(raw))))
    if not slugs:
        print(f"{label}: no Substack links, skipped.")
        return True
    eps, notes = {}, []
    for s in slugs:
        ep, why = episode(s)
        if ep:
            eps[s] = ep
            notes.append(f"{s}: plays here ({ep['dur'] // 60} min)")
        else:
            notes.append(f"{s}: link kept, {why}")
            if why.startswith(("lookup failed", "Substack HTTP")):
                print(f"{label}: {why}; left unchanged.")
                return False
    base = strip(raw)
    updated = base.rstrip() + "\n\n" + block(eps) if eps else base
    detail = "; ".join(notes)
    if updated == raw:
        print(f"{label}: already up to date. [{detail}]")
        return True
    bdir = HERE.parent / "backups"
    bdir.mkdir(exist_ok=True)
    bak = bdir / f"{kind[:-1]}-{post_id}-{time.strftime('%Y%m%d-%H%M%S')}.html"
    bak.write_text(raw)
    if not apply:
        (bdir / f"{kind[:-1]}-{post_id}-podcast-proposed.html").write_text(updated)
        print(f"{label}: would update. [{detail}] Dry run; backup {bak.name}")
        return True
    code, res = wp.request("POST", f"/wp/v2/{kind}/{post_id}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or (eps and START not in res["content"]["raw"]):
        print(f"{label}: update FAILED (HTTP {code}). Restore from backups/{bak.name} if needed.")
        return False
    print(f"{label}: updated {res['link']} [{detail}]")
    return True


def all_ids():
    ids = []
    for kind in ("posts", "pages"):
        for status in ("publish", "future"):
            page = 1
            while True:
                code, rows = wp.request("GET", f"/wp/v2/{kind}?status={status}&per_page=100&page={page}"
                                               "&context=edit&_fields=id,content")
                if code != 200 or not rows:
                    break
                ids += [r["id"] for r in rows if "sammons.substack.com/p/" in r["content"]["raw"]]
                if len(rows) < 100:
                    break
                page += 1
    return ids


def main(a):
    apply = "--apply" in a
    ids = all_ids() if "--all" in a else [int(x) for x in a if not x.startswith("--")]
    if not ids:
        sys.exit(__doc__)
    ok = all([run(i, apply) for i in ids])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
