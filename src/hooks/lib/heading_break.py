"""Hard line breaks inside a headline, defined once. Read by no-heading-break.py.

A headline is one string and the box wraps it. When an author joins an array of hand-written lines
with <br>, the breaks land wherever the author guessed the box would run out of room, which is
often mid-phrase or mid-word once the font or the width changes.

A violation needs both parts:
  (a) a .join() whose separator is a <br> tag, or a string literal that already contains one; and
  (b) a headline context: the value is named headline, title or heading, or the break sits inside
      an <h1>...</h1> span.
Body copy, footers, table cells and address blocks are never headlines and never match.
"""
import re

BLOCK_TEXT = (
    "Hard line breaks inside a headline are not allowed.\n"
    "\n"
    "A headline is one string and the box wraps it. Do not join an array of hand-written lines\n"
    "with <br>, and do not place a <br> inside a headline or title string. Pass one string and let\n"
    "CSS decide where it breaks, for example with `text-wrap: balance`.\n"
)

HEADLINE_TOKEN_JOIN = re.compile(
    r"\b(headline|title|heading|headtext)\w*\s*\.\s*join\(\s*[`'\"]\s*<br\s*/?>\s*[`'\"]",
    re.I)
HEADLINE_KEY_BR = re.compile(
    r"\b(headline|title|heading)\s*[:=]\s*[`'\"][^`'\"]*<br\s*/?>", re.I)
H1_BLOCK = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
JOIN_BR = re.compile(r"\.join\(\s*[`'\"]\s*<br\s*/?>\s*[`'\"]\s*\)", re.I)

BAN_MARKER = re.compile(r"no-heading-break|heading_break|Hard line breaks inside a headline", re.I)
SKIP_PATH = re.compile(r"/node_modules/|/vendor/|\.min\.[jt]s$")


def find(content, path=""):
    """Return a list of reasons, empty when clean."""
    if not content or SKIP_PATH.search(path or ""):
        return []
    if BAN_MARKER.search(content):
        return []
    reasons = []
    for m in HEADLINE_TOKEN_JOIN.finditer(content):
        line = content.count("\n", 0, m.start()) + 1
        reasons.append("line %d: `%s` joins an array of hand-written lines with <br> into a headline"
                       % (line, m.group(0).strip()))
    for m in HEADLINE_KEY_BR.finditer(content):
        line = content.count("\n", 0, m.start()) + 1
        reasons.append("line %d: a headline or title string carries a hard <br> break: `%s`"
                       % (line, m.group(0)[:80].strip()))
    for hm in H1_BLOCK.finditer(content):
        block = hm.group(1)
        if re.search(r"<br\s*/?>", block, re.I) or JOIN_BR.search(block):
            line = content.count("\n", 0, hm.start()) + 1
            reasons.append("line %d: an <h1> block carries a hard <br> break or a <br>-joined array" % line)
    return reasons
