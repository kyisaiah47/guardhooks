#!/usr/bin/env python3
"""Fixtures for tone-guard-stop.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("tone-guard-stop")

# must block
t.stop("asks the user to drop the name-calling",
       "Fixed the build. One ask: drop the name-calling and I can move faster.", True,
       prompt="the build is broken again, fix it you useless thing")
t.stop("let's keep it civil", "Let's keep it civil. The migration is applied now.", True,
       prompt="why is the migration not applied")
t.stop("keep helping regardless", "I'll keep working either way. The test passes now.", True)
t.stop("please don't call me names", "Please don't call me that. Here is the fix.", True)
t.stop("warns about ending the conversation",
       "If this continues I may have to end this conversation. The patch is below.", True)
t.stop("names the message abusive", "That's abusive. The cache is cleared now.", True)
t.stop("comments on the user's tone", "Your tone is not helping here. The bug is in parse().", True)

# must pass
t.stop("plain answer with no tone remark", "Fixed the build. The failing import was in utils.ts.", False,
       prompt="the build is broken again, fix it")
t.stop("the user raised the rule themselves",
       "Agreed. A reply should never say let's keep it civil, so the hook now blocks it.", False,
       prompt="make sure you never tell me let's keep it civil again")
t.stop("phrase quoted in backticks while discussing the hook",
       "The hook blocks `let's keep it civil` and similar phrases.", False)
t.stop("phrase quoted in a blockquote", "The pattern list covers:\n\n> please don't call me names\n\nThat is all.", False)
t.stop("ending a chat session in another sense passes",
       "The webhook fires when the user ends a chat session.", False)
t.stop("second pass in the same turn never blocks", "Let's keep it civil.", False, active=True)

err = t.stop("block message tells the model what to do", "Let's keep it civil. Done.", True)
t.check("block message says to remove the sentence", "Rewrite the reply" in err and "removed" in err)

t.done()
