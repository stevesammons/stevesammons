#!/usr/bin/env python3
"""Swap the old static map on "Hebron in Caleb's Story" for embed.html.

Credentials come only from the environment and are never printed:
  WP_USER          WordPress username
  WP_APP_PASSWORD  Application Password (Users -> Profile -> Application Passwords)

Usage:
  python3 publish.py            # dry run: fetch, back up, show what would change
  python3 publish.py --apply    # write the change to the live page
"""
import base64, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

SITE = os.environ.get("WP_SITE", "https://stevesammons.com")
PAGE_ID = int(os.environ.get("WP_PAGE_ID", "3169"))
HERE = Path(__file__).resolve().parent
START, END = "<!-- chm:start -->", "<!-- chm:end -->"


def api(method, path, body=None, auth=None):
    req = urllib.request.Request(SITE + "/wp-json/wp/v2" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "hebron-map-publisher")
    if auth:
        req.add_header("Authorization", "Basic " + auth)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        sys.exit(f"{method} {path} failed: HTTP {e.code}: {detail}")


def new_content(raw, embed):
    block = f"{START}\n{embed.strip()}\n{END}"
    if START in raw and END in raw:  # re-run: replace our previous insert
        return re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, raw, count=1, flags=re.S)
    figs = [m for m in re.finditer(r"<figure\b.*?</figure>", raw, flags=re.S)
            if "orientation map" in m.group(0) or "orientation diagram" in m.group(0)]
    if len(figs) != 1:
        sys.exit(f"Expected exactly one old map <figure>, found {len(figs)}. Nothing changed.")
    return raw[:figs[0].start()] + block + raw[figs[0].end():]


def main():
    apply = "--apply" in sys.argv
    user, pw = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
    if not user or not pw:
        sys.exit("Set WP_USER and WP_APP_PASSWORD in the environment first.")
    auth = base64.b64encode(f"{user}:{pw.replace(' ', '')}".encode()).decode()

    page = api("GET", f"/pages/{PAGE_ID}?context=edit", auth=auth)
    raw = page["content"]["raw"]
    backups = HERE / "backups"
    backups.mkdir(exist_ok=True)
    bak = backups / f"page-{PAGE_ID}-{time.strftime('%Y%m%d-%H%M%S')}.html"
    bak.write_text(raw)
    print(f"Fetched '{page['title']['raw']}' (modified {page['modified']}); backup saved to {bak.name}")

    if "<!-- wp:" not in raw:
        sys.exit("Page uses the classic editor; WordPress would add <p>/<br> tags inside the script. Nothing changed.")

    updated = new_content(raw, (HERE / "embed.html").read_text())
    if updated == raw:
        print("Page already has the current map. Nothing to do.")
        return
    print(f"Content length {len(raw)} -> {len(updated)} characters.")
    if not apply:
        (backups / "proposed.html").write_text(updated)
        print("Dry run only. Proposed content saved to backups/proposed.html. Re-run with --apply to publish.")
        return

    res = api("POST", f"/pages/{PAGE_ID}", {"content": updated}, auth=auth)
    saved = res["content"]["raw"]
    if "<script" not in saved or 'id="chm"' not in saved:
        sys.exit("Saved, but WordPress stripped the <script> or map markup (account lacks unfiltered_html?). "
                 f"Restore with backups/{bak.name} if needed.")
    print(f"Published. Page modified {res['modified']}: {res['link']}")


if __name__ == "__main__":
    main()
