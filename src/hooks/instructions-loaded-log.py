#!/usr/bin/env python3
"""InstructionsLoaded: append one line per loaded instruction file to a log. Observational only.

When a model seems to ignore a rule, the first question is whether the rule was in context at all.
Transcripts do not record the CLAUDE.md injection, so they cannot answer it. This log can.

Log: <config>/guardhooks/state/instructions-loaded.log, tab-separated:
  session id (first 8 characters), file path, load reason, memory type, UTC time.
The log is trimmed to its last 10,000 lines when it passes 20,000.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

MAX_LINES = 20000
KEEP_LINES = 10000


def clean(v, default):
    return " ".join(str(v if v not in (None, "") else default).split())


def main():
    ev = G.read_event()
    if not ev:
        return
    try:
        log = os.path.join(G.state_dir(), "instructions-loaded.log")
        row = "\t".join([
            clean(ev.get("session_id"), "?")[:8],
            clean(ev.get("file_path"), "?"),
            clean(ev.get("load_reason"), "?"),
            clean(ev.get("memory_type"), "-"),
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        ])
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(row + "\n")
        with open(log, encoding="utf-8") as fh:
            lines = fh.readlines()
        if len(lines) > MAX_LINES:
            with open(log + ".tmp", "w", encoding="utf-8") as fh:
                fh.writelines(lines[-KEEP_LINES:])
            os.replace(log + ".tmp", log)
    except Exception:
        pass


if __name__ == "__main__":
    main()
