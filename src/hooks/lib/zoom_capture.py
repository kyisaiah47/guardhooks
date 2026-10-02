"""Zoom in a screen recording, defined once. Read by no-zoom-capture.py.

No scale animation on a captured page or screenshot in a recorder. Not a Ken Burns, not a
punch-in, not 1.08x. A clip shows the page at full width and scrolls down it.

Scope: only files that capture a live page are checked. That is a path under capture/, record/,
shoot/, screencast/ or demo-video/, a Playwright spec, or content that drives a screencast or a
beat player. Inside that scope, a scale() on a transform is flagged only when there is also
evidence that it is animated: a transition naming transform, a keyframes block,
requestAnimationFrame, .animate(, a GSAP tween, or a zoom keyword such as zoomTo or kenBurns.
A button's hover scale in app code never enters the scope, because that file is not a recorder.
"""
import re

BLOCK_TEXT = (
    "Zooming in a screen recording is not allowed.\n"
    "\n"
    "Do not animate scale on a captured page or screenshot: no Ken Burns, no punch-in, not even\n"
    "1.08x. Show the page at full width and scroll down it. Remove the scale entirely rather than\n"
    "tuning it to a smaller factor.\n"
)

RECORDER_PATH = re.compile(
    r"(/demo-video/|/capture/|/shoot/|/record/|/recordings?/|/screencast/|\.spec\.[cm]?[jt]s$)", re.I)
RECORDER_CONTENT = re.compile(
    r"startScreencast|recordVideo|startRecording\(|recordVideo:|screencastFrame|"
    r"BEATS\[|requestAnimationFrame\(tick\)|getElementById\(['\"]shot['\"]\)")
SKIP_PATH = re.compile(r"\.bundle\.js$|/node_modules/|\.min\.js$")

SCALE_ASSIGN = re.compile(r"\.style\.transform\s*=\s*[`'\"][^`'\"]*scale\(", re.I)
CSS_SCALE_PROP = re.compile(r"transform\s*:\s*[^;{}\n]*scale\(", re.I)
KEYFRAME_BLOCK = re.compile(r"@keyframes[^{]*\{([\s\S]*?)\}\s*\}", re.I)
ANIMATE_SCALE = re.compile(r"\.animate\(\s*\[[\s\S]{0,400}?scale\(", re.I)
GSAP_SCALE = re.compile(r"gsap\.(to|fromTo|timeline)[\s\S]{0,200}?scale", re.I)

TRANSITION_TRANSFORM = re.compile(r"transition\s*[:=]\s*['\"]?[^;'\"]*transform", re.I)
RAF = re.compile(r"requestAnimationFrame\(")
KEN_BURNS_KEYWORD = re.compile(
    r"\b(kenBurns|ken-burns|punchIn|punch-in|panZoom|pan-zoom|zoomTo|zoomIn|zoom-in|"
    r"zoomOut|zoom-out)\b", re.I)

BAN_MARKER = re.compile(r"no-zoom-capture|zoom_capture|Zooming in a screen recording is not allowed", re.I)


def is_recorder(path, content):
    if SKIP_PATH.search(path or ""):
        return False
    return bool(RECORDER_PATH.search(path or "") or RECORDER_CONTENT.search(content or ""))


def _animated(text):
    return bool(
        TRANSITION_TRANSFORM.search(text) or KEYFRAME_BLOCK.search(text)
        or RAF.search(text) or ANIMATE_SCALE.search(text) or GSAP_SCALE.search(text)
        or KEN_BURNS_KEYWORD.search(text))


def find(content, path=""):
    """Return a list of reasons, empty when clean."""
    if not content or BAN_MARKER.search(content) or not is_recorder(path, content):
        return []
    has_scale = bool(SCALE_ASSIGN.search(content) or CSS_SCALE_PROP.search(content)
                     or ANIMATE_SCALE.search(content) or GSAP_SCALE.search(content))
    if not has_scale or not _animated(content):
        return []
    reasons = []
    for label, rx in (
        ("a .style.transform assignment carrying scale(", SCALE_ASSIGN),
        ("a CSS transform declaration carrying scale(", CSS_SCALE_PROP),
        ("an animate() scale tween", ANIMATE_SCALE),
        ("a GSAP tween touching scale", GSAP_SCALE),
    ):
        for m in rx.finditer(content):
            line = content.count("\n", 0, m.start()) + 1
            snippet = content[m.start():m.start() + 90].splitlines()[0]
            reasons.append("line %d: %s: `%s`" % (line, label, snippet.strip()))
    return reasons
