#!/usr/bin/env python3
"""Fixtures for no-reading-measure-cap.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-reading-measure-cap")

# must deny
t.pre("max-width set to a --measure variable", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".doc p { max-width: var(--measure); }"}, "deny")
t.pre("max-width set to a --prose variable", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".content > * { max-width: var(--prose); }"}, "deny")
t.pre("a 72ch cap", "Write", {"file_path": "/tmp/p/app.css", "content": "dl.facts { max-width: 72ch; }"}, "deny")
t.pre("a 680px cap on a prose selector", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".prose table { max-width: 680px; }"}, "deny")
t.pre("Edit adds a 65ch cap in a component", "Edit",
      {"file_path": "/tmp/p/Article.tsx", "old_string": "x",
       "new_string": "const css = `.lede { max-width: 65ch; }`;"}, "deny")

# must allow
t.pre("a page shell cap", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".shell { max-width: var(--shell-cap); margin: 0 auto; }"}, "allow")
t.pre("a 680px card with no prose selector", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".card { max-width: 680px; }"}, "allow")
t.pre("media at 100 percent", "Write", {"file_path": "/tmp/p/app.css", "content": "img { max-width: 100%; }"}, "allow")
t.pre("a 40ch cap is outside the measure range", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".tag { max-width: 40ch; }"}, "allow")
t.pre("a markdown file is not a stylesheet", "Write",
      {"file_path": "/tmp/p/notes.md", "content": "Use max-width: 72ch on prose."}, "allow")
t.pre("the guard's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/reading_measure_cap.py", "content": "max-width: 72ch"}, "allow")

reason = t.pre("deny message names the shell", "Write",
               {"file_path": "/tmp/p/app.css", "content": "dl { max-width: 72ch; }"}, "deny")
t.check("deny message says to set the width on the shell", "page shell" in reason)

t.done()
