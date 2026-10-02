#!/usr/bin/env python3
"""PreToolUse: deny a Write, Edit, MultiEdit, NotebookEdit or Bash call whose new text has an em dash.

Bash is matched because a heredoc writes a file without touching Write. Only new text is scanned.
In a Bash command, a pipeline segment that searches for the character (grep, rg, ack, ag) or
removes it (tr -d, sed s///, perl s///, .replace) may name it, because those are the tools that fix
the problem.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import em_dash as D
except Exception:
    sys.exit(0)

PROSE_EXT = (".md", ".mdx", ".markdown", ".txt", ".rst", ".text")
# The ban's own files are about the ban.
SELF = ("/lib/em_dash", "no-em-dash")

SPLIT = re.compile(r"\|\||&&|[|;\n]")
DETECTOR = re.compile(
    r"^\s*(?:sudo\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:git\s+)?"
    r"(?:grep|egrep|fgrep|rg|ripgrep|ack|ag|ugrep|rga|look|comm|diff|awk|perl\s+-ne)\b")
DASHES = "[" + D.EM + D.EN + D.BAR + D.MINUS + "]"
SCRUBBER = re.compile(
    r"\btr\s+(?:-d|-s|-c)?\s*['\"]?" + DASHES +
    r"|\bs/" + DASHES +
    r"|\bs\[" + DASHES +
    r"|\.replace\(\s*(?:/)?['\"/\[]*" + DASHES)


def bash_hits(command):
    """Heredoc bodies are content and get no carve. The command line itself is exempt in any
    segment that finds or deletes the character."""
    hits = []
    remainder = command
    for body in G.heredoc_bodies(command):
        hits += D.scan(body, prose=False, allow_double_hyphen=True)
        remainder = remainder.replace(body, " ")
    for seg in SPLIT.split(remainder):
        if not seg.strip() or DETECTOR.search(seg) or SCRUBBER.search(seg):
            continue
        hits += D.scan(seg, prose=False, allow_double_hyphen=True)
    return hits


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    ti = ev.get("tool_input") or {}
    if tool == "Bash":
        command = str(ti.get("command") or "")
        if any(k in command for k in SELF):
            return
        hits = bash_hits(command)
        where = "this Bash command"
    elif tool in G.WRITE_TOOLS:
        path = G.target_path(ti)
        if any(k in path for k in SELF):
            return
        is_prose = path.lower().endswith(PROSE_EXT)
        hits = D.scan(G.new_text(ti), prose=True, allow_double_hyphen=not is_prose)
        where = os.path.basename(path) or "this write"
    else:
        return
    if not hits:
        return
    seen, lines = set(), []
    for label, ctx in hits:
        if (label, ctx) in seen:
            continue
        seen.add((label, ctx))
        lines.append("  - %s in: ...%s..." % (label, ctx))
        if len(lines) >= 6:
            break
    G.deny(D.BLOCK_TEXT + "\nFound in %s:\n%s\n" % (where, "\n".join(lines)))


if __name__ == "__main__":
    main()
