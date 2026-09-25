# stevesammons.com

Self-hosted WordPress on Apache (Csco theme, Wordfence, ModSecurity, Site Kit, MailPoet).
This repo holds code that gets published to the site. The site itself is managed through
its REST API as the `claude` administrator.

## Access

- Run `python3 tools/wp.py check` at the start of any WordPress work.
- Credentials come only from the `WP_USER` and `WP_APP_PASSWORD` environment variables.
  Never print, log, echo or commit them, and never ask for them in chat.
- If `check` reports "not logged in", Wordfence's "Disable WordPress application passwords"
  option (Wordfence > All Options > Brute Force Protection) may have been re-enabled.

## Ground rules

Ask first, and wait for a clear yes, before anything readers would see or that is hard to undo:
- publishing, unpublishing, scheduling or deleting posts and pages
- sending or scheduling MailPoet emails or newsletters
- installing, activating, deactivating, updating or deleting plugins or themes
- creating, changing or deleting users, roles or Application Passwords
- changing site settings, menus, permalinks, Wordfence or other security settings
- deleting media or comments

Allowed without asking: reading anything, creating or editing drafts, and checking live pages.

Always:
- Before editing existing content, save its `content.raw` (`?context=edit`) to `backups/`
  (git-ignored) so it can be restored.
- After publishing, load the live page and confirm it renders.
- Report what changed with links. If something failed, say so.

## Site quirks

- The site's content filters add `<p>` tags and curly quotes inside inline `<script>` blocks.
  Ship scripts as base64 `data:` URIs, as `hebron-map/publish.py` does.
- ModSecurity rejects requests with a bare or unusual User-Agent. Send a real one.
- Use the block editor. Put custom HTML inside a `<!-- wp:html -->` block.

## Known pages

- 3169 Hebron in Caleb's Story. Interactive map in `hebron-map/`, publish with
  `python3 hebron-map/publish.py --apply`.
- /caleb/ Caleb profile. /give-me-the-hard-one/ reflection.

## Back-to-the-story links

Reference pages (character profiles and place maps) get a "Back to the story" card at the top
and bottom via `python3 backlinks/apply.py PAGE_ID POST_IDS SUBJECT --apply`. It only links
posts that are already published, so scheduled posts appear automatically on their publish date.
Done so far: 2903 Ahab (post 2943).

## YouTube videos play on the page

YouTube links (name pronunciations, the "Hear the gospel quartet" song card, other video links)
open in an on-page lightbox instead of sending readers to YouTube. Add it to a post or page with
`python3 video-popup/apply.py ID [ID ...] --apply` (posts or pages; only the content changes, so
scheduled posts keep their date). Links stay unchanged and still work without JavaScript.
Re-running replaces the old copy, so after editing `lightbox.js` re-run it on every ID below.

- Done (2026-09-25): posts 2627, 278, 1282, 1854, 1907; pages 2710 Jochebed, 2648 Nabal,
  2619 Ahithophel, 3133 Jael; scheduled posts 2642, 2656, 2718, 3145.
- Not needed: posts that use WordPress YouTube embed blocks already play on the page
  (294, 376, 331, 1048, 308, 1794).
- New posts or character pages with YouTube links need it too. To find them, search every status
  of posts and pages for `youtube.com/watch`, `youtu.be/` or `shorts/` links without the
  `ss-video:start` marker.

## Podcast plays on the page

"Listen to the podcast" cards (links to sammons.substack.com/p/<slug>) turn into an on-page
audio player: play/pause, seek, back/forward 15s, speed, "Open on Substack", resume where the
reader stopped, lock-screen controls, and a mini bar at the bottom of the screen while it plays.
`python3 podcast-player/apply.py --all --apply` looks each episode up on Substack
(`/api/v1/posts/<slug>`) and writes the public ones into the post with `player.js`. Links to
episodes that aren't out yet stay plain links. It only saves a post when its player block changes
and never touches status or schedule. Run it again after editing `player.js`.

- Done (2026-09-25): posts 2627, 1907, 1854, scheduled post 2642.
- Waiting on Substack: 2656 (the-help-we-forget), 2698 (can-their-good-news-stay-theirs).
- No automatic refresh yet: a twice-daily Routine for `--all --apply` was blocked by the session's
  permission settings on 2026-09-25. Until one is set up, re-run it by hand when an episode goes
  out on Substack or a post with a podcast link is added.
- Audio `src` is the episode's `podcast_url` (api.substack.com/api/v1/audio/upload/<id>/src). It
  redirects to a fresh signed CDN file each time, so it doesn't expire. Browsers can't call the
  Substack API from the site (no CORS), which is why the lookup happens at publish time.
- Paid-only episodes can't play here and keep their Substack link.

## Checking pages from the cloud sandbox

- Headless Chromium needs the proxy and its CA. Launch Playwright with
  `executablePath: '/opt/pw-browsers/chromium'`, `proxy: {server: process.env.HTTPS_PROXY}` and
  `--ignore-certificate-errors-spki-list=<sha256 of /root/.ccr/agent-proxy-ca.crt public key>`.
- YouTube blocks playback of most videos from the sandbox ("Video unavailable", watch pages 403),
  even for plain WordPress embeds. That is the sandbox, not the site. Check the player opens and
  ask the user to confirm playback on a real device. Substack podcast audio does play from the sandbox.
- Known issue, not yet fixed: on phones, /the-art-of-quiet-change/ scrolls sideways because a long
  Wikipedia URL in its footnotes does not wrap.
