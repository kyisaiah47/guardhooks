"""The noise ban, defined once. Read by no-noise.py (PreToolUse) and no-noise-stop.py (Stop).

The pattern list lives in noise_patterns.json beside this file. Each pattern has a slug, a family,
a one-line fix and three scope flags:
  reply    the Stop hook applies it to chat replies.
  answer   applied to text written on the user's behalf: form answers, prompts, email replies.
  copy     applied to product copy: landing pages, posts, captions, cards, listings.

The five families:
  1  PERFORMED SINCERITY    announcing honesty instead of being honest: "to be honest",
                            "honestly", "full disclosure", "I want to be clear", "real talk".
  2  EUPHEMISM FOR NO       saying no without the word: "X is my gap", "not my strongest area",
                            "I'd pick it up on the job", "limited exposure". The answer to
                            "experience with X?" when there is none is "No experience."
  3  NARRATING THE ANSWER   a sentence about the answer instead of the answer: "I should note",
                            "it's worth mentioning", "I'd say", "the short version is", "that said".
  4  FILLER IN COPY         padding instead of what the product does: "designed to", "seamlessly",
                            "powerful", "streamline", "whether you're X or Y", "the ultimate".
  5  COPY THAT ARGUES       the product, its output or the team's own work called unwanted,
     AGAINST THE PRODUCT    unasked for, a toy or useless. A plain stated limit is not this.

The quoting carve: fenced code, inline `backtick` spans, '>' blockquotes, URLs, paths and any
double-quoted span of twelve characters or more are stripped before a reply or a prose file is
scanned, because a rule about this ban has to name the phrases. A writer's own output (a post, a
form answer) is scanned raw.

    python3 noise.py --selftest
    python3 noise.py [--scope answer|copy|reply|all] "text"      (exit 2 on a hit)
    python3 noise.py [--scope ...] --file path
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "noise_patterns.json")
with open(SPEC_PATH, encoding="utf-8") as _fh:
    SPEC = json.load(_fh)

RULE = SPEC["rule"]                 # families 1-3, for text written on the user's behalf
COPY_RULE = SPEC["copy_rule"]       # families 4-5, for product copy
FAMILIES = SPEC["families"]
PATTERNS = [dict(p, re=re.compile(p["pattern"], re.I)) for p in SPEC["patterns"]]
SCOPES = ("answer", "copy", "reply", "all")


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
URL = re.compile(r"https?://\S+|(?:~|/home|/Users)/[\w./~-]+")
QUOTED = re.compile("[“\"][^“”\"\n]{12,}[”\"]")
_SENT = re.compile(r"(?<=[.!?])\s+")


def prose_of(text):
    """Strip quoted material so only the writer's own sentences remain."""
    t = FENCE.sub(" ", text or "")
    t = FENCE_OPEN.sub(" ", t)
    t = INLINE.sub(" ", t)
    t = BLOCKQUOTE.sub(" ", t)
    t = URL.sub(" ", t)
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


def noise_issues(text, scope="answer", families=None):
    """Every pattern in scope that fires, one hit per pattern:
    [{slug, family, fix, fragment, sentence}]. The text is scanned raw. Call prose_of() first when
    the text is prose about the ban (a reply, a rule file) rather than the output itself."""
    t = str(text or "")
    out = []
    for p in patterns_for(scope, families):
        m = p["re"].search(t)
        if not m:
            continue
        out.append({"slug": p["slug"], "family": p["family"], "fix": p["fix"],
                    "fragment": m.group(0).strip(), "sentence": _sentence_around(t, m.start())})
    return out


def noise_issue(text, scope="answer", families=None):
    hits = noise_issues(text, scope, families)
    return hits[0] if hits else None


def scan_reply(reply):
    """Hits in a chat reply: quoted material stripped, reply subset only. None when clean."""
    return noise_issues(prose_of(reply), "reply") or None


def scan_copy(text, quoted=False):
    return noise_issues(prose_of(text) if quoted else text, "copy") or None


def scan_answer(text, quoted=False):
    return noise_issues(prose_of(text) if quoted else text, "answer") or None


def retry_note(hit, scope="answer"):
    """A note to append to a prompt when a model's first draft carried noise."""
    h = hit[0] if isinstance(hit, list) else hit
    quoted = str((h or {}).get("sentence") or (h or {}).get("fragment") or "")[:240]
    fix = str((h or {}).get("fix") or "delete it")
    rule = COPY_RULE if scope == "copy" else RULE
    return ("\n\n## This is a rewrite. The previous answer was rejected.\n\n"
            "It carried noise: \"%s\"\nFix: %s\n\n%s\n\n"
            "Return the whole answer again with that sentence gone. Do not add a new sentence that "
            "does the same job. Do not add a new fact to fill the space; shorten instead.\n"
            % (quoted, fix, rule))


def compose_without_noise(compose, scope="answer", quiet=True, log=print, label="compose"):
    """compose(note) returns text. It is called with '' first, then once with the rewrite note.
    Returns (text, None) on success and (None, hit) when the rewrite still carries noise."""
    text = compose("")
    hit = noise_issue(text, scope)
    if not hit:
        return text, None
    if not quiet:
        log("  %s: noise (%s: \"%s\"), rewriting once with the rule restated" % (label, hit["slug"], hit["fragment"]))
    text = compose(retry_note(hit, scope))
    hit = noise_issue(text, scope)
    if not hit:
        return text, None
    if not quiet:
        log("  %s: refused, still noise after the rewrite (%s: \"%s\")" % (label, hit["slug"], hit["fragment"]))
    return None, hit


def brief(scope="copy"):
    """The rule plus failing and passing examples, rendered from the JSON for use in a prompt."""
    fams = ["4", "5"] if scope == "copy" else ["1", "2", "3"]
    lines = [COPY_RULE if scope == "copy" else RULE, "", "Sentences that fail this rule:"]
    for f in fams:
        lines += ["  " + s for s in SPEC["positives"][f][:8]]
    lines += ["", "Sentences that pass it:"]
    for f in fams:
        lines += ["  " + s for s in SPEC["negatives"][f][:5]]
    return "\n".join(lines)


BLOCK_TEXT = """Noise is not allowed in any output.

Five kinds of noise are blocked:
  1 Performed sincerity: "to be honest", "honestly", "full disclosure", "I want to be clear",
    "let me be clear", "real talk".
  2 Euphemism for no: "X is my gap", "not something I'd claim depth in", "not my strongest
    area", "I'd pick it up", "limited exposure", "less familiar", "still growing there".
    The answer is "No experience." or "None." with no pivot after it.
  3 Narrating the answer: "I should note", "it's worth mentioning", "I'd say", "it's fair to
    say", "the short version is", "put simply", "in other words", "that said",
    "at the end of the day".
  4 Filler in product copy: "designed to", "seamlessly", "powerful", "robust", "streamline",
    "whether you're X or Y", "say goodbye to", "we're excited to", "Introducing",
    "the ultimate", "peace of mind", or a question used as a hook.
  5 Copy that argues against the product: calling it unwanted, unasked for, a toy or useless,
    or selling a paid tier by what it does not give. A plain stated limit is allowed.

Delete the sentence. Do not soften it. The answer stays and the noise goes.
To quote one of these phrases on purpose, put it in a fenced code block, an inline `backtick`
span, a '>' blockquote or "double quotes". Quoted material is not scanned."""


def selftest():
    bad = []
    scope_for = {"1": "answer", "2": "answer", "3": "answer", "4": "copy", "5": "copy"}
    for fam, sents in SPEC["positives"].items():
        for s in sents:
            hits = noise_issues(s, scope_for[fam])
            if not any(str(h["family"]) == fam for h in hits):
                bad.append("POSITIVE (family %s) not caught by its family: %s  [hits: %s]"
                           % (fam, s, [h["slug"] for h in hits]))
    for fam, sents in SPEC["negatives"].items():
        for s in sents:
            hits = noise_issues(s, "all")
            if hits:
                bad.append("NEGATIVE (family %s) flagged (%s): %s" % (fam, hits[0]["slug"], s))
    for fam in ("1", "2", "3", "4"):
        if len(SPEC["positives"][fam]) < 15 or len(SPEC["negatives"][fam]) < 15:
            bad.append("family %s needs at least 15 positives and 15 negatives" % fam)
    # every pattern fires on at least one positive of its own family, so no pattern ships inert
    for p in PATTERNS:
        if not any(p["re"].search(s) for s in SPEC["positives"][str(p["family"])]):
            bad.append("INERT pattern (no positive of family %s fires it): %s" % (p["family"], p["slug"]))
    # the quoting carve
    if scan_reply('The regex bans "to be honest" and the file says `honestly` in a code span.'):
        bad.append("quoting carve failed on a reply")
    if not scan_reply("To be honest, the job has not run since Tuesday."):
        bad.append("reply scan missed a bare honesty preface")
    # the rewrite path
    calls = []
    text, hit = compose_without_noise(lambda n: (calls.append(n), SPEC["positives"]["1"][0])[1])
    if text is not None or not hit or len(calls) != 2 or RULE not in calls[1]:
        bad.append("compose_without_noise did not refuse after one restated rewrite")
    text, hit = compose_without_noise(lambda n: SPEC["positives"]["1"][0] if not n else SPEC["negatives"]["2"][9])
    if text != SPEC["negatives"]["2"][9] or hit:
        bad.append("compose_without_noise did not accept the fixed rewrite")
    for b in bad:
        print("FAIL", b)
    n_pos = sum(len(v) for v in SPEC["positives"].values())
    n_neg = sum(len(v) for v in SPEC["negatives"].values())
    print("noise.py selftest: %d positives, %d negatives, %d patterns, %s"
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
    hits = noise_issues(text, scope)
    if not hits:
        print("clean")
        sys.exit(0)
    for h in hits:
        print("%s (family %s): \"%s\"  in  \"%s\"\n  fix: %s" % (h["slug"], h["family"], h["fragment"], h["sentence"][:200], h["fix"]))
    sys.exit(2)
