#!/usr/bin/env python3
"""Build an interactive Bible map from maps/content/<page>.json.

  python3 maps/build.py 2923 [2925 ...]   # or "all"

Outputs maps/build/<page>.config.json, <page>-relief.jpg and <page>.preview.html.
The relief URL in the config is local until publish.py uploads it to the media library.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import basemap as B

OUT = HERE / "build"
REQUIRED_PLACE = {"name", "ll", "conf", "text"}


def validate(c):
    errs = []
    w, s, e, n = c["bbox"]
    for k, p in c["places"].items():
        miss = REQUIRED_PLACE - p.keys()
        if miss: errs.append(f"place {k} missing {sorted(miss)}")
        lat, lon = p["ll"]
        if not (s <= lat <= n and w <= lon <= e): errs.append(f"place {k} {p['ll']} outside bbox")
        if p["conf"] not in ("secure", "probable", "debated", "modern", "unknown", "region"): errs.append(f"place {k} bad conf")
    for k, r in c.get("routes", {}).items():
        for lat, lon in r["pts"]:
            if not (s <= lat <= n and w <= lon <= e): errs.append(f"route {k} point {lat},{lon} outside bbox")
    for i, ch in enumerate(c["chapters"]):
        for k in ch.get("hot", []) + ([ch["sel"]] if ch.get("sel") else []):
            if k not in c["places"]: errs.append(f"chapter {i + 1} refers to unknown place {k}")
        for k in ch.get("routes", []):
            if k not in c.get("routes", {}): errs.append(f"chapter {i + 1} refers to unknown route {k}")
    if c.get("anchor") and c["anchor"] not in c["places"]: errs.append("anchor is not a place")
    for L in c.get("labels", []):
        lat, lon = L["ll"]
        if not (s <= lat <= n and w <= lon <= e): errs.append(f"label {L['t']} outside bbox")
    return errs


def build(page):
    c = json.load(open(HERE / "content" / f"{page}.json"))
    c["bbox"] = list(B.fit_bbox(tuple(c["bbox"])))
    errs = validate(c)
    if errs:
        raise SystemExit(f"{page}: " + "; ".join(errs))
    OUT.mkdir(exist_ok=True)
    v = B.vectors(tuple(c["bbox"]))
    relief = OUT / f"{page}-relief.jpg"
    dem = B.relief(tuple(c["bbox"]), relief)
    for p in c["places"].values():
        if "elev" not in p:
            p["elev"] = int(round(dem.sample(p["ll"][1], p["ll"][0])))
    cfg = {k: c[k] for k in ("title", "kicker", "anchor", "places", "routes", "labels", "chapters", "note", "mapLabel") if k in c}
    cfg.update({"W": v["W"], "H": v["H"], "bbox": v["bbox"], "k": v["k"], "sx": v["sx"], "land": v["land"],
                "lakes": [{"d": l["d"]} for l in v["lakes"]], "rivers": [{"d": r["d"], "rank": r["rank"], "int": r["int"]} for r in v["rivers"]],
                "borders": v["borders"], "relief": relief.name})
    (OUT / f"{page}.config.json").write_text(json.dumps(cfg, ensure_ascii=False))
    (OUT / f"{page}.preview.html").write_text(
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<style>body{font-family:Lato,Helvetica,Arial,sans-serif;margin:0;padding:16px;background:#fff;color:#777}main{max-width:800px;margin:auto}</style></head>"
        f"<body><main><div id='m'></div></main><script>{(HERE / 'engine.js').read_text()}</script>"
        f"<script>BibleMap(document.getElementById('m'),{json.dumps(cfg, ensure_ascii=False)});</script></body></html>")
    print(f"built {page}: {c['title']} | {len(c['places'])} places, {len(c['chapters'])} chapters, relief {relief.stat().st_size // 1024} KB, "
          f"elevations " + ", ".join(f"{p['name']} {p['elev']} m" for p in c["places"].values() if not p.get("area"))[:200])


if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids == ["all"]:
        ids = sorted(p.stem for p in (HERE / "content").glob("*.json"))
    for i in ids:
        build(i)
