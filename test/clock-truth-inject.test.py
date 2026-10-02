#!/usr/bin/env python3
"""Fixtures for clock-truth-inject.py. The hook must inject the real local time on every prompt."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("clock-truth-inject")

today = datetime.now().astimezone().strftime("%Y-%m-%d")
ctx = t.prompt("injects on an ordinary prompt", "what is left to do on the build?", True, contains=today)
t.check("the injection tells the model to run date again", "run `date` again" in ctx, ctx[:300])
t.check("the injection says the reading goes stale", "stale" in ctx, ctx[:300])
t.prompt("injects even on an empty prompt", "", True)

p = t.run("clock-truth-inject.py", {"not": "a prompt event"})
t.check("an odd event still exits 0", p.returncode == 0, p.stderr[:200])
p = t.run("clock-truth-inject.py", {})
t.check("an empty event still exits 0", p.returncode == 0, p.stderr[:200])

t.done()
