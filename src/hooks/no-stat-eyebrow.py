#!/usr/bin/env python3
"""PreToolUse: deny a write that ships the stat-eyebrow card.

The card is a giant number as the dominant type paired with a small all-caps tracked label. The
hook catches it as CSS (an oversized font size beside an uppercase label tracked 0.08em or more)
and as words (a brief or prompt that asks for a big number, a stat card or a figure under an
eyebrow). The pattern lives in lib/stat_eyebrow.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import stat_eyebrow as S
except Exception:
    sys.exit(0)

# The ban's own files are about the ban.
SELF = ("/lib/stat_eyebrow", "no-stat-eyebrow")


def main():
    ev = G.read_event()
    if not ev:
        return
    if (ev.get("tool_name") or "") not in G.WRITE_TOOLS:
        return
    ti = ev.get("tool_input") or {}
    path = G.target_path(ti)
    if any(k in path for k in SELF):
        return
    reasons = S.find(G.new_text(ti), path)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    G.deny("%s\nFound in %s:\n%s\n" % (S.BLOCK_TEXT, os.path.basename(path) or "this write", why))


if __name__ == "__main__":
    main()
