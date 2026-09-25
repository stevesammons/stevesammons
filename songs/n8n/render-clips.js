// Renders a song's chord chart into piano-and-bass WAV clips for Suno's Audio reference.
// JavaScript twin of songs/render_chords.py (same chart format, same sound), so it can run
// inside an n8n Code node with nothing installed. build_workflow.py pastes this file into
// the workflow; test it with: node songs/n8n/render-clips.js songs/dinah/chords.json

const RATE = 22050;
const NOTE = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
const QUALITY = {
  '': [0, 4, 7], m: [0, 3, 7], '7': [0, 4, 7, 10], m7: [0, 3, 7, 10],
  maj7: [0, 4, 7, 11], '6': [0, 4, 7, 9], m6: [0, 3, 7, 9],
  dim: [0, 3, 6], dim7: [0, 3, 6, 9], sus4: [0, 5, 7], '7sus4': [0, 5, 7, 10],
  '9': [0, 4, 7, 10, 14], add9: [0, 4, 7, 14],
};
const CHORD = /^([A-G])([#b]?)([^/~]*)(?:\/([A-G][#b]?))?(?:~(\d+))?$/;

function pitchClass(name) {
  const shift = name[1] === '#' ? 1 : name[1] === 'b' ? -1 : 0;
  return (((NOTE[name[0]] + shift) % 12) + 12) % 12;
}

const mod12 = (n) => ((n % 12) + 12) % 12;

function parseChord(symbol) {
  const m = CHORD.exec(symbol);
  if (!m || !(m[3] in QUALITY)) throw new Error(`Unknown chord: ${symbol}`);
  const root = pitchClass(m[1] + m[2]);
  return {
    root,
    intervals: QUALITY[m[3]],
    bass: m[4] ? pitchClass(m[4]) : root,
    hold: parseInt(m[5] || '1', 10),
  };
}

function chordEvents(chart, sectionNames) {
  const bpb = chart.beats_per_bar;
  const out = [];
  let beat = 0;
  for (const name of sectionNames) {
    const section = chart.sections[name];
    if (!section) throw new Error(`No section named ${name}`);
    const feel = section.feel || 'pattern';
    for (const bar of section.bars) {
      const chords = bar.trim().split(/\s+/);
      let split = chords.map(() => bpb / chords.length);
      if (chords.length === 2 && bpb === 3) split = [2, 1];
      chords.forEach((symbol, i) => {
        const c = parseChord(symbol);
        const bassNote = 40 + mod12(c.bass - 40);
        const tones = c.intervals.map((iv) => 55 + mod12(c.root + iv - 55)).sort((a, b) => a - b);
        const total = split[i] + (c.hold - 1) * bpb;
        out.push({ start: beat, beats: total, bassNote, tones, feel });
        beat += total;
      });
    }
  }
  return out;
}

function renderClip(chart, sectionNames) {
  const spb = 60 / chart.bpm;
  const evs = chordEvents(chart, sectionNames);
  const last = evs[evs.length - 1];
  const totalSeconds = (last.start + last.beats) * spb + 2;
  const audio = new Float64Array(Math.floor(totalSeconds * RATE) + RATE);

  const add = (startBeat, beats, note, vol, decay, bright) => {
    const start = Math.floor(startBeat * spb * RATE);
    const seconds = beats * spb + 0.3;
    const n = Math.floor(seconds * RATE);
    const freq = 440 * Math.pow(2, (note - 69) / 12);
    for (let i = 0; i < n && start + i < audio.length; i++) {
      const t = i / RATE;
      let w = 0;
      for (let k = 0; k < 5; k++) w += Math.pow(bright, k) * Math.sin(2 * Math.PI * freq * (k + 1) * t);
      const env = Math.exp(-t * decay) * Math.min(1, t / 0.005);
      const tail = Math.min(1, (seconds - t) / 0.05);
      audio[start + i] += vol * w * env * tail;
    }
  };

  for (const e of evs) {
    if (e.feel === 'sustain') {
      add(e.start, e.beats, e.bassNote, 0.30, 0.35, 0.35);
      for (const n of e.tones) add(e.start, e.beats, n, 0.13, 0.30, 0.45);
      continue;
    }
    add(e.start, e.beats, e.bassNote, 0.32, 1.2, 0.35); // bass on the downbeat
    for (let off = 1; off < e.beats; off += 1) {        // chord on the remaining beats
      for (const n of e.tones) add(e.start + off, Math.min(1, e.beats - off), n, 0.11, 2.5, 0.5);
    }
  }

  let peak = 0;
  for (const v of audio) peak = Math.max(peak, Math.abs(v));
  const scale = (peak || 1) / 0.8;
  const wav = Buffer.alloc(44 + audio.length * 2);
  wav.write('RIFF', 0);
  wav.writeUInt32LE(36 + audio.length * 2, 4);
  wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);        // PCM
  wav.writeUInt16LE(1, 22);        // mono
  wav.writeUInt32LE(RATE, 24);
  wav.writeUInt32LE(RATE * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write('data', 36);
  wav.writeUInt32LE(audio.length * 2, 40);
  for (let i = 0; i < audio.length; i++) wav.writeInt16LE(Math.trunc((audio[i] / scale) * 32767), 44 + i * 2);
  return { wav, seconds: totalSeconds };
}

// Returns { clipName: { wav: Buffer, seconds } } for every clip the chart lists.
function renderClips(chart) {
  const clips = {};
  for (const [name, sections] of Object.entries(chart.clips)) clips[name] = renderClip(chart, sections);
  return clips;
}

if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  const fs = require('fs');
  const path = require('path');
  const file = process.argv[2];
  const clips = renderClips(JSON.parse(fs.readFileSync(file, 'utf8')));
  for (const [name, clip] of Object.entries(clips)) {
    const out = path.join(path.dirname(file), `chords-${name}.js.wav`);
    fs.writeFileSync(out, clip.wav);
    console.log(`${out} (${Math.round(clip.seconds)} s)`);
  }
}
