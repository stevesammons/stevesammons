#!/usr/bin/env python3
"""Write songs/supabase/seed-posts-N-of-M.sql: every Bible-character post (Old and New Testament
categories, published and scheduled; posts only, never pages) as a row in the songs table,
with the post's plain text as the song's story source and every live link we can find:
the WordPress post, the matching Substack post and podcast episode, and the song's YouTube video.

  python3 songs/supabase/export_posts.py

Priority follows Steve's order: scheduled posts from the latest date backwards, then
published posts from newest to oldest. Re-running refreshes post fields and fills in links
that have gone live; it never erases a link, a song or a status already in Supabase.
"""
import html, json, re, subprocess, sys, urllib.request
from datetime import date
from pathlib import Path

CATEGORIES = "1804,1805"  # Old Testament, New Testament
SUBSTACK = "https://sammons.substack.com"
OUT = Path(__file__).with_name("seed-posts.sql")  # written as seed-posts-N-of-M.sql
PER_FILE = 20

# Songs made before this pipeline (song.md packages in Steve's Google Drive).
DONE_BEFORE = {
    1854: "Caleb", 1903: "Solomon", 1907: "Hezekiah", 2656: "Nabal", 2642: "Nathan",
    1875: "Shadrach, Meshach, and Abednego",
}
# Song videos already on YouTube (from the song.md packages).
YOUTUBE = {1907: "https://youtu.be/Z7MxXz8HG2A", 2642: "https://youtu.be/C_elMZW17Jk"}
# Substack podcast episodes have their own titles, so map them by hand: slug -> post ID.
PODCASTS = {
    "when-truth-feels-dangerous": 2642,          # Nathan
    "the-dangerous-gap-between-smart-and": 2627,  # Ahithophel
    "what-do-we-owe-the-years-we-were": 1907,     # Hezekiah
    "when-faithfulness-cannot-see-the": 1875,     # Shadrach, Meshach, and Abednego
    "why-an-85-year-old-chose-giants": 1854,      # Caleb
}
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) stevesammons-songs"}


def wp(path):
    out = subprocess.run([sys.executable, "tools/wp.py", "GET", path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def substack_archive():
    items, offset = {}, 0
    while True:
        req = urllib.request.Request(f"{SUBSTACK}/api/v1/archive?sort=new&offset={offset}&limit=50", headers=UA)
        batch = json.load(urllib.request.urlopen(req, timeout=60))
        for p in batch:
            items[p["id"]] = p
        if not batch:
            return list(items.values())
        offset += len(batch)


def plain_text(raw):
    t = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    t = re.sub(r"<(script|style)\b.*?</\1>", "", t, flags=re.S | re.I)
    t = re.sub(r"</?(p|h[1-6]|li|blockquote|div|br)\b[^>]*>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def norm(title):
    return re.sub(r"[^a-z0-9]", "", html.unescape(title).lower().replace("’", "'"))


SEMI = "[[semicolon]]"


def quote(value, tag="q"):
    """Dollar-quote a value. Supabase's SQL Editor splits scripts at every semicolon, even inside
    quoted text, so semicolons are written as a placeholder and put back by replace(...chr(59))."""
    if value is None:
        return "null"
    s = str(value)
    assert f"${tag}$" not in s and SEMI not in s
    if ";" not in s:
        return f"${tag}${s}${tag}$"
    return f"replace(${tag}${s.replace(';', SEMI)}${tag}$, '{SEMI}', chr(59))"


def match_substack(posts, archive):
    """Newsletter posts: same slug, then same title, then the only one published within a day."""
    letters = [a for a in archive if a.get("type") == "newsletter"]
    found, used = {}, set()
    for rule in ("slug", "title", "date"):
        for p in posts:
            if p["id"] in found or p["status"] != "publish":
                continue
            day = date.fromisoformat(p["date"][:10])
            hits = [a for a in letters if a["id"] not in used and (
                a["slug"] == p["slug"] if rule == "slug" else
                norm(a["title"]) == norm(p["title"]["raw"]) if rule == "title" else
                abs((date.fromisoformat(a["post_date"][:10]) - day).days) <= 1)]
            if len(hits) == 1:
                found[p["id"]] = hits[0]["canonical_url"]
                used.add(hits[0]["id"])
    unmatched = [a["slug"] for a in letters if a["id"] not in used]
    return found, unmatched


def main():
    posts = {}
    for status in ("future", "publish"):
        page = 1
        while True:
            batch = wp(f"/wp/v2/posts?status={status}&categories={CATEGORIES}&per_page=100&page={page}"
                       "&context=edit&_fields=id,date,date_gmt,slug,link,status,title,content")
            for p in batch:
                posts[p["id"]] = p
            if len(batch) < 100:
                break
            page += 1

    archive = substack_archive()
    substack, unmatched = match_substack(list(posts.values()), archive)
    podcasts = {PODCASTS[a["slug"]]: a for a in archive if a.get("type") == "podcast" and a["slug"] in PODCASTS}
    new_podcasts = [a["slug"] for a in archive if a.get("type") == "podcast" and a["slug"] not in PODCASTS]

    future = sorted((p for p in posts.values() if p["status"] == "future"), key=lambda p: p["date"], reverse=True)
    published = sorted((p for p in posts.values() if p["status"] == "publish"), key=lambda p: p["date"], reverse=True)

    lines = ["-- Generated by songs/supabase/export_posts.py. Run in Supabase > SQL Editor after schema.sql.",
             f"-- {len(future)} scheduled and {len(published)} published Bible-character posts.", ""]
    for priority, p in enumerate(future + published, start=1):
        pid = p["id"]
        character = DONE_BEFORE.get(pid)
        podcast = podcasts.get(pid)
        values = [
            str(pid), quote(html.unescape(p["title"]["raw"])), quote(p["slug"]),
            quote(plain_text(p["content"]["raw"]), "pt"), quote(p["date_gmt"] + "Z"), quote(p["status"]),
            str(priority),
            quote(p["link"] if p["status"] == "publish" else None),
            quote(substack.get(pid)),
            quote(podcast and podcast["canonical_url"]), quote(podcast and podcast["title"]),
            quote(YOUTUBE.get(pid)),
            quote(character), quote("done_before" if character else "waiting"),
        ]
        lines.append(
            "insert into public.songs (post_id, post_title, slug, post_text, publish_date, post_status, priority, "
            "wordpress_url, substack_url, podcast_url, podcast_title, youtube_url, character, status) values ("
            + ", ".join(values) + ")\n"
            "on conflict (post_id) do update set post_title = excluded.post_title, slug = excluded.slug, "
            "post_text = excluded.post_text, publish_date = excluded.publish_date, "
            "post_status = excluded.post_status, priority = excluded.priority, "
            "wordpress_url = coalesce(excluded.wordpress_url, songs.wordpress_url), "
            "substack_url = coalesce(excluded.substack_url, songs.substack_url), "
            "podcast_url = coalesce(excluded.podcast_url, songs.podcast_url), "
            "podcast_title = coalesce(excluded.podcast_title, songs.podcast_title), "
            "youtube_url = coalesce(excluded.youtube_url, songs.youtube_url);")
    # Several small files: the Supabase SQL Editor and some copy tools cut off very long pastes.
    for old in OUT.parent.glob("seed-posts*.sql"):
        old.unlink()
    header, rows = lines[:3], lines[3:]
    parts = [rows[i:i + PER_FILE] for i in range(0, len(rows), PER_FILE)]
    for n, part in enumerate(parts, start=1):
        name = OUT.parent / f"seed-posts-{n}-of-{len(parts)}.sql"
        name.write_text("\n".join(header + [f"-- Part {n} of {len(parts)}.", ""] + part) + "\n")
    print(f"{len(parts)} files, largest {max(f.stat().st_size for f in OUT.parent.glob('seed-posts-*.sql')) // 1024} KB")
    print(f"{OUT.parent}: {len(posts)} posts ({len(future)} scheduled, {len(published)} published), "
          f"{sum(1 for i in posts if i in DONE_BEFORE)} done_before")
    print(f"links: {len(substack)} Substack posts, {len(podcasts)} podcasts, {len(YOUTUBE)} YouTube")
    if unmatched:
        print("Substack newsletters with no Bible-character post:", ", ".join(unmatched))
    if new_podcasts:
        print("Podcasts not yet mapped in PODCASTS:", ", ".join(new_podcasts))


if __name__ == "__main__":
    main()
