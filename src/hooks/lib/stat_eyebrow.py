"""The stat-eyebrow card, defined once. Read by no-stat-eyebrow.py (PreToolUse) and
no-stat-eyebrow-inject.py (UserPromptSubmit).

The banned register: a number set as the dominant type element on a surface, paired with a small
all-caps letter-spaced label above or below it. The signature is the size jump between a giant
numeral and a tiny tracked caption. It is the most common template move in generated slides, cards
and dashboards, and it reads as a template.

Not banned: a small tracked uppercase label on its own (section headers, chips, rails), a number
inside a sentence or a headline, and tables, ledgers and charts where figures sit at body size.
"""
import re

# 1. an oversized type declaration
BIG_PX = re.compile(r'font-?[sS]ize\s*[:=]\s*[\'"]?\s*(\d{2,4})\s*px', re.M)
BIG_REM = re.compile(r'font-?[sS]ize\s*[:=]\s*[\'"]?\s*(\d+(?:\.\d+)?)\s*rem', re.M)
BIG_PT = 90          # px at which a figure stops being type and becomes a stat slab
BIG_REM_PT = 5.5

# 2. a small all-caps letter-spaced label
TRACKED = re.compile(r'letter-?[sS]pacing\s*[:=]\s*[\'"]?\s*\.?(\d+(?:\.\d+)?)\s*em', re.M)
UPPER = re.compile(r'text-?[tT]ransform\s*[:=]\s*[\'"]?\s*uppercase', re.M)

# 3. the big element is a figure, not a headline
FIGURE_TOKEN = re.compile(
    r'\b(fig|figure|stat|stats|statistic|number|numeral|num|metric|kpi|count|counter|'
    r'tally|value|amount|score|pct|percent|percentage|digit|tabular-nums|bignum|big-number)\b',
    re.I)
EYEBROW_TOKEN = re.compile(r'\b(eyebrow|kicker|overline|rail|superhead|supertitle)\b', re.I)

# 4. the same register asked for in words: a brief, a prompt, a style menu
PROSE = [
    (re.compile(r'\b(big|large|huge|giant|oversized|enormous|massive)\s+(number|numeral|stat|statistic|figure|metric|digit)', re.I),
     'asks for an oversized number as the dominant element'),
    (re.compile(r'\b(stat|statistic|metric|kpi|number)[- ]?(card|tile|hero|block|slab|panel)\b', re.I),
     'names the stat card or metric tile'),
    (re.compile(r'\beyebrow\b[^.\n]{0,60}\b(number|numeral|stat|figure|metric)\b', re.I),
     'pairs an eyebrow with a figure'),
    (re.compile(r'\b(number|numeral|stat|figure|metric)\b[^.\n]{0,60}\beyebrow\b', re.I),
     'pairs a figure with an eyebrow'),
    (re.compile(r'\bcount[- ]?up\b[^.\n]{0,40}\b(stat|number|figure|metric)\b', re.I),
     'asks for a count-up stat'),
    (re.compile(r'\bextreme\s+(type\s+)?(size\s+)?contrast\b[^.\n]{0,60}\b(number|numeral|figure|stat)\b', re.I),
     'asks for extreme size contrast built on a figure'),
]

# Text whose job is to describe the ban is not an instance of it.
BAN_MARKER = re.compile(
    r'no-stat-eyebrow|stat_eyebrow|stat-eyebrow (card|register|ban)|banned stat|'
    r'never (use|ship|generate)[^\n]{0,60}(stat|eyebrow)',
    re.I)


def _max_font_px(text):
    hits = [int(m.group(1)) for m in BIG_PX.finditer(text)]
    hits += [int(float(m.group(1)) * 16) for m in BIG_REM.finditer(text)
             if float(m.group(1)) >= BIG_REM_PT]
    return max(hits) if hits else 0


def find(text, path=''):
    """Return a list of reasons this content ships the banned register. Empty means clean."""
    if not text:
        return []
    if BAN_MARKER.search(text):
        return []
    out = []

    big = _max_font_px(text)
    if big >= BIG_PT:
        tracked = []
        for m in TRACKED.finditer(text):
            raw = m.group(0).split(':')[-1].split('=')[-1].strip().strip('\'"')
            try:
                tracked.append(abs(float(raw.replace('em', '').strip())))
            except ValueError:
                pass
        wide = [t for t in tracked if t >= 0.08]
        if wide and UPPER.search(text) and (FIGURE_TOKEN.search(text) or EYEBROW_TOKEN.search(text)):
            out.append('a %dpx type element sits beside an all-caps label tracked at %.2fem. '
                       'That is the stat-eyebrow pairing.' % (big, max(wide)))

    for rx, why in PROSE:
        m = rx.search(text)
        if m:
            frag = ' '.join(m.group(0).split())[:90]
            out.append('"%s" %s.' % (frag, why))

    return out


RULE_TEXT = (
    "The stat-eyebrow card is not allowed on any surface.\n"
    "\n"
    "The banned register has two parts together:\n"
    "  1. a number, figure or metric is the dominant type element (the largest on the surface, or\n"
    "     about 1.6 times its headline or more), and\n"
    "  2. it is paired with a small all-caps label (an eyebrow, kicker or rail) directly above or\n"
    "     below it, tracked at 0.08em or more.\n"
    "\n"
    "It applies to video, cards, covers, decks, PDFs, landing pages, prompts and option lists.\n"
    "\n"
    "Lead with a sentence instead. The headline or claim is the largest element on the surface. A\n"
    "figure that earns a place sits at body size inside the sentence.\n"
    "\n"
    "Not banned: a small tracked uppercase label on its own, a number inside a headline or a\n"
    "sentence, and tables, ledgers and charts where figures sit at body size.\n"
)

BLOCK_TEXT = RULE_TEXT
