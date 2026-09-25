#!/usr/bin/env python3
"""Add "Back to the story" links to a reference page.

  python3 backlinks/apply.py PAGE_ID POST_IDS [SUBJECT] [--apply]

POST_IDS is comma-separated (the posts that link to the page). SUBJECT is the short name
shown in "<SUBJECT> appears in" (e.g. Ahab). Without --apply this is a dry run.
The page is backed up to backups/ first, and re-running replaces the previous insert.
"""
import base64, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import wp  # noqa: E402

TOP_S, TOP_E = "<!-- ss-back:start -->", "<!-- ss-back:end -->"
BOT_S, BOT_E = "<!-- ss-back-end:start -->", "<!-- ss-back-end:end -->"


def blocks(post_ids, subject):
    js = base64.b64encode((HERE / "backlink.js").read_bytes()).decode()
    subj = f' data-subject="{subject}"' if subject else ""
    top = (f'{TOP_S}<nav class="ss-back" data-posts="{post_ids}"{subj} aria-label="Back to the story"></nav>'
           f'<script src="data:text/javascript;base64,{js}"></script>{TOP_E}')
    bottom = f'{BOT_S}<nav class="ss-back ss-back--end" data-posts="{post_ids}" aria-label="Back to the story"></nav>{BOT_E}'
    return top, bottom


def strip(raw):
    for s, e in ((TOP_S, TOP_E), (BOT_S, BOT_E)):
        raw = re.sub(re.escape(s) + r".*?" + re.escape(e), "", raw, flags=re.S)
    return raw


def insert(raw, top, bottom):
    raw = strip(raw)
    # Single Custom HTML block wrapping one container div: go inside the container.
    m = re.match(r"(\s*<!-- wp:html -->\s*<div[^>]*>)", raw)
    tail = re.search(r"(</div>\s*<!-- /wp:html -->\s*)$", raw)
    if m and tail:
        return raw[:m.end()] + top + raw[m.end():tail.start()] + bottom + raw[tail.start():]
    return (f"<!-- wp:html -->{top}<!-- /wp:html -->\n\n" + raw.rstrip() +
            f"\n\n<!-- wp:html -->{bottom}<!-- /wp:html -->")


def main(a):
    apply = "--apply" in a
    a = [x for x in a if x != "--apply"]
    if len(a) < 2:
        sys.exit(__doc__)
    page_id, post_ids = int(a[0]), ",".join(str(int(x)) for x in a[1].split(","))
    subject = a[2] if len(a) > 2 else ""

    code, page = wp.request("GET", f"/wp/v2/pages/{page_id}?context=edit&_fields=id,title,link,modified,content")
    if code != 200:
        sys.exit(f"Could not read page {page_id}: HTTP {code} {page}")
    raw = page["content"]["raw"]
    bdir = HERE.parent / "backups"
    bdir.mkdir(exist_ok=True)
    bak = bdir / f"page-{page_id}-{time.strftime('%Y%m%d-%H%M%S')}.html"
    bak.write_text(raw)

    updated = insert(raw, *blocks(post_ids, subject))
    print(f"{page['title']['raw']} ({page['link']}): {len(raw)} -> {len(updated)} chars; backup {bak.name}")
    if updated == raw:
        print("Already up to date.")
        return
    if not apply:
        (bdir / f"page-{page_id}-proposed.html").write_text(updated)
        print("Dry run. Re-run with --apply to publish.")
        return
    code, res = wp.request("POST", f"/wp/v2/pages/{page_id}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or "ss-back" not in res["content"]["raw"]:
        sys.exit(f"Update failed: HTTP {code}. Restore from backups/{bak.name} if needed.")
    print(f"Published: {res['link']} (modified {res['modified']})")


if __name__ == "__main__":
    main(sys.argv[1:])
