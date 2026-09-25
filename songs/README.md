# Quartet song pipeline

Claude writes each song in a claude.ai Project (your subscription, no API). Supabase keeps
track of every post. n8n turns each new song into chord clips and emails it to you, ready to
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
In **SQL Editor**, run these files in order (each is safe to run again):
1. `supabase/schema.sql`: the `songs` table, the `next_songs` view and the private `song-clips` bucket.
2. `supabase/seed-posts.sql`: all 98 Bible-character posts (52 scheduled, 46 published). The 6
   songs made earlier are marked `done_before`.
3. `supabase/dinah.sql`: the Dinah song, which makes a good first test of n8n.

`seed-posts.sql` is about 300 KB. If the editor struggles, split it in half; each post is one
statement. To refresh it after new posts are scheduled: `python3 songs/supabase/export_posts.py`.

### 2. Claude Project
In claude.ai, create a Project called **Quartet Songs** and paste everything below the line in
`claude-project-instructions.md` into its Instructions.

### 3. n8n
1. **Workflows > Import from File**, and choose `n8n/song-clips-workflow.json`.
2. Open the **Settings** node. Set `supabase_url` (Supabase > Project Settings > API > Project URL)
   and `notify_email`.
3. Credentials:
   - **Supabase API** (Host = the project URL, Service Role Secret = the `service_role` key) on
     the three Supabase nodes and both **Upload** nodes (Authentication is already set to the
     Supabase credential type).
   - **Gmail OAuth2** on both email nodes.
4. Click **Execute workflow**. Dinah should arrive in your inbox with two WAV files, and her row
   should switch to `clips_ready`. Then turn the workflow **Active**.

The workflow is plain n8n nodes plus one Code node, with nothing to install. If you change the
renderer, run `python3 songs/n8n/build_workflow.py` and re-import.

## Making a song (a few minutes each)

1. In Supabase, open **next_songs** and copy the top row's `chat_prompt` cell.
2. Start a new chat in the Quartet Songs project and paste it.
3. Read the lyrics. If you like them, copy the SQL block into the Supabase SQL Editor and run it.
   Want changes? Ask in the same chat for a revised SQL block, then run that instead.
4. Within 5 minutes you get the email: paste Title, Styles and Lyrics into Suno (Create >
   Advanced), upload the reference clip, and click Create.
5. Update the row as you go: `generated` (add `candidate_urls`), then `picked` (`winner_url`),
   then `downloaded`.

## Statuses

| status | meaning |
|---|---|
| waiting | no song yet |
| ready | song pasted in; n8n will make the clips |
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
| `supabase/schema.sql`, `seed-posts.sql`, `dinah.sql` | database setup and data |
| `supabase/export_posts.py` | rebuilds `seed-posts.sql` from WordPress |
| `n8n/render-clips.js` | chord chart to WAV (JavaScript, used inside n8n) |
| `n8n/build_workflow.py`, `song-clips-workflow.json` | the n8n workflow and its builder |
| `render_chords.py` | the same renderer in Python, plus MIDI files, for local use |
| `dinah/` | the first song package |
