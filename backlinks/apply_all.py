#!/usr/bin/env python3
"""Apply back links to every page in backups/backlink-map.json and verify each live page."""
import json, re, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = json.load(open(ROOT / "backups/backlink-map.json"))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
results = []
for r in rows:
    title = r["title"].replace("&#8217;", "’")
    place = "Story" in title  # "Jericho in Zacchaeus's Story", "The World of Abel's Story"
    args = [sys.executable, str(ROOT / "backlinks/apply.py"), str(r["page"]), ",".join(map(str, r["posts"]))]
    if not place:
        args.append(title)
    args.append("--apply")
    out = subprocess.run(args, capture_output=True, text=True)
    msg = (out.stdout + out.stderr).strip().splitlines()[-1] if (out.stdout + out.stderr).strip() else ""
    time.sleep(1)
    req = urllib.request.Request(r["link"] + f"?v={int(time.time())}", headers={"User-Agent": UA})
    try:
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        slots = html.count('class="ss-back')
        clean = bool(re.search(r'data:text/javascript;base64,[A-Za-z0-9+/=]+"', html))
        live = "ok" if slots == 2 and clean else f"CHECK slots={slots} script_ok={clean}"
    except Exception as e:
        live = f"CHECK fetch failed: {e}"
    ok = out.returncode == 0 and live == "ok"
    results.append({**r, "result": msg, "live": live, "ok": ok})
    print(("OK  " if ok else "FAIL"), r["page"], title, "|", msg, "|", live, flush=True)
json.dump(results, open(ROOT / "backups/backlink-results.json", "w"), indent=1)
print(sum(x["ok"] for x in results), "of", len(results), "pages OK")
