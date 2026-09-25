#!/usr/bin/env python3
"""Build songs/n8n/song-clips-workflow.json, the n8n workflow that turns songs marked 'ready'
in Supabase into chord clips (two per version), stores them and emails Steve.

  python3 songs/n8n/build_workflow.py

The Code node embeds render-clips.js, so edit that file and rebuild rather than editing the
JSON by hand. Import the result in n8n: Workflows > Import from File.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
RENDERER = (HERE / "render-clips.js").read_text().split("\nif (typeof require")[0]

RENDER_CODE = RENDERER + r"""
// ---- n8n: group clips_queue rows (one per version) into one item per song ----
const SUNO = [
  'IN SUNO: Create > Advanced, model v6.',
  "Upload the chosen version's reference clip (attached, named v1-... or v2-...) as the Audio reference, not Cover.",
  'More Options: Vocal Gender Male, Audio Influence about 40%, Style Influence about 75%, Weirdness about 25%.',
  'If the ending falls flat, use Replace Section on the last 20-30 seconds with the [Tag] and [End] lines; the tag clip is attached too.',
  "Afterwards set the row's chosen_version and status 'generated', and paste the Suno links into candidate_urls.",
].join('\n');

const songs = new Map();
for (const { json: r } of $input.all()) {
  if (!songs.has(r.post_id)) {
    songs.set(r.post_id, { post_id: r.post_id, post_title: r.post_title, character: r.character, versions: [] });
  }
  songs.get(r.post_id).versions.push(r);
}

const slugify = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const out = [];
for (const song of songs.values()) {
  const base = { post_id: song.post_id, post_title: song.post_title, character: song.character };
  let current = null;
  try {
    const binary = {};
    const clip_paths = {};
    const sections = [];
    for (const v of song.versions.sort((a, b) => a.version - b.version)) {
      current = v.version;
      const chart = typeof v.chords === 'string' ? JSON.parse(v.chords) : v.chords;
      if (!chart || !chart.clips || !chart.clips.reference || !chart.clips.tag) {
        throw new Error('chords must list clips.reference and clips.tag');
      }
      const clips = renderClips(chart);
      for (const name of ['reference', 'tag']) {
        const key = `v${v.version}_${name}`;
        binary[key] = {
          data: clips[name].wav.toString('base64'), mimeType: 'audio/wav',
          fileName: `v${v.version}-${slugify(v.song_title)}-chords-${name}.wav`, fileExtension: 'wav',
        };
        clip_paths[key] = name === 'reference' ? v.reference_clip : v.tag_clip;
      }
      sections.push([
        `==== VERSION ${v.version}: ${v.song_title} ====`,
        `Format ${v.format || '?'} | ${v.feel || ''} | reference clip ${Math.round(clips.reference.seconds)} s`,
        `Exclude styles: ${v.exclude_styles || ''}`,
        '', 'STYLES:', v.style, '', 'LYRICS:', v.lyrics, '', 'NOTES:', v.notes || '',
      ].join('\n'));
    }
    const count = song.versions.length;
    out.push({
      json: {
        ...base, ok: true, clip_paths,
        attachments: Object.keys(binary).join(','),
        subject: `Song ready for Suno: ${song.character || song.post_title} (${count} version${count === 1 ? '' : 's'})`,
        email_body: [`Post ${song.post_id}: ${song.post_title}`, SUNO, ...sections].join('\n\n'),
      },
      binary,
    });
  } catch (e) {
    out.push({ json: { ...base, ok: false, error: `Version ${current}: ${(e && e.message) || e}` } });
  }
}
return out;
"""

LIST_CODE = r"""// One item per clip file, so the upload node sends each one.
const out = [];
for (const item of $input.all()) {
  for (const [key, bin] of Object.entries(item.binary || {})) {
    out.push({ json: { path: item.json.clip_paths[key] }, binary: { data: bin } });
  }
}
return out;
"""

ERROR_EMAIL = """=n8n couldn't render the chord clips for post {{ $('Rendered OK?').item.json.post_id }} ({{ $('Rendered OK?').item.json.post_title }}).

{{ $('Rendered OK?').item.json.error }}

The row is now 'needs_fix'. Paste the error into the post's chat in the Quartet Songs project, ask for corrected SQL, and run it; that sets the row back to 'ready'."""


def cond(key, value):
    return {"keyName": key, "condition": "eq", "keyValue": value}


def node(name, ntype, version, pos, params):
    return {"parameters": params, "id": name.lower().replace(" ", "-").replace("?", ""), "name": name,
            "type": ntype, "typeVersion": version, "position": pos}


def update_song(name, pos, post_id, fields):
    return node(name, "n8n-nodes-base.supabase", 1, pos, {
        "operation": "update", "tableId": "songs",
        "filterType": "manual", "matchType": "allFilters",
        "filters": {"conditions": [cond("post_id", post_id)]},
        "dataToSend": "defineBelow",
        "fieldsUi": {"fieldValues": [{"fieldId": k, "fieldValue": v} for k, v in fields]}})


nodes = [
    node("Every 5 minutes", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 300],
         {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}}),
    node("Settings", "n8n-nodes-base.set", 3.4, [220, 300], {
        "assignments": {"assignments": [
            {"id": "supabase-url", "name": "supabase_url", "type": "string",
             "value": "https://YOUR-PROJECT-REF.supabase.co"},
            {"id": "notify-email", "name": "notify_email", "type": "string",
             "value": "you@example.com"}]},
        "options": {}}),
    node("Songs ready for clips", "n8n-nodes-base.supabase", 1, [440, 300], {
        "operation": "getAll", "tableId": "clips_queue", "returnAll": True, "filterType": "none"}),
    node("Render chord clips", "n8n-nodes-base.code", 2, [660, 300],
         {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": RENDER_CODE}),
    node("Rendered OK?", "n8n-nodes-base.if", 2, [880, 300], {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
            "conditions": [{"id": "ok", "leftValue": "={{ $json.ok }}", "rightValue": True,
                            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
            "combinator": "and"},
        "options": {}}),
    node("List clip files", "n8n-nodes-base.code", 2, [1120, 120],
         {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": LIST_CODE}),
    node("Upload clip", "n8n-nodes-base.httpRequest", 4.2, [1340, 120], {
        "method": "POST",
        "url": "={{ $('Settings').first().json.supabase_url }}/storage/v1/object/song-clips/{{ $json.path }}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "supabaseApi",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "x-upsert", "value": "true"},
            {"name": "Content-Type", "value": "audio/wav"}]},
        "sendBody": True,
        "contentType": "binaryData",
        "inputDataFieldName": "data",
        "options": {}}),
    node("Email the song", "n8n-nodes-base.gmail", 2.1, [1120, 380], {
        "sendTo": "={{ $('Settings').first().json.notify_email }}",
        "subject": "={{ $json.subject }}",
        "emailType": "text",
        "message": "={{ $json.email_body }}",
        "options": {"appendAttribution": False,
                    "attachmentsUi": {"attachmentsBinary": [{"property": "={{ $json.attachments }}"}]}}}),
    update_song("Mark clips ready", [1340, 380], "={{ $('Render chord clips').item.json.post_id }}", [
        ("status", "clips_ready"), ("clips_made_at", "={{ $now.toISO() }}"), ("clip_error", "")]),
    update_song("Mark needs fix", [1120, 600], "={{ $json.post_id }}", [
        ("status", "needs_fix"), ("clip_error", "={{ $json.error }}")]),
    node("Email the error", "n8n-nodes-base.gmail", 2.1, [1340, 600], {
        "sendTo": "={{ $('Settings').first().json.notify_email }}",
        "subject": "=Chord clips failed: post {{ $('Rendered OK?').item.json.post_id }}",
        "emailType": "text",
        "message": ERROR_EMAIL,
        "options": {"appendAttribution": False}}),
]


def link(*targets):
    return {"main": [[{"node": t, "type": "main", "index": 0} for t in targets]]}


connections = {
    "Every 5 minutes": link("Settings"),
    "Settings": link("Songs ready for clips"),
    "Songs ready for clips": link("Render chord clips"),
    "Render chord clips": link("Rendered OK?"),
    # The upload branch sits above the email so it runs first; if an upload fails the run stops
    # before the email and the song stays 'ready' to retry in 5 minutes.
    "Rendered OK?": {"main": [
        [{"node": "List clip files", "type": "main", "index": 0},
         {"node": "Email the song", "type": "main", "index": 0}],
        [{"node": "Mark needs fix", "type": "main", "index": 0}]]},
    "List clip files": link("Upload clip"),
    "Email the song": link("Mark clips ready"),
    "Mark needs fix": link("Email the error"),
}

workflow = {
    "name": "Quartet songs: chord clips",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"},
    "active": False,
}

out = HERE / "song-clips-workflow.json"
out.write_text(json.dumps(workflow, indent=2) + "\n")
print(f"{out} ({len(nodes)} nodes)")
