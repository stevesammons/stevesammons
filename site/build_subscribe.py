#!/usr/bin/env python3
"""Generate and publish the Subscribe page (/subscribe/). New subscribers sign up on Substack.

  python3 site/build_subscribe.py [--apply]

The existing MailPoet list is untouched; this only changes where new readers sign up.
"""
import sys
from storykit import CSS, DEEP_DIVES, SERIES, SITE, SUBSCRIBE, SUBSTACK, YOUTUBE, block, publish, script

SUB_CSS = """
.cw-sub{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:28px;align-items:start}
.cw-sub iframe{width:100%;height:320px;border:1px solid var(--line);border-radius:6px;background:#fff}
.cw-sub ul{margin:0 0 18px;padding-left:1.1em}
.cw-sub li{margin:0 0 8px;line-height:1.5}
.cw-note{font-size:.9em;color:var(--muted)}
@media (max-width:760px){.cw-sub{grid-template-columns:1fr}}
"""


def render():
    body = (
        f'<div class="cw"><style>{CSS}{SUB_CSS}</style>'
        f'<p class="cw-intro"><b>{SERIES}</b> arrives by email once a week: one person from the Bible and one lesson worth keeping. '
        'It is free, and you can unsubscribe any time.</p>'
        '<div class="cw-sub"><div><ul>'
        '<li><b>The short read</b>, about three minutes, every week.</li>'
        f'<li><b>The song</b>: a gospel quartet tune for the story. <a href="{SITE}/songs/">Hear them</a></li>'
        f'<li><b>The deep dive</b>: the long version, 10 to 45 minutes, to listen to on a walk or a drive. <a href="{DEEP_DIVES}" target="_blank" rel="noopener">Browse deep dives</a></li>'
        f'<li><b>Profiles and maps</b> for every character. <a href="{SITE}/bible-characters/">See them all</a></li>'
        '</ul>'
        f'<p class="cw-note">Sign-up is handled by Substack. Prefer to do it there? <a href="{SUBSCRIBE}" target="_blank" rel="noopener">Subscribe on Substack</a>. '
        'Already getting the weekly email from this site? You don’t need to do anything; it keeps coming.</p></div>'
        f'<iframe src="{SUBSTACK}/embed" title="Subscribe to {SERIES} on Substack" loading="lazy" scrolling="no"></iframe></div>'
        f'<p class="cw-note" style="margin-top:22px">Songs are also on <a href="{YOUTUBE}" target="_blank" rel="noopener">YouTube</a>.</p>'
        + script("void 0;") + "</div>"
    )
    return block(body)


if __name__ == "__main__":
    publish("subscribe", "Subscribe", render(),
            "Get Characters Worth Following by email: a short Bible character reflection each week, plus songs, deep dives, profiles and maps. Free.",
            "--apply" in sys.argv)
