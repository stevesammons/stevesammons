# Hebron in Caleb's Story: interactive map

This replaces the static orientation map on
https://stevesammons.com/hebron-in-calebs-story/.

## Install on WordPress

1. Edit the page and select the old map (the `<figure>` with the grey grid and the JERUSALEM/HEBRON boxes). Delete it.
2. Add a **Custom HTML** block in its place.
3. Paste the entire contents of `embed.html` into it, then Update.

All CSS is scoped to `#chm` and the script runs once, so the widget won't affect the theme.
You need an administrator account (WordPress's `unfiltered_html` capability) for the
`<script>` and `<style>` tags to be saved.

## What it does

- Six story chapters (Numbers 13–14; Joshua 14–15), each highlighting the places and routes involved:
  the scouts sent out from Kadesh, Hebron and the Anakites, the two reports, Caleb's request at Gilgal at 85,
  the taking of Hebron, and Debir, Othniel and Achsah.
- Click or tab to any place for an info card with its scripture context and how certain its identification is
  (secure, probable, debated, or a modern reference point).
- Elevation profiles for the two "going up" moments (Kadesh to Hebron, Gilgal to Hebron).
- Toggles for modern reference points and terrain regions, a scale bar, and a north arrow.
- Every reference links to Bible Gateway (NIV). Works with a keyboard, respects reduced-motion settings and fits phone widths.

`preview.html` wraps the embed in a plain page for viewing it locally.

## Publishing automatically

`publish.py` updates page 3169 via the WordPress REST API. It reads `WP_USER` and
`WP_APP_PASSWORD` from the environment and never prints them. Before changing anything it
backs up the page's current content to `backups/`, which is git-ignored.

```
python3 hebron-map/publish.py          # dry run
python3 hebron-map/publish.py --apply  # publish
```

It replaces only the old map `<figure>`, between `<!-- chm:start -->` and `<!-- chm:end -->`
markers, so re-running it after editing `embed.html` updates the map in place.
