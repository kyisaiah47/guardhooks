#!/usr/bin/env node
// Runs every test file: test/*.test.py with python3 and test/*.test.mjs with node.
// Exits 1 when any file fails, and when no test file is found at all.
import { readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const only = process.argv.slice(2);
const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');

const files = readdirSync(here)
  .filter((f) => f.endsWith('.test.py') || f.endsWith('.test.mjs'))
  .filter((f) => only.length === 0 || only.some((o) => f.startsWith(o)))
  .sort();

if (files.length === 0) {
  console.error('no test files found');
  process.exit(1);
}

const failed = [];
for (const f of files) {
  const cmd = f.endsWith('.py') ? python : process.execPath;
  const r = spawnSync(cmd, [join(here, f)], {
    stdio: 'inherit',
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  });
  if (r.status !== 0) failed.push(f);
}

console.log(`\n${files.length - failed.length} of ${files.length} test files passed.`);
if (failed.length) {
  console.log('Failed:\n  ' + failed.join('\n  '));
  process.exit(1);
}
