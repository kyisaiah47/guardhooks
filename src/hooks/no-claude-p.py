#!/usr/bin/env python3
"""PreToolUse: deny writing or running a headless Claude CLI call.

The rule: every headless model call goes through the CLI the user chose, named in the
GUARDHOOKS_HEADLESS_CLI environment variable. A write is scanned after the quoting carve, so a rule
or a doc may quote the command. A Bash command is scanned raw. Only new text is scanned. The ban's
own files are exempt.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import claude_p as C
except Exception:
    sys.exit(0)


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    ti = ev.get("tool_input") or {}
    if tool == "Bash":
        text = str(ti.get("command") or "")
        if C.is_self(text):
            return
        scanned = text
        where = "this Bash command"
    elif tool in G.WRITE_TOOLS:
        path = G.target_path(ti)
        if not path or C.is_self(path):
            return
        scanned = C.prose_of(G.new_text(ti))
        where = os.path.basename(path) or "this write"
    else:
        return
    if not scanned.strip():
        return
    hits = C.findings(scanned)
    if not hits:
        return
    lines = []
    for h in hits[:4]:
        lines.append("  - %s found: %s" % (h["slug"], h["fragment"]))
        lines.append("    fix: %s" % h["fix"])
    G.deny(C.block_text() + "\n\nFound in %s:\n%s\n" % (where, "\n".join(lines)))


if __name__ == "__main__":
    main()
