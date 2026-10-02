#!/usr/bin/env python3
"""PreToolUse: remind the model to batch independent tool calls after a long run of lone calls.

Every request re-sends the whole conversation, so a tool call alone in its own request costs the
full context no matter how small its result is. Two independent reads sent one after the other
cost twice what the same two cost in one message.

Calls that arrive in the same request reach this hook within milliseconds of each other. A gap
under BATCH_WINDOW seconds means the call was batched with a sibling, and the streak resets.
After STREAK_LIMIT lone calls in a row, the hook adds a reminder. It never denies a call.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

HOOK_ID = "batch-tools-guard"
STREAK_LIMIT = 12
BATCH_WINDOW = 0.45


def main():
    ev = G.read_event()
    if not ev:
        return
    sid = "".join(c for c in str(ev.get("session_id") or "unknown") if c.isalnum() or c in "-_") or "unknown"
    path = os.path.join(G.state_dir(HOOK_ID), sid + ".json")

    now = time.time()
    st = {"last": 0.0, "streak": 0, "nagged": 0}
    try:
        with open(path) as fh:
            st.update(json.load(fh))
    except Exception:
        pass

    if now - float(st.get("last") or 0) < BATCH_WINDOW:
        st["streak"] = 0
    else:
        st["streak"] = int(st.get("streak") or 0) + 1
    st["last"] = now

    fire = st["streak"] >= STREAK_LIMIT
    if fire:
        st["streak"] = 0
        st["nagged"] = int(st.get("nagged") or 0) + 1
    try:
        with open(path, "w") as fh:
            json.dump(st, fh)
    except Exception:
        pass

    if fire:
        G.context(
            "You have made %d tool calls in a row, each one alone in its own request.\n"
            "Every request re-sends the whole conversation, so each lone call costs the full context.\n"
            "For the rest of the session, put every independent tool call in the same message:\n"
            "several Bash calls, a Read with a Grep, several Reads.\n"
            "Only wait between calls when a call needs the output of the one before it.\n"
            "Chain related shell steps into one Bash call with && instead of taking a turn per step."
            % STREAK_LIMIT,
            event="PreToolUse")


if __name__ == "__main__":
    main()
