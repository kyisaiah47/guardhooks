#!/usr/bin/env python3
"""Fixtures for agent-status-must-be-measured.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("agent-status-must-be-measured")

t.prompt("what is the agent doing", "what's the agent doing right now", True, contains="Measure it")
t.prompt("how is the agent going", "how's the agent", True)
t.prompt("agent running for an hour", "the agent has been running for 1 hr, is it stuck", True)
t.prompt("check on the subagent", "check on the subagent please", True)
t.prompt("why is it still running", "why is it still running", True)
t.prompt("status of the agents", "status of the agents?", True)
t.prompt("an unrelated prompt", "rename the config file", False)
t.prompt("a user agent string is not about an agent's state", "set the user agent header to curl", False)
ctx = t.prompt("the reminder forbids timing from files", "is the agent done", True)
t.check("reminder says not to time an agent from a file", "modification time" in ctx)

t.done()
