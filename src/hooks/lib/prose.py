"""Information, not prose, defined once. Read by no-prose.py (PreToolUse) and no-prose-stop.py (Stop).

The pattern list lives in prose_patterns.json beside this file. Each pattern has a slug, a family, a
one-line fix and the scope flags reply, answer and copy (same meaning as in noise_patterns.json). A
pattern may also carry `requires` (the sentence around the hit must match it), `unless` (the hit is
dropped when the sentence matches it) and `min_words`. `requires` and `unless` are case-sensitive on
purpose: a payer clause needs a subject, and "the state grants" has one while "relief granted" does
not.

The five families, each a shape a regex can see:
  1  CAPTION FOR A LINK         a noun phrase ending in a colon in front of a link.
  2  FIGURE WITHOUT A PAYER     a percent or dollar figure about money with no clause saying who pays.
  3  METAPHOR FOR THE PRODUCT   "under the hood", "secret sauce", "the magic", in outward copy.
  4  LABEL, NOT A SENTENCE      a noun phrase ending in a colon alone on a line, then prose or a link.
  5  MODIFIER TAIL ON A NAME    a tagline or headline with a clause hung off the plain noun.

The quoting carve: fenced code, inline `backtick` spans, '>' blockquotes and double-quoted spans of
twelve characters or more are stripped before a reply or a file is scanned. URLs are not stripped.
They become the token <url> in every scan, so a caption before a link can be seen.

    python3 prose.py --selftest
    python3 prose.py [--scope answer|copy|reply|all] "text"      (exit 2 on a hit)
    python3 prose.py [--scope ...] --file path
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "prose_patterns.json")
with open(SPEC_PATH, encoding="utf-8") as _fh:
    SPEC = json.load(_fh)

RULE = SPEC["rule"]                 # for text written on the user's behalf, and for replies
COPY_RULE = SPEC["copy_rule"]       # for product copy
FAMILIES = SPEC["families"]
SCOPES = ("answer", "copy", "reply", "all")


def _compile(p):
    d = dict(p)
    d["re"] = re.compile(p["pattern"], re.I | re.M)
    d["requires_re"] = re.compile(p["requires"]) if p.get("requires") else None
    d["unless_re"] = re.compile(p["unless"]) if p.get("unless") else None
    return d


PATTERNS = [_compile(p) for p in SPEC["patterns"]]


def patterns_for(scope="answer", families=None):
    if scope not in SCOPES:
        raise ValueError("scope must be one of %s" % (SCOPES,))
    out = []
    for p in PATTERNS:
        if scope != "all" and not p.get(scope):
            continue
        if families and p["family"] not in families:
            continue
        out.append(p)
    return out


# the quoting carve
FENCE = re.compile(r"```.*?```", re.S)
FENCE_OPEN = re.compile(r"```.*\Z", re.S)
INLINE = re.compile(r"`[^`\n]*`")
BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)
URL = re.compile("https?://[^\\s\"”'<>)\\]]+|(?:~|/home|/Users)/[\\w./~-]+")
QUOTED = re.compile("[“\"][^“”\"\n]{12,}[”\"]")
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def urls_to_token(text):
    """Every URL and path becomes the token <url>, so a caption before a link keeps its shape."""
    return URL.sub("<url>", str(text or ""))


def prose_of(text):
    """Strip quoted material so only the writer's own sentences remain."""
    # A fence or a blockquote leaves a list marker behind, so a label above it still reads as a
    # heading over quoted material and not as a label over prose.
    t = FENCE.sub("\n- (quoted)\n", text or "")
    t = FENCE_OPEN.sub("\n- (quoted)\n", t)
    t = INLINE.sub(" ", t)
    t = BLOCKQUOTE.sub("> (quoted)", t)
    t = urls_to_token(t)
    return QUOTED.sub(" ", t)


def _sentence_around(text, index):
    pos = 0
    for s in _SENT.split(text):
        end = pos + len(s)
        if pos <= index < end:
            return " ".join(s.split())
        pos = end + 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return " ".join(text[max(0, index - 80):index + 120].split())


_WORD = re.compile(r"[A-Za-z][A-Za-z']*")


def _word_count(s):
    return len(_WORD.findall(s))


def prose_issues(text, scope="answer", families=None):
    """Every pattern in scope that fires, one hit per pattern:
    [{slug, family, fix, fragment, sentence}]. URLs are replaced by <url> first. Everything else is
    scanned raw. Call prose_of() first when the text is prose about the rule (a reply, a rule file)
    rather than the output itself."""
    t = urls_to_token(text)
    out = []
    for p in patterns_for(scope, families):
        hit = None
        for m in p["re"].finditer(t):
            # A pattern may open on the end of the previous sentence, so the sentence reported is
            # the one around the first word of the match.
            off = len(m.group(0)) - len(m.group(0).lstrip(".!? \t\n"))
            sentence = _sentence_around(t, m.start() + off)
            if p.get("min_words") and _word_count(sentence) < p["min_words"]:
                continue
            if p["requires_re"] is not None and not p["requires_re"].search(sentence):
                continue
            if p["unless_re"] is not None and p["unless_re"].search(sentence):
                continue
            hit = (m.group(0).strip(".!? \t\n"), sentence)
            break
        if hit:
            out.append({"slug": p["slug"], "family": p["family"], "fix": p["fix"],
                        "fragment": " ".join(hit[0].split())[:200], "sentence": hit[1]})
    return out


def prose_issue(text, scope="answer", families=None):
    hits = prose_issues(text, scope, families)
    return hits[0] if hits else None


def scan_reply(reply):
    """Hits in a chat reply: quoted material stripped, reply subset only. None when clean."""
    return prose_issues(prose_of(reply), "reply") or None


def scan_copy(text, quoted=False):
    return prose_issues(prose_of(text) if quoted else text, "copy") or None


def scan_answer(text, quoted=False):
    return prose_issues(prose_of(text) if quoted else text, "answer") or None


def retry_note(hit, scope="answer"):
    """A note to append to a prompt when a model's first draft carried prose."""
    h = hit[0] if isinstance(hit, list) else hit
    quoted = str((h or {}).get("sentence") or (h or {}).get("fragment") or "")[:240]
    fix = str((h or {}).get("fix") or "write the plain sentence")
    rule = COPY_RULE if scope == "copy" else RULE
    return ("\n\n## This is a rewrite. The previous answer was rejected.\n\n"
            "It carried prose in place of information: \"%s\"\nFix: %s\n\n%s\n\n"
            "Return the whole answer again with that sentence rewritten as plain sentences, one fact "
            "each, subject, verb, object. Do not add a new fact. Drop one if the length needs it.\n"
            % (quoted, fix, rule))


def compose_without_prose(compose, scope="answer", quiet=True, log=print, label="compose"):
    """compose(note) returns text. It is called with '' first, then once with the rewrite note.
    Returns (text, None) on success and (None, hit) when the rewrite still carries prose."""
    text = compose("")
    hit = prose_issue(text, scope)
    if not hit:
        return text, None
    if not quiet:
        log("  %s: prose (%s: \"%s\"), rewriting once with the rule restated" % (label, hit["slug"], hit["fragment"]))
    text = compose(retry_note(hit, scope))
    hit = prose_issue(text, scope)
    if not hit:
        return text, None
    if not quiet:
        log("  %s: refused, still prose after the rewrite (%s: \"%s\")" % (label, hit["slug"], hit["fragment"]))
    return None, hit


def brief(scope="copy"):
    """The rule plus failing and passing examples, rendered from the JSON for use in a prompt."""
    fams = ["1", "2", "3", "4", "5"]
    lines = [COPY_RULE if scope == "copy" else RULE, "", "Sentences that fail this rule:"]
    for f in fams:
        lines += ["  " + s.replace("\n", " / ") for s in SPEC["positives"][f][:3]]
    lines += ["", "Sentences that pass it:"]
    for f in fams:
        lines += ["  " + s.replace("\n", " / ") for s in SPEC["negatives"][f][:2]]
    return "\n".join(lines)


BLOCK_TEXT = """Write information, not prose.

Ask who reads the sentence and what they need from it. Write one fact per sentence, with a subject,
a verb and an object. Use the reader's words and the product's own words.

Five shapes are blocked:
  1 Caption for a link: "A four-minute tour of the product: <link>".
    Write: "Here is a demo video: <link>".
  2 Figure without a payer: "25 percent of relief granted".
    Write: "You pay 25 percent of what the state grants."
  3 Metaphor for the product: "under the hood", "secret sauce", "the magic".
    Write what the part is called and what it does.
  4 Label in place of a sentence: a noun phrase ending in a colon alone on a line, then prose.
    Write the sentence the label stands for.
  5 Modifier tail on a name: "four boards, recounted every night".
    Write the plain noun: "four ranking sites".

A length limit is met by dropping a fact, never by deleting the subject or verb from a fact.
To quote one of these shapes on purpose, put it in a fenced code block, an inline `backtick`
span, a '>' blockquote or "double quotes". Quoted material is not scanned."""


def selftest():
    bad = []
    for fam, sents in SPEC["positives"].items():
        for s in sents:
            hits = prose_issues(s, "all")
            if not any(str(h["family"]) == fam for h in hits):
                bad.append("POSITIVE (family %s) not caught by its family: %r  [hits: %s]"
                           % (fam, s, [h["slug"] for h in hits]))
    for fam, sents in SPEC["negatives"].items():
        for s in sents:
            hits = prose_issues(s, "all")
            if hits:
                bad.append("NEGATIVE (family %s) flagged (%s: %r): %r" % (fam, hits[0]["slug"], hits[0]["fragment"], s))
    for fam in FAMILIES:
        if len(SPEC["positives"][fam]) < 10 or len(SPEC["negatives"][fam]) < 10:
            bad.append("family %s needs at least 10 positives and 10 negatives" % fam)
    # every pattern fires on at least one positive of its own family, so no pattern ships inert
    for p in PATTERNS:
        if not any(any(h["slug"] == p["slug"] for h in prose_issues(s, "all"))
                   for s in SPEC["positives"][str(p["family"])]):
            bad.append("INERT pattern (no positive of family %s fires it): %s" % (p["family"], p["slug"]))
    # two failing sentences and their correct rewrites, in the answer scope
    FAIL_1 = "Lines come back in 48 hours, 25 percent of relief granted, nothing if nothing is found."
    FAIL_2 = "A four-minute tour of the product: https://example.com/share/demo"
    OK_1 = ("You get the scored lines and drafted protests back inside 48 hours. "
            "You pay 25 percent of what the state grants, and nothing if we find nothing.")
    OK_2 = "Here is a demo video: https://example.com/share/demo"
    if not scan_answer(FAIL_1):
        bad.append("answer scan missed the 48-hours sentence")
    if not scan_answer(FAIL_2):
        bad.append("answer scan missed the caption before a link")
    if scan_answer(OK_1) or scan_answer(OK_2):
        bad.append("answer scan flagged a correct sentence: %s" % (scan_answer(OK_1) or scan_answer(OK_2)))
    if not scan_reply(FAIL_2):
        bad.append("reply scan missed the caption before a link")
    if scan_reply(OK_1 + "\n" + OK_2):
        bad.append("reply scan flagged the correct sentences")
    # the quoting carve
    if scan_reply('The draft read "A four-minute tour of the product: https://x.y/z" and is gone.'):
        bad.append("quoting carve failed on a reply")
    if scan_reply("The draft:\n```\nA four-minute tour of the product: https://x.y/z\n```\nis gone."):
        bad.append("fence carve failed on a reply")
    if scan_reply("The hook, the JSON list beside it, and the test all pass. Files written:\n- prose.py\n- prose.cjs"):
        bad.append("reply scan flagged an ordinary engineering reply")
    # the rewrite path
    calls = []
    text, hit = compose_without_prose(lambda n: (calls.append(n), SPEC["positives"]["3"][1])[1], "copy")
    if text is not None or not hit or len(calls) != 2 or COPY_RULE not in calls[1]:
        bad.append("compose_without_prose did not refuse after one restated rewrite")
    text, hit = compose_without_prose(lambda n: SPEC["positives"]["3"][1] if not n else SPEC["negatives"]["3"][1], "copy")
    if text != SPEC["negatives"]["3"][1] or hit:
        bad.append("compose_without_prose did not accept the fixed rewrite")
    for b in bad:
        print("FAIL", b)
    n_pos = sum(len(v) for v in SPEC["positives"].values())
    n_neg = sum(len(v) for v in SPEC["negatives"].values())
    print("prose.py selftest: %d positives, %d negatives, %d patterns, %s"
          % (n_pos, n_neg, len(PATTERNS), "FAILED" if bad else "ok"))
    return 1 if bad else 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    scope = "answer"
    if "--scope" in argv:
        i = argv.index("--scope")
        scope = argv[i + 1]
        del argv[i:i + 2]
    if "--file" in argv:
        i = argv.index("--file")
        with open(argv[i + 1], encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    else:
        text = " ".join(argv) or sys.stdin.read()
    hits = prose_issues(text, scope)
    if not hits:
        print("clean")
        sys.exit(0)
    for h in hits:
        print("%s (family %s): \"%s\"  in  \"%s\"\n  fix: %s" % (h["slug"], h["family"], h["fragment"], h["sentence"][:200], h["fix"]))
    sys.exit(2)
