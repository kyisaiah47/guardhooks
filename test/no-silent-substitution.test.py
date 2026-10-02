#!/usr/bin/env python3
"""Fixtures for no-silent-substitution.py. Each case runs the real hook with a real transcript."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-silent-substitution")

NAMED_PROMPT = "run bg-remove on 2 and 3 and render the video with those replacing"
PLAIN_PROMPT = "make me three new hero images for the landing page"
GEN = "node scripts/generate-hero.mjs --out /tmp/p/hero"
IMAGE_API = "curl -s https://api." + "openai.com/v1/images/generations -d @/tmp/p/body.json"


def transcript(prompt):
    fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
    fh.close()
    return fh.name


def case(label, prompt, command, want, session="s1", ctx_has=None):
    path = transcript(prompt)
    try:
        p, decision, reason, ctx = t.pre_result("no-silent-substitution.py", "Bash", {"command": command},
                                                extra_event={"transcript_path": path, "session_id": session})
    finally:
        os.unlink(path)
    ok = decision == want and p.returncode == 0
    if ok and ctx_has:
        ok = ctx_has in ctx
    t.check(label, ok, "want %s got %s ctx=%r err=%s" % (want, decision, ctx[:120], p.stderr[:200]))
    return reason


reason = case("a generator behind a prompt that named inputs is denied", NAMED_PROMPT, GEN, "deny", "a")
t.check("the denial names what the prompt named", "2 and 3" in reason or "with those" in reason, reason[:300])
case("the same generator again in the same turn goes through", NAMED_PROMPT, GEN, "allow", "a")
case("a new session with the same prompt is denied once again", NAMED_PROMPT, GEN, "deny", "b")
case("an image API call behind named inputs is denied", NAMED_PROMPT, IMAGE_API, "deny", "c")

case("a generator with no named inputs only gets a reminder", PLAIN_PROMPT, GEN, "allow", "d",
     ctx_has="makes a new subject")
case("a transform behind named inputs is allowed", NAMED_PROMPT,
     "python3 tools/bg_remove.py in/2.png in/3.png --out out/", "allow", "e")
case("an ordinary command is allowed", NAMED_PROMPT, "ls -la ./renders", "allow", "f")
case("a generator name inside a heredoc body is not a call", NAMED_PROMPT,
     "cat > notes.md <<'EOF'\nnode scripts/generate-hero.mjs was the old way\nEOF", "allow", "g")

t.pre("a non-Bash tool is ignored", "Write", {"file_path": "/tmp/p/a.md", "content": GEN}, "allow")

# a user's own generator entry point from the config dir
os.makedirs(os.path.join(t.config, "guardhooks"), exist_ok=True)
with open(os.path.join(t.config, "guardhooks", "generator-commands.txt"), "w") as fh:
    fh.write("\\bmake-art\\b\n")
case("a user generator pattern from the config dir is honoured", NAMED_PROMPT, "make-art --seed 4", "deny", "h")

t.done()
