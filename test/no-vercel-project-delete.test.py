#!/usr/bin/env python3
"""Fixtures for no-vercel-project-delete.py. Each case runs the real hook with a real PreToolUse event.

Fixtures carry a '^' inside the key words, removed at run time by u(), so this file never holds a
deletion command in a form another guard would act on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402


def u(s):
    return s.replace("^", "")


t = T("no-vercel-project-delete")

# must deny
t.pre("the CLI rm subcommand in Bash", "Bash", {"command": u("vercel project^s rm my-app --yes")}, "deny")
t.pre("the singular CLI form in Bash", "Bash", {"command": u("vercel project^ rm my-app")}, "deny")
t.pre("curl DELETE against the project itself", "Bash",
      {"command": u('curl -X DELETE "https://api.vercel.com/v^9/projects/$PID" -H "Authorization: Bearer $T"')},
      "deny")
t.pre("fetch DELETE in a JS file", "Write",
      {"file_path": "/tmp/p/tools/cleanup.mjs",
       "content": u("await fetch(`https://api.vercel.com/v^9/projects/${p.id}`, { method: 'DELETE', headers });\n")},
      "deny")
t.pre("fetch DELETE split across lines", "Write",
      {"file_path": "/tmp/p/tools/cleanup.mjs",
       "content": u("await fetch(`https://api.vercel.com/v^9/projects/${id}`, {\n  method: 'DELETE',\n  headers,\n});\n")},
      "deny")
t.pre("a Python requests DELETE", "Edit",
      {"file_path": "/tmp/p/tools/cleanup.py", "old_string": "x",
       "new_string": u("requests.request('DELETE', f'https://api.vercel.com/v^9/projects/{pid}', headers=h)")},
      "deny")
t.pre("a shell script with the CLI rm subcommand", "Write",
      {"file_path": "/tmp/p/tools/prune.sh", "content": u("for p in $DEAD; do vercel project^s rm \"$p\"; done\n")},
      "deny")
t.pre("MultiEdit adding a deletion in the second edit", "MultiEdit",
      {"file_path": "/tmp/p/tools/prune.sh", "edits": [
          {"old_string": "a", "new_string": "echo start"},
          {"old_string": "b", "new_string": u("vercel project^s rm old-app")}]}, "deny")

# must allow
t.pre("a DELETE against an env var subresource", "Bash",
      {"command": u('curl -X DELETE "https://api.vercel.com/v^9/projects/$PID/env/$EID" -H "Authorization: Bearer $T"')},
      "allow")
t.pre("a DELETE against the git link subresource", "Write",
      {"file_path": "/tmp/p/tools/link.mjs",
       "content": u("await fetch(`https://api.vercel.com/v^9/projects/${id}/link`, { method: 'DELETE', headers });\n")},
      "allow")
t.pre("a GET of the project", "Bash",
      {"command": u('curl -s "https://api.vercel.com/v^9/projects/$PID" -H "Authorization: Bearer $T"')}, "allow")
t.pre("the command on a shell comment line", "Write",
      {"file_path": "/tmp/p/tools/notes.sh", "content": u("# never run: vercel project^s rm my-app\necho ok\n")},
      "allow")
t.pre("the command on a JS comment line", "Write",
      {"file_path": "/tmp/p/tools/notes.mjs", "content": u("// never call DELETE /v^9/projects/:id here\nexport {};\n")},
      "allow")
t.pre("listing projects", "Bash", {"command": "vercel projects ls"}, "allow")
t.pre("an ordinary command", "Bash", {"command": "npm run build"}, "allow")
t.pre("Read is never scanned", "Read", {"file_path": "/tmp/p/tools/cleanup.mjs"}, "allow")

reason = t.pre("deny message states the rule", "Bash", {"command": u("vercel project^s rm my-app")}, "deny")
t.check("message says deletion is by hand and subresources are allowed",
        "by hand" in reason and "subresource" in reason)

t.done()
