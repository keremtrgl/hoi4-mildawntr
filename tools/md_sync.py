"""Keep the submod's copies of Millennium Dawn files in step with MD updates.

The submod ships some files at the same path as MD files, which makes the game use our copy
instead of MD's (see md_overrides.json). When MD updates, those copies silently go stale. This tool:

  status    (default) what changed in MD since our base snapshot, per file, plus a check for MD
            code that still calls things only MD's replaced files defined. Exit code 1 = action needed.
  merge     3-way merge MD's changes into every 'merge' file (git merge-file: base -> MD new,
            base -> ours). Clean merges also refresh the base snapshot; conflicts are left marked.
  accept F  after reviewing MD's changes to a 'replace' file, record MD's current copy as the base.
  snapshot  record MD's current copies of all listed files as the base (first-time setup).

usage: python tools/md_sync.py [status|merge|accept <path>|snapshot] [--md <MD folder>]
"""
import argparse, collections, filecmp, glob, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'tools', 'md_overrides.json'), encoding='utf-8'))
BASE = os.path.join(ROOT, 'tools', 'md_base')
DEFAULT_MD = r'C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/' + CFG['md_workshop_id']


def read(path):
    return open(path, encoding='utf-8-sig', errors='ignore').read().replace('\r\n', '\n')


def same(a, b):
    return os.path.exists(a) and os.path.exists(b) and read(a) == read(b)


def md_version(md):
    for p in (os.path.join(md, 'descriptor.mod'),):
        if os.path.exists(p):
            m = re.search(r'^version\s*=\s*"([^"]+)"', read(p), re.M)
            if m:
                return m.group(1)
    return '?'


# ---------------------------------------------------------------- definitions / references

def strip_code(t):
    """drop comments and quoted strings (log texts, loc keys in quotes are not references)"""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == '#':
            j = t.find('\n', i); i = n if j < 0 else j; continue
        if c == '"':
            j = t.find('"', i + 1); i = n if j < 0 else j + 1; out.append(' '); continue
        out.append(c); i += 1
    return ''.join(out)


def blocks(t):
    """depth-0 (key, body) pairs"""
    out, d, start, key = [], 0, None, None
    for m in re.finditer(r'([\w.:@\-]+)\s*=\s*\{|\{|\}', t):
        s = m.group(0)
        if s == '}':
            d -= 1
            if d == 0 and start is not None:
                out.append((key, t[start:m.end()])); start = None
        else:
            if d == 0:
                key, start = m.group(1), m.start()
            d += 1
    return out


def inner(body):
    return body[body.index('{') + 1:-1]


def definitions(rel, text):
    """ids a file defines, by file kind"""
    t = strip_code(text)
    if rel.startswith('events/'):
        return {re.search(r'\bid\s*=\s*([\w.\-]+)', b).group(1) for k, b in blocks(t)
                if k in ('country_event', 'news_event', 'state_event', 'unit_leader_event') and re.search(r'\bid\s*=', b)}
    if rel.startswith('common/ideas/'):
        return {ik for k, b in blocks(t) for ck, cb in blocks(inner(b)) for ik, ib in blocks(inner(cb))}
    if rel.startswith('common/characters/'):
        return {ck for k, b in blocks(t) for ck, cb in blocks(inner(b))}
    if rel.startswith('common/decisions/categories/') or rel.startswith('common/scripted_effects/') \
            or rel.startswith('common/scripted_triggers/'):
        return {k for k, b in blocks(t)}
    if rel.startswith('common/decisions/'):
        return {dk for k, b in blocks(t) for dk, db in blocks(inner(b))}
    if rel.startswith('common/national_focus/'):
        return set(re.findall(r'(?m)^\s*id\s*=\s*([\w\-]+)', t))
    return set()


def dangling(md):
    """things only MD's (replaced) copies define that MD or the submod still reference"""
    ours = {p.replace('\\', '/') for p in glob.glob(os.path.join(ROOT, '**', '*.*'), recursive=True)}
    ours = {os.path.relpath(p, ROOT).replace('\\', '/') for p in ours}
    our_defs = set()
    for p in glob.glob(os.path.join(ROOT, 'common', '**', '*.txt'), recursive=True) + glob.glob(os.path.join(ROOT, 'events', '*.txt')):
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        our_defs |= definitions(rel, read(p))
    lost = {}
    for rel, spec in CFG['files'].items():
        if spec['mode'] == 'replace' and os.path.exists(os.path.join(md, rel)):
            for d in definitions(rel, read(os.path.join(md, rel))):
                if d not in our_defs:
                    lost[d] = rel
    hits = collections.defaultdict(list)
    sources = [(os.path.relpath(p, md).replace('\\', '/'), p) for p in
               glob.glob(os.path.join(md, 'common', '**', '*.txt'), recursive=True) + glob.glob(os.path.join(md, 'events', '*.txt'))]
    sources = [(r, p) for r, p in sources if r not in ours]
    sources += [('submod:' + os.path.relpath(p, ROOT).replace('\\', '/'), p) for p in
                glob.glob(os.path.join(ROOT, 'common', '**', '*.txt'), recursive=True) + glob.glob(os.path.join(ROOT, 'events', '*.txt'))]
    for rel, p in sources:
        words = set(re.findall(r'[\w.\-]+', strip_code(read(p))))
        for w in words & lost.keys():
            hits[w].append(rel)
    return lost, hits


# ---------------------------------------------------------------- commands

def cmd_snapshot(md, only=None):
    for rel in (only or CFG['files']):
        src = os.path.join(md, rel)
        dst = os.path.join(BASE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
    if not only:
        CFG['base_version'] = md_version(md)
        json.dump(CFG, open(os.path.join(ROOT, 'tools', 'md_overrides.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print('base snapshot = MD', CFG['base_version'])


def cmd_status(md):
    print(f"MD installed: {md_version(md)}   base snapshot: {CFG['base_version']}")
    action = False
    for rel, spec in CFG['files'].items():
        mdp, basep, ourp = (os.path.join(x, rel) for x in (md, BASE, ROOT))
        if not os.path.exists(mdp):
            state = 'MD REMOVED THIS FILE: our copy may now add, not replace'; action = True
        elif not os.path.exists(basep):
            state = 'no base snapshot (run snapshot)'; action = True
        elif same(mdp, basep):
            state = 'MD unchanged'
        else:
            action = True
            if spec['mode'] == 'merge':
                state = 'MD CHANGED -> run: python tools/md_sync.py merge'
            else:
                a, b = definitions(rel, read(basep)), definitions(rel, read(mdp))
                state = f'MD CHANGED (+{len(b - a)} / -{len(a - b)} definitions) -> review, then: accept "{rel}"'
        print(f"  [{spec['mode']:7s}] {rel}\n            {state}")
    # new collisions: submod files that now shadow an MD file but are not listed
    for p in glob.glob(os.path.join(ROOT, '**', '*.*'), recursive=True):
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        if rel.split('/')[0] in ('common', 'events', 'history', 'localisation', 'interface') \
                and rel not in CFG['files'] and os.path.exists(os.path.join(md, rel)):
            print(f'  [NEW    ] {rel}\n            shadows an MD file but is not listed in md_overrides.json')
            action = True
    lost, hits = dangling(md)
    print(f'\nDefinitions only in MD copies of replaced files: {len(lost)}; still referenced: {len(hits)}')
    for w, refs in sorted(hits.items()):
        print(f'  {w}  (defined in MD {lost[w]})  <- {", ".join(refs[:4])}{" ..." if len(refs) > 4 else ""}')
        action = True
    print('\nACTION NEEDED' if action else '\nall in sync')
    return 1 if action else 0


DT = re.compile(r'(?m)^defined_text = \{\n\tname = (\S+)\n')


def dt_blocks(text):
    """name -> list of lines inside a top-level defined_text (after the name line)"""
    out, starts = {}, list(DT.finditer(text))
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        out[m.group(1)] = text[m.end():end].split('\n')
    return out


def regen_party_names(ours, base, new):
    """Rebuild our politics-view copy on top of MD's new file: our extra lines go back to the top of the
    same defined_text blocks and the MD lines we removed stay removed. Never conflicts."""
    ob, bb = dt_blocks(ours), dt_blocks(base)
    inserts, removals = {}, {}
    for name, olines in ob.items():
        blines = bb.get(name, [])
        bset, oset = set(blines), set(olines)
        add = [l for l in olines if l not in bset]
        rem = {l for l in blines if l not in oset and l.strip()}
        if add or rem:
            inserts[name], removals[name] = add, rem
    starts = list(DT.finditer(new))
    pieces = [new[:starts[0].start()] if starts else new]
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(new)
        lines = new[m.end():end].split('\n')
        name = m.group(1)
        if name in inserts:
            # our lines sit right after the name line (first match wins); MD lines we removed stay removed
            lines = inserts[name] + [l for l in lines if l not in removals[name]]
        pieces.append(new[m.start():m.end()] + '\n'.join(lines))
    text = ''.join(pieces)
    # our file header (comments before the first block) replaces MD's
    our_head = ours[:DT.search(ours).start()] if DT.search(ours) else ''
    new_head = new[:starts[0].start()] if starts else ''
    return our_head + text[len(new_head):]


def normalized_copy(path, tmpdir, name):
    """LF, no BOM: Windows checkouts are CRLF while MD ships LF, which would make every line conflict"""
    dst = os.path.join(tmpdir, name)
    open(dst, 'w', encoding='utf-8', newline='\n').write(read(path))
    return dst


def cmd_merge(md):
    import tempfile
    conflicts = 0
    for rel, spec in CFG['files'].items():
        if spec['mode'] != 'merge':
            continue
        mdp, basep, ourp = (os.path.join(x, rel) for x in (md, BASE, ROOT))
        if same(mdp, basep):
            continue
        raw = open(ourp, 'rb').read()
        bom, crlf = raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw
        if spec.get('strategy') == 'party_names':
            out = regen_party_names(read(ourp), read(basep), read(mdp))
            if crlf:
                out = out.replace('\n', '\r\n')
            open(ourp, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8'))
            cmd_snapshot(md, [rel])
            print('regenerated on MD\'s new copy:', rel)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            o, b, n = (normalized_copy(p, tmp, x) for p, x in ((ourp, 'ours'), (basep, 'base'), (mdp, 'new')))
            r = subprocess.run(['git', 'merge-file', '-L', 'submod', '-L', 'md-base', '-L', 'md-new', '-p', o, b, n],
                               capture_output=True)
        if r.returncode < 0 or r.returncode > 127:
            sys.exit('git merge-file failed for ' + rel)
        out = r.stdout.decode('utf-8')
        if crlf:
            out = out.replace('\n', '\r\n')
        open(ourp, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8'))
        if r.returncode == 0:
            cmd_snapshot(md, [rel])
            print('merged cleanly:', rel)
        else:
            conflicts += r.returncode
            print(f'CONFLICTS ({r.returncode}) left marked in:', rel)
    return 1 if conflicts else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('command', nargs='?', default='status', choices=['status', 'merge', 'accept', 'snapshot'])
    ap.add_argument('path', nargs='?')
    ap.add_argument('--md', default=DEFAULT_MD)
    a = ap.parse_args()
    if a.command == 'snapshot':
        cmd_snapshot(a.md)
    elif a.command == 'accept':
        if a.path not in CFG['files']:
            sys.exit('not a listed override: ' + str(a.path))
        cmd_snapshot(a.md, [a.path]); print('base updated for', a.path)
    elif a.command == 'merge':
        sys.exit(cmd_merge(a.md))
    else:
        sys.exit(cmd_status(a.md))
