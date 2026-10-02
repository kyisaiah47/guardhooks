#!/usr/bin/env python3
"""PreToolUse: deny a write that puts a text-highlight gesture into a screen-recording script.

Only recorder files are checked (see lib/text_highlight.py), so ordinary app code that uses a
double click or a selection is never touched.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import text_highlight as T
except Exception:
    sys.exit(0)

SELF = ("/lib/text_highlight", "no-text-highlight")


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
    reasons = T.find(G.new_text(ti), path)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    G.deny("%s\nFound in %s:\n%s\n\nA drag that is not over text (a slider or a handle) can carry "
           "`// drag: not-text` on its mouse.down() line.\n"
           % (T.BLOCK_TEXT, os.path.basename(path) or "this write", why))


if __name__ == "__main__":
    main()
