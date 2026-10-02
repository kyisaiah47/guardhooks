#!/usr/bin/env node
// Rebuilds the hook table and the hook reference in README.md from src/manifests/*.json.
//
//   node scripts/readme.mjs          rewrite README.md in place
//   node scripts/readme.mjs --check  exit 1 when README.md is out of date
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const README = path.join(ROOT, 'README.md');
const dir = path.join(ROOT, 'src', 'manifests');
const manifests = fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()
  .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));

// Escape < and > outside backtick spans, so text such as <br> or <config> shows as written.
const escapeHtml = (s) => String(s).split(/(`[^`]*`)/).map((part, i) =>
  i % 2 ? part : part.replace(/</g, '&lt;').replace(/>/g, '&gt;')).join('');
const cell = (s) => escapeHtml(s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
const events = (m) => [...new Set(m.hooks.map((h) => h.event))].join(', ');

const table = [
  '| Hook | Runs on | What it blocks or adds |',
  '|---|---|---|',
  ...manifests.map((m) => `| \`${m.id}\` | ${events(m)} | ${cell(m.summary)} |`),
].join('\n');

const reference = manifests.map((m) => {
  const runs = m.hooks.map((h) => `${h.event}${h.matcher ? ` on \`${cell(h.matcher)}\`` : ''}`).join('; ');
  const escape = m.declare ? `\n\nEscape: \`npx guardhooks declare ${m.id} "<reason>"\` records a two-hour exception.` : '';
  return `### \`${m.id}\`\n\n${escapeHtml(m.doc)}\n\nRuns on: ${runs}. Install: \`npx guardhooks add ${m.id}\`.${escape}`;
}).join('\n\n');

function replaceBetween(text, name, body) {
  const start = `<!-- ${name}:start -->`;
  const end = `<!-- ${name}:end -->`;
  const a = text.indexOf(start);
  const b = text.indexOf(end);
  if (a < 0 || b < 0) throw new Error(`README.md is missing the ${start} / ${end} markers`);
  return text.slice(0, a + start.length) + '\n' + body + '\n' + text.slice(b);
}

const current = fs.readFileSync(README, 'utf8');
let next = replaceBetween(current, 'hooks-table', table);
next = replaceBetween(next, 'hooks-reference', reference);

if (process.argv.includes('--check')) {
  if (next !== current) {
    console.error('README.md is out of date. Run: node scripts/readme.mjs');
    process.exit(1);
  }
  console.log('README.md is up to date.');
} else {
  fs.writeFileSync(README, next);
  console.log(`README.md: ${manifests.length} hooks.`);
}
