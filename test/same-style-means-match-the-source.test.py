#!/usr/bin/env python3
"""Fixtures for same-style-means-match-the-source.py. Each case runs the real hook with a
UserPromptSubmit event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("same-style-means-match-the-source")

# must inject
t.prompt("same style as the existing cards", "use the same style as the onboarding cards", True,
         contains="content model")
t.prompt("a word wedged between same and style", "just do the same exact style please", True)
t.prompt("a typo of style", "I asked for the same stlye", True)
t.prompt("make it look like", "make the summary card look like our launch video cards", True)
t.prompt("similar to", "build a pricing page similar to the docs page", True)
t.prompt("match the", "match the header on the marketing site", True)
t.prompt("like our clips", "cut it like our tiktok clips", True)

# must stay silent
t.prompt("an unrelated request", "add pagination to the users endpoint", False)
t.prompt("a style word with no sameness", "write a style guide for error messages", False)
t.prompt("an empty prompt", "", False)

ctx = t.prompt("context says to put them side by side", "same layout as the old report", True)
t.check("context says side by side", "side by side" in ctx)
t.check("context says to open the rendered output", "rendered output" in ctx)

t.done()
