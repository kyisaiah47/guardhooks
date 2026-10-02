#!/usr/bin/env python3
"""PreToolUse on every tool: deny anything that completes a purchase.

A purchase can arrive as an MCP tool call, a shell command or a browser checkout, so this hook is
registered on the "*" matcher. The allowed price and availability reads are checked first, so a
price lookup is never caught. A file that only names a registrar command is documentation and is
not blocked. The pattern list lives in lib/purchase_patterns.json.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    SPEC = G.load_json("purchase_patterns.json")
except Exception:
    sys.exit(0)


def refuse(what, found, fix):
    G.deny(SPEC["block_text"] + "\n\nFound: %s\n  %s\n  fix: %s\n" % (what, found, fix))


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = str(ev.get("tool_name") or "")
    ti = ev.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}

    # 1. a purchase-shaped tool name. The allowed reads are checked first.
    bare = tool.rsplit("__", 1)[-1]
    allowed = set(SPEC["allowed"]["tools"])
    if bare in allowed or tool in allowed:
        return
    for p in SPEC["tool_names"]:
        if re.search(p["re"], tool, re.I) or re.search(p["re"], bare, re.I):
            refuse("a purchase-shaped tool call", tool, p["fix"])

    # 2. a purchase-shaped shell command
    if tool == "Bash":
        command = str(ti.get("command") or "")
        if any(k in command for k in SPEC["self_paths"]):
            return
        for p in SPEC["shell"]:
            m = re.search(p["re"], command, re.I)
            if m:
                refuse("a command that completes a purchase", m.group(0)[:160], p["fix"])


if __name__ == "__main__":
    main()
