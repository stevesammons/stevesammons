#!/usr/bin/env python3
"""Update the interactive Bible maps (pages tagged "Bible Map").

  python3 bible-maps/apply.py [PAGE_ID ...] [--category ID] [--apply]

For every map page (or just the IDs given):
- swaps in the current bible-maps/engine.js, keeping the page's own map config;
- adds modern country names to the config (C.countries), computed from Natural Earth 10m map
  units so they match the dashed modern borders. They show and hide with "Modern borders";
- with --category ID, sets the page's category to ID (e.g. Bible Maps).
Each page is backed up to backups/ first and only saved when something changed.
Without --apply this is a dry run. Needs shapely (pip install shapely).
"""
import base64, json, math, re, sys, time, urllib.request
from pathlib import Path

from shapely.geometry import Point, box, shape
from shapely.ops import unary_union
from shapely import prepared

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp  # noqa: E402

TAG = 1727  # "Bible Map"
NE_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
          "ne_10m_admin_0_map_units.geojson")
NE_FILE = ROOT / "backups" / "ne_10m_admin_0_map_units.geojson"
# Natural Earth map units -> label. Units not listed use their own NAME; None means no label.
MERGE = {"Iraqi Kurdistan": "Iraq", "N. Cyprus": "Cyprus", "Cyprus U.N. Buffer Zone": "Cyprus",
         "Akrotiri": "Cyprus", "Dhekelia": "Cyprus", "UNDOF Zone": None}
# Preferred spots for particular names, as {page_id: {name: [lat, lon]}}. The engine puts the name
# at the free spot nearest this point instead of the most central one.
NEAR = {
    3111: {"Israel": [31.7815, 35.2135]},  # West Jerusalem, clear of the Old City
}
SCRIPT = re.compile(r"(<!-- bm:start -->.*?data:text/javascript;base64,)([A-Za-z0-9+/=]+)", re.S)
CALL = "(function(){var r=document.getElementById("


def units():
    if not NE_FILE.exists():
        NE_FILE.parent.mkdir(exist_ok=True)
        req = urllib.request.Request(NE_URL, headers={"User-Agent": "Mozilla/5.0"})
        NE_FILE.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    groups = {}
    for f in json.loads(NE_FILE.read_text())["features"]:
        name = f["properties"]["NAME"]
        label = MERGE.get(name, name)
        if label:
            groups.setdefault(label, []).append(shape(f["geometry"]))
    return {k: unary_union(v) for k, v in groups.items()}


def project(geom, cfg):
    bb, K, SX = cfg["bbox"], cfg["k"], cfg["sx"]
    from shapely.ops import transform
    return transform(lambda lon, lat, z=None: ((lon - bb[0]) * K * SX, (bb[3] - lat) * SX), geom)


def countries(cfg, world, near=None):
    W, H, bb = cfg["W"], cfg["H"], cfg["bbox"]
    frame = box(0, 0, W, H)
    ll = box(bb[0] - 1, bb[1] - 1, bb[2] + 1, bb[3] + 1)
    step = max(W, H) / 40.0
    out = []
    for name, g in world.items():
        if not g.intersects(ll):
            continue
        pg = project(g.intersection(ll), cfg)
        vis = pg.intersection(frame)
        if vis.is_empty or vis.area < W * H * 0.004:
            continue
        edge, inside, pts = pg.boundary, prepared.prep(pg), []
        ny, nx = int(H / step) + 1, int(W / step) + 1
        for j in range(ny):
            for i in range(nx):
                x, y = (i + 0.5) * step, (j + 0.5) * step
                if x > W or y > H:
                    continue
                pt = Point(x, y)
                if inside.contains(pt):
                    d = edge.distance(pt)
                    if d >= 3:
                        pts += [round(x, 1), round(y, 1), round(d, 1)]
        if pts:
            c = {"t": name, "pts": pts}
            if near and name in near:
                lat, lon = near[name]
                c["near"] = [round((lon - bb[0]) * cfg["k"] * cfg["sx"], 1), round((bb[3] - lat) * cfg["sx"], 1)]
            out.append(c)
    out.sort(key=lambda c: c["t"])
    return out


def split(js):
    i = js.rfind(CALL)
    call = js[i:]
    m = re.search(r"BibleMap\(r,(\{.*\})\);\}\}\)\(\);\s*$", call, re.S)
    return js[:i], call[:m.start(1)], json.loads(m.group(1)), call[m.end(1):]


def main(a):
    apply = "--apply" in a
    cat = None
    if "--category" in a:
        cat = int(a[a.index("--category") + 1])
    ids = [int(x) for i, x in enumerate(a) if x.isdigit() and (i == 0 or a[i - 1] != "--category")]
    engine = (HERE / "engine.js").read_text().rstrip() + "\n"
    world = units()
    code, pages = wp.request("GET", f"/wp/v2/pages?tags={TAG}&per_page=100&context=edit"
                                    "&_fields=id,slug,link,categories,content")
    if code != 200:
        sys.exit(f"Could not list maps: HTTP {code}")
    pages = [p for p in pages if not ids or p["id"] in ids]
    bdir = ROOT / "backups"
    bdir.mkdir(exist_ok=True)
    ok = True
    for p in pages:
        raw = p["content"]["raw"]
        m = SCRIPT.search(raw)
        if not m:
            print(f"{p['id']} {p['slug']}: no map script found, skipped.")
            ok = False
            continue
        old_engine, pre, cfg, post = split(base64.b64decode(m.group(2)).decode())
        cfg["countries"] = countries(cfg, world, NEAR.get(p["id"]))
        js = engine + pre + json.dumps(cfg, ensure_ascii=False, separators=(",", ":")) + post
        updated = raw[:m.start(2)] + base64.b64encode(js.encode()).decode() + raw[m.end(2):]
        body = {}
        if updated != raw:
            body["content"] = updated
        if cat and p.get("categories") != [cat]:
            body["categories"] = [cat]
        names = ", ".join(c["t"] for c in cfg["countries"]) or "none"
        label = f"{p['id']} {p['slug']}"
        if not body:
            print(f"{label}: up to date. [{names}]")
            continue
        (bdir / f"page-{p['id']}-{time.strftime('%Y%m%d-%H%M%S')}.html").write_text(raw)
        if not apply:
            print(f"{label}: would update {', '.join(body)}. [{names}]")
            continue
        code, res = wp.request("POST", f"/wp/v2/pages/{p['id']}", json.dumps(body).encode(),
                               {"Content-Type": "application/json"})
        if code != 200:
            print(f"{label}: update FAILED (HTTP {code}). Backup in backups/.")
            ok = False
            continue
        print(f"{label}: updated {', '.join(body)}. [{names}] {res['link']}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
