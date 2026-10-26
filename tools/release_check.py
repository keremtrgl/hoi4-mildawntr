"""Pre-release check for the +Turkey submod and its Turkish language pack.

Run it before every Workshop upload. It resolves every reference against the same files the game
loads (vanilla HOI4, then Millennium Dawn with its replace_path folders, then this mod) and reports
problems by severity:

  ERROR  breaks something in game (missing event/idea/focus, broken localisation line, bad file)
  WARN   probably wrong or unfinished (event nothing fires, placeholder lost in translation, ...)
  INFO   numbers worth knowing (translation coverage, release state)

    python tools/release_check.py                 full check, exit code 1 if there are errors
    python tools/release_check.py --strict        warnings also fail
    python tools/release_check.py --all           list every item instead of the first 15 per check
    python tools/release_check.py --report FILE   also write the report as Markdown
    python tools/release_check.py --only refs,loc run some groups: files, loc, refs, pack, release, log

Paths default to this machine's Steam/Documents folders; override with --game, --md, --docs.
"""
import argparse, collections, glob, hashlib, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_sync import blocks, inner, strip_code, definitions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, 'turkish_pack')
STEAM = r'C:/Program Files (x86)/Steam/steamapps'
MD_ID, MOD_ID, PACK_ID = '2777392649', '3826896215', '3827287270'
# folders that never ship (keep in step with the robocopy sync in NOTLAR.md)
DEV_DIRS = {'.git', 'turkish_pack', '_archive', '.claude', '_workshop_gallery', '.vscode', 'tools', 'MD_source'}
DEV_FILES = {'.gitignore', 'NOTLAR.md'}
EVENT_KEYS = ('country_event', 'news_event', 'state_event', 'unit_leader_event', 'operative_leader_event')
LOC_LINE = re.compile(r'^\s*([^\s:#"]+):(\d*)\s*"(.*)"\s*(#.*)?$')
TOKENS = re.compile(r'\$[^$\s]+\$|\[[^\]\s][^\]]*\]|£\w+')

# ---------------------------------------------------------------- report


class Report:
    def __init__(self):
        self.checks = []          # (group, title, severity, items)

    def add(self, group, title, severity, items):
        self.checks.append((group, title, severity, list(items)))

    def count(self, severity):
        return sum(1 for c in self.checks if c[2] == severity and c[3])

    def text(self, limit):
        out = []
        for group in dict.fromkeys(c[0] for c in self.checks):
            out.append('')
            out.append('== ' + group.upper() + ' ' + '=' * (60 - len(group)))
            for g, title, sev, items in self.checks:
                if g != group:
                    continue
                if not items:
                    out.append(f'  [ OK  ] {title}')
                    continue
                tag = {'ERROR': 'ERROR', 'WARN': 'WARN ', 'INFO': 'INFO '}[sev]
                out.append(f'  [{tag}] {title} ({len(items)})' if sev != 'INFO' or len(items) > 1 else f'  [{tag}] {title}')
                shown = items if limit is None else items[:limit]
                for it in shown:
                    out.append('            ' + it)
                if len(shown) < len(items):
                    out.append(f'            ... {len(items) - len(shown)} more (--all to list everything)')
        return '\n'.join(out)

    def markdown(self):
        out = ['# Release check', '', time.strftime('%Y-%m-%d %H:%M'), '',
               f'**{self.count("ERROR")} errors, {self.count("WARN")} warnings**', '']
        for g, title, sev, items in self.checks:
            mark = 'OK' if not items else sev
            out.append(f'- **{mark}** {g}: {title}' + (f' ({len(items)})' if items and sev != 'INFO' else ''))
            for it in items:
                out.append(f'  - {it}')
        return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- loading

def read(path):
    return open(path, encoding='utf-8-sig', errors='replace').read().replace('\r\n', '\n')


def rel(path, base):
    return os.path.relpath(path, base).replace(os.sep, '/')


def files_under(base, patterns, skip_dev=False):
    out = {}
    for pat in patterns:
        for p in glob.glob(os.path.join(base, pat), recursive=True):
            r = rel(p, base)
            if skip_dev and r.split('/')[0] in DEV_DIRS:
                continue
            if os.path.isfile(p):
                out[r] = p
    return out


def replace_paths(md):
    d = os.path.join(md, 'descriptor.mod')
    return {p.strip('/') for p in re.findall(r'replace_path\s*=\s*"([^"]+)"', read(d))} if os.path.exists(d) else set()


class Layers:
    """the files the game loads: vanilla, MD over it (minus MD's replace_path folders), this mod over both"""

    def __init__(self, game, md):
        self.game, self.md = game, md
        self.replaced = replace_paths(md)

    def resolve(self, patterns):
        merged = {}
        for base, is_game in ((self.game, True), (self.md, False), (ROOT, False)):
            got = files_under(base, patterns, skip_dev=base == ROOT)
            if is_game:
                got = {r: p for r, p in got.items() if os.path.dirname(r) not in self.replaced}
            merged.update(got)
        return merged

    def layer_of(self, path):
        p = os.path.abspath(path)
        if p.startswith(os.path.abspath(ROOT)):
            return 'mod'
        return 'md' if p.startswith(os.path.abspath(self.md)) else 'game'


def loc_entries(path):
    """[(line_no, key, value)] plus [(line_no, text)] for malformed lines"""
    good, bad = [], []
    lines = read(path).split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith('#') or (i <= 2 and re.match(r'^l_\w+:\s*$', s)):
            continue
        m = LOC_LINE.match(line)
        if m:
            good.append((i, m.group(1), m.group(3)))
        else:
            bad.append((i, s[:90]))
    return good, bad


# ---------------------------------------------------------------- checks

def check_files(rep, mod_files):
    group = 'files'
    bom_missing, bom_bad, header_bad, braces, not_utf8, fake_dds, oggs = [], [], [], [], [], [], []
    for r, p in sorted(mod_files.items()):
        ext = os.path.splitext(r)[1].lower()
        raw = open(p, 'rb').read()
        if ext == '.ogg':
            oggs.append(r)
        if ext == '.dds' and not raw.startswith(b'DDS '):
            fake_dds.append(f'{r} (starts with {raw[:4]!r}, not a DDS texture)')
        if ext not in ('.txt', '.yml', '.gui', '.gfx', '.asset', '.mod'):
            continue
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as e:
            not_utf8.append(f'{r}: byte {e.start}')
            continue
        bom = raw.startswith(b'\xef\xbb\xbf')
        if ext == '.yml':
            if not bom:
                bom_missing.append(r)
            first = raw.decode('utf-8-sig').lstrip().split('\n', 1)[0].strip()
            if not re.match(r'^l_\w+:\s*$', first):
                header_bad.append(f'{r}: first line is "{first[:40]}"')
        elif bom and re.match(r'common/(scripted_effects|scripted_triggers)/', r):
            bom_bad.append(f'{r} (the parser rejects a BOM here)')
        if ext in ('.txt', '.gui', '.gfx', '.asset'):
            t = strip_code(read(p))
            depth, line = 0, 1
            for ch in t:
                if ch == '\n':
                    line += 1
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth < 0:
                        braces.append(f'{r}:{line} closes a block that was never opened')
                        break
            else:
                if depth > 0:
                    braces.append(f'{r}: {depth} block(s) never closed')
    rep.add(group, 'Script files have balanced braces', 'ERROR', braces)
    rep.add(group, 'Files are valid UTF-8', 'ERROR', not_utf8)
    rep.add(group, 'Localisation files start with a UTF-8 BOM', 'ERROR', bom_missing)
    rep.add(group, 'Localisation files start with an l_<language>: header', 'ERROR', header_bad)
    rep.add(group, 'No BOM in scripted effect/trigger files', 'ERROR', bom_bad)
    rep.add(group, '.dds files are real DDS textures', 'ERROR', fake_dds)
    rep.add(group, 'No OGG sounds (HOI4 plays sound effects from WAV only)', 'ERROR', oggs)


def check_loc(rep, en_mod_files, loc_union):
    group = 'loc'
    malformed, seen, dups = [], {}, []
    for r, p in sorted(en_mod_files.items()):
        good, bad = loc_entries(p)
        malformed += [f'{r}:{i}: {s}' for i, s in bad]
        for i, k, v in good:
            if k in seen and seen[k][0] != r + ':' + str(i):
                dups.append(f'{k}: {seen[k][0]} and {r}:{i}')
            else:
                seen[k] = (r + ':' + str(i), v)
    rep.add(group, 'Every localisation line is "key:0 \\"text\\""', 'ERROR', malformed)
    rep.add(group, 'No key defined twice in the mod', 'ERROR', dups)
    empty_desc = sorted(k for k, (_, v) in seen.items() if k.endswith('_desc') and not v.strip())
    rep.add(group, 'Focus/idea descriptions still empty', 'INFO',
            [f'{len(empty_desc)} empty *_desc keys (tools/focus_desc fills them in batches)'] if empty_desc else [])
    return seen


def check_refs(rep, layers, loc_union, mod_loc):
    group = 'refs'
    ev_files = layers.resolve(['events/*.txt'])
    common = layers.resolve(['common/**/*.txt'])
    history = layers.resolve(['history/**/*.txt'])
    gfx = layers.resolve(['interface/**/*.gfx'])
    texts = {r: strip_code(read(p)) for r, p in {**ev_files, **common, **history}.items()}

    events, mod_events, triggered = set(), {}, set()
    for r, p in ev_files.items():
        t = texts[r]
        for k, b in blocks(t):
            if k in EVENT_KEYS:
                m = re.search(r'\bid\s*=\s*([\w.\-]+)', b)
                if m:
                    events.add(m.group(1))
                    if layers.layer_of(p) == 'mod':
                        mod_events[m.group(1)] = (r, b)
                        if re.search(r'\bis_triggered_only\s*=\s*yes', b):
                            triggered.add(m.group(1))
    ideas = set()
    for r, p in common.items():
        if r.startswith('common/ideas/'):
            ideas |= definitions(r, read(p))
    focuses, trees, focus_ids_by_file = set(), set(), collections.defaultdict(set)
    for r, p in common.items():
        if r.startswith('common/national_focus/'):
            for kind, fid in focus_ids(texts[r]):
                (trees if kind == 'tree' else focuses).add(fid)
                if kind == 'focus':
                    focus_ids_by_file[r].add(fid)
    sprites, textures = {}, []
    for r, p in gfx.items():
        # sprite blocks may hold one level of nested blocks (animation = { ... }); keywords are case-insensitive
        for m in re.finditer(r'(?i)\b(?:spriteType|corneredTileSpriteType|frameAnimatedSpriteType|textSpriteType)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}',
                             strip_code_keep_strings(read(p))):
            body = re.sub(r'\{[^{}]*\}', '', m.group(1))
            n = re.search(r'(?i)\bname\s*=\s*"?([\w\-.]+)"?', body)
            tex = re.search(r'(?i)\btexturefile1?\s*=\s*"([^"]+)"', body)
            if n:
                sprites[n.group(1)] = r
                if tex and layers.layer_of(p) == 'mod':
                    textures.append((r, n.group(1), tex.group(1).replace('\\', '/')))

    mod_scripts = {r: t for r, t in texts.items() if layers.layer_of({**ev_files, **common, **history}[r]) == 'mod'}
    missing_ev, missing_idea, missing_focus, missing_tree, missing_sprite = (collections.defaultdict(set) for _ in range(5))
    for r, t in mod_scripts.items():
        for m in re.finditer(r'\b(?:' + '|'.join(EVENT_KEYS) + r')\s*=\s*(?:\{[^{}]*?\bid\s*=\s*)?([A-Za-z][\w\-]*\.[\w.\-]+)', t):
            if m.group(1) not in events:
                missing_ev[m.group(1)].add(r)
        for m in re.finditer(r'\b(?:add_ideas|remove_ideas)\s*=\s*(\{[^{}]*\}|[\w\-]+)', t):
            for i in re.findall(r'[\w\-]+', m.group(1)):
                if i not in ideas:
                    missing_idea[i].add(r)
        for m in re.finditer(r'\b(?:has_idea|remove_idea|add_idea|idea)\s*=\s*([\w\-]+)', t):
            if m.group(1) not in ideas and m.group(1) not in ('yes', 'no'):
                missing_idea[m.group(1)].add(r)
        for m in re.finditer(r'\b(?:has_completed_focus|complete_national_focus|unlock_national_focus|focus)\s*=\s*([\w\-.]+)', t):
            if m.group(1) not in focuses:
                missing_focus[m.group(1)].add(r)
        for m in re.finditer(r'\b(?:load_focus_tree|has_focus_tree)\s*=\s*(?:\{\s*tree\s*=\s*)?([\w\-]+)', t):
            if m.group(1) not in trees and m.group(1) not in ('yes', 'no'):
                missing_tree[m.group(1)].add(r)
        if r.startswith(('common/national_focus/', 'events/', 'common/decisions/')):
            for m in re.finditer(r'\b(?:icon|picture)\s*=\s*(GFX_[\w\-]+)', t):
                if m.group(1) not in sprites:
                    missing_sprite[m.group(1)].add(r)
        if r.startswith('common/ideas/'):
            for m in re.finditer(r'\bpicture\s*=\s*([\w\-]+)', t):
                s = m.group(1) if m.group(1).startswith('GFX_') else 'GFX_idea_' + m.group(1)
                if s not in sprites:
                    missing_sprite[s].add(r)

    fmt = lambda d: [f'{k}  <- {", ".join(sorted(v)[:3])}' for k, v in sorted(d.items())]
    rep.add(group, 'Every fired event exists', 'ERROR', fmt(missing_ev))
    rep.add(group, 'Every idea/national spirit used exists', 'ERROR', fmt(missing_idea))
    rep.add(group, 'Every focus referenced exists', 'ERROR', fmt(missing_focus))
    rep.add(group, 'Every focus tree loaded exists', 'ERROR', fmt(missing_tree))
    rep.add(group, 'Every focus icon / event picture / idea picture sprite exists', 'WARN', fmt(missing_sprite))

    roots = [ROOT, layers.md, layers.game]
    no_tex = [f'{n} -> {t}  ({r})' for r, n, t in textures if not any(os.path.exists(os.path.join(b, t)) for b in roots)]
    rep.add(group, 'Every sprite the mod defines points to an existing texture', 'ERROR', no_tex)

    # events nothing fires: triggered-only, never mentioned outside their own definition
    unfired = []
    if triggered:
        ns = sorted({e.split('.')[0] for e in triggered})
        pat = re.compile(r'\b((?:' + '|'.join(map(re.escape, ns)) + r')\.\w+)\b')
        uses = collections.Counter()
        for t in texts.values():
            uses.update(pat.findall(t))
        for gui in layers.resolve(['interface/**/*.gui']).values():
            uses.update(pat.findall(read(gui)))
        unfired = sorted(f'{e}  ({mod_events[e][0]})' for e in triggered if uses[e] <= 1)
    rep.add(group, 'Every triggered-only event is fired by something', 'WARN', unfired)

    # localisation the mod's own content needs
    need = []
    for r, t in mod_scripts.items():
        if r.startswith('common/national_focus/'):
            need += [(f, r) for f in focus_ids_by_file[r]]
        if r.startswith('common/ideas/'):
            need += [(i, r) for i in definitions(r, t)]
    for e, (r, b) in mod_events.items():
        if re.search(r'\bhidden\s*=\s*yes', b):
            continue
        for k in re.findall(r'\b(?:title|desc)\s*=\s*([A-Za-z][\w\-]*\.[\w.\-]+)', b):
            need.append((k, r))
        for k in re.findall(r'\bname\s*=\s*([A-Za-z][\w\-]*\.[\w.\-]+)', b):
            need.append((k, r))
    idea_names = set()
    for r, t in mod_scripts.items():
        if r.startswith('common/ideas/'):
            idea_names |= set(re.findall(r'\bname\s*=\s*([\w\-.]+)', t))
    missing_loc = sorted({f'{k}  ({r})' for k, r in need if k not in loc_union and k not in idea_names})
    rep.add(group, 'Focuses, spirits and events have localised names', 'WARN', missing_loc)

    sounds = files_under(ROOT, ['sound/**/*.asset'])
    no_sound = []
    for r, p in sounds.items():
        for f in re.findall(r'\bfile\s*=\s*"?([^"\s]+\.(?:wav|ogg))"?', read(p)):
            if not glob.glob(os.path.join(ROOT, 'sound', '**', os.path.basename(f)), recursive=True):
                no_sound.append(f'{f}  ({r})')
    rep.add(group, 'Every sound file referenced exists', 'ERROR', no_sound)


def focus_ids(t):
    """('tree', id) and ('focus', id) pairs of a national_focus file (comments stripped)"""
    out = []
    for k, b in blocks(t):
        if k == 'focus_tree':
            m = re.search(r'\bid\s*=\s*([\w\-.]+)', b)
            if m:
                out.append(('tree', m.group(1)))
            items = blocks(inner(b))
        elif k == 'shared_focus':
            items = [(k, b)]
        else:
            continue
        for fk, fb in items:
            if fk in ('focus', 'shared_focus'):
                m = re.search(r'\bid\s*=\s*([\w\-.]+)', fb)
                if m:
                    out.append(('focus', m.group(1)))
    return out


def strip_code_keep_strings(t):
    return re.sub(r'#[^\n"]*(?=\n|$)', '', t)


def check_pack(rep, loc_union, en_values, docs):
    group = 'pack'
    pack_files = files_under(PACK, ['localisation/**/*.yml'])
    malformed, seen, dups, orphans, token_diff, bom = [], {}, [], [], [], []
    for r, p in sorted(pack_files.items()):
        if not open(p, 'rb').read(3) == b'\xef\xbb\xbf':
            bom.append(r)
        good, bad = loc_entries(p)
        malformed += [f'{r}:{i}: {s}' for i, s in bad]
        for i, k, v in good:
            if k in seen:
                dups.append(f'{k}: {seen[k]} and {r}:{i}')
                continue
            seen[k] = f'{r}:{i}'
            if k not in loc_union:
                orphans.append(f'{k}  ({r}:{i})')
                continue
            en = en_values.get(k)
            if en is not None:
                a, b = collections.Counter(TOKENS.findall(en)), collections.Counter(TOKENS.findall(v))
                if a != b:
                    lost = list((a - b).elements())[:3]
                    extra = list((b - a).elements())[:3]
                    token_diff.append(f'{k}: ' + (f'missing {" ".join(lost)} ' if lost else '') + (f'extra {" ".join(extra)}' if extra else ''))
    rep.add(group, 'Pack files start with a UTF-8 BOM', 'ERROR', bom)
    rep.add(group, 'Every pack line is "key:0 \\"text\\""', 'ERROR', malformed)
    rep.add(group, 'No key translated twice', 'ERROR', dups)
    rep.add(group, 'No translations for keys that no longer exist (deleted content)', 'WARN', orphans)
    rep.add(group, 'Translations keep the $variables$, [scripted loc] and £icons of the English text', 'WARN', token_diff)
    mod_keys = {k for k, v in en_values.items() if v.strip()}
    missing = sorted(mod_keys - seen.keys())
    pct = 100 * (len(mod_keys) - len(missing)) / max(1, len(mod_keys))
    rep.add(group, 'Translation coverage', 'INFO',
            [f'{len(mod_keys) - len(missing)} / {len(mod_keys)} English keys of the mod translated ({pct:.1f}%)'] +
            ([f'untranslated, e.g. {", ".join(missing[:5])}'] if missing else []))


def tree_hashes(base, skip_dev):
    out = {}
    for d, dirs, fs in os.walk(base):
        rd = rel(d, base)
        if skip_dev and rd.split('/')[0] in DEV_DIRS:
            dirs[:] = []
            continue
        for f in fs:
            r = rel(os.path.join(d, f), base)
            if skip_dev and (r in DEV_FILES or r.split('/')[0] in DEV_DIRS):
                continue
            out[r] = os.path.join(d, f)
    return out


def same_files(a, b):
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    h = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
    return h(a) == h(b)


def check_release(rep, docs, md, game):
    group = 'release'
    desc = read(os.path.join(ROOT, 'descriptor.mod'))
    version = re.search(r'^version\s*=\s*"([^"]+)"', desc, re.M)
    version = version.group(1) if version else '?'
    problems = []
    if f'remote_file_id="{MOD_ID}"' not in desc.replace(' ', ''):
        problems.append(f'descriptor.mod has no remote_file_id="{MOD_ID}"')
    sv = re.search(r'supported_version\s*=\s*"([^"]+)"', desc)
    mdv = re.search(r'supported_version\s*=\s*"([^"]+)"', read(os.path.join(md, 'descriptor.mod'))) if os.path.exists(os.path.join(md, 'descriptor.mod')) else None
    if sv and mdv and sv.group(1) != mdv.group(1):
        problems.append(f'supported_version {sv.group(1)} differs from Millennium Dawn\'s {mdv.group(1)}')
    rep.add(group, 'descriptor.mod is complete and matches Millennium Dawn', 'ERROR', problems)

    git = lambda *a: subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, encoding='utf-8').stdout.strip()
    dirty = [l for l in git('status', '--porcelain').split('\n') if l.strip()]
    rep.add(group, 'Working tree is committed', 'WARN', dirty[:50])
    tag = 'v' + version
    tagged = git('rev-list', '-n1', tag)
    head = git('rev-parse', 'HEAD')
    stale = [f'{tag} already exists on another commit: bump version= in descriptor.mod before uploading'] if tagged and tagged != head else []
    rep.add(group, f'Version {version} is new (no tag on an older commit)', 'WARN', stale)

    upload = os.path.join(docs, 'mod', 'md_turkey_upload')
    sync = []
    if os.path.isdir(upload):
        a, b = tree_hashes(ROOT, True), tree_hashes(upload, False)
        sync += [f'missing in upload folder: {r}' for r in sorted(set(a) - set(b))]
        sync += [f'extra in upload folder: {r}' for r in sorted(set(b) - set(a))]
        sync += [f'differs: {r}' for r in sorted(set(a) & set(b)) if not same_files(a[r], b[r])]
    else:
        sync.append(f'{upload} does not exist')
    rep.add(group, 'Upload folder mod/md_turkey_upload matches the repository', 'WARN', sync)

    pack_local = os.path.join(docs, 'mod', 'md_turkey_tr')
    psync = []
    if os.path.isdir(pack_local):
        a, b = tree_hashes(PACK, False), tree_hashes(pack_local, False)
        psync += [f'missing: {r}' for r in sorted(set(a) - set(b))] + [f'extra: {r}' for r in sorted(set(b) - set(a))]
        psync += [f'differs: {r}' for r in sorted(set(a) & set(b)) if not same_files(a[r], b[r])]
    rep.add(group, 'Pack folder mod/md_turkey_tr matches turkish_pack/', 'WARN', psync)

    # local .mod entries carrying a Workshop id make the game skip the Workshop copy (system.log: Active Mod Count)
    clash = []
    for f in glob.glob(os.path.join(docs, 'mod', '*.mod')):
        name = os.path.basename(f)
        m = re.search(r'remote_file_id\s*=\s*"(\d+)"', read(f))
        if m and not name.startswith('ugc_') and os.path.exists(os.path.join(docs, 'mod', f'ugc_{m.group(1)}.mod')):
            clash.append(f'{name} has remote_file_id {m.group(1)} like ugc_{m.group(1)}.mod: the game will skip the Workshop copy. '
                         'Keep it out of mod/ except while uploading.')
    rep.add(group, 'No local .mod shadows a Workshop item', 'WARN', clash)

    sync_md = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'md_sync.py'), 'status', '--md', md],
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
    rep.add(group, 'Millennium Dawn files we override are in step with MD (tools/md_sync.py)', 'WARN',
            [] if sync_md.returncode == 0 else ['md_sync status reports changes; run python tools/md_sync.py'])
    rep.add(group, 'Release', 'INFO', [f'mod version {version}, pack version '
                                       + (re.search(r'^version\s*=\s*"([^"]+)"', read(os.path.join(PACK, 'descriptor.mod')), re.M) or [None, '?'])[1]])


def check_log(rep, docs):
    group = 'log'
    logs = os.path.join(docs, 'logs')
    sysl, errl = os.path.join(logs, 'system.log'), os.path.join(logs, 'error.log')
    if not os.path.exists(errl):
        rep.add(group, 'Last game session', 'INFO', ['no logs found'])
        return
    age = (time.time() - os.path.getmtime(errl)) / 3600
    active = re.findall(r'Active Mod: (.+)', read(sysl)) if os.path.exists(sysl) else []
    rep.add(group, 'Last game session', 'INFO', [f'{age:.1f} h ago, mods: ' + (', '.join(a.strip() for a in active) or '?')])
    ours = [a for a in active if '+Turkey (MD 2.0' in a]
    rep.add(group, 'The last session actually loaded +Turkey', 'WARN',
            [] if ours else ['system.log does not list +Turkey as an active mod: the game skipped it (see the shadowing check above)'])
    mod_paths = set(tree_hashes(ROOT, True))
    hits = []
    for line in read(errl).split('\n'):
        m = re.search(r'(?:file:? *"?|^\S+\]: )((?:common|events|history|interface|gfx|localisation|map|sound)/[^":]+?\.(?:txt|yml|gui|gfx|asset))', line)
        if m and m.group(1) in mod_paths:
            hits.append(line.split(']: ', 1)[-1][:200])
    rep.add(group, 'error.log has no errors from the mod\'s files', 'WARN', sorted(set(hits)))


# ---------------------------------------------------------------- main

def main():
    docs_default = os.path.join(os.path.expanduser('~'), 'Documents', 'Paradox Interactive', 'Hearts of Iron IV')
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--game', default=os.path.join(STEAM, 'common', 'Hearts of Iron IV'))
    ap.add_argument('--md', default=os.path.join(STEAM, 'workshop', 'content', '394360', MD_ID))
    ap.add_argument('--docs', default=docs_default)
    ap.add_argument('--only', default='files,loc,refs,pack,release,log')
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--report')
    a = ap.parse_args()
    only = set(a.only.split(','))
    for p, what in ((a.game, '--game'), (a.md, '--md')):
        if not os.path.isdir(p):
            sys.exit(f'{what} folder not found: {p}')

    t0 = time.time()
    rep = Report()
    layers = Layers(a.game, a.md)
    mod_files = tree_hashes(ROOT, True)
    en_mod = files_under(ROOT, ['localisation/english/**/*.yml'])
    loc_union, en_values = set(), {}
    if only & {'loc', 'refs', 'pack'}:
        for base in (a.game, a.md):
            for p in glob.glob(os.path.join(base, 'localisation', '**', '*.yml'), recursive=True):
                if '_l_english' in p or os.sep + 'english' in p or '/english' in p:
                    loc_union |= {k for _, k, _ in loc_entries(p)[0]}
        for r, p in en_mod.items():
            for _, k, v in loc_entries(p)[0]:
                loc_union.add(k)
                en_values[k] = v
    if 'files' in only:
        check_files(rep, {r: p for r, p in mod_files.items()} | {('turkish_pack/' + r): p for r, p in tree_hashes(PACK, False).items()})
    if 'loc' in only:
        check_loc(rep, en_mod, loc_union)
    if 'refs' in only:
        check_refs(rep, layers, loc_union, en_values)
    if 'pack' in only:
        check_pack(rep, loc_union, en_values, a.docs)
    if 'release' in only:
        check_release(rep, a.docs, a.md, a.game)
    if 'log' in only:
        check_log(rep, a.docs)

    print(rep.text(None if a.all else 15))
    errors, warns = rep.count('ERROR'), rep.count('WARN')
    print(f'\n{errors} error check(s), {warns} warning check(s)  [{time.time() - t0:.0f}s]')
    if a.report:
        open(a.report, 'w', encoding='utf-8').write(rep.markdown())
        print('report written to', a.report)
    sys.exit(1 if errors or (a.strict and warns) else 0)


if __name__ == '__main__':
    main()
