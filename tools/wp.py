#!/usr/bin/env python3
"""Minimal WordPress REST client for stevesammons.com.

Credentials come only from the environment and are never printed:
  WP_USER, WP_APP_PASSWORD   (optional WP_SITE, default https://stevesammons.com)

Usage:
  python3 tools/wp.py check                              # verify login and show capabilities
  python3 tools/wp.py GET  /wp/v2/pages?search=hebron
  python3 tools/wp.py POST /wp/v2/posts '{"title":"Draft","status":"draft"}'
  python3 tools/wp.py POST /wp/v2/pages/3169 @body.json  # JSON body from a file
  python3 tools/wp.py DELETE /wp/v2/posts/123
  python3 tools/wp.py UPLOAD image.jpg                   # add to the media library
Paths are relative to /wp-json. Output is JSON on stdout.
"""
import base64, json, mimetypes, os, sys, urllib.error, urllib.request
from pathlib import Path

SITE = os.environ.get("WP_SITE", "https://stevesammons.com").rstrip("/")


def auth_header():
    user, pw = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
    if not user or not pw:
        return None
    return "Basic " + base64.b64encode(f"{user}:{pw.replace(' ', '')}".encode()).decode()


def request(method, path, data=None, headers=None):
    url = SITE + "/wp-json" + (path if path.startswith("/") else "/" + path)
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("User-Agent", "stevesammons-claude")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    a = auth_header()
    if a:
        req.add_header("Authorization", a)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read()
            return r.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"error": body[:500]}


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd = argv[1].upper()
    if cmd == "CHECK":
        if not auth_header():
            sys.exit("WP_USER / WP_APP_PASSWORD are not set in this session.")
        code, me = request("GET", "/wp/v2/users/me?context=edit")
        if code != 200:
            hint = ""
            if isinstance(me, dict) and me.get("code") == "rest_not_logged_in":
                hint = ("\nThe login was ignored. Application Passwords are probably disabled "
                        "(Wordfence > Login Security > Settings) or Apache is dropping the Authorization header.")
            sys.exit(f"Login failed (HTTP {code}): {me.get('code') if isinstance(me, dict) else me}{hint}")
        caps = me.get("capabilities", {})
        print(json.dumps({"user": me.get("slug"), "roles": me.get("roles"),
                          "administrator": bool(caps.get("manage_options")),
                          "unfiltered_html": bool(caps.get("unfiltered_html")),
                          "install_plugins": bool(caps.get("install_plugins"))}, indent=2))
        return
    if cmd == "UPLOAD":
        f = Path(argv[2])
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        code, out = request("POST", "/wp/v2/media", f.read_bytes(),
                            {"Content-Type": ctype, "Content-Disposition": f'attachment; filename="{f.name}"'})
    else:
        body = None
        if len(argv) > 3:
            raw = argv[3]
            body = (Path(raw[1:]).read_text() if raw.startswith("@") else raw).encode()
        code, out = request(cmd, argv[2], body, {"Content-Type": "application/json"} if body else None)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if code >= 400:
        sys.exit(f"HTTP {code}")


if __name__ == "__main__":
    main(sys.argv)
