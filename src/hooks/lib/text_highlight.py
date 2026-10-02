"""The text-highlight ban for screen recordings, defined once. Read by no-text-highlight.py.

A recorder is a file under a capture, record, shoot, screencast or video path, a Playwright spec,
or content that drives a screencast. In such a file, each gesture below paints a selection
highlight over the page's text, and a blue band across the product's own words is the first thing
a viewer sees.

A measurement Range (createRange plus getBoundingClientRect) paints nothing and is not matched.
Only a Range added to the live Selection is.

Escape: a drag that is not over text (a slider, a resize handle) carries `// drag: not-text` on
its mouse.down() line.
"""
import re

BLOCK_TEXT = (
    "Text highlighting is not allowed in a screen recording.\n"
    "\n"
    "Banned in a recorder: a drag-select, a double or triple click, selectText(), a Range added to\n"
    "the live Selection, execCommand('selectAll') and a `select` beat. The pointer should not rest\n"
    "on body text either. Hold still, hover a control, or move on.\n"
    "\n"
    "Recorders should also inject `user-select: none` and a transparent ::selection style.\n"
)

RECORDER_PATH = re.compile(
    r"(/videos?/|/demo-video/|/capture|/shoot|/record|/screencast|\.spec\.[cm]?[jt]s$)", re.I)
RECORDER_CONTENT = re.compile(
    r"startScreencast|recordVideo|startRecording\(|screencastFrame|\.screencast\(")
SKIP_PATH = re.compile(r"\.bundle\.js$|/node_modules/|\.min\.js$")

GESTURES = [
    ("a `select` beat declaration", re.compile(r"\bselect\s*:\s*\{")),
    ("selectText()", re.compile(r"\bselectText\s*\(")),
    ("a mouse-down to mouse-up drag gesture", re.compile(r"mouse\.down\(\)[\s\S]{0,800}?mouse\.up\(\)")),
    ("a double or triple click (clickCount 2 or 3)", re.compile(r"clickCount\s*:\s*[23]\b")),
    ("dblclick()", re.compile(r"\.dblclick\s*\(")),
    ("execCommand('selectAll')", re.compile(r"execCommand\(\s*['\"]selectAll")),
    ("a Range added to the live Selection",
     re.compile(r"getSelection\(\)[\s\S]{0,120}?\.addRange\s*\(|setBaseAndExtent\s*\(")),
]

# A per-line escape for a drag that is not over text. Nothing else clears the gesture.
ESCAPE = re.compile(r"mouse\.down\(\)[^\n]*//\s*drag:\s*not-text")


def is_recorder(path, content):
    if SKIP_PATH.search(path or ""):
        return False
    return bool(RECORDER_PATH.search(path or "") or RECORDER_CONTENT.search(content or ""))


def find(content, path=""):
    """Return a list of reasons, empty when clean."""
    if not content or not is_recorder(path, content):
        return []
    reasons = []
    for label, rx in GESTURES:
        for m in rx.finditer(content):
            if label.startswith("a mouse-down") and ESCAPE.search(content[m.start():m.end()]):
                continue
            snippet = content[m.start():m.start() + 90].splitlines()[0]
            line = content.count("\n", 0, m.start()) + 1
            reasons.append("line %d: %s: `%s`" % (line, label, snippet.strip()))
    return reasons
