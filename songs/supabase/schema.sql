-- Characters Worth Following songs: one row per Bible-character post in songs (post text and
-- every link: WordPress, Substack, podcast, YouTube), and two song versions per post in
-- song_versions. Paste once into Supabase > SQL Editor and run. Safe to run again.
-- The SQL Editor splits scripts at every semicolon, even inside quotes, so no quoted text here
-- (or in any SQL for this project) may contain one.
--
-- songs.status flow:
--   waiting      post text loaded, no song yet (seed-posts.sql)
--   ready        two versions pasted in from the Claude Project, n8n will make the chord clips
--   clips_ready  n8n rendered the clips, stored them in the song-clips bucket and emailed Steve
--   needs_fix    n8n couldnt render the chords (see clip_error), paste corrected SQL
--   generated    candidates made in Suno (set chosen_version, fill candidate_urls)
--   picked       Steve chose the winner (fill winner_url)
--   downloaded   winner downloaded (uses one of the monthly Suno downloads)
--   done_before  song made before this pipeline existed
--   skip         no song for this post

create table if not exists public.songs (
  post_id          bigint primary key,
  post_title       text not null,
  slug             text,
  post_text        text,                 -- plain text of the post: the only story source
  publish_date     timestamptz,
  post_status      text,                 -- WordPress status when loaded: publish or future
  priority         integer,              -- lower numbers get songs first
  -- Links (never given to Claude). Filled once each is live, the loader never erases one.
  wordpress_url    text,                 -- the live post on stevesammons.com
  substack_url     text,                 -- the matching live Substack post
  podcast_url      text,                 -- the Substack podcast episode about this post
  podcast_title    text,
  youtube_url      text,                 -- the songs YouTube video
  character        text,
  status           text not null default 'waiting' check (status in
                     ('waiting','ready','clips_ready','needs_fix','generated','picked',
                      'downloaded','done_before','skip')),
  chosen_version   smallint,             -- which version Steve took to Suno
  clips_made_at    timestamptz,
  clip_error       text,
  candidate_urls   text[],
  winner_url       text,
  credits_used     integer,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- Upgrades a songs table made by an earlier version of this file.
alter table public.songs add column if not exists slug text;
alter table public.songs add column if not exists wordpress_url text;
alter table public.songs add column if not exists substack_url text;
alter table public.songs add column if not exists podcast_url text;
alter table public.songs add column if not exists podcast_title text;
alter table public.songs add column if not exists youtube_url text;
alter table public.songs drop column if exists post_url;

create table if not exists public.song_versions (
  post_id          bigint not null references public.songs (post_id) on delete cascade,
  version          smallint not null check (version between 1 and 9),
  song_title       text not null,
  format           text,                 -- A (sung ballad) or B (talking story)
  feel             text,                 -- meter, key, tempo, e.g. 3/4 hymn waltz, D minor to F, 68 BPM
  style            text not null,        -- Suno Styles box
  exclude_styles   text,                 -- Suno More Options > Exclude styles
  lyrics           text not null,        -- Suno Lyrics box
  chords           jsonb not null,       -- chord chart, same format as songs/<character>/chords.json
  notes            text,                 -- scripture checked, audit, anything Steve should check
  reference_clip   text generated always as (post_id || '/v' || version || '-chords-reference.wav') stored,
  tag_clip         text generated always as (post_id || '/v' || version || '-chords-tag.wav') stored,
  created_at       timestamptz not null default now(),
  primary key (post_id, version)
);

create index if not exists songs_status_priority on public.songs (status, priority);

-- Keep updated_at current (Supabases moddatetime extension, no function body to paste).
create extension if not exists moddatetime schema extensions;
drop trigger if exists songs_touch on public.songs;
create trigger songs_touch before update on public.songs
  for each row execute procedure extensions.moddatetime(updated_at);

-- Only the dashboard and the service-role key (n8n) can read or write.
alter table public.songs enable row level security;
alter table public.song_versions enable row level security;

-- The next posts to write songs for. Copy chat_prompt into the Claude Project.
create or replace view public.next_songs with (security_invoker = on) as
select post_id,
       post_title,
       publish_date::date as publish_date,
       'Post ID: ' || post_id || E'\n'
         || 'Title: ' || post_title || E'\n'
         || 'Publishes: ' || coalesce(publish_date::date::text, 'unknown') || E'\n\n'
         || coalesce(post_text, '') as chat_prompt
from public.songs
where status = 'waiting'
order by priority;

-- Every post with its links, newest first.
create or replace view public.post_links with (security_invoker = on) as
select post_id, character, post_title, publish_date::date as publish_date, post_status, status,
       wordpress_url, substack_url, podcast_url, youtube_url
from public.songs
order by publish_date desc;

-- What n8n picks up: every version of every song marked ready.
create or replace view public.clips_queue with (security_invoker = on) as
select v.post_id, s.post_title, s.character, v.version, v.song_title, v.format, v.feel,
       v.style, v.exclude_styles, v.lyrics, v.chords, v.notes, v.reference_clip, v.tag_clip
from public.song_versions v
join public.songs s using (post_id)
where s.status = 'ready'
order by s.priority, v.post_id, v.version;

-- Private bucket for the chord clips (n8n uploads with the service-role key).
insert into storage.buckets (id, name, public)
values ('song-clips', 'song-clips', false)
on conflict (id) do nothing;
