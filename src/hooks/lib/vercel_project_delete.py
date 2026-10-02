"""The one place the Vercel project deletion pattern is defined. Read by no-vercel-project-delete.py.

It matches the `rm` subcommand of the Vercel CLI's project command, and a REST DELETE against a
project itself under /vN/projects/. A DELETE against a project subresource (env, domains, alias,
link) stays allowed, because those are ordinary maintenance. Comment lines are skipped.
"""
import re

CLI_RM = re.compile(r'\bvercel\s+projects?\s+rm\b')
API_PATH = re.compile(r'/v\d+/projects/')
HAS_DELETE = re.compile(r'\bDELETE\b')

_INTERP = [
    re.compile(r'\$\{[^}]*\}'),
    re.compile(r'\$\([^)]*\)'),
    re.compile(r'\$\{?[A-Za-z_][A-Za-z0-9_]*\}?'),
    re.compile(r'\{[A-Za-z_][A-Za-z0-9_.\[\]\'"]*\}'),
]

BLOCK_TEXT = """Nothing may delete a Vercel project automatically. Deleting a project is a decision a
person makes by hand.

A project without a custom domain is not abandoned. A project created today has no custom domain
yet. No age, traffic or name rule makes automated deletion safe.
A project with no traffic costs nothing to keep.

Do this instead: report the project in your output and leave it in place.

Still allowed: a DELETE against a project subresource, such as the env, domains, alias or link
endpoints under a project. Only a DELETE against the project itself is refused.

To mention the command on purpose, put it on a comment line. Comment lines are not scanned."""


def _literal_tail(tail):
    for rx in _INTERP:
        tail = rx.sub('', tail)
    return tail.replace('%s', '').replace('%d', '')


def _targets_project_itself(tail):
    m = re.search(r'["\'`\s)>;,]', tail)
    url = _literal_tail(tail[:m.start()] if m else tail)
    return '/' not in url.split('?')[0]


def _mask_comments(lines, is_shell):
    mask = [False] * len(lines)
    in_block = False
    for i, raw in enumerate(lines):
        t = raw.strip()
        if in_block:
            mask[i] = True
            if '*/' in t:
                in_block = False
            continue
        if is_shell and t.startswith('#'):
            mask[i] = True
            continue
        if t.startswith('//') or t.startswith('*'):
            mask[i] = True
            continue
        if t.startswith('/*'):
            mask[i] = True
            if '*/' not in t:
                in_block = True
    return mask


def _statement_at(lines, i):
    depth = 0
    out = ''
    for k in range(i, min(i + 5, len(lines))):
        line = lines[k]
        out += line + '\n'
        for c in line:
            if c in '({[':
                depth += 1
            elif c in ')}]':
                depth -= 1
        if not (depth > 0 or line.rstrip().endswith(('\\', ','))):
            break
    return out


def violations(text, is_shell=False):
    """Return [(lineno, kind, line)] for every place this text can delete a Vercel project."""
    if not text:
        return []
    if '/projects/' not in text and 'project rm' not in text and 'projects rm' not in text:
        return []
    lines = text.split('\n')
    mask = _mask_comments(lines, is_shell)
    hits = []
    for i, line in enumerate(lines):
        if mask[i]:
            continue
        if CLI_RM.search(line):
            hits.append((i + 1, 'vercel CLI', line.strip()[:160]))
            continue
        for m in API_PATH.finditer(line):
            tail = line[m.end():]
            if not _targets_project_itself(tail):
                continue
            scope = _statement_at(lines, i)
            b = i - 1
            while b >= 0 and b >= i - 3 and lines[b].rstrip().endswith('\\'):
                scope = lines[b] + '\n' + scope
                b -= 1
            if HAS_DELETE.search(scope):
                hits.append((i + 1, 'REST DELETE', line.strip()[:160]))
                break
    return hits
