#!/usr/bin/env python3
"""Strip leftover old-theme markup (prev/next article, "You May Also Like" carousel,
empty post-meta header) from imported posts. Dry run by default; --apply to save.

  python3 site/strip_theme_junk.py [--apply] POST_ID ...
"""
import html, json, re, sys, time
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp

VOID = {"img", "br", "hr", "meta", "input", "source", "link", "wbr", "area", "col", "embed", "param", "track"}


class Stack(HTMLParser):
    def __init__(self):
        super().__init__(); self.st = []

    def handle_starttag(self, t, a):
        if t not in VOID:
            self.st.append(t)

    def handle_endtag(self, t):
        if t in self.st:
            while self.st and self.st.pop() != t:
                pass


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def drop(t, start_pat):
    """Remove every element whose opening tag matches start_pat, with its children."""
    while True:
        m = re.search(start_pat, t)
        if not m:
            return t
        tag, depth = m.group(1), 0
        for x in re.finditer(rf"<(/?){tag}\b[^>]*>", t[m.start():]):
            depth += -1 if x.group(1) else 1
            if depth == 0:
                t = t[:m.start()] + t[m.start() + x.end():]
                break
        else:
            return t


def clean(raw):
    cuts = [raw.find(m) for m in ('<section class="posts-pagination"', '<section class="section-carousel"') if m in raw]
    t = raw[:min(cuts)] if cuts else raw
    t = re.sub(r'<ul class="post-meta">\s*(<li class="meta-views">\s*</li>\s*)?</ul>', "", t)
    t = drop(t, r'<(div) class="pk-share-buttons-wrap')
    t = drop(t, r'<(section) class="post-tags"')
    t = t.replace('<div class="pk-clearfix"></div>', "")
    t = re.sub(r"(<p>)?(<!--|&lt;!--) \.(post-main|entry-wrap) <!-- -->(</p>)?", "", t).rstrip()
    p = Stack(); p.feed(t)
    return t + "\n" + "".join(f"</{x}>" for x in reversed(p.st))


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    for pid in [int(a) for a in sys.argv[1:] if a.isdigit()]:
        c, p = wp.request("GET", f"/wp/v2/posts/{pid}?context=edit&_fields=id,slug,status,content")
        raw = p["content"]["raw"]; new = clean(raw)
        cut = raw[len(new):] if raw.startswith(new[:len(new) - 30]) else ""
        print(f"{pid} {p['status']:8} {p['slug'][:50]:50} {len(raw):6} -> {len(new):6}  View Post {raw.count('View Post')}->{new.count('View Post')}")
        print("   ends:", text(new)[-110:])
        if apply and new != raw:
            (ROOT / "backups" / f"post-{pid}-before-junk-{time.strftime('%Y%m%d-%H%M%S')}.json").write_text(json.dumps(p))
            c, _ = wp.request("POST", f"/wp/v2/posts/{pid}", json.dumps({"content": new}).encode(), {"Content-Type": "application/json"})
            print("   saved", c)
