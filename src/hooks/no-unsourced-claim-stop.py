#!/usr/bin/env python3
"""Stop: block a reply that quotes something the session never saw or names a path that does
not exist.

The transcript and the filesystem are the evidence, so the check never has to trust the model.
A reply is never evidence for itself: this turn's own text is left out of the pool.

A session is blocked at most MAX_BLOCKS times in total, and at most once per turn. The escape is
`npx guardhooks declare no-unsourced-claim-stop "<reason>"`, which lasts two hours.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import sourced as S
except Exception:
    sys.exit(0)

HOOK_ID = "no-unsourced-claim-stop"
MAX_BLOCKS = 3


def main():
    ev = G.read_event()
    if not ev or ev.get("stop_hook_active"):
        return
    tpath = ev.get("transcript_path") or ""
    if not tpath or not os.path.exists(tpath):
        return
    sid = str(ev.get("session_id") or "nosession")
    reply, pool, raw, has_image, _prompt = G.read_session(tpath)
    if not reply.strip():
        return

    bad_quotes = []
    for q, ctx in S.quoted_claims(reply) + S.numeric_quotes(reply):
        if S.supported(q, pool, raw):
            continue
        if has_image and S.IMAGE_SOURCE.search(ctx):
            continue
        if q not in bad_quotes:
            bad_quotes.append(q)
    bad_paths = [p for p in S.path_claims(reply) if not S.resolves(p) and p not in raw]
    if not bad_quotes and not bad_paths:
        return
    if G.declared(HOOK_ID):
        return

    counter = os.path.join(G.state_dir(HOOK_ID), "".join(c for c in sid if c.isalnum() or c in "-_") + ".blocks")
    try:
        with open(counter) as fh:
            n = int(fh.read().strip() or 0)
    except Exception:
        n = 0

    detail = ""
    if bad_quotes:
        detail += "Quotes that appear nowhere in this session:\n"
        for q in bad_quotes[:S.MAX_FLAG]:
            detail += '  "%s"\n' % (q[:150] + ("..." if len(q) > 150 else ""))
    if bad_paths:
        detail += "Paths that do not exist and came from no tool result:\n"
        for p in bad_paths[:S.MAX_FLAG]:
            detail += "  %s\n" % p

    if n >= MAX_BLOCKS:
        sys.stderr.write("no-unsourced-claim-stop: letting the reply through after %d blocks. "
                         "These are still unverified:\n%s" % (n, detail))
        return
    try:
        with open(counter, "w") as fh:
            fh.write(str(n + 1))
    except OSError:
        pass

    G.block(
        "The reply quotes something or names a file that this session has never seen.\n\n"
        + detail +
        "\nA quote of what was said must come from the transcript. A path must exist.\n"
        "A detail that makes the argument stronger does not feel like a guess, so it is the one to check.\n"
        "A correction is checked like any other reply.\n\n"
        "Fix it before you reply:\n"
        "  1. Search the transcript for each flagged quote. Use what it says, or delete the quote.\n"
        "  2. List each flagged path. Use the real one, or say you have not found it.\n"
        "  3. If a quote came from an image, say so in the sentence (\"the screenshot shows ...\").\n"
        "  4. If you already stated a wrong detail, put the correction in the first sentence.\n\n"
        "If a flagged item has a real source outside the transcript, record it:\n"
        "  npx guardhooks declare %s \"<the quote or path, and where you read it>\"\n" % HOOK_ID
    )


if __name__ == "__main__":
    main()
