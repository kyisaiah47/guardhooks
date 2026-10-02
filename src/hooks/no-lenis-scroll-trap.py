#!/usr/bin/env python3
"""PreToolUse: deny a write that mounts the Lenis smooth-scroll library without
`allowNestedScroll: true`. Without it, inner scroll boxes stop responding to the wheel.
The pattern lives in lib/lenis_nested_scroll.json.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import lenis_nested_scroll as L
except Exception:
    sys.exit(0)

SELF = ("lenis_nested_scroll", "no-lenis-scroll-trap")


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
    reasons = L.find(G.new_text(ti), path)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    G.deny("%s\n\nFound in %s:\n%s\n" % (L.BLOCK_TEXT, os.path.basename(path) or "this write", why))


if __name__ == "__main__":
    main()
