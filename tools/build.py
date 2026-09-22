#!/usr/bin/env python3
"""Build the RuneScape: Dragonwilds Arabic patch pak(s).

Usage:
  python build.py [--game games/rs-dragonwilds] [--repak tools/bin/repak.exe]

Produces:
  <game>/dist/RSDragonwilds-Arabic-over-English_P.pak
      replaces en-GB/Game.locres -> game shows Arabic immediately (default install)
  <game>/dist/RSDragonwilds-Arabic-over-French_P.pak
      replaces fr/Game.locres and relabels the "French" menu entry as "العربية"
      in en-GB, so players can switch between English and Arabic in the language menu

Inputs (inside <game>):
  source/locres/<culture>/Game.locres   original files extracted from the game pak
  translations/ar/Game.json             the Arabic translation
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import locres  # noqa: E402

LOC_DIR = "RSDragonwilds/Content/Localization/Game"
FRENCH_LABEL_KEY = ("ST_Settings", "ui.settings.accessibility.language.language.Choice2")


def apply(base, tr):
    hit = 0
    for ns, keys in base.items():
        for k, e in locres.entries(keys).items():
            t = tr.get(ns, {}).get(k, {}).get("text", "")
            if t:
                e["text"] = t
                hit += 1
    return hit


def pack(repak, retoc, stage, out_pak):
    """Write <name>.pak (repak) plus an empty IoStore container <name>.utoc/.ucas (retoc).

    UE 5.6 refuses to mount a pak that has no matching .utoc next to it, so the
    trio must ship together. The container is empty because .locres files are
    served from the .pak, not the IoStore."""
    os.makedirs(os.path.dirname(out_pak), exist_ok=True)
    base = out_pak[:-4]
    for ext in (".pak", ".utoc", ".ucas"):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    subprocess.run([repak, "pack", "--version", "V11", "--mount-point", "../../../", stage, out_pak], check=True)
    with tempfile.TemporaryDirectory() as t:
        subprocess.run([retoc, "to-zen", "--version", "UE5_6", stage, os.path.join(t, "c.utoc")], check=True)
        shutil.copy(os.path.join(t, "c.utoc"), base + ".utoc")
        shutil.copy(os.path.join(t, "c.ucas"), base + ".ucas")
    print("built", out_pak, os.path.getsize(out_pak), "bytes (+ .utoc/.ucas)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=os.path.join(HERE, "..", "games", "rs-dragonwilds"))
    ap.add_argument("--repak", default=os.path.join(HERE, "bin", "repak.exe"))
    ap.add_argument("--retoc", default=os.path.join(HERE, "bin", "retoc.exe"))
    a = ap.parse_args()
    game = os.path.abspath(a.game)
    tr = json.load(open(os.path.join(game, "translations", "ar", "Game.json"), encoding="utf-8"))
    src_locres = lambda c: os.path.join(game, "source", "locres", c, "Game.locres")

    # 1) Arabic over English (en-GB)
    with tempfile.TemporaryDirectory() as tmp:
        _, base = locres.read_locres(src_locres("en-GB"))
        n = apply(base, tr)
        d = os.path.join(tmp, LOC_DIR, "en-GB")
        os.makedirs(d)
        locres.write_locres(os.path.join(d, "Game.locres"), base)
        print(f"en-GB: {n} of {locres.count(base)} entries translated")
        pack(a.repak, a.retoc, tmp, os.path.join(game, "dist", "RSDragonwilds-Arabic-over-English_P.pak"))

    # 2) Arabic over French (fr) + relabel "French" -> "العربية" in the English menu
    with tempfile.TemporaryDirectory() as tmp:
        _, base = locres.read_locres(src_locres("fr"))
        n = apply(base, tr)
        d = os.path.join(tmp, LOC_DIR, "fr")
        os.makedirs(d)
        locres.write_locres(os.path.join(d, "Game.locres"), base)
        _, en = locres.read_locres(src_locres("en-GB"))
        en[FRENCH_LABEL_KEY[0]][FRENCH_LABEL_KEY[1]]["text"] = "العربية (Arabic)"
        d = os.path.join(tmp, LOC_DIR, "en-GB")
        os.makedirs(d)
        locres.write_locres(os.path.join(d, "Game.locres"), en)
        print(f"fr: {n} of {locres.count(base)} entries translated")
        pack(a.repak, a.retoc, tmp, os.path.join(game, "dist", "RSDragonwilds-Arabic-over-French_P.pak"))


if __name__ == "__main__":
    main()
