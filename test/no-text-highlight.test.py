#!/usr/bin/env python3
"""Fixtures for no-text-highlight.py. Each case runs the real hook with a real PreToolUse event.

Gesture strings are assembled from fragments, so this file does not itself read as a recorder
that clicks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

DOWN = "mouse." + "down()"
UP = "mouse." + "up()"
MOVE = "mouse." + "move"

t = T("no-text-highlight")

DRAG = ("await page.%s(200, 300);\nawait page.%s;\nawait page.%s(600, 300, { steps: 20 });\nawait page.%s;\n"
        % (MOVE, DOWN, MOVE, UP))
DBL = "await page.click('pre', { clickCount: 2 });\n"
SELECT_TEXT = "await page.locator('h1').selectText();\n"
RANGE = ("await page.evaluate(() => { const r = document.createRange(); r.selectNodeContents(document.body);"
         " window.getSelection().addRange(r); });\n")
BEAT = "const beats = [{ at: 2, select: { from: 'h1', to: 'p' } }];\n"
SELECT_ALL = "await page.evaluate(() => document.execCommand('selectAll'));\n"
DBLCLICK = "await page.locator('code').dblclick();\n"

# must deny, by path
t.pre("drag-select in a capture script", "Write", {"file_path": "/tmp/p/capture/demo.mjs", "content": DRAG}, "deny")
t.pre("double click in a recording script", "Write", {"file_path": "/tmp/p/record/walkthrough.mjs", "content": DBL}, "deny")
t.pre("selectText in a Playwright spec", "Write", {"file_path": "/tmp/p/e2e/demo.spec.ts", "content": SELECT_TEXT}, "deny")
t.pre("Range added to the live Selection in a video script", "Write",
      {"file_path": "/tmp/p/video/intro.mjs", "content": RANGE}, "deny")
t.pre("a select beat in a shoot script", "Write", {"file_path": "/tmp/p/shoot/beats.mjs", "content": BEAT}, "deny")
t.pre("execCommand selectAll in a screencast script", "Write",
      {"file_path": "/tmp/p/screencast/run.mjs", "content": SELECT_ALL}, "deny")
t.pre("dblclick in a demo-video script", "Edit",
      {"file_path": "/tmp/p/demo-video/run.mjs", "old_string": "x", "new_string": DBLCLICK}, "deny")

# must deny, by content: any file that starts a screencast is a recorder
t.pre("a drag in a file that calls startScreencast", "Write",
      {"file_path": "/tmp/p/tools/run.mjs",
       "content": "await client.send('Page.startScreencast');\n" + DRAG}, "deny")

# must allow
t.pre("the escape on a slider drag", "Write",
      {"file_path": "/tmp/p/capture/slider.mjs",
       "content": "await page.%s(100, 500);\nawait page.%s; // drag: not-text\nawait page.%s(300, 500);\nawait page.%s;\n"
       % (MOVE, DOWN, MOVE, UP)}, "allow")
t.pre("a measurement Range that is never added to the Selection", "Write",
      {"file_path": "/tmp/p/capture/measure.mjs",
       "content": "const r = document.createRange(); r.selectNodeContents(el); const box = r.getBoundingClientRect();\n"},
      "allow")
t.pre("a double click in ordinary app code is not a recorder", "Write",
      {"file_path": "/tmp/p/src/components/Editor.tsx", "content": DBL + DBLCLICK}, "allow")
t.pre("a scroll-only recorder", "Write",
      {"file_path": "/tmp/p/capture/scroll.mjs",
       "content": "for (let y = 0; y < h; y += 40) { await page.evaluate((v) => window.scrollTo(0, v), y); }\n"}, "allow")
t.pre("vendored bundles are not scanned", "Write",
      {"file_path": "/tmp/p/video/node_modules/lib/index.js", "content": SELECT_TEXT}, "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/text_highlight.py", "content": SELECT_TEXT}, "allow")
t.pre("Bash is not this hook's tool", "Bash", {"command": "ls capture"}, "allow")

reason = t.pre("deny message names the escape", "Write",
               {"file_path": "/tmp/p/capture/demo.mjs", "content": DRAG}, "deny")
t.check("deny message names the drag escape", "drag: not-text" in reason)
t.check("deny message gives the line number", "line 2" in reason)

t.done()
