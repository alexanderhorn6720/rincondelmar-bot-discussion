# Working Modes

This repo follows the Working Modes convention. Available commands:

- **brain** / **brain mode**: think mode. Analyze, propose options with tradeoffs, ask before assuming user vote. No code execution or destructive actions. Output: spec doc when applicable. Default mode if none specified.
  - **brain quick**: 5 min, fast decision, no formal spec
  - **brain deep**: 1h+, extensive analysis, full spec doc

- **DoIt** / **do it mode**: autonomous execution. No permission requests per step. Take minor technical decisions alone. Stay in scope (out-of-scope findings → open issue, do NOT fix here). Tests pass = done, do not over-polish. If stuck >30 min, stop and report. Each PR = 1 spec section. Semantic commits (feat/fix/test/docs/chore). Self-review before merge.

- **verify** / **verify mode**: validation against real system. User executes commands, agent guides with exact copy-paste commands. Minimum viable end-to-end (1-3 actions max). Failure = immediate rollback. Evidence required (log, screenshot, query result).

Typical flow: brain → spec doc → DoIt → verify.

Style: concise, technical, no flattery. Tables and lists over long prose. Ask before assuming user vote on product decisions.

## Spec doc template

Required 7 sections for any spec doc produced in brain mode:
1. Context (why, problem solved)
2. Explicit scope (what YES, what NO)
3. Closed decisions (already voted, do not re-litigate)
4. Implementation (files, schemas, contracts)
5. Tests (what to validate)
6. Definition of done (checkable list)
7. Risks and mitigations

Path convention: `cc-instructions-{workstream}/YYYY-MM-DD-{name}.md`

## Operational rules

- **Pre-flight check before long DoIt**: spec complete, tests passing on main, dependencies/credentials in place, rollback path documented.
- **Handoffs**: any session closing without completing task MUST push handoff doc with state, next steps, blockers, exact commands to resume.
- **Cost budgets**: declare expected LLM budget before tasks >$10. Report actual at close. Exceed 1.5x = stop and re-evaluate.
- **Multi-agent**: parallel sessions OK if scope isolated. Lockless coordination via `git pull --rebase` before push. Each agent respects its territory.
- **Blocks**: identify within 5 min, document, switch to non-dependent task. Do not fight the tool.
- **Validation**: canary 0% → smoke test (1 real action) → 10% → 24h observation → 25% → 50% → 100%. Failure = rollback, not in-prod debug.
- **When NOT to use AI**: catastrophic-cost errors, business decisions requiring human judgment, actions without backup/rollback.
- **Operating without the system**: in contexts where the system does not apply (offline, conversations with humans, rest periods, emergencies), operate without spec docs, without parallelization, without obsessive documentation.

## Workstream conventions for this repo

- **CC-Bot territory**: `apps/worker-bot/`, `packages/agents/`, Greeter, Booker, canary, bot infrastructure
- **CC-Data territory**: `data/`, data mining scripts, D1 INSERT to guests/leads/guest_events, R2 operator_playbook.md
- **WC territory**: `threads/`, `cc-instructions-{bot,data}/`, strategy, PR reviews
- **Alex territory**: deploys, smoke tests, canary scaling, merges, business decisions

## Thread + PR numbering

- Threads: `threads/XX-{author}-{topic}.md`, sequential numbering across all workstreams
- PRs CC-Bot: prefix `A` (A4, A6, A7, A7.5, A7.6, A7.7, A8...)
- PRs CC-Data: prefix `D` (D1, D2, D3...)
- Branches CC-Bot: `feat/greeter-v5-*`, `feat/canary-*`, etc
- Branches CC-Data: `feat/data-*`, etc

### Atomic thread claim

Always claim a new thread number via the script — never hand-pick a number:

```bash
bash scripts/new-thread.sh <author> <topic-slug>
# Example:
bash scripts/new-thread.sh CC-Bot kv-bug-fix-report
```

The script combines a local lock (flock or mkdir fallback) with
fetch+rebase+push retry, eliminating the collision class documented in
thread/172 (27/204 threads = 13% had duplicates before this). It:

- Validates `<author>` against the enum (WC, WC-Platform, WC-Impl, CC,
  CC-Bot, CC-Data, CC-Pago, CC-Web, Alex)
- Validates `<topic-slug>` as lowercase-kebab-case, min 5 chars
- Requires a clean working tree on `main`
- Pushes a stub directly to `origin main` (threads bypass PR review)
- Prints the new relative path to stdout (so callers can read it)

Exit codes: `0` success, `1` bad args/state, `2` lock timeout, `3` push
failed after 5 attempts.

Tests live in `scripts/tests/test_new_thread.sh` and run on every PR
that touches `scripts/**` (see `.github/workflows/scripts-tests.yml`).

## Thread frontmatter schema enforcement

Every `threads/*.md` carries a YAML frontmatter block (between two
`---` lines). Required fields and allowed values are defined in
[`schemas/thread.schema.json`](schemas/thread.schema.json):

| Field | Type | Constraint |
|---|---|---|
| `thread` | integer | >= 1, set by `scripts/new-thread.sh` |
| `author` | enum | WC / WC-Platform / WC-Impl / CC / CC-Bot / CC-Data / CC-Pago / CC-Web / Alex |
| `date` | string | `YYYY-MM-DD` (UTC) |
| `topic` | string | min 5 chars |
| `mode` | enum | brain · brain quick · brain deep · brain ultra · DoIt · verify · challenge response · synthesis |
| `status` | enum | draft · open · response · halt · closed · abandoned · open-for-alex-vote · ready-for-cc-execution · open-for-challenge |

`additionalProperties: true` — extra fields (`related`, `deliverable`,
`inputs`, `target_session`, etc.) are allowed.

### CI lint

`.github/workflows/thread-schema-lint.yml` runs
`node scripts/validate-threads.mjs` on every PR that touches
`threads/`. Two modes:

- **SOFT** (default for 7 days post thread/175 merge): violations are
  printed to stderr and the JSON report is uploaded as a CI artifact,
  but the job never fails.
- **HARD** (planned cutover 2026-05-29): violations on threads
  `>= GRANDFATHER_THRESHOLD` (default 175) fail the build.

Threads with number below the grandfather threshold are reported as
advisories — they reflect historical inconsistency (many older
threads have no frontmatter at all) that we don't retroactively fix.

Run locally:

```bash
node scripts/validate-threads.mjs            # soft, no failures
SCHEMA_MODE=hard node scripts/validate-threads.mjs  # fail on blocking
```

Self-tests for the validator:

```bash
node --test scripts/tests/test_validate_threads.mjs
```

## Anti-patterns (do NOT do)

- Casa Chamán in Greeter system prompt until renovation complete
- Beds24 sync mode "Everything" (overwrites Airbnb content — ALWAYS use Prices&Availability)
- Commits with secrets in plaintext
- ALTER TABLE during multi-agent execution
- Deploy to production Fridays after 5pm
- Trust "tests pass" without self-review of the diff
