#!/usr/bin/env python3
"""Stop: block a chat reply that carries noise, so the model rewrites it.

The companion to no-noise.py, which covers files and shell commands. Only the patterns flagged
`reply: true` in noise_patterns.json apply here. That subset is small on purpose, because a guard
that fires on ordinary engineering replies gets switched off.

Fenced code, inline `backtick` spans, '>' blockquotes, paths and long double-quoted spans are
stripped before the scan. Quoting a phrase is allowed. Writing it in your own sentence is not.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import noise as N
except Exception:
    sys.exit(0)


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    hits = N.scan_reply(reply)
    if not hits:
        return
    out = [N.BLOCK_TEXT, "", "In the reply you just wrote:"]
    for h in hits[:5]:
        out.append("  - %s (family %s: %s)" % (h["slug"], h["family"], N.FAMILIES[str(h["family"])]["title"]))
        out.append("    found: %s" % h["sentence"][:200])
        out.append("    fix: %s" % h["fix"])
        out.append("")
    out.append("Rewrite the reply with each of them gone. Delete the sentence. Do not soften it.")
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
