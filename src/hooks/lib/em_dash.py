"""The em dash ban, defined once. Read by no-em-dash.py (PreToolUse) and no-em-dash-stop.py (Stop).

Banned:
  U+2014 EM DASH, U+2013 EN DASH, U+2015 HORIZONTAL BAR and U+2212 MINUS SIGN.
  ' -- ' used as a dash in prose.
  Spellings that name the character instead of typing it: \\u2014, &mdash;, &#8212;, chr(0x2014).

Not banned:
  A hyphen. A CLI flag such as --force. The shell's ' -- ' argument separator. Text the model only
  reads. Text already in a file outside the new text. A grep for the character. A sed or tr that
  deletes it.

The quoting carve: in prose, fenced code blocks, inline `backtick` spans and '>' blockquotes are
stripped before the scan. A source that really carries a dash can be quoted byte for byte there.
"""
import re

EM = "\u2014"
EN = "\u2013"
BAR = "\u2015"
MINUS = "\u2212"

GLYPHS = [
    (EM, "U+2014 EM DASH"),
    (EN, "U+2013 EN DASH"),
    (BAR, "U+2015 HORIZONTAL BAR"),
    (MINUS, "U+2212 MINUS SIGN"),
]
GLYPH_RE = re.compile("[" + EM + EN + BAR + MINUS + "]")

# The character named instead of typed. Without these the ban is one chr() call away from useless.
LAUNDER = re.compile(
    r"\\u201[345]|\\U0000201[345]|\\x\{201[345]\}|&mdash;|&ndash;|&#8211;|&#8212;|"
    r"&#x201[34];|chr\(\s*0x201[345]\s*\)|chr\(\s*821[12]\s*\)|"
    r"\\N\{EM DASH\}|\\N\{EN DASH\}",
    re.I)

# ' -- ' with a space on each side and a word after it is a dash in prose. A CLI flag (--force),
# a decrement (i--) and `npm test -- --watch` do not match.
DOUBLE_HYPHEN_PROSE = re.compile(r"(?<=\S)\s--\s(?=[A-Za-z(\"'])")

FENCE = re.compile(r"```.*?```", re.S)
FENCE_OPEN = re.compile(r"```.*\Z", re.S)
INLINE = re.compile(r"`[^`\n]*`")
BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)


def prose_of(text):
    """Strip quoted material so only the writer's own sentences remain."""
    t = FENCE.sub(" ", text or "")
    t = FENCE_OPEN.sub(" ", t)
    t = INLINE.sub(" ", t)
    t = BLOCKQUOTE.sub(" ", t)
    return t


def _context(text, idx, width=64):
    s = max(0, idx - width)
    return " ".join(text[s:idx + width].replace("\n", " ").split())


def scan(text, prose=True, allow_double_hyphen=False):
    """Return [(label, context), ...]. An empty list means clean.

    prose=True    strip fences, inline code and blockquotes first (replies, .md, .txt).
    prose=False   scan the raw text (a shell command, source code).
    allow_double_hyphen  set for shell and code, where ' -- ' is a real separator.
    """
    if not text:
        return []
    body = prose_of(text) if prose else text
    out = []
    for m in GLYPH_RE.finditer(body):
        name = next(n for g, n in GLYPHS if g == m.group(0))
        out.append((name, _context(body, m.start())))
    for m in LAUNDER.finditer(body):
        out.append(("the dash spelled instead of typed (%s)" % m.group(0), _context(body, m.start())))
    if prose and not allow_double_hyphen:
        for m in DOUBLE_HYPHEN_PROSE.finditer(body):
            out.append(("' -- ' used as a dash", _context(body, m.start())))
    return out


BLOCK_TEXT = (
    "Em dashes are not allowed in any output.\n"
    "\n"
    "Banned: U+2014 (em dash), U+2013 (en dash), U+2015 (horizontal bar), U+2212 (minus sign),\n"
    "' -- ' used as a dash, and any spelling that names the character instead of typing it\n"
    "(\\u2014, &mdash;, &#8212;, chr(0x2014)).\n"
    "\n"
    "Write one of these instead:\n"
    "  a period     start a new sentence. This is right most of the time.\n"
    "  a comma      for a short aside.\n"
    "  a colon      before an explanation.\n"
    "  parentheses  for a real aside.\n"
    "  a hyphen     only between numbers in a range: 30-50%, 2020-2024.\n"
    "\n"
    "To quote a source that really contains one, put it in a fenced code block, an inline\n"
    "`backtick` span or a '>' blockquote. Quoted material is not scanned.\n"
)
