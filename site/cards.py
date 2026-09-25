#!/usr/bin/env python3
"""Generate branded featured-image cards (1600x900) for posts without a featured image.

  python3 site/cards.py sample            # writes site/cards/sample-*.jpg
  python3 site/cards.py apply             # generate, upload, set featured_media (skips posts that have one)
  python3 site/cards.py one POST_ID         # (re)make one post's card and set it, replacing any image
"""
import html, json, random, sys, textwrap, time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
FONTS = ROOT / "site" / "fonts"
OUT = ROOT / "site" / "cards"
W, H = 1600, 900
RED = (221, 51, 51)


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"Poppins-{name}.ttf"), size)


def background(seed):
    rnd = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = W * (0.62 + rnd.uniform(-0.08, 0.08)), H * (0.42 + rnd.uniform(-0.08, 0.08))
    d = np.sqrt(((x - cx) / W) ** 2 + ((y - cy) / H) ** 2)
    base = 58 - 50 * np.clip(d / 0.9, 0, 1) ** 1.3          # soft light pool, dark edges
    grain = rnd.normal(0, 5.5, (H, W))
    img = np.clip(base + grain, 4, 255).astype(np.uint8)
    im = Image.fromarray(img, "L").filter(ImageFilter.GaussianBlur(0.6)).convert("RGB")
    return im


def fit_lines(draw, text, fnt_name, max_w, sizes, max_lines):
    for size in sizes:
        f = font(fnt_name, size)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=f) <= max_w:
                cur = t
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
    return f, lines[:max_lines]


def card(headline, subtitle, kicker, seed):
    im = background(seed)
    d = ImageDraw.Draw(im)
    x0, max_w = 150, W - 300
    hf, hl = fit_lines(d, headline.upper(), "Bold", max_w, [150, 132, 116, 100, 88, 78, 70], 3)
    sf, sl = fit_lines(d, subtitle.upper(), "SemiBold", max_w, [46, 42, 38, 34], 2) if subtitle else (None, [])
    lh, sh = int(hf.size * 1.02), int((sf.size if sf else 0) * 1.25)
    block = lh * len(hl) + (24 + sh * len(sl) if sl else 0)
    y = (H - block) // 2 - 20
    d.rectangle([x0 - 52, y + 12, x0 - 34, y + block - 6], fill=RED)
    for l in hl:
        d.text((x0, y), l, font=hf, fill=(255, 255, 255)); y += lh
    if sl:
        y += 24
        for l in sl:
            d.text((x0, y), l, font=sf, fill=(235, 235, 235)); y += sh
    kf = font("Medium", 26)
    d.text((x0 - 52, H - 92), "STEVE SAMMONS", font=kf, fill=(200, 200, 200))
    if kicker:
        d.text((W - 110 - d.textlength(kicker.upper(), font=kf), H - 92), kicker.upper(), font=kf, fill=(150, 150, 150))
    return im


def spec(post, chars_by_post, cats):
    title = html.unescape(post["title"]).replace("\xa0", " ").strip()
    cat = next((cats[c] for c in post["cats"] if c in cats), "")
    ch = chars_by_post.get(post["id"])
    if ch and ch not in ("The Christmas Story",):
        return ch, title, cat
    return title, "", cat


def load():
    plan = json.load(open(ROOT / "backups/featured-plan.json"))
    chars = json.load(open(ROOT / "backups/hub-chars.json"))
    by_post = {p["id"]: n for n, c in chars.items() for p in c["posts"]}
    fixes = {1952: "Zechariah", 2064: "Adam", 2508: "Hannah", 1846: "Gideon", 1875: "Shadrach, Meshach and Abednego"}
    by_post.update(fixes)
    import wp
    c, cs = wp.request("GET", "/wp/v2/categories?per_page=100&_fields=id,name")
    cats = {x["id"]: html.unescape(x["name"]) for x in cs}
    return plan, by_post, cats, wp


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    plan, by_post, cats, wp = load()
    todo = [p for p in plan if not p.get("att")]
    if sys.argv[1:2] == ["one"]:
        pid = int(sys.argv[2])
        c, p = wp.request("GET", f"/wp/v2/posts/{pid}?context=edit&_fields=id,title,slug,categories,featured_media")
        (ROOT / "backups").mkdir(exist_ok=True)
        (ROOT / "backups" / f"featured-{pid}-before.json").write_text(json.dumps({"post": pid, "old_featured": p["featured_media"]}))
        h, s_, k = spec({"id": pid, "title": p["title"]["raw"], "cats": p["categories"]}, by_post, cats)
        f = OUT / f"{p['slug'][:60]}-card.jpg"
        card(h, s_, k, pid).save(f, quality=84, optimize=True, progressive=True)
        code, m = wp.request("POST", "/wp/v2/media", f.read_bytes(), {"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{f.name}"'})
        alt = f"{h}: {s_}" if s_ else h
        wp.request("POST", f"/wp/v2/media/{m['id']}", json.dumps({"alt_text": alt[:120], "title": alt[:120]}).encode(), {"Content-Type": "application/json"})
        code, r = wp.request("POST", f"/wp/v2/posts/{pid}", json.dumps({"featured_media": m["id"]}).encode(), {"Content-Type": "application/json"})
        print("set", pid, "->", m["id"], "(old", p["featured_media"], "kept in media library)")
        sys.exit()
    if sys.argv[1:] == ["sample"]:
        for p in todo[:2] + [x for x in todo if x["id"] in (1334, 27, 353)]:
            h, s, k = spec(p, by_post, cats)
            card(h, s, k, p["id"]).save(OUT / f"sample-{p['id']}.jpg", quality=86)
            print("sample", p["id"], h, "|", s, "|", k)
        sys.exit()
    done = 0
    for p in plan:
        c, cur = wp.request("GET", f"/wp/v2/posts/{p['id']}?context=edit&_fields=featured_media,slug")
        if cur.get("featured_media"):
            continue
        if p.get("att"):
            mid = p["att"]
        else:
            h, s, k = spec(p, by_post, cats)
            f = OUT / f"{cur['slug'][:60]}-card.jpg"
            card(h, s, k, p["id"]).save(f, quality=84, optimize=True, progressive=True)
            code, m = wp.request("POST", "/wp/v2/media", f.read_bytes(),
                                 {"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{f.name}"'})
            if code not in (200, 201):
                print("upload failed", p["id"], code, str(m)[:120]); continue
            mid = m["id"]
            alt = f"{h}: {s}" if s else h
            wp.request("POST", f"/wp/v2/media/{mid}", json.dumps({"alt_text": alt[:120], "title": alt[:120]}).encode(), {"Content-Type": "application/json"})
        code, r = wp.request("POST", f"/wp/v2/posts/{p['id']}", json.dumps({"featured_media": mid}).encode(), {"Content-Type": "application/json"})
        done += code == 200
        time.sleep(0.2)
    print("featured images set:", done)
