"""Convert Turkey's 'fire as soon as the trigger holds' polled events into triggered events.

Each converted event gets is_triggered_only, loses its mean_time_to_happen, and records a country
flag in a new immediate block. A generated scripted effect, run once a day for TUR from
on_daily_TUR, evaluates the same triggers and fires the events, so the engine no longer polls
749 events for every country.

usage: python convert_events.py <mod dir>    (rewrites events/*.txt, writes the dispatcher)
"""
import glob, json, os, re, sys

MOD = sys.argv[1]
ROWS = json.load(open(os.path.join(os.environ['TEMP'], 'events_class.json')))
CONVERT = {r['id'] for r in ROWS if r['cat'].startswith('convert')}
DISPATCH_FILE = os.path.join(MOD, 'common', 'scripted_effects', 'TUR_polled_event_dispatcher.txt')


def scan(t):
    """yield (index, char) for structural braces only: skips comments and quoted strings"""
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c == '#':
            j = t.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == '"':
            j = t.find('"', i + 1)
            i = n if j < 0 else j + 1
            continue
        if c in '{}':
            yield i, c
        i += 1


def block_end(t, open_idx):
    d = 0
    for i, c in scan(t[open_idx:]):
        d += 1 if c == '{' else -1
        if d == 0:
            return open_idx + i
    raise ValueError('unbalanced block at %d' % open_idx)


def top_blocks(t):
    """(key, start, open_brace, end) for depth-0 'key = {' blocks"""
    out, d, pending = [], 0, None
    for i, c in scan(t):
        if c == '{':
            if d == 0:
                m = re.search(r'([\w.]+)\s*=\s*$', t[max(0, i - 80):i])
                key = m.group(1) if m else None
                start = i - len(t[max(0, i - 80):i]) + m.start() if m else i
                pending = (key, start, i)
            d += 1
        else:
            d -= 1
            if d == 0 and pending:
                out.append(pending + (i,))
                pending = None
    return out


def child_block(t, start, end, key):
    """first depth-1 'key = {' block inside t[start:end] -> (key_start, open, close) or None"""
    d = 0
    for i, c in scan(t[start:end + 1]):
        i += start
        if c == '{':
            if d == 1:
                m = re.search(r'\b' + key + r'\s*=\s*$', t[max(start, i - 60):i])
                if m:
                    return (i - len(t[max(start, i - 60):i]) + m.start(), i, block_end(t, i))
            d += 1
        else:
            d -= 1
    return None


def strip_comments(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = s.find('"', i + 1)
            j = n if j < 0 else j + 1
            out.append(s[i:j]); i = j; continue
        if c == '#':
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        out.append(c); i += 1
    return ''.join(out)


def flag_for(eid):
    return 'TUR_evf_' + re.sub(r'\W', '_', eid)


def convert_file(path, dispatch):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    t = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in t else '\n'
    done = 0
    # walk events from the end so earlier offsets stay valid
    for key, start, ob, cb in reversed(top_blocks(t)):
        if key != 'country_event':
            continue
        body = t[ob:cb + 1]
        m = re.search(r'\bid\s*=\s*([\w.\-]+)', strip_comments(body))
        if not m or m.group(1) not in CONVERT:
            continue
        eid = m.group(1)
        trig = child_block(t, ob, cb, 'trigger')
        mtth = child_block(t, ob, cb, 'mean_time_to_happen')
        if trig is None:
            raise ValueError(eid + ': no trigger')
        imm = child_block(t, ob, cb, 'immediate')
        trigger_body = strip_comments(t[trig[1] + 1:trig[2]])
        dispatch.append((path, eid, trigger_body))
        ev = t[start:cb + 1]
        off = start
        # 0. existing immediate: record the flag first thing inside it (done before the
        #    other edits so its offsets are still valid; it always sits after id/mtth? not
        #    guaranteed, so apply it on the original text and shift the rest)
        if imm:
            ins = ' set_country_flag = ' + flag_for(eid)
            t = t[:imm[1] + 1] + ins + t[imm[1] + 1:]
            cb += len(ins)
            if trig[0] > imm[1]: trig = (trig[0] + len(ins), trig[1] + len(ins), trig[2] + len(ins))
            if mtth and mtth[0] > imm[1]: mtth = (mtth[0] + len(ins), mtth[1] + len(ins), mtth[2] + len(ins))
            ev = t[start:cb + 1]
        # 1. drop mean_time_to_happen (with its line)
        if mtth:
            ls = t.rfind('\n', 0, mtth[0]) + 1
            le = t.find('\n', mtth[2])
            le = len(t) if le < 0 else le + 1
            if t[ls:mtth[0]].strip() == '' and t[mtth[2] + 1:le].strip() == '':
                ev = ev[:ls - off] + ev[le - off:]
            else:
                ev = ev[:mtth[0] - off] + ev[mtth[2] + 1 - off:]
        # 2. is_triggered_only right after the id line
        idm = re.search(r'(?m)^([ \t]*)id\s*=\s*' + re.escape(eid) + r'[ \t]*\r?\n', ev)
        indent = idm.group(1) or '\t'
        ev = ev[:idm.end()] + indent + 'is_triggered_only = yes' + nl + ev[idm.end():]
        # 3. immediate block before the first option (or before the closing brace)
        opt = re.search(r'(?m)^([ \t]*)option\s*=\s*\{', ev)
        line = indent + 'immediate = { set_country_flag = ' + flag_for(eid) + ' }' + nl
        if imm:
            pass
        elif opt:
            ev = ev[:opt.start()] + line + ev[opt.start():]
        else:
            ev = ev[:ev.rstrip().rfind('}')] + line + '}'
        t = t[:start] + ev + t[cb + 1:]
        done += 1
    open(path, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8'))
    return done


def write_dispatcher(dispatch):
    order = {r['id']: n for n, r in enumerate(ROWS)}
    lines = [
        '# Generated by convert_events.py: fires Turkey events that used to be polled every day for every',
        '# country (mean_time_to_happen = 1 day). Runs once a day for TUR from on_daily_TUR.',
        '# Do not edit by hand: change the event\'s trigger and regenerate, or edit both together.',
        'TUR_dispatch_polled_events = {',
    ]
    for path, eid, body in sorted(dispatch, key=lambda d: order[d[1]]):
        inner = '\n'.join('\t\t\t' + l.strip() for l in body.strip().splitlines() if l.strip())
        lines += [
            '\tif = {  # ' + eid + '  (' + os.path.basename(path) + ')',
            '\t\tlimit = {',
            '\t\t\tNOT = { has_country_flag = ' + flag_for(eid) + ' }',
            inner,
            '\t\t}',
            '\t\tcountry_event = ' + eid,
            '\t}',
        ]
    lines.append('}')
    # no BOM: the parser rejects a BOM in front of a leading comment in scripted_effects
    open(DISPATCH_FILE, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    dispatch = []
    total = 0
    for f in sorted(glob.glob(os.path.join(MOD, 'events', '*.txt'))):
        n = convert_file(f, dispatch)
        if n:
            print(os.path.basename(f), n)
        total += n
    write_dispatcher(dispatch)
    print('converted', total, 'of', len(CONVERT), '-> dispatcher', os.path.relpath(DISPATCH_FILE, MOD))
