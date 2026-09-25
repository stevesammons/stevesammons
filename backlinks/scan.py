#!/usr/bin/env python3
"""Map site pages linked from Bible character posts, plus each character's profile and map pages
from site/stories.json. Writes backups/backlink-map.json."""
import json, re, sys, urllib.parse as up
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import wp

def all_items(path):
    out, page = [], 1
    while True:
        code, d = wp.request("GET", f"{path}&per_page=100&page={page}")
        if code != 200 or not d: break
        out += d
        if len(d) < 100: break
        page += 1
    return out

# Bible character posts live in the Old Testament / New Testament categories (children of Bible Characters).
code, cats = wp.request("GET", "/wp/v2/categories?slug=old-testament,new-testament&_fields=id")
tag_ids = [c["id"] for c in cats]
posts = all_items(f"/wp/v2/posts?categories={','.join(map(str,tag_ids))}&status=publish,future,draft,pending,private&context=edit&_fields=id,title,status,date,content")
pages = all_items("/wp/v2/pages?status=publish&_fields=id,link,title,status")  # only public pages get back links
bypath = {up.urlparse(p["link"]).path.rstrip("/"): p for p in pages}
byid = {p["id"]: p for p in pages}
m, other = {}, set()
for po in posts:
    for href in re.findall(r'href="([^"]+)"', po["content"]["raw"]):
        u = up.urlparse(href)
        if u.netloc and "stevesammons.com" not in u.netloc: continue
        if not u.netloc and not href.startswith("/"): continue
        pid = int(up.parse_qs(u.query).get("page_id", [0])[0])
        pg = byid.get(pid) or bypath.get(u.path.rstrip("/"))
        if pg: m.setdefault(pg["id"], set()).add(po["id"])
        else: other.add(href)
# Also link each character's profile and map pages to their posts from site/stories.json, since some
# older posts never link to their own profile page.
stories = Path(__file__).resolve().parent.parent / "site" / "stories.json"
post_ids = {po["id"] for po in posts}
for c in json.loads(stories.read_text())["characters"] if stories.exists() else []:
    for ref in [c.get("profile")] + c.get("maps", []):
        if ref and ref.get("id") in byid:
            m.setdefault(ref["id"], set()).update(pid for pid in c["posts"] if pid in post_ids)
res = [{"page": k, "title": byid[k]["title"]["rendered"], "status": byid[k]["status"], "link": byid[k]["link"],
        "posts": sorted(v)} for k, v in sorted(m.items())]
Path("backups/backlink-map.json").write_text(json.dumps(res, indent=1))
print(f"categories {tag_ids}; {len(posts)} posts; {len(pages)} site pages; {len(res)} linked pages")
print("multi-post pages:", [(r["title"], r["posts"]) for r in res if len(r["posts"]) > 1])
print("non-published pages:", [(r["title"], r["status"]) for r in res if r["status"] != "publish"])
print("internal links that are not pages:", sorted(other)[:20])
