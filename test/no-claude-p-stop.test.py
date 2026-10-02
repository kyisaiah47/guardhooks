#!/usr/bin/env python3
"""Fixtures for no-claude-p-stop.py. Each case runs the real hook against a real transcript file."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-claude-p-stop")

# must block
t.stop("a reply that plans a headless claude call", "I will write a claude -p fixer for this.", True)
t.stop("a reply that proposes headless claude", "Next I can run headless Claude over each file.", True)
t.stop("a reply that plans the --print flag", "The script will call claude --print on every row.", True)

# must pass
t.stop("a sentence about the ban", "The job no longer uses claude -p; it runs the chosen CLI.", False)
t.stop("a sentence that says instead", "I used the project CLI instead of claude -p.", False)
t.stop("a quoted error line", "The error line was `claude -p exited null`.", False)
t.stop("a fenced quote", "The old script read:\n\n```\nclaude -p \"$P\"\n```\n\nIt is replaced.", False)
t.stop("a blockquote", "> run claude -p on it\n\nThat request is handled by the chosen CLI.", False)
t.stop("an ordinary reply", "Registered the hook and the tests pass.", False)
t.stop("a reply naming the chosen CLI passes", "I will run claude -p style prompts through my-model-cli.", False,
       env={"GUARDHOOKS_HEADLESS_CLI": "my-model-cli"})
t.stop("a second pass in the same turn never blocks", "I will write a claude -p fixer.", False, active=True)

err = t.stop("block message names the chosen CLI", "I will write a claude -p fixer for this.", True,
             env={"GUARDHOOKS_HEADLESS_CLI": "my-model-cli"})
t.check("block message names my-model-cli", "my-model-cli" in err and "Rewrite the reply" in err)

t.done()
