# Developer tools

Not shipped to the Workshop (the upload sync excludes `tools/`).

## When Millennium Dawn updates: `md_sync.py`

The submod ships 16 files at the same path as MD files, so the game uses our copy instead of MD's.
`md_overrides.json` lists them and why. `md_base/` holds MD's copies as of the version we last synced
with (`base_version` in the JSON).

```
python tools/md_sync.py            # what changed in MD since the base; exit code 1 = action needed
python tools/md_sync.py merge      # bring MD's changes into the 'merge' files
python tools/md_sync.py accept "common/ideas/Turkish.txt"   # after reviewing a 'replace' file
```

- **merge** files are MD's file plus our edits. `merge` combines MD's changes with ours (3-way, line
  endings normalised). The politics-view file is rebuilt instead (`strategy: party_names`): our Turkey
  party lines go back to the top of their blocks on MD's new copy, so it never conflicts. Real conflicts
  in the other files are left marked `<<<<<<< submod` for manual resolution.
- **replace** files deliberately replace MD's Turkey content. `status` shows how many definitions MD
  added or removed; review them, port anything Turkey should have, then `accept` the file.
- `status` also lists anything only MD's replaced copies define that MD or the submod still reference
  (an MD event using an MD Turkish spirit we don't ship, say). Those must be added to the submod.

Typical MD update: `status` → `merge` → resolve/review → `accept` each reviewed replace file → test in
game → commit together with `md_base/`.

## When Millennium Dawn updates: `md_loc.py` (language pack)

The pack translates about 44,000 of MD's own English lines (interface, mechanics, EU, Middle East...).
`md_loc_base.json` records a fingerprint of every MD English line in the 120 files the pack translates, as
of the MD version the translations match. When MD changes a line, our Turkish goes stale silently; when
MD adds lines to those files, they show in English.

```
python tools/md_loc.py             # stale translations and new untranslated MD lines; exit code 1 = work to do
python tools/md_loc.py --all       # the full list
python tools/md_loc.py snapshot    # after translating them: record MD's current English as the base
```

`release_check.py` runs the same comparison in its pack group (two WARN checks).

## `convert_events.py`

Converts "fire as soon as the trigger holds" polled events into triggered events plus the daily
dispatcher in `common/scripted_effects/TUR_polled_event_dispatcher.txt`. Already applied in
2.0.2-TUR.2; kept for reference and for converting new events the same way.

## Before every release: `release_check.py`

Resolves references the way the game loads files (vanilla, then Millennium Dawn with its `replace_path`
folders, then this mod) and reports ERROR / WARN / INFO per check. Exit code 1 on errors.

```
python tools/release_check.py                  # everything, ~1 min
python tools/release_check.py --only refs,scope --all
python tools/release_check.py --report report.md
```

Groups: `files` (braces, encoding, BOM, real DDS, no OGG), `loc` (line syntax, duplicate keys), `refs`
(events, spirits, focuses, trees, sprites, textures, sounds, unfired events, missing names, flags read but never
set or set as another kind — reviewed ones go in `tools/flag_allow.json` — and prerequisites in another tree), `balance`
(unknown modifier names; modifiers stronger than MD's own strongest for the same key — reviewed ones go in
`tools/balance_allow.json` as `{"reviewed": ["idea_name:modifier_key", ...]}`), `scope` (state-only effects in
country scope and the other way round), `pack` (Turkish pack: syntax, duplicates, orphans, lost
`$vars$`/`[loc]`/`£icons`, coverage), `release` (descriptor, git state, version tag, upload folders, local
`.mod` files that make the game skip the Workshop copy, MD sync), `log` (did the last game session load the
mod, errors from our files in `error.log`).

`--offline` runs only what needs neither the game nor Millennium Dawn (syntax, encodings, localisation, dates,
treasury tooltips, power lock, focus layout, scopes). `.github/workflows/check.yml` runs it with `--strict` and the
tests on every push.

## Focus layout: `focus_layout.py`

Places every focus of every tree the way the game does, including the shared branches (Turan, Cyprus, EU/USoE)
that `offset` blocks move by the tree's `*_FOCUS_LOCATION` flag. Reports focuses at a negative position, two
focuses on one square, and `load_focus_tree` calls that do not call `TUR_clear_focus_location` first or do not set
the flag the tree is laid out for. `python tools/focus_layout.py --boxes` prints each tree's bounding box.
`release_check.py` runs the same checks.

## Pre-commit hook

`git config core.hooksPath tools/hooks` enables `tools/hooks/pre-commit`, which runs the content checks
(about 30 s) and blocks the commit on errors. Without game files it runs the `--offline` checks instead. The last report is in `.git/release_check_last.txt`.

## Focus AI weights: `add_ai_weights.py`

Gives every focus in the `MD_TUR_*` trees that has no `ai_will_do` a base weight from its effects and
`search_filters`: economy and research 14, stability and armed forces 10, others 8 (MD's usual base), wars and
annexations 2. Hand-written blocks are kept. `python tools/add_ai_weights.py` reports, `apply` writes; safe to
re-run after adding focuses.

## Focus descriptions: `focus_desc/`

`extract.py` groups focuses with an empty `_desc` by name and writes batches; texts go in `out/dNNN.txt` as
`index ||| English ||| Turkish`; `build.py check` validates them and `build.py apply .` writes them into the
English localisation and the Turkish pack. Re-running `extract.py` renumbers the groups, so the texts of an
applied round are archived with their `groups.json` (`round1/` = 2.0.2-TUR.5, `round2/` = 2.0.3-TUR.6) before
extracting the next round. After round 2 every focus in the trees has a description; the empty `_desc` keys
`release_check.py` still counts belong to commented-out focuses or loc keys no focus uses.
