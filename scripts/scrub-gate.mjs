#!/usr/bin/env node
// Scrub gate. Fails closed when any file in the repo carries private data or a dated incident.
//
//   node scripts/scrub-gate.mjs [root]
//
// It walks every file under root (default: the repo), skipping .git, node_modules and __pycache__. A file it
// cannot read is a failure, not a skip. Exit 0 means clean. Exit 1 lists every finding.
//
// The patterns use character classes such as [@] and [a] so this file never matches itself.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(process.argv[2] || path.join(path.dirname(fileURLToPath(import.meta.url)), '..'));
// Bytecode caches are build output. They are gitignored, removed before packing, and carry the
// absolute path of whatever machine compiled them.
const SKIP_DIRS = new Set(['.git', 'node_modules', '__pycache__']);

export const RULES = [
  // personal email addresses
  ['personal email', /ky[i]saiah47[@]gmail/i],
  ['personal email', /kyisaiah96[@]/i],
  ['personal email', /i[s]aiah\.ky[n]th[@]/i],
  ['personal email', /ky[n]th\.studios[@]/i],
  ['personal email', /fetchdue[@]gmail/i],
  ['personal email', /kyysaua[@]/i],
  ['personal email', /[A-Za-z0-9._%+-]+[@]gmail\.com/i],
  // local machine paths
  ['local home path', /\/Users\/[a]dmin/],
  ['local home path', /\/Users\/[A-Za-z0-9._-]+\//],
  // people
  ['personal name', /\bIsa[i]ah\b/i],
  // internal names and ids
  ['internal name', /Compound[L]abs/],
  ['internal name', /compound[-]ops/i],
  ['internal id', /xowekqdst[t]xwbhfxvusa/],
  ['internal id', /acct_1[T]/],
  ['Stripe account id', /\bacc[t]_[A-Za-z0-9]{16}\b/],
  ['internal tool', /compound[-]secret/i],
  ['internal tool', /compound[-]vault/i],
  // account handles and DIDs
  ['account handle', /kyisa[i]ah47(?!\/guardhooks)/i],
  ['account handle', /kyisa[i]ahh47|kyiisa[i]ah47/i],
  ['account handle', /compoundlabs[i]nc|thecompound[l]abs|ky[n]th[s]tudios|TillDram[a]tic1/i],
  ['account handle', /@compound[l]abs\b/i],
  ['account handle', /\bkyn[t]h/i],
  ['account DID', /did:pl[c]:[a-z0-9]{8,}/i],
  // key-shaped strings
  ['key shape', /sk-an[t]-[A-Za-z0-9_-]{16,}/],
  ['key shape', /\bs[k]-(?:proj-)?[A-Za-z0-9_-]{32,}/],
  ['key shape', /\b(?:s[k]|r[k]|p[k])_(?:live|test)_[A-Za-z0-9]{16,}/],
  ['key shape', /\bwhse[c]_[A-Za-z0-9]{16,}/],
  ['key shape', /\bgh[pousr]_[A-Za-z0-9]{30,}/],
  ['key shape', /\bgithub_pa[t]_[A-Za-z0-9_]{30,}/],
  ['key shape', /\bAKI[A][0-9A-Z]{16}\b/],
  ['key shape', /\bAIz[a][0-9A-Za-z_-]{35}\b/],
  ['key shape', /\bxox[abprs]-[A-Za-z0-9-]{10,}/],
  ['key shape', /\bnpm_[A-Za-z0-9]{36}\b/],
  ['key shape', /\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/],
  ['key shape', /-----BEGI[N] (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/],
  // dated incidents: hook messages state the rule, never a dated quote
  ['dated incident', /\b20\d\d-[01]\d-[0-3]\d\b/],
  // bot-detection bypass code never enters a public repo
  ['bot-detection bypass', /puppeteer-extra-plugin-[s]tealth|playwright-[e]xtra|Stealth[P]lugin/],
  ['bot-detection bypass', /\b2[c]aptcha\b|anti-?[c]aptcha|cap[s]olver|captcha.?[s]olv/i],
  ['bot-detection bypass', /defineProperty\(\s*navigator\s*,\s*['"]webdr[i]ver/],
];

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) {
      if (!SKIP_DIRS.has(e.name)) walk(path.join(dir, e.name), acc);
    } else acc.push(path.join(dir, e.name));
  }
  return acc;
}

export function scan(root = ROOT) {
  const findings = [];
  for (const file of walk(root)) {
    const rel = path.relative(root, file);
    let text;
    try {
      text = fs.readFileSync(file).toString('latin1');
    } catch (e) {
      findings.push({ file: rel, line: 0, rule: 'unreadable file', text: e.message });
      continue;
    }
    for (const [name, rx] of RULES) {
      if (rx.test(rel)) findings.push({ file: rel, line: 0, rule: name, text: '(in the file name)' });
    }
    const lines = text.split('\n');
    lines.forEach((ln, i) => {
      for (const [name, rx] of RULES) {
        const m = ln.match(rx);
        if (m) findings.push({ file: rel, line: i + 1, rule: name, text: m[0].slice(0, 60) });
      }
    });
  }
  return findings;
}

const invoked = process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) {
  let findings;
  try {
    findings = scan(ROOT);
  } catch (e) {
    console.error(`scrub gate could not walk ${ROOT}: ${e.message}`);
    process.exit(1);
  }
  if (findings.length) {
    console.error(`scrub gate: ${findings.length} finding(s) in ${ROOT}`);
    for (const f of findings) console.error(`  ${f.file}:${f.line}  ${f.rule}  ${JSON.stringify(f.text)}`);
    process.exit(1);
  }
  console.log(`scrub gate: clean (${walk(ROOT).length} files scanned)`);
}
