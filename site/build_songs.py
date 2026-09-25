#!/usr/bin/env python3
"""Generate and publish the Songs page (/songs/).

  python3 site/stories.py              # picks up new songs from the YouTube channel
  python3 site/build_songs.py [--apply]

The top player is the channel's uploads playlist, so it shows new songs as soon as they are on
YouTube. The cards below come from stories.json and link each song to the rest of its story.
"""
import sys
from storykit import CSS, SERIES, SITE, UPLOADS, YOUTUBE, block, characters, chips, esc, publish, script

chars = [c for c in characters() if c.get("song")]
chars.sort(key=lambda c: c["name"].lower())

SONG_CSS = """
.cw-player{position:relative;aspect-ratio:16/9;background:#111;border-radius:6px;overflow:hidden;margin:0 0 12px}
.cw-player iframe,.cw-play img{position:absolute;inset:0;width:100%;height:100%;border:0;object-fit:cover}
.cw-play{position:relative;display:block;aspect-ratio:16/9;background:#111;cursor:pointer;border:0;padding:0;width:100%}
.cw-play::after{content:"";position:absolute;left:50%;top:50%;width:62px;height:44px;margin:-22px 0 0 -31px;border-radius:12px;background:rgba(221,51,51,.92) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23fff' d='M8 5v14l11-7z'/%3E%3C/svg%3E") center/26px no-repeat;transition:transform .15s}
.cw-play:hover::after{transform:scale(1.08)}
.cw-song{font-size:1.1em!important;font-weight:700;color:var(--ink)!important;margin:0}
"""

PLAY_JS = r"""(function(){[].slice.call(document.querySelectorAll('.cw-play')).forEach(function(b){b.addEventListener('click',function(){
var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.v+'?autoplay=1&rel=0';f.title=b.getAttribute('aria-label');
f.allow='autoplay; encrypted-media; picture-in-picture';f.allowFullscreen=true;var w=document.createElement('div');w.className='cw-player';w.style.margin='0';w.appendChild(f);b.parentNode.replaceChild(w,b);});});})();"""


def card(c):
    s = c["song"]
    rows = c.get("post_rows", [])
    return (f'<article class="cw-card" data-t="{c["t"]}" data-s="{esc((c["name"] + " " + s["title"]).lower())}">'
            f'<button type="button" class="cw-play" data-v="{esc(s["id"])}" aria-label="Play {esc(s["title"])}">'
            f'<img src="https://i.ytimg.com/vi/{esc(s["id"])}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"></button>'
            f'<div class="cw-body"><span class="cw-kicker">{esc(c["name"])}</span><p class="cw-song">{esc(s["title"])}</p>'
            + (f'<p>The song for “{esc(rows[-1]["title"])}.”</p>' if rows else "")
            + chips(c) + "</div></article>")


def render():
    body = (
        f'<div class="cw"><style>{CSS}{SONG_CSS}</style>'
        f'<p class="cw-intro">Every story in <b>{SERIES}</b> gets its own gospel quartet song. The reflection makes the point; '
        'the song makes it stick. Play one on the way to work and the story comes back to you all week.</p>'
        f'<div class="cw-player"><iframe src="https://www.youtube-nocookie.com/embed/videoseries?list={UPLOADS}&rel=0" '
        'title="Characters Worth Following: all songs" loading="lazy" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>'
        f'<div class="cw-cta"><a class="cw-btn red" href="{YOUTUBE}?sub_confirmation=1" target="_blank" rel="noopener">Subscribe on YouTube</a>'
        f'<a class="cw-btn alt" href="{SITE}/bible-characters/">All characters</a></div>'
        f'<section class="cw-sec"><h2>The songs <span>{len(chars)} so far</span></h2><div class="cw-grid">'
        + "".join(card(c) for c in chars) + "</div></section>"
        '<p class="cw-intro" style="margin-top:26px;font-size:.95em">New songs arrive with new stories. The player above always has the latest; '
        f'<a href="{YOUTUBE}" target="_blank" rel="noopener">the YouTube channel</a> has every one.</p>'
        + script(PLAY_JS) + "</div>"
    )
    return block(body)


if __name__ == "__main__":
    publish("songs", "Songs", render(),
            "Gospel quartet songs for Characters Worth Following: one song for each Bible character story, so the lesson sticks.",
            "--apply" in sys.argv)
