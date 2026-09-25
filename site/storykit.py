"""Shared pieces for the Characters Worth Following pages (hub, songs, maps, post strip).

Data comes from site/stories.json (refresh it with `python3 site/stories.py`).
"""
import base64, html, json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wp  # noqa: E402

SERIES = "Characters Worth Following"
SITE = "https://stevesammons.com"
YOUTUBE = "https://www.youtube.com/@CharactersWorthFollowing"
UPLOADS = "UUuXn2l6fvPZCFTWCxkLr_pA"  # the channel's uploads playlist
SUBSTACK = "https://sammons.substack.com"
DEEP_DIVES = SUBSTACK + "/podcast"
SUBSCRIBE = SUBSTACK + "/subscribe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
PARTS = [("read", "Read"), ("listen", "Listen"), ("deep", "Deep dive"), ("profile", "Profile"), ("map", "Map")]

esc = html.escape


def characters():
    return json.loads((ROOT / "site" / "stories.json").read_text())["characters"]


def month(d):
    return time.strftime("%B %Y", time.strptime(d, "%Y-%m-%d"))


def parts(c):
    """The five parts for a character: {key: (href or None, detail text, post id if scheduled)}."""
    out = {}
    rows = c.get("post_rows", [])
    live = [r for r in rows if r["status"] == "publish"]
    if live:
        out["read"] = (live[-1]["link"], live[-1]["title"], None)
    elif rows:
        out["read"] = (None, "Coming " + month(rows[0]["date"]), rows[0]["id"])
    if c.get("song"):
        out["listen"] = (c["song"]["url"], c["song"]["title"], None)
    if c.get("deep"):
        d = c["deep"]
        out["deep"] = (d["url"], f'{d["title"]} ({d["minutes"]} min)' if d.get("minutes") else d["title"], None)
    if c.get("profile"):
        out["profile"] = (c["profile"]["link"], c["name"], None)
    if c.get("maps"):
        out["map"] = (c["maps"][0]["link"], c["maps"][0]["title"], None)
    return out


def chips(c, cls="cw-parts"):
    """Numbered row of the five parts; missing parts are dimmed so the pattern stays visible."""
    p = parts(c)
    items = []
    for i, (k, label) in enumerate(PARTS, 1):
        href, detail, pending = p.get(k, (None, "Not yet", None))
        ext = href and not href.startswith(SITE)
        tip = esc(f"{label}: {detail}")
        if href:
            items.append(f'<a class="cw-part is-on" href="{esc(href)}" title="{tip}"'
                         + (' target="_blank" rel="noopener"' if ext else "") + f'><i>{i}</i>{label}</a>')
        else:
            data = f' data-post="{pending}"' if pending else ""
            items.append(f'<span class="cw-part"{data} title="{tip}"><i>{i}</i>{label}</span>')
    return f'<nav class="{cls}" aria-label="{esc(c["name"])} in five parts">' + "".join(items) + "</nav>"


CSS = """
.cw{--ink:#111;--muted:#6b6b6b;--line:#e6e2d8;--accent:#dd3333;--paper:#faf8f3}
.cw-intro{font-size:1.1em;line-height:1.65;color:#333;margin:0 0 18px}
.cw-steps{list-style:none;margin:0 0 26px;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;counter-reset:s}
.cw-steps li{border:1px solid var(--line);border-top:3px solid var(--ink);border-radius:4px;padding:10px 12px;background:#fff;font-size:.85em;line-height:1.45;color:#444;counter-increment:s}
.cw-steps li b{display:block;font-size:1.05em;color:var(--ink);margin-bottom:2px}
.cw-steps li b::before{content:counter(s) ". ";color:var(--accent)}
.cw-steps a{color:var(--accent);font-weight:600}
.cw-parts{display:flex;flex-wrap:wrap;gap:4px}
.cw-part{display:inline-flex;align-items:center;gap:4px;font-size:.72em;font-weight:600;line-height:1;padding:4px 7px 4px 4px;border-radius:999px;border:1px solid var(--line);color:#b3b0a8;white-space:nowrap;text-decoration:none!important}
.cw-part i{font-style:normal;display:inline-grid;place-items:center;width:15px;height:15px;border-radius:50%;background:#eee;color:#999;font-size:.9em}
.cw-part.is-on{color:var(--ink);border-color:#cfcabe}
.cw-part.is-on i{background:var(--accent);color:#fff}
a.cw-part.is-on:hover{background:var(--ink);color:#fff;border-color:var(--ink)}
.cw-bar{position:sticky;top:64px;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 0;background:#fff;border-bottom:1px solid var(--line);margin-bottom:18px}
.cw-bar button{font:inherit;font-size:.85em;padding:6px 14px!important;border-radius:999px;border:1px solid var(--line)!important;background:#fff!important;color:var(--ink)!important;cursor:pointer;line-height:1.4;min-height:0;letter-spacing:normal;text-transform:none}
.cw-bar button[aria-pressed="true"]{background:var(--ink)!important;border-color:var(--ink)!important;color:#fff!important}
.cw-bar input{flex:1 1 180px;min-width:0;font:inherit;font-size:.9em;padding:7px 12px;border:1px solid var(--line);border-radius:999px}
.cw-sec h2{display:flex;align-items:baseline;gap:10px;margin:28px 0 14px}
.cw-sec h2 span{font-size:.5em;font-weight:400;color:var(--muted);letter-spacing:.04em;text-transform:uppercase}
.cw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px}
.cw-card{border:1px solid var(--line);border-radius:6px;overflow:hidden;background:#fff;display:flex;flex-direction:column;transition:box-shadow .15s,transform .15s}
.cw-card:hover{box-shadow:0 6px 20px rgba(0,0,0,.08);transform:translateY(-2px)}
.cw-card img,.cw-noimg{display:block;width:100%;aspect-ratio:16/9;height:auto;object-fit:cover;background:#222}
.cw-noimg{display:grid;place-items:center;color:#fff;font-size:2.2em;font-weight:700;background:linear-gradient(135deg,#1f1f1f,#4a4a4a)}
.cw-body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.cw-body h3{margin:0;font-size:1.05em;line-height:1.25}
.cw-body h3 a{color:var(--ink)!important;text-decoration:none}
.cw-body h3 a:hover{color:var(--accent)!important}
.cw-body p{margin:0;font-size:.85em;line-height:1.5;color:#444}
.cw-body .cw-parts{margin-top:auto;padding-top:4px}
.cw-kicker{font-size:.72em;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.cw-empty{display:none;color:var(--muted);font-style:italic;padding:20px 0}
.cw-btn{display:inline-block;padding:10px 18px;border-radius:999px;background:var(--ink);color:#fff!important;font-weight:700;font-size:.9em;text-decoration:none!important}
.cw-btn.alt{background:#fff;color:var(--ink)!important;border:1px solid var(--ink)}
.cw-btn.red{background:var(--accent)}
.cw-cta{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 26px}
@media (max-width:600px){.cw-bar{top:0}.cw-steps{grid-template-columns:1fr 1fr}}
"""

# Filter by testament/search, and upgrade "Coming <month>" chips once a scheduled post is public.
FILTER_JS = r"""(function(){var r=document.querySelector('.cw');if(!r)return;
var cards=[].slice.call(r.querySelectorAll('.cw-card')),secs=[].slice.call(r.querySelectorAll('.cw-sec')),btns=[].slice.call(r.querySelectorAll('.cw-bar button')),q=r.querySelector('.cw-bar input'),empty=r.querySelector('.cw-empty'),mode='all';
function apply(){var s=((q&&q.value)||'').trim().toLowerCase(),n=0;cards.forEach(function(c){var ok=(mode==='all'||c.dataset.t===mode||(mode==='song'&&c.dataset.song))&&(!s||c.dataset.s.indexOf(s)>=0);c.style.display=ok?'':'none';if(ok)n++;});
secs.forEach(function(sec){sec.style.display=[].some.call(sec.querySelectorAll('.cw-card'),function(c){return c.style.display!=='none';})?'':'none';});if(empty)empty.style.display=n?'none':'block';}
btns.forEach(function(b){b.addEventListener('click',function(){mode=b.dataset.f;btns.forEach(function(x){x.setAttribute('aria-pressed',x===b);});apply();});});
if(q)q.addEventListener('input',apply);
var soon=[].slice.call(r.querySelectorAll('.cw-part[data-post]'));if(!soon.length)return;
var ids=soon.map(function(e){return e.dataset.post;}).filter(function(v,i,a){return a.indexOf(v)===i;});
fetch('/wp-json/wp/v2/posts?include='+ids.join(',')+'&per_page=100&_fields=id,link,title',{credentials:'omit'}).then(function(x){return x.ok?x.json():[];}).then(function(list){
list.forEach(function(p){soon.forEach(function(e){if(+e.dataset.post===p.id){var a=document.createElement('a');a.className='cw-part is-on';a.href=p.link;var t=document.createElement('textarea');t.innerHTML=p.title.rendered;a.title='Read: '+t.value;a.innerHTML=e.innerHTML;e.parentNode.replaceChild(a,e);}});});}).catch(function(){});
})();"""


def script(js):
    """Inline scripts get mangled by the site's content filters, so ship them as data: URIs."""
    return f'<script src="data:text/javascript;base64,{base64.b64encode(js.encode()).decode()}"></script>'


def block(body):
    return "<!-- wp:html -->" + body + "<!-- /wp:html -->"


def publish(slug, title, content, excerpt, apply, status="publish"):
    (ROOT / "site" / f"{slug}.html").write_text(content)
    print(f"{slug}: {len(content) // 1024} KB")
    if not apply:
        return None
    code, existing = wp.request("GET", f"/wp/v2/pages?slug={slug}&status=publish,draft&context=edit&_fields=id,content,excerpt")
    body = {"title": title, "slug": slug, "status": status, "content": content}
    if existing:
        (ROOT / "backups").mkdir(exist_ok=True)
        (ROOT / "backups" / f"page-{existing[0]['id']}-{int(time.time())}.json").write_text(json.dumps(existing[0]))
        if not existing[0]["excerpt"]["raw"].strip():
            body["excerpt"] = excerpt  # never overwrite a hand-edited excerpt
    else:
        body["excerpt"] = excerpt
    path = f"/wp/v2/pages/{existing[0]['id']}" if existing else "/wp/v2/pages"
    code, res = wp.request("POST", path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    if code not in (200, 201):
        print("FAILED", code, res)
        return None
    print("saved", res["id"], res["status"], res["link"])
    if status == "publish":
        check(res["link"], script=True)
    return res


def check(url, must=(), script=False):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + f"v={int(time.time())}", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            page = r.read().decode("utf-8", "replace")
            missing = [m for m in must if m not in page]
            ok = r.status == 200 and (not script or "data:text/javascript;base64," in page) and not missing
            print("live", r.status, "ok" if ok else f"CHECK missing={missing}", url)
            return ok
    except Exception as e:
        print("live CHECK failed", e, url)
        return False
