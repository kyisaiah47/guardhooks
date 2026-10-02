#!/usr/bin/env python3
"""Fixtures for mobile-screenshot-guard.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("mobile-screenshot-guard")

PLAYWRIGHT_PHONE = (
    "node -e \"const { chromium } = require('playwright');(async () => {"
    "const b = await chromium.launch();"
    "const p = await b.newPage({ viewport: { width: 390, height: 844 } });"
    "await p.goto('https://example.com');"
    "await p.screenshot({ path: 'home.png' });await b.close();})();\"")

PHONE_CONST = """
const PHONE = { w: 430, h: 932 };
await page.setViewport({ width: PHONE.w, height: PHONE.h });
await page.goto(url);
await page.screenshot({ path: out });
"""
DESKTOP_CONST = """
const DESKTOP = { w: 1280, h: 900 };
await page.setViewport({ width: DESKTOP.w, height: DESKTOP.h });
await page.goto(url);
await page.screenshot({ path: out });
"""
UA_MOBILE = ("await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X)');\n"
             "await page.setViewport({ width: 1280, height: 800, isMobile: true });\n"
             "await page.goto(url);\nawait page.screenshot({ path: out });\n")
LOCAL_CARD = """
const m = await b.newPage();
await m.setViewport({ width: 390, height: 488, deviceScaleFactor: 3 });
await m.goto('file://' + tmp, { waitUntil: 'networkidle0' });
await m.screenshot({ path: out });
"""
THIRD_PARTY_FORM = """
const PHONE_VP = { width: 390, height: 844, isMobile: true };  // phone-viewport: third-party form
await page.setViewport(PHONE_VP);
await page.goto('https://forms.example.org/profile');
await page.screenshot({ path: p });
"""

# must deny
t.pre("a Playwright one-off at a 390 viewport against a live site", "Bash", {"command": PLAYWRIGHT_PHONE}, "deny")
t.pre("the Playwright CLI at a phone viewport size", "Bash",
      {"command": "npx playwright screenshot --viewport-size=390,844 https://example.com home.png"}, "deny")
t.pre("the Playwright CLI with a phone device", "Bash",
      {"command": "npx playwright screenshot --device='iPhone 13' https://example.com home.png"}, "deny")
t.pre("headless Chrome at a phone window size", "Bash",
      {"command": "chrome --headless --screenshot=out.png --window-size=390,844 https://example.com"}, "deny")
t.pre("a script with a phone frame constant", "Write", {"file_path": "/tmp/p/tools/shoot.mjs", "content": PHONE_CONST}, "deny")
t.pre("a script with isMobile and a phone user agent", "Write",
      {"file_path": "/tmp/p/tools/shoot.mjs", "content": UA_MOBILE}, "deny")
t.pre("a Playwright device descriptor", "Bash",
      {"command": "node -e \"const {chromium, devices} = require('playwright');(async()=>{const b=await chromium.launch();"
                  "const c=await b.newContext({...devices['iPhone 15']});const p=await c.newPage();"
                  "await p.goto('https://example.com');await p.screenshot({path:'x.png'});})()\""}, "deny")

# an Edit is judged on the file as it will be after the edit
with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
    fh.write(DESKTOP_CONST)
    on_disk = fh.name
t.pre("Edit that narrows a desktop script to phone width", "Edit",
      {"file_path": on_disk, "old_string": "await page.setViewport({ width: DESKTOP.w, height: DESKTOP.h });",
       "new_string": "await page.setViewport({ width: 390, height: 844 });"}, "deny")
t.pre("Edit whose new text adds no phone width is not refused", "Edit",
      {"file_path": on_disk, "old_string": "w: 1280", "new_string": "w: 1440"}, "allow")
with open(on_disk, "w") as fh:
    fh.write(PHONE_CONST + "\nconst OTHER = { width: 480 };\n")
t.pre("Edit that moves one phone width to desktop while others remain", "Edit",
      {"file_path": on_disk, "old_string": "w: 430", "new_string": "w: 1280"}, "allow")
os.unlink(on_disk)

# must allow
t.pre("the same capture at desktop width", "Write", {"file_path": "/tmp/p/tools/shoot.mjs", "content": DESKTOP_CONST}, "allow")
t.pre("the Playwright CLI at desktop width", "Bash",
      {"command": "npx playwright screenshot --viewport-size=1440,900 https://example.com home.png"}, "allow")
t.pre("a local file render at phone scale", "Write", {"file_path": "/tmp/p/tools/card.mjs", "content": LOCAL_CARD}, "allow")
t.pre("a line carrying the third-party-form escape", "Write",
      {"file_path": "/tmp/p/tools/profile.mjs", "content": THIRD_PARTY_FORM}, "allow")
t.pre("layout QA in an e2e folder", "Write", {"file_path": "/tmp/p/e2e/mobile-layout.mjs", "content": PHONE_CONST}, "allow")
t.pre("layout QA in a .spec file", "Write", {"file_path": "/tmp/p/src/nav.spec.ts", "content": PHONE_CONST}, "allow")
t.pre("layout QA run from a tests folder", "Bash", {"command": "node ./tests/phone-sweep.mjs --vw 390"}, "allow")
t.pre("opening an existing screenshot", "Bash", {"command": "open /tmp/p/home.png"}, "allow")
t.pre("ordinary Bash with no screenshot", "Bash", {"command": "git status && npm test"}, "allow")
t.pre("a phone viewport with no capture", "Write",
      {"file_path": "/tmp/p/tools/check.mjs",
       "content": "await page.setViewport({ width: 390, height: 844 });\nawait page.goto(url);\nconst h = await page.title();\n"},
      "allow")

reason = t.pre("deny message names the desktop width", "Bash", {"command": PLAYWRIGHT_PHONE}, "deny")
t.check("deny message names 1280 CSS px", "1280 CSS px" in reason)
t.check("deny message names the escape", "phone-viewport: third-party form" in reason)

t.done()
