"""The reading-measure cap on content, defined once. Read by no-reading-measure-cap.py.

A reading measure (about 50 to 75 characters) is real typography. Applied inside a column that is
already bounded by the page's own shell or grid, it adds a second, narrower right edge and leaves a
dead band of white space between the content and whatever sits beside it.

Flagged in a stylesheet or component file:
  - max-width: var(--measure), var(--prose), var(--reading), var(--readable) or var(--copy-width);
  - max-width between 60ch and 85ch;
  - max-width between 550px and 759px when the file also has a prose-like selector such as .prose,
    .copy, .lede, .body, .doc or .article.

Not flagged: a page's own outer shell or grid cap, a modal's max-width, max-width: 100% on media.
"""
import re

MEASURE_VAR = re.compile(
    r'max-width\s*:\s*var\(\s*--(measure|prose|reading|readable|copy-width)\b', re.I)
MEASURE_CH = re.compile(r'max-width\s*:\s*(6[0-9]|7[0-9]|8[0-5])ch\b', re.I)
MEASURE_PX = re.compile(r'max-width\s*:\s*(5[5-9]\d|6\d\d|7[0-5]\d)px\b', re.I)
PROSE_SELECTOR = re.compile(r'\.(doc|prose|copy|body|lede|article|content|note)\b', re.I)
STYLE_EXT = ('.css', '.scss', '.sass', '.less', '.tsx', '.ts', '.jsx')

BLOCK_TEXT = (
    "A reading-measure width cap on content is not allowed here.\n"
    "\n"
    "Content fills its column. A second, narrower cap inside a column that the page already bounds\n"
    "leaves a dead band of white space beside the content.\n"
    "\n"
    "Set the width once, on the page shell or the grid track. A page-level shell cap, a modal's\n"
    "max-width and max-width: 100% on media are fine.\n"
)


def find(content, path):
    if not content or not (path or '').lower().endswith(STYLE_EXT):
        return []
    reasons = []
    for m in MEASURE_VAR.finditer(content):
        reasons.append('a reading-measure custom property capping content width: `%s`' % m.group(0))
    for m in MEASURE_CH.finditer(content):
        reasons.append('a reading-measure ch cap on content: `%s`' % m.group(0))
    if PROSE_SELECTOR.search(content):
        for m in MEASURE_PX.finditer(content):
            reasons.append('a reading-measure px cap on prose content: `%s`' % m.group(0))
    seen, out = set(), []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out[:8]
