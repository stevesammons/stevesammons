#!/usr/bin/env python3
"""Build songs/n8n/song-clips-workflow.json, the n8n workflow that turns 'ready' rows in the
Supabase songs table into chord clips, stores them and emails Steve.

  python3 songs/n8n/build_workflow.py

The Code node embeds render-clips.js, so edit that file and rebuild rather than editing the
JSON by hand. Import the result in n8n: Workflows > Import from File.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
RENDERER = (HERE / "render-clips.js").read_text().split("\nif (typeof require")[0]

CODE = RENDERER + r"""
// ---- n8n: one output item per song row, with the clips as binary 'reference' and 'tag' ----
const out = [];
for (const item of $input.all()) {
  const row = item.json;
  const base = {
    post_id: row.post_id, post_title: row.post_title, character: row.character,
    song_title: row.song_title, style: row.style, exclude_styles: row.exclude_styles,
    lyrics: row.lyrics, notes: row.notes,
  };
  try {
    const chart = typeof row.chords === 'string' ? JSON.parse(row.chords) : row.chords;
    if (!chart || !chart.clips || !chart.clips.reference || !chart.clips.tag) {
      throw new Error('chords must list clips.reference and clips.tag');
    }
    const clips = renderClips(chart);
    const slug = String(row.song_title || row.post_id).toLowerCase()
      .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const binary = {};
    for (const [name, clip] of Object.entries(clips)) {
      binary[name] = {
        data: clip.wav.toString('base64'), mimeType: 'audio/wav',
        fileName: `${slug}-chords-${name}.wav`, fileExtension: 'wav',
      };
    }
    out.push({
      json: {
        ...base, ok: true,
        reference_clip: `${row.post_id}/chords-reference.wav`,
        tag_clip: `${row.post_id}/chords-tag.wav`,
        reference_seconds: Math.round(clips.reference.seconds),
      },
      binary,
    });
  } catch (e) {
    out.push({ json: { ...base, ok: false, error: String((e && e.message) || e) } });
  }
}
return out;
"""

EMAIL = """={{ $json.character }}: {{ $json.song_title }}
Post {{ $json.post_id }}: {{ $json.post_title }}

IN SUNO: Create > Advanced, model v6
1. Audio: upload the attached {{ $binary.reference.fileName }} as the audio reference (not Cover).
2. More Options: Vocal Gender Male, Audio Influence about 40%, Style Influence about 75%, Weirdness about 25%.
3. Exclude styles: {{ $json.exclude_styles }}
4. Title: {{ $json.song_title }}
5. Styles box:

{{ $json.style }}

6. Lyrics box:

{{ $json.lyrics }}

NOTES
{{ $json.notes }}

If the ending falls flat, use the Song Editor's Replace Section on the last 20-30 seconds with the [Tag] and [End] lines; the tag clip is attached too.
When you've generated it, set the row's status to 'generated' and paste the two links into candidate_urls."""

ERROR_EMAIL = """=n8n couldn't render the chord clips for post {{ $json.post_id }} ({{ $json.song_title }}).

Error: {{ $json.error }}

The row is now 'needs_fix'. Ask the Quartet Songs project to correct the chords JSON and paste the new SQL; that sets it back to 'ready'."""


def cond(key, value):
    return {"keyName": key, "condition": "eq", "keyValue": value}


def node(name, ntype, version, pos, params, **extra):
    return {"parameters": params, "id": name.lower().replace(" ", "-"), "name": name,
            "type": ntype, "typeVersion": version, "position": pos, **extra}


ROW = "={{ $('Render chord clips').item.json.post_id }}"
UPLOAD_URL = ("={{ $('Settings').first().json.supabase_url }}/storage/v1/object/song-clips/"
              "{{ $json.%s }}")


def upload(name, pos, field):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos, {
        "method": "POST",
        "url": UPLOAD_URL % f"{field}_clip",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "supabaseApi",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "x-upsert", "value": "true"},
            {"name": "Content-Type", "value": "audio/wav"}]},
        "sendBody": True,
        "contentType": "binaryData",
        "inputDataFieldName": field,
        "options": {},
    })


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
        "operation": "getAll", "tableId": "songs", "limit": 5,
        "filterType": "manual", "matchType": "allFilters",
        "filters": {"conditions": [cond("status", "ready")]}}),
    node("Render chord clips", "n8n-nodes-base.code", 2, [660, 300],
         {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": CODE}),
    node("Rendered OK?", "n8n-nodes-base.if", 2, [880, 300], {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
            "conditions": [{"id": "ok", "leftValue": "={{ $json.ok }}", "rightValue": True,
                            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
            "combinator": "and"},
        "options": {}}),
    upload("Upload reference clip", [1120, 60], "reference"),
    upload("Upload tag clip", [1120, 220], "tag"),
    node("Email the song", "n8n-nodes-base.gmail", 2.1, [1120, 380], {
        "sendTo": "={{ $('Settings').first().json.notify_email }}",
        "subject": "=Song ready for Suno: {{ $json.character }} ({{ $json.song_title }})",
        "emailType": "text",
        "message": EMAIL,
        "options": {"appendAttribution": False,
                    "attachmentsUi": {"attachmentsBinary": [{"property": "reference,tag"}]}}}),
    node("Mark clips ready", "n8n-nodes-base.supabase", 1, [1340, 380], {
        "operation": "update", "tableId": "songs",
        "filterType": "manual", "matchType": "allFilters",
        "filters": {"conditions": [cond("post_id", ROW)]},
        "dataToSend": "defineBelow",
        "fieldsUi": {"fieldValues": [
            {"fieldId": "status", "fieldValue": "clips_ready"},
            {"fieldId": "reference_clip", "fieldValue": "={{ $('Render chord clips').item.json.reference_clip }}"},
            {"fieldId": "tag_clip", "fieldValue": "={{ $('Render chord clips').item.json.tag_clip }}"},
            {"fieldId": "clips_made_at", "fieldValue": "={{ $now.toISO() }}"},
            {"fieldId": "clip_error", "fieldValue": ""}]}}),
    node("Mark needs fix", "n8n-nodes-base.supabase", 1, [1120, 600], {
        "operation": "update", "tableId": "songs",
        "filterType": "manual", "matchType": "allFilters",
        "filters": {"conditions": [cond("post_id", "={{ $json.post_id }}")]},
        "dataToSend": "defineBelow",
        "fieldsUi": {"fieldValues": [
            {"fieldId": "status", "fieldValue": "needs_fix"},
            {"fieldId": "clip_error", "fieldValue": "={{ $json.error }}"}]}}),
    node("Email the error", "n8n-nodes-base.gmail", 2.1, [1340, 600], {
        "sendTo": "={{ $('Settings').first().json.notify_email }}",
        "subject": "=Chord clips failed: post {{ $('Rendered OK?').item.json.post_id }}",
        "emailType": "text",
        "message": ERROR_EMAIL.replace("$json.", "$('Rendered OK?').item.json."),
        "options": {"appendAttribution": False}}),
]


def link(*targets):
    return {"main": [[{"node": t, "type": "main", "index": 0} for t in targets]]}


connections = {
    "Every 5 minutes": link("Settings"),
    "Settings": link("Songs ready for clips"),
    "Songs ready for clips": link("Render chord clips"),
    "Render chord clips": link("Rendered OK?"),
    # Uploads sit above the email so they run first; if one fails the run stops before the
    # email and the row stays 'ready' to retry in 5 minutes.
    "Rendered OK?": {"main": [
        [{"node": n, "type": "main", "index": 0}
         for n in ("Upload reference clip", "Upload tag clip", "Email the song")],
        [{"node": "Mark needs fix", "type": "main", "index": 0}]]},
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
