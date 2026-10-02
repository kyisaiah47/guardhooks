#!/usr/bin/env python3
"""PreToolUse on the Workflow tool: deny every call.

A request for thorough research is a request for a thorough answer. It is not consent to start a
multi-agent run, which can spend a very large number of tokens before anyone sees a result. This
hook refuses the Workflow tool outright. To allow it again, remove the hook.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

MESSAGE = (
    "The Workflow tool is blocked by the block-workflow-fanout hook.\n"
    "\n"
    "A request for deep or thorough research asks for a thorough answer. It does not authorize a\n"
    "multi-agent run.\n"
    "\n"
    "Do this instead, in the main conversation:\n"
    "  1. Read the primary source yourself: the docs, the API, the repo.\n"
    "  2. Run a few targeted searches or fetches on the questions that change the answer.\n"
    "  3. Write the answer out in full.\n"
    "\n"
    "If the task cannot be done that way, stop and tell the user what a multi-agent run would\n"
    "cost (agent count and rough token cost) and wait for an explicit yes.\n"
)


def main():
    ev = G.read_event()
    if not ev:
        return
    if (ev.get("tool_name") or "") != "Workflow":
        return
    G.deny(MESSAGE)


if __name__ == "__main__":
    main()
