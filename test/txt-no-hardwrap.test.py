#!/usr/bin/env python3
"""Fixtures for txt-no-hardwrap.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("txt-no-hardwrap")

WRAPPED = ("Thanks for the note about the onboarding flow. We looked at\n"
           "the drop-off between the second and third steps and found that\n"
           "the email check was timing out.\n")
ONE_LINE = ("Thanks for the note about the onboarding flow. We looked at the drop-off between the second and "
            "third steps and found that the email check was timing out.\n\n"
            "The fix ships this week.\n")
LABELS = "Subject line\nWhy this role\n\nShort answer.\n\nBest,\nSam\n"
LIST = "- apples\n- pears\n- plums\n"

# must deny
t.pre("a wrapped paragraph in a .txt", "Write", {"file_path": "/tmp/p/reply.txt", "content": WRAPPED}, "deny")
t.pre("Edit adds a wrapped paragraph", "Edit",
      {"file_path": "/tmp/p/reply.txt", "old_string": "x", "new_string": WRAPPED}, "deny")

# must allow
t.pre("one paragraph per line", "Write", {"file_path": "/tmp/p/reply.txt", "content": ONE_LINE}, "allow")
t.pre("short label lines and a sign-off", "Write", {"file_path": "/tmp/p/reply.txt", "content": LABELS}, "allow")
t.pre("a list of short items", "Write", {"file_path": "/tmp/p/list.txt", "content": LIST}, "allow")
t.pre("a wrapped paragraph in a .md is not checked", "Write", {"file_path": "/tmp/p/notes.md", "content": WRAPPED}, "allow")
t.pre("a .txt under node_modules is not checked", "Write",
      {"file_path": "/tmp/p/node_modules/x/LICENSE.txt", "content": WRAPPED}, "allow")

reason = t.pre("deny message shows the two lines", "Write", {"file_path": "/tmp/p/reply.txt", "content": WRAPPED}, "deny")
t.check("deny message names the line numbers", "Line 1" in reason and "line 2" in reason)
t.check("deny message gives the fix", "one unwrapped line" in reason)

t.done()
