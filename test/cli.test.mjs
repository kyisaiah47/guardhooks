// Tests for the guardhooks CLI: add, remove, list, doc and declare, against temporary config dirs.
// The proof case: `guardhooks add no-noise` writes a valid settings entry, and the installed hook,
// run with the exact command written into settings.json, denies a fixture input.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CLI = path.join(ROOT, 'src', 'cli.mjs');
const MANIFESTS = path.join(ROOT, 'src', 'manifests');
const EVENTS = new Set(['PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop', 'SubagentStop', 'SubagentStart',
  'SessionStart', 'SessionEnd', 'Notification', 'PreCompact', 'InstructionsLoaded']);

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'guardhooks-cli-'));
const cli = (args, env = {}) =>
  spawnSync(process.execPath, [CLI, ...args], { encoding: 'utf8', env: { ...process.env, ...env } });
const readSettings = (dir) => JSON.parse(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8'));
const manifests = () =>
  fs.readdirSync(MANIFESTS).filter((f) => f.endsWith('.json')).sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(MANIFESTS, f), 'utf8')));

// Run a settings.json command the way Claude Code does: through a shell, with the event on stdin.
function runCommand(command, event, env = {}) {
  return spawnSync('/bin/sh', ['-c', command], {
    input: JSON.stringify(event),
    encoding: 'utf8',
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', ...env },
  });
}

function ourCommands(settings) {
  const out = [];
  for (const [event, groups] of Object.entries(settings.hooks || {})) {
    for (const g of groups) for (const h of g.hooks || []) {
      if (String(h.command).includes('/hooks/guardhooks/')) out.push({ event, matcher: g.matcher, ...h });
    }
  }
  return out;
}

test('every manifest is complete and points at real files', () => {
  const all = manifests();
  assert.ok(all.length >= 2, 'at least two hooks ship');
  const scripts = new Set();
  for (const m of all) {
    assert.match(m.id, /^[a-z0-9-]+$/, `${m.id}: id is kebab-case`);
    assert.ok(m.summary && m.summary.length > 20, `${m.id}: summary`);
    assert.ok(m.doc && m.doc.split(/[.!?](\s|$)/).length > 3, `${m.id}: doc is a paragraph`);
    assert.ok(!/[\u2014\u2013]/.test(m.summary + m.doc), `${m.id}: no em or en dash in docs`);
    assert.ok(Array.isArray(m.hooks) && m.hooks.length > 0, `${m.id}: hooks`);
    for (const h of m.hooks) {
      assert.ok(EVENTS.has(h.event), `${m.id}: event ${h.event}`);
      assert.ok(fs.existsSync(path.join(ROOT, 'src', 'hooks', h.script)), `${m.id}: script ${h.script} exists`);
      assert.ok(!scripts.has(h.script), `${m.id}: script ${h.script} belongs to one hook only`);
      scripts.add(h.script);
      if (['PreToolUse', 'PostToolUse'].includes(h.event)) assert.ok(h.matcher, `${m.id}: tool event has a matcher`);
    }
    assert.ok(fs.existsSync(path.join(ROOT, 'test', `${m.id}.test.py`)), `${m.id}: has test/${m.id}.test.py`);
  }
});

test('README hook table and reference match the manifests', () => {
  const r = spawnSync(process.execPath, [path.join(ROOT, 'scripts', 'readme.mjs'), '--check'], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stdout + r.stderr);
});

test('README lists every hook', () => {
  const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8');
  for (const m of manifests()) assert.ok(readme.includes(`\`${m.id}\``), `README mentions ${m.id}`);
});

test('add no-noise writes a valid settings entry and the installed hook denies a fixture', () => {
  const dir = tmp();
  const r = cli(['add', 'no-noise', '--config-dir', dir]);
  assert.equal(r.status, 0, r.stderr);
  const settings = readSettings(dir);
  const ours = ourCommands(settings);
  const manifest = JSON.parse(fs.readFileSync(path.join(MANIFESTS, 'no-noise.json'), 'utf8'));
  assert.equal(ours.length, manifest.hooks.length, 'one entry per manifest event');
  const pre = ours.find((h) => h.event === 'PreToolUse');
  assert.ok(pre, 'a PreToolUse entry');
  assert.equal(pre.type, 'command');
  assert.equal(pre.matcher, manifest.hooks[0].matcher);
  assert.ok(pre.command.includes(path.join(dir, 'hooks', 'guardhooks', 'no-noise.py')), 'absolute path into the chosen config dir');
  assert.ok(fs.existsSync(path.join(dir, 'hooks', 'guardhooks', 'lib', 'guardhooks_core.py')), 'lib copied');

  const fixture = {
    hook_event_name: 'PreToolUse',
    tool_name: 'Write',
    tool_input: { file_path: '/tmp/p/landing/hero.md', content: 'Say goodbye to manual data entry. Our powerful parser seamlessly handles every invoice.' },
  };
  const out = runCommand(pre.command, fixture, { CLAUDE_CONFIG_DIR: dir });
  assert.equal(out.status, 0, out.stderr);
  const decision = JSON.parse(out.stdout).hookSpecificOutput;
  assert.equal(decision.permissionDecision, 'deny');
  assert.ok(decision.permissionDecisionReason.length > 40, 'the reason states the rule');

  const clean = runCommand(pre.command, {
    ...fixture,
    tool_input: { file_path: '/tmp/p/landing/hero.md', content: 'A call is charged only when it succeeds, so a failed call costs nothing.' },
  }, { CLAUDE_CONFIG_DIR: dir });
  assert.equal(clean.status, 0, clean.stderr);
  assert.equal(clean.stdout.trim(), '', 'clean copy is allowed');
});

test('add is idempotent and keeps every other setting', () => {
  const dir = tmp();
  const before = {
    model: 'example-model',
    permissions: { allow: ['Bash(ls:*)'] },
    hooks: { PreToolUse: [{ matcher: 'Bash', hooks: [{ type: 'command', command: 'echo mine' }] }] },
  };
  fs.writeFileSync(path.join(dir, 'settings.json'), JSON.stringify(before));
  assert.equal(cli(['add', 'no-em-dash', '--config-dir', dir]).status, 0);
  assert.equal(cli(['add', 'no-em-dash', '--config-dir', dir]).status, 0);
  const s = readSettings(dir);
  assert.equal(s.model, 'example-model');
  assert.deepEqual(s.permissions, before.permissions);
  assert.equal(ourCommands(s).length, 1, 'still one entry after two adds');
  assert.ok(s.hooks.PreToolUse.some((g) => g.hooks.some((h) => h.command === 'echo mine')), 'user hook kept');
});

test('remove deletes the entries and the install folder, and keeps user hooks', () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'settings.json'), JSON.stringify({
    hooks: { Stop: [{ hooks: [{ type: 'command', command: 'echo stop' }] }] },
  }));
  assert.equal(cli(['add', 'no-em-dash', 'no-em-dash-stop', '--config-dir', dir]).status, 0);
  assert.equal(ourCommands(readSettings(dir)).length, 2);
  assert.equal(cli(['remove', 'no-em-dash', '--config-dir', dir]).status, 0);
  let s = readSettings(dir);
  assert.equal(ourCommands(s).length, 1);
  assert.ok(!fs.existsSync(path.join(dir, 'hooks', 'guardhooks', 'no-em-dash.py')));
  assert.ok(fs.existsSync(path.join(dir, 'hooks', 'guardhooks', 'no-em-dash-stop.py')));
  assert.equal(cli(['remove', 'no-em-dash-stop', '--config-dir', dir]).status, 0);
  s = readSettings(dir);
  assert.equal(ourCommands(s).length, 0);
  assert.ok(!fs.existsSync(path.join(dir, 'hooks', 'guardhooks')), 'folder removed with the last hook');
  assert.ok(s.hooks.Stop.some((g) => g.hooks.some((h) => h.command === 'echo stop')), 'user Stop hook kept');
  assert.equal(s.hooks.PreToolUse, undefined, 'empty event arrays are dropped');
});

test('CLAUDE_CONFIG_DIR is used when no flag is given', () => {
  const dir = tmp();
  const r = cli(['add', 'no-em-dash'], { CLAUDE_CONFIG_DIR: dir });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(ourCommands(readSettings(dir)).length, 1);
  const list = cli(['list'], { CLAUDE_CONFIG_DIR: dir });
  assert.equal(list.status, 0);
  assert.match(list.stdout, /\[x\] no-em-dash\s/);
  assert.match(list.stdout, /\[ \] no-em-dash-stop/);
});

test('unknown hooks and broken settings fail without writing', () => {
  const dir = tmp();
  assert.equal(cli(['add', 'no-such-hook', '--config-dir', dir]).status, 1);
  assert.ok(!fs.existsSync(path.join(dir, 'settings.json')));
  fs.writeFileSync(path.join(dir, 'settings.json'), '{ not json');
  const r = cli(['add', 'no-em-dash', '--config-dir', dir]);
  assert.equal(r.status, 1);
  assert.equal(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8'), '{ not json');
});

test('doc prints the paragraph for a hook', () => {
  const r = cli(['doc', 'no-em-dash']);
  assert.equal(r.status, 0);
  assert.match(r.stdout, /PreToolUse/);
  assert.match(r.stdout, /blockquote/);
});

test('declare works only for hooks that offer the escape', () => {
  const dir = tmp();
  const withEscape = manifests().find((m) => m.declare);
  const without = manifests().find((m) => !m.declare);
  assert.equal(cli(['declare', without.id, 'this is a full sentence reason', '--config-dir', dir]).status, 1);
  if (withEscape) {
    assert.equal(cli(['declare', withEscape.id, 'short', '--config-dir', dir]).status, 1, 'a one-word reason is refused');
    const r = cli(['declare', withEscape.id, 'the quoted figure comes from a pasted image', '--config-dir', dir]);
    assert.equal(r.status, 0, r.stderr);
    const file = path.join(dir, 'guardhooks', 'state', 'declared', `${withEscape.id}.tsv`);
    assert.match(fs.readFileSync(file, 'utf8'), /pasted image/);
  }
});

test('every hook installs together and runs from its installed location', () => {
  const dir = tmp();
  const ids = manifests().map((m) => m.id);
  const r = cli(['add', ...ids, '--config-dir', dir]);
  assert.equal(r.status, 0, r.stderr);
  const ours = ourCommands(readSettings(dir));
  assert.equal(ours.length, manifests().reduce((n, m) => n + m.hooks.length, 0));
  const work = tmp();
  const transcript = path.join(work, 't.jsonl');
  fs.writeFileSync(transcript, [
    JSON.stringify({ type: 'user', message: { role: 'user', content: 'list the files' } }),
    JSON.stringify({ type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: 'There are three files in the folder.' }] } }),
  ].join('\n') + '\n');
  for (const h of ours) {
    const event = {
      PreToolUse: { hook_event_name: 'PreToolUse', session_id: 'smoke', tool_name: 'Read', tool_input: { file_path: path.join(work, 'notes.txt') } },
      PostToolUse: { hook_event_name: 'PostToolUse', session_id: 'smoke', tool_name: 'Read', tool_input: { file_path: path.join(work, 'notes.txt') }, tool_response: {} },
      UserPromptSubmit: { hook_event_name: 'UserPromptSubmit', session_id: 'smoke', prompt: 'list the files', transcript_path: transcript },
      Stop: { hook_event_name: 'Stop', session_id: 'smoke', transcript_path: transcript, stop_hook_active: false },
    }[h.event] || { hook_event_name: h.event, session_id: 'smoke', transcript_path: transcript };
    const out = runCommand(h.command, event, { CLAUDE_CONFIG_DIR: dir });
    assert.equal(out.status, 0, `${h.command} exited ${out.status}: ${out.stderr}`);
    if (out.stdout.trim()) {
      const parsed = JSON.parse(out.stdout);
      assert.notEqual(parsed?.hookSpecificOutput?.permissionDecision, 'deny', `${h.command} denied a plain read`);
    }
  }
  assert.equal(cli(['remove', ...ids, '--config-dir', dir]).status, 0);
  assert.equal(ourCommands(readSettings(dir)).length, 0);
  assert.ok(!fs.existsSync(path.join(dir, 'hooks', 'guardhooks')));
});

test('the worked example denies the draft and allows the live copy', () => {
  const r = spawnSync(process.execPath, [path.join(ROOT, 'examples', 'parserail-copy', 'run.mjs')], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /event-draft\.json: deny/);
  assert.match(r.stdout, /event-live\.json: allow/);
});

test('settings.example.json matches what add writes', () => {
  const dir = tmp();
  assert.equal(cli(['add', 'no-noise', 'no-noise-stop', 'no-em-dash', '--config-dir', dir]).status, 0);
  const written = fs.readFileSync(path.join(dir, 'settings.json'), 'utf8').split(dir).join('/home/you/.claude');
  const example = fs.readFileSync(path.join(ROOT, 'examples', 'settings.example.json'), 'utf8');
  assert.deepEqual(JSON.parse(example), JSON.parse(written));
});
