#!/usr/bin/env node
// Removes Python bytecode caches before npm packs the package. They hold the absolute path of the
// machine that compiled them and are never part of a release.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let removed = 0;
function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!e.isDirectory() || e.name === '.git' || e.name === 'node_modules') continue;
    const p = path.join(dir, e.name);
    if (e.name === '__pycache__') {
      fs.rmSync(p, { recursive: true, force: true });
      removed++;
    } else walk(p);
  }
}
walk(ROOT);
console.log(`clean: removed ${removed} __pycache__ folder(s)`);
