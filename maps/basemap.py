#!/usr/bin/env python3
"""Build the base layer for an interactive Bible map.

For a bounding box it produces SVG paths (land, lakes, rivers, modern borders) in an
equirectangular projection scaled by cos(mid-latitude), plus a shaded-relief JPEG built
from AWS Terrain Tiles (Terrarium encoding). Elevations of places are sampled from the
same data so facts like "2,600 ft above sea level" come from real measurements.
Data: Natural Earth (public domain); terrain tiles from SRTM/GMTED and others via AWS.
"""
import io, json, math, urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import box, shape, LineString, MultiLineString, Polygon, MultiPolygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TILES = DATA / "tiles"
VB_W = 640  # SVG viewBox width


def _load(name):
    return json.load(open(DATA / f"{name}.geojson"))["features"]


@lru_cache(None)
def layers():
    return {k: _load(v) for k, v in {
        "land": "ne_10m_land", "lakes": "ne_10m_lakes",
        "rivers": "ne_10m_rivers_lake_centerlines",
        "borders": "ne_10m_admin_0_boundary_lines_land"}.items()}


class Proj:
    """lon/lat -> SVG units for bbox (w, s, e, n)."""
    def __init__(self, bbox):
        self.w, self.s, self.e, self.n = bbox
        self.k = math.cos(math.radians((self.s + self.n) / 2))
        self.sx = VB_W / ((self.e - self.w) * self.k)
        self.W = VB_W
        self.H = round((self.n - self.s) * self.sx, 1)

    def xy(self, lon, lat):
        return ((lon - self.w) * self.k * self.sx, (self.n - lat) * self.sx)


def fit_bbox(bbox, min_aspect=0.62, max_aspect=1.25):
    """Pad a bbox so its height/width stays in a pleasant range."""
    w, s, e, n = bbox
    k = math.cos(math.radians((s + n) / 2))
    width, height = (e - w) * k, (n - s)
    if height / width < min_aspect:
        pad = (width * min_aspect - height) / 2
        s, n = s - pad, n + pad
    elif height / width > max_aspect:
        pad = (height / max_aspect - width) / 2 / k
        w, e = w - pad, e + pad
    return (w, s, e, n)


def _d(geom, p, tol):
    """Geometry -> SVG path data (projected, simplified)."""
    out = []
    def ring(coords, close):
        pts = [p.xy(x, y) for x, y in coords]
        ls = LineString(pts).simplify(tol) if len(pts) > 2 else LineString(pts)
        c = list(ls.coords)
        if len(c) < 2:
            return
        out.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in c) + (" Z" if close else ""))
    def walk(g):
        if isinstance(g, Polygon):
            ring(g.exterior.coords, True)
            for i in g.interiors:
                ring(i.coords, True)
        elif isinstance(g, (MultiPolygon,)):
            for x in g.geoms: walk(x)
        elif isinstance(g, LineString):
            ring(g.coords, False)
        elif isinstance(g, MultiLineString):
            for x in g.geoms: walk(x)
        elif hasattr(g, "geoms"):
            for x in g.geoms: walk(x)
    walk(geom)
    return " ".join(out)


def vectors(bbox):
    p = Proj(bbox)
    span = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    m = span * 0.05
    clip = box(bbox[0] - m, bbox[1] - m, bbox[2] + m, bbox[3] + m)
    tol = 0.35
    L = layers()
    land = unary_union([shape(f["geometry"]).intersection(clip) for f in L["land"]
                        if shape(f["geometry"]).intersects(clip)])
    lakes = []
    for f in L["lakes"]:
        g = shape(f["geometry"])
        if g.intersects(clip) and g.area > (span * 0.0015) ** 2:
            lakes.append({"name": f["properties"].get("name") or "", "d": _d(g.intersection(clip), p, tol)})
    max_rank = 6 if span < 3 else 5 if span < 8 else 4 if span < 20 else 3
    rivers = []
    for f in L["rivers"]:
        pr = f["properties"]
        if pr.get("featurecla") not in ("River", "Lake Centerline", "Lake Centerline (Intermittent)", "River (Intermittent)"):
            continue
        if (pr.get("scalerank") or 9) > max_rank:
            continue
        g = shape(f["geometry"])
        if g.intersects(clip):
            rivers.append({"name": pr.get("name_en") or pr.get("name") or "", "rank": pr.get("scalerank"),
                           "int": "Intermittent" in pr.get("featurecla", ""), "d": _d(g.intersection(clip), p, tol)})
    borders = []
    for f in L["borders"]:
        g = shape(f["geometry"])
        if g.intersects(clip):
            borders.append(_d(g.intersection(clip), p, tol))
    return {"W": p.W, "H": p.H, "bbox": list(bbox), "k": p.k, "sx": p.sx,
            "land": _d(land, p, tol), "lakes": [l for l in lakes if l["d"]],
            "rivers": [r for r in rivers if r["d"]], "borders": [b for b in borders if b]}


# ---------- terrain ----------
def _tile(z, x, y):
    TILES.mkdir(parents=True, exist_ok=True)
    f = TILES / f"{z}-{x}-{y}.png"
    if not f.exists():
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        f.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    a = np.asarray(Image.open(f).convert("RGB"), dtype=np.float64)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def _merc(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


class DEM:
    def __init__(self, bbox, out_w=1100):
        w, s, e, n = bbox
        k = math.cos(math.radians((s + n) / 2))
        z = 3
        while z < 11:
            x0, _ = _merc(w, n, z); x1, _ = _merc(e, n, z)
            if (x1 - x0) * 256 >= out_w * 1.1:
                break
            z += 1
        self.z = z
        x0, y0 = _merc(w, n, z); x1, y1 = _merc(e, s, z)
        tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
        rows = []
        for ty in range(ty0, ty1 + 1):
            rows.append(np.hstack([_tile(z, tx, ty) for tx in range(tx0, tx1 + 1)]))
        self.mosaic = np.vstack(rows)
        self.tx0, self.ty0 = tx0, ty0
        self.bbox = bbox
        self.out_w = out_w
        self.out_h = int(round(out_w * (n - s) / ((e - w) * k)))

    def sample(self, lon, lat):
        x, y = _merc(lon, lat, self.z)
        px, py = (x - self.tx0) * 256, (y - self.ty0) * 256
        return self._bilinear(np.array([px]), np.array([py]))[0]

    def _bilinear(self, px, py):
        m = self.mosaic
        px = np.clip(px, 0, m.shape[1] - 1.001); py = np.clip(py, 0, m.shape[0] - 1.001)
        x0 = np.floor(px).astype(int); y0 = np.floor(py).astype(int)
        fx, fy = px - x0, py - y0
        return (m[y0, x0] * (1 - fx) * (1 - fy) + m[y0, x0 + 1] * fx * (1 - fy) +
                m[y0 + 1, x0] * (1 - fx) * fy + m[y0 + 1, x0 + 1] * fx * fy)

    def grid(self):
        w, s, e, n = self.bbox
        lons = np.linspace(w, e, self.out_w)
        lats = np.linspace(n, s, self.out_h)
        LON, LAT = np.meshgrid(lons, lats)
        n2 = 2 ** self.z
        X = (LON + 180) / 360 * n2
        Y = (1 - np.log(np.tan(np.radians(LAT)) + 1 / np.cos(np.radians(LAT))) / np.pi) / 2 * n2
        return self._bilinear((X - self.tx0) * 256, (Y - self.ty0) * 256)


def relief(bbox, path, out_w=1100):
    """Write a shaded-relief JPEG for bbox; returns the DEM for sampling."""
    dem = DEM(bbox, out_w)
    Z = dem.grid()
    w, s, e, n = bbox
    lat_mid = (s + n) / 2
    dx = (e - w) / dem.out_w * 111320 * math.cos(math.radians(lat_mid))
    dy = (n - s) / dem.out_h * 110574
    span_km = (e - w) * 111 * math.cos(math.radians(lat_mid))
    exag = 1.6 if span_km < 80 else 2.4 if span_km < 250 else 4 if span_km < 800 else 7
    gy, gx = np.gradient(Z * exag, dy, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(42)
    shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    shade = np.clip(shade, 0, 1)
    # Hypsometric tint: low valleys cool olive, uplands warm sand, peaks pale.
    stops = [(-450, (205, 214, 190)), (0, (226, 228, 205)), (300, (236, 229, 204)),
             (800, (229, 214, 180)), (1500, (214, 196, 160)), (2500, (206, 196, 178)), (4000, (240, 238, 232))]
    ev = [s_[0] for s_ in stops]
    tint = np.stack([np.interp(Z, ev, [c[1][i] for c in stops]) for i in range(3)], -1)
    light = 0.62 + 0.5 * shade[..., None]
    img = np.clip(tint * light, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, "JPEG", quality=78, optimize=True, progressive=True)
    return dem
