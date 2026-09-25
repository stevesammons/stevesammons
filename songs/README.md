# Quartet song pipeline

One song for every Bible-character post (posts only, never pages). Claude writes two versions
of each song in a claude.ai Project (your subscription, no API), working only from the post's
text, which is stored in Supabase, plus Scripture it checks by web search. Supabase keeps track of every
post and both versions. n8n turns each new song into chord clips and emails it to you, ready to
paste into Suno.

```
next_songs view ──copy──▶ Claude Project ──SQL──▶ Supabase (status 'ready')
                                                      │  n8n checks every 5 minutes
                                                      ▼
                            email with lyrics + clips ◀── n8n renders WAVs, stores them
                                                      ▼
                         you: paste into Suno, pick the winner, update the row
```

## One-time setup (about 20 minutes)

### 1. Supabase
In **SQL Editor**, run these files in order, one at a time (each is safe to run again):
1. `supabase/schema.sql`: the `songs` table (one row per post: its text plus the WordPress,
   Substack, podcast and YouTube links), `song_versions` (two versions per song), the
   `next_songs`, `post_links` and `clips_queue` views, and the private `song-clips` bucket. It
   also upgrades a `songs` table made by an earlier version of this file.
2. `supabase/seed-posts-1-of-5.sql` through `seed-posts-5-of-5.sql`: all 98 Bible-character posts
   (52 scheduled, 46 published) with their text and every live link. The 6 songs made earlier
   are marked `done_before`.
3. `supabase/dinah.sql`: the Dinah song (one version), which makes a good first test of n8n.

Every file stays under 100 lines (each post's insert is one line) because some file viewers only
copy the first 100 lines, and no quoted value contains a semicolon, because the SQL Editor can
split scripts at semicolons. Semicolons and line breaks in post text are stored as placeholders
that `replace(... chr(59))` and `chr(10)` put back. After loading, `select count(*) from songs`
should say 98.
To refresh posts and links as more go live: `python3 songs/supabase/export_posts.py`, then run
the new seed files. It fills in links and never erases a link, song or status you've set.

### 2. Claude Project
1. In claude.ai, create a Project called **Quartet Songs** and paste everything below the line in
   `claude-project-instructions.md` into its Instructions.
2. Add the Supabase connector: claude.ai **Settings > Connectors > Add custom connector**, URL
   `https://mcp.supabase.com/mcp?project_ref=YOUR-PROJECT-REF` (the ref is in your Supabase project
   URL). Sign in to Supabase when asked. Leave read-only off, so the Project can save songs.
3. In a Project chat, turn on web search and the Supabase connector.

Then just talk to it: "Let's do the next one", "Let's do Balaam", "Let's finish the scheduled
posts", "What's left?", and "Save it" once you like both versions.

### 3. n8n
1. **Workflows > Import from File**, and choose `n8n/song-clips-workflow.json`.
2. Open the **Settings** node. Set `supabase_url` (Supabase > Project Settings > API > Project URL)
   and `notify_email`.
3. Credentials:
   - **Supabase API** (Host = the project URL, Service Role Secret = the `service_role` key) on
     the three Supabase nodes and the **Upload clip** node (its Authentication is already set to
     the Supabase credential type).
   - **Gmail OAuth2** on both email nodes.
4. Click **Execute workflow**. Dinah should arrive in your inbox with two WAV files, and her row
   should switch to `clips_ready`. Then turn the workflow **Active**.

The workflow is plain n8n nodes plus one Code node, with nothing to install. If you change the
renderer, run `python3 songs/n8n/build_workflow.py` and re-import.

## Making a song (a few minutes each)

1. In a Quartet Songs chat, say "Let's do the next one" (or name a character).
2. Claude shows two versions. Ask for changes, or say "Save it" and it stores both in Supabase.
   (Without the connector: copy `chat_prompt` from `next_songs` into the chat, then run the SQL it
   returns in the Supabase SQL Editor.)
3. Within 5 minutes you get one email with both versions and four clips (`v1-...` and `v2-...`).
   Pick a version, paste its Title, Styles and Lyrics into Suno (Create > Advanced), upload that
   version's reference clip, and click Create.
4. Update the row as you go: set `chosen_version` and `generated` (add `candidate_urls`), then
   `picked` (`winner_url`), then `downloaded`.

## Statuses

| status | meaning |
|---|---|
| waiting | no song yet |
| ready | both versions pasted in; n8n will make the clips |
| clips_ready | clips made and emailed |
| needs_fix | chords couldn't be rendered (see `clip_error`); ask the Project for corrected SQL |
| generated / picked / downloaded | your progress in Suno |
| done_before | made before this pipeline |
| skip | no song for this post |

## Budget

Suno Pro: 2,500 credits and about 20 downloads a month. A Create run makes two candidates for
about 10 credits, so downloads are the real limit: roughly 5 finished songs a week.

## Files

| file | what |
|---|---|
| `claude-project-instructions.md` | the Project prompt: song rules, tender ears, big finish, chords, SQL format |
| `supabase/schema.sql`, `seed-posts-*.sql`, `dinah.sql` | database setup and data |
| `supabase/export_posts.py` | rebuilds the seed files from WordPress and the Substack archive |
| `n8n/render-clips.js` | chord chart to WAV (JavaScript, used inside n8n) |
| `n8n/build_workflow.py`, `song-clips-workflow.json` | the n8n workflow and its builder |
| `render_chords.py` | the same renderer in Python, plus MIDI files, for local use |
| `dinah/` | the first song package |
