"""Shared helpers for every GuardHooks hook.

Each hook reads one JSON event from stdin and answers in one of three ways.

  PreToolUse        deny(reason) prints a permissionDecision of "deny". Claude Code refuses the
                    tool call and shows the reason to the model.
  UserPromptSubmit  context(text) prints text that Claude Code adds next to the prompt.
  Stop              block(text) writes the reason to stderr and exits 2. Claude Code keeps the
                    turn open and the model rewrites the reply.

A hook that cannot load its own files or parse its input exits 0 and stays silent. A broken guard
must never block work.

Paths are never hard-coded. The config directory is $CLAUDE_CONFIG_DIR when it is set and
~/.claude otherwise. State that a hook keeps lives under <config>/guardhooks/state/.
"""
import json
import os
import re
import sys
import time
import unicodedata


# ---------------------------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------------------------
def config_dir():
    """The Claude Code config directory: $CLAUDE_CONFIG_DIR, or ~/.claude."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def state_dir(*parts):
    """A directory under <config>/guardhooks/state/ for a hook's own state. Created on demand."""
    d = os.path.join(config_dir(), "guardhooks", "state", *parts)
    os.makedirs(d, exist_ok=True)
    return d


def lib_dir():
    return os.path.dirname(os.path.abspath(__file__))


def load_json(name):
    """Load a pattern list that sits beside this file in lib/."""
    with open(os.path.join(lib_dir(), name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------------------------
# input and output
# ---------------------------------------------------------------------------------------------
def read_event():
    """The hook event from stdin as a dict, or None when stdin is not JSON."""
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return None
    return ev if isinstance(ev, dict) else None


def deny(reason):
    """PreToolUse: refuse the tool call with this reason. Exits."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def context(text, event="UserPromptSubmit"):
    """UserPromptSubmit or PreToolUse: add this text to what the model sees. Exits."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": text,
        }
    }))
    sys.exit(0)


def block(text):
    """Stop: keep the turn open and tell the model why. Exits with code 2."""
    sys.stderr.write(text.rstrip() + "\n")
    sys.exit(2)


def allow():
    sys.exit(0)


# ---------------------------------------------------------------------------------------------
# what a tool call is about to write
# ---------------------------------------------------------------------------------------------
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def target_path(tool_input):
    return str((tool_input or {}).get("file_path") or (tool_input or {}).get("notebook_path") or "")


def new_text(tool_input):
    """Only the NEW text of a write: Write content, Edit new_string, MultiEdit new strings and
    NotebookEdit new_source. Text already in the file is never scanned."""
    ti = tool_input or {}
    parts = []
    for key in ("content", "new_string", "new_source"):
        if ti.get(key) is not None:
            parts.append(str(ti[key]))
    if isinstance(ti.get("edits"), list):
        parts += [str((e or {}).get("new_string") or "") for e in ti["edits"] if isinstance(e, dict)]
    return "\n".join(parts)


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1\s*\n(.*?)^\s*\2\s*$", re.S | re.M)


def heredoc_bodies(command):
    return [m.group(3) for m in HEREDOC.finditer(command or "")]


# ---------------------------------------------------------------------------------------------
# the quoting carve
#
# A rule about a banned phrase has to be able to name it. Fenced code, inline `backtick` spans and
# '>' blockquotes are stripped before a reply or a prose file is scanned, so quoted material passes
# byte for byte. Writing the phrase in your own sentence is what fails.
# ---------------------------------------------------------------------------------------------
FENCE = re.compile(r"```.*?```", re.S)
FENCE_OPEN = re.compile(r"```.*\Z", re.S)
INLINE = re.compile(r"`[^`\n]*`")
BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)


def strip_quoted(text, double_quotes_min=None):
    """Remove quoted material. With double_quotes_min set, a double-quoted span at least that
    many characters long counts as a quotation too."""
    t = FENCE.sub(" ", text or "")
    t = FENCE_OPEN.sub(" ", t)
    t = INLINE.sub(" ", t)
    t = BLOCKQUOTE.sub(" ", t)
    if double_quotes_min:
        t = re.compile("[“\"][^“”\"\n]{%d,}[”\"]" % int(double_quotes_min)).sub(" ", t)
    return t


# ---------------------------------------------------------------------------------------------
# transcripts
# ---------------------------------------------------------------------------------------------
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def norm(t):
    """Lowercase, strip punctuation and collapse whitespace, so typography never decides a match."""
    t = unicodedata.normalize("NFKD", t or "")
    t = t.replace("\u2014", " ").replace("\u2013", " ")
    t = _PUNCT.sub(" ", t.lower())
    return _WS.sub(" ", t).strip()


def _text_of(msg, kinds=("text",)):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") in kinds)
    return ""


def iter_transcript(path):
    """Yield each JSON line of a Claude Code transcript. Bad lines are skipped."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if isinstance(d, dict):
                    yield d
    except OSError:
        return


def read_session(transcript_path):
    """Return (reply, evidence_norm, evidence_raw, has_image, last_prompt).

    reply          the final assistant text of this turn.
    evidence_*     everything the session has seen, EXCEPT this turn's assistant text. A reply is
                   never evidence for itself, or a made-up quote would match its own sentence.
    has_image      the session contains an image block.
    last_prompt    the text of the user's most recent real prompt.
    """
    reply, has_image, last_prompt = "", False, ""
    frames = []
    turn_mark = 0
    for d in iter_transcript(transcript_path):
        m = d.get("message") or {}
        role, content = m.get("role"), m.get("content")
        raw = json.dumps(content) if content is not None else ""
        if '"image"' in raw or '"base64"' in raw:
            has_image = True
        if role == "user":
            t = _text_of(m)
            if t.strip() and "tool_use_id" not in raw[:400]:
                turn_mark = len(frames)
                last_prompt = t
            frames.append((False, raw))
        elif role == "assistant":
            t = _text_of(m)
            if t.strip():
                reply = t
                frames.append((True, raw))
            else:
                frames.append((False, raw))
        else:
            frames.append((False, raw))
    kept = [raw for i, (is_text, raw) in enumerate(frames) if not (is_text and i >= turn_mark)]
    joined = " ".join(kept)
    return reply, norm(joined), joined, has_image, last_prompt


def stop_reply(event):
    """The reply that is about to end the turn, or '' when a Stop hook should stay out of it.

    A Stop hook that already blocked once in this turn (stop_hook_active) stays out, so a guard can
    never trap the model in a loop.
    """
    if not event or event.get("stop_hook_active"):
        return ""
    path = event.get("transcript_path") or ""
    if path and os.path.exists(path):
        return read_session(path)[0]
    return str(event.get("last_assistant_message") or "")


# ---------------------------------------------------------------------------------------------
# declarations: the named escape for the hooks that have one
#
# `npx guardhooks declare <hook-id> "<reason>"` appends a line to
# <config>/guardhooks/state/declared/<hook-id>.tsv. A declaration lasts two hours. Only hooks whose
# docs name this escape read it.
# ---------------------------------------------------------------------------------------------
DECLARE_MAX_AGE = 7200


def declared(hook_id, session_id=None, max_age=DECLARE_MAX_AGE):
    """The newest live declaration reason for this hook, or None."""
    path = os.path.join(config_dir(), "guardhooks", "state", "declared", hook_id + ".tsv")
    now = time.time()
    best = None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t", 2)
                if len(parts) != 3:
                    continue
                try:
                    when = float(parts[0])
                except ValueError:
                    continue
                if now - when > max_age:
                    continue
                if session_id and parts[1] not in (session_id, "any"):
                    continue
                best = parts[2]
    except OSError:
        pass
    return best


def write_declaration(hook_id, reason, session_id="any"):
    d = state_dir("declared")
    with open(os.path.join(d, hook_id + ".tsv"), "a", encoding="utf-8") as fh:
        fh.write("%f\t%s\t%s\n" % (time.time(), session_id, " ".join(str(reason).split())))
