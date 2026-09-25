-- Dinah, in the format the Claude Project returns (one version; newer songs get two).
-- Paste into Supabase > SQL Editor after schema.sql and seed-posts.sql.
begin;
update public.songs
   set character = $t$Dinah$t$, status = 'ready', chosen_version = null,
       clips_made_at = null, clip_error = null
 where post_id = 3149;
delete from public.song_versions where post_id = 3149;
insert into public.song_versions
  (post_id, version, song_title, format, feel, style, exclude_styles, lyrics, chords, notes)
values
  (3149, 1,
   $t$Let Her Story Be Her Own$t$,
   'A',
   $t$3/4 hymn waltz, D minor to F, final chorus and tag in G, 68 BPM$t$,
   $style$Barbershop quartet, 1940s gospel quartet, close four-part male harmony, warm baritone lead, tenor lock, a cappella-style with light piano and upright bass, slow 3/4 hymn waltz, 66-70 BPM, grave tender minor-key verses, chorus opens into warm major, final chorus modulates up a whole step, reverent and dignified not triumphant, ends with a barbershop tag: ritardando, lead holds the last word while the tenor rises to a high ringing sustained note above the full chord, long fermata, clean stop$style$,
   $t$female vocals, choir, drums, synth, autotune, rap, pop$t$,
   $lyrics$[Intro: quartet hums the opening chord softly]
Mmm...

[Verse 1]
Jacob's daughter, Leah's child,
Went to see the women of the land;
Shechem, son of Hamor, took her,
And the wrong was by his hand.
Then the men began their bargains:
Marriage, trade, and title to the ground;
Every man had something wanted,
But no word of hers is found.

[Chorus: full four-part harmony]
She's a person, not a pretext,
Not a bargain to be made,
Not the fuel for someone's fury,
Not a debt that must be paid;
She is more than what was done to her,
Slow down, and listen.

[Verse 2]
Then her brothers answered Hamor
With deceit inside their terms;
While the men of Shechem lay healing,
Simeon and Levi drew their swords.
"Should he treat our sister so?"
They shot back to Jacob in their rage;
But it never let us hear her,
Not one word of hers is on the page.

[Chorus: full four-part harmony]
She's a person, not a pretext,
Not a bargain to be made,
Not the fuel for someone's fury,
Not a debt that must be paid;
She is more than what was done to her,
Slow down, and listen.

[Verse 3]
We can do the same today, friends,
When another's wound becomes our case:
Tell the details they never offered,
Let our anger take their place.
Even righteous care stops listening
When it only wants to win;
Ask her what she needs, respect it,
Let her choose where to begin.

[Bridge: softer, lead alone, quartet echoes]
The wrong was his and never hers, (never hers)
Her going out was not the cause; (not the cause)
No wedding terms could wash it over,
And no sword gave back what was lost.
Their anger named a real outrage,
But vengeance only multiplied the cost.

[Final Chorus: up a whole step, fuller, all four voices ringing]
She's a person, not a pretext,
Not a bargain to be made,
Not the fuel for someone's fury,
Not a debt that must be paid;
She is more than what was done to her,
Slow down, and listen.

[Tag: slow down, full four-part chord, lead holds the last word, tenor rises high above it and holds]
Let her story, (let her story)
Be her own, (be her own)
Let her story be her o-o-o-own.

[End: long held final chord, tenor on top, then silence]$lyrics$,
   $chords${"bpm": 68, "beats_per_bar": 3, "clips": {"reference": ["verse", "chorus"], "tag": ["tag"]}, "sections": {"verse": {"key": "D minor", "bars": ["Dm", "Dm/C", "Bb", "A7", "Dm", "Gm", "A7", "Dm"]}, "chorus": {"key": "F major", "bars": ["F", "F7", "Bb", "Bbm6", "F/C", "D7", "G7", "C7", "F", "A7", "Dm", "Bb Bbm6", "F/C C7", "F"]}, "bridge": {"key": "D minor to F major", "bars": ["Bb", "C", "Am", "Dm", "Gm7", "C7", "A7", "D7"]}, "final_chorus": {"key": "G major (up a whole step)", "bars": ["G", "G7", "C", "Cm6", "G/D", "E7", "A7", "D7", "G", "B7", "Em", "C Cm6", "G/D D7", "G"]}, "tag": {"key": "G major", "feel": "sustain", "bars": ["C", "Cm6", "G/D", "E7", "A7", "D7", "G~3"]}}}$chords$::jsonb,
   $notes$Scripture checked: Genesis 34. Format A: one clear turn (everyone speaks, bargains or takes revenge; Dinah's own voice never appears).
Tender ears: the crime is only 'took her' and 'the wrong'; Genesis 34:31's 'harlot' is paraphrased as 'Should he treat our sister so?'
Left out for length: the circumcision condition by name, removing Dinah from Shechem's house, the plunder.
Written before the two-version rule, so this post has one version.$notes$);
commit;
