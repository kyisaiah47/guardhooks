#!/usr/bin/env python3
"""Fixtures for primary-source-guard.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("primary-source-guard")

t.prompt("a request to make something", "make a new hero image for the pricing page", True,
         contains="primary source")
t.prompt("a request to rewrite copy", "rewrite the landing copy", True)
t.prompt("a request to fix something", "fix the footer spacing", True)
t.prompt("a challenge that something is wrong", "that's not what the product does", True)
t.prompt("a why question", "why is the card blue", True)
t.prompt("a conversational prompt", "thanks, that helps", False)
t.prompt("a plain question with no production verb", "how many tests are there", False)
ctx = t.prompt("the reminder names the description sources", "draft the release notes", True)
t.check("reminder lists what counts as a description", "alt text" in ctx and "filename" in ctx)

t.done()
