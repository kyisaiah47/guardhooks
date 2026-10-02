#!/usr/bin/env python3
"""Fixtures for block-workflow-fanout.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("block-workflow-fanout")

t.pre("a Workflow call is denied", "Workflow", {"script": "run agents over every file"}, "deny")
t.pre("a Workflow call with an empty input is denied", "Workflow", {}, "deny")
t.pre("another tool is untouched", "Bash", {"command": "ls"}, "allow")
t.pre("the Agent tool is untouched", "Agent", {"prompt": "look at one file"}, "allow")
reason = t.pre("the message names the alternative", "Workflow", {"script": "x"}, "deny")
t.check("deny message tells the model to answer in the main conversation",
        "main conversation" in reason and "explicit yes" in reason)

t.done()
