"""Compare what the user asked for with what is about to happen.

Most guards check an action against a list of known bad shapes, so each one only catches the
failure it was written after. This one holds no failure shapes. It reads a verb and an object out
of the user's recent prompts, reads a verb and an object out of the tool call about to run, and
reports when they disagree on the same object.

The distinction it enforces:
  The TARGET is what changes. The user names it with the verb.
  The MODEL is what the result should resemble. Naming it is not permission to edit it.
  "make A match B" means B is the reference and A changes.
  "do it like X" describes the output. It is not a request to edit X.
"""
import json
import os
import re

import guardhooks_core as G


def _load():
    try:
        return G.load_json("instruction_match_patterns.json")
    except Exception:
        return {"verbs": {}, "conflicts": [], "object_stopwords": [], "boundaries": [],
                "side_effecting_tools": []}


RAW = _load()
VERBS = RAW.get("verbs", {})
CONFLICTS = {tuple(sorted(p)) for p in RAW.get("conflicts", []) if len(p) == 2}
STOP = set(w.lower() for w in RAW.get("object_stopwords", []))
SIDE_EFFECTING = set(RAW.get("side_effecting_tools", []))

# Prepositions end the object. "add the numbers to the deck" is an edit of the deck.
_REDIRECT = r"\b(?:to|into|onto|in|on|from|for|at|about|against|under|over|within|per)\b"
_BOUNDARY = re.compile("|".join(RAW.get("boundaries", []) + [_REDIRECT, r"\n"]), re.I)

_NEGATION = re.compile(r"(?:do\s*n[o']?t|don't|dont|never|no\s+need\s+to|instead\s+of|"
                       r"rather\s+than|without|avoid|stop)\s*$", re.I)


def _verb_rx():
    out = {}
    for cls, words in VERBS.items():
        words = sorted(words, key=len, reverse=True)
        alts = "|".join(re.escape(w).replace(r"\ ", r"\s+") for w in words)
        out[cls] = re.compile(r"\b(%s)\b" % alts, re.I)
    return out


VERB_RX = _verb_rx()
_WORD = re.compile(r"[a-z0-9]+")


def _stem(w):
    w = w.lower()
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def object_words(phrase):
    """Content words of an object phrase, stemmed, with generic nouns dropped."""
    out = []
    for w in _WORD.findall((phrase or "").lower()):
        if w in STOP or len(w) < 3:
            continue
        s = _stem(w)
        if s in STOP or len(s) < 3:
            continue
        if s not in out:
            out.append(s)
    return out


def head_noun(words):
    """The one word that names the thing. Matching on every word of an object phrase makes
    coincidental path segments look like the named object."""
    return words[-1] if words else ""


_NOT_AN_OBJECT = re.compile(r"^(?:sure|out|off|up|down|back)\b", re.I)

# "update it", "change that", "edit the existing one": the object is the one last named. This only
# rebinds toward edit or delete, never toward create, so it can only remove blocks.
_ANAPHOR = re.compile(r"^(?:it|that|this|them|those|these|the\s+(?:existing|same|current|old)"
                      r"\s+(?:one|ones)?|the\s+one)\b", re.I)

# Paths that are never the user's artifact: notes, scratch space, caches, hooks.
_NEVER_THEIRS = re.compile(
    r"(?:/memory/|/\.claude[\w.-]*/|/scratchpad/|^/private/tmp|^/tmp/|/node_modules/|"
    r"/\.git/|/state/|\.bak(?:-|$)|/hooks/)", re.I)


def clauses(text, limit=40):
    """Every (verb, class, object) in the text, in order. A negated verb is dropped: a brief that
    says "do not build a new deck" is not an instruction to build one."""
    if not text:
        return []
    found = []
    for cls, rx in VERB_RX.items():
        for m in rx.finditer(text):
            before = text[max(0, m.start() - 22):m.start()]
            if _NEGATION.search(before):
                continue
            tail = text[m.end():m.end() + 90]
            if _NOT_AN_OBJECT.match(tail.lstrip()):
                continue
            b = _BOUNDARY.search(tail)
            phrase = tail[:b.start()] if b else tail
            words = object_words(phrase)
            if not words:
                if _ANAPHOR.match(tail.lstrip()) and cls in ("edit", "delete"):
                    found.append({"verb": m.group(1).lower(), "cls": cls, "at": m.start(),
                                  "object": " ".join(tail.split())[:60], "words": [],
                                  "anaphor": True})
                continue
            found.append({"verb": m.group(1).lower(), "cls": cls, "at": m.start(),
                          "object": " ".join(phrase.split())[:60], "words": words})
    found.sort(key=lambda c: c["at"])
    return found[:limit]


def instruction(prompts):
    """What the user asked for, as {object word: clause}.

    It reads a window of recent prompts, because the verb and the object often arrive in
    different messages. A new message does not cancel the previous one. The last clause on an
    object wins, so a real reversal ("actually just update it") counts as a reversal.
    """
    byword, order = {}, []
    plist = [p for p in (prompts or []) if p and p.strip()]
    for i, p in enumerate(plist):
        last = (i == len(plist) - 1)
        for c in clauses(p):
            if c["cls"] not in ("create", "edit", "delete"):
                continue
            if c.get("anaphor"):
                if last and order:
                    prev = byword[order[-1]]
                    byword[order[-1]] = dict(c, words=prev["words"], object=prev["object"])
                continue
            h = head_noun(c["words"])
            if not h:
                continue
            if h not in byword:
                order.append(h)
            byword[h] = c
    return byword, order


def planned(tool_name, tool_input):
    """What is about to happen, in the same terms.

    A Write to a path that does not exist is a create. Every other file write is an edit. An
    Agent or Task brief is parsed the same way a prompt is: the PreToolUse payload carries the
    brief at tool_input.prompt and its title at tool_input.description.
    """
    ti = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in ("Agent", "Task"):
        desc = ti.get("description") or ""
        brief = ti.get("prompt") or ""
        if not (desc or brief).strip():
            return None
        head = desc + ". " + brief[:900]
        for c in clauses(head):
            if c["cls"] in ("create", "edit", "delete") and head_noun(c["words"]):
                return {"cls": c["cls"], "verb": c["verb"], "words": [head_noun(c["words"])],
                        "object": c["object"], "kind": "brief",
                        "where": "the agent brief titled %r" % (desc[:60] or "untitled")}
        return None

    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path or _NEVER_THEIRS.search(path):
        return None
    exists = os.path.exists(os.path.expanduser(path))
    cls = "edit" if (tool_name != "Write" or exists) else "create"
    stem = os.path.splitext(os.path.basename(path))[0]
    words = object_words(stem.replace("-", " ").replace("_", " ").replace(".", " "))
    h = head_noun(words)
    return {"cls": cls, "verb": tool_name.lower(), "words": [h] if h else [],
            "object": path, "kind": "file", "exists": exists,
            "where": "%s on %s" % (tool_name, path)}


# The user said the thing already exists. Without this, editing a generator script would read as
# editing the thing the user asked to create.
_EXISTS = re.compile(
    r"\bwe\s+(?:already\s+have|have|got|made|built)\b[^.?!]{0,80}\balready\b"
    r"|\bwe\s+already\s+(?:have|made|built|did|wrote|got)\b"
    r"|\b(?:there\s+is|there's|theres|we've\s+got|weve\s+got)\b[^.?!]{0,60}\balready\b"
    r"|\bthe\s+(?:existing|current|old|previous|original)\s+[a-z]{3,}"
    r"|\b(?:one|ones)\s+(?:we|you|i)\s+(?:have|made|built|use|used|already)\b", re.I)


def asserts_exists(prompts, noun):
    """Did the user say an artifact of this kind already exists, as the thing to copy?"""
    for p in prompts or []:
        for m in _EXISTS.finditer(p or ""):
            span = (p[max(0, m.start() - 40):m.end() + 60]).lower()
            if noun in [_stem(w) for w in _WORD.findall(span)]:
                return " ".join(m.group(0).split())[:80]
    return ""


def divergence(byword, plan, prompts=None):
    """The first object the user named that the planned action treats with a conflicting verb.
    No shared object means no verdict."""
    if not plan or not byword:
        return None
    for w in plan.get("words", []):
        theirs = byword.get(w)
        if not theirs:
            continue
        if tuple(sorted((theirs["cls"], plan["cls"]))) not in CONFLICTS:
            continue
        if plan.get("kind") == "file":
            # A file edit only diverges when the file is the thing the user said already exists.
            ex = asserts_exists(prompts, w)
            if not (ex and plan.get("exists")):
                continue
            return {"noun": w, "theirs": theirs, "plan": plan, "exists": ex}
        return {"noun": w, "theirs": theirs, "plan": plan, "exists": ""}
    return None


def declaration_contradicts(declaration, d):
    """True when a declared reason still uses a verb that conflicts with the user's on the same
    object. Such a declaration only rewords the divergence, so it is ignored. Every content word
    of each clause counts here, not only the head noun, so "update the deck slides" still names
    the deck."""
    for c in clauses(declaration or ""):
        if c["cls"] not in ("create", "edit", "delete") or d["noun"] not in c["words"]:
            continue
        if tuple(sorted((d["theirs"]["cls"], c["cls"]))) in CONFLICTS:
            return True
    return False


# ---- transcript reading --------------------------------------------------------------------
def _text_of(msg):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") in (None, "text"))
    return ""


_SYNTHETIC = ("<task-notification", "<system-reminder", "<command-name", "<local-command",
              "stop hook feedback", "[request interrupted", "caveat: the messages below",
              "<user-prompt-submit-hook", "base directory for this skill", "[image:",
              "<additional-context", "<budget:", "this session is being continued")

# A user frame is not always the user. An agent brief, a cross-session note and a headless run's
# opening prompt all arrive as user messages, and none of them is the user's instruction.
_NOT_THE_USER = re.compile(
    r"<cross-session-message|another\s+claude\s+session|^you\s+are\s+(?:a|an|the|finishing|"
    r"building|working)|\bthe\s+user\s+(?:decided|said|wants|asked|approved|is\s+asking)|"
    r"^base\s+directory\s+for\s+this\s+skill", re.I)


def is_the_user(text, index=None):
    if _NOT_THE_USER.search(text or ""):
        return False
    if index == 0 and len(text or "") > 300:
        return False
    return True


def is_real_prompt(text, content):
    """A tool_result frame has role=user too, and so do hook injections and notices."""
    if not text or not text.strip():
        return False
    if text.lstrip()[:60].lower().startswith(_SYNTHETIC):
        return False
    try:
        if "tool_use_id" in json.dumps(content)[:400]:
            return False
    except Exception:
        pass
    return True


def user_window(transcript_path, n=3):
    """The user's last n real prompts, oldest first."""
    out, seen = [], []
    for d in G.iter_transcript(transcript_path):
        m = d.get("message") or {}
        if m.get("role") != "user":
            continue
        t = _text_of(m)
        if is_real_prompt(t, m.get("content")):
            idx = len(seen)
            seen.append(t)
            if is_the_user(t, idx):
                out.append(t)
    return out[-n:]
