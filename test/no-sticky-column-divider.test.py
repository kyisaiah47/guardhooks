#!/usr/bin/env python3
"""Fixtures for no-sticky-column-divider.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-sticky-column-divider")

# must deny
t.pre("a sticky rail with border-right", "Write",
      {"file_path": "/tmp/p/app/globals.css",
       "content": ".rail { position: sticky; top: 64px; max-height: 100vh; border-right: 1px solid var(--rule); }"},
      "deny")
t.pre("a sticky aside with border-left", "Write",
      {"file_path": "/tmp/p/styles.scss",
       "content": "aside.toc {\n  position: sticky;\n  top: 0;\n  border-left: 1px solid #e5e5e5;\n}"}, "deny")
t.pre("border-inline-end on a sticky column", "Edit",
      {"file_path": "/tmp/p/layout.css", "old_string": "x",
       "new_string": ".side { position: sticky; inset-block-start: 0; border-inline-end: 1px solid #ddd; }"}, "deny")
t.pre("a Tailwind sticky rail with border-r", "Write",
      {"file_path": "/tmp/p/Sidebar.tsx",
       "content": '<nav className="sticky top-16 h-screen border-r border-gray-200 w-64">...</nav>'}, "deny")

# must allow
t.pre("a sticky table header cell", "Write",
      {"file_path": "/tmp/p/table.css",
       "content": "table th { position: sticky; top: 0; border-right: 1px solid #ddd; }"}, "allow")
t.pre("a sticky rail with no side border", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".rail { position: sticky; top: 64px; }"}, "allow")
t.pre("a stretching column with the border", "Write",
      {"file_path": "/tmp/p/app.css",
       "content": ".rail { align-self: stretch; border-right: 1px solid #ddd; }\n.rail-inner { position: sticky; top: 64px; }"},
      "allow")
t.pre("a sticky rail with border-right: none", "Write",
      {"file_path": "/tmp/p/app.css", "content": ".rail { position: sticky; top: 0; border-right: none; }"}, "allow")
t.pre("a non-style file is not checked", "Write",
      {"file_path": "/tmp/p/notes.md", "content": ".rail { position: sticky; top: 0; border-right: 1px solid red; }"},
      "allow")
t.pre("the guard's own files", "Write",
      {"file_path": "/tmp/p/hooks/no-sticky-column-divider.py",
       "content": ".rail { position: sticky; top: 0; border-right: 1px solid red; }"}, "allow")

reason = t.pre("deny message gives the grid fix", "Write",
               {"file_path": "/tmp/p/app.css", "content": ".rail { position: sticky; top: 0; border-right: 1px solid #ddd; }"},
               "deny")
t.check("deny message says the line belongs to the grid", "belongs to the grid" in reason)

t.done()
