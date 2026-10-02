#!/usr/bin/env python3
"""Stop: block a reply that offers to buy something, so the model rewrites it.

The companion to no-purchase.py, which covers the tool call and the shell command. A price report
never fires. A sentence that says the user buys, or that the model will not buy, passes. Quoted
material (fenced code, inline backticks, '>' blockquotes and double-quoted spans of twelve
characters or more) is stripped before the scan.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    SPEC = G.load_json("purchase_patterns.json")
except Exception:
    sys.exit(0)

SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def sentence_at(text, index):
    pos = 0
    for s in SENT.split(text):
        end = pos + len(s)
        if pos <= index < end:
            return " ".join(s.split())
        pos = end + 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return " ".join(text[max(0, index - 80):index + 120].split())


def offers(reply):
    t = G.strip_quoted(reply, double_quotes_min=12)
    offer = re.compile(SPEC["reply"]["offer"], re.I)
    neg = re.compile(SPEC["reply"]["negation"], re.I)
    hits = []
    for m in offer.finditer(t):
        sentence = sentence_at(t, m.start())
        if neg.search(sentence):
            continue
        hits.append((m.group(0).strip(), sentence))
    return hits


def main():
    reply = G.stop_reply(G.read_event())
    if not reply.strip():
        return
    hits = offers(reply)
    if not hits:
        return
    out = [SPEC["block_text"], "", "In the reply you just wrote:"]
    for frag, sentence in hits[:4]:
        out.append("  - found: %s" % frag)
        out.append("    in: %s" % sentence[:200])
    out += ["", "Delete the offer. State the name, the price and whether it is available, and stop there."]
    G.block("\n".join(out))


if __name__ == "__main__":
    main()
