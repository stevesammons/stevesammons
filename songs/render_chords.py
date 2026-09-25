#!/usr/bin/env python3
"""Render a song's chord chart to MIDI and a plain piano-and-bass WAV.

The WAV is uploaded to Suno as the Audio reference (Create > Advanced) so the
harmony is anchored by sound, not by chord names typed into the text boxes.

Usage:
  python3 songs/render_chords.py songs/dinah/chords.json

chords.json:
  {"bpm": 68, "beats_per_bar": 3, "clips": {
      "reference": ["verse", "chorus"],        # sections rendered into each clip
      "tag": ["tag"]},
   "sections": {"verse": {"bars": ["Dm", "Dm/C", "Bb A7", ...]}, ...}}

Each bar string holds one or more chords (split across the bar's beats).
"G~3" sounds one chord held for 3 bars. A section with "feel": "sustain"
plays held block chords instead of the bass-then-chord pattern.
Needs numpy and mido (pip install numpy mido).
"""
import json, re, sys, wave
from pathlib import Path

import mido
import numpy as np

RATE = 22050
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITY = {  # intervals above the root
    "": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10),
    "maj7": (0, 4, 7, 11), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9),
    "dim": (0, 3, 6), "dim7": (0, 3, 6, 9), "sus4": (0, 5, 7), "7sus4": (0, 5, 7, 10),
    "9": (0, 4, 7, 10, 14), "add9": (0, 4, 7, 14),
}
CHORD = re.compile(r"^([A-G])([#b]?)([^/~]*)(?:/([A-G][#b]?))?(?:~(\d+))?$")


def pitch_class(name):
    pc = NOTE[name[0]]
    return (pc + (1 if name[1:] == "#" else -1 if name[1:] == "b" else 0)) % 12


def parse(symbol):
    m = CHORD.match(symbol)
    if not m or m.group(3) not in QUALITY:
        sys.exit(f"Unknown chord: {symbol}")
    root = pitch_class(m.group(1) + m.group(2))
    bass = pitch_class(m.group(4)) if m.group(4) else root
    return root, QUALITY[m.group(3)], bass, int(m.group(5) or 1)


def voice(root, intervals, bass):
    """Bass note between E2 and D#3, close chord tones between G3 and G4."""
    bass_note = 40 + (bass - 40) % 12
    tones = sorted(55 + (root + i - 55) % 12 for i in intervals)
    return bass_note, tones


def events(chart, section_names):
    """Yield (start_beat, beats, bass, tones, feel) for each chord."""
    beats_per_bar, beat = chart["beats_per_bar"], 0.0
    for name in section_names:
        section = chart["sections"][name]
        feel = section.get("feel", "pattern")
        for bar in section["bars"]:
            chords = bar.split()
            split = [beats_per_bar / len(chords)] * len(chords)
            if len(chords) == 2 and beats_per_bar == 3:
                split = [2, 1]
            for symbol, length in zip(chords, split):
                root, intervals, bass, hold = parse(symbol)
                bass_note, tones = voice(root, intervals, bass)
                total = length + (hold - 1) * beats_per_bar
                yield beat, total, bass_note, tones, feel
                beat += total


def tone(freq, seconds, bright, decay):
    t = np.arange(int(seconds * RATE)) / RATE
    wave_ = sum((bright ** k) * np.sin(2 * np.pi * freq * (k + 1) * t) for k in range(5))
    env = np.exp(-t * decay) * np.minimum(1, t / 0.005)
    tail = np.minimum(1, (seconds - t) / 0.05)
    return wave_ * env * tail


def midi_freq(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def render(chart, section_names, out_wav, out_mid):
    spb = 60.0 / chart["bpm"]
    evs = list(events(chart, section_names))
    total = (evs[-1][0] + evs[-1][1]) * spb + 2.0
    audio = np.zeros(int(total * RATE) + RATE)
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(chart["bpm"])))
    track.append(mido.MetaMessage("time_signature", numerator=chart["beats_per_bar"], denominator=4))
    notes = []  # (beat, on/off, note, velocity)

    def add(start_beat, beats, note, vol, decay, bright):
        start = int(start_beat * spb * RATE)
        seg = vol * tone(midi_freq(note), beats * spb + 0.3, bright, decay)
        audio[start:start + len(seg)] += seg
        notes.append((start_beat, 1, note, min(127, int(40 + vol * 250))))
        notes.append((start_beat + beats, 0, note, 0))

    for start, beats, bass, tones, feel in evs:
        if feel == "sustain":
            add(start, beats, bass, 0.30, 0.35, 0.35)
            for n in tones:
                add(start, beats, n, 0.13, 0.30, 0.45)
            continue
        add(start, beats, bass, 0.32, 1.2, 0.35)  # bass on the downbeat
        offbeat = 1.0
        while offbeat < beats:  # chord on the remaining beats
            for n in tones:
                add(start + offbeat, min(1.0, beats - offbeat), n, 0.11, 2.5, 0.5)
            offbeat += 1.0

    audio = audio / (np.max(np.abs(audio)) or 1) * 0.8
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((audio * 32767).astype("<i2").tobytes())

    last = 0
    for beat, on, note, vel in sorted(notes, key=lambda n: (n[0], n[1])):
        tick = int(round(beat * 480))
        track.append(mido.Message("note_on" if on else "note_off", note=note,
                                  velocity=vel, time=tick - last))
        last = tick
    mid.save(str(out_mid))
    return total


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    chart = json.loads(path.read_text())
    for clip, sections in chart["clips"].items():
        wav, mid = path.with_name(f"chords-{clip}.wav"), path.with_name(f"chords-{clip}.mid")
        seconds = render(chart, sections, wav, mid)
        print(f"{wav} ({seconds:.0f} s) and {mid.name}")


if __name__ == "__main__":
    main()
