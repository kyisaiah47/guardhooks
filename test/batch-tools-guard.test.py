#!/usr/bin/env python3
"""Fixtures for batch-tools-guard.py. The streak state is prepared in the test's own config dir,
then the real hook runs, so the cases need no waiting."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("batch-tools-guard")
state = os.path.join(t.config, "guardhooks", "state", "batch-tools-guard")
os.makedirs(state, exist_ok=True)


def seed(session, last, streak):
    with open(os.path.join(state, session + ".json"), "w") as fh:
        json.dump({"last": last, "streak": streak, "nagged": 0}, fh)


def read(session):
    with open(os.path.join(state, session + ".json")) as fh:
        return json.load(fh)


def call(session):
    return t.pre_result("batch-tools-guard.py", "Bash", {"command": "ls"}, extra_event={"session_id": session})


p, decision, _, ctx = call("fresh")
t.check("the first call of a session is silent", decision == "allow" and not ctx and p.returncode == 0)
t.check("the first call starts a streak of one", read("fresh")["streak"] == 1, repr(read("fresh")))

seed("long", time.time() - 10, 11)
p, decision, _, ctx = call("long")
t.check("the twelfth lone call adds a reminder", "in a row" in ctx and decision == "allow", repr(ctx[:200]))
t.check("the reminder never denies the call", decision == "allow")
t.check("the streak resets after the reminder", read("long")["streak"] == 0, repr(read("long")))

seed("batched", time.time(), 11)
p, decision, _, ctx = call("batched")
t.check("a call that arrives with a sibling resets the streak and stays silent",
        not ctx and read("batched")["streak"] == 0, repr(read("batched")))

seed("short", time.time() - 10, 3)
p, decision, _, ctx = call("short")
t.check("a short streak is silent", not ctx and read("short")["streak"] == 4, repr(read("short")))

with open(os.path.join(state, "broken.json"), "w") as fh:
    fh.write("not json")
p, decision, _, ctx = call("broken")
t.check("a corrupt state file is replaced, not fatal", p.returncode == 0 and read("broken")["streak"] == 1)

t.done()
