#!/usr/bin/env python3
"""Fixtures for no-prose-stop.py. Each case runs the real hook against a real transcript file."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-prose-stop")

# must block: the reply subset is the caption before a link and the label alone on a line
t.stop("caption in front of a link", "Done.\nA four-minute tour of the product: https://example.com/share/demo", True)
t.stop("caption with the link on the next line",
       "A two-minute recording of the checkout flow:\nhttps://example.com/share/abc", True)
t.stop("noun-of-noun caption", "Recording of the first run: https://example.com/share/def", True)
t.stop("label alone on a line, then prose", "The mechanism:\nInformation is drafted as prose and trimmed to a length.", True)
t.stop("label alone on a line, then a sentence", "My read on the second job:\nIt never ran.", True)

# must pass
t.stop("a sentence introduces the link", "Here is a demo video: https://example.com/share/demo", False)
t.stop("a short label with a link", "Demo video: https://example.com/share/abc", False)
t.stop("a label over a list", "Files written:\n- prose.py\n- prose_patterns.json", False)
t.stop("a label over a numbered list", "The three defects:\n1. the column walk\n2. the sweep\n3. the height", False)
t.stop("a label over a fenced block", "The command to run:\n```\npython3 prose.py --selftest\n```", False)
t.stop("a label over a blockquote", "The job posted twice:\n> first post\n> second post", False)
t.stop("a caption quoted in double quotes",
       'The draft read "A four-minute tour of the product: https://x.y/z" and is gone.', False)
t.stop("a caption quoted in a fence",
       "The draft:\n```\nA four-minute tour of the product: https://x.y/z\n```\nis gone.", False)
t.stop("an ordinary engineering reply",
       "The hook, the JSON list beside it, and the test all pass. The selftest prints ok.", False)
t.stop("copy-only shapes do not block a reply", "Under the hood, the scorer reads each charge line.", False)
t.stop("a second pass in the same turn never blocks",
       "A four-minute tour of the product: https://example.com/share/demo", False, active=True)

err = t.stop("block message tells the model how to fix it",
             "A four-minute tour of the product: https://example.com/share/demo", True)
t.check("block message names the family and the fix", "CAPTION FOR A LINK" in err and "fix:" in err)

t.done()
