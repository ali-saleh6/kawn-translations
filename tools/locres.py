#!/usr/bin/env python3
"""Read/write Unreal Engine .locres files (format versions 0-3).

Usage:
  python locres.py export <in.locres> <out.json>
  python locres.py import <template.locres> <translations.json> <out.locres>
  python locres.py roundtrip <in.locres> <out.locres>   (self-test)

JSON layout:
  {"<namespace>": {"__ns_hash__": <uint32>,
                   "<key>": {"key_hash": <uint32>, "hash": <uint32 source-text hash>,
                             "src": "<original text>", "text": "<translation>"}}}

`import` writes every entry of the template locres, using `text` from the
translations JSON where a non-empty translation exists and the template's own
text otherwise. Namespace/key hashes and source hashes are preserved verbatim
from the template so the game accepts the entries.
"""
import json
import struct
import sys

MAGIC = bytes.fromhex("0e147475674a03fc4a15909dc3377f1b")


class Reader:
    def __init__(self, b):
        self.b, self.p = b, 0

    def u8(self):
        v = self.b[self.p]
        self.p += 1
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.p)[0]
        self.p += 4
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.b, self.p)[0]
        self.p += 4
        return v

    def i64(self):
        v = struct.unpack_from("<q", self.b, self.p)[0]
        self.p += 8
        return v

    def fstr(self):
        n = self.i32()
        if n == 0:
            return ""
        if n < 0:
            n = -n
            s = self.b[self.p:self.p + n * 2].decode("utf-16-le", "surrogatepass")
            self.p += n * 2
        else:
            s = self.b[self.p:self.p + n].decode("latin-1")
            self.p += n
        return s.rstrip("\0")


def _mk_table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t


_CRC_TABLE = _mk_table()


def crc32_str_hash(s: str) -> int:
    """FCrc::StrCrc32<TCHAR>: CRC32 over each UTF-16 code unit, low byte then high byte."""
    crc = 0xFFFFFFFF
    tbl = _CRC_TABLE
    raw = s.encode("utf-16-le", "surrogatepass")
    for u in struct.unpack("<%dH" % (len(raw) // 2), raw):
        crc = tbl[(crc ^ (u & 0xFF)) & 0xFF] ^ (crc >> 8)
        crc = tbl[(crc ^ (u >> 8)) & 0xFF] ^ (crc >> 8)
    return (~crc) & 0xFFFFFFFF


def read_locres(path):
    b = open(path, "rb").read()
    if b[:16] != MAGIC:
        raise SystemExit(f"{path}: not a .locres file (bad magic)")
    r = Reader(b)
    r.p = 16
    version = r.u8()
    strings = []
    if version >= 1:
        arr_off = r.i64()
        save = r.p
        r.p = arr_off
        for _ in range(r.i32()):
            s = r.fstr()
            if version >= 2:
                r.i32()  # ref count
            strings.append(s)
        r.p = save
    if version >= 2:
        r.i32()  # total entry count
    out = {}
    for _ in range(r.i32()):
        ns_hash = r.u32() if version >= 2 else None
        ns = r.fstr()
        kc = r.i32()
        d = out.setdefault(ns, {})
        if ns_hash is not None:
            d["__ns_hash__"] = ns_hash
        for _ in range(kc):
            key_hash = r.u32() if version >= 2 else None
            key = r.fstr()
            src_hash = r.u32()
            text = strings[r.i32()] if version >= 1 else r.fstr()
            d[key] = {"hash": src_hash, "text": text}
            if key_hash is not None:
                d[key]["key_hash"] = key_hash
    return version, out


def fstr_bytes(s):
    if s == "":
        return struct.pack("<i", 1) + b"\x00"  # UE writes "" as a lone NUL
    if all(ord(c) < 128 for c in s):
        b = s.encode("ascii") + b"\x00"
        return struct.pack("<i", len(b)) + b
    b = (s + "\0").encode("utf-16-le", "surrogatepass")
    return struct.pack("<i", -(len(b) // 2)) + b


def entries(ns_dict):
    return {k: v for k, v in ns_dict.items() if k != "__ns_hash__"}


def write_locres(path, data, version=3):
    strings, sidx, refs = [], {}, []
    body = bytearray(struct.pack("<i", 0))  # placeholder: total entries
    body += struct.pack("<i", len(data))
    total = 0
    for ns, keys in data.items():
        ents = entries(keys)
        body += struct.pack("<I", keys.get("__ns_hash__", crc32_str_hash(ns))) + fstr_bytes(ns)
        body += struct.pack("<i", len(ents))
        for key, e in ents.items():
            t = e["text"]
            if t not in sidx:
                sidx[t] = len(strings)
                strings.append(t)
                refs.append(0)
            refs[sidx[t]] += 1
            body += struct.pack("<I", e.get("key_hash", crc32_str_hash(key))) + fstr_bytes(key)
            body += struct.pack("<I", e["hash"]) + struct.pack("<i", sidx[t])
            total += 1
    struct.pack_into("<i", body, 0, total)
    head = MAGIC + bytes([version])
    out = bytearray(head + struct.pack("<q", len(head) + 8 + len(body)) + body)
    out += struct.pack("<i", len(strings))
    for s, rc in zip(strings, refs):
        out += fstr_bytes(s) + struct.pack("<i", rc)
    open(path, "wb").write(out)


def count(data):
    return sum(len(entries(v)) for v in data.values())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "export":
        ver, data = read_locres(sys.argv[2])
        for ns in data.values():
            for k, e in entries(ns).items():
                e["src"] = e.pop("text")
                e["text"] = ""
        with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"version {ver}, {len(data)} namespaces, {count(data)} entries -> {sys.argv[3]}")
    elif cmd == "import":
        ver, base = read_locres(sys.argv[2])
        tr = json.load(open(sys.argv[3], encoding="utf-8"))
        hit = 0
        for ns, keys in base.items():
            for k, e in entries(keys).items():
                t = tr.get(ns, {}).get(k, {}).get("text", "")
                if t:
                    e["text"] = t
                    hit += 1
        write_locres(sys.argv[4], base)
        print(f"wrote {sys.argv[4]}: {hit} translated of {count(base)} entries")
    elif cmd == "roundtrip":
        ver, base = read_locres(sys.argv[2])
        write_locres(sys.argv[3], base)
        ver2, again = read_locres(sys.argv[3])
        a, b = open(sys.argv[2], "rb").read(), open(sys.argv[3], "rb").read()
        print("roundtrip data equal:", base == again, "| bytes identical:", a == b, len(a), len(b))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
