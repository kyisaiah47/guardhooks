#!/usr/bin/env python3
"""UserPromptSubmit: when the user asks what a subagent is doing, remind the model to measure the
agent's state with its tools instead of narrating the brief it wrote.

A brief describes planned work. Repeating it back reads like a status report and is wrong as soon
as the agent finished, stalled or did something else.
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
    r"agent.{0,30}(?:status|doing|running|stuck|hung|done|finished|progress|going|still)"
    r"|(?:status|check|how).{0,30}(?:on|of).{0,20}agent"
    r"|(?:whats?|what.s|hows?|how.s) the agent"
    r"|agent.{0,20}(?:been|for) [0-9]"
    r"|subagent"
    r"|why is it still"
    r"|(?:still|keeps) (?:running|going)"
    r"|is it (?:still )?(?:done|finished|stuck)",
    re.I)

RULE = (
    "You were asked about an agent's state. Measure it. Do not narrate the brief you wrote.\n"
    "\n"
    "Before any sentence about what an agent is doing, how long it has run, or whether it is stuck:\n"
    "  1. Check the agent's status with the agent tools. They are the only authority on status and\n"
    "     elapsed time. A completed agent is completed.\n"
    "  2. To say what it is doing now, read its live progress output or send it a message and ask.\n"
    "     Do not reconstruct its activity from its prompt.\n"
    "  3. Do not time an agent from a file's modification time. A file written when the task was\n"
    "     created is not a sign of activity.\n"
    "  4. If the user says something is still running and your tools say otherwise, the user is\n"
    "     seeing something real. Look for live processes and for servers the agents depend on.\n"
    "  5. If you cannot establish a fact, say so plainly instead of filling it in.\n"
    "\n"
    "Then act on what you found: stop what should stop, restart what died, and report it."
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
