#!/usr/bin/env python3
"""UserPromptSubmit: put the real wall clock next to every prompt, with a warning that it goes stale.

The model has no clock. Between two readings it tends to estimate the time from how much work it
has done, and that estimate is often wrong by a wide margin. This hook gives it the true time at
the moment of the prompt and tells it to read the clock again before stating a time later.
Pairs with no-invented-clock-stop, which checks the reply.
"""
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)


def main():
    G.read_event()
    now = datetime.now().astimezone()
    stamp = now.strftime("%A %Y-%m-%d %H:%M:%S %Z")
    G.context(
        "Wall clock, read at this prompt: %s (epoch %d).\n"
        "This reading is true only at the moment of this prompt. It is stale from here on.\n"
        "Tool calls are not a clock. Doing more work does not tell you how much time has passed.\n"
        "Before you state the current time, the time left before a deadline, the time elapsed, or\n"
        "whether something is still reachable today, run `date` again at that moment and use its output."
        % (stamp, int(time.time()))
    )


if __name__ == "__main__":
    main()
