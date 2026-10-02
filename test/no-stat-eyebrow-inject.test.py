#!/usr/bin/env python3
"""Fixtures for no-stat-eyebrow-inject.py. Each case runs the real hook with a UserPromptSubmit event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-stat-eyebrow-inject")

t.prompt("design a cover", "design a cover for the launch post", True, contains="stat-eyebrow")
t.prompt("a dashboard layout", "build the dashboard layout for the admin page", True, contains="Lead with a sentence")
t.prompt("a slide deck", "make me three slide options for the deck", True)
t.prompt("a thumbnail", "I need a YouTube thumbnail", True)
t.prompt("an infographic", "turn these numbers into an infographic", True)

t.prompt("a refactor prompt stays silent", "rename the parser function and run the tests", False)
t.prompt("a database prompt stays silent", "add an index on users.email", False)
t.prompt("an empty prompt stays silent", "", False)

ctx = t.prompt("context says never to propose it", "brainstorm poster ideas", True)
t.check("context forbids listing it as an option", "list it as an option" in ctx)

t.done()
