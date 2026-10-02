#!/usr/bin/env python3
"""Stop: block a reply that states the current time, or does deadline arithmetic, without a
fresh clock reading.

Two checks, both against the transcript's own timestamps:
  1. A time stated as now must be within TOLERANCE_MIN minutes of the real instant that sentence
     was written.
  2. Minutes-left or time-elapsed arithmetic needs a clock reading (date, Date.now(), and the
     like) in this turn, no older than STALE_READ_MIN minutes when the claim was written.

Quoted text is exempt: fenced code, inline code, blockquotes and double-quoted spans. A session is
blocked at most MAX_BLOCKS times in total, and at most once per turn. The escape is
`npx guardhooks declare no-invented-clock-stop "<reason>"`, which lasts two hours.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import clock as C
except Exception:
    sys.exit(0)

HOOK_ID = "no-invented-clock-stop"
MAX_BLOCKS = 3


def main():
    ev = G.read_event()
    if not ev or ev.get("stop_hook_active"):
        return
    tpath = ev.get("transcript_path") or ""
    if not tpath or not os.path.exists(tpath):
        return
    sid = str(ev.get("session_id") or "nosession")
    _start, blocks, cmds = C.read_turn(tpath)
    if not blocks:
        return

    wrong, unread = [], []
    for when, text in blocks:
        for phrase, h, mi, ap in C.now_claims(text):
            off = C.delta_minutes(h, mi, ap, when)
            if off > C.TOLERANCE_MIN:
                stated = "%d:%02d%s" % (h, mi, (" " + ap) if ap else "")
                wrong.append((phrase, stated, when.strftime("%H:%M"), off))
        claims = C.elapsed_claims(text)
        if claims:
            last = C.last_read_before(cmds, when)
            age = None if last is None else (when - last).total_seconds() / 60.0
            if age is None or age > C.STALE_READ_MIN:
                for phrase in claims:
                    unread.append((when, phrase, age))

    if not wrong and not unread:
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
    if wrong:
        detail += "Times stated as now that do not match the clock:\n"
        for phrase, stated, real, off in wrong[:8]:
            detail += '  "%s": you wrote %s, the real time was %s, off by %d minutes\n' % (
                phrase, stated, real, round(off))
    if unread:
        detail += "Deadline or elapsed-time arithmetic with no fresh clock reading:\n"
        for when, phrase, age in unread[:8]:
            stale = "no clock reading this turn" if age is None else "last reading %d minutes earlier" % round(age)
            detail += '  "%s" (%s, written at %s)\n' % (phrase, stale, when.strftime("%H:%M"))
    reads = [t for t, c in cmds if C.reads_clock(c)]
    detail += "Clock readings this turn: %s\n" % (
        ", ".join(t.strftime("%H:%M:%S") for t in reads) if reads else "none")
    detail += "Real time now: %s\n" % datetime.now().astimezone().strftime("%H:%M:%S")

    if n >= MAX_BLOCKS:
        sys.stderr.write("no-invented-clock-stop: letting the reply through after %d blocks. "
                         "These clock claims are still unverified:\n%s" % (n, detail))
        return
    try:
        with open(counter, "w") as fh:
            fh.write(str(n + 1))
    except OSError:
        pass

    G.block(
        "The reply states a time without reading the clock.\n"
        "The transcript records the real instant each sentence was written, and these do not match.\n\n"
        + detail +
        "\nTool calls are not a clock. A clock reading is stale as soon as it is taken.\n"
        "A time that makes the argument land does not feel like a guess, so it is the one to check.\n\n"
        "Fix it before you reply:\n"
        "  1. Run `date` now, in this turn.\n"
        "  2. Rewrite every clock time and every minutes-left figure from that output.\n"
        "  3. If you already told the user a deadline was missed or close and the clock says\n"
        "     otherwise, put the correction in the first sentence.\n\n"
        "If the flagged text quotes a time instead of claiming one, put it in backticks or a\n"
        "blockquote. If it claims nothing about the present, record why:\n"
        "  npx guardhooks declare %s \"<what these times refer to>\"\n" % HOOK_ID
    )


if __name__ == "__main__":
    main()
