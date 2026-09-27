#!/usr/bin/env python3
"""Tighten the top of every Bible-series post and page (no reading time, less white space).

  python3 series-layout/apply.py [ID ...] [--apply]

Adds the "Bible series layout" synced pattern (wp_block 4676, source series-layout/pattern.html)
to each post or page in the series, after its own content and before the invisible
ss-video / ss-pod / ss-wrap script blocks. The pattern is only CSS, so editing it once restyles
every page that uses it. Also removes "· N minute read" text written into a page's own content.

Series = posts in the Bible Characters / Old Testament / New Testament categories or with the
Bible series tags; pages that are maps, have back-to-the-story links, the index pages, and EXTRA.
Items without block markup are converted (subscribe/wpautop.py) into a Custom HTML block and only
saved if a scratch draft renders them identically; set SCRATCH_DRAFT=<draft id> to reuse a draft. Only content changes; status and schedule stay.
Each item is backed up to backups/ first. Without --apply this is a dry run.
"""
import json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "subscribe"))
import wp  # noqa: E402
from apply import split_tail, rendered_as_draft, norm  # noqa: E402  (subscribe/apply.py)
from wpautop import wpautop  # noqa: E402

REF = 4676
BLOCK = f'<!-- wp:block {{"ref":{REF}}} /-->'
CATS = {1803, 1804, 1805}           # Bible Characters, Old Testament, New Testament
TAGS = {1716, 1676, 1648, 1727}     # Bible character(s), substack-characters, Bible Map
INDEX_SLUGS = {"bible-characters", "songs", "bible-maps"}
EXTRA = {1968, 1936, 1893, 1664, 1656, 629, 1494, 2251, 2225}  # character pages without back links
READTIME = re.compile(r"\s*(?:&middot;|·)\s*\d+\s+minute read", re.I)


def items(ids):
    out = []
    for kind in ("posts", "pages"):
        for st in ("publish", "future", "draft"):
            page = 1
            while True:
                code, rows = wp.request("GET", f"/wp/v2/{kind}?status={st}&per_page=100&page={page}"
                                               "&context=edit&_fields=id,status,date,slug,title,categories,tags,content")
                if code != 200 or not rows:
                    break
                for r in rows:
                    r["kind"] = kind
                    raw = r["content"]["raw"]
                    tags = set(r.get("tags") or [])
                    if ids:
                        keep = r["id"] in ids
                    elif kind == "posts":
                        keep = bool(set(r.get("categories") or []) & CATS or tags & TAGS)
                    else:
                        keep = ("ss-back:start" in raw or tags & TAGS or r["slug"] in INDEX_SLUGS or r["id"] in EXTRA)
                    if keep:
                        out.append(r)
                if len(rows) < 100:
                    break
                page += 1
    return out


def run(p, apply):
    raw = p["content"]["raw"]
    label = f"{p['kind'][:-1]} {p['id']} {p['slug'][:45]} ({p['status']})"
    updated = READTIME.sub("", raw)
    if BLOCK not in updated:
        if "<!-- wp:" not in updated:
            # No block markup: WordPress adds paragraphs on display, and stops once a block is
            # added. Write them out (wpautop.py) in a Custom HTML block, and only keep the result
            # if a scratch draft renders it exactly like the live page.
            converted = "<!-- wp:html -->\n" + wpautop(updated).strip() + "\n<!-- /wp:html -->"
            if norm(rendered_as_draft(converted)) != norm(p["content"]["rendered"]):
                print(f"{label}: no block markup and the conversion doesn't render identically; SKIPPED.")
                return False
            body, tail = converted, ""
        else:
            body, tail = split_tail(updated)
        updated = body + "\n\n" + BLOCK + ("\n\n" + tail if tail else "")
    if updated == raw:
        return True
    changes = ", ".join(x for x, on in (("layout", BLOCK not in raw), ("read time text", bool(READTIME.search(raw)))) if on)
    (ROOT / "backups").mkdir(exist_ok=True)
    (ROOT / "backups" / f"{p['kind'][:-1]}-{p['id']}-{time.strftime('%Y%m%d-%H%M%S')}.html").write_text(raw)
    if not apply:
        print(f"{label}: would add {changes}.")
        return True
    code, res = wp.request("POST", f"/wp/v2/{p['kind']}/{p['id']}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or BLOCK not in res["content"]["raw"] or res["status"] != p["status"]:
        print(f"{label}: update FAILED (HTTP {code}). Backup in backups/.")
        return False
    print(f"{label}: {changes} done.")
    return True


def main(a):
    apply = "--apply" in a
    ids = {int(x) for x in a if x.isdigit()}
    todo = items(ids)
    ok = all([run(p, apply) for p in todo])
    done = sum(1 for p in todo if BLOCK in p["content"]["raw"])
    print(f"{len(todo)} series items ({sum(p['kind'] == 'posts' for p in todo)} posts, "
          f"{sum(p['kind'] == 'pages' for p in todo)} pages); {done} already had the layout.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
