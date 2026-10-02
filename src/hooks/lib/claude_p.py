"""Reader for claude_p_patterns.json. Used by no-claude-p.py and no-claude-p-stop.py.

The rule: every headless model call goes through the CLI the user chose. A headless Claude CLI
call (print mode, the model flag, a spawn of the claude binary) is refused, and the message names
the chosen CLI. The chosen CLI comes from the GUARDHOOKS_HEADLESS_CLI environment variable, read at
run time. An interactive Claude Code session is not a headless call and is never affected.

The quoting carve: a fenced block, an inline backtick span, a '>' blockquote or a double-quoted span
of twelve characters or more is stripped before a prose write or a reply is scanned.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "claude_p_patterns.json")

with open(SPEC_PATH, "r", encoding="utf-8") as _fh:
    SPEC = json.load(_fh)

SELF_PATHS = tuple(SPEC["self_paths"])
INVOCATION = [dict(p, re=re.compile(p["re"], re.I)) for p in SPEC["invocation"]]
MENTION = re.compile(SPEC["reply"]["mention"], re.I)
NEGATION = re.compile(SPEC["reply"]["negation"], re.I)

ENV_VAR = "GUARDHOOKS_HEADLESS_CLI"
DEFAULT_CLI = "the headless CLI this project uses"

FENCE = re.compile(r"```.*?```", re.S)
FENCE_OPEN = re.compile(r"```.*\Z", re.S)
INLINE = re.compile(r"`[^`\n]*`")
BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)
QUOTED = re.compile("[“\"][^“”\"\n]{12,}[”\"]")
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def chosen_cli():
    """The headless CLI the user chose, or None when GUARDHOOKS_HEADLESS_CLI is unset."""
    v = (os.environ.get(ENV_VAR) or "").strip()
    return v or None


def is_self(text):
    """The ban's own files, and the rules files that state it."""
    return any(k in (text or "") for k in SELF_PATHS)


def prose_of(text):
    """Strip quoted material so only the writer's own sentences remain."""
    t = FENCE.sub(" ", text or "")
    t = FENCE_OPEN.sub(" ", t)
    t = INLINE.sub(" ", t)
    t = BLOCKQUOTE.sub(" ", t)
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


def findings(text):
    """Every headless Claude CLI call written into a file or run from a shell:
    [{slug, fix, fragment, sentence}]. One hit per pattern."""
    t = str(text or "")
    out = []
    for p in INVOCATION:
        m = p["re"].search(t)
        if not m:
            continue
        out.append({"slug": p["slug"], "fix": p["fix"],
                    "fragment": m.group(0).strip(), "sentence": _sentence_around(t, m.start())})
    return out


def reply_hits(reply):
    """Sentences in a reply that plan a headless Claude CLI call. A sentence that also carries a
    negation (not, never, instead, replaced, error and similar) is about the ban and passes. A
    sentence that names the chosen CLI passes too."""
    t = prose_of(reply)
    cli = chosen_cli()
    cli_re = re.compile(r"(?<![\w-])" + re.escape(cli) + r"(?![\w-])", re.I) if cli else None
    out = []
    for m in MENTION.finditer(t):
        sentence = _sentence_around(t, m.start())
        if NEGATION.search(sentence):
            continue
        if cli_re and cli_re.search(sentence):
            continue
        out.append({"fragment": m.group(0).strip(), "sentence": sentence})
    return out


def block_text():
    cli = chosen_cli()
    name = cli or DEFAULT_CLI
    lines = [
        "Headless model calls go through %s." % name,
        "",
        "This project routes every scripted, non-interactive model call through one CLI.",
        "A headless Claude CLI call (claude -p, claude --print, claude --model, or a spawn of the",
        "claude binary) bypasses that choice.",
        "Write the call with %s instead." % name,
        "",
        "An interactive Claude Code session is not a headless call and is not affected.",
        "To quote the command on purpose, for example in a rule or a log line, put it in a fenced",
        "code block, an inline backtick span, a '>' blockquote or a double-quoted span.",
    ]
    if not cli:
        lines += ["", "Set %s to name the CLI this project uses." % ENV_VAR]
    return "\n".join(lines)
