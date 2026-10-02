"""A reading measure and a fill never live on the same element. Read by no-half-width-block.py.

A reading measure (about 60 to 70ch) is good typography on bare prose. The defect is putting it on
an element that also paints a background. The fill draws an edge, the measure stops the text short
of that edge, and the empty band inside the box reads as a broken layout.

This file catches the same-element case: one CSS rule block that declares both a fill and a ch or
em width cap. It cannot see a bare ch cap on a paragraph whose filled ancestor sits higher up in
the tree, because that is a fact about the rendered page, not about the file being written.
"""
import re

BLOCK_TEXT = (
    "A reading measure on an element that paints a fill is not allowed.\n"
    "\n"
    "A filled block draws its own edge. A ch or em max-width on that same element stops the text\n"
    "short of that edge, and the empty band reads as a broken box.\n"
    "\n"
    "Fix it one of two ways:\n"
    "  - narrow the block to the measure, so the fill hugs the text; or\n"
    "  - keep the block wide and drop the measure, so the text fills the box.\n"
    "Moving the same cap onto an inner span is not a fix. It renders the same way.\n"
)

_FILL = re.compile(
    r"(?:^|[;{])\s*background(?:-color|-image)?\s*:\s*(?!\s*(?:none|transparent|inherit|initial|unset)\s*[;}])[^;}]+",
    re.I)
_MEASURE = re.compile(r"(?:^|[;{])\s*(max-width|width)\s*:\s*[^;}]*?[\d.]+\s*(ch|em)\b", re.I)
_BLOCK = re.compile(r"([^{}]*)\{([^{}]*)\}", re.S)


def find(content, path=""):
    """Return one reason per rule block that carries both a fill and a ch or em measure."""
    if not content or "{" not in content or ":" not in content:
        return []
    out = []
    for m in _BLOCK.finditer(content):
        sel, body = m.group(1).strip(), m.group(2)
        if sel.startswith("@"):
            continue
        fill = _FILL.search(body)
        meas = _MEASURE.search(body)
        if fill and meas:
            sel1 = " ".join(sel.split())[-70:]
            out.append("%s { ... } declares a fill (%s) and a reading measure (%s)" % (
                sel1,
                fill.group(0).strip().lstrip(";{").strip()[:46],
                meas.group(0).strip().lstrip(";{").strip()[:40]))
    return out
