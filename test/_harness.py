"""Shared test helpers. Every case runs the REAL hook script as a subprocess, with a real JSON
event on stdin, and judges the hook's own decision. Testing a library function alone can pass
while the hook never sees the field it guards.

Each run gets its own temporary CLAUDE_CONFIG_DIR, so a test never reads or writes the config of
the machine running it.

    from _harness import T
    t = T("no-em-dash")
    t.pre("an em dash in prose", "Write", {"file_path": "/tmp/p/a.md", "content": "..."}, "deny")
    t.stop("reply with a dash", "text", block=True)
    t.prompt("injects the clock", "what time is it", contains="date")
    t.done()
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "src", "hooks")


class T:
    def __init__(self, name):
        self.name = name
        self.fails = []
        self.count = 0
        self.config = tempfile.mkdtemp(prefix="guardhooks-test-")
        print("\n=== %s ===" % name)

    # -- plumbing ------------------------------------------------------------------------
    def env(self, extra=None):
        e = dict(os.environ)
        e["CLAUDE_CONFIG_DIR"] = self.config
        e["PYTHONDONTWRITEBYTECODE"] = "1"
        if extra:
            e.update(extra)
        return e

    def run(self, script, event, env=None):
        path = os.path.join(HOOKS, script)
        return subprocess.run([sys.executable, path], input=json.dumps(event),
                              capture_output=True, text=True, env=self.env(env), timeout=60)

    def record(self, ok, label, detail=""):
        self.count += 1
        print("  %-4s %s%s" % ("PASS" if ok else "FAIL", label, ("  [" + detail + "]") if detail and not ok else ""))
        if not ok:
            self.fails.append(label)

    @staticmethod
    def transcript(reply, prompt="go", prior=None):
        """Write a minimal transcript: optional prior (role, text) pairs, the prompt, the reply."""
        fh = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for role, text in (prior or []):
            fh.write(json.dumps({"type": role, "message": {"role": role, "content": [{"type": "text", "text": text}]}}) + "\n")
        fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
        fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]}}) + "\n")
        fh.close()
        return fh.name

    # -- PreToolUse ------------------------------------------------------------------------
    def pre_result(self, script, tool, tool_input, env=None, extra_event=None):
        ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "session_id": "test"}
        if extra_event:
            ev.update(extra_event)
        p = self.run(script, ev, env)
        decision, reason, ctx = "allow", "", ""
        if p.stdout.strip():
            try:
                out = json.loads(p.stdout)["hookSpecificOutput"]
                decision = out.get("permissionDecision") or "allow"
                reason = out.get("permissionDecisionReason") or ""
                ctx = out.get("additionalContext") or ""
            except Exception:
                decision = "allow"
        return p, decision, reason, ctx

    def pre(self, label, tool, tool_input, want, script=None, env=None, extra_event=None):
        p, decision, reason, _ = self.pre_result(script or self.name + ".py", tool, tool_input, env, extra_event)
        self.record(decision == want and p.returncode == 0, label,
                    "want %s got %s exit %d %s" % (want, decision, p.returncode, p.stderr.strip()[:300]))
        return reason

    # -- Stop ------------------------------------------------------------------------------
    def stop_result(self, script, reply, prompt="go", prior=None, env=None, active=False):
        path = self.transcript(reply, prompt, prior)
        try:
            p = self.run(script, {"hook_event_name": "Stop", "transcript_path": path,
                                  "session_id": "test", "stop_hook_active": active}, env)
        finally:
            os.unlink(path)
        return p

    def stop(self, label, reply, block, script=None, prompt="go", prior=None, env=None, active=False):
        p = self.stop_result(script or self.name + ".py", reply, prompt, prior, env, active)
        blocked = p.returncode == 2
        self.record(blocked == block, label,
                    "want %s got exit %d %s" % ("block" if block else "pass", p.returncode, p.stderr.strip()[:300]))
        return p.stderr

    # -- UserPromptSubmit -----------------------------------------------------------------------
    def prompt_result(self, script, prompt, env=None):
        p = self.run(script, {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "session_id": "test"}, env)
        ctx = ""
        if p.stdout.strip():
            try:
                ctx = json.loads(p.stdout)["hookSpecificOutput"].get("additionalContext") or ""
            except Exception:
                ctx = p.stdout
        return p, ctx

    def prompt(self, label, prompt, inject, contains=None, script=None, env=None):
        p, ctx = self.prompt_result(script or self.name + ".py", prompt, env)
        ok = p.returncode == 0 and bool(ctx.strip()) == inject
        if ok and contains:
            ok = contains in ctx
        self.record(ok, label, "want inject=%s got %r exit %d" % (inject, ctx[:200], p.returncode))
        return ctx

    # -- generic -------------------------------------------------------------------------
    def check(self, label, cond, detail=""):
        self.record(bool(cond), label, detail)

    def done(self):
        shutil.rmtree(self.config, ignore_errors=True)
        print("  %s: %d checks, %d failed" % (self.name, self.count, len(self.fails)))
        sys.exit(1 if self.fails or self.count == 0 else 0)
