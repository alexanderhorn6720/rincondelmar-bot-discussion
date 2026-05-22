#!/usr/bin/env node
// Validate frontmatter of every threads/*.md against schemas/thread.schema.json.
//
// Spec: thread/175 task T3.
//
// Modes (SCHEMA_MODE env var):
//   - soft (default): warn on all violations, exit 0
//   - hard:           fail (exit 1) on violations in threads >= GRANDFATHER_THRESHOLD
//
// Grandfathering: threads with `thread:` number below GRANDFATHER_THRESHOLD
// (default 175) are reported as advisories, never fail in HARD mode. New
// threads must conform.
//
// Output:
//   - stdout: markdown summary table
//   - $GITHUB_STEP_SUMMARY (if set): same markdown table appended
//   - stderr: one line per violation, prefixed by file:line
//   - JSON: written to ./.thread-schema-report.json (machine readable)
//
// No npm deps — uses only Node built-ins. CI install step skipped.
//
// Usage:
//   node scripts/validate-threads.mjs
//   SCHEMA_MODE=hard node scripts/validate-threads.mjs
//   GRANDFATHER_THRESHOLD=200 SCHEMA_MODE=hard node scripts/validate-threads.mjs

import { readdir, readFile, writeFile, appendFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const MODE = (process.env.SCHEMA_MODE || 'soft').toLowerCase();
const GRANDFATHER = Number.parseInt(process.env.GRANDFATHER_THRESHOLD || '175', 10);

if (MODE !== 'soft' && MODE !== 'hard') {
  console.error(`ERROR: SCHEMA_MODE must be 'soft' or 'hard' (got '${MODE}')`);
  process.exit(2);
}

// ---------- schema (kept in sync with schemas/thread.schema.json) ----------
const REQUIRED = ['thread', 'author', 'date', 'topic', 'mode', 'status'];
const AUTHOR_ENUM = new Set([
  'WC',
  'WC-Platform',
  'WC-Impl',
  'CC',
  'CC-Bot',
  'CC-Data',
  'CC-Pago',
  'CC-Web',
  'Alex',
]);
const MODE_ENUM = new Set([
  'brain',
  'brain quick',
  'brain deep',
  'brain ultra',
  'DoIt',
  'verify',
  'challenge response',
  'synthesis',
]);
const STATUS_ENUM = new Set([
  'draft',
  'open',
  'response',
  'halt',
  'closed',
  'abandoned',
  'open-for-alex-vote',
  'ready-for-cc-execution',
  'open-for-challenge',
]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

// ---------- minimal YAML frontmatter parser ----------
// Handles only the shapes used in rdm-discussion threads:
//   key: value          (string, number, or unquoted scalar)
//   key: "value"        (quoted string — strip quotes)
//   key:                (followed by list lines starting with `  - ...`)
//   nested map:         (skipped — flat keys only at top level)
// Tabs/comments/blank lines tolerated.

function extractFrontmatter(text) {
  // Matches a leading `---\n...\n---` block. Tolerates BOM.
  const stripped = text.replace(/^﻿/, '');
  const m = stripped.match(/^---\r?\n([\s\S]*?)\r?\n---\s*(\r?\n|$)/);
  if (!m) return { found: false, body: '' };
  return { found: true, body: m[1] };
}

function parseFrontmatter(body) {
  const out = {};
  const lines = body.split(/\r?\n/);
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    i++;
    if (!line.trim() || line.trim().startsWith('#')) continue;
    // Top-level key (no leading whitespace).
    const kvMatch = line.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$/);
    if (!kvMatch) continue;
    const key = kvMatch[1];
    let rest = kvMatch[2];
    if (rest === '' || rest === undefined) {
      // List or nested map: collect subsequent indented `  - ...` lines.
      const items = [];
      while (i < lines.length) {
        const sub = lines[i];
        if (/^\s+-\s+/.test(sub)) {
          items.push(sub.replace(/^\s+-\s+/, '').trim());
          i++;
        } else if (sub === '' || sub.startsWith('#')) {
          i++;
        } else if (/^[A-Za-z_]/.test(sub)) {
          // Next top-level key — stop.
          break;
        } else {
          // Indented non-list (nested map) — skip but don't break the loop on a key.
          i++;
        }
      }
      if (items.length > 0) {
        out[key] = items;
      } else {
        out[key] = null;
      }
    } else {
      // Strip inline comments, but only if the comment marker is preceded
      // by whitespace (so it isn't confused with a `#` inside a value).
      rest = rest.replace(/\s+#.*$/, '').trim();
      // Strip surrounding quotes.
      if ((rest.startsWith('"') && rest.endsWith('"')) || (rest.startsWith("'") && rest.endsWith("'"))) {
        rest = rest.slice(1, -1);
      }
      // Type coercion: integer if pure digit string.
      if (/^-?\d+$/.test(rest)) {
        out[key] = Number.parseInt(rest, 10);
      } else if (/^-?\d+\.\d+$/.test(rest)) {
        out[key] = Number.parseFloat(rest);
      } else {
        out[key] = rest;
      }
    }
  }
  return out;
}

// ---------- validation rules ----------
function validateFrontmatter(fm) {
  const violations = [];
  for (const key of REQUIRED) {
    if (!(key in fm) || fm[key] === '' || fm[key] === null || fm[key] === undefined) {
      violations.push({ key, kind: 'missing', message: `required field '${key}' missing or empty` });
    }
  }
  if ('thread' in fm && !(Number.isInteger(fm.thread) && fm.thread >= 1)) {
    violations.push({
      key: 'thread',
      kind: 'type',
      message: `thread must be a positive integer (got ${JSON.stringify(fm.thread)})`,
    });
  }
  if ('author' in fm && typeof fm.author === 'string' && !AUTHOR_ENUM.has(fm.author)) {
    violations.push({
      key: 'author',
      kind: 'enum',
      message: `author '${fm.author}' not in enum (${[...AUTHOR_ENUM].join(', ')})`,
    });
  }
  if ('date' in fm && typeof fm.date === 'string' && !DATE_RE.test(fm.date)) {
    violations.push({
      key: 'date',
      kind: 'format',
      message: `date '${fm.date}' must be YYYY-MM-DD`,
    });
  }
  if ('topic' in fm && typeof fm.topic === 'string' && fm.topic.length < 5) {
    violations.push({
      key: 'topic',
      kind: 'minlength',
      message: `topic '${fm.topic}' must be at least 5 chars`,
    });
  }
  if ('mode' in fm && typeof fm.mode === 'string' && !MODE_ENUM.has(fm.mode)) {
    violations.push({
      key: 'mode',
      kind: 'enum',
      message: `mode '${fm.mode}' not in enum`,
    });
  }
  if ('status' in fm && typeof fm.status === 'string' && !STATUS_ENUM.has(fm.status)) {
    violations.push({
      key: 'status',
      kind: 'enum',
      message: `status '${fm.status}' not in enum`,
    });
  }
  return violations;
}

// ---------- main ----------
async function main() {
  const threadsDir = path.resolve(process.cwd(), 'threads');
  if (!existsSync(threadsDir)) {
    console.error(`ERROR: ${threadsDir} not found (run from rdm-discussion root).`);
    process.exit(2);
  }
  const all = await readdir(threadsDir);
  const files = all.filter((f) => f.endsWith('.md')).sort();

  const fileResults = [];
  let totalViolations = 0;
  let blockingViolations = 0;

  for (const f of files) {
    const full = path.join(threadsDir, f);
    const text = await readFile(full, 'utf8');
    const { found, body } = extractFrontmatter(text);
    // Match leading digits, tolerate suffixes (e.g. 84b-, 158a-).
    const numberMatch = f.match(/^(\d+)/);
    const threadNumFromFilename = numberMatch ? Number.parseInt(numberMatch[1], 10) : null;

    if (!found) {
      const isGrandfathered =
        threadNumFromFilename !== null && threadNumFromFilename < GRANDFATHER;
      const violation = {
        key: '(frontmatter)',
        kind: 'missing',
        message: 'no `---` frontmatter block found',
      };
      fileResults.push({
        file: f,
        thread_number: threadNumFromFilename,
        grandfathered: isGrandfathered,
        violations: [violation],
      });
      totalViolations++;
      if (!isGrandfathered) blockingViolations++;
      continue;
    }

    const fm = parseFrontmatter(body);
    const violations = validateFrontmatter(fm);
    const declaredThread = typeof fm.thread === 'number' ? fm.thread : null;
    const threadNumEffective = declaredThread ?? threadNumFromFilename ?? 0;
    const isGrandfathered = threadNumEffective < GRANDFATHER;
    fileResults.push({
      file: f,
      thread_number: threadNumEffective,
      grandfathered: isGrandfathered,
      violations,
    });
    totalViolations += violations.length;
    if (!isGrandfathered) blockingViolations += violations.length;
  }

  // ---------- report ----------
  const rows = fileResults.filter((r) => r.violations.length > 0);
  const reportLines = [];
  reportLines.push(`# Thread schema validation report`);
  reportLines.push('');
  reportLines.push(
    `- mode: \`${MODE}\` (${MODE === 'hard' ? 'CI fails on blocking violations' : 'CI passes; advisory only'})`,
  );
  reportLines.push(`- grandfather threshold: \`${GRANDFATHER}\` (threads below this are advisory)`);
  reportLines.push(`- scanned: ${files.length} files`);
  reportLines.push(`- with violations: ${rows.length} files`);
  reportLines.push(`- total violations: ${totalViolations}`);
  reportLines.push(`- blocking violations (thread >= ${GRANDFATHER}): ${blockingViolations}`);
  reportLines.push('');

  if (rows.length > 0) {
    reportLines.push('| file | thread | grandfathered | violations |');
    reportLines.push('|---|---|---|---|');
    for (const r of rows) {
      const msgs = r.violations
        .map((v) => `\`${v.key}\`: ${v.message}`)
        .join('<br>');
      reportLines.push(
        `| \`${r.file}\` | ${r.thread_number ?? '?'} | ${r.grandfathered ? '✅' : '❌'} | ${msgs} |`,
      );
    }
  } else {
    reportLines.push('No violations found.');
  }

  const md = reportLines.join('\n');
  process.stdout.write(`${md}\n`);

  if (process.env.GITHUB_STEP_SUMMARY) {
    try {
      await appendFile(process.env.GITHUB_STEP_SUMMARY, `${md}\n`);
    } catch (err) {
      console.error(`WARN: could not write to GITHUB_STEP_SUMMARY: ${err.message}`);
    }
  }

  // JSON report for machine consumers
  await writeFile(
    path.resolve(process.cwd(), '.thread-schema-report.json'),
    `${JSON.stringify({ mode: MODE, grandfather: GRANDFATHER, files: fileResults }, null, 2)}\n`,
    'utf8',
  );

  // stderr per-violation for grep-ability
  for (const r of rows) {
    for (const v of r.violations) {
      const tag = r.grandfathered ? '[advisory]' : '[blocking]';
      console.error(`${tag} ${r.file}: ${v.key}: ${v.message}`);
    }
  }

  if (MODE === 'hard' && blockingViolations > 0) {
    process.exit(1);
  }
  process.exit(0);
}

main().catch((err) => {
  console.error('FATAL:', err);
  process.exit(2);
});
