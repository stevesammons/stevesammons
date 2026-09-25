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
- Menu items can't be created through the REST API (a theme or plugin hook on
  `wp_update_nav_menu_item` demands an admin nonce and aborts with "link expired"). Deleting works.
  Build menus with a single-use Code Snippets snippet that calls `remove_all_actions(
  'wp_update_nav_menu_item' )` first (see `site/menu-snippet.php`).
- The sammons-social-tags plugin outputs Open Graph tags and switches itself off when an SEO
  plugin such as Rank Math is active. Rank Math can't be configured without its admin wizard,
  so SEO is handled by our own snippet instead (below). Don't install another SEO plugin.

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

## Site structure (reorganized 2026-09-25)

- Categories: Bible Characters > Old Testament / New Testament (every Bible character post, and
  only those), Leadership > Character & Integrity, Faith & Spiritual Living, Marketing & Branding
  > SEO / Advertising / LinkedIn / UI/UX Design / Technology, Publishing, Nonprofits & Education >
  Fundraising / Higher Education / Children's Literacy. Default category: Leadership.
  New Bible character posts go only in Old Testament or New Testament.
- Primary menu (id 14, also mobile): Bible Characters (OT, NT, Bible Maps), Leadership
  (Character & Integrity), Faith, Marketing (Publishing, Nonprofits & Education), About, Newsletter.
- Hub: /bible-characters/ built by `python3 site/build_hub.py --apply` from
  `backups/hub-chars.json`. Rebuild it when a character post is added (the approval for the post
  covers it). Scheduled reflections link themselves in the browser once they publish.
- About page: /about/ (source `site/about.html`). /stevesammons/ redirects there.

## Code Snippets on the site (Code Snippets plugin, REST at /code-snippets/v1/snippets)

- SEO essentials (id in `seo/snippet-id.txt`, source `seo/seo-snippet.php`, front-end scope):
  meta descriptions from excerpts, JSON-LD (Person, WebSite, BlogPosting, WebPage, BreadcrumbList),
  noindex for tag archives with fewer than 3 posts and for date/author/search pages, sitemap
  cleanup, homepage H1 and share image, readable-contrast CSS, /stevesammons/ redirect.
- Keep reading (id in `seo/related-snippet-id.txt`, source `seo/related-snippet.php`): 4 related
  published posts after each post, cached 12 hours.
- Always `php -l` a snippet before uploading, keep scope `front-end` unless it must run in admin,
  and verify the live site returns 200 right after activating. Edit the source file, then push the
  code with POST /code-snippets/v1/snippets/<id> {"code": ...}.
- `.htaccess` has an `SS Browser Caching` marker block (30-day browser caching for static files);
  the server keeps `.htaccess.ss-backup-*` copies. Test any new server rules in a sandbox folder
  first, since a bad rule takes down the site and the API with it.

## Content conventions

- Every post and map page needs a hand-written excerpt (about 150 characters). It is the search and
  social description.
- Every post needs a featured image. Posts without one get a branded card from
  `python3 site/cards.py apply` (Poppins fonts in site/fonts, downloaded from google/fonts).
