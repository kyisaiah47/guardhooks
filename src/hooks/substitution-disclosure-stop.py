#!/usr/bin/env python3
"""Stop: block a reply that ends a turn in which a generator ran behind a prompt that named
existing inputs, unless the reply says plainly whether the named thing was used.

Three conditions must all hold before it blocks, so an ordinary generation turn never trips it:
  1. this turn's prompt named an existing artifact,
  2. a generator ran in this turn,
  3. the reply contains no sentence stating that what was used is not what was named.

A session is blocked at most MAX_BLOCKS times in total, and at most once per turn. The escape is
`npx guardhooks declare substitution-disclosure-stop "<reason>"`, which lasts two hours.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import substitution as L
except Exception:
    sys.exit(0)

HOOK_ID = "substitution-disclosure-stop"
MAX_BLOCKS = 3


def main():
    ev = G.read_event()
    if not ev or ev.get("stop_hook_active"):
        return
    tpath = ev.get("transcript_path") or ""
    if not tpath or not os.path.exists(tpath):
        return
    sid = str(ev.get("session_id") or "nosession")
    prompt, assistant, cmds = L.read_turn(tpath)
    if not assistant.strip():
        return
    named = L.names_existing_artifact(prompt)
    if not named:
        return
    gens = sorted({g for g in (L.is_generator(c) for c in cmds) if g})
    if not gens:
        return
    if L.discloses(assistant):
        return
    if G.declared(HOOK_ID):
        return

    counter = os.path.join(G.state_dir(HOOK_ID), "".join(c for c in sid if c.isalnum() or c in "-_") + ".blocks")
    try:
        with open(counter) as fh:
            n = int(fh.read().strip() or 0)
    except Exception:
        n = 0

    hid = L.conceals(assistant)
    detail = ("  the prompt named: %s\n"
              "  generators that ran: %s\n"
              "  disclosure in the reply: none\n" % (named, ", ".join(gens)))
    if hid:
        detail += "  wording that hides it: %s\n" % ", ".join(hid)

    if n >= MAX_BLOCKS:
        sys.stderr.write("substitution-disclosure-stop: letting the reply through after %d blocks. "
                         "The reply still does not say whether the named thing was used:\n%s" % (n, detail))
        return
    try:
        with open(counter, "w") as fh:
            fh.write(str(n + 1))
    except OSError:
        pass

    extra = ""
    if hid:
        extra = ("\nThe reply uses process words (%s). They describe a process applied to a subject,\n"
                 "so they tell the user the subject survived. A generator makes a new subject.\n" % ", ".join(hid))
    G.block(
        "A generator ran in a turn where the user named something that already exists.\n"
        "The reply does not say whether the named thing is what was used.\n\n"
        + detail + extra +
        "\nAnswer that before you reply. There are two honest endings:\n"
        "  A. You used what was named. Say so and name the files. One sentence is enough.\n"
        "  B. You did not use what was named. Say that in the first sentence, in plain words:\n"
        "     \"I did not use the two images you looked at; these are new ones.\" Then say why in one\n"
        "     line, and ask whether the user wants it done the way they asked.\n\n"
        "If the generator made something unrelated, and nothing the user named was replaced, record why:\n"
        "  npx guardhooks declare %s \"<what the generator made and why it replaced nothing>\"\n" % HOOK_ID
    )


if __name__ == "__main__":
    main()
