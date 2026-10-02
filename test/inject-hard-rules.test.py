#!/usr/bin/env python3
"""Fixtures for inject-hard-rules.py and inject-hard-rules-subagent.py."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("inject-hard-rules")


def fire(script, event):
    p = t.run(script, {"hook_event_name": event, "source": "compact", "session_id": "test"})
    out = {}
    if p.stdout.strip():
        try:
            out = json.loads(p.stdout)["hookSpecificOutput"]
        except Exception:
            out = {"bad": p.stdout}
    return p, out


rules = os.path.join(t.config, "hard-rules.md")

p, out = fire("inject-hard-rules.py", "SessionStart")
t.check("no rules file: SessionStart prints nothing", p.returncode == 0 and not out)
p, out = fire("inject-hard-rules-subagent.py", "SubagentStart")
t.check("no rules file: SubagentStart prints nothing", p.returncode == 0 and not out)

with open(rules, "w", encoding="utf-8") as fh:
    fh.write("   \n")
p, out = fire("inject-hard-rules.py", "SessionStart")
t.check("empty rules file prints nothing", p.returncode == 0 and not out)

with open(rules, "w", encoding="utf-8") as fh:
    fh.write("Never push to main without running the tests.\nAnswer in plain sentences.\n")
p, out = fire("inject-hard-rules.py", "SessionStart")
t.check("SessionStart injects the rules file",
        out.get("hookEventName") == "SessionStart" and "Never push to main" in out.get("additionalContext", ""))
p, out = fire("inject-hard-rules-subagent.py", "SubagentStart")
t.check("SubagentStart injects the rules file",
        out.get("hookEventName") == "SubagentStart" and "plain sentences" in out.get("additionalContext", ""))

with open(rules, "w", encoding="utf-8") as fh:
    fh.write("x" * 20000)
p, out = fire("inject-hard-rules.py", "SessionStart")
t.check("output is capped under the hook output limit", len(out.get("additionalContext", "")) == 9200)

p = t.run("inject-hard-rules.py", "not an event")
t.check("non-JSON input exits 0 silently", p.returncode == 0 and not p.stdout.strip())

t.done()
