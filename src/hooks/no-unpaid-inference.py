#!/usr/bin/env python3
"""PreToolUse: deny any tool call that would spend a paid Anthropic or OpenAI API key outside a
paying customer's request.

A billed token cannot be refunded and a spending call does not fail, so the only place to stop it is
the tool call itself. The patterns live in lib/paid_inference_patterns.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import paid_inference as P
except Exception:
    sys.exit(0)

KEYS = ("command", "url", "urls", "prompt", "query", "text", "value", "description",
        "content", "new_string", "new_source", "code", "script", "body", "action")


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = str(ev.get("tool_name") or "")
    ti = ev.get("tool_input") or {}
    if not isinstance(ti, dict):
        return
    path = G.target_path(ti)
    # A write carries file content, where a fence or a backtick span is documentation.
    # A Bash command or a URL is never documentation, so it is matched raw.
    authored = tool in G.WRITE_TOOLS or bool(path)

    parts = []
    for k in KEYS:
        v = ti.get(k)
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(x) for x in v if isinstance(x, (str, int, float)))
    if isinstance(ti.get("edits"), list):
        parts.extend(str((e or {}).get("new_string") or "") for e in ti["edits"] if isinstance(e, dict))
    # Browser and batch tools carry their payload one level down.
    for k in ("actions", "steps", "batch", "commands"):
        v = ti.get(k)
        if isinstance(v, list):
            parts.append(json.dumps(v))

    blob = "\n".join(parts)
    if not blob.strip():
        return
    reasons = P.find(blob, path, authored=authored)
    if not reasons:
        return
    why = "\n".join("  - %s" % r for r in reasons)
    where = os.path.basename(path) or (tool or "this tool call")
    G.deny("%s\nFound in %s:\n%s\n" % (P.BLOCK_TEXT, where, why))


if __name__ == "__main__":
    main()
