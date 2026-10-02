#!/usr/bin/env python3
"""Fixtures for no-unsourced-claim-stop.py. Each case runs the real hook on a real transcript file.

The pairing cases matter in both directions. The hook must catch quoted readings that were never
written, and it must not read the prose between two real quotations as a quotation.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src", "hooks", "lib"))
from _harness import T  # noqa: E402
import sourced as S  # noqa: E402

t = T("no-unsourced-claim-stop")

# --- the library's quote pairing, checked directly -------------------------------------------
TWO = ('`at` is 08:07:21 today, which matches the "9m ago" on your screen. `count: 41` means one '
       'banner fired and 40 further hits were dropped inside the notify window. So the site answered '
       '"Something went wrong. Try reloading." on 41 of the targets in one sweep.')
spans = [inner for _, _, inner in S.quoted_spans(TWO)]
t.check("pairing recovers exactly the two real quotations",
        spans == ["9m ago", "Something went wrong. Try reloading."], repr(spans))
flagged = [q for q, _ in S.numeric_quotes(TWO)]
t.check("the prose between two quotations is not a quote",
        not any("means one banner fired" in q for q in flagged), repr(flagged))

THREE = 'They said "the first one" then "the second one" and finally "the third one here".'
t.check("three quotations pair as three, not five",
        [i for _, _, i in S.quoted_spans(THREE)] == ["the first one", "the second one", "the third one here"])
UNBAL = 'They said "an opening with no close\nand the next line carries 8:20 and 9:45 freely.'
t.check("an unbalanced quote stops at the newline",
        not [i for _, _, i in S.quoted_spans(UNBAL) if "next line" in i])
CURLY = "She wrote “the first thing” and then 41 more, then “the second thing”."
t.check("curly quotes pair by direction",
        [i for _, _, i in S.quoted_spans(CURLY)] == ["the first thing", "the second thing"])
BETWEEN = 'The row says "x-something-went-wrong" and the file it reads contains "the signature table".'
t.check("a verb between two quotations quotes neither the gap nor across it",
        not any("and the file it reads" in q for q, _ in S.quoted_claims(BETWEEN)))

# --- the hook ---------------------------------------------------------------------------------
EVIDENCE = [("assistant", "Earlier readings: the log showed 7:36 and later 8:52 on the status line.")]
APOLOGY = 'Every clock reading after it, "it\'s 7:36", "7:55", "8:05", "8:20", "8:35", "8:52", I made up.'
err = t.stop("invented quoted readings are caught", APOLOGY, True, prior=EVIDENCE)
t.check("each invented reading is listed", all(x in err for x in ('"7:55"', '"8:05"', '"8:20"', '"8:35"')), err[:400])
t.check("a reading the session really saw is not listed", '"8:52"' not in err, err[:400])

t.stop("a quoted reading the session saw passes", 'The status line showed "8:52" at that point.', False,
       prior=EVIDENCE)
t.stop("an attributed quote that was never said is caught",
       'You said "never rebuild any of the landing pages from scratch today".', True)
t.stop("an attributed quote that was said passes",
       'You said "never rebuild any of the landing pages from scratch today".', False,
       prior=[("user", "never rebuild any of the landing pages from scratch today")])
t.stop("two real quotations in one paragraph pass", TWO, False,
       prior=[("assistant", 'tool output: 9m ago | Something went wrong. Try reloading.')])
t.stop("an ordinary quoted phrase with no attribution passes",
       'The "clean" mode skips the cache and the "fast" mode keeps it.', False)
t.stop("a quote inside a code span is not a claim", 'The config sets `"retries": "3"` by default.', False)

MISSING = "~/guardhooks-missing-%d/notes/plan.md" % os.getpid()
t.stop("a home path that does not exist is caught", "I saved the plan to %s for later." % MISSING, True)
t.stop("a missing path that came from a tool result passes",
       "The tool listed %s as the target." % MISSING, False,
       prior=[("assistant", "tool result: wrote %s" % MISSING)])
t.stop("a templated path is skipped", "Each product keeps its config at ~/projects/<slug>/config.json.", False)

home = os.path.expanduser("~")
here = os.path.abspath(__file__)
if here.startswith(home + os.sep):
    rel = "~/" + os.path.relpath(here, home)
    t.stop("a home path that exists passes", "The fixtures live in %s now." % rel, False)

# a quote whose sentence names a pasted image passes when the session has an image
fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": [
    {"type": "text", "text": "look at this"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}}]}}) + "\n")
fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
    {"type": "text", "text": 'The screenshot shows "Trial ends in 14 days" in the header.'}]}}) + "\n")
fh.close()
p = t.run("no-unsourced-claim-stop.py", {"transcript_path": fh.name, "session_id": "img", "stop_hook_active": False})
os.unlink(fh.name)
t.check("a quote attributed to a pasted image passes", p.returncode == 0, p.stderr[:300])

t.stop("a second pass in the same turn never blocks", APOLOGY, False, prior=EVIDENCE, active=True)

# the declaration escape, written into this test's own config dir
os.environ["CLAUDE_CONFIG_DIR"] = t.config
import guardhooks_core as G  # noqa: E402
G.write_declaration("no-unsourced-claim-stop", "the readings come from a log file outside this session")
t.stop("a live declaration lets the reply through", APOLOGY, False, prior=EVIDENCE)

t.done()
