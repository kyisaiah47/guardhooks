#!/usr/bin/env python3
"""Fixtures for no-unobserved-outcome-stop.py. Each case writes a real transcript with tool calls
and tool results, then runs the hook against it."""
import json
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-unobserved-outcome-stop")
SCRIPT = "no-unobserved-outcome-stop.py"
IMG = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo="}}]
_n = [0]


def user(text, side=False):
    return {"type": "user", "isSidechain": side, "message": {"role": "user", "content": text}}


def call(name, inp, side=False):
    _n[0] += 1
    return {"type": "assistant", "isSidechain": side, "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "tu%d" % _n[0], "name": name, "input": inp}]}}


def result(content, side=False):
    return {"type": "user", "isSidechain": side, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "tu%d" % _n[0], "content": content}]}}


def pasted(text):
    return {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}] + IMG}}


def reply(text, side=False):
    return {"type": "assistant", "isSidechain": side, "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


def run(rows, sid="s1"):
    fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    fh.close()
    try:
        return t.run(SCRIPT, {"hook_event_name": "Stop", "transcript_path": fh.name,
                              "session_id": sid, "stop_hook_active": False})
    finally:
        os.unlink(fh.name)


def case(label, rows, block, sid=None):
    p = run(rows, sid or "case-%d" % t.count)
    t.check(label, (p.returncode == 2) == block,
            "want %s got exit %d %s" % ("block" if block else "pass", p.returncode, p.stderr[:300]))
    return p.stderr


SHOT_CMD = "node shot.mjs https://example.com /tmp/p/shot.png"

# [1] a visual claim with nothing observed
case("card renders claim with nothing observed",
     [user("fix the share card"), call("Edit", {"file_path": "/tmp/p/meta.ts", "old_string": "a", "new_string": "b"}),
      result("ok"), reply("The share card renders correctly now.")], True)

# [2] the same claim after a real capture read back
case("card renders claim after a real capture read back",
     [user("fix the share card"), call("Bash", {"command": SHOT_CMD}), result("saved"),
      call("Read", {"file_path": "/tmp/p/shot.png"}), result(IMG),
      reply("The share card renders correctly now.")], False)

# [3] a relayed subagent confirmation with no evidence of our own
err = case("relayed agent confirmation",
           [user("is the page fixed"), call("Agent", {"prompt": "check the page"}), result("done"),
            reply("The agent confirmed the page renders correctly.")], True)
t.check("relay block message says a subagent report is not an observation", "subagent's report" in err)

# [3b] a subagent's screenshot on its sidechain is not this session's evidence
case("a subagent's sidechain screenshot does not count",
     [user("is the page fixed"),
      call("Read", {"file_path": "/tmp/p/shot.png"}, side=True), result(IMG, side=True),
      reply("The page renders correctly now.")], True)

# [4] ordinary work claims carry their own evidence
case("tests pass, committed and pushed",
     [user("ship it"), call("Bash", {"command": "npm test && git push"}), result("ok"),
      reply("The tests pass. Committed and pushed to main.")], False)
case("file content claim", [user("edit it"), reply("The file now contains the new export.")], False)
case("a filename is not a platform",
     [user("fix it"), reply("I fixed the bug in tools/vercel-token.mjs and the import is correct.")], False)

# [5] predictions and quoting always pass
case("written as a prediction",
     [user("fix the card"), reply("The card should render correctly now. I have not checked it.")], False)
case("leading conditional", [user("x"), reply("If the cache clears, the page is live.")], False)
case("claim inside backticks", [user("x"), reply("The commit message says `the card renders correctly`.")], False)
case("claim inside a blockquote", [user("x"), reply("The report said:\n\n> the page is live\n\nI will check.")], False)

# [6] external claims
case("live claim with no probe",
     [user("deploy it"), call("Bash", {"command": "npm run deploy"}), result("exit 0"),
      reply("The fix is live on production.")], True)
case("live claim after curl of the site",
     [user("deploy it"), call("Bash", {"command": "curl -sI https://example.com"}), result("HTTP/2 200"),
      reply("The fix is live on production.")], False)
case("a probe of a different host does not answer a named surface",
     [user("deploy it"), call("Bash", {"command": "curl -sI https://example.com"}), result("HTTP/2 200"),
      reply("The post landed on github.com.")], True)
case("a fetch of the named host answers it",
     [user("post it"), call("WebFetch", {"url": "https://github.com/acme/repo/issues/1"}), result("issue text"),
      reply("The comment is live on github.com.")], False)

# [7] composed images are not captures
err = case("an image composed with PIL is not evidence",
           [user("fix the thumbnail"),
            call("Bash", {"command": "python3 -c \"from PIL import Image; Image.new('RGB',(10,10)).save('/tmp/p/mock.png')\""}),
            result("ok"), call("Read", {"file_path": "/tmp/p/mock.png"}), result(IMG),
            reply("The thumbnail now shows the new logo.")], True)
t.check("composed block message says the image was composed", "composed by this session" in err)
case("a crop of a real capture is still a capture",
     [user("fix the thumbnail"), call("Bash", {"command": SHOT_CMD}), result("saved"),
      call("Bash", {"command": "python3 -c \"from PIL import Image; Image.open('/tmp/p/shot.png').crop((0,0,9,9)).save('/tmp/p/crop.png')\""}),
      result("ok"), call("Read", {"file_path": "/tmp/p/crop.png"}), result(IMG),
      reply("The thumbnail now shows the new logo.")], False)
case("a capture of one site does not prove another named site",
     [user("check google"), call("Bash", {"command": SHOT_CMD}), result("saved"),
      call("Read", {"file_path": "/tmp/p/shot.png"}), result(IMG),
      reply("The Google result now shows the new thumbnail.")], True)

# [8] a user-pasted image counts
case("the user pasted a screenshot this turn",
     [pasted("here is what I see"), reply("The banner displays the new colours.")], False)

# [9] budget: the same claim blocks at most three times
rows = [user("fix the card"), reply("The share card renders correctly now.")]
codes = [run(rows, "budget").returncode for _ in range(4)]
t.check("same claim blocks three times then passes", codes == [2, 2, 2, 0], str(codes))

# [10] the declare escape
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "hooks", "lib"))
os.environ["CLAUDE_CONFIG_DIR"] = t.config
import guardhooks_core as G  # noqa: E402
G.write_declaration("no-unobserved-outcome-stop", "I captured the live card in the browser tool and looked at it.")
case("a live declaration lets the claim through",
     [user("fix the card"), reply("The share card renders correctly now.")], False)
shutil.rmtree(os.path.join(t.config, "guardhooks", "state", "declared"), ignore_errors=True)

# [11] fail open
p = t.run(SCRIPT, {"hook_event_name": "Stop", "transcript_path": "/tmp/p/does-not-exist.jsonl", "session_id": "x"})
t.check("a missing transcript passes", p.returncode == 0)
bad = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
bad.write("not json\n{\"message\": 5}\n")
bad.close()
p = t.run(SCRIPT, {"hook_event_name": "Stop", "transcript_path": bad.name, "session_id": "x"})
os.unlink(bad.name)
t.check("a malformed transcript passes", p.returncode == 0)
p = t.run(SCRIPT, {"hook_event_name": "Stop", "transcript_path": "", "stop_hook_active": True})
t.check("stop_hook_active passes", p.returncode == 0)

t.done()
