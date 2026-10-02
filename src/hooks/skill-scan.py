#!/usr/bin/env python3
"""Skill supply-chain scan, as a PreToolUse (Bash) hook and as a command.

As a hook: when a shell command copies, moves, syncs or links something into a skills folder
(<config>/skills, ~/.claude/skills, a project's .claude/skills), the source is scanned first and
the command is denied when the scan finds anything. A command that downloads or clones straight
into a skills folder is denied, because there is nothing on disk to scan yet.

As a command:
    python3 skill-scan.py <skill-dir | SKILL.md> [more ...]
Exit 0 means clean, 1 means findings, 64 means a usage error.

The checks and the allowlist are described in lib/skillscan.py.
"""
import glob
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import skillscan as K
except Exception:
    sys.exit(0)

SELF = os.path.abspath(__file__)
SPLIT = re.compile(r"\|\||&&|[;\n]")
COPY_TOOLS = {"cp", "mv", "rsync", "ditto", "ln", "install"}
FETCH_TOOLS = re.compile(r"^(?:git\s+clone|gh\s+repo\s+clone|curl|wget|unzip|tar|svn\s+(?:checkout|co|export)|npx\s+degit|degit)\b")


def skills_dir_rx():
    parts = [r"\.claude[\w.-]*/skills\b", r"\$\{?CLAUDE_CONFIG_DIR\}?/skills\b"]
    cfg = G.config_dir().rstrip("/")
    parts.append(re.escape(cfg) + r"/skills\b")
    home = os.path.expanduser("~")
    if cfg.startswith(home):
        parts.append(r"~" + re.escape(cfg[len(home):]) + r"/skills\b")
    return re.compile("|".join(parts))


def expand(token, cwd):
    t = token.replace("${HOME}", "~").replace("$HOME", "~")
    t = t.replace("${CLAUDE_CONFIG_DIR}", G.config_dir()).replace("$CLAUDE_CONFIG_DIR", G.config_dir())
    t = os.path.expanduser(t)
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    return t


def sources_of(segment, cwd, in_skills):
    """(tool, [source paths]) for a copy-like segment whose destination is a skills folder."""
    try:
        argv = shlex.split(segment)
    except ValueError:
        argv = segment.split()
    while argv and (argv[0] == "sudo" or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0])):
        argv = argv[1:]
    if not argv:
        return None, []
    tool = os.path.basename(argv[0])
    if tool not in COPY_TOOLS:
        return None, []
    operands = [a for a in argv[1:] if not a.startswith("-")]
    if len(operands) < 2 or not in_skills(operands[-1]):
        return None, []
    out = []
    for src in operands[:-1]:
        if in_skills(src):
            continue
        p = expand(src, cwd)
        matches = glob.glob(p) if any(ch in p for ch in "*?[") else [p]
        out += matches or [p]
    return tool, out


def hook():
    ev = G.read_event()
    if not ev or ev.get("tool_name") != "Bash":
        return
    command = str((ev.get("tool_input") or {}).get("command") or "")
    if SELF in command or "skill-scan.py" in command:
        return
    rx = skills_dir_rx()
    if not rx.search(command):
        return
    cwd = str(ev.get("cwd") or os.getcwd())

    def in_skills(tok):
        return bool(rx.search(tok)) or bool(rx.search(expand(tok, cwd)))

    reports, missing = [], []
    for seg in SPLIT.split(command):
        seg = seg.strip()
        if not seg or not rx.search(seg):
            continue
        if FETCH_TOOLS.match(seg):
            G.deny(
                "This command downloads or unpacks straight into a skills folder, so nothing can be scanned first.\n"
                "Community skills are untrusted input, and a skill runs with your local permissions.\n\n"
                "Do this instead:\n"
                "  1. Fetch the source into a scratch folder. Do not run anything from it.\n"
                "  2. Scan it: python3 %s <fetched-dir>\n"
                "  3. If it is clean, copy the skill folder into the skills folder.\n"
                "     The copy is scanned again by this hook." % SELF)
        tool, srcs = sources_of(seg, cwd, in_skills)
        if not tool:
            continue
        for src in srcs:
            res = K.scan(src)
            if res is None:
                missing.append(src)
                continue
            active, suppressed = res
            if active:
                reports.append(K.report(src, active, suppressed))
    if missing:
        G.deny("This command copies into a skills folder, but the source could not be found to scan:\n  %s\n"
               "Copy from a path that exists so it can be scanned first." % "\n  ".join(missing))
    if reports:
        G.deny(
            "The skill you are copying into a skills folder failed the supply-chain scan.\n\n"
            + "\n\n".join(reports) +
            "\n\nRead every finding before you decide. Do not install the skill as it is.\n"
            "If a finding is a reviewed, legitimate part of the skill, add a line\n"
            "\"<CHECK> <path-glob>\" to %s and copy again." % K.allowlist_path())


def cli(argv):
    if argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nChecks: " + ", ".join("%s=%s" % (k, v) for k, v in K.CHECK_DESC.items() if k != "READ"))
        return 0
    rules = K.load_allowlist()
    total = 0
    for target in argv:
        res = K.scan(target, rules)
        if res is None:
            print("error: no such path: %s" % target, file=sys.stderr)
            return 64
        active, suppressed = res
        print(K.report(os.path.abspath(os.path.expanduser(target)), active, suppressed))
        total += len(active)
    return 1 if total else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    hook()
