#!/usr/bin/env python3
"""UserPromptSubmit: when a prompt asks for something to look like, match, or use the same style
as an artifact that already exists, add a short rule on how to match it.

Reading the reference is not the same as reproducing it. The usual failure copies the reference's
measurements and pours a different content model into them, so the numbers match and the result
looks nothing like the reference.

The patterns tolerate common typos of "style", because a hurried prompt is when this matters most.
The hook stays silent on any prompt that does not ask for a likeness.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

STYLE = r"styl|stlye|styel|sytle|ttlye|stle"

SAMENESS = re.compile(
    r"(same|exact|identical|matching)[^.!?]{0,30}(%s|look|format|layout|design|card)" % STYLE, re.I)
COMPARISON = re.compile(
    r"(mak|make|made|makes)[^.!?]{0,20}look[^.!?]{0,20}(like|same)"
    r"|look(s|ed)?[^.!?]{0,12}(more )?like (the|our|this|that|these|those)"
    r"|similar to|just like|match (the|our|this|that)|same as (the|our)"
    r"|the (%s)[a-z]* that"
    r"|like (the|our) [a-z-]+ (card|cards|video|videos|clip|clips|page|pages|deck|film|films|post|posts)"
    % STYLE, re.I)

RULE = """This request asks for something to match an artifact that already exists. Reading the reference is not enough. The output has to be in the reference's style. Do these three things in order before showing anything.

1. Open the reference's own rendered output in this turn. Use the actual pixels: the shipped clip, the published page or the exported image. Do not work from a config file, a renderer's source, alt text, an earlier summary or memory. If the reference is a video, pull real frames from it.

2. Reproduce its content model, not only its geometry. For every slot in the reference, ask what kind of thing goes there: a sentence or a figure, a full clause or a fragment, two elements or five. Copying the spacing and font sizes while keeping a different content model gives matching measurements and a result that looks nothing like the reference.

3. Put the reference and the output side by side in the deliverable, at the same scale, and look at the comparison yourself before handing it over.

If a reviewer rejects one element, go back to the reference and re-match the whole thing. Do not patch only the element they named."""


def main():
    ev = G.read_event()
    if not ev:
        return
    prompt = str(ev.get("prompt") or "")
    if not prompt.strip():
        return
    if SAMENESS.search(prompt) or COMPARISON.search(prompt):
        G.context(RULE)


if __name__ == "__main__":
    main()
