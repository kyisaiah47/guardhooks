#!/usr/bin/env python3
"""Fixtures for tone-rule-inject.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("tone-rule-inject")

t.prompt("injects on an ordinary prompt", "fix the login bug", True, contains="never to how")
t.prompt("injects on an angry prompt", "WHY IS THIS STILL BROKEN", True, contains="Swearing is venting")
t.prompt("injects on an empty prompt", "", True)
p = t.run("tone-rule-inject.py", "not json")
t.check("non-JSON input exits 0 silently", p.returncode == 0 and not p.stdout.strip())

t.done()
