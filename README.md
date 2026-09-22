# Kawn Translations — ترجمات كون

Community Arabic (Saudi / Najdi) translations for games, plus one-click installers.

| Game | Status | Install |
|---|---|---|
| [RuneScape: Dragonwilds](games/rs-dragonwilds/) | in progress | `games/rs-dragonwilds/Install-Arabic.bat` |

## التركيب (للاعبين)

1. حمّل المستودع (Code → Download ZIP) وفك الضغط.
2. اقفل اللعبة.
3. شغّل `games/rs-dragonwilds/Install-Arabic.bat` بدبل كليك.
4. افتح اللعبة — النصوص بالعربي.

للإزالة: `Uninstall-Arabic.bat`. الباتش ما يعدّل أي ملف أصلي، هو ملف واحد ينحط في
`RSDragonwilds\Content\Paks\~mods\` والتحقق من ملفات اللعبة في Steam يرجّع كل شي.

**خيار ثاني:** `Install-Arabic.bat French` يخلي الإنجليزي كما هو ويحط العربي مكان الفرنسي، وتبدّل بينهم من
الإعدادات > اللغة (الخيار "العربية"). مناسب إذا تبي تقارن أو ترجع للإنجليزي بسرعة.

## How it works

RuneScape: Dragonwilds is Unreal Engine 5. Its text lives in `Game.locres` files (one per
culture) inside the main `.pak`. The game only exposes English and French in its language
menu and picks the culture from Steam at startup, so a brand-new `ar` culture would never be
selectable. Instead we ship a patch pak (`*_P.pak`, which the engine loads on top of the
original) that replaces the en-GB (or fr) `Game.locres` with the Arabic one. The game already
ships Noto Sans Arabic, so Arabic renders without font changes.

## Repo layout

```
TRANSLATION_GUIDE.md      style guide: Najdi Saudi dialect, technical rules
GLOSSARY.md               fixed terms and names (skills, gods, NPCs, places, items, UI)
tools/
  locres.py               UE .locres <-> JSON (export / import), byte-exact roundtrip
  chunk.py                split source JSON into translation chunks (unique texts)
  merge.py                merge chunks back + validate placeholders/tags/line breaks
  build.py                build the patch paks (json -> locres -> pak via repak)
  bin/repak.exe           https://github.com/trumank/repak (MIT/Apache-2.0)
games/rs-dragonwilds/
  source/en-GB/Game.json  extracted English text (15,112 entries, 152 namespaces)
  source/locres/*/        original Game.locres files used as build templates
  translations/ar/Game.json   the Arabic translation (edit "text")
  dist/*.pak              built patches
  Install-Arabic.ps1/.bat installer (auto-detects the Steam install)
```

## Contributing a translation fix

1. Find the string in `games/rs-dragonwilds/translations/ar/Game.json` (search the English in `src`).
2. Edit `text` following `TRANSLATION_GUIDE.md` and `GLOSSARY.md`.
3. Rebuild and test:

```bash
python tools/build.py
games/rs-dragonwilds/Install-Arabic.bat
```

4. Open a pull request.

## Re-extracting after a game update

```bash
tools/bin/repak.exe unpack -o work/extract -i "RSDragonwilds/Content/Localization/**" "C:/Program Files (x86)/Steam/steamapps/common/RSDragonwilds/RSDragonwilds/Content/Paks/RSDragonwilds-Windows.pak"
copy work/extract/RSDragonwilds/Content/Localization/Game/en-GB/Game.locres games/rs-dragonwilds/source/locres/en-GB/
copy work/extract/RSDragonwilds/Content/Localization/Game/fr/Game.locres    games/rs-dragonwilds/source/locres/fr/
python tools/locres.py export games/rs-dragonwilds/source/locres/en-GB/Game.locres games/rs-dragonwilds/source/en-GB/Game.json
python tools/chunk.py games/rs-dragonwilds/source/en-GB/Game.json work/chunks --existing games/rs-dragonwilds/translations/ar/Game.json
# translate the new chunks, then:
python tools/merge.py games/rs-dragonwilds/source/en-GB/Game.json work/chunks games/rs-dragonwilds/translations/ar/Game.json
python tools/build.py
```

## Legal

Fan-made, unofficial. Game text and assets belong to Jagex. This repo only contains the
translation and tooling; it does not redistribute game files beyond the localisation tables
needed to build the patch.
