#!/usr/bin/env python3
"""UserPromptSubmit: when a prompt asks for something to be made or says something is wrong, remind
the model to ground the work in the primary source, not in a description of it.

It fires only on prompts with a production verb (make, build, write, fix, redo...) or a challenge
(why is, that's not, wrong). Conversational prompts get nothing, so it costs no tokens there.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

TRIGGER = re.compile(
    r"make|build|generat|creat|writ|draft|design|redo|regenerat|rewrit|update|replac|fix|"
    r"new (?:image|prompt|copy|card|version)|why (?:is|does|are)|what is the point|"
    r"that'?s not|that is not|wrong|look(?:s)? like",
    re.I)

RULE = (
    "Ground the work in the primary source, not in a description of it. Before producing anything\n"
    "about a subject, open the subject itself in this session.\n"
    "\n"
    "A description is never the brief: alt text, a caption, a filename, a tagline, a slug, a\n"
    "constant grepped from a template or stylesheet, the old artifact being replaced, a previous\n"
    "brief, or memory.\n"
    "\n"
    "The primary source is the brief: the live page fetched now, the repo and its README, the file\n"
    "on disk, computed styles on the running page, or a real browser screenshot.\n"
    "\n"
    "When replacing an artifact, work from what it was supposed to show, not from a paraphrase of\n"
    "the old one. When writing \"real\", \"live\", \"actual\" or \"as rendered\", the value must come\n"
    "from something fetched in this session, and the reply says where. A value read from a source\n"
    "file is what the source declares, not what the page does."
)


def main():
    ev = G.read_event()
    if not ev:
        return
    prompt = str(ev.get("prompt") or "")
    if not TRIGGER.search(prompt):
        return
    G.context(RULE, "UserPromptSubmit")


if __name__ == "__main__":
    main()
