#!/usr/bin/env node
// guardhooks: install Claude Code hooks one at a time.
//
//   npx guardhooks list
//   npx guardhooks doc <hook>
//   npx guardhooks add <hook> [<hook> ...] [--config-dir DIR] [--python CMD]
//   npx guardhooks remove <hook> [<hook> ...] [--config-dir DIR]
//   npx guardhooks declare <hook> "<reason>" [--config-dir DIR]
//
// The config directory is --config-dir, else $CLAUDE_CONFIG_DIR, else ~/.claude.
// `add` copies the hook's script and the shared lib/ folder into <config>/hooks/guardhooks/ and
// writes one entry per event into <config>/settings.json. Every other setting is kept as it was.
// `remove` deletes those entries and the hook's script. When no GuardHooks entry is left, the
// hooks/guardhooks/ folder is deleted too.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = path.dirname(fileURLToPath(import.meta.url));
const HOOKS_SRC = path.join(SRC, 'hooks');
const MANIFESTS = path.join(SRC, 'manifests');
const INSTALL_SUBDIR = path.join('hooks', 'guardhooks');
const MARK = '/hooks/guardhooks/';

// ---------------------------------------------------------------------------------------------
// manifests
// ---------------------------------------------------------------------------------------------
export function loadManifests(dir = MANIFESTS) {
  const out = new Map();
  for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()) {
    const m = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    if (m.id !== f.replace(/\.json$/, '')) throw new Error(`manifest ${f} has id ${m.id}`);
    out.set(m.id, m);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------
// config dir and settings
// ---------------------------------------------------------------------------------------------
export function resolveConfigDir(flag, env = process.env) {
  if (flag) return path.resolve(flag.replace(/^~(?=$|\/)/, os.homedir()));
  if (env.CLAUDE_CONFIG_DIR) return path.resolve(env.CLAUDE_CONFIG_DIR);
  return path.join(os.homedir(), '.claude');
}

function readSettings(file) {
  if (!fs.existsSync(file)) return {};
  const raw = fs.readFileSync(file, 'utf8');
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch (e) {
    throw new Error(`${file} is not valid JSON, so it was left untouched: ${e.message}`);
  }
}

function writeSettings(file, settings) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.guardhooks-${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(settings, null, 2) + '\n');
  fs.renameSync(tmp, file);
}

const isOurs = (cmd, script) =>
  typeof cmd === 'string' && cmd.replace(/\\/g, '/').includes(MARK + (script || ''));

function stripScript(settings, script) {
  const hooks = settings.hooks || {};
  for (const event of Object.keys(hooks)) {
    const groups = Array.isArray(hooks[event]) ? hooks[event] : [];
    const kept = [];
    for (const g of groups) {
      const inner = (g.hooks || []).filter((h) => !isOurs(h.command, script));
      if (inner.length) kept.push({ ...g, hooks: inner });
    }
    if (kept.length) hooks[event] = kept;
    else delete hooks[event];
  }
  if (Object.keys(hooks).length) settings.hooks = hooks;
  else delete settings.hooks;
  return settings;
}

function anyOurs(settings) {
  for (const groups of Object.values(settings.hooks || {})) {
    for (const g of groups || []) for (const h of g.hooks || []) if (isOurs(h.command)) return true;
  }
  return false;
}

export function commandFor(python, scriptPath) {
  return `${python} -B "${scriptPath}"`;
}

// ---------------------------------------------------------------------------------------------
// add / remove
// ---------------------------------------------------------------------------------------------
function copyDir(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const e of fs.readdirSync(from, { withFileTypes: true })) {
    if (e.name === '__pycache__') continue;
    const a = path.join(from, e.name);
    const b = path.join(to, e.name);
    if (e.isDirectory()) copyDir(a, b);
    else fs.copyFileSync(a, b);
  }
}

export function add(ids, { configDir, python }) {
  const manifests = loadManifests();
  const unknown = ids.filter((id) => !manifests.has(id));
  if (unknown.length) throw new Error(`unknown hook: ${unknown.join(', ')}. Run "guardhooks list".`);
  const settingsFile = path.join(configDir, 'settings.json');
  const settings = readSettings(settingsFile);
  const dest = path.join(configDir, INSTALL_SUBDIR);
  copyDir(path.join(HOOKS_SRC, 'lib'), path.join(dest, 'lib'));
  const written = [];
  // Remove every old entry for these scripts first, so a re-add never duplicates an entry and a
  // script registered on two events keeps both entries.
  for (const id of ids) for (const h of manifests.get(id).hooks) stripScript(settings, h.script);
  for (const id of ids) {
    const m = manifests.get(id);
    for (const h of m.hooks) {
      const from = path.join(HOOKS_SRC, h.script);
      const to = path.join(dest, h.script);
      fs.copyFileSync(from, to);
      fs.chmodSync(to, 0o755);
      settings.hooks = settings.hooks || {};
      settings.hooks[h.event] = settings.hooks[h.event] || [];
      const entry = { type: 'command', command: commandFor(python, to) };
      if (h.timeout) entry.timeout = h.timeout;
      settings.hooks[h.event].push(h.matcher ? { matcher: h.matcher, hooks: [entry] } : { hooks: [entry] });
      written.push(`${h.event}${h.matcher ? ` (${h.matcher})` : ''}: ${h.script}`);
    }
  }
  writeSettings(settingsFile, settings);
  return { settingsFile, written };
}

export function remove(ids, { configDir }) {
  const manifests = loadManifests();
  const unknown = ids.filter((id) => !manifests.has(id));
  if (unknown.length) throw new Error(`unknown hook: ${unknown.join(', ')}. Run "guardhooks list".`);
  const settingsFile = path.join(configDir, 'settings.json');
  const settings = readSettings(settingsFile);
  const dest = path.join(configDir, INSTALL_SUBDIR);
  const removed = [];
  for (const id of ids) {
    for (const h of manifests.get(id).hooks) {
      stripScript(settings, h.script);
      fs.rmSync(path.join(dest, h.script), { force: true });
      removed.push(h.script);
    }
  }
  writeSettings(settingsFile, settings);
  if (!anyOurs(settings)) fs.rmSync(dest, { recursive: true, force: true });
  return { settingsFile, removed };
}

export function installed(configDir) {
  const settings = readSettings(path.join(configDir, 'settings.json'));
  const manifests = loadManifests();
  const on = new Set();
  for (const [id, m] of manifests) {
    const all = m.hooks.every((h) =>
      (settings.hooks?.[h.event] || []).some((g) => (g.hooks || []).some((x) => isOurs(x.command, h.script))));
    if (all) on.add(id);
  }
  return on;
}

// ---------------------------------------------------------------------------------------------
// declare: the named escape for the hooks whose docs offer one
// ---------------------------------------------------------------------------------------------
export function declare(id, reason, { configDir }) {
  const manifests = loadManifests();
  const m = manifests.get(id);
  if (!m) throw new Error(`unknown hook: ${id}`);
  if (!m.declare) throw new Error(`${id} has no declaration escape.`);
  if (!reason || reason.trim().split(/\s+/).length < 4) throw new Error('give the reason in a full sentence.');
  const dir = path.join(configDir, 'guardhooks', 'state', 'declared');
  fs.mkdirSync(dir, { recursive: true });
  const line = `${Date.now() / 1000}\tany\t${reason.replace(/\s+/g, ' ').trim()}\n`;
  fs.appendFileSync(path.join(dir, `${id}.tsv`), line);
  return path.join(dir, `${id}.tsv`);
}

// ---------------------------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------------------------
const HELP = `guardhooks: Claude Code hooks you install one at a time.

  guardhooks list                      every hook, what it blocks, and whether it is installed
  guardhooks doc <hook>                the hook's full description
  guardhooks add <hook> [<hook> ...]   install hooks into <config>/settings.json
  guardhooks remove <hook> [...]       uninstall hooks
  guardhooks declare <hook> "<reason>" record a two-hour exception for a hook that offers one

Options:
  --config-dir DIR   the Claude Code config directory. Default: $CLAUDE_CONFIG_DIR, else ~/.claude
  --python CMD       the Python 3 command written into settings.json. Default: python3

Each hook is a Python 3 script. Nothing else is installed.`;

function parse(argv) {
  const args = [];
  const opts = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--config-dir') opts.configDir = argv[++i];
    else if (a.startsWith('--config-dir=')) opts.configDir = a.slice(13);
    else if (a === '--python') opts.python = argv[++i];
    else if (a.startsWith('--python=')) opts.python = a.slice(9);
    else if (a === '-h' || a === '--help') opts.help = true;
    else args.push(a);
  }
  return { args, opts };
}

function wrap(text, width = 78, indent = '  ') {
  const words = String(text).split(/\s+/);
  const lines = [];
  let cur = '';
  for (const w of words) {
    if ((cur + ' ' + w).trim().length > width - indent.length) {
      lines.push(indent + cur.trim());
      cur = w;
    } else cur += ' ' + w;
  }
  if (cur.trim()) lines.push(indent + cur.trim());
  return lines.join('\n');
}

export function main(argv = process.argv.slice(2)) {
  const { args, opts } = parse(argv);
  const [cmd, ...rest] = args;
  if (!cmd || opts.help || cmd === 'help') {
    console.log(HELP);
    return 0;
  }
  const configDir = resolveConfigDir(opts.configDir);
  const python = opts.python || (process.platform === 'win32' ? 'python' : 'python3');
  const manifests = loadManifests();

  if (cmd === 'list') {
    const on = installed(configDir);
    console.log(`Config dir: ${configDir}\n`);
    for (const [id, m] of manifests) {
      const events = [...new Set(m.hooks.map((h) => h.event))].join(', ');
      console.log(`${on.has(id) ? '[x]' : '[ ]'} ${id}  (${events})`);
      console.log(wrap(m.summary, 78, '      '));
    }
    console.log(`\n${on.size} of ${manifests.size} installed. Install one with: npx guardhooks add <hook>`);
    return 0;
  }
  if (cmd === 'doc') {
    const m = manifests.get(rest[0]);
    if (!m) {
      console.error(`unknown hook: ${rest[0] || '(none)'}. Run "guardhooks list".`);
      return 1;
    }
    console.log(`${m.id}\n\n${wrap(m.doc, 78, '')}\n`);
    for (const h of m.hooks) console.log(`  ${h.event}${h.matcher ? ` on ${h.matcher}` : ''}: ${h.script}`);
    if (m.declare) console.log(`\n  Escape: npx guardhooks declare ${m.id} "<reason>" (lasts two hours).`);
    return 0;
  }
  if (cmd === 'add' || cmd === 'remove') {
    if (!rest.length) {
      console.error(`usage: guardhooks ${cmd} <hook> [<hook> ...]`);
      return 1;
    }
    try {
      if (cmd === 'add') {
        const r = add(rest, { configDir, python });
        console.log(`Wrote ${r.settingsFile}`);
        for (const w of r.written) console.log(`  added ${w}`);
        console.log('Restart Claude Code, or open /hooks, to load the change.');
      } else {
        const r = remove(rest, { configDir });
        console.log(`Wrote ${r.settingsFile}`);
        for (const w of r.removed) console.log(`  removed ${w}`);
      }
    } catch (e) {
      console.error(e.message);
      return 1;
    }
    return 0;
  }
  if (cmd === 'declare') {
    try {
      const file = declare(rest[0], rest.slice(1).join(' '), { configDir });
      console.log(`Recorded in ${file}. It expires in two hours.`);
    } catch (e) {
      console.error(e.message);
      return 1;
    }
    return 0;
  }
  console.error(`unknown command: ${cmd}\n\n${HELP}`);
  return 1;
}

const invoked = process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) process.exit(main());
