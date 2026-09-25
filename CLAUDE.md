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
- Keep "Back to the story" links complete. Whenever a Bible character post (tag "Bible
  character" or "Bible characters") is created, edited, scheduled or published, or a reference
  page it links to is created, run `python3 backlinks/scan.py` then
  `python3 backlinks/apply_all.py`, and report any page that fails. The user's approval for
  that post covers updating its reference pages. Any other page that links readers to a
  reference page on this site should get the same back link. Ask before extending it to other
  tags or posts.

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
All 50 reference pages linked from the 25 posts tagged "Bible character" / "Bible characters"
were done on 2026-09-25. For new posts or links: `python3 backlinks/scan.py` (rebuilds
`backups/backlink-map.json`), then `python3 backlinks/apply_all.py` (idempotent; re-publishes
only pages whose back links changed, and checks each live page).

- Pages come in three layouts: a Custom HTML block wrapping one div, the same with a stray
  `<meta charset>` before it, and classic-editor HTML wrapped in one div (e.g. Nob in Doeg's
  Story). `apply.py` handles all three. Never add block markup to a classic page.
- The tag is split into "Bible character" (1716) and "Bible characters" (1676). Scan both.
- Not yet covered: "Give Me the Hard One" (untagged Caleb post) and its Caleb and Hebron pages.

## Bible map pages: tags and descriptions

- Pages can have tags and categories via the "Pages with category and tag" plugin
  (installed 2026-09-25 at the user's request).
- Every page with a Bible map carries "Bible Map", "Map of the Bible", "Biblical Geography"
  and "Bible Places", plus tags for its characters, places, books and testament, reusing
  existing tag names. It also gets a hand-written excerpt (about 160 characters), which the
  theme uses as the page's search and social description. Don't overwrite an existing excerpt.
- The data lives in `seo/map-pages.json` and is applied with `python3 seo/apply_tags.py`.
  When a new map page is created, add an entry and run it (the user's approval for the page
  covers its tags and excerpt).
