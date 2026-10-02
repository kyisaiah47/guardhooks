#!/usr/bin/env python3
"""Fixtures for approval-lock-inject.py. The reminder appears only on deploy and publish words."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("approval-lock-inject")

ctx = t.prompt("deploy", "looks good, deploy it", True)
t.check("the reminder says to use the exact bytes", "exact bytes" in ctx, ctx[:300])
t.check("the reminder says to ask when it cannot be delivered unchanged", "ask one plain question" in ctx, ctx[:500])
t.prompt("publish", "publish the approved card to the blog", True)
t.prompt("embed", "embed the banner in the email", True)
t.prompt("use the approved", "use the approved hero on the landing page", True)
t.prompt("upload", "upload the cover to the store listing", True)

t.prompt("a question", "what does the banner say?", False)
t.prompt("a design request", "try three new layouts for the pricing card", False)
t.prompt("a word that only contains an action word", "the army alarm was loud", False)

p = t.run("approval-lock-inject.py", {})
t.check("an empty event exits 0 silently", p.returncode == 0 and not p.stdout.strip())

t.done()
