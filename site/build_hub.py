#!/usr/bin/env python3
"""Generate and publish the Bible Characters hub page (/bible-characters/).

  python3 site/build_hub.py [--apply]

Reads backups/hub-chars.json (built from posts in the Old/New Testament categories and the
profile and map pages they link to), applies the corrections below, and renders a filterable
card grid. Published reflections are linked directly; scheduled ones show their month and are
upgraded in the browser once the post is public.
"""
import base64, html, json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp  # noqa: E402

chars = json.load(open(ROOT / "backups/hub-chars.json"))
pages = json.load(open(ROOT / "backups/all-pages.json"))
by_title = {html.unescape(p["title"]["raw"]): p for p in pages}
maps = [x["id"] for x in json.load(open(ROOT / "seo/map-pages.json"))]
by_id = {p["id"]: p for p in pages}

# post id -> (character name, profile page title or None, extra place page titles)
FIX = {
    1952: ("Zechariah, father of John the Baptist", "Zechariah (John's father)", []),
    2064: ("Adam", None, []),
    2508: ("Hannah", None, ["Shiloh"]),
    1846: ("Gideon", "Gideon", []),
    1875: ("Shadrach, Meshach and Abednego", "Shadrach, Meshach, Abednego", ["Where Is the Plain of Dura Today?"]),
}

# Re-key characters whose post was attributed to a non-character page.
fixed = {}
for name, c in chars.items():
    for p in c["posts"]:
        if p["id"] in FIX:
            new, prof, places = FIX[p["id"]]
            d = fixed.setdefault(new, {"name": new, "t": c["t"], "posts": [], "profile": None, "maps": [], "places": [], "summary": "", "img": c.get("img")})
            d["posts"].append(p)
            if prof and prof in by_title:
                d["profile"] = {"id": by_title[prof]["id"], "link": by_title[prof]["link"]}
            for pl in places:
                if pl in by_title:
                    d["places"].append({"title": pl, "link": by_title[pl]["link"]})
            break
    else:
        c.setdefault("places", [])
        fixed[name] = c
chars = fixed


def summary_from(raw):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", raw, flags=re.S)
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()
    t = re.sub(r"^(Lived|Born|Died|Era)\s*:\s*.*?\b(BC|AD|BCE|CE)\b[.,]?\s*", "", t)
    t = re.sub(r"\s*\([^)]*\)", "", t)
    t = re.sub(r"^Bible character (profile|places)\s*\u00b7\s*[A-Z][\w ]*?(?=\s[A-Z][a-z]+\s(was|is|lived|ruled|served|appears|came|grew|led))", "", t).strip()
    t = re.sub(r"^([A-Z][\w’' ]+?),\s+\1\b", r"\1", t)
    s = re.split(r"(?<=[.!?])\s", t)[0] if t else ""
    if "is remembered in Scripture through choices" in s:
        return ""
    return s


MANUAL_SUMMARY = {
    "Abel": "Adam and Eve's second son, a shepherd whose offering God accepted and whose brother Cain killed him (Genesis 4).",
    "Achan": "An Israelite who secretly kept plunder from Jericho that was devoted to God, bringing defeat at Ai (Joshua 7).",
    "Adam": "The first man in Genesis, placed in Eden with one command and the choice of whether to trust it (Genesis 2–3).",
    "Hannah": "A childless woman who prayed at Shiloh for a son and dedicated Samuel to the Lord (1 Samuel 1–2).",
    "Jephthah": "A rejected son of Gilead who became Israel's judge, remembered for his victory over Ammon and a tragic vow (Judges 11).",
    "Joab": "David's nephew and army commander, fiercely loyal and often ruthless, who served through most of David's reign.",
    "Judah and Tamar": "Jacob's son Judah failed his daughter-in-law Tamar, yet their story leads into the family line of David (Genesis 38).",
    "Michal": "Saul's daughter and David's first wife, whose love and loss were caught up in the politics of two kings.",
    "Miriam": "Sister of Moses and Aaron, a prophet who led Israel's song after the sea crossing (Exodus 15:20–21).",
    "Naaman": "An Aramean army commander with a skin disease who was healed after washing in the Jordan at Elisha's word (2 Kings 5).",
    "Uriah the Hittite": "One of David's elite warriors and Bathsheba's husband, whose loyalty David exploited (2 Samuel 11).",
    "Jesus": "How Jesus entered difficult relationships with grace, from Judas and Peter to Zacchaeus and the woman at the well.",
    "John the Apostle": "One of the Twelve, a son of Zebedee and brother of James, traditionally linked with the Gospel of John and Revelation.",
    "Mary": "The young woman from Nazareth whose courageous yes to God's call brought Jesus into the world (Luke 1:26–38).",
    "Priscilla and Aquila": "A tentmaking couple who worked beside Paul and taught the faith from their home (Acts 18; Romans 16:3–5).",
    "Simon of Cyrene": "A man from Cyrene in North Africa whom Roman soldiers forced to carry Jesus's cross (Mark 15:21).",
    "The Christmas Story": "Matthew and Luke tell the birth of Jesus for two different audiences, and the difference is the point.",
    "Zacchaeus": "A wealthy chief tax collector in Jericho who climbed a sycamore-fig tree to see Jesus and repaid those he had cheated (Luke 19).",
}


def clip(s, n=150):
    s = s.replace("—", ", ").replace(" ,", ",")
    m = re.match(r"^(.{2,45}?),\s{2,}(.*)$", s)
    if m:
        s = m.group(2)
    if len(s) <= n:
        return s
    return s[: s.rfind(" ", 0, n)].rstrip(",;:") + "…"


for c in chars.values():
    if c.get("profile") and not c.get("summary"):
        raw = by_id.get(c["profile"]["id"], {}).get("content", {}).get("raw", "")
        c["summary"] = summary_from(raw)
    c["summary"] = clip(c.get("summary") or "")
    if not c["summary"] and c["name"] in MANUAL_SUMMARY:
        c["summary"] = MANUAL_SUMMARY[c["name"]]

# Attach map pages by title: "... in <Name>'s Story" or "... in <Name>’s Story".
for mid in maps:
    p = by_id.get(mid)
    if not p:
        continue
    t = html.unescape(p["title"]["raw"])
    m = re.search(r"in ([A-Z][\w .]+?)[’']s? Story", t) or re.search(r"^(Elizabeth)", t) or re.search(r"(Uz)$", t)
    if not m:
        continue
    key = m.group(1)
    alias = {"Uz": "Job", "Simon": "Simon of Cyrene", "James": "James, son of Zebedee", "Andrew": "Andrew the Apostle",
             "Ezra": "Ezra the Scribe", "Doeg": "Doeg the Edomite", "Uriah": "Uriah the Hittite", "Micah": "Micah of Ephraim",
             "Zechariah": "Zechariah (prophet)", "Abimelech": "Abimelech", "Caleb": "Caleb", "Cornelius": "Cornelius"}.get(key, key)
    target = chars.get(alias) or next((c for n, c in chars.items() if n.split(",")[0] == alias or n.startswith(alias + " ")), None)
    if target and mid not in [x["id"] for x in target["maps"]]:
        target["maps"].append({"id": mid, "title": t, "link": p["link"]})


def month(d):
    return time.strftime("%B %Y", time.strptime(d, "%Y-%m-%d"))


def card(c):
    name = html.escape(c["name"])
    img = c.get("img")
    pic = (f'<img src="{html.escape(img)}" alt="Imagined portrait of {name}" loading="lazy" decoding="async" width="400" height="225">'
           if img else f'<div class="bc-noimg" aria-hidden="true">{html.escape(c["name"][0])}</div>')
    links = []
    for p in sorted(c["posts"], key=lambda x: x["date"]):
        if p["status"] == "publish" and p.get("link"):
            links.append(f'<a class="bc-read" href="{p["link"]}">{html.escape(p["title"])}</a>')
        else:
            links.append(f'<span class="bc-soon" data-post="{p["id"]}">New reflection coming {month(p["date"])}</span>')
    extra = []
    if c.get("profile"):
        extra.append(f'<a href="{c["profile"]["link"]}">Profile</a>')
    for m in c.get("maps", [])[:2]:
        extra.append(f'<a href="{m["link"]}">Map</a>')
    for pl in c.get("places", [])[:1]:
        extra.append(f'<a href="{pl["link"]}">Place</a>')
    search = html.escape((c["name"] + " " + " ".join(p["title"] for p in c["posts"])).lower())
    return (f'<article class="bc-card" data-t="{c["t"]}" data-s="{search}">{pic}<div class="bc-body">'
            f'<h3>{name}</h3>' + (f'<p>{html.escape(c["summary"])}</p>' if c.get("summary") else "") +
            '<div class="bc-posts">' + "".join(links) + '</div>' +
            (f'<div class="bc-links">{" · ".join(extra)}</div>' if extra else "") + '</div></article>')


def section(t, label):
    cs = sorted((c for c in chars.values() if c["t"] == t), key=lambda c: c["name"].lower())
    return (f'<section class="bc-sec" data-sec="{t}"><h2>{label} <span>{len(cs)} people</span></h2>'
            f'<div class="bc-grid">' + "".join(card(c) for c in cs) + '</div></section>')


CSS = """
.bc{--ink:#111;--muted:#6b6b6b;--line:#e6e2d8;--accent:#dd3333;--paper:#faf8f3}
.bc-intro{font-size:1.1em;line-height:1.65;color:#333;margin:0 0 18px}
.bc-stats{display:flex;flex-wrap:wrap;gap:8px 22px;margin:0 0 22px;font-size:.9em;color:var(--muted)}
.bc-stats b{color:var(--ink);font-size:1.25em;margin-right:4px}
.bc-bar{position:sticky;top:64px;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 0;background:#fff;border-bottom:1px solid var(--line);margin-bottom:18px}
.bc-bar button{font:inherit;font-size:.85em;padding:6px 14px!important;border-radius:999px;border:1px solid var(--line)!important;background:#fff!important;color:var(--ink)!important;cursor:pointer;line-height:1.4;min-height:0;letter-spacing:normal;text-transform:none}
.bc-bar button[aria-pressed="true"]{background:var(--ink)!important;border-color:var(--ink)!important;color:#fff!important}
.bc-bar input{flex:1 1 180px;min-width:0;font:inherit;font-size:.9em;padding:7px 12px;border:1px solid var(--line);border-radius:999px}
.bc-sec h2{display:flex;align-items:baseline;gap:10px;margin:28px 0 14px}
.bc-sec h2 span{font-size:.5em;font-weight:400;color:var(--muted);letter-spacing:.04em;text-transform:uppercase}
.bc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px}
.bc-card{border:1px solid var(--line);border-radius:6px;overflow:hidden;background:#fff;display:flex;flex-direction:column;transition:box-shadow .15s,transform .15s}
.bc-card:hover{box-shadow:0 6px 20px rgba(0,0,0,.08);transform:translateY(-2px)}
.bc-card img,.bc-noimg{display:block;width:100%;aspect-ratio:16/9;height:auto;object-fit:cover;background:#222}
.bc-noimg{display:grid;place-items:center;color:#fff;font-size:2.2em;font-weight:700;background:linear-gradient(135deg,#1f1f1f,#4a4a4a)}
.bc-body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.bc-body h3{margin:0;font-size:1.05em;line-height:1.25}
.bc-body p{margin:0;font-size:.85em;line-height:1.5;color:#444}
.bc-posts{display:flex;flex-direction:column;gap:4px;margin-top:auto}
.bc-read{font-weight:700;font-size:.88em;color:var(--ink);text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:3px}
.bc-soon{font-size:.8em;color:var(--muted);font-style:italic}
.bc-links{font-size:.8em;color:var(--muted)}
.bc-links a{color:var(--accent);font-weight:600}
.bc-empty{display:none;color:var(--muted);font-style:italic;padding:20px 0}
.bc-maps{columns:2 260px;column-gap:28px;padding-left:18px}
.bc-maps li{margin:3px 0;break-inside:avoid}
"""

JS = r"""(function(){var r=document.querySelector('.bc');if(!r)return;
var cards=[].slice.call(r.querySelectorAll('.bc-card')),secs=[].slice.call(r.querySelectorAll('.bc-sec')),btns=[].slice.call(r.querySelectorAll('.bc-bar button')),q=r.querySelector('.bc-bar input'),empty=r.querySelector('.bc-empty'),mode='all';
function apply(){var s=(q.value||'').trim().toLowerCase(),n=0;cards.forEach(function(c){var ok=(mode==='all'||c.dataset.t===mode)&&(!s||c.dataset.s.indexOf(s)>=0);c.style.display=ok?'':'none';if(ok)n++;});
secs.forEach(function(sec){sec.style.display=[].some.call(sec.querySelectorAll('.bc-card'),function(c){return c.style.display!=='none';})?'':'none';});empty.style.display=n?'none':'block';}
btns.forEach(function(b){b.addEventListener('click',function(){mode=b.dataset.f;btns.forEach(function(x){x.setAttribute('aria-pressed',x===b);});apply();});});
q.addEventListener('input',apply);
var soon=[].slice.call(r.querySelectorAll('.bc-soon[data-post]'));if(!soon.length)return;
var ids=soon.map(function(e){return e.dataset.post;});
fetch('/wp-json/wp/v2/posts?include='+ids.join(',')+'&per_page=100&_fields=id,link,title',{credentials:'omit'}).then(function(x){return x.ok?x.json():[];}).then(function(list){
list.forEach(function(p){soon.forEach(function(e){if(+e.dataset.post===p.id){var a=document.createElement('a');a.className='bc-read';a.href=p.link;var t=document.createElement('textarea');t.innerHTML=p.title.rendered;a.textContent=t.value;e.parentNode.replaceChild(a,e);}});});}).catch(function(){});
})();"""


def render():
    n_chars = len(chars)
    n_pub = sum(1 for c in chars.values() for p in c["posts"] if p["status"] == "publish")
    map_links = []
    for mid in maps:
        p = by_id.get(mid)
        if p:
            map_links.append((html.unescape(p["title"]["raw"]), p["link"]))
    map_links.sort(key=lambda x: x[0].lower())
    body = (
        f'<div class="bc"><style>{CSS}</style>'
        '<p class="bc-intro">Leadership lessons from the people of the Bible. Each reflection looks at one person’s choices under pressure, '
        'with a profile that sticks to what the text says and an interactive map of where the story happened. Search by name or browse by testament.</p>'
        f'<div class="bc-stats"><span><b>{n_chars}</b>people</span><span><b>{n_pub}</b>reflections so far</span><span><b>{len(map_links)}</b>interactive maps</span><span><b>1</b>new story every week</span></div>'
        '<div class="bc-bar" role="search"><button type="button" data-f="all" aria-pressed="true">All</button>'
        '<button type="button" data-f="OT" aria-pressed="false">Old Testament</button><button type="button" data-f="NT" aria-pressed="false">New Testament</button>'
        '<input type="search" placeholder="Search by name or title" aria-label="Search Bible characters"></div>'
        + section("OT", "Old Testament") + section("NT", "New Testament") +
        '<p class="bc-empty">No one matches that search yet.</p>'
        '<h2>All interactive Bible maps</h2><ul class="bc-maps">' +
        "".join(f'<li><a href="{l}">{html.escape(t)}</a></li>' for t, l in map_links) + '</ul>'
        f'<script src="data:text/javascript;base64,{base64.b64encode(JS.encode()).decode()}"></script></div>'
    )
    return "<!-- wp:html -->" + body + "<!-- /wp:html -->"


if __name__ == "__main__":
    content = render()
    (ROOT / "site" / "bible-characters.html").write_text(content)
    print(len(chars), "characters,", len(content) // 1024, "KB")
    if "--apply" in sys.argv:
        c, existing = wp.request("GET", "/wp/v2/pages?slug=bible-characters&_fields=id")
        body = {"title": "Bible Characters", "slug": "bible-characters", "status": "publish", "content": content,
                "excerpt": "Leadership lessons from the people of the Bible: every character with their reflection, profile and interactive map, grouped by Old and New Testament."}
        path = f"/wp/v2/pages/{existing[0]['id']}" if existing else "/wp/v2/pages"
        code, res = wp.request("POST", path, json.dumps(body).encode(), {"Content-Type": "application/json"})
        print("published" if code in (200, 201) else f"FAILED {code} {res}", res.get("link") if isinstance(res, dict) else "")
