#!/usr/bin/env python3
"""PreToolUse: deny a write or a command that sends already-shipped work back to a generator so it
matches a newer style.

Blocked: a backfill that clears an asset field so the generator redraws it, a loop that re-renders
every existing asset, and a gate that refuses a reused asset.
Never blocked: generating an asset for something that never had one, pointing at a file that
already exists, and retiring an old asset in place so it stops being served.

The patterns live in lib/retro_rerender_patterns.json. In a prose file, fenced code, inline
backtick spans and '>' blockquotes are stripped first, so a doc can quote a banned line. The ban's
own files and rules files are exempt.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    P = G.load_json("retro_rerender_patterns.json")
except Exception:
    sys.exit(0)

SELF = ("no-retro-rerender", "retro_rerender_patterns", "CLAUDE.md", "AGENTS.md")
PROSE_EXT = (".md", ".mdx", ".markdown", ".txt", ".rst")

MESSAGE = """Never re-run already-shipped work so it matches a newer style.

Old work keeps the style it shipped with. New work gets the new style.

Blocked here: %s
Matched: %s

Do this instead: retire the old asset in place. It stops being served and nothing redraws it.
Still allowed: pointing at a file that already exists, and generating an asset for something that
never had one.

To quote one of these lines on purpose in a doc, put it in a fenced code block, an inline backtick
span or a '>' blockquote of a Markdown or text file."""


def scan(text):
    for pat in P.get("code_patterns", []):
        m = re.search(pat, text or "", re.I)
        if m:
            return m.group(0).strip()[:160]
    return None


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    ti = ev.get("tool_input") or {}
    if tool in G.WRITE_TOOLS:
        path = G.target_path(ti)
        if any(k in path for k in SELF):
            return
        body = G.new_text(ti)
        if path.lower().endswith(PROSE_EXT):
            body = G.strip_quoted(body)
        what = "a file that sends already-shipped work back to a generator"
    elif tool == "Bash":
        body = str(ti.get("command") or "")
        if any(k in body for k in SELF):
            return
        what = "a command that re-renders already-shipped work"
    else:
        return
    hit = scan(body)
    if hit:
        G.deny(MESSAGE % (what, hit))


if __name__ == "__main__":
    main()
