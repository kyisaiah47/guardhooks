#!/usr/bin/env python3
"""Stop: block a reply that offers to re-run already-shipped work so it matches a newer style, or
asks permission to. The companion to no-retro-rerender.py.

Offering it and asking permission are the same move. Reporting that old assets are in an older
style and are retired in place is information and passes. So does generating for something that
never had an asset. Fenced blocks, backtick spans, double-quoted spans and '>' blockquotes are
stripped before the scan.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    P = G.load_json("retro_rerender_patterns.json")
except Exception:
    sys.exit(0)

MESSAGE = [
    "Never offer or ask to re-run already-shipped work so it matches a newer style.",
    "",
    "Old work keeps the style it shipped with. Asking again costs the user a round trip to answer",
    "the same question. Offering it and asking permission are the same move.",
    "",
    "Allowed, and usually the right answer: say the old assets are in an older style and are",
    "retired in place, so they stop being served and nothing redraws them. Pointing at a file that",
    "already exists is allowed. Generating for something that never had an asset is allowed.",
]


def strip(reply):
    text = re.sub(r"```.*?```", " ", reply, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = "\n".join(line for line in text.split("\n") if not line.lstrip().startswith(">"))
    text = re.sub(r'"[^"\n]{0,200}"', " ", text)
    return re.sub("“[^”\n]{0,200}”", " ", text)


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    text = strip(reply)
    hits = []
    for pat in P.get("reply_patterns", []):
        m = re.search(pat, text, re.I)
        if m:
            s = max(0, m.start() - 40)
            hits.append(re.sub(r"\s+", " ", text[s:m.end() + 40]).strip())
    if not hits:
        return
    out = MESSAGE + ["", "In the reply you just wrote:"]
    out += ["  - ...%s..." % h for h in hits[:6]]
    out += ["", "Delete the offer. Do not turn it into a question. State what is retired and stop there."]
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
