#!/usr/bin/env python3
"""Fixtures for aggregate-composition-stop.py."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("aggregate-composition-stop")

# must block
t.stop("a source ranked by a bare total",
       "YouTube is our biggest real source, with 446 people over the period.", True)
t.stop("an average with no median or sample",
       "The newsletter account averages 813 views per post, against 288 for the blog.", True)
t.stop("a multiple with no sample size",
       "The new channel gets 3x the clicks of the old one.", True)
err = t.stop("a cross-platform ranking without coverage",
             "Over the last 30 days, n=40 posts, median 170: product posts beat other posts, "
             "with 900 views on Threads and 300 views on Bluesky.", True)
t.check("the cross-platform block names COVERAGE", "[COVERAGE]" in err)

# must pass
t.stop("a fully decomposed number",
       "Over the last 30 days the blog had 446 people across n=52 posts. The median post drew 7 "
       "people, and one post carried 210 of them.", False)
t.stop("a cross-platform comparison that states coverage",
       "Over the last 30 days, n=40 posts, median 170: product posts beat other posts on Threads "
       "with 900 views. Bluesky does not report views, so it is not compared.", False)
t.stop("an engineering reply with a count of users", "The seed script now creates 50 users per page of the fixture.", False)
t.stop("numbers inside a code block are ignored",
       "Here is the query output:\n\n```\nsource | visitors\nyoutube | 446 people\n```\n\nNothing else changed.", False)
t.stop("a reply with no numbers", "The migration is applied and the tests pass.", False)
t.stop("second pass in the same turn never blocks", "YouTube is our biggest source, with 446 people.", False, active=True)

# the declare escape
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "hooks", "lib"))
os.environ["CLAUDE_CONFIG_DIR"] = t.config
import guardhooks_core as G  # noqa: E402
G.write_declaration("aggregate-composition-stop", "The user asked only for the raw total from the dashboard.")
t.stop("a live declaration lets the bare total through",
       "YouTube is our biggest real source, with 446 people over the period.", False)

t.done()
