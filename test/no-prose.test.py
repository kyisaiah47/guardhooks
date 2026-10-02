#!/usr/bin/env python3
"""Fixtures for no-prose.py. Each case runs the real hook with a real PreToolUse event.

This file is the hook contract: which paths are in scope, the quoting carve and the Bash redirect.
The pattern list's own positives and negatives run through the library selftest at the end, and
every positive is also driven through the hook in a copy path.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T, HOOKS  # noqa: E402

P = "/tmp/p"
SPEC = json.load(open(os.path.join(HOOKS, "lib", "prose_patterns.json"), encoding="utf-8"))

t = T("no-prose")

# must deny: one fixture per family, in a copy path
t.pre("Write: caption in front of a link in an email", "Write",
      {"file_path": P + "/mail/emails/intro.txt",
       "content": "Thanks for the reply.\nA four-minute tour of the product: https://example.com/share/demo"}, "deny")
t.pre("Write: figure without a payer in landing copy", "Write",
      {"file_path": P + "/site/content/pricing.md",
       "content": "Lines come back in 48 hours, 25 percent of relief granted, nothing if nothing is found."}, "deny")
t.pre("Write: metaphor for the product in a page.tsx", "Write",
      {"file_path": P + "/site/src/app/page.tsx",
       "content": "<p>Under the hood, the scorer reads each charge line.</p>"}, "deny")
t.pre("Write: label in place of a sentence in a .md", "Write",
      {"file_path": P + "/site/content/notes.md",
       "content": "A note on timing:\nThe state deadline is thirty days from the statement date."}, "deny")
t.pre("Write: modifier tail on a tagline", "Write",
      {"file_path": P + "/site/tagline.txt", "content": "four boards, recounted every night"}, "deny")
t.pre("Edit: figure without a payer in an answer template", "Edit",
      {"file_path": P + "/outreach/reply-template.txt", "old_string": "x",
       "new_string": "Scored lines and drafted protests inside 48 hours, 25 percent of relief."}, "deny")
t.pre("Write: data file values are scanned raw", "Write",
      {"file_path": P + "/site/copy.json", "content": "{\"hero\": \"Our secret sauce is the protest drafter.\"}"}, "deny")

# must deny: shell
t.pre("Bash: heredoc into a copy path carrying a metaphor", "Bash",
      {"command": "cat > " + P + "/marketing/post.txt <<'EOF'\nBehind the scenes, the model matches every record.\nEOF"}, "deny")

# must allow
t.pre("Write: the plain sentence with a payer", "Write",
      {"file_path": P + "/site/content/pricing.md",
       "content": "You pay 25 percent of what the state grants, and nothing if we find nothing."}, "allow")
t.pre("Write: a sentence that introduces a link", "Write",
      {"file_path": P + "/mail/emails/intro.txt", "content": "Here is a demo video: https://example.com/share/demo"}, "allow")
t.pre("Write: a label over a list is fine", "Write",
      {"file_path": P + "/site/content/notes.md", "content": "The three steps:\n- upload\n- score\n- file"}, "allow")
t.pre("Write: a shape quoted in a fenced block", "Write",
      {"file_path": P + "/site/content/review.md",
       "content": "The draft said:\n\n```\nUnder the hood, the scorer reads each line.\n```\n\nIt is gone now."}, "allow")
t.pre("Write: a shape quoted in double quotes", "Write",
      {"file_path": P + "/site/content/review.md",
       "content": "The draft opened with \"Under the hood, the scorer reads each line.\" and is gone now."}, "allow")
t.pre("Write: a code comment in a copy folder", "Write",
      {"file_path": P + "/marketing/build.mjs",
       "content": "// under the hood this calls the renderer\nexport const n = 1;"}, "allow")
t.pre("Write: a file outside every scope", "Write",
      {"file_path": P + "/tools/report.log", "content": "Under the hood, 25 percent of relief."}, "allow")
t.pre("Write: the rule's own pattern file", "Write",
      {"file_path": P + "/hooks/lib/prose_patterns.json", "content": "{\"pattern\": \"under the hood\"}"}, "allow")
t.pre("Bash: heredoc into a scratch path", "Bash",
      {"command": "cat > /tmp/scratch/notes.txt <<'EOF'\nUnder the hood, it is one file.\nEOF"}, "allow")
t.pre("Bash: grep for a shape", "Bash", {"command": "grep -rn 'under the hood' ./site"}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": P + "/site/content/notes.md"}, "allow")

reason = t.pre("deny message states the rule and the carve", "Write",
               {"file_path": P + "/site/content/a.md", "content": "The magic is in the matching step."}, "deny")
t.check("deny message names the family, the fix and the carve",
        "METAPHOR FOR THE PRODUCT" in reason and "fix:" in reason and "blockquote" in reason)

# every positive in the pattern list is denied by the hook in a copy path
for fam, sents in SPEC["positives"].items():
    missed = []
    for s in sents:
        _, decision, _, _ = t.pre_result("no-prose.py", "Write",
                                         {"file_path": P + "/site/content/draft.txt", "content": s})
        if decision != "deny":
            missed.append(s)
    t.check("hook denies every family %s positive in a copy path" % fam, not missed, repr(missed[:3]))

# the library's own positives and negatives
p = subprocess.run([sys.executable, os.path.join(HOOKS, "lib", "prose.py"), "--selftest"],
                   capture_output=True, text=True, env=t.env())
t.check("prose.py --selftest passes", p.returncode == 0, p.stdout[-400:])

# A Markdown doc that names a banned shape in short double quotes is about the rule.
t.pre("Markdown doc naming metaphors in double quotes passes", "Write",
      {"file_path": "/tmp/p/docs/README.md",
       "content": 'It blocks a metaphor for the product ("under the hood", "secret sauce", "the magic").'}, "allow")
t.pre("the same metaphor in a Markdown sentence of its own is denied", "Write",
      {"file_path": "/tmp/p/docs/README.md",
       "content": "Under the hood, the parser reads every invoice."}, "deny")

t.done()
