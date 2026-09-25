-- Suno song pipeline: one row per Bible-character post.
-- Paste once into Supabase > SQL Editor and run. Safe to run again.
--
-- status flow:
--   waiting      post loaded, no song yet (seed-posts.sql)
--   ready        song SQL pasted in from the Claude Project; n8n will make the chord clips
--   clips_ready  n8n rendered the clips, stored them in the song-clips bucket and emailed Steve
--   generated    candidates made in Suno (fill candidate_urls)
--   picked       Steve chose the winner (fill winner_url)
--   downloaded   winner downloaded (uses one of the monthly Suno downloads)
--   done_before  song made before this pipeline existed
--   skip         no song for this post
--   needs_fix    n8n couldn't render the chords (see clip_error); paste a corrected song SQL

create table if not exists public.songs (
  post_id          bigint primary key,
  post_title       text not null,
  post_url         text,
  substack_url     text,
  publish_date     timestamptz,
  post_status      text,                 -- WordPress status when loaded: publish or future
  post_text        text,                 -- plain text of the post, for the Claude Project chat
  priority         integer,              -- lower numbers get songs first
  character        text,
  song_title       text,
  format           text,                 -- A (sung ballad) or B (talking story)
  style            text,                 -- Suno Styles box
  exclude_styles   text,                 -- Suno More Options > Exclude styles
  lyrics           text,                 -- Suno Lyrics box
  chords           jsonb,                -- chord chart, same format as songs/<character>/chords.json
  notes            text,                 -- format rationale, audit, anything Steve should check
  status           text not null default 'waiting' check (status in
                     ('waiting','ready','clips_ready','needs_fix','generated','picked','downloaded','done_before','skip')),
  reference_clip   text,                 -- storage path of chords-reference.wav
  tag_clip         text,                 -- storage path of chords-tag.wav
  clips_made_at    timestamptz,
  clip_error       text,
  candidate_urls   text[],
  winner_url       text,
  credits_used     integer,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create index if not exists songs_status_priority on public.songs (status, priority);

create or replace function public.songs_touch() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists songs_touch on public.songs;
create trigger songs_touch before update on public.songs
  for each row execute function public.songs_touch();

-- Only the dashboard and the service-role key (n8n) can read or write songs.
alter table public.songs enable row level security;

-- The next posts to write songs for, with everything the Claude Project chat needs in one cell.
create or replace view public.next_songs with (security_invoker = on) as
select post_id,
       post_title,
       publish_date::date as publish_date,
       'Post ' || post_id || ': ' || post_title || E'\n'
         || 'WordPress: ' || coalesce(post_url, '') || E'\n'
         || 'Substack: ' || coalesce(substack_url, '') || E'\n'
         || 'Publishes: ' || coalesce(publish_date::date::text, '') || E'\n\n'
         || coalesce(post_text, '') as chat_prompt
from public.songs
where status = 'waiting'
order by priority;

-- Private bucket for the chord clips (n8n uploads with the service-role key).
insert into storage.buckets (id, name, public)
values ('song-clips', 'song-clips', false)
on conflict (id) do nothing;
