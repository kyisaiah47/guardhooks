// Tests for scripts/scrub-gate.mjs. Every banned value is assembled from fragments at runtime, so
// this file never carries one and the gate can scan it like any other file.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const GATE = path.join(ROOT, 'scripts', 'scrub-gate.mjs');
const run = (dir) => spawnSync(process.execPath, [GATE, dir], { encoding: 'utf8' });
const j = (...parts) => parts.join('');

function dirWith(content, name = 'file.txt') {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'guardhooks-scrub-'));
  fs.writeFileSync(path.join(dir, name), content);
  return dir;
}

test('a clean tree passes', () => {
  const r = run(dirWith('A plain sentence about hooks. Run npx guardhooks list.\n'));
  assert.equal(r.status, 0, r.stderr);
});

const CASES = [
  ['personal email', j('kyisa', 'iah47', '@', 'gmail.com')],
  ['personal email', j('someone', '@', 'gmail.com')],
  ['personal email', j('fetch', 'due', '@', 'gmail.com')],
  ['local home path', j('/Us', 'ers/', 'ad', 'min/projects')],
  ['local home path', j('/Us', 'ers/', 'jane/code')],
  ['personal name', j('Isa', 'iah said so')],
  ['internal name', j('Compound', 'Labs/tools')],
  ['internal name', j('compound', '-ops/lib')],
  ['internal id', j('xowekq', 'dsttxwbhfxvusa')],
  ['internal id', j('acct', '_1T', 'abc')],
  ['Stripe account id', j('acc', 't_', 'Zq8kP2mVx7LwR4nB')],
  ['internal tool', j('compound', '-secret KEY')],
  ['internal tool', j('compound', '-vault get')],
  ['account handle', j('@kyisa', 'iah47 on X')],
  ['account DID', j('did:', 'plc:', 'abcdefgh12345678')],
  ['key shape', j('sk-', 'ant-', 'a'.repeat(24))],
  ['key shape', j('gh', 'p_', 'A'.repeat(36))],
  ['key shape', j('AK', 'IA', 'ABCDEFGHIJKLMNOP')],
  ['key shape', j('-----BEG', 'IN RSA PRIVATE KEY-----')],
  ['dated incident', j('On 20', '26-', '09-04 the user said')],
  ['bot-detection bypass', j('puppeteer-extra-plugin-', 'stealth')],
  ['bot-detection bypass', j('2', 'captcha')],
];

for (const [rule, text] of CASES) {
  test(`fails closed on ${rule}`, () => {
    const r = run(dirWith(`line one\n${text}\n`));
    assert.equal(r.status, 1, `expected a finding for ${rule}`);
    assert.ok(r.stderr.includes(rule), r.stderr);
  });
}

test('the repo URL path is allowed', () => {
  const r = run(dirWith(j('https://github.com/kyisa', 'iah47/guardhooks\n')));
  assert.equal(r.status, 0, r.stderr);
});

test('a banned value in a file name fails', () => {
  const r = run(dirWith('clean\n', j('notes-20', '26-', '01-01.txt')));
  assert.equal(r.status, 1);
});

test('the repository itself is clean', () => {
  const r = run(ROOT);
  assert.equal(r.status, 0, r.stderr);
});
