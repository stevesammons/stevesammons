# Let Her Story Be Her Own

- **Character:** Dinah (Genesis 34)
- **Source:** [A Person, Not a Pretext](https://stevesammons.com/?p=3149), WordPress post 3149, scheduled April 16, 2028.
  The Substack twin is probably `sammons.substack.com/p/a-person-not-a-pretext` (not verified; it is still scheduled).
- **Guide:** canonical `suno-gospel-quartet-songwriting-guide.md` (Drive), adopted September 24, 2026
- **Suno account:** @stevesammons, Pro plan (no Studio, so no MIDI route)
- **Model:** v6
- **Status:** package ready; no candidates generated yet

## Format and rationale

**Format A, sung ballad.** The post has one clear turn: everyone around Dinah speaks, bargains or
takes revenge, and her own voice never appears. A thesis chorus carries that better than a
talking-story narrative, and a talking-story's easy humor would be wrong for this subject.

**Feel:** slow 3/4 hymn waltz, about 68 BPM. Verses sit in D minor (grave, careful); the chorus
opens into F major (warm, steady). The final chorus steps up a whole tone to G major and ends in a
barbershop **tag** with the tenor posting high above the held chord. The finish should sound like
dignity being restored in the telling, not like victory: full and ringing, not brassy.

**Catalog check (from the song.md files in Drive):** Hezekiah is a rolling 6/8 testimony,
Shadrach/Meshach/Abednego a 2/4 march, and Nathan and Nabal are swung 4/4 ballads. A minor-to-relative-major
3/4 waltz with a modulating tag is new ground. (`melodic-diversity-registry.json` is on Steve's
computer and was not checked.)

## Harmonic map and production route

**Route: uploaded audio reference** (Create > Advanced > Audio). Chord names never go in the
style or lyrics boxes. The chart lives in `chords.json` and is rendered by
`python3 songs/render_chords.py songs/dinah/chords.json`:

- `chords-reference.wav` (60 s): verse + chorus, piano and walking bass in 3/4 at 68 BPM. Upload this.
- `chords-tag.wav` (26 s): the tag as held chords, for the ending fix below if needed.
- `.mid` files of both, for the record.

| Section | Key | Bars (3/4, one chord per bar) |
|---|---|---|
| Verse | D minor | Dm · Dm/C · Bb · A7 · Dm · Gm · A7 · Dm |
| Chorus | F major | F · F7 · Bb · Bbm6 · F/C · D7 · G7 · C7 · F · A7 · Dm · Bb Bbm6 · F/C C7 · F |
| Bridge | D minor to F | Bb · C · Am · Dm · Gm7 · C7 · A7 · D7 (pivot up) |
| Final chorus | G major | chorus up a whole step |
| Tag | G major | C · Cm6 · G/D · E7 · A7 · D7 · G (held 3 bars) |

The chorus leans on barbershop moves: the minor iv (Bbm6), secondary dominants (D7, G7, A7) and
the tag's circle of fifths (E7 · A7 · D7 · G), which are the chords quartets "ring" on.

## Suno settings

| Setting | Value |
|---|---|
| Mode | Create > **Advanced** |
| Model | v6 |
| Audio | upload `chords-reference.wav` as the audio reference (not Cover) |
| Audio Influence | start at 40%; raise if the chords drift, lower if the piano sound takes over |
| Style Influence | high (about 75%) |
| Weirdness | low (about 25%) |
| Vocal Gender | Male |
| Exclude styles | female vocals, choir, drums, synth, autotune, rap, pop |

The influence numbers are starting points, not tested values. Record what was actually used
under Candidates.

## Ready-to-paste Suno package

Paste the STYLE line into **Styles**, and everything from `[Intro]` down into **Lyrics**.

```text
STYLE: Barbershop quartet, 1940s gospel quartet, close four-part male harmony, warm baritone lead, tenor lock, a cappella-style with light piano and upright bass, slow 3/4 hymn waltz, 66-70 BPM, grave tender minor-key verses, chorus opens into warm major, final chorus modulates up a whole step, reverent and dignified not triumphant, ends with a barbershop tag: ritardando, lead holds the last word while the tenor rises to a high ringing sustained note above the full chord, long fermata, clean stop

TITLE: Let Her Story Be Her Own

[Intro: quartet hums the opening chord softly]
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

[End: long held final chord, tenor on top, then silence]
```

## Getting the big finish

The ending is asked for in three places, because a single bracket tag is only a hint to Suno:

1. **Style line:** "ends with a barbershop tag: ritardando, lead holds the last word while the
   tenor rises to a high ringing sustained note above the full chord, long fermata, clean stop."
   "Tag" is the barbershop term for exactly this ending, and the tenor holding above the others
   is called a "post".
2. **Lyrics:** a `[Tag: ...]` direction, an open vowel to hold ("o-o-o-own" sings better than a
   closed word like "person"), echoes in parentheses to set up the call-and-answer before the hold,
   and an `[End: ...]` line asking for a held chord and then silence so it doesn't fade or ramble.
3. **Harmony:** the tag is written as a circle of fifths (E7 · A7 · D7 · G), the classic
   barbershop run into a ringing final chord, and it's already a whole step up from the chorus.

**If a candidate is good but the ending is weak,** don't regenerate the whole song. In the Song
Editor, select the last 20 to 30 seconds, choose **Replace Section**, paste the `[Tag]` and `[End]`
lines, and describe it: "slow barbershop tag, lead holds 'own', tenor soars to a high sustained
note over the full chord, long fermata, clean stop." If replacing needs audio, use `chords-tag.wav`.

## Lyric and source audit

- Keeps the post's sequence: the visit to the women of the land; Shechem's crime; the bargaining
  over marriage, land and trade; the brothers' deceit; Simeon and Levi killing the men while they
  were healing; Jacob's fear for the household; the brothers' retort (Genesis 34:31, paraphrased). Left out for
  length: the circumcision condition by name, removing Dinah from Shechem's house, and the plunder.
- Keeps the post's moral distinctions: the crime is Shechem's, not Dinah's; her visit did not cause
  it; marriage terms could not erase it; the massacre named a real outrage but multiplied the
  victims; the text never gives Dinah a voice, and the song doesn't invent one.
- No graphic detail. "Took her" and "the wrong was by his hand" follow the post's restraint.
- The modern verse follows the post's application: don't make someone's wound your argument; ask
  what she needs; respect her choices.
- Read-aloud check: the lines scan in 3/4, with near-rhymes (terms/swords, lost/cost) rather than
  forced rhymes.

**Tender ears:** written for a grandmother to hear. The crime is named only as "took her" and
"the wrong," and Genesis 34:31's "harlot" is paraphrased as "Should he treat our sister so?"

## Candidates

Generate two (one Create run gives two). Steve picks; nothing is downloaded before that.

| # | Suno link | Length | Audio / Style Influence | Hard gates | Ending |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
