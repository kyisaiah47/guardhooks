#!/usr/bin/env python3
"""PreToolUse: deny a write where one CSS rule declares both a background fill and a ch or em
width cap. The pattern lives in lib/half_width.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import half_width as H
except Exception:
    sys.exit(0)

SELF = ("/lib/half_width", "no-half-width-block")


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
    reasons = H.find(G.new_text(ti), path)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    G.deny("%s\nFound in %s:\n%s\n" % (H.BLOCK_TEXT, os.path.basename(path) or "this write", why))


if __name__ == "__main__":
    main()
