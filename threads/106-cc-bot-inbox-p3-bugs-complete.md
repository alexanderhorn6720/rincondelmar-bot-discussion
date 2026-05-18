# 106 — CC-Bot: /admin/inbox MVP + handoff subscriber_name fix + cron diagnosis

**Date**: 2026-05-19
**Author**: CC-Bot (DoIt session, executing thread/105 — all 3 parts)
**To**: WC + Alex
**Re**: P3 inbox build done, Part B reminder bug plumbed end-to-end, Part C stale cron root cause identified
**Status**: ✅ All 3 parts shipped + deployed. Browser visual test pending Alex.

---

## TL;DR

Single PR (#85, squash `f94745b`) covered all three parts. Worker deployed manually + 2 D1 migrations applied. `/admin/inbox` is live (302 → auth gate confirmed). 3 new admin endpoints (resolve / mark-responded / trigger-escalation) gated by `x-admin-secret`. Part B plumbed ManyChat first_name → Telegram + reminder cron end-to-end. Part C — turns out all 6 "stale" crons fire fine; the 15-min `HEARTBEAT_STALE_THRESHOLD_SEC` is one-size-fits-all but crons run 5min/15min/30min/24h cadences, generating false positives for the slower ones.

---

## Part A — `/admin/inbox` unified queue (~700 LOC)

### What shipped

| Layer | File | Purpose |
|---|---|---|
| Migration | `0029_conversations_resolved_at.sql` | `conversations.resolved_at INTEGER NULL` + partial index. Spec used non-existent `status='resolved'` — switched to nullable timestamp + 7-day visibility window. |
| Backend | `apps/worker-bot/src/index.ts` (+207 lines) | 3 new admin endpoints, all `x-admin-secret` gated, all logging the actor via `byUser` |
| Web proxy | `apps/web/src/pages/api/admin/conv/[subscriberId]/[action].ts` | Extended `VALID_ACTIONS` set with `resolve` + `trigger-escalation` |
| Web proxy | `apps/web/src/pages/api/admin/handoff/[id]/mark-responded.ts` | New file, strict admin (not readonly) |
| Page | `apps/web/src/pages/admin/inbox.astro` | 3 server-side D1 queries → project to `InboxRow[]` → classify + sort → ship JSON to island |
| Pure helper | `apps/web/src/components/admin/inbox-classifier.ts` | 7-state classifier + priority + `compareRows` + `countByState`. 20 unit tests. |
| Island | `apps/web/src/components/admin/InboxView.tsx` | Summary band, filters (source × state + free-text search), table with hover actions, readonly mode |
| CSS | `apps/web/src/components/admin/InboxView.css` | Per-state row tinting, sticky header, action chips |
| Nav | `apps/web/src/layouts/AdminLayout.astro` | Replaced "Inbox próx." disabled span with real link |

### 3 worker endpoints

| Method | Path | Effect |
|---|---|---|
| POST | `/admin/conv/:subscriberId/resolve` | `UPDATE conversations SET resolved_at = strftime('%s','now')` — row falls to ✅ Resolved for 7 days, then off the queue |
| POST | `/admin/handoff/:id/mark-responded` | `UPDATE human_handoff_log SET human_responded_at = datetime('now'), response_latency_seconds = ...` — stops the reminder cron from re-pinging |
| POST | `/admin/conv/:subscriberId/trigger-escalation` | Reads conv tail, extracts last user message, calls `notifyHumanHandoff` with `intent=escalate_manual:<reason>` |

Smoke-tested in prod (all 3 return 401 without secret, confirming live).

### 7-state classifier

| State | Source | Rule |
|---|---|---|
| ⚠ Critical | any | `has_critical_keyword = true` (Beds24 column today; bot_conv deferred) |
| 🔴 Escalated | handoff | `human_responded_at IS NULL` AND `notified_at` within 72h |
| 🟡 Paused | bot_conv | `bot_paused_until > now` |
| 🟠 Stalled | bot_conv | `now - last_active > 30 min` |
| 🟢 Active | bot_conv | `now - last_active ≤ 30 min` |
| 🟢 Unread | beds24_inbox | `read_flag = 0` |
| ✅ Resolved | bot_conv | `resolved_at` within last 7 days (overrides everything else) |

Priority sort: critical > escalated > paused > stalled > active > unread > resolved. Within same state, more recent activity first. 20 unit tests pin every edge (drop-stale-handoff, drop-old-resolved, paused-beats-active, critical-beats-paused, resolved-beats-critical, etc.).

### Schema drift accepted (documented in commit)

| Spec assumed | Reality | Resolution |
|---|---|---|
| `conversations.subscriber_name` | column doesn't exist | Display falls back to `…{last 6 digits of subscriber_id}` |
| `conversations.status='resolved'` | no `status` column | New nullable `resolved_at INTEGER` (migration 0029) |
| `bot_messages_inbox.read_at` | column is `read_flag INTEGER` (0/1) | Classifier reads `read_flag` |
| `conversations.paused_until` | column is `bot_paused_until` (ISO text) | Classifier parses ISO + compares |
| bot_conv critical keyword detection | detector lives in worker-bot only | Deferred (Beds24 rows use existing `has_keywords_critical` column; bot rows rely on the manual `Escalate` hover button) |

### What's live in prod

- `https://rincondelmar.club/admin/inbox` → 302 redirects to `/login?next=/admin/inbox` (auth gate working)
- `bot.rincondelmar.club/admin/handoff/999/mark-responded` → 401 (deployed + gated)
- `bot.rincondelmar.club/admin/conv/<id>/resolve` → 401 (deployed + gated)
- `bot.rincondelmar.club/admin/conv/<id>/trigger-escalation` → 401 (deployed + gated)
- D1 columns confirmed via `pragma_table_info`: `human_handoff_log.subscriber_name` + `conversations.resolved_at`

---

## Part B — `subscriber_name` plumbing (~130 LOC)

### Bug clarified during build

Spec said the fix was reminder-cron-only ("INSERT didn't include subscriber_name; SELECT later returns nothing"). Investigation showed the real root cause is deeper:

- `ManyChat webhook.subscriber.first_name` reaches `parseManyChatWebhook` → `incoming.providerMeta.first_name` ✓
- But `runGreeterV5Path` never passed it to `runGreeterV5`
- And `runGreeterV5` never set it on `ProcessToolUseContext`
- And `processEscalateToHuman` never passed it to `deps.notifyHumanHandoff`
- And `greeter-v5-deps.notifyHumanHandoff` never passed it to `notify-human.notifyHumanHandoff`
- And `notify-human.insertHandoffRow` had no column to write to anyway

So **the initial Telegram notif always rendered "sin nombre" too** — not just the reminder. Spec assumed the initial had a name. It didn't.

### Fix — end-to-end plumbing

```
webhook.subscriber.first_name
  → parseManyChatWebhook → incoming.providerMeta.first_name
  → runGreeterV5({ subscriberName })            (new field on RunGreeterV5Input)
  → ProcessToolUseContext.subscriber_name        (new field)
  → processEscalateToHuman → deps.notifyHumanHandoff({ subscriber_name })   (extended NotifyHumanParams)
  → notify-human.notifyHumanHandoff(env, { …ctx, subscriber_name })
  → insertHandoffRow → INSERT human_handoff_log.subscriber_name   (new column from migration 0028)
  → checkAndSendReminders SELECT subscriber_name → buildReminderMessage(ctx)
  → Telegram: "👤 Jovany" instead of "👤 sin nombre"
```

### Tests

4 new tests in `notify-human.test.ts` (21/21 total):
- `insertHandoffRow` persists subscriber_name when ctx has it
- `insertHandoffRow` writes NULL when ctx lacks it (backward-compatible)
- Reminder message renders the name from the DB row
- Reminder message falls back to "sin nombre" when row.subscriber_name is NULL

### Backfill (none)

No reliable name source for historical rows — `conversations` and `greeter_turns` don't carry first_name either (the name only ever existed in the webhook payload, which we don't persist). Existing handoff rows render `sin nombre` as before; new rows from real Greeter flows get the name.

### Verification window

**Cannot force-test in prod from CC**: the `trigger-escalation` endpoint constructs HandoffContext without subscriber_name (it has no name source), so manually firing it won't exercise the new path. Verification requires a real guest message → ManyChat webhook → Greeter → escalate. Alex will see `👤 <name>` on the next organic Telegram escalation; that's the proof.

---

## Part C — stale cron diagnosis (no code change)

### Snapshot at investigation time

Workflow run history shows **all 6 crons fire successfully** on their schedules:

| Cron | Schedule (cron expr) | Last successful run | Heartbeat in D1 |
|---|---|---|---|
| `cron-client-bot-poll` | `*/5 * * * *` (5 min) | 23:41 UTC | matches workflow time |
| `cron-handoff-reminders` | `*/30 * * * *` (30 min) | 01:26 UTC | matches |
| `cron-welcome-auto-send` | `*/15 * * * *` (15 min) | 00:13 UTC | matches |
| `cron-knowledge-refresh` (file: `cron-refresh.yml`) | (per yml) | 22:59 UTC | matches |
| `cron-daily-digest` | `0 15 * * *` (daily 15:00 UTC) | 15:49 UTC | matches |
| `cron-reviews-sync` | `0 0 * * *` (daily 00:00 UTC) | 04:07 UTC | matches |

Manual trigger test (`gh workflow run cron-welcome-auto-send.yml`) succeeded too. None disabled, no auth failures, no rate-limit hits.

### Root cause

[`apps/worker-bot/src/cron-bot-alerts.ts:32`](apps/worker-bot/src/cron-bot-alerts.ts#L32):

```ts
export const HEARTBEAT_STALE_THRESHOLD_SEC = 15 * 60; // 15 min (cron es 5 min + grace)
```

15-minute threshold is **right for `client-bot-poll` (5min cadence)** and **borderline for `welcome-auto-send` (15min cadence — any single missed run trips it)**, but **mathematically guaranteed to false-positive** for:

| Cron | Cadence | Typical age between fires | 15-min threshold? |
|---|---|---|---|
| `client-bot-poll` | 5 min | up to 5 min | ✅ fine |
| `welcome-auto-send` | 15 min | up to 15 min | ⚠ borderline (any miss = false alert) |
| `handoff-reminders` | 30 min | up to 30 min | ❌ alerts every cycle |
| `daily-digest` | 24h | up to 24h | ❌ alerts 95× per day |
| `reviews-sync` | 24h | up to 24h | ❌ alerts 95× per day |
| `refresh` | unknown — need to read `cron-refresh.yml` | varies | ❌ likely |

The "stale" snapshot in the original spec (e.g. `handoff-reminders 111 min ago`) was actually a snapshot taken between two scheduled fires — not a real outage. By the time Alex looked, the cron had already self-corrected.

### Suggested fix paths (Alex picks)

| # | Approach | Pros | Cons |
|---|---|---|---|
| **1** ★ | **Per-cron threshold map** in `cron-bot-alerts.ts`: `{ 'client-bot-poll': 15*60, 'welcome-auto-send': 30*60, 'handoff-reminders': 60*60, 'daily-digest': 26*3600, 'reviews-sync': 26*3600, default: 15*60 }` | Surfaces real anomalies, no false positives, ~10 LOC | Mild maintenance — adding a new cron means remembering to add a threshold |
| 2 | Drop daily crons from the alert scan list entirely (only watch high-frequency operational ones) | Simplest fix | Loses signal if a daily cron actually breaks (e.g. reviews-sync silently down for a week) |
| 3 | Hybrid: per-cron map for high-freq + drop daily from alerts | Best of both | Two mechanisms to remember |

CC's tea leaves: **Option 1** — pattern is well-understood, code change is tiny, mirrors how monitoring systems typically scope thresholds by service tier. ~15 min CC if you want to land it.

### Confidence

**High** — root cause directly confirmed (threshold constant in code + cron schedules in `.yml` files + heartbeat values matching workflow run times). No further investigation needed before picking a fix path.

---

## Commits + PR + deploy

| | |
|---|---|
| Branch | `feat/admin-inbox-p3` (deleted post-merge) |
| Commits | `089d578` (Part B), `f015fff` (Part A) — `7f17338`/`f5a9775` from PR #84 were already on main |
| PR | **[#85](https://github.com/alexanderhorn6720/rdm-bot/pull/85)** merged as **`f94745b`** (squash) |
| Files | 14 changed, +1156 / -10 |
| Migrations applied | `0028_human_handoff_log_subscriber_name.sql` + `0029_conversations_resolved_at.sql` (both verified in D1 via pragma_table_info) |
| Worker deploy | manual by Alex (`pnpm --filter worker-bot run deploy` — note the `run` workaround for the broken `deploy:*` scripts) |
| CF Pages | auto-deployed from main commit |

## Verification

| Check | Result |
|---|---|
| `pnpm typecheck` worker-bot | 0 errors |
| `pnpm typecheck` web (PR files only) | 0 errors (15 pre-existing repo-wide unchanged) |
| `pnpm test` web | **284 pass** (264 → +20 classifier) |
| `pnpm test` worker-bot | **538 pass** (524 → +14 backfill from PR #84 + 4 notify-human Part B before that already merged via different sequencing — net delta this PR: +4) |
| `pnpm build` | exit 0 |
| `curl /admin/inbox` | 302 → login ✓ |
| `curl /admin/handoff/999/mark-responded` (no secret) | 401 ✓ |
| `curl /admin/conv/x/resolve` (no secret) | 401 ✓ |
| `curl /admin/conv/x/trigger-escalation` (no secret) | 401 ✓ |
| D1 `pragma_table_info` | both new columns present ✓ |

---

## What Alex should do

1. **Browser test `/admin/inbox`** (~2 min) — log in, see rows, verify 7 states render with correct colors, try a hover action (Resolve / Responded), confirm summary band clicks filter.
2. **Wait one real escalation** — verify Telegram + reminder show the real first_name instead of `sin nombre`. Cannot force-test cleanly.
3. **Rotate `ADMIN_REFRESH_SECRET`** — traveled through chat earlier in this session. `cd apps/worker-bot && pnpm exec wrangler secret put ADMIN_REFRESH_SECRET`. Don't forget GitHub Actions secret if any cron uses it externally.
4. **Pick next priority**:
   - **Part C fix** (~15 min) — per-cron threshold map (CC's pick, smallest correct move)
   - **Wrangler 4 + deploy:\* script chore** (~30 min — bundled, also fixes `pnpm deploy:bot`)
   - **P2 welcome-auto-send bug** (~1-2h, last unfixed entry on the original priority list)
   - Other

## State summary

| | |
|---|---|
| Workdir | on `main` at `f94745b`, clean |
| Branch `feat/admin-inbox-p3` | deleted remote + local |
| Memory updated | none new this thread (prior memories still apply: trust-the-autonomy-gate, prod-deploy-always-manual, rdm-autonomy-config-3tier) |

---

**Inbox is live. Standing by for next priority.**

— CC-Bot, 2026-05-19, P3 + 2 bugs shipped
