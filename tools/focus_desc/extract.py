"""Collect focuses with empty descriptions, grouped by English name, with a compact summary of what each
does, and write them in batches for writing descriptions. Run from the mod root:
    python <this> <out dir>
"""
import collections, glob, json, os, re, sys
sys.path.insert(0, 'tools')
import md_sync as m

OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, 'batches'), exist_ok=True)
loc, tr = {}, {}
for p in glob.glob('localisation/english/**/*.yml', recursive=True):
    for k, v in re.findall(r'(?m)^\s*([^#\s:"][^:\s]*):\d*\s*"(.*)"\s*$', m.read(p)):
        loc[k] = v
for p in glob.glob('turkish_pack/localisation/english/replace/*.yml'):
    for k, v in re.findall(r'(?m)^\s*([^#\s:"][^:\s]*):\d*\s*"(.*)"\s*$', m.read(p)):
        tr[k] = v
PATH_NAMES = {'MD_TUR_DEM': 'AKP / democratic Turkey', 'MD_TUR_OTT': 'Islamist-Ottomanist', 'MD_TUR_TKP': 'TKP communist',
              'MD_TUR_ANARCHY': 'anarchist', 'MD_TUR_MHF': 'MHP / Grey Wolves nationalist', 'MD_TUR_AYM': 'Constitutional Court rule',
              'MD_TUR_TECH': 'technocratic HP', 'MD_TUR_CHP': 'CHP social democrat', 'MD_TUR_HEPAR': "Osman Pamukoglu's HEPAR",
              'MD_TUR_MIT': 'MIT intelligence state', 'MD_TUR_ATA_X': 'Ataturk returns (fiction)', 'MD_TUR_MAFIA': 'mafia regime',
              'MD_TUR_ANAP': 'ANAP liberal', 'MD_TUR_DSP': 'DSP (Ecevit) government', 'MD_TUR_AK2007': 'reformed AKP (2008)',
              'MD_TUR_GENC': 'GENCPARTI (Cem Uzan)', 'MD_TUR_LDP': 'LDP libertarian', 'MD_TUR_SAADET': 'Saadet / Milli Gorus',
              'MD_TUR_TSK': 'Turkish Armed Forces junta', 'MD_TUR_COM': 'communist bloc', 'MD_TUR_MHPs': 'MHP (nationalist movement)',
              'MD_TUR_COUP': 'Islamist coup regime', 'MD_TUR_MIL': 'military junta'}


def clean(s):
    return re.sub(r'§.|£\w+|\[[^\]]*\]|\$[^$]*\$', '', s).strip()


def summarize(fb):
    cr = re.search(r'completion_reward\s*=\s*\{', fb)
    if not cr:
        return ''
    body = fb[cr.end():]
    parts = []
    for idea in re.findall(r'(?:add_ideas|add_timed_idea\s*=\s*\{\s*idea)\s*=\s*([\w\-]+)', body):
        parts.append('spirit "' + clean(loc.get(idea, idea)) + '"')
    for idea in re.findall(r'remove_ideas\s*=\s*([\w\-]+)', body):
        parts.append('removes "' + clean(loc.get(idea, idea)) + '"')
    for (a, b) in re.findall(r'swap_ideas\s*=\s*\{\s*remove_idea\s*=\s*([\w\-]+)\s*add_idea\s*=\s*([\w\-]+)', body):
        parts.append('"' + clean(loc.get(a, a)) + '" -> "' + clean(loc.get(b, b)) + '"')
    for ev in re.findall(r'(?:country_event|news_event)\s*=\s*\{?\s*(?:id\s*=\s*)?([\w.\-]+)', body):
        t = loc.get(ev + '.title') or loc.get(ev + '.t')
        if t:
            parts.append('event "' + clean(t) + '"')
    for kw, label in (('add_political_power', 'PP'), ('add_stability', 'stability'), ('add_war_support', 'war support')):
        for v in re.findall(kw + r'\s*=\s*(-?[\d.]+)', body):
            parts.append(f'{label} {v}')
    for b in re.findall(r'type\s*=\s*(\w+)\s+level\s*=\s*\d+|add_building_construction\s*=\s*\{\s*type\s*=\s*(\w+)', body):
        pass
    bl = re.findall(r'add_building_construction\s*=\s*\{\s*type\s*=\s*(\w+)', body)
    if bl:
        parts.append('builds ' + ', '.join(sorted(set(bl))))
    for t in re.findall(r'load_focus_tree\s*=\s*\{?\s*(?:tree\s*=\s*)?(\w+)', body):
        parts.append('switches to ' + PATH_NAMES.get(t, t) + ' tree')
    for tag in re.findall(r'(?:create_wargoal|declare_war_on)\s*=\s*\{[^}]*target\s*=\s*(\w+)', body):
        parts.append('war goal/war on ' + tag)
    for tag in re.findall(r'annex_country\s*=\s*\{\s*target\s*=\s*(\w+)', body):
        parts.append('annexes ' + tag)
    for tt in re.findall(r'custom_effect_tooltip\s*=\s*([\w.\-]+)', body):
        if tt in loc and not tt.endswith('_tt') and len(clean(loc[tt])) < 160:
            parts.append('tooltip: ' + clean(loc[tt]))
    seen, out = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p); out.append(p)
    return '; '.join(out)[:300]


groups = collections.OrderedDict()
for p in sorted(glob.glob('common/national_focus/*.txt')):
    t = m.strip_code(m.read(p))
    for k, b in m.blocks(t):
        if k not in ('focus_tree', 'shared_focus'):
            continue
        tid = re.search(r'\bid\s*=\s*([\w\-]+)', b).group(1)
        items = m.blocks(m.inner(b)) if k == 'focus_tree' else [(k, b)]
        for fk, fb in items:
            if fk not in ('focus', 'shared_focus'):
                continue
            fid = re.search(r'\bid\s*=\s*([\w\-]+)', fb).group(1)
            if loc.get(fid + '_desc', '').strip():
                continue
            name = loc.get(fid)
            if not name:
                continue
            g = groups.setdefault(name, {'name': name, 'tr': tr.get(fid, ''), 'ids': [], 'trees': [], 'effects': '', 'pre': ''})
            g['ids'].append(fid)
            path = PATH_NAMES.get(tid, tid)
            if path not in g['trees']:
                g['trees'].append(path)
            if not g['effects']:
                g['effects'] = summarize(fb)
            if not g['pre']:
                pre = re.findall(r'prerequisite\s*=\s*\{([^{}]*)\}', fb)
                pn = [clean(loc.get(x, x)) for blk in pre for x in re.findall(r'focus\s*=\s*([\w\-]+)', blk)]
                g['pre'] = ' / '.join(pn[:2])

items = list(groups.values())
json.dump(items, open(os.path.join(OUT, 'groups.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
SIZE = 60
for n in range(0, len(items), SIZE):
    with open(os.path.join(OUT, 'batches', f'd{n // SIZE:03d}.txt'), 'w', encoding='utf-8') as f:
        for i, g in enumerate(items[n:n + SIZE], n):
            f.write(f"{i} ||| {clean(g['name'])} ||| TR: {clean(g['tr'])} ||| path: {', '.join(g['trees'][:3])}"
                    f" ||| after: {g['pre'] or '-'} ||| does: {g['effects'] or '-'}\n")
print('groups', len(items), 'batches', (len(items) + SIZE - 1) // SIZE)
