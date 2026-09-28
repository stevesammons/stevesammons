#!/usr/bin/env python3
"""Generate and publish the Characters hub page (/bible-characters/).

  python3 site/stories.py              # refresh the data first
  python3 site/build_hub.py [--apply]

The page lists posts only: one card per character with a published reflection, leading to that post,
with the character's five parts (read, gospel quartet, podcast, profile, map) as chips. Characters whose
post is only scheduled are in the page but hidden, and appear in the browser as soon as the post is public.
"""
import sys
from storykit import (CSS, DEEP_DIVES, SERIES, SITE, YOUTUBE, block, characters, chips, esc,
                      publish, script)

chars = characters()


def card(c):
    """One card per character, leading to their reflection post. Characters whose post is only
    scheduled are in the page but hidden; HUB_JS reveals them once the post is public."""
    name = esc(c["name"])
    rows = c.get("post_rows", [])
    live = [r for r in rows if r["status"] == "publish"]
    post = live[-1] if live else rows[0]
    href = esc(post["link"]) if live else "#"
    pic = (f'<img src="{esc(c["img"])}" alt="Imagined portrait of {name}" loading="lazy" decoding="async" width="400" height="225">'
           if c.get("img") else f'<div class="cw-noimg" aria-hidden="true">{esc(c["name"][0])}</div>')
    search = esc((c["name"] + " " + " ".join(r["title"] for r in rows) + (" " + c["song"]["title"] if c.get("song") else "")).lower())
    song = ' data-song="1"' if c.get("song") else ""
    wait = "" if live else f' data-wait="{post["id"]}" hidden'
    return (f'<article class="cw-card" data-t="{c["t"]}"{song} data-s="{search}"{wait}><a class="cw-pic" href="{href}" tabindex="-1" aria-hidden="true">{pic}</a>'
            f'<div class="cw-body"><h3><a href="{href}">{name}</a></h3>'
            f'<p><b class="cw-ptitle">{esc(post["title"])}.</b> {esc(c.get("summary", ""))}</p>{chips(c)}</div></article>')


def section(t, label):
    cs = sorted((c for c in chars if c["t"] == t and c.get("post_rows")), key=lambda c: c["name"].lower())
    n = sum(1 for c in cs if any(r["status"] == "publish" for r in c["post_rows"]))
    return (f'<section class="cw-sec"><h2>{label} <span><b class="cw-n">{n}</b> people</span></h2>'
            '<div class="cw-grid">' + "".join(card(c) for c in cs) + "</div></section>")


# Filter by testament/search, and reveal scheduled characters once their post is public
# (the public REST API only returns published posts, so no clock or rebuild is needed).
HUB_JS = r"""(function(){var r=document.querySelector('.cw');if(!r)return;
var all=[].slice.call(r.querySelectorAll('.cw-card')),secs=[].slice.call(r.querySelectorAll('.cw-sec')),btns=[].slice.call(r.querySelectorAll('.cw-bar button')),q=r.querySelector('.cw-bar input'),empty=r.querySelector('.cw-empty'),mode='all';
function apply(){var s=((q&&q.value)||'').trim().toLowerCase(),n=0;all.forEach(function(c){if(c.hasAttribute('data-wait'))return;var ok=(mode==='all'||c.dataset.t===mode||(mode==='song'&&c.dataset.song))&&(!s||c.dataset.s.indexOf(s)>=0);c.hidden=!ok;if(ok)n++;});
secs.forEach(function(sec){var live=sec.querySelectorAll('.cw-card:not([data-wait])');sec.querySelector('.cw-n').textContent=live.length;sec.hidden=![].some.call(live,function(c){return !c.hidden;});});if(empty)empty.style.display=n?'none':'block';}
btns.forEach(function(b){b.addEventListener('click',function(){mode=b.dataset.f;btns.forEach(function(x){x.setAttribute('aria-pressed',x===b);});apply();});});
if(q)q.addEventListener('input',apply);
var wait=[].slice.call(r.querySelectorAll('.cw-card[data-wait]'));if(!wait.length)return;
var ids=wait.map(function(e){return e.getAttribute('data-wait');});
fetch('/wp-json/wp/v2/posts?include='+ids.join(',')+'&per_page=100&_fields=id,link,title',{credentials:'omit'}).then(function(x){return x.ok?x.json():[];}).then(function(list){
list.forEach(function(p){wait.forEach(function(c){if(+c.getAttribute('data-wait')!==p.id)return;
[].forEach.call(c.querySelectorAll('.cw-pic,h3 a'),function(a){a.href=p.link;});
[].forEach.call(c.querySelectorAll('.cw-part[data-post="'+p.id+'"]'),function(e){var a=document.createElement('a');a.className='cw-part is-on';a.href=p.link;a.innerHTML=e.innerHTML;e.parentNode.replaceChild(a,e);});
c.removeAttribute('data-wait');});});apply();}).catch(function(){});
})();"""


def render():
    n_pub = sum(1 for c in chars for r in c.get("post_rows", []) if r["status"] == "publish")
    n_people = sum(1 for c in chars if any(r["status"] == "publish" for r in c.get("post_rows", [])))
    n_song = sum(1 for c in chars if c.get("song") and any(r["status"] == "publish" for r in c.get("post_rows", [])))
    n_deep = sum(1 for c in chars if c.get("deep"))
    n_maps = len({m["link"] for c in chars for m in c.get("maps", [])})
    steps = (
        '<ol class="cw-steps">'
        '<li><b>Read</b>A short reflection, about three minutes.</li>'
        f'<li><b>Gospel Quartet</b>A gospel quartet song to remember it by. <a href="{SITE}/songs/">Songs</a></li>'
        f'<li><b>Podcast</b>The long version, 10 to 45 minutes. <a href="{DEEP_DIVES}" target="_blank" rel="noopener">Podcast</a></li>'
        '<li><b>Profile</b>Who they were, from the text itself.</li>'
        f'<li><b>Map</b>Where it happened. <a href="{SITE}/bible-maps/">Maps</a></li>'
        "</ol>"
    )
    body = (
        f'<div class="cw"><style>{CSS}.cw [hidden]{{display:none!important}}.cw-pic{{display:block}}</style>'
        f'<p class="cw-intro"><b>{SERIES}.</b> One person from the Bible at a time, told in five parts. Start with the short read, '
        'keep the song in your head, go deeper when you have time, then meet the person and see the place.</p>'
        + steps +
        '<div class="cw-bar" role="search"><button type="button" data-f="all" aria-pressed="true">All</button>'
        '<button type="button" data-f="OT" aria-pressed="false">Old Testament</button>'
        '<button type="button" data-f="NT" aria-pressed="false">New Testament</button>'
        f'<button type="button" data-f="song" aria-pressed="false">With a song ({n_song})</button>'
        '<input type="search" placeholder="Search by name or title" aria-label="Search Bible characters"></div>'
        + section("OT", "Old Testament") + section("NT", "New Testament") +
        '<p class="cw-empty">No one matches that search yet.</p>'
        f'<p class="cw-intro" style="margin-top:30px;font-size:.95em">{n_people} people · {n_pub} reflections · {n_song} songs · '
        f'{n_deep} podcast episodes · {n_maps} maps · a new story every week. <a href="{YOUTUBE}" target="_blank" rel="noopener">Songs on YouTube</a></p>'
        + script(HUB_JS) + "</div>"
    )
    return block(body)


if __name__ == "__main__":
    content = render()
    print(len(chars), "characters")
    publish("bible-characters", "Bible Characters", content,
            "Characters Worth Following: every Bible character in five parts, a short read, a gospel quartet song, a podcast episode, a profile and an interactive map.",
            "--apply" in sys.argv)
