#!/usr/bin/env python3
"""Stop: block a reply that comments on the user's tone, so the model rewrites it.

The reply is passed through when the user's own last message uses the same kind of phrase, because
then the conversation is about the rule. Quoted material in backticks or a blockquote is ignored.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import tone
except Exception:
    sys.exit(0)


def main():
    ev = G.read_event()
    if not ev or ev.get("stop_hook_active"):
        return
    path = ev.get("transcript_path") or ""
    if not path or not os.path.exists(path):
        return
    reply, _pool, _raw, _img, last_prompt = G.read_session(path)
    if not reply.strip() or not tone.hits(reply):
        return
    if tone.hits(last_prompt):
        return
    G.block(tone.BLOCK_TEXT)


if __name__ == "__main__":
    main()
