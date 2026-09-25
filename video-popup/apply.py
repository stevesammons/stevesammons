#!/usr/bin/env python3
"""Make a post's YouTube links play in an on-page lightbox instead of leaving the site.

  python3 video-popup/apply.py POST_ID [POST_ID ...] [--apply]

Adds one Custom HTML block at the end of the post that loads lightbox.js (as a base64
data: URI, so the site's content filters can't mangle it). The links themselves are not
changed, so they still go to YouTube without JavaScript. Without --apply this is a dry run.
Each post is backed up to backups/ first, and re-running replaces the previous insert.
"""
import base64, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import wp  # noqa: E402

START, END = "<!-- ss-video:start -->", "<!-- ss-video:end -->"


def block():
    js = base64.b64encode((HERE / "lightbox.js").read_bytes()).decode()
    return (f"<!-- wp:html -->{START}<script src=\"data:text/javascript;base64,{js}\"></script>"
            f"{END}<!-- /wp:html -->")


def insert(raw):
    raw = re.sub(r"\s*<!-- wp:html -->" + re.escape(START) + r".*?" + re.escape(END) + r"<!-- /wp:html -->",
                 "", raw, flags=re.S)
    return raw.rstrip() + "\n\n" + block()


def run(post_id, apply):
    code, post = wp.request("GET", f"/wp/v2/posts/{post_id}?context=edit&_fields=id,title,link,status,content")
    if code != 200:
        print(f"{post_id}: could not read post: HTTP {code} {post}")
        return False
    raw = post["content"]["raw"]
    if "youtu" not in raw:
        print(f"{post_id}: no YouTube links, skipped.")
        return True
    bdir = HERE.parent / "backups"
    bdir.mkdir(exist_ok=True)
    bak = bdir / f"post-{post_id}-{time.strftime('%Y%m%d-%H%M%S')}.html"
    bak.write_text(raw)

    updated = insert(raw)
    label = f"{post_id} {post['title']['raw']!r} ({post['status']})"
    if updated == raw:
        print(f"{label}: already up to date.")
        return True
    if not apply:
        (bdir / f"post-{post_id}-proposed.html").write_text(updated)
        print(f"{label}: {len(raw)} -> {len(updated)} chars. Dry run; backup {bak.name}")
        return True
    code, res = wp.request("POST", f"/wp/v2/posts/{post_id}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or START not in res["content"]["raw"]:
        print(f"{label}: update FAILED (HTTP {code}). Restore from backups/{bak.name} if needed.")
        return False
    print(f"{label}: updated {res['link']}")
    return True


def main(a):
    apply = "--apply" in a
    ids = [int(x) for x in a if x != "--apply"]
    if not ids:
        sys.exit(__doc__)
    ok = all([run(i, apply) for i in ids])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
