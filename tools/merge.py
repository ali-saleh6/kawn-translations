#!/usr/bin/env python3
"""Merge translated chunk outputs into the translations JSON and validate.

Usage:
  python merge.py <source.json> <chunks_dir> <out_dir> <translations.json>

  <chunks_dir>/chunk_NNN.json   produced by chunk.py (has id, src, ns, key)
  <out_dir>/chunk_NNN.json      produced by translators: [{"id": n, "ar": "..."}]

Every source entry whose text equals a translated item's src receives the
translation. Creates or updates <translations.json> (same layout as
source.json with "text" filled). Existing translations are kept unless a chunk
output overrides them.

Validation warnings (never block): placeholder / rich-text tag / line-break
mismatches, and translations identical to the English source.
"""
import glob
import json
import os
import re
import sys

PH = re.compile(r"\{[^{}]*\}")
# real rich-text tags only (<Warning>, <b>, <a url="...">, </>) — not dialogue choices like <Accept Quest>
TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9_]*(?:\s+[A-Za-z]+=\"[^\"]*\")*>|</>")


def check(src, tr):
    problems = []
    if sorted(PH.findall(src)) != sorted(PH.findall(tr)):
        problems.append(f"placeholders {PH.findall(src)} vs {PH.findall(tr)}")
    if sorted(TAG.findall(src)) != sorted(TAG.findall(tr)):
        problems.append(f"tags {TAG.findall(src)} vs {TAG.findall(tr)}")
    if src.count("\n") != tr.count("\n"):
        problems.append(f"line breaks {src.count(chr(10))} vs {tr.count(chr(10))}")
    if tr.strip() == src.strip() and re.search(r"[A-Za-z]{3,}", src):
        problems.append("untranslated (identical to source)")
    return problems


def main():
    source, chunks_dir, out_dir, out = sys.argv[1:5]
    src = json.load(open(source, encoding="utf-8"))
    tr = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}

    by_text = {}
    for cpath in sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.json"))):
        opath = os.path.join(out_dir, os.path.basename(cpath))
        if not os.path.exists(opath):
            continue
        items = {i["id"]: i["src"] for i in json.load(open(cpath, encoding="utf-8"))}
        for o in json.load(open(opath, encoding="utf-8")):
            t = str(o.get("ar") or "").strip("\r\n")
            if t.strip() and o["id"] in items:
                by_text[items[o["id"]]] = t

    applied, warned = 0, 0
    for ns, v in src.items():
        tns = tr.setdefault(ns, {})
        if "__ns_hash__" in v:
            tns["__ns_hash__"] = v["__ns_hash__"]
        for k, e in v.items():
            if k == "__ns_hash__":
                continue
            te = tns.setdefault(k, {"key_hash": e.get("key_hash"), "hash": e["hash"], "src": e["src"], "text": ""})
            te["hash"], te["src"] = e["hash"], e["src"]
            if e.get("key_hash") is not None:
                te["key_hash"] = e["key_hash"]
            new = by_text.get(e["src"])
            if new:
                # keep the source's leading/trailing whitespace (some strings glue onto others)
                lead = e["src"][:len(e["src"]) - len(e["src"].lstrip())]
                trail = e["src"][len(e["src"].rstrip()):]
                te["text"] = lead + new.strip() + trail
                applied += 1
            if te["text"]:
                for p in check(e["src"], te["text"]):
                    warned += 1
                    print(f"WARN {ns}/{k}: {p}")
    # drop entries that no longer exist in the source
    for ns in list(tr):
        if ns not in src:
            del tr[ns]
            continue
        for k in list(tr[ns]):
            if k != "__ns_hash__" and k not in src[ns]:
                del tr[ns][k]

    total = sum(1 for v in src.values() for k in v if k != "__ns_hash__")
    filled = sum(1 for v in tr.values() for k, e in v.items() if k != "__ns_hash__" and e.get("text"))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tr, f, ensure_ascii=False, indent=1)
    print(f"applied {applied}; {filled}/{total} entries translated; {warned} warnings -> {out}")


if __name__ == "__main__":
    main()
