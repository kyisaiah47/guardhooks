#!/usr/bin/env python3
"""Fixtures for no-purchase-suggestion-stop.py. Each case runs the real hook against a real
transcript file. The positives and negatives come from the pattern list itself, so the list's own
examples are pinned."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T, HOOKS  # noqa: E402

with open(os.path.join(HOOKS, "lib", "purchase_patterns.json"), encoding="utf-8") as fh:
    SPEC = json.load(fh)

t = T("no-purchase-suggestion-stop")

for s in SPEC["reply"]["positives"]:
    t.stop("block offer: %s" % s, "example.dev is available for $9.99/yr. " + s, True)
for s in SPEC["reply"]["negatives"]:
    t.stop("pass report: %s" % s, s, False)

t.stop("block: do you want me to buy", "Do you want me to purchase the plan?", True)
t.stop("pass: offer quoted in backticks", "The banned line is `Want me to grab the domain?` and it is gone.", False)
t.stop("pass: offer in a blockquote", "> I'll buy it once you confirm.\n\nThat sentence is now blocked.", False)
t.stop("pass: offer in a long double-quoted span", 'The hook refuses "Want me to grab the domain?" in replies.', False)
t.stop("pass: an ordinary reply", "The build passes and the hook is registered.", False)
t.stop("a second pass in the same turn never blocks", "Want me to grab the domain?", False, active=True)

err = t.stop("block message tells the model what to write", "Want me to grab the domain?", True)
t.check("block message says to delete the offer", "Delete the offer" in err and "by hand" in err)

t.done()
