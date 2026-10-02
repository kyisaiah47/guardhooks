#!/usr/bin/env python3
"""Fixtures for no-parallel-repo-fanout.py."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-parallel-repo-fanout")

# must deny
t.pre("loop that backgrounds git push", "Bash",
      {"command": "for r in a b c; do (cd /tmp/p/$r && git push -q) & done; wait"}, "deny")
t.pre("loop that backgrounds commit and push", "Bash",
      {"command": "for r in a b c; do\n  git -C /tmp/p/$r commit -qm msg && git -C /tmp/p/$r push &\ndone\nwait"}, "deny")
t.pre("while loop that backgrounds npm install", "Bash",
      {"command": "ls /tmp/p | while read r; do (cd /tmp/p/$r && npm install) & done"}, "deny")
t.pre("xargs -P 8 git pull", "Bash",
      {"command": "ls /tmp/p | xargs -P 8 -I{} git -C /tmp/p/{} pull"}, "deny")
t.pre("GNU parallel running builds", "Bash",
      {"command": "parallel -j4 'cd {} && npm run build' ::: /tmp/p/a /tmp/p/b"}, "deny")

# must allow
t.pre("sequential loop with git push", "Bash",
      {"command": "for r in a b c; do git -C /tmp/p/$r push -q || echo failed $r; done"}, "allow")
t.pre("a single backgrounded dev server is not a repo fanout", "Bash",
      {"command": "npm run dev > /tmp/p/dev.log 2>&1 &"}, "allow")
t.pre("loop with && only", "Bash",
      {"command": "for r in a b; do cd /tmp/p/$r && git pull && cd -; done"}, "allow")
t.pre("xargs -P 1 is serial", "Bash",
      {"command": "ls /tmp/p | xargs -P 1 -I{} git -C /tmp/p/{} fetch"}, "allow")
t.pre("xargs -P 8 on light work", "Bash",
      {"command": "find /tmp/p -name '*.md' | xargs -P 8 wc -l"}, "allow")
t.pre("heavy verbs only inside a heredoc", "Bash",
      {"command": "cat > /tmp/p/notes.md <<'EOF'\nfor r in a b; do git push & done\nEOF"}, "allow")
t.pre("the word parallel in prose is not GNU parallel", "Bash",
      {"command": "echo 'the parallel version' && git push"}, "allow")
t.pre("redirect 2>&1 inside a loop is not a background job", "Bash",
      {"command": "for r in a b; do git -C /tmp/p/$r push 2>&1 | tail -1; done"}, "allow")
t.pre("not a Bash call", "Write", {"file_path": "/tmp/p/a.sh", "content": "for r in a b; do git push & done"}, "allow")

reason = t.pre("message shows the sequential form", "Bash",
               {"command": "for r in a b; do git -C $r push & done"}, "deny")
t.check("deny message names the declare escape", "guardhooks declare no-parallel-repo-fanout" in reason)

# the declare escape
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "hooks", "lib"))
os.environ["CLAUDE_CONFIG_DIR"] = t.config
import guardhooks_core as G  # noqa: E402
G.write_declaration("no-parallel-repo-fanout", "The user asked for parallel pushes in this session.")
t.pre("a live declaration allows the parallel run", "Bash",
      {"command": "for r in a b; do git -C $r push & done"}, "allow")

t.done()
