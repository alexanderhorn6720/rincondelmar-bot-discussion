#!/usr/bin/env node
// Unit tests for scripts/validate-threads.mjs.
//
// Uses node:test (Node 20+). No npm deps required.
//
// Runs the validator in a temp dir against synthetic threads/*.md inputs,
// then asserts on stdout, exit code, and the JSON report.
//
// Usage:
//   node --test scripts/tests/test_validate_threads.mjs

import { mkdtemp, writeFile, mkdir, rm, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';

const THIS_FILE = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(THIS_FILE), '../..');
const VALIDATOR = path.join(REPO_ROOT, 'scripts/validate-threads.mjs');

function runValidator(cwd, env = {}) {
  return new Promise((resolve) => {
    const proc = spawn(process.execPath, [VALIDATOR], {
      cwd,
      env: { ...process.env, ...env },
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    proc.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    proc.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

async function setupSandbox(threadFiles) {
  const dir = await mkdtemp(path.join(tmpdir(), 'validate-threads-'));
  await mkdir(path.join(dir, 'threads'), { recursive: true });
  for (const [name, content] of Object.entries(threadFiles)) {
    await writeFile(path.join(dir, 'threads', name), content, 'utf8');
  }
  return dir;
}

const validFrontmatter = `---
thread: 999
author: CC-Bot
date: 2026-05-22
topic: valid-thread-example-here
mode: brain
status: draft
---

Body content.
`;

test('valid thread passes with no violations', async () => {
  const dir = await setupSandbox({ '999-CC-Bot-example.md': validFrontmatter });
  try {
    const r = await runValidator(dir);
    assert.equal(r.code, 0, `expected exit 0, got ${r.code}\n${r.stderr}`);
    const report = JSON.parse(await readFile(path.join(dir, '.thread-schema-report.json'), 'utf8'));
    assert.equal(report.files.length, 1);
    assert.deepEqual(report.files[0].violations, []);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('missing required field flagged as blocking when >= grandfather', async () => {
  const fm = `---
thread: 999
author: CC-Bot
date: 2026-05-22
topic: missing-mode-test-here
status: draft
---
`;
  const dir = await setupSandbox({ '999-CC-Bot-missing.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1, 'hard mode must fail on blocking violation');
    assert.match(r.stderr, /\[blocking\].*mode/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('missing field reported as advisory when < grandfather', async () => {
  const fm = `---
thread: 50
author: WC
date: 2026-05-22
topic: old-thread-grandfathered-here
status: closed
---
`;
  const dir = await setupSandbox({ '50-WC-old.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 0, 'hard mode must NOT fail on advisory (grandfathered)');
    assert.match(r.stderr, /\[advisory\].*mode/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('invalid author enum rejected', async () => {
  const fm = `---
thread: 999
author: Bob
date: 2026-05-22
topic: invalid-author-here
mode: brain
status: draft
---
`;
  const dir = await setupSandbox({ '999-Bob-bad.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /author 'Bob' not in enum/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('invalid date format rejected', async () => {
  const fm = `---
thread: 999
author: CC-Bot
date: 2026/05/22
topic: bad-date-test-thread
mode: brain
status: draft
---
`;
  const dir = await setupSandbox({ '999-CC-Bot-baddate.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /date '2026\/05\/22' must be YYYY-MM-DD/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('topic too short rejected', async () => {
  const fm = `---
thread: 999
author: CC-Bot
date: 2026-05-22
topic: abcd
mode: brain
status: draft
---
`;
  const dir = await setupSandbox({ '999-CC-Bot-short.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /at least 5 chars/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('invalid mode enum rejected', async () => {
  const fm = `---
thread: 999
author: CC-Bot
date: 2026-05-22
topic: valid-topic-here-good
mode: brain (challenge response)
status: draft
---
`;
  const dir = await setupSandbox({ '999-CC-Bot-paren-mode.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /mode 'brain \(challenge response\)' not in enum/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('SOFT mode (default) never fails even with blocking violations', async () => {
  const fm = `---
thread: 999
author: Bob
date: 2026-05-22
topic: soft-mode-warns-only
mode: brain
status: draft
---
`;
  const dir = await setupSandbox({ '999-Bob-soft.md': fm });
  try {
    const r = await runValidator(dir);
    assert.equal(r.code, 0, 'SOFT mode must always exit 0');
    assert.match(r.stderr, /\[blocking\].*author 'Bob'/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('no frontmatter block reported', async () => {
  const fm = `No frontmatter here.\nJust prose.`;
  const dir = await setupSandbox({ '999-WC-no-frontmatter.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /no `---` frontmatter block found/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('GRANDFATHER_THRESHOLD env var honored', async () => {
  const fm = `---
thread: 180
author: Bob
date: 2026-05-22
topic: should-be-advisory-now
mode: brain
status: draft
---
`;
  const dir = await setupSandbox({ '180-Bob.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard', GRANDFATHER_THRESHOLD: '200' });
    assert.equal(r.code, 0, 'with threshold 200, thread 180 is grandfathered');
    assert.match(r.stderr, /\[advisory\]/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('JSON report file is written and valid', async () => {
  const dir = await setupSandbox({ '999-CC-Bot-ok.md': validFrontmatter });
  try {
    await runValidator(dir);
    const report = JSON.parse(await readFile(path.join(dir, '.thread-schema-report.json'), 'utf8'));
    assert.ok(typeof report.mode === 'string');
    assert.ok(typeof report.grandfather === 'number');
    assert.ok(Array.isArray(report.files));
    assert.equal(report.files[0].thread_number, 999);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('multiple violations on a single thread all reported', async () => {
  const fm = `---
thread: 999
author: Bob
date: bad-date
topic: ab
mode: nonsense
status: weird
---
`;
  const dir = await setupSandbox({ '999-Bob-many.md': fm });
  try {
    const r = await runValidator(dir, { SCHEMA_MODE: 'hard' });
    assert.equal(r.code, 1);
    const report = JSON.parse(await readFile(path.join(dir, '.thread-schema-report.json'), 'utf8'));
    const violKeys = report.files[0].violations.map((v) => v.key).sort();
    assert.deepEqual(violKeys, ['author', 'date', 'mode', 'status', 'topic']);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('perf: 100 synthetic threads validate in under 5s', async () => {
  const files = {};
  for (let i = 1; i <= 100; i++) {
    const num = 200 + i;
    files[`${num}-CC-Bot-perf-${i}.md`] = validFrontmatter.replace('999', String(num));
  }
  const dir = await setupSandbox(files);
  try {
    const t0 = Date.now();
    const r = await runValidator(dir);
    const elapsed = Date.now() - t0;
    assert.equal(r.code, 0);
    assert.ok(elapsed < 5000, `expected <5s, took ${elapsed}ms`);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
