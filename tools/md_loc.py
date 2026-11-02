"""Keep the language pack's translations of Millennium Dawn's own texts in step with MD updates.

The pack translates MD's English localisation (interface, mechanics, EU, Middle East...). When MD
changes an English line, our Turkish line goes stale without any error; when MD adds lines to a file we
translated, they show in English. md_loc_base.json records a short fingerprint of every MD English line
in the files we translated, as of the MD version the translations were made against. This tool compares
MD's current English with that record:

  status    (default) translations whose MD English changed since the record, and new MD lines in files
            we translate that have no translation yet. Exit code 1 = something to translate.
  snapshot  record MD's current English as the base. Run it after updating the translations.

usage: python tools/md_loc.py [status|snapshot] [--md <MD folder>] [--all]
"""
import argparse, glob, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, 'turkish_pack')
BASE = os.path.join(ROOT, 'tools', 'md_loc_base.json')
DEFAULT_MD = r'C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/2777392649'
LOC_LINE = re.compile(r'^\s*([^\s:#"]+):(\d*)\s*"(.*)"\s*(#.*)?$')


def entries(path):
    """{key: value} of a localisation file"""
    out = {}
    with open(path, encoding='utf-8-sig', errors='replace') as source:
        for line in source:
            m = LOC_LINE.match(line.rstrip('\r\n'))
            if m:
                out[m.group(1)] = m.group(3)
    return out


def english_files(base):
    """relative path -> absolute path of every English localisation file under base"""
    found = {}
    for p in glob.glob(os.path.join(base, 'localisation', '**', '*.yml'), recursive=True):
        r = os.path.relpath(p, base).replace('\\', '/')
        if '/english/' in r or r.endswith('_l_english.yml'):
            found[r] = p
    return found


def md_english(md):
    """key -> (MD file, English text), with MD's replace/ folder winning like it does in game"""
    out = {}
    for r, p in sorted(english_files(md).items(), key=lambda i: '/replace/' in i[0]):
        for k, v in entries(p).items():
            out[k] = (r, v)
    return out


def mod_keys():
    keys = set()
    for p in english_files(ROOT).values():
        keys |= entries(p).keys()
    return keys


def pack_keys():
    keys = set()
    for p in glob.glob(os.path.join(PACK, 'localisation', '**', '*.yml'), recursive=True):
        keys |= entries(p).keys()
    return keys


def fingerprint(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]


def md_version(md):
    p = os.path.join(md, 'descriptor.mod')
    if os.path.exists(p):
        m = re.search(r'^version\s*=\s*"([^"]+)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M)
        if m:
            return m.group(1)
    return '?'


def snapshot(md):
    """fingerprints of every line in the MD files the pack translates (the mod's own keys excluded)"""
    md_now, ours, translated = md_english(md), mod_keys(), pack_keys()
    files = {r for k, (r, _) in md_now.items() if k in translated and k not in ours}
    lines = {k: fingerprint(v) for k, (r, v) in md_now.items() if r in files and k not in ours}
    return {'md_version': md_version(md), 'files': sorted(files), 'lines': dict(sorted(lines.items()))}


def compare(md, base=None):
    """(changed, new): translated keys whose MD English changed since the base, and MD lines in the
    covered files that are not in the base and not translated. Each item is (key, MD file, English)."""
    if base is None:
        if not os.path.exists(BASE):
            return [], []
        base = json.load(open(BASE, encoding='utf-8'))
    md_now, ours, translated = md_english(md), mod_keys(), pack_keys()
    files, lines = set(base['files']), base['lines']
    changed, new = [], []
    for k, (r, v) in sorted(md_now.items()):
        if k in ours:
            continue
        if k in lines:
            if k in translated and fingerprint(v) != lines[k]:
                changed.append((k, r, v))
        elif r in files and k not in translated and v.strip():
            new.append((k, r, v))
    return changed, new


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', nargs='?', default='status', choices=['status', 'snapshot'])
    ap.add_argument('--md', default=DEFAULT_MD)
    ap.add_argument('--all', action='store_true', help='list every line, not just the first 40')
    a = ap.parse_args()
    if not os.path.isdir(a.md):
        sys.exit(f'MD folder not found: {a.md}')

    if a.command == 'snapshot':
        snap = snapshot(a.md)
        with open(BASE, 'w', encoding='utf-8', newline='\n') as out:
            json.dump(snap, out, ensure_ascii=False, indent=0, sort_keys=False)
            out.write('\n')
        print(f"recorded {len(snap['lines'])} MD lines in {len(snap['files'])} files (MD {snap['md_version']})")
        return

    if not os.path.exists(BASE):
        sys.exit('no tools/md_loc_base.json yet: run python tools/md_loc.py snapshot')
    base = json.load(open(BASE, encoding='utf-8'))
    changed, new = compare(a.md, base)
    limit = None if a.all else 40
    print(f"MD {md_version(a.md)} against the base recorded for MD {base['md_version']}")
    for title, items in (('MD changed the English of translated lines', changed),
                         ('New MD lines with no translation', new)):
        print(f'\n{title}: {len(items)}')
        for k, r, v in items[:limit]:
            print(f'  {k}  ({r})\n      {v[:160]}')
        if limit and len(items) > limit:
            print(f'  ... {len(items) - limit} more (--all)')
    if not changed and not new:
        print('\nall translations in step with MD')
    sys.exit(1 if changed or new else 0)


if __name__ == '__main__':
    main()
