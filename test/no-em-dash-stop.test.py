#!/usr/bin/env python3
"""Fixtures for no-em-dash-stop.py. Each case runs the real hook against a real transcript file."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

EM = chr(0x2014)
EN = chr(0x2013)

t = T("no-em-dash-stop")

# must block
t.stop("reply has a dash in its own sentence", "The three hooks are registered %s all of them fire." % EM, True)
t.stop("reply has an en dash", "Two jobs %s both on." % EN, True)
t.stop("reply uses ' -- ' as a dash", "The gate is on -- nothing ships.", True)
t.stop("reply spells the dash", "I wrote a literal \\u2014 into the file.", True)

# must pass
t.stop("reply quotes a user in a blockquote", "You said:\n\n> never output an em dash %s ever\n\nDone." % EM, False)
t.stop("reply quotes a file in a fenced block",
       "The file reads:\n\n```\nconst x = 'a %s b';\n```\n\nThat is the only hit." % EM, False)
t.stop("reply quotes a phrase in backticks", "The line is `on %s live` and it is gone now." % EM, False)
t.stop("ordinary reply with hyphens, ranges and flags",
       "Registered three hooks. Run `git log --oneline`. The range is 30-50% over 2020-2024.", False)
t.stop("a second pass in the same turn never blocks", "Still %s here." % EM, False, active=True)

err = t.stop("block message tells the model how to fix it", "a %s b" % EM, True)
t.check("block message names the replacement", "a period" in err and "Rewrite the reply" in err)

t.done()
