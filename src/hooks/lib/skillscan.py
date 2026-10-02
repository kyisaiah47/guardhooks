"""The skill supply-chain scanner. Read by skill-scan.py (hook and command line).

It scans a skill directory, or a single SKILL.md, for the red flags of a malicious or careless
community skill:

  NET       a network call in code (curl, wget, fetch(), requests, urllib, a URL)
  PIPE      pipe-to-shell (curl ... | sh)
  BLOB      a base64 or hex blob of 200 characters or more
  CRED      a credential path or key reference (~/.ssh, .env, .netrc, keychain, api_key, tokens)
  RMRF      rm -rf
  OVERRIDE  instruction-override language ("ignore previous instructions", "do not tell the user")
  UNICODE   invisible or bidirectional unicode characters
  EXEC      an executable or binary file shipped with the skill

In Markdown, NET and CRED only count inside fenced code; the other checks apply everywhere.

Allowlist: <config>/guardhooks/skill-scan-allowlist.txt, one "<CHECK> <path-glob>" per line, where
CHECK is one of the names above or *. The glob matches the relative path the scanner prints,
for example "my-skill/SKILL.md". Add a line only after reading the flagged line yourself.
"""
import fnmatch
import os
import re
import stat

import guardhooks_core as G

MD_EXT = {".md", ".markdown"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf",
            ".mp4", ".mov", ".mp3", ".wav", ".woff", ".woff2", ".ttf", ".otf",
            ".zip", ".gz", ".tar", ".dmg", ".pkg"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
MAX_CONTENT_BYTES = 2 * 1024 * 1024

RE_NET = re.compile(r"\bcurl\b|\bwget\b|\bfetch\s*\(|\brequests\.(get|post|put)\b"
                    r"|\burllib\.request\b|https?://", re.I)
RE_PIPE = re.compile(
    r"(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(sh|bash|zsh|dash|python3?|node|perl|ruby)\b"
    r"|\b(sh|bash|zsh)\s+<\(\s*(curl|wget)\b"
    r"|\b(sh|bash|zsh)\s+-c\s+[\"']?\s*\$\(\s*(curl|wget)\b", re.I)
RE_B64 = re.compile(r"[A-Za-z0-9+/]{200,}={0,3}")
RE_HEX = re.compile(r"\b[0-9a-fA-F]{200,}\b|(?:\\x[0-9a-fA-F]{2}){67,}")
RE_CRED = re.compile(
    r"~/\.ssh|\$HOME/\.ssh|\.ssh/(id_|config|known_hosts|authorized_keys)"
    r"|(?<!process)(?<!\bmeta)(?<!Deno)\.env\b"
    r"|\.netrc\b|\.aws/credentials|\.npmrc\b|\.pypirc\b|\.kube/config"
    r"|\bkeychain\b|security\s+find-(generic|internet)-password"
    r"|api[_-]?key|(access|auth|secret|bearer|refresh)[_-]?token|credentials?\.json",
    re.I)
RE_RM = re.compile(r"\brm\s+((-{1,2}[A-Za-z-]+)\s+)*-{1,2}[A-Za-z-]+")
RE_OVERRIDE = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts)"
    r"|disregard\s+(all\s+)?(previous|prior|above|earlier|the)\s+(instructions|rules|system\s+prompt)"
    r"|do\s+not\s+tell\s+the\s+user|don.?t\s+tell\s+the\s+user"
    r"|without\s+telling\s+the\s+user|never\s+(tell|inform)\s+the\s+user"
    r"|hide\s+(this|it)\s+from\s+the\s+user"
    r"|do\s+not\s+(mention|disclose|reveal)\s+(this|it)"
    r"|bypasspermissions|dangerously", re.I)

BAD_UNI = set()
for _lo, _hi in ((0x00AD, 0x00AD), (0x180E, 0x180E), (0x200B, 0x200F),
                 (0x202A, 0x202E), (0x2060, 0x2064), (0x2066, 0x2069), (0xFEFF, 0xFEFF)):
    BAD_UNI.update(range(_lo, _hi + 1))

CHECK_DESC = {
    "NET": "network call in code",
    "PIPE": "pipe-to-shell",
    "BLOB": "large base64 or hex blob",
    "CRED": "credential path or key reference",
    "RMRF": "rm -rf",
    "OVERRIDE": "instruction-override language",
    "UNICODE": "invisible or bidirectional unicode",
    "EXEC": "executable or binary file",
    "READ": "unreadable file",
}


def allowlist_path():
    return os.path.join(G.config_dir(), "guardhooks", "skill-scan-allowlist.txt")


def skills_root():
    return os.path.realpath(os.path.join(G.config_dir(), "skills"))


def excerpt(line):
    s = line.strip()
    return s[:160] + ("..." if len(s) > 160 else "")


def rm_rf_hit(line):
    for m in RE_RM.finditer(line):
        has_r = has_f = False
        for tok in m.group(0).split()[1:]:
            if tok.startswith("--"):
                has_r = has_r or tok == "--recursive"
                has_f = has_f or tok == "--force"
            elif tok.startswith("-"):
                has_r = has_r or ("r" in tok or "R" in tok)
                has_f = has_f or ("f" in tok)
        if has_r and has_f:
            return True
    return False


def load_allowlist():
    rules = []
    try:
        with open(allowlist_path(), encoding="utf-8") as fh:
            for raw in fh:
                s = raw.strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split(None, 1)
                if len(parts) == 2:
                    rules.append((parts[0].upper(), parts[1]))
    except OSError:
        pass
    return rules


def is_allowed(check, rel, rules):
    return any((c == "*" or c == check) and fnmatch.fnmatch(rel, g) for c, g in rules)


def scan_content(path, rel, findings):
    ext = os.path.splitext(path)[1].lower()
    try:
        if os.path.getsize(path) > MAX_CONTENT_BYTES:
            findings.append(("READ", rel, 0, "larger than 2 MB, content not scanned"))
            return
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        findings.append(("READ", rel, 0, "unreadable: %s" % e))
        return
    if b"\x00" in raw[:8192]:
        return
    text = raw.decode("utf-8", errors="replace")
    is_md = ext in MD_EXT
    in_fence = False
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.lstrip()
        if is_md and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = not in_fence
            continue
        code_ctx = (not is_md) or in_fence
        if RE_PIPE.search(line):
            findings.append(("PIPE", rel, i, excerpt(line)))
        if rm_rf_hit(line):
            findings.append(("RMRF", rel, i, excerpt(line)))
        if RE_B64.search(line):
            findings.append(("BLOB", rel, i, "base64-like blob of 200+ characters: " + excerpt(line)[:80]))
        elif RE_HEX.search(line):
            findings.append(("BLOB", rel, i, "hex blob of 200+ characters: " + excerpt(line)[:80]))
        if RE_OVERRIDE.search(line):
            findings.append(("OVERRIDE", rel, i, excerpt(line)))
        bad = sorted({ord(c) for c in line if ord(c) in BAD_UNI})
        if bad:
            findings.append(("UNICODE", rel, i, "invisible or bidi characters: " + ", ".join("U+%04X" % c for c in bad)))
        if code_ctx:
            if RE_NET.search(line):
                findings.append(("NET", rel, i, excerpt(line)))
            if RE_CRED.search(line):
                findings.append(("CRED", rel, i, excerpt(line)))


def walk_exec(root, relbase, findings):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if os.path.islink(p):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            kinds = []
            if st.st_mode & 0o111:
                kinds.append("exec-bit")
            try:
                with open(p, "rb") as fh:
                    if b"\x00" in fh.read(8192):
                        kinds.append("binary")
            except OSError:
                pass
            if kinds:
                findings.append(("EXEC", os.path.relpath(p, relbase), 0,
                                 "+".join(kinds) + " file shipped with the skill"))


def rel_base_for(target):
    """Report paths relative to the skills folder when the target is inside it, otherwise relative
    to the target's parent, so a report reads <skill-name>/<file>."""
    rt = os.path.realpath(target)
    root = skills_root()
    if rt == root or rt.startswith(root + os.sep):
        return root
    return os.path.dirname(rt) if os.path.isdir(rt) else os.path.dirname(os.path.dirname(rt))


def scan(target, rules=None):
    """Scan one skill directory or file. Returns (active findings, suppressed findings), or None
    when the target does not exist. Each finding is (check, relpath, line, detail)."""
    rules = load_allowlist() if rules is None else rules
    target = os.path.abspath(os.path.expanduser(target))
    if not os.path.exists(target):
        return None
    # Walk the real path, so relative paths in the report agree with rel_base_for, which also
    # resolves symlinks (on macOS /tmp is a link to /private/tmp).
    target = os.path.realpath(target)
    relbase = rel_base_for(target)
    findings = []
    if os.path.isdir(target):
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                if os.path.islink(p) or os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    continue
                scan_content(p, os.path.relpath(p, relbase), findings)
        walk_exec(target, relbase, findings)
    else:
        scan_content(target, os.path.relpath(target, relbase), findings)
        if os.path.basename(target) == "SKILL.md":
            walk_exec(os.path.dirname(target), relbase, findings)
    active, suppressed = [], []
    for f in findings:
        (suppressed if is_allowed(f[0], f[1], rules) else active).append(f)
    active.sort(key=lambda f: (f[1], f[2], f[0]))
    return active, suppressed


def report(target, active, suppressed):
    lines = ["skill-scan: %s" % target]
    for check, rel, line, detail in active:
        loc = "%s:%d" % (rel, line) if line else rel
        lines.append("  [%-8s] %s: %s" % (check, loc, detail))
    if active:
        lines.append("  FAIL: %d finding(s)%s" % (
            len(active), (", %d allowlisted hit(s) suppressed" % len(suppressed)) if suppressed else ""))
    else:
        lines.append("  CLEAN: no findings%s" % (
            (" (%d allowlisted hit(s) suppressed)" % len(suppressed)) if suppressed else ""))
    return "\n".join(lines)
