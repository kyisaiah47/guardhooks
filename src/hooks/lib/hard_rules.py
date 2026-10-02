"""Shared body of inject-hard-rules.py and inject-hard-rules-subagent.py.

Reads <config>/hard-rules.md and returns it as additional context for the event that fired.
Subagents such as Explore and Plan do not read the CLAUDE.md hierarchy, and a long session can lose
user-level instructions at a compaction. Injecting a short rules file at SessionStart and
SubagentStart puts the rules back in front of the model in both cases.

Claude Code spills hook output over 10,000 characters to a file, so only the first 9,200
characters of the rules file are sent.
"""
import os

import guardhooks_core as G

MAX_CHARS = 9200
FILENAME = "hard-rules.md"


def rules_path():
    return os.path.join(G.config_dir(), FILENAME)


def run(default_event):
    ev = G.read_event()
    if ev is None:
        return
    path = rules_path()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read(MAX_CHARS)
    except OSError:
        return
    if not content.strip():
        return
    G.context(content, ev.get("hook_event_name") or default_event)
