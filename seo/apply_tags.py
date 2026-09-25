#!/usr/bin/env python3
"""Apply tags and excerpts from seo/map-pages.json to pages. Reuses existing tags by name
(case-insensitive) and creates missing ones. Backs up each page's current tags and excerpt."""
import json, sys, time, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp

data = json.load(open(ROOT / "seo/map-pages.json"))
tags, page = [], 1
while True:
    c, t = wp.request("GET", f"/wp/v2/tags?per_page=100&page={page}&_fields=id,name")
    if c != 200 or not t: break
    tags += t; page += 1
import html
by_name = {html.unescape(t["name"]).lower(): t["id"] for t in tags}

def tag_id(name):
    k = name.lower()
    if k not in by_name:
        c, t = wp.request("POST", "/wp/v2/tags", json.dumps({"name": name}).encode(), {"Content-Type": "application/json"})
        if c not in (200, 201):
            if isinstance(t, dict) and t.get("code") == "term_exists":
                by_name[k] = t["data"]["term_id"]
                return by_name[k]
            sys.exit(f"Could not create tag {name}: {c} {t}")
        by_name[k] = t["id"]
        print(f"  created tag: {name}")
    return by_name[k]

bdir = ROOT / "backups"; bdir.mkdir(exist_ok=True)
backup, ok = {}, 0
for row in data:
    c, cur = wp.request("GET", f"/wp/v2/pages/{row['id']}?context=edit&_fields=id,title,link,tags,excerpt")
    backup[row["id"]] = {"tags": cur.get("tags", []), "excerpt": cur["excerpt"]["raw"]}
    ids = sorted(set(cur.get("tags", [])) | {tag_id(n) for n in row["tags"]})
    body = {"tags": ids}
    if not cur["excerpt"]["raw"].strip():
        body["excerpt"] = row["excerpt"]
    c, res = wp.request("POST", f"/wp/v2/pages/{row['id']}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    good = c == 200 and set(ids) <= set(res.get("tags", []))
    ok += good
    print(("OK  " if good else "FAIL"), row["id"], cur["title"]["raw"], f"{len(ids)} tags", "| excerpt set" if "excerpt" in body else "| excerpt kept")
    time.sleep(0.5)
json.dump(backup, open(bdir / f"page-tags-excerpts-{time.strftime('%Y%m%d-%H%M%S')}.json", "w"), indent=1)
print(ok, "of", len(data), "pages updated")
