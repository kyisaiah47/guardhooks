#!/usr/bin/env python3
"""Fixtures for block-skill-install.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("block-skill-install")

reason = t.pre("npx skills add", "Bash", {"command": "npx skills add someone/skill-pack"}, "deny")
t.check("the denial points at skill-scan", "skill-scan.py" in reason, reason[:300])
t.check("the denial names the config dir skills folder", os.path.join(t.config, "skills") in reason, reason[:400])
t.pre("bare skills install", "Bash", {"command": "skills install pdf-tools"}, "deny")
t.pre("claude plugin install", "Bash", {"command": "claude plugin install some-plugin@market"}, "deny")
t.pre("/plugin install", "Bash", {"command": "/plugin install formatter"}, "deny")
t.pre("an install after another command", "Bash", {"command": "cd /tmp/p && npx skills add x/y"}, "deny")

t.pre("listing skills is allowed", "Bash", {"command": "ls ~/.claude/skills"}, "allow")
t.pre("a sentence about skills is allowed", "Bash", {"command": "echo 'the skills are ready'"}, "allow")
t.pre("an npm install is allowed", "Bash", {"command": "npm install --save-dev prettier"}, "allow")
t.pre("a plugin list is allowed", "Bash", {"command": "claude plugin list"}, "allow")
t.pre("a non-Bash tool is ignored", "Write", {"file_path": "/tmp/p/a.md", "content": "npx skills add x"}, "allow")

t.done()
