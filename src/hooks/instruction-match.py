#!/usr/bin/env python3
"""PreToolUse (Agent, Task, Write, Edit, MultiEdit, NotebookEdit): deny an action whose verb
contradicts what the user asked for, on the same object.

If the user said "create a new deck" and an agent brief says "update the existing deck", or a
file edit changes the deck the user named as the model to copy, the hook puts the two side by
side and denies the call once. No shared object means no verdict, so ordinary work is untouched.

The escape is `npx guardhooks declare instruction-match "<verb> <object>, and why that is what
was asked>"`. It lasts two hours. A declaration whose own verb still contradicts the user's on
the same object is ignored, so it cannot be used to reword the divergence.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import instruction_match as M
except Exception:
    sys.exit(0)

HOOK_ID = "instruction-match"


def main():
    ev = G.read_event()
    if not ev:
        return
    tool = ev.get("tool_name") or ""
    if tool not in M.SIDE_EFFECTING:
        return
    tpath = ev.get("transcript_path") or ""
    if not tpath or not os.path.exists(tpath):
        return
    prompts = M.user_window(tpath, 3)
    byword, _order = M.instruction(prompts)
    if not byword:
        return
    plan = M.planned(tool, ev.get("tool_input") or {})
    d = M.divergence(byword, plan, prompts)
    if not d:
        return

    decl = G.declared(HOOK_ID)
    if decl and not M.declaration_contradicts(decl, d):
        return

    sid = str(ev.get("session_id") or "nosession")
    key = hashlib.sha1("|".join([sid, prompts[-1] if prompts else "", d["noun"], d["plan"]["cls"]])
                       .encode("utf-8", "replace")).hexdigest()[:16]
    latch = os.path.join(G.state_dir(HOOK_ID), "fired-" + key)
    if os.path.exists(latch):
        return
    try:
        with open(latch, "w") as fh:
            fh.write(d["plan"]["where"][:300])
    except OSError:
        pass

    theirs = d["theirs"]
    extra = ""
    if d.get("exists"):
        extra = ("\nThe user also said this one already exists (\"%s\"). That makes it the model to copy,\n"
                 "not the thing to change. The new one goes beside it, under a new name.\n" % d["exists"])
    G.deny(
        "This action does not match what the user asked for.\n\n"
        "  the user said: %s %s\n"
        "  planned:       %s %s\n"
        "  shared object: %s\n"
        "  seen in:       %s\n"
        "%s"
        "\n%s is not %s. Do the verb the user used, on the object the user named.\n\n"
        "The target is what changes. The user names it with the verb.\n"
        "The model is what the result should resemble. Naming it is not permission to edit it.\n"
        "\"make A match B\" means B is the reference and A changes.\n"
        "\"do it like X\" describes the output. It is not a request to edit X.\n\n"
        "If you cannot tell which the user meant, ask in one line before doing anything.\n"
        "If the planned action really is what was asked, record it in those terms:\n"
        "  npx guardhooks declare %s \"<verb> <object>, and why that is what was asked>\"\n"
        "A declaration whose verb still contradicts the user's is ignored."
        % (theirs["verb"].upper(), theirs["object"] or d["noun"],
           d["plan"]["verb"].upper(), (d["plan"]["object"] or "")[:90],
           d["noun"], d["plan"]["where"], extra,
           d["plan"]["cls"].upper(), theirs["cls"].upper(), HOOK_ID)
    )


if __name__ == "__main__":
    main()
