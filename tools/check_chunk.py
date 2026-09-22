#!/usr/bin/env python3
"""Validate a translated chunk output against its source chunk.

Usage:
  python check_chunk.py work/chunks/chunk_000.json work/out/chunk_000.json

Output file layout: JSON list of {"id": <int>, "ar": "<translation>"}.
Reports: missing/extra ids, empty translations, placeholder/tag/line-break
mismatches, and translations left identical to the English. Exit code 1 if
anything is wrong.
"""
import json
import re
import sys

PH = re.compile(r"\{[^{}]*\}")
# real rich-text tags only (<Warning>, <b>, <a url="...">, </>) — not dialogue choices like <Accept Quest>
TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9_]*(?:\s+[A-Za-z]+=\"[^\"]*\")*>|</>")


def main():
    src = {i["id"]: i for i in json.load(open(sys.argv[1], encoding="utf-8"))}
    try:
        out = json.load(open(sys.argv[2], encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("INVALID JSON:", e)
        sys.exit(1)
    tr = {}
    for o in out:
        tr[o["id"]] = o.get("ar", "")
    bad = 0
    missing = [i for i in src if i not in tr or not str(tr[i]).strip()]
    extra = [i for i in tr if i not in src]
    if missing:
        bad += len(missing)
        print(f"MISSING/EMPTY ids ({len(missing)}): {missing[:50]}")
    if extra:
        print(f"EXTRA ids ({len(extra)}): {extra[:20]}")
    for i, s in src.items():
        if i not in tr:
            continue
        a, t = s["src"], str(tr[i])
        probs = []
        if sorted(PH.findall(a)) != sorted(PH.findall(t)):
            probs.append(f"placeholders {PH.findall(a)} != {PH.findall(t)}")
        if sorted(TAG.findall(a)) != sorted(TAG.findall(t)):
            probs.append(f"tags {TAG.findall(a)} != {TAG.findall(t)}")
        if a.count("\n") != t.count("\n"):
            probs.append(f"line breaks {a.count(chr(10))} != {t.count(chr(10))}")
        if t.strip() == a.strip() and re.search(r"[A-Za-z]{3,}", a):
            probs.append("identical to English")
        if not re.search(r"[؀-ۿ]", t) and re.search(r"[A-Za-z]{3,}", a) and not PH.fullmatch(a.strip() or "x"):
            probs.append("no Arabic letters in translation")
        for p in probs:
            bad += 1
            print(f"id {i}: {p}\n   EN: {a[:100]!r}\n   AR: {t[:100]!r}")
    print(f"{len(src)} items, {len(tr)} translated, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
