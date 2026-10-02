#!/usr/bin/env python3
"""Fixtures for no-heading-break.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-heading-break")

FIXED_GENERATOR = r"""
const headlineText = (h) => {
  const parts = Array.isArray(h) ? h : [h];
  const joined = parts.map((x) => String(x == null ? "" : x)).join(" ");
  if (/<br\s*\/?>/i.test(joined) || /\n/.test(joined)) {
    throw new Error("a headline may not carry a hard line break");
  }
  return joined.replace(/\s+/g, " ").trim();
};
function render(s) {
  return `<h1>${headlineText(s.headline)}</h1>`;
}
"""

# must deny
t.pre("a headline array joined with <br> inside an h1", "Write",
      {"file_path": "/tmp/p/tools/card.mjs", "content": '<h1>${s.headline.join("<br>")}</h1>'}, "deny")
t.pre("a title array joined with <br> in a new generator", "Write",
      {"file_path": "/tmp/p/tools/fact-card.mjs",
       "content": 'function render(s) { return `<h1>${s.title.join("<br>")}</h1>`; }'}, "deny")
t.pre("a headline string with a hand-placed break", "Write",
      {"file_path": "/tmp/p/tools/spec.mjs",
       "content": 'const spec = { headline: "1,210 documents<br>scored against 3 vendors" };'}, "deny")
t.pre("an h1 literal with a hard break", "Write",
      {"file_path": "/tmp/p/tools/panel.mjs", "content": "return `<h1>1,210 documents<br>scored</h1>`;"}, "deny")
t.pre("Edit adds a <br/> to a heading", "Edit",
      {"file_path": "/tmp/p/src/Hero.tsx", "old_string": "x",
       "new_string": "const heading = 'Ship faster<br/>with fewer tools';"}, "deny")

# must allow
t.pre("a generator that joins to one string and refuses breaks", "Write",
      {"file_path": "/tmp/p/tools/card.mjs", "content": FIXED_GENERATOR}, "allow")
t.pre("a headline passed as one escaped string", "Write",
      {"file_path": "/tmp/p/tools/release.mjs", "content": "return `<h1>${esc(cfg.headline)}</h1>`;"}, "allow")
t.pre("a table cell joined with <br>", "Write",
      {"file_path": "/tmp/p/tools/report.mjs",
       "content": "rows.push(`<tr><td>${d.answers.map(([a, n]) => `${a} (${n})`).join('<br>')}</td></tr>`);"},
      "allow")
t.pre("a paragraph joined with <br>", "Write",
      {"file_path": "/tmp/p/tools/digest.mjs", "content": "`<p>${lines.map((l) => esc(l)).join('<br>')}</p>`"}, "allow")
t.pre("a footer address join", "Write",
      {"file_path": "/tmp/p/tools/footer.mjs", "content": 'const footRight = (s) => (s || "").split("\\n").join("<br>");'},
      "allow")
t.pre("vendored code is not scanned", "Write",
      {"file_path": "/tmp/p/node_modules/x/index.js", "content": '<h1>${s.headline.join("<br>")}</h1>'}, "allow")
t.pre("the ban's own library", "Write",
      {"file_path": "/tmp/p/hooks/lib/heading_break.py", "content": '<h1>a<br>b</h1>'}, "allow")

reason = t.pre("deny message names text-wrap", "Write",
               {"file_path": "/tmp/p/tools/panel.mjs", "content": "<h1>a<br>b</h1>"}, "deny")
t.check("deny message suggests text-wrap: balance", "text-wrap: balance" in reason)

t.done()
