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

## `convert_events.py`

Converts "fire as soon as the trigger holds" polled events into triggered events plus the daily
dispatcher in `common/scripted_effects/TUR_polled_event_dispatcher.txt`. Already applied in
2.0.2-TUR.2; kept for reference and for converting new events the same way.
