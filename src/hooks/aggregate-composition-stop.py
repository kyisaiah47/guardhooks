#!/usr/bin/env python3
"""Stop: block a reply that reports a traffic, reach or engagement number without its composition.

A headline number ships with its sample size, its time window and its spread (a median, a
per-person ratio or a breakdown). A ranking across platforms also says which platforms report the
metric. Code blocks are ignored.

Escape: `npx guardhooks declare aggregate-composition-stop "<why this number needs no breakdown>"`
lasts two hours.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import aggregate as A
except Exception:
    sys.exit(0)

HOOK_ID = "aggregate-composition-stop"


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    problems = A.scan(reply)
    if not problems:
        return
    if G.declared(HOOK_ID):
        return
    out = ["The reply reports an aggregate number without its composition. Break it down before "
           "reporting it.", ""]
    for kind, why in problems:
        out.append("  [%s] %s" % (kind, why))
    out += ["",
            "Add to the reply: the sample size (n), the time window or a by-week breakdown, and a",
            "median or per-person ratio. When comparing platforms, say which ones report the metric",
            "and which return nothing.",
            "",
            "If this number really needs no breakdown, record why for two hours with:",
            "    npx guardhooks declare aggregate-composition-stop \"<reason>\""]
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
