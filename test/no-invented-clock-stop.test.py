#!/usr/bin/env python3
"""Fixtures for no-invented-clock-stop.py. Each case builds a transcript whose frames carry real
timestamps, made at runtime, and runs the real hook against it."""
import json
import os
import sys

sys.dont_write_bytecode = True
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-invented-clock-stop")
sessions = iter(range(1000))


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def run(reply, written_at, cmds=(), active=False):
    """cmds: [(when, command)] Bash calls made in this turn before the reply."""
    start = written_at - timedelta(minutes=20)
    fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    fh.write(json.dumps({"type": "user", "timestamp": iso(start),
                         "message": {"role": "user", "content": "how long until the release?"}}) + "\n")
    for i, (when, cmd) in enumerate(cmds):
        fh.write(json.dumps({"type": "assistant", "timestamp": iso(when), "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t%d" % i, "name": "Bash", "input": {"command": cmd}}]}}) + "\n")
        fh.write(json.dumps({"type": "user", "timestamp": iso(when), "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t%d" % i, "content": "ok"}]}}) + "\n")
    fh.write(json.dumps({"type": "assistant", "timestamp": iso(written_at), "message": {"role": "assistant", "content": [
        {"type": "text", "text": reply}]}}) + "\n")
    fh.close()
    try:
        return t.run("no-invented-clock-stop.py", {"transcript_path": fh.name, "session_id": "s%d" % next(sessions),
                                                   "stop_hook_active": active})
    finally:
        os.unlink(fh.name)


def hm(dt):
    return dt.strftime("%H:%M")


def case(label, reply, written_at, block, cmds=(), active=False):
    p = run(reply, written_at, cmds, active)
    t.check(label, (p.returncode == 2) == block,
            "want %s got exit %d %s" % ("block" if block else "pass", p.returncode, p.stderr[:300]))
    return p.stderr


now = datetime.now().astimezone().replace(second=0, microsecond=0)
ahead = now + timedelta(minutes=77)
err = case("a time stated as now that is 77 minutes off is caught",
           "It's %s now, so the release window has closed." % hm(ahead), now, True)
t.check("the message shows the real time of the sentence", hm(now) in err and "off by" in err, err[:400])
case("a time stated as now that matches the clock passes",
     "It's %s now, so there is still room before the release." % hm(now), now, False)
case("a time two minutes off is inside the tolerance",
     "It is %s right now." % hm(now + timedelta(minutes=2)), now, False)
case("a time in a scheduled job name claims nothing about now",
     "The 00:30 nightly job and the 07:45 check both ran.", now, False)
case("a quoted time in backticks is reported speech",
     "The log line said `it's %s now` and that was wrong." % hm(ahead), now, False)
case("a quoted time in a blockquote is reported speech",
     "> It's %s now\n\nThat line was invented." % hm(ahead), now, False)
case("a count is not a time", "We have currently 3 files left to port.", now, False)

case("minutes-left arithmetic with no clock reading is caught",
     "We have 20 minutes left before the release.", now, True)
case("minutes-left arithmetic after a fresh date reading passes",
     "We have 20 minutes left before the release.", now, False,
     cmds=[(now - timedelta(minutes=1), "date '+%H:%M:%S'")])
case("minutes-left arithmetic after a stale date reading is caught",
     "We have 20 minutes left before the release.", now, True,
     cmds=[(now - timedelta(minutes=12), "date")])
case("a Date.now() reading counts as a clock reading",
     "That leaves us 15 minutes to finish.", now, False,
     cmds=[(now - timedelta(minutes=1), "node -e 'console.log(Date.now())'")])
case("a second pass in the same turn never blocks",
     "It's %s now." % hm(ahead), now, False, active=True)

os.environ["CLAUDE_CONFIG_DIR"] = t.config
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "hooks", "lib"))
import guardhooks_core as G  # noqa: E402
G.write_declaration("no-invented-clock-stop", "these times are from a schedule file, not the present")
case("a live declaration lets the reply through", "It's %s now." % hm(ahead), now, False)

t.done()
