#!/usr/bin/env python3
"""Stop: block a reply that contains an em dash, so the model rewrites it.

The companion to no-em-dash.py, which covers files and shell commands. Fenced code, inline
`backtick` spans and '>' blockquotes are stripped before the scan, so quoted material passes.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import em_dash as D
except Exception:
    sys.exit(0)


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    hits = D.scan(reply, prose=True)
    if not hits:
        return
    seen, lines = set(), []
    for label, ctx in hits:
        if (label, ctx) in seen:
            continue
        seen.add((label, ctx))
        lines.append("  - %s in: ...%s..." % (label, ctx))
        if len(lines) >= 6:
            break
    G.block("\n".join([
        D.BLOCK_TEXT,
        "In the reply you just wrote:",
        *lines,
        "",
        "Rewrite the reply with each one replaced. If a flagged span quotes something that really",
        "contains the character, wrap it in backticks or a '>' blockquote.",
    ]))


if __name__ == "__main__":
    main()
