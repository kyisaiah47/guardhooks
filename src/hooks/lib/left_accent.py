"""The one-sided accent stripe, defined once. Read by no-left-accent.py.

Banned: a border on one side, 2px or wider, in a visible colour. That is the accent bar, a coloured
tab stuck to one edge of a card, row, callout or bar. It is the most templated move in dashboard UI.
Give the object its identity with a tint or a fill and a hairline on all four sides instead.

Not banned:
  - a 1px border on one side, which is structure (a table divider, a blockquote rule, a separator);
  - a border on all four sides at any weight;
  - a transparent, none, currentColor or 0 one-sided border used to reserve space;
  - a width token with no colour beside it.
Comments are blanked before matching, so a comment that explains the rule never trips it.
"""
import re

SIDE = r'(?:left|right|inline-start|inline-end)'

SHORTHAND = re.compile(r'border-' + SIDE + r'\s*:\s*([^;}\n"\'`]+)', re.I)
LONG_W = re.compile(r'border-' + SIDE + r'-width\s*:\s*([0-9.]+)(px|rem|em)', re.I)
LONG_C = re.compile(r'border-' + SIDE + r'-color\s*:\s*([^;}\n"\'`]+)', re.I)
TW = re.compile(r'\bborder-(?:l|r|s|e)-(2|4|8|\[[^\]]+\])\b')

INVISIBLE = re.compile(r'^(?:transparent|none|initial|inherit|unset|currentcolor|0)$', re.I)
STYLE_WORD = re.compile(r'\b(solid|dashed|dotted|double|groove|ridge|inset|outset)\b', re.I)
LEN = re.compile(r'([0-9.]+)(px|rem|em)')

BLOCK_TEXT = (
    "One-sided accent borders are not allowed.\n"
    "\n"
    "A border 2px or wider on one edge in a visible colour is an accent bar. It makes a surface\n"
    "read as a component library template.\n"
    "\n"
    "Give the object its own colour instead: a tint or a fill, plus a hairline on all four sides,\n"
    "for example `background: <tint>; border: 1px solid <hue>;`.\n"
    "\n"
    "Allowed: a 1px border on one side (a divider or rule), a border on all four sides at any\n"
    "weight, and a transparent one-sided border that reserves space.\n"
)


def _decomment(t):
    """Blank comments before matching, keeping line offsets."""
    out = re.sub(r'/\*[\s\S]*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), t)
    out = re.sub(r'(^|[^:])//[^\n]*',
                 lambda m: m.group(1) + ' ' * (len(m.group(0)) - len(m.group(1))), out)
    out = re.sub(r'^([ \t]*)#[^\n]*',
                 lambda m: m.group(1) + ' ' * (len(m.group(0)) - len(m.group(1))), out, flags=re.M)
    return out


def _px(value, unit):
    try:
        n = float(value)
    except ValueError:
        return None
    return n if unit == 'px' else n * 16.0


def find(content, path=''):
    """Every one-sided accent stripe in `content`. An empty list means clean."""
    txt = _decomment(content or '')
    hits = []

    for m in SHORTHAND.finditer(txt):
        decl = m.group(1).strip()
        w = LEN.search(decl)
        if not w:
            continue
        wide = _px(w.group(1), w.group(2))
        if wide is None or wide < 2:
            continue
        colour = STYLE_WORD.sub('', LEN.sub('', decl, count=1)).strip()
        if not colour or INVISIBLE.match(colour):
            continue
        hits.append('%gpx one-sided border in a visible colour: %s' % (wide, decl))

    colour_set = LONG_C.search(txt)
    if colour_set and not INVISIBLE.match(colour_set.group(1).strip()):
        for m in LONG_W.finditer(txt):
            wide = _px(m.group(1), m.group(2))
            if wide is None or wide < 2:
                continue
            hits.append('%gpx one-sided border-width with a colour set: %s' % (wide, m.group(0)))

    for m in TW.finditer(txt):
        hits.append('Tailwind one-sided accent: %s' % m.group(0))

    return hits
