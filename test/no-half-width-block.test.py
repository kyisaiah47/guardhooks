#!/usr/bin/env python3
"""Fixtures for no-half-width-block.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-half-width-block")

# must deny
t.pre("a filled panel with a ch max-width", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": ".panel { background: #f4f1ea; padding: 24px; max-width: 68ch; }"}, "deny")
t.pre("background-color with an em width", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": ".note {\n  background-color: var(--tint);\n  width: 40em;\n}"}, "deny")
t.pre("a background-image with a ch cap", "Edit",
      {"file_path": "/tmp/p/app.scss", "old_string": "x",
       "new_string": ".hero-copy { background-image: linear-gradient(#fff, #eee); max-width: 60ch; }"}, "deny")
t.pre("an inline <style> block in HTML", "Write",
      {"file_path": "/tmp/p/index.html",
       "content": "<style>.callout{background:#fffbe6;max-width:62ch}</style><div class=callout>Hi</div>"}, "deny")

# must allow
t.pre("a ch measure on bare prose", "Write",
      {"file_path": "/tmp/p/app.css", "content": "article p { max-width: 68ch; line-height: 1.6; }"}, "allow")
t.pre("a fill with a px width", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".panel { background: #f4f1ea; max-width: 720px; }"}, "allow")
t.pre("a transparent background with a measure", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".lede { background: transparent; max-width: 60ch; }"}, "allow")
t.pre("fill and measure on different elements", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": ".panel { background: #eee; }\n.panel p { max-width: 65ch; }"}, "allow")
t.pre("an at-rule block is not a rule", "Write",
      {"file_path": "/tmp/p/app.css", "content": "@media (min-width: 40em) { .x { color: red; } }"}, "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/half_width.py",
       "content": ".panel { background: #eee; max-width: 68ch; }"}, "allow")

reason = t.pre("deny message gives both fixes", "Write",
               {"file_path": "/tmp/p/app.css", "content": ".panel { background: #eee; max-width: 68ch; }"}, "deny")
t.check("deny message names both fixes", "narrow the block" in reason and "drop the measure" in reason)
t.check("deny message names the selector", ".panel" in reason)

t.done()
