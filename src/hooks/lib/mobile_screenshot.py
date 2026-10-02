"""No phone-width photo of a site. Every capture of a product or a site is desktop width.

A phone photo of a site needs three things together:
  1. a capture: .screenshot(, a screencast, recordVideo, `playwright screenshot`, `--screenshot`;
  2. a phone viewport: a viewport under 600 CSS px, isMobile, a phone user agent or device
     descriptor, a phone-sized frame constant, or a phone width on --vw, --width, --frame,
     --viewport-size or --window-size;
  3. a site: a navigation to anything that is not a local file:// render.

Layout QA is not banned. A file under qa/, e2e/, tests/ or gates/, or a .test or .spec file,
renders at phone width to find broken mobile layouts, and that is allowed.

Escape: a line carrying `phone-viewport: third-party form` is automation that must emulate a
phone to operate someone else's form. It produces no media.

The pattern list lives in mobile_capture_patterns.json beside this file.
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "mobile_capture_patterns.json"), encoding="utf-8") as _f:
    P = json.load(_f)

PHONE = [(p["label"], re.compile(p["re"])) for p in P["phone_viewport"]]
CAPTURE = re.compile("|".join(P["capture"]))
GOTO = re.compile(P["goto"])
LOCAL_RENDER = re.compile(P["local_render"])
SITE_HINT = re.compile(P["site_hint"])
LOCAL_CONTENT = re.compile(P["local_content"])
QA_PATHS = re.compile(P["qa_paths"])
ESCAPE = re.compile(re.escape(P["escape"]))

BLOCK_TEXT = (
    "Phone-width photos of a site are not allowed. Capture it at desktop width.\n"
    "\n"
    "Use a viewport 1280 CSS px wide or wider. Do not set isMobile, a phone user agent or a phone\n"
    "device descriptor. Do not pass a phone width on --vw, --width, --frame, --viewport-size or\n"
    "--window-size.\n"
    "\n"
    "Layout QA at phone width is allowed in qa/, e2e/, tests/ and gates/ folders and in .test and\n"
    ".spec files. Automation that must emulate a phone to operate a third-party form can mark the\n"
    "line with `phone-viewport: third-party form`.\n"
)

# Reading, copying, moving or opening an image that already exists is not taking one.
SKIP_EVIDENCE = re.compile(r"^\s*(open|cp|mv|cat|file|identify|ffprobe|rm|ls)\b|\bgrep\b|\brg\b", re.I)

# Text about the ban is not an instance of it.
BAN_MARKER = re.compile(r"mobile-screenshot-guard|mobile_screenshot\.py|mobile_capture_patterns", re.I)


def _navigates_a_site(text):
    gotos = len(GOTO.findall(text))
    local = len(LOCAL_RENDER.findall(text))
    if gotos:
        return gotos > local
    if LOCAL_CONTENT.search(text):
        return False
    return bool(SITE_HINT.search(text))


def phone_hits(text):
    hits = []
    lines = text.split("\n")
    for label, rx in PHONE:
        for m in rx.finditer(text):
            ln = text.count("\n", 0, m.start())
            if ESCAPE.search(lines[ln] if ln < len(lines) else ""):
                continue
            hits.append((label, ln + 1, m.group(0)[:80]))
    return hits


def find(text, path=""):
    """Return a list of reasons, empty when clean. `path` is '' for a Bash command."""
    text = text or ""
    if not text.strip():
        return []
    if BAN_MARKER.search(text) or BAN_MARKER.search(path or ""):
        return []
    if path and QA_PATHS.search(path):
        return []
    if not path:
        if SKIP_EVIDENCE.search(text) or QA_PATHS.search(text):
            return []
    if not CAPTURE.search(text):
        return []
    hits = phone_hits(text)
    if not hits or not _navigates_a_site(text):
        return []
    if path:
        return ["line %d: %s (%r)" % (ln, label, snippet) for label, ln, snippet in hits]
    return ["%s (%r)" % (label, snippet) for label, ln, snippet in hits]
