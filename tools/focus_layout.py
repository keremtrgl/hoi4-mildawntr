"""Where every focus ends up on screen, per focus tree.

The shared branches (Turan, Cyprus, EU/USoE) are moved by `offset` blocks that test the tree's
`*_FOCUS_LOCATION` country flag, so a position is only known once the tree and its flag are. This module
places every focus the way the game does and reports focuses left of the screen edge (x < 0), focuses on
the same square, and places that load a tree without setting the flag its layout expects.

    python tools/focus_layout.py            report
    python tools/focus_layout.py --boxes    also print the bounding box and shared roots of every tree

No game files are needed.
"""
import collections, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = re.compile(r'\s+|#[^\n]*|"(?:[^"\\\n]|\\.)*"?|[{}]|[<>=]+|[^\s{}=<>#"]+')
FLAG = re.compile(r'^\w+_FOCUS_LOCATION$')
CLEAR = 'TUR_clear_focus_location'


class Block(list):
    """items are (key, value, line); value is a string or a Block; key is None for bare values"""
    line = 0


def parse(text):
    tokens, line = [], 1
    for m in TOKEN.finditer(text):
        s = m.group(0)
        if not s.isspace() and s[0] != '#':
            tokens.append((s, line))
        line += s.count('\n')
    pos = 0

    def block(start):
        nonlocal pos
        out = Block()
        out.line = start
        while pos < len(tokens):
            s, at = tokens[pos]
            if s == '}':
                pos += 1
                return out
            if s == '{':
                pos += 1
                out.append((None, block(at), at))
            elif pos + 2 < len(tokens) and tokens[pos + 1][0][0] in '<>=' and s[0] not in '<>=':
                value, value_at = tokens[pos + 2]
                pos += 3
                out.append((s, block(value_at) if value == '{' else value, at))
            else:
                pos += 1
                out.append((None, s, at))
        return out
    return block(1)


def read(path):
    with open(path, encoding='utf-8-sig', errors='replace') as source:
        return source.read()


def values(block, key):
    return [v for k, v, _ in block if k == key]


def walk(block):
    for item in block:
        yield item
        if isinstance(item[1], Block):
            yield from walk(item[1])


def linked(focus, key):
    return [v for group in values(focus, key) if isinstance(group, Block) for k, v, _ in group if k == 'focus']


def holds(trigger, flag):
    """a trigger block of an offset, for Turkey holding exactly one location flag (or none)"""
    for k, v, _ in trigger:
        if k in ('tag', 'original_tag'):
            ok = v == 'TUR'
        elif k == 'has_country_flag':
            ok = v == flag
        elif k == 'NOT':
            ok = not any(holds([item], flag) for item in v)
        elif k == 'OR':
            ok = any(holds([item], flag) for item in v)
        elif k == 'AND':
            ok = holds(v, flag)
        else:
            ok = False
        if not ok:
            return False
    return True


class Trees:
    def __init__(self, root=ROOT):
        self.root = root
        self.trees, self.shared = {}, {}          # tree id -> (file, block, {focus id: block}); id -> (file, block)
        for path in sorted(glob.glob(os.path.join(root, 'common', 'national_focus', '*.txt'))):
            name = os.path.basename(path)
            for k, v, _ in parse(read(path)):
                if k == 'focus_tree':
                    own = {values(f, 'id')[0]: f for fk, f, _ in v if fk == 'focus'}
                    self.trees[values(v, 'id')[0]] = (name, v, own)
                elif k == 'shared_focus' and isinstance(v, Block):
                    self.shared[values(v, 'id')[0]] = (name, v)
        self.children = collections.defaultdict(set)
        for fid, (_, f) in self.shared.items():
            for parent in linked(f, 'prerequisite'):
                self.children[parent].add(fid)
        self.sites = self.load_sites()

    def load_sites(self):
        """[(tree, file, line, flags set next to the load, clears the old flags first?)]"""
        sites = []
        for pattern in ('common/**/*.txt', 'events/*.txt', 'history/**/*.txt'):
            for path in sorted(glob.glob(os.path.join(self.root, pattern), recursive=True)):
                name = os.path.relpath(path, self.root).replace(os.sep, '/')

                def visit(block):
                    for k, v, line in block:
                        if k == 'load_focus_tree':
                            tree = v if not isinstance(v, Block) else values(v, 'tree')[0]
                            flags = sorted({fv for fk, fv, _ in walk(block)
                                            if fk == 'set_country_flag' and isinstance(fv, str) and FLAG.match(fv)})
                            sites.append((tree, name, line, flags, any(fk == CLEAR for fk, _, _ in block)))
                        if isinstance(v, Block):
                            visit(v)
                visit(parse(read(path)))
        return sites

    def flag_of(self, tree):
        """the location flag a tree is laid out for: the one most of its load sites set"""
        seen = collections.Counter(f for t, _, _, flags, _ in self.sites if t == tree for f in flags)
        return seen.most_common(1)[0][0] if seen else None

    def members(self, tree):
        _, block, own = self.trees[tree]
        shared, todo = set(), [r for r in values(block, 'shared_focus') if isinstance(r, str)]
        while todo:
            fid = todo.pop()
            if fid in self.shared and fid not in shared:
                shared.add(fid)
                todo += self.children[fid]
        return own, shared

    def positions(self, tree, flag):
        own, shared = self.members(tree)
        done = {}

        def place(fid, trail=()):
            if fid in done:
                return done[fid]
            focus = own.get(fid) or self.shared[fid][1]
            x, y = int(values(focus, 'x')[0]), int(values(focus, 'y')[0])
            for offset in values(focus, 'offset'):
                trigger = values(offset, 'trigger')
                if not trigger or holds(trigger[0], flag):
                    x, y = x + int(values(offset, 'x')[0]), y + int(values(offset, 'y')[0])
            anchor = values(focus, 'relative_position_id')
            if anchor and anchor[0] not in trail and (anchor[0] in own or anchor[0] in self.shared):
                ax, ay = place(anchor[0], trail + (fid,))
                x, y = x + ax, y + ay
            done[fid] = (x, y)
            return done[fid]
        return {fid: place(fid) for fid in list(own) + sorted(shared)}


def problems(trees=None):
    """(off screen, overlapping, load sites with a wrong or missing flag) as lists of report lines"""
    trees = trees or Trees()
    off, over, flags = [], [], []
    expected = {t: trees.flag_of(t) for t in trees.trees}
    for tree in sorted(trees.trees):
        name = trees.trees[tree][0]
        placed = trees.positions(tree, expected[tree])
        left = sorted((xy, fid) for fid, xy in placed.items() if xy[0] < 0 or xy[1] < 0)
        if left:
            off.append(f'{name} ({tree}): {len(left)} focuses, e.g. ' +
                       ', '.join(f'{fid} at {xy[0]},{xy[1]}' for xy, fid in left[:4]))
        squares = collections.defaultdict(list)
        for fid, xy in placed.items():
            squares[xy].append(fid)
        over += [f'{name} ({tree}): {" and ".join(sorted(ids))} at {xy[0]},{xy[1]}'
                 for xy, ids in sorted(squares.items()) if len(ids) > 1]
    for tree, name, line, set_flags, clears in trees.sites:
        want = expected.get(tree)
        if tree not in trees.trees:
            continue
        if want and want not in set_flags:
            flags.append(f'{name}:{line}: loads {tree} without setting {want}')
        elif len(set_flags) > 1:
            flags.append(f'{name}:{line}: loads {tree} and sets {", ".join(set_flags)}')
        if not clears:
            flags.append(f'{name}:{line}: loads {tree} without {CLEAR} (an old location flag would move the shared branches)')
    return off, over, flags


def main():
    trees = Trees()
    if '--boxes' in sys.argv:
        for tree in sorted(trees.trees):
            flag = trees.flag_of(tree)
            placed = trees.positions(tree, flag)
            xs, ys = [p[0] for p in placed.values()], [p[1] for p in placed.values()]
            roots = {r: placed[r] for r in values(trees.trees[tree][1], 'shared_focus') if r in placed}
            print(f'{tree:16} {flag or "-":24} {len(placed):4} focuses  x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}  {roots}')
    off, over, flags = problems(trees)
    for title, items in (('Focuses left of or above the screen', off), ('Focuses on the same square', over),
                         ('Tree loads with a wrong location flag', flags)):
        print(f'{title}: {len(items)}')
        for item in items:
            print('   ' + item)
    sys.exit(1 if off or over or flags else 0)


if __name__ == '__main__':
    main()
