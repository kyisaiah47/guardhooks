#!/usr/bin/env python3
"""Fixtures for no-retro-rerender-stop.py. Each case runs the real hook against a real transcript file.

Fixtures carry a '^' inside the key verbs, removed at run time by u(), so this file never holds an
offer in a form another guard would act on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402


def u(s):
    return s.replace("^", "")


t = T("no-retro-rerender-stop")

MUST_FIRE = [
    "47 entry pages show a placeholder until the next sync re^generates them. "
    "I can kick the sync now if you want them back sooner.",
    "I can re^generate the old covers so they match the new register.",
    "Want me to back^fill the existing cards?",
    "Should I re-^render the remaining tiles?",
    "The next sync will re-^request them.",
    "I'll re-^shoot the old product films to match the house grammar.",
]
MUST_NOT_FIRE = [
    "The 47 rows are retired in place: they stop being served and nothing draws them again.",
    "Measured across all 58 rows: 9 transparent objects, 49 older renders with a painted ground.",
    "The index builder asks the generator for an object for any row that has never had one.",
    "I repointed 2 rows at an object that already existed on disk.",
    "The sticky header condenses past the first scroll.",
    "I can run the same resolver against the table.",
    "Pushed to a private remote, main tracks origin/main.",
    "The plate flag stops the generator drawing a replacement.",
    "I fixed the contrast on the new table and re-ran the gate.",
    "Let me re-run the typecheck.",
    "I'll re^generate the TypeScript types from the schema.",
]

for s in MUST_FIRE:
    t.stop("block: %s" % u(s)[:60], u(s), True)
for s in MUST_NOT_FIRE:
    t.stop("pass: %s" % u(s)[:60], u(s), False)

t.stop("pass: an offer quoted in backticks", u("The banned line is `Want me to back^fill the existing cards?`."), False)
t.stop("pass: an offer in a blockquote", u("> I can re^generate the old covers.\n\nThat offer is now blocked."), False)
t.stop("pass: an offer in double quotes", u('The hook refuses "Should I re-^render the remaining tiles?" now.'), False)
t.stop("a second pass in the same turn never blocks", u("Want me to back^fill the existing cards?"), False, active=True)

err = t.stop("block message names the alternative", u("Want me to back^fill the existing cards?"), True)
t.check("block message says retired in place", "retired in place" in err and "Delete the offer" in err)

t.done()
