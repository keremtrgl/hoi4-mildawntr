"""Check written focus descriptions and apply them.

out/dNNN.txt lines:  <index> ||| <English description> ||| <Turkish description>

    python build.py check [dNNN]      validate (all written batches or one)
    python build.py apply <mod dir>   write *_desc keys into the mod's English localisation and the Turkish pack
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, 'groups.json'), encoding='utf-8'))


def load(only=None):
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, 'out', 'd*.txt'))):
        if only and not os.path.basename(p).startswith(only):
            continue
        for ln, l in enumerate(open(p, encoding='utf-8').read().split('\n'), 1):
            if not l.strip():
                continue
            parts = l.split(' ||| ')
            if len(parts) != 3:
                print(f'BAD LINE {os.path.basename(p)}:{ln}: {l[:80]}')
                continue
            out[int(parts[0])] = (parts[1].strip(), parts[2].strip())
    return out


def check(only=None):
    d = load(only)
    names = [only] if only else sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(HERE, 'out', 'd*.txt')))
    bad = 0
    for name in names:
        ids = [int(l.split(' ||| ')[0]) for l in open(os.path.join(HERE, 'batches', name + '.txt'), encoding='utf-8') if l.strip()]
        miss = [i for i in ids if i not in d]
        if miss:
            print(name, 'missing', miss[:10]); bad += len(miss)
    for i, (en, tr) in d.items():
        for lang, s in (('en', en), ('tr', tr)):
            if '"' in s or '§' in s or '\\' in s or '$' in s or '[' in s:
                print(f'{i} {lang}: forbidden character'); bad += 1
            w = len(s.split())
            if w < (8 if lang == 'en' else 6) or w > 70:  # Turkish is agglutinative: fewer, longer words
                print(f'{i} {lang}: {w} words'); bad += 1
        if re.search(r'[ğışĞİŞ]', en):  # letters outside Latin-1 that English fonts may lack; ü ö ç in names are fine
            print(f'{i} en: Turkish letters in English text'); bad += 1
        if not re.search(r'[çğışöüÇĞİŞÖÜ]', tr) and len(tr.split()) > 12:
            print(f'{i} tr: no Turkish letters (wrong column?)'); bad += 1
    print(f'written {len(d)} / {len(G)}, problems {bad}')
    return bad


def apply(mod):
    d = load()
    want = {}
    for i, (en, tr) in d.items():
        for fid in G[i]['ids']:
            want[fid] = (en, tr)
    key = re.compile(r'^(\s*)([^#\s:"][^:\s]*):(\d*)\s*"(.*)"(\s*)$')

    def rewrite(path, text_of, name_files):
        raw = open(path, 'rb').read()
        bom, crlf = raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw
        lines = raw.decode('utf-8-sig').replace('\r\n', '\n').split('\n')
        present, out, n = set(), [], 0
        for l in lines:
            mm = key.match(l)
            if mm and mm.group(2).endswith('_desc') and mm.group(2)[:-5] in want:
                fid = mm.group(2)[:-5]
                present.add(fid)
                if not mm.group(4).strip():
                    l = f'{mm.group(1)}{mm.group(2)}:{mm.group(3) or 0} "{text_of(want[fid])}"'; n += 1
            out.append(l)
        # descriptions with no key yet: add right after the focus name line in the file that has the name
        final = []
        for l in out:
            final.append(l)
            mm = key.match(l)
            if mm and mm.group(2) in want and mm.group(2) not in present and name_files:
                final.append(f'{mm.group(1)}{mm.group(2)}_desc:0 "{text_of(want[mm.group(2)])}"'); n += 1
                present.add(mm.group(2))
        t = '\n'.join(final)
        if crlf:
            t = t.replace('\n', '\r\n')
        open(path, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8'))
        return n

    en_n = sum(rewrite(p, lambda v: v[0], True) for p in glob.glob(os.path.join(mod, 'localisation', 'english', '**', '*.yml'), recursive=True))
    tr_n = sum(rewrite(p, lambda v: v[1], True) for p in glob.glob(os.path.join(mod, 'turkish_pack', 'localisation', 'english', 'replace', '*.yml')))
    print('english descriptions written', en_n, '| turkish', tr_n)


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        sys.exit(1 if check(sys.argv[2] if len(sys.argv) > 2 else None) else 0)
    if sys.argv[1] == 'apply':
        apply(sys.argv[2])
