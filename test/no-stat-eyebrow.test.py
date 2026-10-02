#!/usr/bin/env python3
"""Fixtures for no-stat-eyebrow.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-stat-eyebrow")

CARD_CSS = """
.stat-number { font-size: 212px; font-weight: 800; line-height: 1; }
.stat-label { font-size: 27px; text-transform: uppercase; letter-spacing: 0.13em; }
"""
CARD_REM = """
.kpi { font-size: 9rem; }
.eyebrow { text-transform: uppercase; letter-spacing: .14em; font-size: 14px; }
"""
CARD_JSX = """
const s = { num: { fontSize: '178px' }, eyebrow: { textTransform: 'uppercase', letterSpacing: '0.14em' } };
"""

# must deny: the CSS shape
t.pre("CSS: a 212px figure beside an uppercase label tracked .13em", "Write",
      {"file_path": "/tmp/p/cover.css", "content": CARD_CSS}, "deny")
t.pre("CSS: a 9rem KPI under a tracked eyebrow", "Write",
      {"file_path": "/tmp/p/slide.css", "content": CARD_REM}, "deny")
t.pre("JSX style object: 178px number and a tracked eyebrow", "Write",
      {"file_path": "/tmp/p/Card.tsx", "content": CARD_JSX}, "deny")
t.pre("Edit: the card arrives in the new string", "Edit",
      {"file_path": "/tmp/p/cover.css", "old_string": ".x{}", "new_string": CARD_CSS}, "deny")
t.pre("MultiEdit: the card arrives across two edits", "MultiEdit",
      {"file_path": "/tmp/p/cover.css", "edits": [
          {"old_string": "a", "new_string": ".stat-number { font-size: 200px; }"},
          {"old_string": "b", "new_string": ".label { text-transform: uppercase; letter-spacing: 0.1em; }"}]},
      "deny")

# must deny: the same thing asked for in words
t.pre("prompt asks for a big number", "Write",
      {"file_path": "/tmp/p/brief.md", "content": "Cover idea: a big number in the middle with the date."}, "deny")
t.pre("brief names a stat card", "Write",
      {"file_path": "/tmp/p/brief.md", "content": "Option B is a stat card with the growth figure."}, "deny")
t.pre("brief pairs a figure with an eyebrow", "Write",
      {"file_path": "/tmp/p/prompt.txt", "content": "Show the figure with a small eyebrow above it."}, "deny")
t.pre("brief asks for a count-up stat", "Write",
      {"file_path": "/tmp/p/motion.md", "content": "Open on a count-up of the signup number."}, "deny")

# must allow
t.pre("a tracked uppercase label on its own", "Write",
      {"file_path": "/tmp/p/nav.css",
       "content": ".section-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; }"}, "allow")
t.pre("a large headline with no tracked label", "Write",
      {"file_path": "/tmp/p/hero.css", "content": "h1 { font-size: 96px; letter-spacing: -0.02em; }"}, "allow")
t.pre("a table of figures at body size", "Write",
      {"file_path": "/tmp/p/table.css",
       "content": "td.num { font-size: 15px; font-variant-numeric: tabular-nums; }\nth { text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px; }"},
      "allow")
t.pre("a number inside a sentence", "Write",
      {"file_path": "/tmp/p/copy.md", "content": "The import finished 4,210 rows in nine seconds."}, "allow")
t.pre("a style guide that states the ban", "Write",
      {"file_path": "/tmp/p/STYLE.md", "content": "Never use a stat card. The banned stat layout is a big number over an eyebrow."},
      "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/stat_eyebrow.py", "content": CARD_CSS}, "allow")
t.pre("Bash is not this hook's tool", "Bash", {"command": "echo big number"}, "allow")

reason = t.pre("deny message names the alternative", "Write",
               {"file_path": "/tmp/p/cover.css", "content": CARD_CSS}, "deny")
t.check("deny message tells the model to lead with a sentence", "Lead with a sentence" in reason)
t.check("deny message names the file", "cover.css" in reason)

t.done()
