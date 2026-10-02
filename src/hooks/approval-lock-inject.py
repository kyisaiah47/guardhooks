#!/usr/bin/env python3
"""UserPromptSubmit: when a prompt asks to deploy, publish, upload, embed or use an approved
artifact, remind the model that approval locks the exact artifact.

An approved image, card or layout is the final input, not a visual reference. Deploying it is
not a chance for a new design pass. The reminder appears only on prompts with those action words.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

ACTION = re.compile(
    r"\b(?:arm|deploy|publish|upload|embed|ship|wire(?:\s+it)?|use\s+(?:it|that|the\s+approved))\b", re.I)


def main():
    ev = G.read_event()
    if not ev:
        return
    if not ACTION.search(str(ev.get("prompt") or "")):
        return
    G.context(
        "Approval lock: a request to deploy, publish or use an approved artifact does not reopen it.\n\n"
        "Before you change code or assets, find the exact approved source in the transcript or the approved preview.\n"
        "Use those exact bytes, with the exact crop, dimensions, placement and CSS that were approved.\n"
        "If a preview was inline (for example a data URI), host the same bytes.\n"
        "Do not generate, substitute, resize, crop or recompose it to make it fit.\n"
        "Do not make nearby visual changes while you deploy it.\n"
        "If the approved source cannot be found, or cannot be delivered unchanged, stop and ask one plain question first."
    )


if __name__ == "__main__":
    main()
