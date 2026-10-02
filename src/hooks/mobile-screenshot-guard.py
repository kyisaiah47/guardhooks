#!/usr/bin/env python3
"""PreToolUse: deny a Bash, Write, Edit or MultiEdit call that takes a phone-width photo of a site,
or writes code that takes one.

An Edit is judged on the file as it will be after the edit, so a viewport change is read together
with the screenshot and navigation already in the file. An edit that adds no phone width (for
example one that moves a phone width to desktop) is never refused for lines it has not reached.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import mobile_screenshot as M
except Exception:
    sys.exit(0)


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    ti = ev.get("tool_input") or {}
    path = ""
    if tool == "Bash":
        text = str(ti.get("command") or "")
    elif tool in ("Write", "Edit", "MultiEdit"):
        path = G.target_path(ti) or "unnamed"
        if tool == "Write":
            text = str(ti.get("content") or "")
        else:
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except Exception:
                text = ""
            edits = ti.get("edits") if isinstance(ti.get("edits"), list) else [ti]
            added = "\n".join(str((e or {}).get("new_string") or "") for e in edits)
            if not M.phone_hits(added):
                return
            for e in edits:
                old, new = str((e or {}).get("old_string") or ""), str((e or {}).get("new_string") or "")
                if old and old in text:
                    text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
                else:
                    text += "\n" + new
    else:
        return
    reasons = M.find(text, path)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    where = os.path.basename(path) if path else "this command"
    G.deny("%s\nFound in %s:\n%s\n" % (M.BLOCK_TEXT, where, why))


if __name__ == "__main__":
    main()
