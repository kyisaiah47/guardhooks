"""Matcher for the Lenis nested-scroll guard. Read by no-lenis-scroll-trap.py.

The patterns live in lenis_nested_scroll.json beside this file.
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "lenis_nested_scroll.json"), encoding="utf-8") as fh:
    _SPEC = json.load(fh)

BLOCK_TEXT = _SPEC["block_text"]
MIN_VERSION = _SPEC["min_version"]
INITS = [(label, re.compile(rx)) for label, rx in _SPEC["inits"]]
SATISFIED = [re.compile(rx) for rx in _SPEC["satisfied_by"]]


def strip_comments(src):
    """Drop // and /* */ comments, keeping newlines so line numbers survive.

    A comment that explains the option quotes the option, so a plain search would pass on the
    comment alone with the option deleted from the code.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        c, d = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and d == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and d == "*":
            i += 2
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                if src[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
            continue
        if c in "\"'`":
            q = c
            out.append(c)
            i += 1
            while i < n:
                if src[i] == "\\":
                    out.append(src[i:i + 2])
                    i += 2
                    continue
                out.append(src[i])
                if src[i] == q:
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def options_after(code, start):
    """The balanced brace group that follows a mount, which is where the option belongs."""
    open_ = code.find("{", start)
    if open_ < 0 or open_ - start > 400:
        return ""
    depth, instr, i = 0, None, open_
    while i < len(code):
        ch = code[i]
        if instr:
            if ch == "\\":
                i += 2
                continue
            if ch == instr:
                instr = None
            i += 1
            continue
        if ch in "\"'`":
            instr = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return code[open_:i + 1]
        i += 1
    return code[open_:]


def find(content, path=""):
    """Every Lenis mount in `content` that does not allow nested scroll."""
    code = strip_comments(content or "")
    hits = []
    for label, rx in INITS:
        for m in rx.finditer(code):
            opts = options_after(code, m.end())
            if not opts:
                hits.append("%s with no options object, so allowNestedScroll is at its default (false)" % label)
                continue
            if any(s.search(opts) for s in SATISFIED):
                continue
            if re.search(r"allowNestedScroll", opts):
                hits.append("%s where allowNestedScroll is present but not `true`" % label)
            else:
                hits.append("%s with no `allowNestedScroll: true`" % label)
    return hits
