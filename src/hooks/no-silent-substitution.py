#!/usr/bin/env python3
"""PreToolUse (Bash): deny the first generator call of a turn whose prompt named existing inputs.

A generator makes a new subject from a prompt. When the user named specific existing files and
the session runs a generator instead of using them, the result is new artwork presented as the
old. The hook denies the first such call in a turn and explains what to do. A repeated call in
the same turn goes through, and substitution-disclosure-stop then requires the reply to say so.

When no inputs were named, a generator call gets a short reminder and is never denied.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import substitution as L
except Exception:
    sys.exit(0)

HOOK_ID = "no-silent-substitution"


def main():
    ev = G.read_event()
    if not ev or ev.get("tool_name") != "Bash":
        return
    cmd = str((ev.get("tool_input") or {}).get("command") or "")
    gen = L.is_generator(cmd)
    if not gen:
        return
    sid = str(ev.get("session_id") or "nosession")
    prompt, _assistant, _cmds = L.read_turn(ev.get("transcript_path") or "")
    named = L.names_existing_artifact(prompt)

    if not named:
        G.context(
            "Substitution check: this command (%s) makes a new subject from a prompt. It does not\n"
            "transform an existing one. If anything the user already saw or approved will not be what\n"
            "ends up used, say so in the first sentence of the reply, in plain words. Do not call it\n"
            "regenerated, re-ran, reformatted or \"at native size\"." % gen,
            event="PreToolUse")

    turn = hashlib.sha1((sid + "|" + prompt).encode("utf-8", "replace")).hexdigest()[:16]
    latch = os.path.join(G.state_dir(HOOK_ID), "fired-" + turn)
    if os.path.exists(latch):
        return
    try:
        with open(latch, "w") as fh:
            fh.write(cmd[:400])
    except OSError:
        pass

    G.deny(
        "This command makes a new subject, and the prompt named something that already exists.\n\n"
        "  the prompt named: %s\n"
        "  this command runs: %s\n\n"
        "Running it makes new output. It does not reformat, resize, convert or refresh the named thing.\n\n"
        "Do this instead, in this order:\n"
        "  1. Use the inputs the user named. Deliver the request with them, even if the result is imperfect.\n"
        "  2. If the request cannot be done with those inputs, say so first in one plain sentence and ask.\n"
        "     Deliver first, then offer the alternative as a question.\n"
        "  3. If the user already asked for new output, or this generator makes something unrelated to\n"
        "     what was named, run it again. The first sentence of the reply must then say plainly that\n"
        "     what the user saw is not what was used.\n\n"
        "These are not reasons to substitute: it would look better, the format is wrong, the named\n"
        "operation cannot do it, it is fewer steps.\n\n"
        "This is the only denial this turn. Running the command again will go through."
        % (named, gen)
    )


if __name__ == "__main__":
    main()
