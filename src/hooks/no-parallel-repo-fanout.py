#!/usr/bin/env python3
"""PreToolUse on Bash: deny a command that runs heavy per-repo work in parallel.

Heavy work means git push, pull, fetch, clone or commit, package installs and builds, browser
test runners and deploy scripts. Each of these can start its own hooks, node processes and
browsers. A loop that backgrounds them with '&', or xargs -P / GNU parallel with more than one
worker, runs them all at once and can make the machine unusable. The same loop run one repo at a
time is safe.

Heredoc bodies are ignored, so a commit message or a note that mentions these commands is fine.
Escape: `npx guardhooks declare no-parallel-repo-fanout "<reason>"` allows parallel runs for two
hours.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

HOOK_ID = "no-parallel-repo-fanout"

HEAVY = re.compile(
    r"git\s+(?:-C\s+\S+\s+)?(?:push|pull|fetch|clone|commit)\b"
    r"|\bvercel\s|\bnpm\s+(?:run|ci|install)\b|\bpnpm\s|\byarn\s|\bnext\s+build\b"
    r"|\bplaywright\b|deploy[\w-]*\.sh\b")
LOOP = re.compile(r"(?:^|[\s;&|(])(?:for|while|until)\s")
BARE_AMP = re.compile(r"(?<![&>|<])&(?![&>])")
XARGS_P = re.compile(r"\bxargs\b[^|;]*-P\s*(?:[2-9]|[1-9][0-9]+)")
GNU_PARALLEL = re.compile(r"(?:^|[;&|]\s*)parallel\s+(?:-|:::)", re.M)

MESSAGE = (
    "This command runs heavy per-repo work in parallel. Run it one repo at a time.\n"
    "\n"
    "Each git push, install, build or deploy can start its own hooks, node processes and\n"
    "browsers. Backgrounding them in a loop, or using xargs -P or GNU parallel, starts all of\n"
    "them at once and can make the machine unusable. The command still exits 0, so nothing\n"
    "reports the problem.\n"
    "\n"
    "Use a plain sequential loop with no '&' and no -P:\n"
    "\n"
    "    for repo in repo-a repo-b repo-c; do\n"
    "      git -C \"$repo\" push -q || echo \"failed $repo\"\n"
    "    done\n"
    "\n"
    "If the batch would exceed the tool timeout, split it across several calls.\n"
    "\n"
    "If the user explicitly wants parallel runs, record it for two hours with:\n"
    "    npx guardhooks declare no-parallel-repo-fanout \"<the user's reason>\"\n"
)


def strip_heredocs(command):
    return G.HEREDOC.sub(" <<HEREDOC ", command)


def backgrounded_loop(cmd):
    return bool(LOOP.search(cmd) and BARE_AMP.search(cmd))


def parallel_workers(cmd):
    return bool(XARGS_P.search(cmd) or GNU_PARALLEL.search(cmd))


def main():
    ev = G.read_event()
    if not ev or (ev.get("tool_name") or "") != "Bash":
        return
    command = str((ev.get("tool_input") or {}).get("command") or "")
    if not command:
        return
    cmd = strip_heredocs(command)
    if not HEAVY.search(cmd):
        return
    if not (backgrounded_loop(cmd) or parallel_workers(cmd)):
        return
    if G.declared(HOOK_ID):
        return
    G.deny(MESSAGE)


if __name__ == "__main__":
    main()
