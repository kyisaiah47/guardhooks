"""Shared matchers for the three substitution hooks.

  named-artifact-guard.py          UserPromptSubmit   adds the rule when a prompt names inputs
  no-silent-substitution.py        PreToolUse (Bash)  stops the first generator call that turn
  substitution-disclosure-stop.py  Stop               blocks a reply that hides the swap

Three questions, one answer each:
  names_existing_artifact(prompt)  Did the prompt point at something that already exists?
  is_generator(command)            Does this command make a new subject from a prompt?
  discloses(reply)                 Does the reply say plainly that the named thing was not used?

The pattern lists live in named_artifact_patterns.json and generator_commands.json beside this
file. A user can add lines in <config>/guardhooks/named-artifact-patterns.txt and
<config>/guardhooks/generator-commands.txt, one regex per line.
"""
import json
import os
import re

import guardhooks_core as G


def _compile(lines):
    out = []
    for line in lines:
        line = (line or "").strip()
        if not line or line.startswith("#"):
            continue
        try:
            out.append(re.compile(line, re.I))
        except re.error:
            continue
    return out


def _load(json_name, user_txt):
    lines = []
    try:
        lines += G.load_json(json_name).get("patterns", [])
    except Exception:
        pass
    try:
        with open(os.path.join(G.config_dir(), "guardhooks", user_txt), encoding="utf-8") as fh:
            lines += fh.read().splitlines()
    except OSError:
        pass
    return _compile(lines)


NAMED_ARTIFACT = _load("named_artifact_patterns.json", "named-artifact-patterns.txt")
GENERATOR = _load("generator_commands.json", "generator-commands.txt")


def names_existing_artifact(prompt):
    """The phrase that shows the prompt named something that already exists, or ''."""
    if not prompt:
        return ""
    for rx in NAMED_ARTIFACT:
        m = rx.search(prompt)
        if m:
            return m.group(0).strip()
    return ""


# A generator's name in a heredoc body is documentation or a fixture, not a call. A command that
# runs a hook script never authors artwork either.
_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1\b", re.S)
_HOOK_RUN = re.compile(r"\.claude[\w.-]*/hooks/|/hooks/guardhooks/", re.I)


def is_generator(cmd):
    """The matched fragment when this shell command makes a new subject from a prompt, or ''."""
    if not cmd or _HOOK_RUN.search(cmd):
        return ""
    stripped = _HEREDOC.sub(" ", cmd)
    for rx in GENERATOR:
        m = rx.search(stripped)
        if m:
            return m.group(0).strip()
    return ""


# A disclosure must state that the thing used is NOT the thing named. A sentence about a process
# ("regenerated at native size") describes a mechanism and reads as a format conversion, so none
# of these phrases can be satisfied by describing a pipeline step.
DISCLOSURE = [re.compile(p, re.I) for p in (
    r"\bdid\s*n[o']?t\s+use\b",
    r"\bhave\s*n[o']?t\s+used\b",
    r"\bnot\s+the\s+(?:one|ones|image|images|file|files|asset|assets|version|versions|render|renders|object|objects)\b[^.]{0,60}\b(?:you|i\s+showed|shown|saw|picked|chose|approved)\b",
    r"\bthese\s+are\s+not\s+the\b",
    r"\bthis\s+is\s+not\s+the\b",
    r"\bnot\s+the\s+same\s+(?:image|images|file|files|asset|assets|artwork|object|objects|render)\b",
    r"\bdifferent\s+(?:image|images|file|files|asset|assets|artwork|object|objects)\b[^.]{0,60}\bthan\s+(?:the\s+)?(?:one|ones|what)\b",
    r"\bnew\s+(?:artwork|art|image|images|object|objects|render|renders|photograph|photographs)\b",
    r"\bbrand[- ]new\b",
    r"\bsubstitut(?:ed|ion|ing)\b",
    r"\bswapped\s+(?:in|out)\s+(?:a|an|two|three|different|new)\b",
    r"\bI\s+(?:made|generated|created|authored)\s+(?:a\s+|two\s+|three\s+|)new\b",
    r"\bnever\s+(?:used|touched)\s+the\s+(?:one|ones|file|files|image|images)\s+you\b",
)]

# True sentences about a mechanism that read as a reformat of the named thing.
CONCEALING = [re.compile(p, re.I) for p in (
    r"\bre-?generat(?:ed|ion|ions|ing)\b",
    r"\bre-?ran\b",
    r"\bre-?run\b",
    r"\bre-?format(?:ted|ting)?\b",
    r"\bre-?built\b",
    r"\bre-?fresh(?:ed)?\b",
    r"\bre-?process(?:ed)?\b",
    r"\bre-?render(?:ed)?\b",
    r"\bre-?shot\b",
    r"\bre-?made\b",
    r"\bat\s+(?:exactly\s+)?(?:its\s+|the\s+)?native\s+(?:size|resolution|aspect)\b",
    r"\bno\s+cropping\b",
    r"\bran\s+the\s+pipeline\s+again\b",
)]


def discloses(text):
    return bool(text) and any(rx.search(text) for rx in DISCLOSURE)


def conceals(text):
    if not text:
        return []
    return sorted({rx.search(text).group(0).lower() for rx in CONCEALING if rx.search(text)})


def _text_of(msg):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") in (None, "text"))
    return ""


def read_turn(transcript_path):
    """(last real user prompt, last assistant text, [shell commands and skill calls this turn])."""
    prompt, assistant, cmds = "", "", []
    if not transcript_path:
        return prompt, assistant, cmds
    for d in G.iter_transcript(transcript_path):
        m = d.get("message") or {}
        role = m.get("role")
        content = m.get("content")
        if role == "user":
            t = _text_of(m)
            if t.strip() and "tool_use_id" not in json.dumps(content)[:400]:
                prompt, assistant, cmds = t, "", []
        elif role == "assistant":
            t = _text_of(m)
            if t.strip():
                assistant = t
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        inp = b.get("input") or {}
                        c = inp.get("command")
                        if isinstance(c, str):
                            cmds.append(c)
                        s = inp.get("skill")
                        if isinstance(s, str):
                            cmds.append("/" + s)
    return prompt, assistant, cmds
