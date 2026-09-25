#!/usr/bin/env python3
"""Publish built interactive maps to their WordPress pages.

  python3 maps/publish.py 2923 [2925 ...] [--apply]     # or "all"

For each page: upload the terrain image to the media library (once), bundle engine + config
into a base64 data: URI script (the site's content filters mangle inline scripts), and
replace the page's static map <figure> with the interactive map. The original figure is
kept inside <noscript> as the fallback and saved to maps/originals/. Re-running replaces
the previous insert. Every page is backed up to backups/ before it changes.
"""
import base64, json, re, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp  # noqa: E402

START, END = "<!-- bm:start -->", "<!-- bm:end -->"
MEDIA = HERE / "media.json"
ORIG = HERE / "originals"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def upload_relief(page, slug):
    media = json.loads(MEDIA.read_text()) if MEDIA.exists() else {}
    f = HERE / "build" / f"{page}-relief.jpg"
    key = str(page)
    digest = f"{f.stat().st_size}"
    if key in media and media[key].get("size") == digest:
        return media[key]["url"]
    name = f"bible-map-{slug}-terrain.jpg"
    code, res = wp.request("POST", "/wp/v2/media", f.read_bytes(),
                           {"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{name}"'})
    if code not in (200, 201):
        raise SystemExit(f"{page}: media upload failed {code} {res}")
    wp.request("POST", f"/wp/v2/media/{res['id']}", json.dumps({
        "alt_text": "Shaded terrain for an interactive Bible map", "title": f"Bible map terrain: {slug}"}).encode(),
        {"Content-Type": "application/json"})
    media[key] = {"id": res["id"], "url": res["source_url"], "size": digest}
    MEDIA.write_text(json.dumps(media, indent=1))
    return res["source_url"]


def bundle(page, cfg):
    js = (HERE / "engine.js").read_text() + (
        f"\n(function(){{var r=document.getElementById('bm-{page}');if(r&&!r.dataset.ready){{r.dataset.ready='1';"
        f"BibleMap(r,{json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))});}}}})();\n")
    return "data:text/javascript;base64," + base64.b64encode(js.encode()).decode()


def find_figure(raw):
    figs = [m for m in re.finditer(r"<figure\b.*?</figure>", raw, flags=re.S) if re.search(r"map", m.group(0), re.I)]
    return figs[0] if len(figs) == 1 else None


def publish(page, apply):
    code, pg = wp.request("GET", f"/wp/v2/pages/{page}?context=edit&_fields=id,slug,link,title,content")
    if code != 200:
        raise SystemExit(f"{page}: cannot read page ({code})")
    raw = pg["content"]["raw"]
    (ROOT / "backups").mkdir(exist_ok=True)
    (ROOT / "backups" / f"page-{page}-{time.strftime('%Y%m%d-%H%M%S')}-maps.html").write_text(raw)
    ORIG.mkdir(exist_ok=True)
    orig_file = ORIG / f"{page}.html"

    if START in raw:
        span = re.search(re.escape(START) + r".*?" + re.escape(END), raw, flags=re.S).span()
        fallback = orig_file.read_text() if orig_file.exists() else ""
    elif "<!-- chm:start -->" in raw:  # the first Hebron map
        span = re.search(r"<!-- chm:start -->.*?<!-- chm:end -->", raw, flags=re.S).span()
        fallback = ('<p><em>This interactive map needs JavaScript. Hebron lies in the Judean hill country, '
                    'about 20 miles south of Jerusalem (Joshua 14:12–15; 15:13–14).</em></p>')
        if not orig_file.exists():
            orig_file.write_text(fallback)
    else:
        m = find_figure(raw)
        if not m:
            raise SystemExit(f"{page}: no single map <figure> found; nothing changed")
        span = m.span()
        fallback = m.group(0)
        if not orig_file.exists():
            orig_file.write_text(fallback)

    cfg = json.loads((HERE / "build" / f"{page}.config.json").read_text())
    cfg["relief"] = upload_relief(page, pg["slug"]) if apply else cfg["relief"]
    block = (f'{START}<div id="bm-{page}" class="bm-root"></div><script src="{bundle(page, cfg)}"></script>'
             f'<noscript>{fallback}</noscript>{END}')
    updated = raw[:span[0]] + block + raw[span[1]:]
    kb = len(updated.encode()) // 1024
    if not apply:
        (ROOT / "backups" / f"page-{page}-maps-proposed.html").write_text(updated)
        print(f"DRY {page} {pg['title']['raw']}: {len(raw) // 1024} KB -> {kb} KB")
        return True
    code, res = wp.request("POST", f"/wp/v2/pages/{page}", json.dumps({"content": updated}).encode(),
                           {"Content-Type": "application/json"})
    if code != 200 or START not in res["content"]["raw"]:
        print(f"FAIL {page}: update returned {code}")
        return False
    time.sleep(1)
    html = urllib.request.urlopen(urllib.request.Request(pg["link"] + f"?v={int(time.time())}", headers={"User-Agent": UA}),
                                  timeout=90).read().decode("utf-8", "replace")
    ok = f'id="bm-{page}"' in html and re.search(r'data:text/javascript;base64,[A-Za-z0-9+/=]{1000,}"', html)
    print(("OK  " if ok else "CHECK"), page, pg["title"]["raw"], f"{kb} KB", pg["link"])
    return bool(ok)


if __name__ == "__main__":
    args = sys.argv[1:]
    apply = "--apply" in args
    ids = [a for a in args if a != "--apply"]
    if ids == ["all"]:
        ids = sorted(p.stem for p in (HERE / "content").glob("*.json"))
    results = [publish(int(i), apply) for i in ids]
    print(f"{sum(results)} of {len(results)} pages {'published' if apply else 'ready'}")
