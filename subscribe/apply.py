#!/usr/bin/env python3
"""Put the "Subscribe form" synced pattern (wp_block 4313) at the end of posts.

  python3 subscribe/apply.py ID [ID ...] [--apply]
  python3 subscribe/apply.py --all [--apply]      # every published, scheduled and draft post

Adds <!-- wp:block {"ref":4313} /--> after the post's own content (before the invisible
ss-video / ss-pod / ss-wrap script blocks). Posts that already have it are skipped, and only the
content changes (status and schedule are untouched).

Classic-editor posts are first converted to explicit paragraphs (wpautop.py) inside a Classic
block, because WordPress stops adding paragraphs once a post contains any block. The conversion
is rendered on a scratch draft and must match the live rendering exactly, or the post is skipped.
Each post is backed up to backups/ first. Without --apply this is a dry run.
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))
import wp  # noqa: E402
from wpautop import wpautop  # noqa: E402

REF = 4313
FORM = f'<!-- wp:block {{"ref":{REF}}} /-->'
TRAILING = re.compile(r'\s*<!-- wp:html --><!-- ss-(?:video|pod|wrap):start -->.*?<!-- ss-(?:video|pod|wrap):end --><!-- /wp:html -->\s*$', re.S)
_scratch = int(os.environ["SCRATCH_DRAFT"]) if os.environ.get("SCRATCH_DRAFT") else None  # reuse a draft


def split_tail(raw):
    """Return (body, tail) where tail is the run of trailing script-only blocks."""
    tail = ""
    while True:
        m = TRAILING.search(raw)
        if not m:
            return raw.rstrip(), tail
        tail = m.group(0).strip() + ("\n\n" + tail if tail else "")
        raw = raw[:m.start()]


def norm(h):
    return re.sub(r"\s+", " ", h).strip()


def rendered_as_draft(content):
    """Render content through the_content on a private scratch draft."""
    global _scratch
    body = json.dumps({"content": content}).encode()
    hdr = {"Content-Type": "application/json"}
    if _scratch is None:
        code, d = wp.request("POST", "/wp/v2/posts", json.dumps(
            {"title": "Scratch: subscribe form check (safe to delete)", "status": "draft", "content": content}).encode(), hdr)
        _scratch = d["id"]
    else:
        wp.request("POST", f"/wp/v2/posts/{_scratch}", body, hdr)
    code, g = wp.request("GET", f"/wp/v2/posts/{_scratch}?context=edit&_fields=content")
    return g["content"]["rendered"]


def run(p, apply):
    raw = p["content"]["raw"]
    label = f"{p['id']} {p['title']['raw'][:50]!r} ({p['status']} {p['date'][:10]})"
    if FORM in raw:
        print(f"{label}: already has the form.")
        return True
    classic = "<!-- wp:" not in raw
    if classic:
        converted = "<!-- wp:freeform -->\n" + wpautop(raw).strip() + "\n<!-- /wp:freeform -->"
        if norm(rendered_as_draft(converted)) != norm(p["content"]["rendered"]):
            print(f"{label}: classic post, conversion does not render identically; SKIPPED.")
            return False
        body, tail = converted, ""
    else:
        body, tail = split_tail(raw)
    updated = body + "\n\n" + FORM + ("\n\n" + tail if tail else "")
    kind = "classic, converted" if classic else "block"
    bdir = HERE.parent / "backups"
    bdir.mkdir(exist_ok=True)
    (bdir / f"post-{p['id']}-{time.strftime('%Y%m%d-%H%M%S')}.html").write_text(raw)
    if not apply:
        print(f"{label}: would add the form ({kind}).")
        return True
    code, res = wp.request("POST", f"/wp/v2/posts/{p['id']}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or FORM not in res["content"]["raw"] or res["status"] != p["status"]:
        print(f"{label}: update FAILED (HTTP {code}). Backup in backups/.")
        return False
    print(f"{label}: added ({kind}).")
    return True


def posts(ids):
    fields = "&context=edit&_fields=id,status,date,title,content"
    if ids:
        out = []
        for i in ids:
            code, p = wp.request("GET", f"/wp/v2/posts/{i}?{fields[1:]}")
            if code == 200:
                out.append(p)
        return out
    out = []
    for st in ("publish", "future", "draft", "pending"):
        page = 1
        while True:
            code, rows = wp.request("GET", f"/wp/v2/posts?status={st}&per_page=100&page={page}{fields}")
            if code != 200 or not rows:
                break
            out += [r for r in rows if not r["title"]["raw"].startswith(("Scratch: subscribe", "TEST subscribe"))]
            if len(rows) < 100:
                break
            page += 1
    return out


def main(a):
    apply = "--apply" in a
    ids = [int(x) for x in a if x.isdigit()]
    if not ids and "--all" not in a:
        sys.exit(__doc__)
    ok = True
    todo = posts(ids)
    for p in todo:
        ok = run(p, apply) and ok
    print(f"{len(todo)} posts checked.")
    if _scratch:
        print(f"Scratch draft {_scratch} was used for checks; it is safe to delete.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
