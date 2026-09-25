#!/usr/bin/env python3
"""Check map content files against CONTENT_GUIDE.md.  python3 maps/lint.py [ids...|all]"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UK = r"\b(colour|centre|metre|kilometre|travelled|travelling|neighbour|favour|honour|labour|defence|offence|organise|recognise|realise|emphasise|grey|towards|whilst|amongst|judgement|fulfil|behaviour|harbour|theatre|programme|analyse|catalogue|dialogue|mould|plough|sceptic|storey|jewellery|practise|licence|cheque)\b"


def text_of(c):
    parts = []
    for p in c["places"].values():
        parts += [p.get("name", ""), p.get("sub", ""), p.get("text", "")]
    for ch in c["chapters"]:
        parts += [ch.get("title", ""), ch.get("html", "")] + ch.get("facts", []) + (ch.get("quote") or [])
    parts += [c.get("title", ""), c.get("kicker", "")]
    return parts


def lint(i):
    c = json.load(open(HERE / "content" / f"{i}.json"))
    w = []
    blob = "\n".join(text_of(c))
    if "—" in blob: w.append(f"em dash x{blob.count(chr(0x2014))}")
    for m in set(re.findall(UK, blob, re.I)): w.append(f"UK spelling: {m}")
    n = len(c["chapters"])
    if not 3 <= n <= 6: w.append(f"{n} chapters")
    for k, ch in enumerate(c["chapters"], 1):
        words = len(re.sub(r"<[^>]+>", " ", ch.get("html", "")).split())
        if not 45 <= words <= 140: w.append(f"ch{k} text {words} words")
        if not ch.get("facts"): w.append(f"ch{k} no facts")
        if len(ch.get("facts", [])) > 3: w.append(f"ch{k} {len(ch['facts'])} facts")
        q = ch.get("quote")
        if q:
            if len(q[0].split()) > 22: w.append(f"ch{k} quote {len(q[0].split())} words")
            if "NIV" not in q[1]: w.append(f"ch{k} quote not cited NIV")
        if len(ch.get("tab", "")) > 16: w.append(f"ch{k} long tab '{ch['tab']}'")
    for k, p in c["places"].items():
        if len(p.get("text", "").split()) > 85: w.append(f"place {k} text long")
    if not any(p.get("main") for p in c["places"].values()): w.append("no main place")
    return c.get("title", "?"), w


if __name__ == "__main__":
    ids = sys.argv[1:] or ["all"]
    if ids == ["all"]:
        ids = sorted(p.stem for p in (HERE / "content").glob("*.json"))
    bad = 0
    for i in ids:
        t, w = lint(i)
        bad += bool(w)
        print(("OK  " if not w else "WARN"), i, t, "|", "; ".join(w))
    print(f"{len(ids) - bad} of {len(ids)} clean")
