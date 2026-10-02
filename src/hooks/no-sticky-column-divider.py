#!/usr/bin/env python3
"""PreToolUse: deny a write that draws a column divider on a sticky column.

A sticky side rail is only as tall as its own content, and it is usually capped at the viewport.
A border-right on the rail therefore stops where the rail's content ends, while the middle column
runs on. The divider belongs to the grid, not to the sticky column.

Matched: one CSS rule that has position: sticky, a top offset and a left or right border that is
not none or 0. Table cells (th or td in the selector) are exempt, because a sticky table cell is as
tall as its row. In Tailwind: one className with sticky, a top-* utility and border-l or border-r.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

SELF = ("no-sticky-column-divider",)
STYLE_FILE = re.compile(r"\.(css|scss|sass|less|html?|tsx|jsx|ts|js|mjs|cjs|vue|svelte|astro)$")
SIDE_BORDER = re.compile(
    r"border-(?:left|right|inline-start|inline-end)\s*:\s*(?!\s*(?:none|0)\b)[^;}{]*\d|"
    r"border-(?:left|right)-width\s*:\s*(?!0\b)\d")

BLOCK_TEXT = (
    "A column divider drawn on a sticky column stops where that column's content ends.\n"
    "\n"
    "A sticky rail is only as tall as its own content, so its border-right ends there while the\n"
    "middle column runs on. The line belongs to the grid, not to the sticky column.\n"
    "\n"
    "Do one of these instead:\n"
    "  - paint the line on the grid container at full height, for example\n"
    "      .shell { background: linear-gradient(var(--rule), var(--rule)) <rail-width>px 0 / 1px 100% no-repeat; }\n"
    "    and take the border off the sticky rail; or\n"
    "  - let the column stretch (align-self: stretch) with the border on it, and make an inner\n"
    "    wrapper sticky.\n"
)


def find(content):
    reasons = []
    for m in re.finditer(r"([^{}]{1,300})\{([^{}]*)\}", content):
        sel, body = m.group(1).strip(), m.group(2)
        if not re.search(r"position\s*:\s*sticky", body):
            continue
        if not re.search(r"(?<![-\w])top\s*:", body) and not re.search(r"inset-block-start\s*:", body):
            continue
        if not SIDE_BORDER.search(body):
            continue
        if re.search(r"(^|[\s>+~,])(th|td)\b", sel):
            continue
        last = sel.splitlines()[-1].strip() if sel else ""
        reasons.append("%s { position: sticky; top: ...; border-left/right ... }" % last[:80])
    for m in re.finditer(r"className\s*=\s*[{\"'`]([^\"'`}]{0,600})", content):
        cls = m.group(1)
        toks = set(cls.split())
        if ("sticky" in toks and any(t.startswith("top-") for t in toks)
                and any(re.match(r"^border-[lr](-\d+)?$", t) for t in toks)):
            reasons.append('className="%s"' % cls.strip()[:80])
    return reasons


def main():
    ev = G.read_event()
    if not ev:
        return
    if (ev.get("tool_name") or "") not in G.WRITE_TOOLS:
        return
    ti = ev.get("tool_input") or {}
    path = G.target_path(ti)
    if any(k in path for k in SELF) or not STYLE_FILE.search(path):
        return
    reasons = find(G.new_text(ti))
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons[:6])
    G.deny("%s\nFound in %s:\n%s\n" % (BLOCK_TEXT, os.path.basename(path) or "this write", why))


if __name__ == "__main__":
    main()
