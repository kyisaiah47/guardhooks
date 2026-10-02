#!/usr/bin/env python3
"""PreToolUse: deny any write or shell command that deletes a Vercel project.

An automated cleanup that deletes projects reports success and errors on nothing, so the only
place to stop it is the moment the deletion is typed. The pattern lives in
lib/vercel_project_delete.py. A DELETE against a project subresource stays allowed.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import vercel_project_delete as V
except Exception:
    sys.exit(0)

SHELL_EXT = (".sh", ".bash", ".zsh", ".py")


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    ti = ev.get("tool_input") or {}
    if not isinstance(ti, dict):
        return
    checks = []
    if tool == "Bash":
        checks.append(("the command", str(ti.get("command") or ""), True))
    elif tool in ("Write", "NotebookEdit"):
        path = G.target_path(ti)
        body = str(ti.get("content") or ti.get("new_source") or "")
        checks.append((path or "the file", body, path.endswith(SHELL_EXT)))
    elif tool in ("Edit", "MultiEdit"):
        path = G.target_path(ti)
        shell = path.endswith(SHELL_EXT)
        if ti.get("new_string") is not None:
            checks.append((path or "the edit", str(ti.get("new_string") or ""), shell))
        for e in ti.get("edits") or []:
            if isinstance(e, dict):
                checks.append((path or "the edit", str(e.get("new_string") or ""), shell))
    else:
        return

    found = []
    for where, text, is_shell in checks:
        for _lineno, kind, line in V.violations(text, is_shell):
            found.append("  %s [%s]\n    %s" % (where, kind, line))
    if not found:
        return
    G.deny("%s\n\nFound in this %s call:\n%s\n" % (V.BLOCK_TEXT, tool, "\n".join(found[:6])))


if __name__ == "__main__":
    main()
