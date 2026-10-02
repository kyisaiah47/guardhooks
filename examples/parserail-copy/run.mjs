#!/usr/bin/env node
// Worked example: install no-noise and no-em-dash into a throwaway config dir, then send the
// installed hooks two Write events for a product FAQ page. The draft is denied. The live copy passes.
//
//   node examples/parserail-copy/run.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const cli = path.join(here, '..', '..', 'src', 'cli.mjs');
const config = fs.mkdtempSync(path.join(os.tmpdir(), 'guardhooks-example-'));

const add = spawnSync(process.execPath, [cli, 'add', 'no-noise', 'no-em-dash', '--config-dir', config], { encoding: 'utf8' });
if (add.status !== 0) {
  console.error(add.stderr);
  process.exit(1);
}
console.log(add.stdout.trim());

const settings = JSON.parse(fs.readFileSync(path.join(config, 'settings.json'), 'utf8'));
const commands = settings.hooks.PreToolUse.flatMap((g) => g.hooks.map((h) => h.command));

let ok = true;
for (const [name, want] of [['event-draft.json', 'deny'], ['event-live.json', 'allow']]) {
  const event = fs.readFileSync(path.join(here, name), 'utf8');
  const reasons = [];
  for (const command of commands) {
    const r = spawnSync('/bin/sh', ['-c', command], { input: event, encoding: 'utf8', env: { ...process.env, CLAUDE_CONFIG_DIR: config } });
    if (r.stdout.trim()) {
      const out = JSON.parse(r.stdout).hookSpecificOutput;
      if (out.permissionDecision === 'deny') {
        const hook = path.basename(command.split('"')[1], '.py');
        const findings = out.permissionDecisionReason.split('\n').filter((l) => l.startsWith('  - '));
        for (const f of findings) reasons.push(`${hook}: ${f.slice(4, 150)}`);
      }
    }
  }
  const got = reasons.length ? 'deny' : 'allow';
  ok = ok && got === want;
  console.log(`\n${name}: ${got} (expected ${want})`);
  for (const r of reasons) console.log(`  ${r.trim()}`);
}

fs.rmSync(config, { recursive: true, force: true });
process.exit(ok ? 0 : 1);
