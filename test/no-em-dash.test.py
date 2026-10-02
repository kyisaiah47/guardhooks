#!/usr/bin/env python3
"""Fixtures for no-em-dash.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

EM = chr(0x2014)
EN = chr(0x2013)

t = T("no-em-dash")

# must deny: files
t.pre("Write: an em dash in prose", "Write",
      {"file_path": "/tmp/p/report.md", "content": "The gate is on %s nothing ships." % EM}, "deny")
t.pre("Write: an en dash in prose", "Write",
      {"file_path": "/tmp/p/report.md", "content": "Two jobs %s both on." % EN}, "deny")
t.pre("Write: an em dash in a code comment", "Write",
      {"file_path": "/tmp/p/hook.py", "content": "# the pass is on %s nothing ships\nx = 1" % EM}, "deny")
t.pre("Write: the dash spelled, not typed", "Write",
      {"file_path": "/tmp/p/a.js", "content": "const dash = '\\u2014';"}, "deny")
t.pre("Write: the dash as an HTML entity", "Write",
      {"file_path": "/tmp/p/a.html", "content": "<p>on &mdash; nothing ships</p>"}, "deny")
t.pre("Edit: an em dash in the new string", "Edit",
      {"file_path": "/tmp/p/a.md", "old_string": "old", "new_string": "on %s live" % EM}, "deny")
t.pre("MultiEdit: an em dash in the second edit", "MultiEdit",
      {"file_path": "/tmp/p/a.md", "edits": [
          {"old_string": "a", "new_string": "clean"},
          {"old_string": "b", "new_string": "on %s live" % EM}]}, "deny")
t.pre("NotebookEdit: an em dash in the new cell", "NotebookEdit",
      {"notebook_path": "/tmp/p/n.ipynb", "new_source": "# Results %s final" % EM}, "deny")
t.pre("Write: ' -- ' as a dash in a .md", "Write",
      {"file_path": "/tmp/p/a.md", "content": "The gate is on -- nothing ships."}, "deny")

# must deny: shell
t.pre("Bash: heredoc body carries an em dash", "Bash",
      {"command": "cat > /tmp/p/post.md <<'EOF'\nThe job is on %s live now.\nEOF" % EM}, "deny")
t.pre("Bash: echo carries an em dash", "Bash",
      {"command": "echo 'on %s live' >> /tmp/p/log.txt" % EM}, "deny")
t.pre("Bash: printf carries an en dash", "Bash",
      {"command": "printf 'two %s three\\n'" % EN}, "deny")
t.pre("Bash: python -c printing a dash", "Bash",
      {"command": "python3 -c \"print('on %s live')\"" % EM}, "deny")

# must allow
t.pre("Write: hyphens and CLI flags only", "Write",
      {"file_path": "/tmp/p/a.md", "content": "Run `git log --oneline`. Range 30-50%, 2020-2024."}, "allow")
t.pre("Write: a dash inside a fenced block", "Write",
      {"file_path": "/tmp/p/a.md", "content": "The log says:\n\n```\non %s live\n```\n\nSo it is on." % EM}, "allow")
t.pre("Write: a dash inside an inline code span", "Write",
      {"file_path": "/tmp/p/a.md", "content": "The line was `on %s live`, and it is fixed." % EM}, "allow")
t.pre("Write: a dash inside a '>' blockquote", "Write",
      {"file_path": "/tmp/p/a.md", "content": "> on %s live\n\nThe job is up." % EM}, "allow")
t.pre("Write: ' -- ' in source code is a separator", "Write",
      {"file_path": "/tmp/p/run.sh", "content": "npm test -- --watch\ngit checkout -- src/app.ts\n"}, "allow")
t.pre("Edit: dash in the old string only", "Edit",
      {"file_path": "/tmp/p/a.md", "old_string": "on %s live" % EM, "new_string": "on, live"}, "allow")
t.pre("Bash: grep for the character", "Bash",
      {"command": "grep -rn '%s' ./docs | head -20" % EM}, "allow")
t.pre("Bash: rg for the character", "Bash", {"command": "rg -l '%s' ." % EM}, "allow")
t.pre("Bash: sed removing the character", "Bash",
      {"command": "sed -i '' 's/%s/, /g' /tmp/p/a.md" % EM}, "allow")
t.pre("Bash: tr deleting the character", "Bash",
      {"command": "tr -d '%s' < /tmp/p/a.md > /tmp/p/b.md" % EM}, "allow")
t.pre("Bash: the shell's own ' -- ' separator", "Bash",
      {"command": "git checkout -- src/app.ts && npm run build -- --watch"}, "allow")
t.pre("Bash: an ordinary command", "Bash", {"command": "ls -la ./src | head -40"}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": "/tmp/p/a.md"}, "allow")
t.pre("Write: the ban's own library is about the ban", "Write",
      {"file_path": "/tmp/p/hooks/lib/em_dash.py", "content": "EM = '%s'" % EM}, "allow")

reason = t.pre("deny message states the rule and the fix", "Write",
               {"file_path": "/tmp/p/a.md", "content": "x %s y" % EM}, "deny")
t.check("deny message names the alternatives", "a period" in reason and "blockquote" in reason)

t.done()
