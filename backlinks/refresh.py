#!/usr/bin/env python3
"""Re-publish the current backlink.js on every page that already has "Back to the story" links.

  python3 backlinks/refresh.py [--apply]

Only the script inside each page's existing ss-back block is swapped, so the page's own post
list, subject and layout stay as they are. Run it after editing backlink.js. Pages are backed up to backups/ first. Without --apply: dry run.
"""
import base64, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))
import wp  # noqa: E402
from apply import TOP_S, TOP_E  # noqa: E402

SCRIPT = re.compile(re.escape(TOP_S) + r'(.*?data:text/javascript;base64,)([A-Za-z0-9+/=]+)(".*?)' + re.escape(TOP_E), re.S)


def main(a):
    apply = "--apply" in a
    pages, page = [], 1
    while True:
        code, rows = wp.request("GET", f"/wp/v2/pages?status=publish,future,draft,private&per_page=100&page={page}"
                                       "&context=edit&_fields=id,slug,link,content")
        if code != 200 or not rows:
            break
        pages += [r for r in rows if TOP_S in r["content"]["raw"]]
        if len(rows) < 100:
            break
        page += 1
    js = base64.b64encode((HERE / "backlink.js").read_bytes()).decode()
    bdir = HERE.parent / "backups"
    bdir.mkdir(exist_ok=True)
    ok = True
    for p in pages:
        raw = p["content"]["raw"]
        m = SCRIPT.search(raw)
        posts = re.search(r'data-posts="([\d,]+)"', raw).group(1)
        label = f"{p['id']} {p['slug']} (posts {posts})"
        if not m:
            print(f"{label}: no back-link script found, skipped.")
            ok = False
            continue
        updated = raw[:m.start(2)] + js + raw[m.end(2):]
        if updated == raw:
            print(f"{label}: up to date.")
            continue
        (bdir / f"page-{p['id']}-{time.strftime('%Y%m%d-%H%M%S')}.html").write_text(raw)
        if not apply:
            print(f"{label}: would update.")
            continue
        code, res = wp.request("POST", f"/wp/v2/pages/{p['id']}", json.dumps({"content": updated}).encode(),
                               {"Content-Type": "application/json"})
        if code != 200 or TOP_S not in res["content"]["raw"]:
            print(f"{label}: update FAILED (HTTP {code}). Backup in backups/.")
            ok = False
            continue
        print(f"{label}: updated {res['link']}")
    print(f"{len(pages)} pages with back links.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
