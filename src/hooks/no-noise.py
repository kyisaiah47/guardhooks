#!/usr/bin/env python3
"""PreToolUse: deny a Write, Edit, MultiEdit, NotebookEdit or Bash call that puts noise into product
copy or into a prompt or answer template.

Scope by path:
  A copy path (landing, copy, social, marketing, brand, email, press, listing, newsletter, content,
  a Next.js app/page.tsx, copy.json, a hero or tagline file, any .md or .mdx file) is scanned for
  families 4 and 5: filler in copy and copy that argues against the product.
  A prompt or answer path (prompt, template, answer, reply, cover letter, outreach, profile.json)
  is scanned for families 1 to 3: performed sincerity, euphemism for no, narrating the answer.
  A Bash command whose redirect or tee lands in such a path is scanned the same way. A headless
  model call with a print flag (see HEADLESS below) is a prompt and gets families 1 to 3.

Only new text is scanned. The quoting carve applies: fenced code, inline backtick spans, '>'
blockquotes, URLs, paths and long double-quoted spans are stripped first. In a code file, comments
are stripped too, so a comment about a sturdy retry is not read as copy. String literals are
scanned, because in these folders they are the copy. Data files (JSON, YAML, CSV) are scanned raw,
because their values are the copy.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import noise as N
except Exception:
    sys.exit(0)

# The ban's own files, tests and rule files name the phrases on purpose.
SELF = ("noise_patterns", "/lib/noise.", "no-noise", "/hooks/lib/", "/tests/", "/test/", ".test.",
        "CLAUDE.md", "AGENTS.md")

COPY_PATH = re.compile(
    r"/(?:social|landings?|copy|captions?|cards?|emails?|marketing|brand|listings?|press"
    r"|newsletters?|seo|content|blog|posts?|messages?)/"
    r"|(?:^|/)(?:src/)?app/(?:\([^/]*\)/)?page\.(?:tsx|jsx)$|(?:^|/)(?:src/)?app/[^/]+/page\.(?:tsx|jsx)$"
    r"|copy\.json$|hero|tagline|caption|-copy\.|copy-"
    r"|\.mdx?$", re.I)
PROMPT_PATH = re.compile(
    r"prompt|template|answer|cover-?letter|ground-truth|profile\.json|/outreach/|/recruit/"
    r"|reply|replies|/press/|/mail/", re.I)
CODE_EXT = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".sh", ".rb", ".go", ".rs")
DATA_EXT = (".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv")
MD_EXT = (".md", ".mdx", ".markdown", ".txt")

REDIRECT = re.compile(r"(?:>>?|\btee\s+(?:-a\s+)?)\s*[\"']?([^\s\"';|&]+)")
QUOTED_STR = re.compile(r"\"((?:[^\"\\]|\\.){20,}?)\"|'([^']{20,})'", re.S)
# A headless model CLI run with a print flag, or an exec subcommand.
HEADLESS = re.compile(r"\b(?:claude|gemini)\b[^\n|;&]*\s-p\b|\bcodex\s+exec\b")


def strip_code_comments(text):
    t = re.sub(r"/\*[\s\S]*?\*/", " ", text)
    t = re.sub(r"(?m)^\s*(?://|#)(?!!).*$", " ", t)
    t = re.sub(r"(?m)(?<=[;)\]}\s])\s//[^\n\"']*$", " ", t)
    return t


def scopes_for(path):
    """Which scopes apply to a write at this path. Both can apply."""
    scopes = []
    if COPY_PATH.search(path):
        scopes.append("copy")
    if PROMPT_PATH.search(path):
        scopes.append("answer")
    return scopes


def scan(text, scopes, path):
    low = path.lower()
    # A data file is all quoted strings, so the carve would strip everything. Its values are the copy.
    body = text if low.endswith(DATA_EXT) else N.prose_of(text)
    if low.endswith(CODE_EXT):
        body = strip_code_comments(body)
    # In a prose file, a single banned word in double quotes is a quotation too.
    if low.endswith(MD_EXT):
        body = re.sub("[\u201c\"][^\u201c\u201d\"\n]{3,}[\u201d\"]", " ", body)
    hits = []
    for sc in scopes:
        hits += N.noise_issues(body, sc)
    return hits


def bash_hits(command):
    targets = [m.group(1) for m in REDIRECT.finditer(command)]
    scopes = []
    for t in targets:
        for sc in scopes_for(t):
            if sc not in scopes:
                scopes.append(sc)
    if HEADLESS.search(command) and "answer" not in scopes:
        scopes.append("answer")
    if not scopes:
        return [], ""
    bodies = G.heredoc_bodies(command)
    remainder = G.HEREDOC.sub(" ", command)
    bodies += [g for m in QUOTED_STR.finditer(remainder) for g in m.groups() if g]
    hits = []
    for b in bodies:
        for sc in scopes:
            # A prompt names banned phrases in double quotes, so the carve applies to it. A JSON or
            # HTML body piped into a copy file is double-quoted copy, so it is scanned raw.
            hits += N.noise_issues(N.QUOTED.sub(" ", b) if sc == "answer" else b, sc)
    where = ", ".join(t for t in targets if scopes_for(t)) or "a headless model prompt"
    return hits, where


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
        hits, where = bash_hits(command)
        where = "this Bash command writing to %s" % where
    elif tool in G.WRITE_TOOLS:
        path = G.target_path(ti)
        if not path or any(k in path for k in SELF):
            return
        scopes = scopes_for(path)
        if not scopes:
            return
        hits = scan(G.new_text(ti), scopes, path)
        where = "%s (scope: %s)" % (os.path.basename(path) or "this write", "+".join(scopes))
    else:
        return
    if not hits:
        return
    seen, lines = set(), []
    for h in hits:
        key = (h["slug"], h["fragment"])
        if key in seen:
            continue
        seen.add(key)
        lines.append("  - %s (family %s) found: ...%s..." % (h["slug"], h["family"], h["sentence"][:160]))
        lines.append("    fix: %s" % h["fix"])
        if len(lines) >= 12:
            break
    G.deny(N.BLOCK_TEXT + "\n\nFound in %s:\n%s\n" % (where, "\n".join(lines)))


if __name__ == "__main__":
    main()
