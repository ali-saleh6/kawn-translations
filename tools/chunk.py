#!/usr/bin/env python3
"""Split an exported source JSON (from locres.py export) into translation chunks.

Usage:
  python chunk.py <source.json> <out_dir> [--chars 20000] [--existing translations.json]

Each chunk is a JSON list of unique texts:
  [{"id": 12, "ns": "ST_ItemNames", "key": "OakLog", "src": "Oak Log", "refs": 3, "ar": ""}, ...]
Identical source texts are emitted once (first namespace/key shown, `refs` = how
many entries share it). Texts that already have a translation in --existing are
skipped. Chunks keep namespaces together so translators see related lines.
"""
import argparse
import json
import os
import re

LOREM = re.compile(r"^\s*Lorem ipsum", re.I)
# legal texts stay in English (EULA, privacy policy, third-party licences, terms of service)
LEGAL_KEY = re.compile(r"eula|licen[cs]e|privacy|terms.?of.?service|\btos\b|legal", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--chars", type=int, default=20000)
    ap.add_argument("--existing")
    a = ap.parse_args()

    src = json.load(open(a.source, encoding="utf-8"))
    done = {}
    if a.existing and os.path.exists(a.existing):
        ex = json.load(open(a.existing, encoding="utf-8"))
        for ns, v in ex.items():
            for k, e in v.items():
                if k != "__ns_hash__" and e.get("text"):
                    done[(ns, k)] = e["text"]

    # namespaces in the order they should be translated: UI first, then the '' widget namespace last
    order = sorted(src, key=lambda n: (n == "", n))
    seen = {}
    items = []
    for ns in order:
        for k, e in src[ns].items():
            if k == "__ns_hash__":
                continue
            t = e["src"]
            if not t.strip() or LOREM.match(t) or (ns, k) in done:
                continue
            if not re.search(r"[A-Za-z]", t):
                continue  # numbers/symbols only: nothing to translate
            if LEGAL_KEY.search(k) and len(t) > 300:
                continue
            if len(t) > 1500 and re.search(r"(Licen[cs]e|LICENSE|Copyright|WARRANT)", t):
                continue
            if t in seen:
                items[seen[t]]["refs"] += 1
                continue
            seen[t] = len(items)
            items.append({"id": len(items), "ns": ns, "key": k, "src": t, "refs": 1, "ar": ""})

    os.makedirs(a.out_dir, exist_ok=True)
    chunks, cur, size = [], [], 0
    for it in items:
        if cur and size + len(it["src"]) > a.chars:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(it)
        size += len(it["src"])
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks):
        with open(os.path.join(a.out_dir, f"chunk_{i:03d}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
    print(f"{len(items)} unique texts -> {len(chunks)} chunks in {a.out_dir}")


if __name__ == "__main__":
    main()
