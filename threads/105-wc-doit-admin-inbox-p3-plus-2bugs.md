# 105 — WC: DoIt — P3 `/admin/inbox` + 2 bug fixes

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: P3 inbox build (per thread/85) bundled with 2 operational bugs discovered during Alex review
**Mode**: DoIt
**Status**: 🟢 Ready (after thread/103 backfill completes)
**Estimated effort**: 13-20h CC (Part A spec) + 1-2h bugs (Part B + C)

---

## TL;DR

3 parts in this DoIt:

| Part | Scope | Effort | Why bundled |
|---|---|---|---|
| **A** | `/admin/inbox` unified (per thread/85 spec) | 13-17h | P3 priority — main build |
| **B** | Fix bug: handoff reminder shows "sin nombre" always | ~1h | Discovered today via Telegram alert |
| **C** | Investigate + report 6 stale crons (NOT fix yet) | ~30 min | Diagnosis only — fix decisions need Alex |

Bundled because CC is here anyway, and B+C are blockers for clean inbox UX (B affects escalations row; C affects cron-driven sources).

---

## §1 — Part A: `/admin/inbox` build (spec ref thread/85)

### Spec reference (DO NOT re-litigate)

Full spec lives in:
- `threads/85-wc-admin-inbox-unified-spec.md` (high-level architecture)
- `threads/86-wc-bookings-inbox-delta-list-view-kv-inquiries.md` (Phase 4 list view + KV inquiries patterns)

Read both before starting. Section below summarizes scope.

### Scope summary

Build `/admin/inbox` consolidating 3 signal sources:

1. **Bot conversations** (`conversations` table) — paused, stalled, active WhatsApp sessions
2. **Beds24 inbox** (`bot_messages_inbox` table) — guest messages Airbnb/Booking/Direct
3. **Escalations** (`human_handoff_log` table) — open escalations awaiting human response

**Read-only MVP**. Click row → jumps to `/admin/conv?subscriber=X` for actions. No reply integration yet (Phase 2).

### 7 states color-coded

| State | Color | Meaning |
|---|---|---|
| 🔴 Escalated | red | `human_handoff_log.human_responded_at IS NULL` AND `notified_at > now-72h` |
| 🟡 Paused | yellow | `conversations.paused_until > now` |
| 🟠 Stalled | orange | `conversations.last_turn_at < now-30min` AND not closed |
| 🟢 Active bot | green | `conversations.last_turn_at > now-30min` |
| 🟢 Beds24 unread | green | `bot_messages_inbox.read_at IS NULL` |
| ⚠ Critical keyword | warning | last turn matches critical keywords |
| ✅ Resolved | gray | manually marked resolved within last 7 days |

### Priority sort order

1. critical keyword
2. escalated (red)
3. paused (yellow)
4. stalled (orange)
5. active bot (green dot)
6. beds24 unread (green badge)
7. resolved (gray, recent only)

### Filters

- Type: bot conv / beds24 / handoff / all
- Status: any of 7 states (multi-select)
- Channel: whatsapp / airbnb / booking / direct (multi-select)
- Time: last 24h / 7d / 30d / all
- Search: free text matching subscriber name, phone, or last message snippet

### Top-of-page summary

```
5 need attention now  ·  2 escalated · 1 paused · 2 stalled
```

Click any number → filter applied automatically.

### Hover actions per row

- **Open conversation** → `/admin/conv?subscriber=<id>`
- **Mark responded** (if escalated) → POST `/admin/handoff-mark-responded`
- **Resolve conversation** (if stalled/active) → POST `/admin/conv-resolve`
- **Unpause / Extend pause** (if paused) → POST `/admin/conv-unpause` or `/admin/conv-extend-pause`
- **Open Beds24** (if beds24 source) → `https://beds24.com/control2.php?ajax=bookedit&id=<beds24_booking_id>&tab=1`
- **Trigger escalation** (if no escalation yet) → POST `/admin/trigger-escalation`

### 3 new worker endpoints needed

1. `POST /admin/handoff-mark-responded` — sets `human_responded_at=now`, calculates `response_latency_seconds`
2. `POST /admin/conv-resolve` — sets `conversations.status='resolved'`
3. `POST /admin/trigger-escalation` — calls notifyHumanHandoff manually for selected conv

All admin-protected via existing auth (Better Auth + admin role).

### Readonly user support

If user has `admin-readonly` role: all hover actions disabled (grayed out), only navigation links work.

### OUT of scope (Phase 2)

- ❌ Reply integration (WhatsApp send-from-inbox)
- ❌ Real-time updates (page refresh fine for MVP)
- ❌ Bulk actions
- ❌ Push notifications
- ❌ Mobile design (tablet+ only)
- ❌ Customizable views / SLA timers per row

---

## §2 — Part B: Fix handoff reminders showing "sin nombre" always

### Bug evidence

WC discovered via code review (`apps/worker-bot/src/notify-human.ts`):

**Line 134 + 152**: render uses `ctx.subscriber_name ?? 'sin nombre'`.

**Line 397 (INSERT INTO human_handoff_log)**: column list = `subscriber_id, intent, property, telegram_msg_ids, success, error`. **subscriber_name NOT included**.

**Schema D1** (`human_handoff_log` table per pragma):
```
id, notified_at, subscriber_id, intent, property, telegram_msg_ids,
success, error, reminder_1h_sent_at, reminder_8h_sent_at,
human_responded_at, response_latency_seconds
```

**No subscriber_name column.** Initial notif renders name from `ctx` passed live by Greeter. But reminder cron later queries `human_handoff_log` directly → no name → fallback "sin nombre".

### Fix scope

1. Add column `subscriber_name TEXT` to `human_handoff_log` via migration
2. UPDATE `insertHandoffRow` (line 389-415 in notify-human.ts) to include subscriber_name in INSERT
3. UPDATE `checkAndSendReminders` SELECT (line 452-460) to include subscriber_name
4. Pass through to `buildReminderMessage` call (line 480-485)
5. Backfill existing rows where possible:
   - JOIN against `conversations` table or `greeter_turns` to recover name for existing rows
   - For rows where no source exists, leave NULL (display as "sin nombre" fallback)

### Migration file

`migrations/00XX_human_handoff_log_add_subscriber_name.sql`:

```sql
-- Add subscriber_name column to human_handoff_log for reminder cron display
ALTER TABLE human_handoff_log ADD COLUMN subscriber_name TEXT;

-- Backfill from conversations where possible
UPDATE human_handoff_log
SET subscriber_name = (
  SELECT c.subscriber_name FROM conversations c
  WHERE c.subscriber_id = human_handoff_log.subscriber_id
  LIMIT 1
)
WHERE subscriber_name IS NULL;

-- Index not needed (low cardinality + small table)
```

### Tests

- Update existing `notify-human.test.ts`:
  - Verify INSERT includes subscriber_name parameter
  - Verify reminder SELECT returns subscriber_name
  - Verify "sin nombre" fallback still works when subscriber_name NULL

---

## §3 — Part C: Diagnose 6 stale crons (NO fix yet — report only)

### Symptom (WC verified via D1 MCP)

`bot_config` rows with key `cron_heartbeat:*`:

```
cron_heartbeat:welcome-auto-send       64.7 min ago   🔴 stale (>15min threshold)
cron_heartbeat:client-bot-poll         97 min ago     🔴 stale
cron_heartbeat:handoff-reminders       111 min ago    🔴 stale
cron_heartbeat:refresh                 139 min ago    🔴 stale
cron_heartbeat:daily-digest            568 min ago    🔴 muy stale
cron_heartbeat:reviews-sync            1270 min ago   🔴 21h sin correr
```

Stale threshold = 15 min (`cron-bot-alerts.ts:32`). All 6 crons missing schedule.

### CC investigation scope (Part C)

CC investigates WITHOUT fixing. Report findings only, Alex decides actions.

1. **List all GH Actions workflows in `rdm-bot`**:
   ```bash
   ls .github/workflows/
   ```
   Identify which workflow drives each cron:
   - welcome-auto-send
   - client-bot-poll
   - handoff-reminders
   - refresh (Beds24 token refresh?)
   - daily-digest
   - reviews-sync

2. **Check workflow status via GitHub API**:
   ```bash
   gh workflow list --repo alexanderhorn6720/rdm-bot
   gh run list --repo alexanderhorn6720/rdm-bot --limit 20
   ```
   Identify:
   - Failed runs (most recent 5 per workflow)
   - Disabled workflows
   - Missing workflows (referenced but not present)

3. **Check workflow file content** for each cron yml:
   - Cron schedule (every X minutes)
   - Endpoint called
   - Secrets referenced
   - Branch/repo references (may be stale after rename)

4. **Possible causes to verify** (hypotheses):
   - GH Actions paused/disabled due to repo rename
   - Secrets expired (PAT, ADMIN_REFRESH_SECRET, BEDS24_REFRESH_TOKEN)
   - GH Actions monthly minutes limit hit
   - Workflow yml has hardcoded `rincondelmar-bot` reference instead of `rdm-bot`
   - Cron schedule too aggressive (rate-limited by GH)

5. **Quick test**: trigger one workflow manually via:
   ```bash
   gh workflow run <workflow-file> --repo alexanderhorn6720/rdm-bot
   ```
   See if it succeeds or fails. Capture stderr.

### CC report format for Part C

In thread/106:

```markdown
## Cron diagnosis (Part C from thread/105)

### Workflow inventory
- workflow A → drives cron Y → status [active/disabled/missing]
- workflow B → ...

### Recent runs
- Workflow A: last 5 runs (success/failed/skipped)
- Workflow B: ...

### Suspected root cause
- [specific hypothesis from list above]

### Suggested fix paths (for Alex to choose)
- Option 1: <action> — pros: X, cons: Y
- Option 2: <action> — pros: X, cons: Y

### Files affected
- .github/workflows/*.yml (X files)
- Possibly secrets configuration

### Confidence
- High / Medium / Low
```

Alex picks fix path in next session. CC does NOT auto-execute fix.

---

## §4 — Execution order

```
Part A (build inbox)
  1. Read threads 85 + 86 fully
  2. Create branch feat/admin-inbox-p3
  3. Backend: 3 new worker endpoints + tests
  4. Frontend: bookings.astro pattern reused for inbox.astro
  5. List view with priority sort + 7 states + filters
  6. Hover actions wired to endpoints
  7. Top summary band
  8. Tests pass: typecheck/lint/test/build
  9. 3-5 atomic commits

Part B (bug fix subscriber_name)
  10. Migration file 00XX
  11. UPDATE insertHandoffRow + checkAndSendReminders
  12. Backfill query
  13. Tests
  14. 1 atomic commit

Part C (cron diagnosis, no fix)
  15. Inventory workflows
  16. Check recent runs
  17. Test manual trigger one workflow
  18. Capture findings
  19. Add findings to thread/106 report (NOT commit code)

End
  20. Push branch
  21. PR + review summary
  22. gh pr merge --squash --delete-branch
  23. wrangler deploy (worker)
  24. Verify D1 migration applied
  25. Smoke tests
  26. Report thread/106
```

============================================================
PRE-FLIGHT (auto-execute, halt only on actual failure)
============================================================

1. cd "$env:USERPROFILE\rdm\dev\bot"
2. git status --short  → clean (or stashed)
3. git fetch origin
4. git checkout main && git pull origin main
5. gh auth status → logged in
6. Verify dependencies for inbox build:
   - apps/web/src/components/admin/ exists (BookingsView.tsx pattern lives here)
   - apps/worker-bot/src/notify-human.ts exists (Part B target)
   - .github/workflows/ exists (Part C target)
7. Verify thread/103 backfill task completed (CC's responsibility — check thread/104 status before starting)

============================================================
DELIVERABLES
============================================================

### Part A — Build /admin/inbox

PASO 1 — Read full specs
   Read threads/85 and threads/86 completely. Reference them in PR description.

PASO 2 — Branch
   git checkout -b feat/admin-inbox-p3

PASO 3 — Worker endpoints
   Create 3 admin endpoints:
   - POST /admin/handoff-mark-responded
   - POST /admin/conv-resolve
   - POST /admin/trigger-escalation
   
   Wire to existing auth (Better Auth admin guard).
   Update D1 with timestamps + status.
   Each returns JSON { ok: true, ... }.
   Tests per endpoint.

PASO 4 — Frontend: list view
   apps/web/src/pages/admin/inbox.astro
   Reuse list view pattern from PR #82 BookingsView.tsx where applicable.
   3 data sources joined client-side (or single endpoint server-side):
     SELECT FROM conversations ...
     SELECT FROM bot_messages_inbox ...
     SELECT FROM human_handoff_log ...
   
   Server-side preferred for clean priority sort.

PASO 5 — 7 states + sort + filters
   Implement state classifier function (pure):
   classifyRow(row) → state enum
   
   Sort rows by priority enum.
   Filter UI (4 multi-selects + free text).

PASO 6 — Hover actions
   Wire each action to corresponding endpoint.
   Confirm-before-destroy where applicable.

PASO 7 — Top summary band
   Compute counts per state.
   Click number → filter applied.

PASO 8 — Verification chain
   pnpm typecheck → 0 errors
   pnpm lint → no new errors
   pnpm test → all green
   pnpm build → clean

PASO 9 — 3-5 atomic commits
   commit 1: worker endpoints (with tests)
   commit 2: inbox.astro skeleton + data fetching
   commit 3: 7-state classifier + sort
   commit 4: filters + hover actions
   commit 5: top summary band + polish

### Part B — Fix subscriber_name in handoff log

PASO 10 — Migration
   Create migrations/00XX_human_handoff_log_add_subscriber_name.sql
   (use next available migration number)

PASO 11 — Code updates
   apps/worker-bot/src/notify-human.ts:
   - insertHandoffRow: add subscriber_name to INSERT
   - checkAndSendReminders: add subscriber_name to SELECT
   - buildReminderMessage: pass subscriber_name through

PASO 12 — Tests
   Update notify-human.test.ts:
   - INSERT case includes subscriber_name
   - SELECT case returns subscriber_name
   - Fallback "sin nombre" when NULL

PASO 13 — Apply migration
   wrangler d1 migrations apply rincon --remote
   (requires Y/N — ask tier per autonomy config)

PASO 14 — Atomic commit
   commit 6: fix(handoff): subscriber_name in log + reminders + backfill

### Part C — Cron diagnosis (NO code change)

PASO 15 — Workflow inventory
   ls .github/workflows/ on rdm-bot repo
   Identify cron-driven workflows

PASO 16 — GH API checks
   gh workflow list --repo alexanderhorn6720/rdm-bot
   gh run list --repo alexanderhorn6720/rdm-bot --limit 20 (per workflow)

PASO 17 — Manual trigger one workflow
   Pick one cron yml (e.g., welcome-auto-send if exists)
   gh workflow run <file> --repo alexanderhorn6720/rdm-bot
   Wait 30 sec
   gh run list --limit 1 → see if it succeeded or failed
   Capture stderr if failed

PASO 18 — Add diagnosis to thread/106 report (NOT a commit)
   Per format in §3 above.

### Final

PASO 19 — Push + PR
   git push origin feat/admin-inbox-p3
   gh pr create --title "feat(admin/inbox): unified inbox + handoff subscriber_name fix" \
                --body "..."

PASO 20 — Merge
   gh pr merge <N> --squash --delete-branch

PASO 21 — Worker deploy
   wrangler deploy (ask tier)

PASO 22 — Smoke tests
   curl /admin/inbox (returns 200/302)
   Browser: list view loads, 7 states render, filters work, hover actions work
   Verify reminder cron next run shows real name (or fallback if NULL)

PASO 23 — Report thread/106

============================================================
DEFAULTS
============================================================

- Commit format: Conventional Commits
- Encoding: UTF-8 file contents
- Squash merge with --delete-branch
- Branch: feat/admin-inbox-p3
- 5-7 atomic commits (5 for Part A, 1 for Part B, 0 for Part C)
- Migration via wrangler (ask tier per autonomy config)
- Worker deploy via wrangler deploy (ask tier)
- Use existing patterns from BookingsView.tsx (PR #82)
- Reuse beds24-links.ts helper for Beds24 links in inbox rows

============================================================
OUT OF SCOPE (NO HACER)
============================================================

- ❌ Reply integration (WhatsApp send-from-inbox) — Phase 2
- ❌ Real-time updates (refresh-based MVP)
- ❌ Bulk actions
- ❌ Push notifications
- ❌ Mobile responsive (tablet+ only)
- ❌ Customizable views per user
- ❌ SLA timers per row
- ❌ Auto-fix any stale cron in Part C (report only)
- ❌ Touch rdm-platform repo
- ❌ Touch welcome auto-send bug (separate task)
- ❌ Touch beds24 backfill (separate task, thread/103)
- ❌ New tests beyond what's specified
- ❌ Refactor existing /admin/conv beyond minimal changes for navigation from inbox

============================================================
EXTERNAL STATE (informational only)
============================================================

- 6 crons stale per D1 cron_heartbeat (welcome-auto-send 65min, client-bot-poll 97min, handoff-reminders 111min, refresh 139min, daily-digest 9.4h, reviews-sync 21h)
- D1 tables ready: conversations, bot_messages_inbox, human_handoff_log all populated
- Migrations in repo: check existing migration numbering before creating new one
- Beds24 backfill (thread/103) is parallel sprint — may add new rows to beds24_bookings during this build

============================================================
CRITERIO DE ÉXITO
============================================================

Part A:
- /admin/inbox returns 200/302
- 7 states render with correct colors
- Filters work
- Hover actions update DB + reflect in UI
- Top summary shows accurate counts
- Click any count → filter applied
- Readonly user can navigate but not act
- Click row → /admin/conv?subscriber=X works

Part B:
- Migration applied (D1 has subscriber_name column)
- New escalations include subscriber_name in row
- Reminder cron message shows real name (not "sin nombre") for new rows
- Existing rows backfilled where conversation match exists
- Tests green

Part C:
- thread/106 contains diagnosis: workflow inventory + recent runs + suspected root cause + suggested fix paths + confidence
- No code changes for Part C

Overall:
- pnpm test green (existing + new tests)
- 5-7 atomic commits clean history
- PR squash-merged, branch deleted
- CF Pages deploy succeeded for /admin/inbox
- Worker deployed for new endpoints
- Smoke tests pass

============================================================
SI TE ATORAS
============================================================

- Migration number conflict: pick next available, report number used
- Auth middleware missing for new admin endpoints: extend existing pattern, ask if unclear
- 3-source SELECT performance bad (UI laggy): add LIMIT 200, paginate, report perf in thread/106
- Stale cron diagnosis blocked (e.g., GH API down): mark Part C as "deferred, see thread/106", report what was learned
- Migration apply requires Y/N and Alex not available: pause Part B, finish Part A + C, resume Part B when Alex back
- pnpm test fails on existing tests: investigate, may need test fixture update
- Anything unexpected: STOP, report

============================================================
REPORTAR AL FINAL (thread/106-cc-bot-inbox-p3-bugs-complete.md)
============================================================

### Part A summary
- /admin/inbox URL + smoke test result
- 7 states implemented with screenshots/descriptions
- Filters working list
- Hover actions wired list
- 3 endpoints created with signatures
- Commits (5 SHAs)

### Part B summary
- Migration number applied
- Code changes (files + lines)
- Backfill query result (X rows updated)
- Test changes
- Commit (1 SHA)
- Reminder cron next run verification (real name appears)

### Part C summary
- Workflow inventory (list)
- Recent runs status (success/fail per cron)
- Manual trigger test result
- Suspected root cause
- Suggested fix paths (Alex picks)
- Confidence level
- NO commit — diagnosis only

### Overall
- PR # + merge SHA + URL
- Worker deploy status + URL
- /admin/inbox first impressions
- Any blockers for next priority (P2 welcome bug, M1 pricing, others?)

---

## §5 — What Alex does after thread/106

1. Open `/admin/inbox` in browser, verify 7 states render
2. Test 1-2 hover actions (mark responded, resolve)
3. Verify Telegram reminder cron next run shows real name (Part B)
4. Review Part C diagnosis, decide which fix path
5. Pick next priority:
   - **Fix stale crons** (from Part C diagnosis)
   - **P2 welcome bug** investigation
   - **M1 Pricing** start
   - Other

---

## §6 — Why this bundling

### Why Part B + C bundled with A?

- CC working in same files (notify-human.ts touches both A endpoints and B bug)
- Single PR cycle reduces overhead
- Reminders showing real name is FOR the inbox UX (clearer escalations row)
- Stale crons block inbox accuracy (bot_messages_inbox depends on client-bot-poll cron)

### Why Part C is diagnose-only?

- Stale cron root cause unknown — could be 5 different things
- Some fixes may need decisions (e.g., re-create GH Actions workflow vs migrate to CF Cron Trigger)
- Better to diagnose properly than guess and break something

### Why thread/85+86 specs aren't re-litigated here?

- Already approved by Alex in earlier sprints
- This thread/105 = execution task, not re-design
- If CC sees gap during build, halt + report per template v3

---

**WC standing by. CC executes after thread/103 (backfill) completes. Estimated total 15-19h.**

— WC, 2026-05-19
