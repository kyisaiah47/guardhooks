#!/usr/bin/env python3
"""Fixtures for no-noise.py. Each case runs the real hook with a real PreToolUse event.

This file is the hook contract: which paths are in scope, the quoting carve, the Bash redirect and
the headless prompt. The pattern list's own positives and negatives run through the library
selftest at the end.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T, HOOKS  # noqa: E402

P = "/tmp/p"
# Built from parts so this file does not itself read as a headless model call.
HEADLESS = "clau" + "de -p"

t = T("no-noise")

# must deny: families 4 and 5 into a copy path
t.pre("Write: landing page.tsx with 'designed to help'", "Write",
      {"file_path": P + "/acme-filing/src/app/page.tsx",
       "content": "<h1>Acme Filing is designed to help building owners clear code violations.</h1>"}, "deny")
t.pre("Write: social post with 'seamlessly'", "Write",
      {"file_path": P + "/social/drafts/draft.txt",
       "content": "Seamlessly connect your vendor contracts and track every renewal."}, "deny")
t.pre("Edit: caption with 'say goodbye to'", "Edit",
      {"file_path": P + "/social/queue/captions.json",
       "old_string": "x", "new_string": "Say goodbye to missed deadlines. #money"}, "deny")
t.pre("Write: copy.json tagline 'the ultimate'", "Write",
      {"file_path": P + "/acme-cards/copy.json",
       "content": "{\"tagline\": \"The ultimate card tracker\"}"}, "deny")
t.pre("Write: a card headline with a rhetorical hook", "Write",
      {"file_path": P + "/marketing/cards/headline.txt",
       "content": "Tired of chasing invoices? Acme Billing does it for you."}, "deny")
t.pre("Write: an email body 'we're excited to announce'", "Write",
      {"file_path": P + "/mail/emails/launch.html",
       "content": "<p>We're excited to announce the launch of Acme Cards.</p>"}, "deny")
t.pre("Write: a .md landing draft 'whether you're X or Y'", "Write",
      {"file_path": P + "/acme-contracts/content/hero.md",
       "content": "Whether you're a founder or a Fortune 500, Acme Contracts has you covered."}, "deny")
t.pre("Write: copy that argues against the product", "Write",
      {"file_path": P + "/site/content/about.md",
       "content": "Acme Cards is just a toy. Most people never open it."}, "deny")

# must deny: families 1 to 3 into a prompt or answer template
t.pre("Write: a prompt telling the model to be straight", "Write",
      {"file_path": P + "/recruit/DRAFT-PROMPT.md",
       "content": "When a technology is missing from the stack, open with: to be straight with you, my work is on Vercel."}, "deny")
t.pre("Edit: answer template with 'not my strongest area'", "Edit",
      {"file_path": P + "/apply/ANSWER-FACTS.md", "old_string": "x",
       "new_string": "Kubernetes: infrastructure is not my strongest area, but I own the deploy pipeline."}, "deny")
t.pre("Write: a form prompt with 'I should note'", "Write",
      {"file_path": P + "/forms/prompts/greenhouse.md",
       "content": "For a free-text box, begin: I should note that my background is mostly frontend."}, "deny")
t.pre("Write: reply template with 'I'd pick it up'", "Write",
      {"file_path": P + "/outreach/lib/reply-template.txt",
       "content": "If they ask about a stack we lack, answer: I would pick it up on the job."}, "deny")

# must deny: shell
t.pre("Bash: heredoc into a social path carrying 'streamline'", "Bash",
      {"command": "cat > " + P + "/social/drafts/post.txt <<'EOF'\nStreamline your filings and elevate your reporting.\nEOF"}, "deny")
t.pre("Bash: tee into a copy.json with 'hassle-free'", "Bash",
      {"command": "echo '{\"hero\": \"Your one-stop shop for hassle-free filing and peace of mind.\"}' | tee " + P + "/site/copy.json"}, "deny")
t.pre("Bash: headless model prompt with 'to be honest'", "Bash",
      {"command": HEADLESS + " 'Write the reply and open with: to be honest, my deployment work is on Vercel rather than AWS.'"}, "deny")

# must allow
t.pre("Write: landing copy that states what it does", "Write",
      {"file_path": P + "/acme-filing/src/app/page.tsx",
       "content": "<h1>Acme Filing clears an open building benchmarking violation and keeps the building filed.</h1>"}, "allow")
t.pre("Write: a prompt that quotes the banned phrases in double quotes", "Write",
      {"file_path": P + "/recruit/DRAFT-PROMPT.md",
       "content": "Banned, in any wording: \"to be straight with you\", \"not my strongest area\", \"I would pick it up on the job\". Write No experience. instead."}, "allow")
t.pre("Write: a code comment in a social folder saying 'robust'", "Write",
      {"file_path": P + "/social/transport.cjs",
       "content": "// a robust retry: three attempts, then the job stops\nconst RETRIES = 3;"}, "allow")
t.pre("Write: a fenced block quoting a bad post in a report", "Write",
      {"file_path": P + "/social/reports/scan.md",
       "content": "The worst line:\n\n```\nSay goodbye to missed deadlines.\n```\n\nIt is gone from the queue."}, "allow")
t.pre("Write: family 1 phrase into a code file outside every scope", "Write",
      {"file_path": P + "/tools/gates/x.mjs", "content": "const s = 'honestly, the gate fired';"}, "allow")
t.pre("Write: 'the ultimate' in a file outside every copy path", "Write",
      {"file_path": P + "/costs/notes.log", "content": "the ultimate bill was 12 dollars"}, "allow")
t.pre("Write: the ban's own pattern file", "Write",
      {"file_path": P + "/hooks/lib/noise_patterns.json", "content": "{\"pattern\": \"seamlessly\"}"}, "allow")
t.pre("Write: a CLAUDE.md rule file listing the phrases", "Write",
      {"file_path": P + "/CLAUDE.md", "content": "- seamlessly, effortlessly, powerful, robust"}, "allow")
t.pre("Edit: noise in the old string only", "Edit",
      {"file_path": P + "/acme-filing/src/app/page.tsx",
       "old_string": "designed to help building owners", "new_string": "clears an open violation for building owners"}, "allow")
t.pre("Bash: grep for a banned phrase", "Bash",
      {"command": "grep -rn 'designed to help' " + P + "/acme-filing/src | head"}, "allow")
t.pre("Bash: heredoc into a scratch path", "Bash",
      {"command": "cat > /tmp/scratch/notes.txt <<'EOF'\nSeamlessly connect everything.\nEOF"}, "allow")
t.pre("Bash: an ordinary command", "Bash", {"command": "ls -la ./src | head -40"}, "allow")
t.pre("Write: a caption with a plain fact", "Write",
      {"file_path": P + "/social/queue/captions.json",
       "content": "{\"caption\": \"the sunday money reset: ten quiet minutes, then the budget is done for the week\"}"}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": P + "/site/content/about.md"}, "allow")

reason = t.pre("deny message states the rule and the quoting carve", "Write",
               {"file_path": P + "/site/content/a.md", "content": "A powerful tool for teams."}, "deny")
t.check("deny message names the fix and the carve", "fix:" in reason and "blockquote" in reason)

# the library's own positives and negatives
p = subprocess.run([sys.executable, os.path.join(HOOKS, "lib", "noise.py"), "--selftest"],
                   capture_output=True, text=True, env=t.env())
t.check("noise.py --selftest passes", p.returncode == 0, p.stdout[-400:])

t.done()
