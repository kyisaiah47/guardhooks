#!/usr/bin/env python3
"""Fixtures for no-retro-rerender.py. Each case runs the real hook with a real PreToolUse event.

Fixtures carry a '^' inside the key verbs, removed at run time by u(), so this file never holds a
backfill line in a form another guard would act on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402


def u(s):
    return s.replace("^", "")


t = T("no-retro-rerender")

# must deny: a cleared asset field feeding the generator, a backfill loop, a redraw aimed at a
# newer style, and a backfill script
t.pre("a cleared asset field feeding the next sync", "Write",
      {"file_path": "/tmp/p/x.mjs",
       "content": u("// clear img so the generator draws it\nr.img = null; // the next^ sync will re-^request it\n")},
      "deny")
t.pre("a backfill loop over existing rows", "Write",
      {"file_path": "/tmp/p/y.mjs",
       "content": u("for (const row of existing) await re^generateCover(row); // back^fill all existing covers\n")},
      "deny")
t.pre("a tile pass aimed at a newer register", "Write",
      {"file_path": "/tmp/p/z.mjs", "content": u("// re-^render every old tile to match the new register\n")},
      "deny")
t.pre("a backfill script in Bash", "Bash",
      {"command": u("node scripts/back^fill-all-existing-covers.mjs --re^generate")}, "deny")
t.pre("Edit adding a card pass aimed at the house look", "Edit",
      {"file_path": "/tmp/p/a.py", "old_string": "x",
       "new_string": u("re^render(asset)  # re^render the old cards to match the house style")}, "deny")
t.pre("MultiEdit adding a backfill in the second edit", "MultiEdit",
      {"file_path": "/tmp/p/a.mjs", "edits": [
          {"old_string": "a", "new_string": "const n = 1;"},
          {"old_string": "b", "new_string": u("await back^fillAll(rows); // re^draw every existing image")}]},
      "deny")

# must allow: first asset for a row, retire in place, repoint, ordinary commands, the ban's own files
t.pre("generating the first picture for a row", "Write",
      {"file_path": "/tmp/p/a.mjs",
       "content": "if (!row.img) row.img = await requestImage(spec); // first picture for this row\n"}, "allow")
t.pre("retiring in place", "Write",
      {"file_path": "/tmp/p/b.mjs", "content": "r.plate = true; // retired in place, nothing draws it again\n"},
      "allow")
t.pre("repointing at a file that already exists", "Write",
      {"file_path": "/tmp/p/c.mjs",
       "content": "const found = candidates.find(isTransparent); r.img = found; // repoint at an existing file\n"},
      "allow")
t.pre("an ordinary build command", "Bash", {"command": "node scripts/build-index.mjs --dry"}, "allow")
t.pre("a write to the ban's own pattern list", "Write",
      {"file_path": "/tmp/p/hooks/lib/retro_rerender_patterns.json",
       "content": u("re^generate all existing images to match the new register")}, "allow")
t.pre("a doc quoting a banned line in backticks", "Write",
      {"file_path": "/tmp/p/docs/assets.md",
       "content": u("Never write `back^fill all existing covers` in a sync job.\n")}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": "/tmp/p/y.mjs"}, "allow")

reason = t.pre("deny message states the rule and the alternative", "Write",
               {"file_path": "/tmp/p/z.mjs", "content": u("// re-^render every old tile to match the new register\n")},
               "deny")
t.check("message names retire in place", "retire the old asset in place" in reason)

t.done()
