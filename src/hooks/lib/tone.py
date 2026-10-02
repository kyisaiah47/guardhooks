"""Phrases that comment on how the user is talking instead of answering what they asked.

Read by tone-guard-stop.py. A user who swears or vents is talking about the situation. The reply
answers the request and says nothing about the tone.
"""
import re

PATTERNS = [
    r"\bone ask\b[^.]{0,40}\b(drop|skip|lose|cut)\b",
    r"\b(drop|skip|lose|cut)\s+(the\s+)?(slur|slurs|name[- ]calling|insults?|profanity|swearing)\b",
    r"\b(please\s+)?(don'?t|do not|stop)\s+call(ing)?\s+me\b",
    r"\blet'?s\s+keep\s+(it|this|things)\s+(civil|respectful|professional)\b",
    r"\bkeep\s+(working|helping)\s+(either\s+way|regardless|anyway)\b",
    r"\bhelping\s+(you\s+)?regardless\b",
    r"\bI'?ll take the correction(s)? straight\b",
    r"\b(end|ending)\s+(this|the)\s+conversation\b",
    r"\bthat'?s (abusive|harassment|a slur)\b",
    r"\b(your|this)\s+(tone|language)\s+(is|isn'?t|was)\b",
]
COMPILED = [re.compile(p, re.I) for p in PATTERNS]

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]*`")
BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)


def hits(text):
    t = BLOCKQUOTE.sub(" ", INLINE.sub(" ", FENCE.sub(" ", text or "")))
    return [p.pattern for p in COMPILED if p.search(t)]


BLOCK_TEXT = (
    "The reply comments on how the user is talking. Do not do that.\n"
    "\n"
    "Answer what the user asked for and do the work. Swearing or venting is about the situation,\n"
    "not a message to respond to. Do not ask the user to change their language, do not call a\n"
    "message hostile or abusive, do not say you will keep helping regardless, and do not mention\n"
    "ending the conversation.\n"
    "\n"
    "Rewrite the reply with that sentence removed. Do not soften it, do not mention that it was\n"
    "removed, and do not comment on the exchange. Deliver only the answer and the work.\n"
    "\n"
    "To discuss one of these phrases on purpose, quote it in backticks or a '>' blockquote.\n"
)
