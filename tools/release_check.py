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
    with open(path, encoding='utf-8-sig', errors='replace') as source:
        return source.read().replace('\r\n', '\n')


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
        with open(p, 'rb') as source:
            raw = source.read()
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
        elif re.match(r'common/(scripted_effects|scripted_triggers|scripted_localisation)/', r) \
                and b'\xef\xbb\xbf' in raw:
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
    rep.add(group, 'No BOM in scripted effect/trigger/localisation files', 'ERROR', bom_bad)
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
    # the engine loads the .dds when a .tga path is missing (vanilla's own theatreselector.gfx relies on it)
    tex_exists = lambda t: any(os.path.exists(os.path.join(b, c)) for b in roots
                               for c in (t, re.sub(r'\.tga$', '.dds', t)))
    no_tex = [f'{n} -> {t}  ({r})' for r, n, t in textures if not tex_exists(t)]
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


# ---------------------------------------------------------------- balance and scope

# |value| above which a modifier on a national spirit / dynamic modifier is worth a second look.
# Keys not listed fall back by suffix: *_factor / *_modifier / *_multiplier at 1.0 (= +-100%).
LIMITS = {
    'political_power_cost': 1.0, 'political_power_gain': 2.0, 'political_power_factor': 0.5,
    'stability_factor': 0.30, 'war_support_factor': 0.30, 'stability_weekly': 0.01, 'war_support_weekly': 0.01,
    'consumer_goods_factor': 0.25, 'research_speed_factor': 0.30, 'industrial_capacity_factory': 0.5,
    'industrial_capacity_dockyard': 0.5, 'production_factory_max_efficiency_factor': 0.5,
    'production_factory_efficiency_gain_factor': 0.75, 'production_speed_buildings_factor': 0.75,
    'productivity_growth_modifier': 0.5, 'army_attack_factor': 0.30, 'army_defence_factor': 0.30,
    'army_core_attack_factor': 0.40, 'army_core_defence_factor': 0.40, 'army_org_factor': 0.30,
    'planning_speed': 0.5, 'max_planning': 0.5, 'tax_gain_multiplier_modifier': 0.5,
    'interest_rate_multiplier_modifier': 0.5, 'monthly_population': 0.5, 'conscription': 0.05,
    'democratic_drift': 0.3, 'communism_drift': 0.3, 'fascism_drift': 0.3, 'neutrality_drift': 0.3,
    'nationalist_drift': 0.3,
}
BALANCE_ALLOW = os.path.join(ROOT, 'tools', 'balance_allow.json')
FLAG_ALLOW = os.path.join(ROOT, 'tools', 'flag_allow.json')

STATE_ONLY = {'add_building_construction', 'add_extra_state_shared_building_slots', 'set_state_flag', 'clr_state_flag',
              'add_resource', 'add_core_of', 'remove_core_of', 'add_claim_by', 'remove_claim_by', 'damage_building',
              'set_building_level', 'set_demilitarized_zone', 'add_state_modifier', 'set_state_category'}
COUNTRY_ONLY = {'add_political_power', 'add_stability', 'add_war_support', 'add_ideas', 'remove_ideas', 'swap_ideas',
                'add_timed_idea', 'country_event', 'news_event', 'set_country_flag', 'clr_country_flag', 'set_politics',
                'add_popularity', 'load_focus_tree', 'add_named_threat', 'create_wargoal', 'declare_war_on',
                'add_tech_bonus', 'add_research_slot', 'add_equipment_to_stockpile', 'complete_national_focus',
                'set_party_name', 'retire_country_leader', 'add_opinion_modifier', 'add_to_faction', 'annex_country'}
STATE_SCOPES = {'random_owned_state', 'every_owned_state', 'random_state', 'every_state', 'random_controlled_state',
                'every_controlled_state', 'random_owned_controlled_state', 'every_owned_controlled_state', 'capital_scope',
                'random_core_state', 'every_core_state', 'random_neighbor_state', 'every_neighbor_state'}
COUNTRY_SCOPES = {'owner', 'controller', 'random_country', 'every_country', 'random_other_country', 'every_other_country',
                  'random_neighbor_country', 'every_neighbor_country', 'overlord', 'faction_leader', 'random_enemy_country',
                  'every_enemy_country', 'random_allied_country', 'every_allied_country', 'every_subject_country',
                  'random_subject_country', 'occupied_country_tag'}
TRIGGER_BLOCKS = {'limit', 'trigger', 'available', 'visible', 'allowed', 'potential', 'bypass', 'cancel', 'cancel_if_not_visible',
                  'activation', 'ai_will_do', 'ai_chance', 'mean_time_to_happen', 'modifier', 'is_good', 'target_trigger',
                  'target_root_trigger', 'highlight_states', 'state_target', 'on_map_area', 'cost', 'custom_cost_trigger'}
EFFECT_ROOTS = {'completion_reward': 'country', 'option': 'country', 'immediate': 'country', 'complete_effect': 'country',
                'remove_effect': 'country', 'timeout_effect': 'country', 'cancel_effect': 'country', 'select_effect': 'country'}


def block_items(body):
    """depth-1 items of a block body (comments stripped): (key, value, is_block, offset).
    For a block, value is its inner text and offset where that inner text starts in body."""
    out, depth, key, start = [], 0, None, None
    tok = re.compile(r'([\w.:@\-^]+)\s*[=<>]\s*(\{)|([\w.:@\-^]+)\s*[=<>]\s*([^\s{}]+)|(\{)|(\})')
    for m in tok.finditer(body):
        if m.group(2) or m.group(5):
            if depth == 0 and m.group(2):
                key, start = m.group(1), m.end()
            depth += 1
        elif m.group(6):
            depth -= 1
            if depth == 0 and key is not None:
                out.append((key, body[start:m.start()], True, start))
                key = None
        elif depth == 0 and m.group(3):
            out.append((m.group(3), m.group(4), False, m.start(3)))
    return out


def modifier_blocks(r, t):
    """(owner name, modifier block text) for an ideas or dynamic_modifiers file (comments stripped)"""
    if r.startswith('common/ideas/'):
        return [(idea, mb) for k, b in blocks(t) for ck, cb in blocks(inner(b)) for idea, ib in blocks(inner(cb))
                for mk, mb, is_block, _ in block_items(inner(ib)) if mk == 'modifier' and is_block]
    return [(k, inner(b)) for k, b in blocks(t)]


def numeric_modifiers(body):
    for k, v, is_block, _ in block_items(body):
        if not is_block and re.fullmatch(r'-?\d+(\.\d+)?', v):
            yield k, float(v), v


def known_modifiers(game, md):
    """(exact names, compiled template regex) of modifiers the game recognises: the game's own
    documentation/modifiers_documentation.md plus every layer's common/modifier_definitions"""
    names, templates = set(), []
    doc = os.path.join(game, 'documentation', 'modifiers_documentation.md')
    if os.path.exists(doc):
        for n in re.findall(r'(?m)^\* \[([^\]]+)\]\(#', read(doc)):
            if '<' in n:
                templates.append(re.escape(n).replace(r'\<', '<').replace(r'\>', '>'))
            else:
                names.add(n.lower())
    for base in (game, md, ROOT):
        for p in glob.glob(os.path.join(base, 'common', 'modifier_definitions', '*.txt')):
            names |= {k.lower() for k, _ in blocks(strip_code(read(p)))}
    pat = re.compile('|'.join(re.sub(r'<[^>]+>', r'[a-z0-9_]+', t.lower()) for t in templates) or r'(?!)')
    return names, pat


# keys that sit next to modifiers but are not modifiers (dynamic modifiers carry icon/enable/remove_trigger)
MODIFIER_BLOCK_KEYS = {'custom_modifier_tooltip', 'hidden_modifier', 'icon', 'enable', 'remove_trigger',
                       'valid_relation_trigger', 'attacker_modifier'}


def check_modifier_names(rep, mod_files, game, md):
    names, pat = known_modifiers(game, md)
    unknown = []
    for r, p in sorted(mod_files.items()):
        if not r.endswith('.txt') or not r.startswith(('common/ideas/', 'common/dynamic_modifiers/')):
            continue
        for name, body in modifier_blocks(r, strip_code(read(p))):
            for k, v, is_block, _ in block_items(body):
                # Clausewitz keys are case-insensitive (army_org_Factor works), so compare in lower case
                if is_block or k in MODIFIER_BLOCK_KEYS or k.lower() in names or pat.fullmatch(k.lower()):
                    continue
                unknown.append(f'{name}: {k} = {v}  ({r})')
    rep.add('balance', 'Every modifier name is one the game recognises (unknown ones are silently ignored)', 'ERROR', unknown)


def check_balance(rep, mod_files, md):
    """flag modifiers stronger than anything Millennium Dawn itself uses for the same key (MD's own max |value|);
    keys MD never uses fall back to LIMITS / 100% for *_factor-style keys. ai_* keys only steer AI and are skipped."""
    group = 'balance'
    md_max = collections.defaultdict(float)
    for p in glob.glob(os.path.join(md, 'common', 'ideas', '*.txt')) + glob.glob(os.path.join(md, 'common', 'dynamic_modifiers', '*.txt')):
        r = 'common/' + rel(p, os.path.join(md, 'common'))
        for _, body in modifier_blocks(r, strip_code(read(p))):
            for k, f, _ in numeric_modifiers(body):
                md_max[k.lower()] = max(md_max[k.lower()], abs(f))
    allow = set(json.load(open(BALANCE_ALLOW, encoding='utf-8')).get('reviewed', [])) if os.path.exists(BALANCE_ALLOW) else set()
    hits = []
    for r, p in sorted(mod_files.items()):
        if not r.endswith('.txt') or not r.startswith(('common/ideas/', 'common/dynamic_modifiers/')):
            continue
        for name, body in modifier_blocks(r, strip_code(read(p))):
            for k, f, v in numeric_modifiers(body):
                k = k.lower()
                if k.startswith('ai_') or k in MODIFIER_BLOCK_KEYS:
                    continue
                if k in md_max:
                    lim, src = md_max[k], 'MD max'
                else:
                    lim = LIMITS.get(k) or (1.0 if k.endswith(('_factor', '_modifier', '_multiplier')) else None)
                    src = 'limit'
                if lim is not None and abs(f) > lim + 1e-9 and f'{name}:{k}' not in allow:
                    hits.append(f'{name}: {k} = {v}  ({src} {lim:g})  ({r})')
    rep.add(group, "No modifier stronger than Millennium Dawn's own strongest (reviewed: tools/balance_allow.json)",
            'WARN', hits)


def check_structure(rep, mod_files, md):
    """flags read but never set (or set as another kind), and focuses wired to another tree; intentional flags, such
    as a mission's never-true `available`, go in tools/flag_allow.json"""
    group = 'refs'
    comment = re.compile(r'#[^\n]*')
    mod_text = {r: comment.sub('', read(p)) for r, p in mod_files.items() if r.endswith('.txt')}
    md_text = [comment.sub('', read(p)) for p in files_under(md, ['common/**/*.txt', 'events/**/*.txt']).values()]
    every = '\n'.join(list(mod_text.values()) + md_text)
    ours = '\n'.join(t for r, t in mod_text.items() if 'politicsview' not in r)      # MD's own lines for other countries
    allow = set(json.load(open(FLAG_ALLOW, encoding='utf-8')).get('reviewed', [])) if os.path.exists(FLAG_ALLOW) else set()

    def named(verb, kind, text):
        return (set(re.findall(rf'{verb}_{kind}_flag\s*=\s*(\w+)', text)) |
                set(re.findall(rf'{verb}_{kind}_flag\s*=\s*\{{[^}}]*?flag\s*=\s*(\w+)', text)))

    kinds = ('country', 'global', 'state')
    placed = {k: named('set', k, every) | named('modify', k, every) for k in kinds}
    bad = []
    for kind in kinds:
        for flag in sorted(named('has', kind, ours) - placed[kind] - allow):
            other = [k for k in kinds if flag in placed[k]]
            bad.append(f'has_{kind}_flag = {flag}: ' + (f'set as a {other[0]} flag' if other else 'never set'))
    rep.add(group, 'Every flag read is set as the same kind of flag (reviewed: tools/flag_allow.json)', 'WARN', bad)

    trees = {}
    for r, t in mod_text.items():
        if os.path.basename(r).startswith('MD_TUR_') and '/national_focus/' in '/' + r.replace(os.sep, '/'):
            for block in re.split(r'(?m)^[ \t]*focus[ \t]*=[ \t]*\{', t)[1:]:
                fid = re.search(r'\bid\s*=\s*(\S+)', block)
                if fid:
                    trees[fid.group(1)] = (os.path.basename(r), block)
    wired = []
    for fid, (tree, block) in trees.items():
        for group_body in re.findall(r'prerequisite\s*=\s*\{([^}]*)\}', block):
            for pre in re.findall(r'\bfocus\s*=\s*(\S+)', group_body):
                if pre in trees and trees[pre][0] != tree:
                    wired.append(f'{tree}: {fid} needs {pre} from {trees[pre][0]}')
    rep.add(group, 'Focus prerequisites stay inside their own tree', 'WARN', wired)


def check_logic(rep, mod_files, en_values):
    """conditions that can never hold and numbers that contradict what the player is told"""
    group = 'refs'
    comment = re.compile(r'#[^\n]*')
    texts = {r: comment.sub('', read(p)) for r, p in mod_files.items() if r.endswith('.txt') and 'politicsview' not in r}
    dates, money, party = [], [], []
    money_re = re.compile(r'subtract_from_variable\s*=\s*\{\s*treasury\s*=\s*(-?[\d.]+)\s*\}')

    def day(s):
        return tuple((int(x) for x in (s.split('.') + ['1', '1'])[:3]))

    for r, t in texts.items():
        for m in re.finditer(r'date\s*>\s*([\d.]+)\s+date\s*<\s*([\d.]+)', t):
            if day(m.group(1)) >= day(m.group(2)):
                dates.append(f'{r}:{t.count(chr(10), 0, m.start()) + 1}: date > {m.group(1)} and date < {m.group(2)}')
        for m in money_re.finditer(t):
            near = t[max(0, m.start() - 200):m.end() + 200]
            tips = sorted((abs(x.start() - 200), x.group(1)) for x in re.finditer(r'custom_effect_tooltip\s*=\s*(\S*(?:billion|trillion|million)\S*)', near))
            told = re.search(r'([\d.]+)\s*(Billion|Trillion|Million)', en_values.get(tips[0][1], '')) if tips else None
            if told:
                amount = float(told.group(1)) * {'Billion': 1, 'Trillion': 1000, 'Million': .001}[told.group(2)]
                amount *= 1 if en_values[tips[0][1]].startswith('Add') else -1
                if abs(amount + float(m.group(1))) > 1e-6:
                    money.append(f'{r}:{t.count(chr(10), 0, m.start()) + 1}: changes the treasury by {-float(m.group(1)):g}, {tips[0][1]} says {amount:g}')
        for m in re.finditer(r'party_pop_array\^(\d+)', t):
            if int(m.group(1)) > 23:
                party.append(f'{r}:{t.count(chr(10), 0, m.start()) + 1}: party_pop_array^{m.group(1)} (the array has 24 parties)')
    rep.add(group, 'Date windows can be true', 'WARN', dates)
    rep.add(group, 'Treasury changes match their tooltips', 'WARN', money)
    rep.add(group, 'Party indexes are inside party_pop_array', 'WARN', party)


def check_scopes(rep, mod_files):
    """country-only effects in a state scope and state-only effects in a country scope, in event options and
    immediates, focus rewards and decision effects; scopes we cannot know (ROOT, FROM, PREV, event targets) are skipped"""
    group = 'scope'
    hits = []

    def walk(body, base, scope, text, r, weights=False):
        for k, v, is_block, off in block_items(body):
            if k in TRIGGER_BLOCKS:
                continue
            line = text.count('\n', 0, base + off) + 1
            if scope == 'country' and k in STATE_ONLY:
                hits.append(f'{r}:{line}: {k} in country scope (needs a state scope)')
            elif scope == 'state' and k in COUNTRY_ONLY:
                hits.append(f'{r}:{line}: {k} in state scope (needs owner = {{ }} or a country scope)')
            if not is_block:
                continue
            sub = scope
            if re.fullmatch(r'\d+', k):
                sub = scope if weights else 'state'      # random_list children are weights, not state ids
            elif k in STATE_SCOPES:
                sub = 'state'
            elif k in COUNTRY_SCOPES or re.fullmatch(r'[A-Z][A-Z0-9]{2}', k):
                sub = 'country'
            elif k in ('ROOT', 'FROM', 'PREV', 'THIS') or k.startswith(('event_target:', 'var:', 'FROM.', 'ROOT.', 'PREV.')):
                sub = 'unknown'
            walk(v, base + off, sub, text, r, weights=(k == 'random_list'))

    def roots(body, base, text, r):
        for k, v, is_block, off in block_items(body):
            if not is_block or k in TRIGGER_BLOCKS:
                continue
            if k in EFFECT_ROOTS:
                walk(v, base + off, EFFECT_ROOTS[k], text, r)
            else:
                roots(v, base + off, text, r)

    for r, p in sorted(mod_files.items()):
        if r.endswith('.txt') and r.startswith(('events/', 'common/national_focus/', 'common/decisions/')):
            text = strip_code(read(p))
            if r.startswith('events/'):
                # state_event options run in state scope
                for k, v, is_block, off in block_items(text):
                    if is_block:
                        root_scope = 'state' if k == 'state_event' else 'country'
                        for ck, cv, cb, coff in block_items(v):
                            if cb and ck in ('option', 'immediate'):
                                walk(cv, off + coff, root_scope, text, r)
            else:
                roots(text, 0, text, r)
    rep.add(group, 'State effects run in a state scope and country effects in a country scope', 'WARN', sorted(set(hits)))


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
    ap.add_argument('--only', default='files,loc,refs,balance,scope,pack,release,log')
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
        check_structure(rep, mod_files, a.md)
        check_logic(rep, mod_files, en_values)
    if 'balance' in only:
        check_modifier_names(rep, mod_files, a.game, a.md)
        check_balance(rep, mod_files, a.md)
    if 'scope' in only:
        check_scopes(rep, mod_files)
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
