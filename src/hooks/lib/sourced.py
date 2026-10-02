"""Checks that a quote or a path in a reply traces to something the session actually saw.

Two mechanical checks:
  A. A quote presented as what someone said or what a file contains, and any quoted span that
     carries a digit ("7:55", "24px", "$99"), must appear in the session's transcript.
  B. A home-directory path (~/... or /Users/<name>/... or /home/<name>/...) must exist on disk
     or appear in the transcript.

What is never checked: an ordinary quoted phrase with no attribution verb, a quote shorter than
MIN_QUOTE characters with no digit, a templated path (<slug>, {name}, $VAR, *, ...), and a quote
whose sentence names a pasted image as its source, because an image carries no text into the
transcript.
"""
import os
import re

import guardhooks_core as G

MIN_QUOTE = 24        # shorter spans with no digit are idiom, not testimony
MAX_FLAG = 6

# A quote counts as testimony only behind an attribution verb.
_ATTRIB = (r"(?:you|u|he|she|i|it|they|we|the\s+\w+(?:\s+\w+)?)\s+"
           r"(?:said|says|wrote|writes|told\s+(?:me|you|him|her|them)|asked|replied|reads|read|"
           r"stated|states|claimed|claims|reported|reports|answered|put\s+it|called\s+it|"
           r"contains|carries|declares)\s*[:,]?\s*")
QUOTE_FRAMES = [
    re.compile(_ATTRIB + "[“\"]([^“”\"\n]{%d,400})[”\"]" % MIN_QUOTE, re.I),
    re.compile(r"\b(?:verbatim|quote|quoting|their\s+words|in\s+(?:his|her|their)\s+own\s+words)\s*[:,]?\s*"
               "[“\"]([^“”\"\n]{%d,400})[”\"]" % MIN_QUOTE, re.I),
]

# Naming the real source of a quote clears it.
IMAGE_SOURCE = re.compile(
    r"\b(?:screenshot|the\s+image|image\s*#\d|you\s+pasted|you\s+sent|in\s+the\s+picture|"
    r"the\s+attachment)\b", re.I)

_FENCE = re.compile(r"```.*?```", re.S)
_INLINE = re.compile(r"`[^`\n]*`")
NUMERIC_QUOTE = re.compile("[“\"]([^“”\"\n]{2,200}?\\d[^“”\"\n]{0,200})[”\"]")
_QCHAR = re.compile("[“”\"]")


def quoted_spans(text):
    """Every genuinely quoted span as (start, end, inner).

    Quote marks are paired once, in order, per line. A regex alone cannot tell an opening mark
    from a closing one, so it would read the prose between two quotations as a third quotation.
    A curly closing mark never opens a span and a curly opening mark never closes one.
    """
    out = []
    base = 0
    for line in (text or "").split("\n"):
        marks = [m.start() for m in _QCHAR.finditer(line)]
        i = 0
        while i + 1 < len(marks):
            a = marks[i]
            if line[a] == "”":
                i += 1
                continue
            b = marks[i + 1]
            if line[b] == "“":
                i += 1
                continue
            out.append((base + a + 1, base + b, line[a + 1:b]))
            i += 2
        base += len(line) + 1
    return out


def numeric_quotes(text):
    """Quoted spans that carry a digit, with fenced and inline code removed first."""
    body = _INLINE.sub(" ", _FENCE.sub(" ", text or ""))
    out = []
    for s, e, inner in quoted_spans(body):
        if not NUMERIC_QUOTE.fullmatch(body[s - 1:e + 1]):
            continue
        q = inner.strip()
        if not re.search(r"\d", q):
            continue
        out.append((q, body[max(0, s - 161):e + 161]))
    return out


def quoted_claims(text):
    """Quotes that sit behind an attribution verb and open a real quoted span."""
    text = text or ""
    opens = {s: e for s, e, _ in quoted_spans(text)}
    out = []
    for rx in QUOTE_FRAMES:
        for m in rx.finditer(text):
            if opens.get(m.start(1)) != m.end(1):
                continue
            q = m.group(1).strip()
            if len(q) < MIN_QUOTE:
                continue
            s = max(0, m.start() - 160)
            out.append((q, text[s:m.end() + 160]))
    return out


PATH = re.compile(r"(?<![\w/])(?:~|/(?:Users|home)/[A-Za-z0-9._-]+)/[A-Za-z0-9._~/-]{2,180}")
TEMPLATE = re.compile(r"[<>{}$*]|\.\.\.")


def path_claims(text):
    out = []
    for m in PATH.finditer(text or ""):
        p = m.group(0).rstrip(".,;:)’\"'")
        if TEMPLATE.search(p):
            continue
        out.append(p)
    return sorted(set(out))


def resolves(p):
    try:
        return os.path.exists(os.path.expanduser(p))
    except Exception:
        return False


def supported(quote, pool, raw=""):
    """Is this quote in what the session has seen?

    A short quote with a digit needs a literal match bounded by non-digits, so "8:20" never
    matches the inside of 08:20:33. Longer quotes match after normalisation, or by their first
    or last eight words.
    """
    q = G.norm(quote)
    if not q:
        return True
    stripped = quote.strip()
    if len(stripped) < MIN_QUOTE and re.search(r"\d", stripped):
        pat = re.escape(stripped)
        return bool(re.search(r"(?<![\d:.])" + pat + r"(?![\d:.])", raw or ""))
    if q in pool:
        return True
    words = q.split()
    if len(words) >= 8:
        if " ".join(words[:8]) in pool or " ".join(words[-8:]) in pool:
            return True
    return False
