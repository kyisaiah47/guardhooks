#!/usr/bin/env python3
"""Stop: block a reply that states a visual or external outcome this session never observed.

"The card renders correctly", "it is live on production" and "the agent confirmed it works" are
outcomes on someone else's screen or server. Checking an input (a redirect, a config value, a
deploy that exited 0) does not observe them. The reply passes when this turn read back a real
capture of the thing, or probed the system it names, or wrote the sentence as a prediction.

Each distinct claim is blocked at most three times, and the hook blocks at most twelve times per
session, so it can never trap a session. Any error inside the hook lets the reply through.

Escape: `npx guardhooks declare no-unobserved-outcome-stop "<what you captured and where>"`
lasts two hours.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import outcome as O
except Exception:
    sys.exit(0)

HOOK_ID = "no-unobserved-outcome-stop"
MAX_BLOCKS_PER_CLAIM = 3
CEILING = 12


def _read_int(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return int(fh.read().strip() or 0)
    except Exception:
        return 0


def message(flagged, ev):
    lines = ["The reply states an outcome this session never observed. Every fact behind it can be",
             "true while the outcome is false.", "", "Outcomes stated as fact:"]
    for s, tier, relayed in flagged[:O.MAX_FLAG]:
        tag = tier.upper() + (", relayed from an agent" if relayed else "")
        lines.append("  [%s] %s" % (tag, s[:220]))
    lines.append("")
    lines.append("This turn: images read back = %d, images pasted by the user = %d, external probe = %s."
                 % (ev.get("images", 0), ev.get("pasted", 0), "yes" if ev.get("probe") else "no"))
    if O.composed_only(ev):
        lines.append("Every image read back this turn was composed by this session with an image library.")
        lines.append("A picture you made can only agree with you. It is not a capture of the thing.")
    lines.append("")
    if any(r for _s, _t, r in flagged):
        lines += ["A subagent's report is not an observation. Its screenshots are not in your context.",
                  "Open the artifact yourself, or say it is a report you have not checked.", ""]
    if any(t == "visual" for _s, t, _r in flagged):
        lines += ["For a visual claim:",
                  "  1. Capture the subject itself: the live page, the real composer, the actual render.",
                  "     A drawing, a crop of a source asset or a mock of a third-party UI is not a capture.",
                  "  2. Read the screenshot back as an image in this turn.",
                  "  3. Then describe what you saw.", ""]
    if any(t == "external" for _s, t, _r in flagged):
        lines += ["For an external claim, ask that system in this turn: fetch the live URL, call the real",
                  "API, or drive the browser. A config file, a redirect or a deploy exit code is not its answer.", ""]
    lines += ["Or write it as a prediction and say so: \"it should render correctly now; I have not",
              "checked it\". The hook does not stop reasoning about mechanisms. It stops a mechanism",
              "being reported as an observation.", "",
              "If you did observe it and the hook cannot see how, record it for two hours with:",
              "    npx guardhooks declare no-unobserved-outcome-stop \"<what you captured and where>\""]
    return "\n".join(lines)


def main():
    ev_in = G.read_event()
    if not ev_in or ev_in.get("stop_hook_active"):
        return
    path = ev_in.get("transcript_path") or ""
    if not path or not os.path.exists(path):
        return
    sid = str(ev_in.get("session_id") or "nosession")
    ev = O.read_turn(path)
    if not ev["reply"].strip():
        return
    flagged = [(s, tier, relayed) for s, tier, relayed in O.flag(ev["reply"])
               if not O.satisfied(tier, ev, s)]
    if not flagged:
        return
    if G.declared(HOOK_ID):
        return
    key = hashlib.sha1("\n".join(sorted(s for s, _t, _r in flagged)).encode("utf-8", "replace")).hexdigest()[:12]
    safe_sid = "".join(ch for ch in sid if ch.isalnum() or ch in "-_")[:64] or "nosession"
    state = G.state_dir("outcome")
    cfile = os.path.join(state, "%s.%s.blocks" % (safe_sid, key))
    tfile = os.path.join(state, "%s.blocks" % safe_sid)
    n, total = _read_int(cfile), _read_int(tfile)
    if total >= CEILING or n >= MAX_BLOCKS_PER_CLAIM:
        return
    with open(cfile, "w", encoding="utf-8") as fh:
        fh.write(str(n + 1))
    with open(tfile, "w", encoding="utf-8") as fh:
        fh.write(str(total + 1))
    G.block(message(flagged, ev))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
