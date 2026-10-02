#!/usr/bin/env python3
"""Fixtures for no-zoom-capture.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-zoom-capture")

BEAT_PLAYER = r"""
function startEngine(BEATS, opts) {
  const stage = document.getElementById('shot');
  const t0 = performance.now();
  let curIdx = -1;
  function apply(i) {
    const b = BEATS[i];
    stage.style.transition = 'none';
    stage.src = b.img;
    stage.style.transform = 'scale(1)';
    void stage.offsetWidth;
    stage.style.transition = 'transform ' + Math.max(300, b.end - b.start) + 'ms linear';
    const zoom = (b.zoomTo || 108) / 100;
    requestAnimationFrame(() => { stage.style.transform = 'scale(' + zoom + ')'; });
  }
  function tick() {
    const t = performance.now() - t0;
    const i = BEATS.findIndex((b) => t >= b.start && t < b.end);
    if (i !== -1 && i !== curIdx) { curIdx = i; apply(i); }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
"""

# must deny
t.pre("a beat player with a Ken Burns zoom", "Write",
      {"file_path": "/tmp/p/capture/pages/engine.js", "content": BEAT_PLAYER}, "deny")
t.pre("a keyframe punch-in on a capture stage", "Write",
      {"file_path": "/tmp/p/record/vertical.mjs",
       "content": "const css = `#shot{animation:punchIn 6s linear forwards}@keyframes punchIn{from{transform:scale(1)}to{transform:scale(1.15)}}`;"},
      "deny")
t.pre("a GSAP zoom tween in a recorder", "Write",
      {"file_path": "/tmp/p/shoot/demo.mjs",
       "content": "await page.evaluate(() => { gsap.to('#shot', { duration: 4, scale: 1.12 }); });"}, "deny")
t.pre("an animate() scale tween in a file that records video", "Write",
      {"file_path": "/tmp/p/tools/run.mjs",
       "content": "const ctx = await browser.newContext({ recordVideo: { dir: 'out' } });\n"
                  "el.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.1)' }], 4000);"}, "deny")

# must allow
t.pre("a full-width scroll recorder with no scale", "Write",
      {"file_path": "/tmp/p/capture/scroll.mjs",
       "content": "const h = await page.evaluate(() => document.body.scrollHeight);\n"
                  "for (let y = 0; y < h; y += 40) { await page.evaluate((v) => window.scrollTo(0, v), y); }\n"},
      "allow")
t.pre("a static scale(1) reset with no animation driver", "Write",
      {"file_path": "/tmp/p/capture/reset.mjs", "content": "stage.style.transform = 'scale(1)';\nstage.src = nextImg;\n"},
      "allow")
t.pre("a button press scale in app code", "Write",
      {"file_path": "/tmp/p/src/components/Button.tsx",
       "content": "export const Button = () => (\n  <button style={{ transition: 'transform .15s', transform: 'scale(1)' }}\n"
                  "    onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.97)'; }} />\n);\n"},
      "allow")
t.pre("a file about the ban", "Write",
      {"file_path": "/tmp/p/capture/pages/engine.js", "content": "// see no-zoom-capture\n" + BEAT_PLAYER}, "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/zoom_capture.py", "content": BEAT_PLAYER}, "allow")

reason = t.pre("deny message says to remove the scale", "Write",
               {"file_path": "/tmp/p/capture/pages/engine.js", "content": BEAT_PLAYER}, "deny")
t.check("deny message says remove it entirely", "Remove the scale entirely" in reason)

t.done()
