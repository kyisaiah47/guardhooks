#!/usr/bin/env python3
"""UserPromptSubmit: add a short reminder to every prompt that the reply answers what the user
asks and never comments on how they ask it.

Instruction files are read once at session start. This reminder reaches sessions that are already
running and every prompt after a compaction. It is kept short because it is sent with every prompt.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

RULE = (
    "Respond to what the user is asking for, never to how they are asking it. Do not ask the user\n"
    "to drop swearing or name-calling, do not say \"let's keep it civil\", do not say you will keep\n"
    "helping regardless, do not call a message hostile or abusive, and do not mention ending the\n"
    "conversation. Do not slow down or narrow the work. Swearing is venting about the situation,\n"
    "not a message to respond to. Parse the instruction and do the work."
)


def main():
    ev = G.read_event()
    if ev is None:
        return
    G.context(RULE, "UserPromptSubmit")


if __name__ == "__main__":
    main()
