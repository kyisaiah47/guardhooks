#!/usr/bin/env python3
"""UserPromptSubmit: put the stat-eyebrow rule in front of the model when a prompt asks for design
work.

The PreToolUse hook catches the card when it is written. This hook reaches the model earlier, at
the point where a layout is chosen. It fires only when the prompt mentions design words such as
layout, cover, card, slide, deck, dashboard or chart, so it costs nothing on other prompts.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import stat_eyebrow as S
except Exception:
    sys.exit(0)

DESIGN_WORDS = re.compile(
    r"design|layout|cover|card|banner|poster|slide|deck|thumbnail|hero|tile|frame|variant|option|"
    r"mockup|style|register|typograph|composition|brainstorm|moodboard|figma|video|film|motion|"
    r"graphic|infographic|chart|dashboard",
    re.I)


def main():
    ev = G.read_event()
    if not ev:
        return
    prompt = str(ev.get("prompt") or "")
    if not prompt.strip() or not DESIGN_WORDS.search(prompt):
        return
    G.context("Design rule for this request.\n\n" + S.RULE_TEXT +
              "\nNever generate this card, propose it, or list it as an option.")


if __name__ == "__main__":
    main()
