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
  Build menus with a Code Snippets snippet that calls `remove_all_actions(
  'wp_update_nav_menu_item' )` first (see `site/menu-snippet.php`). Activating a single-use snippet over
  REST does not run it: wrap the code in a run-once `get_option`/`update_option` guard, save it with scope
  `global` and active, load one page, then deactivate it and set it back to single-use.
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
- Primary menu (id 14, also mobile), rebuilt 2026-09-25 by `site/menu-snippet.php`: Characters (/bible-characters/), Songs (/songs/),
  Maps (/bible-maps/), Deep Dives (sammons.substack.com/podcast, new tab), About, Subscribe (/subscribe/,
  menu item class `ss-menu-subscribe`, styled as a red button by the `ss-header` CSS in the SEO snippet).
  Non-Bible topics live in the footer's "More writing" column, not the header.
- The header's duplicate top bar (repeated menu and empty social icons) is hidden by the `ss-header` CSS.
- Series name: **Characters Worth Following** (same as the YouTube channel). Each character has five
  parts: 1 Read (short post), 2 Listen (gospel quartet song, YouTube @CharactersWorthFollowing),
  3 Deep dive (Substack podcast episode, sammons.substack.com/podcast), 4 Profile page, 5 Map page.
  Posts go in the RSS feed; profiles and maps are pages and must stay pages.
- Story data: `site/stories.json` (committed), refreshed by `python3 site/stories.py`. It attaches new
  posts via the profile page they link to and matches new songs and deep dives by character name; it
  prints anything UNASSIGNED/UNMATCHED to fix by hand. Then rebuild what changed:
  `python3 site/build_hub.py --apply` (/bible-characters/), `site/build_songs.py --apply` (/songs/, 3947),
  `site/build_maps.py --apply` (/bible-maps/, 3948, lists seo/map-pages.json), and
  `site/story_strip.py --apply` (the five-part component on each character post: Code Snippet
  id in `site/story-strip-snippet-id.txt`, the_content priority 15, skipped in feeds). Approval for a new
  character post covers all of these.
- Five-part component on posts (rebuilt 2026-09-25, source `site/story_strip.py`, `story-strip.css`,
  `story-strip.js`): parts are Read, Gospel Quartet, Podcast, Profile, Map (Steve renamed Listen and
  Deep dive). A bar under the title with icons, hover titles and a ? panel; up to two cards in the text
  (song or podcast about 40% in; map after the first paragraph naming a place from its title, else
  profile about 70% in); a box at the end. Missing parts are light grey "Coming soon". Gospel Quartet
  opens a popup YouTube player and Podcast a popup audio player (free Substack episodes; `stories.py`
  saves each episode's `audio` URL). The CSS is printed in wp_head: a `<style>` at the start of the
  post content gets stripped along with whatever follows it.
- Subscribing: new subscribers go to Substack via /subscribe/ (1423, `site/build_subscribe.py`). The
  existing MailPoet list (about 8,000) keeps getting email; don't touch it. The footer MailPoet form
  (mailpoet_form-2) was moved to Inactive widgets on 2026-09-25. /newsletter/ (1464) holds the
  Newsletter plugin's [newsletter] shortcode for existing subscribers; leave it.
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
- More than one Claude session works on this site, each on its own `claude/*` branch. Before pushing
  a snippet or rebuilding a generated page, `git fetch` and merge any other `claude/*` branch that
  touches the same files, and compare the live snippet code with your source file. If the live code
  has changes your file lacks, merge them first; pushing a stale file silently undoes the other
  session's work (on 2026-09-25 this dropped the merged-post redirects until they were restored).
- `.htaccess` has an `SS Browser Caching` marker block (30-day browser caching for static files);
  the server keeps `.htaccess.ss-backup-*` copies. Test any new server rules in a sandbox folder
  first, since a bad rule takes down the site and the API with it.

## Content conventions

- Every post and map page needs a hand-written excerpt (about 150 characters). It is the search and
  social description.
- Every post needs a featured image. Posts without one get a branded card from
  `python3 site/cards.py apply` (Poppins fonts in site/fonts, downloaded from google/fonts).

## Featured image design (the house style, confirmed by Steve 2026-09-25)

Two kinds of featured image, both 16:9, black and white with one red accent:

1. **Bible character posts**: the character portrait (imagined, black-and-white documentary
   photo style) with the name in white bold caps top left, a short line under it, and a thin red
   vertical bar to the left of the text. These come from Steve's own artwork; don't replace them.
2. **Everything else (leadership, faith, marketing, publishing, nonprofits), and any Bible post
   without a portrait**: a typographic card made by `site/cards.py`, never a stock or AI
   illustration. Spec:
   - 1600x900 JPEG (quality 84, progressive). Background near black with a soft off-center light
     pool (about #3a3a3a fading to #080808 at the edges) and fine film grain.
   - Red bar #dd3333, 18 px wide, left of the text block, spanning its full height.
   - Headline: Poppins Bold, white, ALL CAPS, left aligned at x=150, vertically centered, 1 to 3
     lines, sized 150 px down to 70 px to fit. Non-Bible posts: the post title. Bible posts: the
     character's name.
   - Subtitle (Bible posts only): the post title in Poppins SemiBold caps, light gray, up to 2 lines.
   - Footer line: "STEVE SAMMONS" bottom left and the category name bottom right, Poppins Medium
     26 px caps, gray.
   - Alt text: the headline (plus subtitle).
   To swap a post's image for a card: `python3 site/cards.py one POST_ID`. It backs up the old
   image id to backups/ and leaves the old image in the media library.

## Footer (redesigned 2026-09-25)

- Widgets (edit through /wp/v2/widgets): sidebar-footer = block-13 (brand, `site/footer/col1.html`),
  sidebar-footer-2 = block-12 (Explore and Topics links, `col2.html`), sidebar-footer-3 = block-14
  (newsletter heading, `col3.html`) followed by mailpoet_form-2. Styling is the `ss-footer` CSS in
  the SEO snippet. Deleting a widget can push others into Inactive widgets, so re-check the
  sidebars after any change.
- Bottom bar: theme mod `footer_text` (copyright with Privacy Policy, About, Newsletter links) and
  the Social menu (id 333: Facebook, X, LinkedIn). Set both with a single-use snippet
  (`site/footer/theme-snippet.php`). Update the year each January.
- Fonts: only Poppins (headings) and Lato (body). The MailPoet form defaults to Montserrat and is
  overridden in the footer CSS.
