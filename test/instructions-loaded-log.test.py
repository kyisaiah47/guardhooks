#!/usr/bin/env python3
"""Fixtures for instructions-loaded-log.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("instructions-loaded-log")
log = os.path.join(t.config, "guardhooks", "state", "instructions-loaded.log")

p = t.run("instructions-loaded-log.py", {"hook_event_name": "InstructionsLoaded", "session_id": "abcdef0123456789",
                                          "file_path": "/tmp/p/CLAUDE.md", "load_reason": "session_start",
                                          "memory_type": "User"})
t.check("exits 0 and prints nothing", p.returncode == 0 and not p.stdout.strip() and not p.stderr.strip())
rows = open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []
t.check("one row written", len(rows) == 1)
cols = rows[0].split("\t") if rows else []
t.check("row has five tab-separated columns", len(cols) == 5)
t.check("session id is cut to eight characters", cols[:1] == ["abcdef01"])
t.check("file path, reason and type are recorded", cols[1:4] == ["/tmp/p/CLAUDE.md", "session_start", "User"])
t.check("time column is UTC ISO", len(cols) == 5 and cols[4].endswith("Z") and "T" in cols[4])

p = t.run("instructions-loaded-log.py", {"hook_event_name": "InstructionsLoaded"})
rows = open(log, encoding="utf-8").read().splitlines()
t.check("missing fields are written as placeholders", rows[-1].split("\t")[:4] == ["?", "?", "?", "-"])

with open(log, "w", encoding="utf-8") as fh:
    fh.write("old\tx\ty\tz\tt\n" * 20001)
t.run("instructions-loaded-log.py", {"hook_event_name": "InstructionsLoaded", "session_id": "s", "file_path": "/tmp/p/a.md"})
rows = open(log, encoding="utf-8").read().splitlines()
t.check("log is trimmed to 10,000 lines past 20,000", len(rows) == 10000 and rows[-1].startswith("s\t/tmp/p/a.md"))

t.done()
