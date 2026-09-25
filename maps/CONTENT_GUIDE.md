# Writing a Bible map content file

Each interactive map is one JSON file: `maps/content/<page id>.json`. The engine
(`engine.js`) and base map (`basemap.py`: real coastlines, rivers, lakes, borders and shaded
terrain) are shared, so a content file only describes the story. `content/2923.json` (Ahab)
is the reference example. Read it first.

## Standards

- **Accurate.** Every claim must be supportable from the Bible text or mainstream
  scholarship. Say "traditionally," "often identified with," or "debated" when a site is not
  certain. Never invent archaeology, dates, distances or quotes. If you are not sure of a
  fact, leave it out. The page's own text (`maps/pages/<id>.txt`) shows the author's careful
  tone: keep it, and never contradict it.
- **American English** (neighbor, center, traveled, meters shown after feet).
- **Bible references** in the form `1 Kings 18:21`. Quotes are optional, at most one per
  chapter, short (under 20 words), from the NIV, cited like `"1 Kings 18:21 (NIV)"`.
  Only quote wording you are certain of; otherwise paraphrase without quotation marks.
- **Interesting facts.** Each chapter gets 1 or 2 "Did you know?" facts: geography,
  archaeology, word meanings, distances, extra-biblical sources. They must be true and
  relevant to that chapter.
- **Readable.** Chapter text is 2 short paragraphs (`<p>` tags, 60–110 words total). Place
  card text is 2–3 sentences. Plain HTML only (`<p>`, `<em>`, `<strong>`).
- 3 to 5 chapters that follow the story in order. Tab names are 1–2 words.
- No em dashes ("—") in any prose. Use commas, colons or periods instead. En dashes in
  verse ranges (16–22) and date ranges are fine.

## Fields

```jsonc
{
 "title": "Follow Ahab between his two royal cities",  // headline over the map, sentence case
 "kicker": "Interactive map • 1 Kings 16–22",          // main passages
 "bbox": [west_lon, south_lat, east_lon, north_lat],     // map extent; padded automatically
 "anchor": "samaria",            // distances in place cards are measured from this place
 "places": {
   "id": {
     "name": "Samaria", "sub": "capital of Israel",       // sub is optional, 1–4 words
     "ll": [lat, lon],            // decimal degrees; use the best-known site coordinates
     "main": true,                // optional: the page's key place (bigger marker)
     "kind": "ref",               // optional: modern reference town (gray marker)
     "conf": "secure|probable|debated|unknown|region|modern",
     "confT": "Traditional site", // optional custom badge text
     "area": [rx_km, ry_km],      // optional: draw an approximate region instead of a point
     "elev": 482,                 // optional: meters; omit to use the terrain model value
     "text": "Place card text with references."
   }
 },
 "routes": { "id": {"pts": [[lat, lon], ...], "style": "" | "dash" | "req"} },
   // "" = solid red (a journey the text describes), "dash" = dotted (uncertain or
   // continuing off the map), "req" = brown (a request, campaign or line of travel whose
   // path is unknown). Keep routes plausible: follow valleys and known roads, and don't
   // cross the sea unless the story does.
 "labels": [ {"t": "Mediterranean Sea", "ll": [lat, lon], "kind": "water|region|river", "rot": -70, "size": 12} ],
 "chapters": [
   {"tab": "Carmel", "title": "Fire on Mount Carmel", "badge": "About 860 BC",  // badge optional
    "refs": [["1 Kings 18", "1 Kings 18"]],     // [display, Bible Gateway query]
    "hot": ["carmel", "jezreel"],               // places highlighted in this chapter
    "routes": ["elijah"], "sel": "carmel",      // routes drawn; place card shown
    "view": [w, s, e, n],                       // optional zoom for this chapter
    "html": "<p>...</p><p>...</p>",
    "quote": ["...", "1 Kings 18:21 (NIV)"],    // optional
    "facts": ["...", "..."]}
 ]
}
```

## Extent and places

- Choose a bbox that shows every place with some margin, plus enough surroundings to orient
  a reader (the coast, a sea or a lake). All places, route points and labels must be inside
  the bbox.
- For a wide map (Egypt, Babylon, Arabia), use chapter `view`s to zoom into local scenes.
- Add 1–3 modern reference towns (`"kind": "ref"`, `"conf": "modern"`), such as Jerusalem,
  Amman, Nablus, Baghdad or Cairo, when they help orientation. Don't clutter the map.
- Label seas, key lakes, rivers and regions, 4–8 labels total. Rotate labels along coasts or
  valleys when it helps. Lakes and rivers are drawn automatically; only add text labels.
- Coordinates matter: place markers on the actual tell or site. Elevations are sampled from
  the terrain at that point, so a marker off a hilltop shows a wrong height. If you know a
  site's documented elevation, set `elev`.

## Checking your work

```
python3 maps/build.py <id>          # validates, builds maps/build/<id>.preview.html
node maps/shot.js $PWD/maps/build/<id>.preview.html $PWD/maps/build/shot-<id>
```

Open the screenshots (`shot-<id>-d1.png`, `-d2.png`, `-m1.png`, `-m2.png`) and fix label
crowding, wrong extents, or routes that look wrong.
