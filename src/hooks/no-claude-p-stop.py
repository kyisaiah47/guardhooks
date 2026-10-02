#!/usr/bin/env python3
"""Stop: block a reply that plans a headless Claude CLI call, so the model rewrites it.

The companion to no-claude-p.py, which covers files and shell commands. A sentence about the ban
(one that says not, never, instead, replaced, or reports an error) passes. Quoted material passes.
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
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    hits = C.reply_hits(reply)
    if not hits:
        return
    name = C.chosen_cli() or C.DEFAULT_CLI
    out = [C.block_text(), "", "In the reply you just wrote:"]
    for h in hits[:4]:
        out.append("  - found: %s" % h["fragment"])
        out.append("    in: %s" % h["sentence"][:200])
    out += ["", "Rewrite the reply with %s named instead." % name,
            "A sentence about the ban passes. A sentence that plans a headless Claude CLI call does not."]
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
