#!/usr/bin/env python3
"""PreToolUse (Bash): deny a direct skill or plugin install, so nothing lands in a skills folder
unscanned.

It matches `npx skills add`, `skills install`, `claude plugin install` and `/plugin install`.
The denial explains how to fetch the source, scan it with skill-scan, and copy it by hand.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
except Exception:
    sys.exit(0)

INSTALL = re.compile(
    r"(?:^|[\s;|&(])skills\s+(?:add|install)(?:\s|$)"
    r"|(?:^|[\s;|&(])/?plugins?\s+(?:install|add)(?:\s|$)", re.I)


def main():
    ev = G.read_event()
    if not ev or ev.get("tool_name") != "Bash":
        return
    command = str((ev.get("tool_input") or {}).get("command") or "")
    if not INSTALL.search(command):
        return
    scanner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill-scan.py")
    G.deny(
        "Direct skill and plugin installs are blocked until the source is scanned.\n"
        "Community skills are untrusted input, and a skill runs with your local permissions and credentials.\n\n"
        "Do this instead:\n"
        "  1. Fetch the source without installing it (git clone or a download into a scratch folder).\n"
        "     Do not run anything from it.\n"
        "  2. Scan it: python3 %s <fetched-dir>\n"
        "  3. If it is clean, copy the skill folder into %s by hand.\n"
        "     If it has findings, read each one before you decide.\n"
        "     A reviewed, legitimate finding can be allowlisted in %s as \"<CHECK> <path-glob>\"."
        % (scanner, os.path.join(G.config_dir(), "skills"),
           os.path.join(G.config_dir(), "guardhooks", "skill-scan-allowlist.txt")))


if __name__ == "__main__":
    main()
