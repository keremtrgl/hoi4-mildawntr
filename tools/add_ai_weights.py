#!/usr/bin/env python3
"""Give every focus in the MD_TUR_* trees that has no ai_will_do a base weight.

Weights are relative and only affect the AI. Hand-written ai_will_do blocks are left alone, so the script can
be re-run after adding focuses.

    python tools/add_ai_weights.py          # report what would change
    python tools/add_ai_weights.py apply
"""
import collections
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DEVELOP = 14   # economy and research first
BASE_SECURITY = 10  # then stability and armed forces
BASE_DEFAULT = 8    # the base Millennium Dawn uses in its own trees
BASE_WAR = 2        # wars and annexations last

DEVELOP = {'FOCUS_FILTER_INDUSTRY', 'FOCUS_FILTER_RESEARCH', 'FOCUS_FILTER_TURKISH_ECONOMY',
           'FOCUS_FILTER_EXPENDITURE', 'FOCUS_FILTER_RESOURCE'}
SECURITY = {'FOCUS_FILTER_STABILITY', 'FOCUS_FILTER_TURKISH_ARMS', 'FOCUS_FILTER_MANPOWER',
            'FOCUS_FILTER_NAVY', 'FOCUS_FILTER_AIRCRAFT'}
WAR_EFFECT = re.compile(r'\bdeclare_war_on\b|\bcreate_wargoal\b|\bannex_country\b')


def focus_spans(text):
    """(start, end) of each top-level focus block; end is the index just past its closing brace."""
    for m in re.finditer(r'(?m)^[ \t]*focus[ \t]*=[ \t]*\{', text):
        i, depth = m.end(), 1
        while depth and i < len(text):
            c = text[i]
            if c == '#':
                while i < len(text) and text[i] != '\n':
                    i += 1
                continue
            depth += (c == '{') - (c == '}')
            i += 1
        if depth:
            raise ValueError(f'unclosed focus block at offset {m.start()}')
        yield m.start(), i


def weight(code):
    filters = re.search(r'search_filters\s*=\s*\{([^}]*)\}', code)
    filters = set(filters.group(1).split()) if filters else set()
    if WAR_EFFECT.search(code) or 'FOCUS_FILTER_ANNEXATION' in filters:
        return BASE_WAR
    if filters & DEVELOP:
        return BASE_DEVELOP
    if filters & SECURITY:
        return BASE_SECURITY
    return BASE_DEFAULT


def process(text):
    spans = []
    for start, end in focus_spans(text):
        code = re.sub(r'#.*', '', text[start:end])
        if 'ai_will_do' not in code:
            spans.append((start, end, weight(code)))
    for start, end, base in reversed(spans):
        close = end - 1
        body_end = close
        while body_end > start and text[body_end - 1] in ' \t':
            body_end -= 1
        indent = re.match(r'[ \t]*', text[start:]).group()
        if text[body_end - 1] == '\n':
            line = f'{indent}\tai_will_do = {{ base = {base} }}\r\n'
            text = text[:body_end] + line + text[body_end:]
        else:
            text = text[:close] + f'ai_will_do = {{ base = {base} }} ' + text[close:]
    return text, collections.Counter(b for _, _, b in spans)


def main():
    apply = sys.argv[1:] == ['apply']
    total = collections.Counter()
    for path in sorted(glob.glob(os.path.join(ROOT, 'common', 'national_focus', 'MD_TUR_*.txt'))):
        raw = open(path, 'rb').read().decode('utf-8')
        new, counts = process(raw)
        total += counts
        print(f'{os.path.basename(path):24} {sum(counts.values()):4}')
        if apply and new != raw:
            open(path, 'wb').write(new.encode('utf-8'))
    print(f'total {sum(total.values())}: ' + ', '.join(f'base {k}: {v}' for k, v in sorted(total.items())))


if __name__ == '__main__':
    main()
