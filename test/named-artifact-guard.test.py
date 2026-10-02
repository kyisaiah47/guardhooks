#!/usr/bin/env python3
"""Fixtures for named-artifact-guard.py. The reminder appears only when a prompt names existing inputs."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("named-artifact-guard")

ctx = t.prompt("numbered picks plus 'with those'",
               "run bg-remove on 2 and 3 (try to get 3 to drop the motion blur) and render the video with those replacing",
               True)
t.check("the reminder says to use the named thing", "Use the named thing" in ctx, ctx[:200])
t.check("the reminder names the first-sentence disclosure", "first sentence" in ctx, ctx[:400])
t.prompt("a literal file name", "put hero-v2.png on the landing page", True)
t.prompt("the ones I picked", "use the ones I picked for the cover", True)
t.prompt("the originals", "go back to the original images", True)
t.prompt("in place of", "use the new logo in place of the old mark", True)
t.prompt("the second one", "the second one looks right, ship that", True)

t.prompt("an ordinary question", "why is the build slow today?", False)
t.prompt("a request for something new", "write a short summary of the release", False)
t.prompt("an empty prompt", "", False)

p = t.run("named-artifact-guard.py", {"no": "prompt"})
t.check("an event with no prompt exits 0 silently", p.returncode == 0 and not p.stdout.strip())

# a user's own pattern file in the config dir extends the list
os.makedirs(os.path.join(t.config, "guardhooks"), exist_ok=True)
with open(os.path.join(t.config, "guardhooks", "named-artifact-patterns.txt"), "w") as fh:
    fh.write("# my own\n\\bthe blue draft\\b\n")
t.prompt("a user pattern from the config dir", "finish the blue draft please", True)

t.done()
