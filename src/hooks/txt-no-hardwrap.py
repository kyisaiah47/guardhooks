#!/usr/bin/env python3
"""PreToolUse: deny a write to a .txt file that hard-wraps a paragraph.

A .txt deliverable is usually pasted somewhere: an email, a form field, a profile box. Hard line
breaks travel with the paste, and the reader has to re-flow every one by hand.

Flagged: two consecutive non-blank lines where the first is 45 characters or longer. That is the
shape of a wrapped paragraph. A short label line above a chunk, a sign-off, a list of short items
and a whole paragraph on one line followed by a blank line all pass.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

MIN_LONG = 45
SKIP = re.compile(r"node_modules|/\.git/|/\.venv/|/dist/|/build/")


def find(content):
    lines = content.split("\n")
    for i in range(len(lines) - 1):
        this, nxt = lines[i].rstrip(), lines[i + 1].strip()
        if len(this) >= MIN_LONG and nxt:
            return i, this, nxt
    return None


def main():
    ev = G.read_event()
    if not ev:
        return
    if (ev.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
        return
    ti = ev.get("tool_input") or {}
    path = G.target_path(ti)
    if not path.endswith(".txt") or SKIP.search(path):
        return
    content = G.new_text(ti)
    if not content:
        return
    hit = find(content)
    if not hit:
        return
    i, this, nxt = hit
    G.deny(
        "This .txt file has a hard-wrapped paragraph.\n"
        "\n"
        "Line %d is %d characters long and line %d continues the same paragraph:\n"
        "  %d: %s...\n"
        "  %d: %s...\n"
        "\n"
        "Write each paragraph as one unwrapped line and separate paragraphs with a blank line.\n"
        "Short label lines and sign-offs are fine. Only a long line followed by more text fails.\n"
        % (i + 1, len(this), i + 2, i + 1, this[:72], i + 2, nxt[:72]))


if __name__ == "__main__":
    main()
