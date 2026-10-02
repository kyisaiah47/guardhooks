#!/usr/bin/env python3
"""Fixtures for no-left-accent.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-left-accent")

# must deny
t.pre("a 3px coloured left border on a card", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".card { border-left: 3px solid #c0392b; padding: 12px; }"}, "deny")
t.pre("a right border in rem with a var colour", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".row { border-right: .25rem solid var(--accent); }"}, "deny")
t.pre("border-inline-start shorthand", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".callout { border-inline-start: 4px solid rebeccapurple; }"}, "deny")
t.pre("longhand width with a colour set", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": ".alert { border-left-width: 4px; border-left-style: solid; border-left-color: #e67e22; }"}, "deny")
t.pre("Tailwind border-l-4", "Write",
      {"file_path": "/tmp/p/Alert.tsx",
       "content": '<div className="border-l-4 border-amber-500 bg-amber-50 p-4">Heads up</div>'}, "deny")
t.pre("an inline style object in JSX", "Edit",
      {"file_path": "/tmp/p/Card.tsx", "old_string": "x",
       "new_string": "<div style={{ borderLeft: '3px solid red' }} />\nconst css = `border-left: 3px solid red;`;"},
      "deny")

# must allow
t.pre("a 1px divider on one side", "Write",
      {"file_path": "/tmp/p/app.css", "content": "td + td { border-left: 1px solid #ddd; }"}, "allow")
t.pre("a border on all four sides", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".card { border: 3px solid #c0392b; }"}, "allow")
t.pre("a transparent one-sided border reserving space", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".tab { border-left: 3px solid transparent; }"}, "allow")
t.pre("a width token with no colour", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".x { --border-left-width: 1px; border-left-width: 4px; }"}, "allow")
t.pre("a comment that explains the rule", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": "/* never use border-left: 3px solid red as an accent */\n.card { background: #fff6f5; border: 1px solid #f2c4bf; }"},
      "allow")
t.pre("Tailwind border-l (1px) divider", "Write",
      {"file_path": "/tmp/p/Nav.tsx", "content": '<li className="border-l border-gray-200 pl-3">Docs</li>'}, "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/left_accent.py", "content": "border-left: 3px solid red"}, "allow")

reason = t.pre("deny message names the alternative", "Write",
               {"file_path": "/tmp/p/app.css", "content": ".card { border-left: 3px solid #c0392b; }"}, "deny")
t.check("deny message suggests a hairline on all four sides", "all four sides" in reason)

t.done()
