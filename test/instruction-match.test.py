#!/usr/bin/env python3
"""Fixtures for instruction-match.py. It must fire when the planned verb contradicts the user's
verb on the same object, and stay silent on ordinary matching work. Both directions matter: a
guard that refuses correct work gets switched off."""
import json
import os
import shutil
import sys

sys.dont_write_bytecode = True
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src", "hooks", "lib"))
from _harness import T  # noqa: E402
import instruction_match as M  # noqa: E402

t = T("instruction-match")

ASKED = [
    "ok we probably want to create a pitch deck with all this info we found no?",
    "we have a pitch deck already for the investors so go with similar style. kick off agents for this",
]
BRIEF = {"description": "Update the investor pitch deck",
         "prompt": "UPDATE THE EXISTING PITCH DECK with the new evidence. Do not build a new deck. "
                   "The deck exists and its style is liked."}
GOOD_BRIEF = {"description": "Create a new evidence pitch deck",
              "prompt": "CREATE A NEW PITCH DECK. A NEW ONE. This is not an edit of anything that exists. "
                        "Read the old one only to learn the style."}

work = tempfile.mkdtemp(dir=HERE, prefix=".im-")
try:
    deck = os.path.join(work, "pitch", "deck.md")
    os.makedirs(os.path.dirname(deck))
    with open(deck, "w") as fh:
        fh.write("# the existing deck\n")

    # --- the library directly ---------------------------------------------------------------
    by, _ = M.instruction(ASKED)
    t.check("the request reads CREATE on 'deck'", by.get("deck", {}).get("cls") == "create", repr(by.get("deck")))
    t.check("fires: a brief that updates the deck the user asked to create",
            bool(M.divergence(by, M.planned("Agent", BRIEF), ASKED)))
    t.check("fires: editing the deck the user named as already existing",
            bool(M.divergence(by, M.planned("Edit", {"file_path": deck}), ASKED)))
    t.check("silent: a brief that creates a new deck", not M.divergence(by, M.planned("Agent", GOOD_BRIEF), ASKED))
    t.check("silent: writing the new deck beside the old one",
            not M.divergence(by, M.planned("Write", {"file_path": os.path.join(work, "pitch", "deck-evidence.md")}), ASKED))
    plain = ["update the deck with the new numbers"]
    t.check("silent: 'update the deck' then editing it",
            not M.divergence(M.instruction(plain)[0], M.planned("Edit", {"file_path": deck}), plain))
    typo = ["fix the typo in deck.md"]
    t.check("silent: 'fix the typo in deck.md' then editing it",
            not M.divergence(M.instruction(typo)[0], M.planned("Edit", {"file_path": deck}), typo))
    gen = ["create a different style banner", "like the other logo and text, figure it out"]
    t.check("silent: editing the generator that makes the new banner",
            not M.divergence(M.instruction(gen)[0],
                             M.planned("Edit", {"file_path": os.path.join(work, "art", "banners.mjs")}), gen))
    rev = ASKED + ["actually just update the existing one"]
    t.check("silent: a later reversal wins",
            not M.divergence(M.instruction(rev)[0], M.planned("Edit", {"file_path": deck}), rev))
    t.check("an agent brief pasted as a user message is not the user",
            not M.is_the_user("You are finishing the port. Build a new comparison page for the sample apps, and "
                              "read the full brief first before you touch anything at all in any of the repositories.", 0))

    # --- the hook, over stdin, with a real transcript -----------------------------------------
    def transcript(prompts):
        fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for p in prompts:
            fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": p}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "ok"}]}}) + "\n")
        fh.close()
        return fh.name

    sessions = iter(range(1000))

    def hook(label, prompts, tool, tool_input, want):
        path = transcript(prompts)
        try:
            return t.pre(label, tool, tool_input, want,
                         extra_event={"transcript_path": path, "session_id": "s%d" % next(sessions)})
        finally:
            os.unlink(path)

    reason = hook("hook denies the update brief", ASKED, "Agent", BRIEF, "deny")
    t.check("the denial shows both verbs and the object",
            "CREATE" in reason and "UPDATE" in reason and "deck" in reason, reason[:300])
    hook("hook denies an edit of the deck named as existing", ASKED, "Edit",
         {"file_path": deck, "old_string": "a", "new_string": "b"}, "deny")
    hook("hook allows the create brief", ASKED, "Agent", GOOD_BRIEF, "allow")
    hook("hook allows a matching edit", plain, "Edit", {"file_path": deck, "old_string": "a", "new_string": "b"}, "allow")
    hook("hook ignores Bash", ASKED, "Bash", {"command": "ls"}, "allow")
    t.pre("hook stays silent with no transcript", "Agent", BRIEF, "allow")

    # the latch: once per divergence per turn
    path = transcript(ASKED)
    try:
        ev = {"transcript_path": path, "session_id": "latched"}
        t.pre("first call in a turn is denied", "Agent", BRIEF, "deny", extra_event=ev)
        t.pre("the same call again in the same turn goes through", "Agent", BRIEF, "allow", extra_event=ev)
    finally:
        os.unlink(path)

    # the escape, and its refusal to launder the divergence
    os.environ["CLAUDE_CONFIG_DIR"] = t.config
    import guardhooks_core as G  # noqa: E402
    G.write_declaration("instruction-match", "update the existing pitch deck slides with the new evidence rows")
    hook("a declaration that still says UPDATE the deck is ignored", ASKED, "Agent", BRIEF, "deny")
    G.write_declaration("instruction-match", "create a new deck at deck-evidence.html, editing only the build script")
    hook("a declaration in the user's own terms lets it through", ASKED, "Agent", BRIEF, "allow")
finally:
    shutil.rmtree(work, ignore_errors=True)

t.done()
