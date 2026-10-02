#!/usr/bin/env python3
"""Fixtures for no-lenis-scroll-trap.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-lenis-scroll-trap")

PATH = "/tmp/p/src/components/SmoothScroll.tsx"


def w(label, src, want, path=PATH):
    t.pre(label, "Write", {"file_path": path, "content": src}, want)


# must deny
w("options without allowNestedScroll", "const lenis = new Lenis({ lerp: 0.35 });", "deny")
w("a typical options object", "const lenis = new Lenis({ autoRaf: true, lerp: 0.35, anchors: false });", "deny")
w("no options at all", "const lenis = new Lenis();", "deny")
w("present but false", "const lenis = new Lenis({ allowNestedScroll: false, lerp: 0.35 });", "deny")
w("multi-line options with the option missing",
  "const lenis = new Lenis({\n  lerp: 0.1,\n  smoothWheel: true,\n  wheelMultiplier: 1,\n});", "deny")
w("a block comment quotes the option but the code does not set it",
  "/* allowNestedScroll: true is why nested boxes scroll. */\nconst lenis = new Lenis({ lerp: 0.35 });", "deny")
w("a line comment quotes the option", "// allowNestedScroll: true\nconst lenis = new Lenis({ lerp: 0.35 });", "deny")
w("a ReactLenis mount without the option",
  "<ReactLenis root options={{ lerp: 0.1 }}>{children}</ReactLenis>", "deny")

# must allow
w("the option set to true",
  "const lenis = new Lenis({ lerp: 0.35, smoothWheel: true, wheelMultiplier: 1, allowNestedScroll: true });", "allow")
w("the option first", "const lenis = new Lenis({ allowNestedScroll: true, autoRaf: true, lerp: 0.35 });", "allow")
w("a prevent() function instead", 'const lenis = new Lenis({ lerp: 0.35, prevent: (node) => node.id === "modal" });', "allow")
w("a ReactLenis mount with the option",
  "<ReactLenis root options={{ lerp: 0.1, allowNestedScroll: true }}>{children}</ReactLenis>", "allow")
w("nothing to do with Lenis", 'const x = new Map();\nconst y = document.querySelector(".fence");', "allow")
w("a sentence about the rule in a comment", "// Lenis needs allowNestedScroll or nested boxes stop scrolling.", "allow")
w("the guard's own pattern file", "const lenis = new Lenis({ lerp: 0.35 });",
  "allow", path="/tmp/p/hooks/lib/lenis_nested_scroll.json")

reason = t.pre("deny message gives the fix", "Write", {"file_path": PATH, "content": "new Lenis()"}, "deny")
t.check("deny message names allowNestedScroll: true", "allowNestedScroll: true" in reason)

t.done()
