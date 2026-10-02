#!/usr/bin/env python3
"""Fixtures for no-claude-p.py. Each case runs the real hook with a real PreToolUse event."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T, HOOKS  # noqa: E402

t = T("no-claude-p")

with open(os.path.join(HOOKS, "lib", "claude_p_patterns.json"), encoding="utf-8") as fh:
    SPEC = json.load(fh)

# every invocation pattern fires on its own fixture, through the real hook
for slug, text in SPEC["fixtures"]["deny"].items():
    reason = t.pre("pattern %s fires on its own fixture" % slug, "Write",
                   {"file_path": "/tmp/p/tools/run.mjs", "content": text}, "deny")
    t.check("deny reason names %s" % slug, slug in reason)

# must deny
t.pre("the print flag in a shell script", "Write",
      {"file_path": "/tmp/p/jobs/new-job.sh", "content": 'claude -p "$PROMPT" --model opus\n'}, "deny")
t.pre("the print flag typed into Bash", "Bash", {"command": 'claude -p "summarise this" --model haiku'}, "deny")
t.pre("the --print long flag in Bash", "Bash", {"command": 'claude --print "check the build"'}, "deny")
t.pre("the model flag on the claude binary", "Write",
      {"file_path": "/tmp/p/tools/new-tool.sh", "content": "claude --model opus < prompt.txt\n"}, "deny")
t.pre("a spawn of the bare binary", "Edit",
      {"file_path": "/tmp/p/tools/new-tool.mjs", "old_string": "x", "new_string": "execFileSync('claude', args)"}, "deny")
t.pre("a spawn of the binary by absolute path", "Edit",
      {"file_path": "/tmp/p/tools/new-tool.mjs", "old_string": "x",
       "new_string": "spawnSync('/opt/bin/claude', args)"}, "deny")
t.pre("the argv form", "Edit",
      {"file_path": "/tmp/p/tools/new-tool.mjs", "old_string": "x", "new_string": "spawn('claude', ['-p', prompt])"}, "deny")
t.pre("an async exec with the argv form", "Edit",
      {"file_path": "/tmp/p/lib/cli.mjs", "old_string": "x",
       "new_string": "    const { stdout } = await exec('claude', ['-p', String(prompt), '--model', seat], {\n"}, "deny")
t.pre("MultiEdit: the call in the second edit", "MultiEdit",
      {"file_path": "/tmp/p/tools/a.sh", "edits": [
          {"old_string": "a", "new_string": "echo ok"},
          {"old_string": "b", "new_string": 'claude -p "$P"'}]}, "deny")

# must allow
t.pre("a different headless CLI", "Bash", {"command": 'my-model-cli -p "summarise this diff" --model fast'}, "allow")
t.pre("an interactive claude session", "Bash", {"command": "claude"}, "allow")
t.pre("claude in a path segment is not the binary", "Bash", {"command": "ls ~/.claude/hooks"}, "allow")
t.pre("a doc quoting the call in backticks", "Write",
      {"file_path": "/tmp/p/docs/headless.md",
       "content": "The job used to run `claude -p --model opus`; it runs the chosen CLI now.\n"}, "allow")
t.pre("a doc quoting the call in a fenced block", "Write",
      {"file_path": "/tmp/p/docs/headless.md", "content": "Before:\n\n```\nclaude -p \"$PROMPT\"\n```\n"}, "allow")
t.pre("a doc quoting the call in a blockquote", "Write",
      {"file_path": "/tmp/p/docs/headless.md", "content": "> claude -p was the old path\n\nIt is gone."}, "allow")
t.pre("ordinary Bash with no model call", "Bash", {"command": "git status && npm test"}, "allow")
t.pre("a write to the ban's own pattern list", "Write",
      {"file_path": "/tmp/p/hooks/lib/claude_p_patterns.json", "content": '{"x": "claude -p"}'}, "allow")
t.pre("a write to a CLAUDE.md rules file", "Write",
      {"file_path": "/tmp/p/CLAUDE.md", "content": "Never run claude -p here.\n"}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": "/tmp/p/a.sh"}, "allow")

# the chosen CLI is named in the message, and never hard-coded
reason = t.pre("message with no CLI configured", "Bash", {"command": "claude -p hi"}, "deny",
               env={"GUARDHOOKS_HEADLESS_CLI": ""})
t.check("default message names the env var", "GUARDHOOKS_HEADLESS_CLI" in reason
        and "the headless CLI this project uses" in reason)
reason = t.pre("message with a CLI configured", "Bash", {"command": "claude -p hi"}, "deny",
               env={"GUARDHOOKS_HEADLESS_CLI": "my-model-cli"})
t.check("configured message names the chosen CLI", "my-model-cli" in reason)

t.done()
