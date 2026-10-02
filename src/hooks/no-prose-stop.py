#!/usr/bin/env python3
"""Stop: block a chat reply that puts a caption or a label where a sentence belongs.

The companion to no-prose.py, which covers files and shell commands. Only the patterns flagged
`reply: true` in prose_patterns.json apply here: a caption in front of a link, and a label alone on
a line followed by prose. The subset is small on purpose, because a guard that fires on ordinary
engineering replies gets switched off.

Fenced code, inline `backtick` spans, '>' blockquotes and long double-quoted spans are stripped
before the scan. A URL becomes the token <url>, so a caption in front of a link can be seen.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import prose as P
except Exception:
    sys.exit(0)


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    hits = P.scan_reply(reply)
    if not hits:
        return
    out = [P.BLOCK_TEXT, "", "In the reply you just wrote:"]
    for h in hits[:5]:
        fam = P.FAMILIES[str(h["family"])]
        out.append("  - %s (family %s: %s)" % (h["slug"], h["family"], fam["title"]))
        out.append("    what: %s" % fam["what"])
        out.append("    found: %s" % h["sentence"][:200])
        out.append("    fix: %s" % h["fix"])
        out.append("")
    out.append("Rewrite the reply with each of them gone. Ask who reads the sentence and what they")
    out.append("need from it. Write that as one plain sentence with a subject and a verb.")
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
