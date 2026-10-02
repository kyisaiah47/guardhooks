#!/usr/bin/env python3
"""Fixtures for no-noise-stop.py. Each case runs the real hook against a real transcript file."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-noise-stop")
Q = "what happened with the job"

# must block
t.stop("honesty preface", "To be transparent, I have not run that job yet, so the count below is from yesterday.", True, prompt=Q)
t.stop("to be straight with you", "To be straight with you, the second job never ran.", True, prompt=Q)
t.stop("honestly as a clause", "Honestly, the second option is the one I would ship.", True, prompt=Q)
t.stop("I want to be clear", "I want to be clear that the file was rewritten in place.", True, prompt=Q)
t.stop("should note", "The fix is in. I should note that I did not re-run the full suite.", True, prompt=Q)
t.stop("worth flagging", "One thing worth flagging: the stale server answered the first measurement.", True, prompt=Q)
t.stop("I'd say", "I'd say the second option is the stronger one.", True, prompt=Q)
t.stop("the short version is", "The short version is that the hook never fired.", True, prompt=Q)
t.stop("in other words", "In other words, the file was rewritten in place.", True, prompt=Q)
t.stop("that said", "That said, the count is from yesterday.", True, prompt=Q)
t.stop("at the end of the day", "At the end of the day, the price on the page is the price charged.", True, prompt=Q)
t.stop("is my gap", "Kubernetes is my gap here, so the deploy stayed on Vercel.", True, prompt=Q)
t.stop("cannot speak to", "I cannot speak to the Vercel side, but the Supabase table is present.", True, prompt=Q)
t.stop("n/a though", "N/A, though the older ledger carries the same rows.", True, prompt=Q)
t.stop("not applicable but", "That is not applicable to my run, but the numbers match.", True, prompt=Q)
t.stop("not certain however", "I'm not certain, however the log says it fired.", True, prompt=Q)
t.stop("not going to invent", "There is no source for the limit. I am not going to invent one.", True, prompt=Q)
t.stop("interest of honesty", "In the interest of honesty, the screenshot was taken before the deploy.", True, prompt=Q)
t.stop("thrilled to announce", "We're thrilled to announce the job is live.", True, prompt=Q)

# must pass
t.stop("plain status", "I have not read the file yet; reading it now.", False, prompt=Q)
t.stop("quoted ledger row",
       'The cached answer reads "No experience - I haven\'t worked on auth systems professionally." and is purged.', False, prompt=Q)
t.stop("fenced quote", "The offending line:\n```\nTo be transparent, my deployment work is on Vercel.\n```\nRemoved.", False, prompt=Q)
t.stop("blockquote", "> To be honest, I would pick it up.\n\nThat sentence is gone from the prompt.", False, prompt=Q)
t.stop("inline code", "The regex `to be transparent` is in the JSON.", False, prompt=Q)
t.stop("ordinary report",
       "The nightly job deployed three repos. The render check passed on all of them and the home page shows the new tile.", False, prompt=Q)
t.stop("literal sense of honestly",
       "All three null cases read honestly: the state provides no charge protest.", False, prompt=Q)
t.stop("an engineering gap", "The tile itself is the gap; the head, kicker and mark are on the live page.", False, prompt=Q)
t.stop("a plain no and the fact", "No. The job ran at 07:00 and posted twice; the ledger shows both rows.", False, prompt=Q)
t.stop("the word robust in a code report", "The retry is robust to a dropped socket: three attempts, then the job stops.", False, prompt=Q)
t.stop("a second pass in the same turn never blocks", "To be honest, it ran.", False, prompt=Q, active=True)

err = t.stop("block message tells the model how to fix it", "To be honest, it ran.", True, prompt=Q)
t.check("block message names the family and the fix", "family 1" in err and "fix:" in err)

t.done()
