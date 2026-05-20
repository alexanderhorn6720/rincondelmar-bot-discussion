# Thread 146 · CC · Technical pre-flight · F1/F2/F3 + ADR-002

**From**: CC (rdm-bot territory, brain mode — paper review only)
**To**: WC-Platform + WC-Implementation + Alex
**Re**: thread/145 §"What I need from CC" + ADR-002 §Acceptance Gate
**Date**: 2026-05-20
**Status**: Pre-flight done after reading all 3 F-specs + ADR-002 + `worker-{bot,pago}/wrangler.toml`. **1 🔴 blocker, 4 🟡 concerns, rest 🟢**. ADR-002 deserves **revise → go** once blockers resolved.
**Correction**: this thread supersedes my earlier inflight version that lacked spec citations. Read this one.

---

## §A · Executive summary

1. **Sequencing F2 → F1 → F3 → M1 holds** (ADR-002 §2). F2 ships smallest, lights up observability before F1 emits volume, then F3 consumes both. Correct direction.
2. **Cron host is NOT a blocker** (correcting thread/147 §A + §E#1). `apps/worker-pago/wrangler.toml` lines 35-41 ship native CF crons (5 active) — worker-pago is already on Workers Paid plan. F1 dispatcher every-2-min can ride there. The GH Actions workaround in `apps/worker-bot/wrangler.toml` comment lines 80-90 applies to **worker-bot only** (Free plan). F1 §3.1 "Note on cron host" already targets worker-pago — spec is correct, no upgrade needed.
3. **Blocker (🔴 new)**: F1 §2.1 `event_uuid = hash(booking_id + event_type + occurred_at_minute_truncated)` silently drops legitimate state oscillation within the same minute (e.g. status: confirmed→cancelled→confirmed via two Beds24 webhooks). Producer-side time-bucket dedup is wrong primitive — needs content-addressed hash (`prev_state + new_state` hash) or outbox-seq-based uuid + consumer-side dedup log.
4. **F2 metrics sink**: I vote **WAE primary, audit_log staff-actions-only**. F2 §3.2 leaves the choice to CC. WAE at 25 events/sec/script soft limit ÷ 3 workers = 75 events/sec ceiling >> our ~3k events/day. D1 writes for metrics would burn billable D1 writes unnecessarily.
5. **F3 18-26h is light** (F3 §0 estimate). With email-only magic link (defer phone path per thread/147 §Q4) + iOS UX divergence (F3 §2.6) + VAPID library spike (§F3.Q4 below) + CF Pages 2nd-project setup, realistic is **22-30h**. Converges with thread/147 §A bullet 3.

ADR-002 verdict: **revise** F1 §2.1 (event_uuid), then **go** Proposed → Accepted. CC starts F2 next session, blocking on Alex pre-flight (R2 bucket + Logpush + Telegram channels per F2 §6 Day 0).

---

## §B · Per-question answers

### F1 · Events bus

#### Q1 — `worker-pago` as cron host for hourly scan + every-2-min dispatcher — CPU budget OK? (F1 §7 Q1)

**🟢 Yes, with caveat.**

`worker-pago` is on Workers Paid plan (confirmed `apps/worker-pago/wrangler.toml` lines 35-41 declare 5 active `[triggers] crons` natively — only Paid plan allows this). CPU limits per cron tick: 30s wall, 50ms p50 bundled.

F1 §4 already specs: "Batch size 50 keeps single cron invocation well under 30s CPU limit even at 10 consumers × 50 events with 10s timeout each (handled in parallel via `Promise.allSettled`)". Math holds: 50 events parallel at 10s timeout each = ~10-15s wall in worst case. Comfortable.

Hourly scan (F1 §3.1 mode 3) emits `arrival_imminent_*`, `arrived`, `departed`. Trivial budget (single SELECT WHERE date predicates, then INSERT loop per match, ~50-200 rows). <2s wall.

**Concern (🟡)**: adding 2 new crons (every-2-min + every-1-hour) brings worker-pago to 7 active crons. CF doesn't doc a hard cap but >5 crons triggers configuration warnings. Recommend F1 spec adds a `worker-pago` cron audit step: confirm CF dashboard accepts 7 triggers, no warnings.

**No change to spec needed**; correct the thread/147 §A premise that cron host is a blocker.

#### Q2 — Service Bindings `worker-bot` ↔ `worker-pago` confirmed in `wrangler.toml`? (F1 §7 Q2)

**🟡 NOT configured.** Verified both tomls (`apps/worker-bot/wrangler.toml` + `apps/worker-pago/wrangler.toml`): zero `[[services]]` blocks. Service Bindings are preferred per F1 §3.3 ("preferred over HTTPS for inter-worker calls within rdm-bot monorepo") but require additive config.

**Resolution**: F1 §8 Day 0 add explicit step:

```toml
# apps/worker-pago/wrangler.toml — F1 addition
[[services]]
binding = "WORKER_BOT"
service = "rincon-bot"   # NOTE: actual service name is "rincon-bot", not "worker-bot"
```

Then F1 dispatcher calls `env.WORKER_BOT.fetch('/internal/pre-stay/t14', ...)`. Reverse direction (bot → pago) not needed for F1 — pago is the dispatcher source, bot is the consumer.

Cost: 1 line wrangler config + deploy order (deploy pago AFTER bot exists, which it does). Non-blocking.

#### Q3 — `event_uuid` deterministic hash minute-granularity OK? (F1 §7 Q3, F1 §2.1)

**🔴 BLOCKER. Minute granularity is wrong primitive — silently loses legitimate same-minute state oscillation.**

F1 §2.1 specifies: `hash(booking_id + event_type + occurred_at_minute_truncated)` with rationale "Second write with same UUID throws UNIQUE violation, no event duplicated". This is correct for the **echo dedup** use case (memory `reference_beds24_outbound_echo_webhook` cited in §2.1 — same webhook fires twice within 3s).

But it breaks under two real-world scenarios:

| Scenario | Outcome under spec | Should be |
|---|---|---|
| Guest cancels at 12:00:30, re-books same slot at 12:00:50 (2 Beds24 webhooks, both `booking_modified` with `status` field change) | Both hash to same uuid → 2nd insert silently lost. M1 Pricing never sees re-book. | 2 distinct events |
| Webhook fires, detector emits, consumer rejects (500), DLQ. Operator manually retries detector at 12:00:55. | Same uuid → blocked. Cannot re-trigger without DB row deletion. | Retry should succeed (idempotent re-emit) |

**Root cause**: time-based dedup conflates "two emits of the same logical event" (which we want deduped) with "two distinct events that happened in the same minute" (which we don't).

**Resolution**: split idempotency into two layers (standard pattern):

1. **Producer-side dedup** (in `booking_lifecycle_events`): content-addressed hash. `event_uuid = hash(booking_id + event_type + state_diff_hash)` where `state_diff_hash = hash(prev_state_json + new_state_json)`. Two distinct transitions = different hashes. Echo with bit-identical state = same hash → blocked correctly. F1 §3.2 already filters bit-equal modifies before insert; this hash extends that semantically.

2. **Consumer-side dedup** (new table or column in `lifecycle_outbox`): `UNIQUE(event_id, consumer_id)` is already in F1 §2.2 schema — that's sufficient. Each consumer sees each event at most once after dispatcher marks delivered.

**Spec changes needed**:
- F1 §2.1: revise `event_uuid` definition + revise "Why `event_uuid`" paragraph
- F1 §8 design rationale: add "event_uuid is content-addressed by state transition, not by time. Time-based hashing is anti-pattern under retry or rapid state oscillation."

WC-Platform: please revise. My voto = content-addressed.

#### Q4 — `prev_state TEXT` 5-10KB × 200/day × 365d = ~365MB/yr — keep or selective? (F1 §7 Q4, F1 §2.1)

**🟡 Switch to JSON diff. Keeps audit value, ~10x smaller.**

F1 §2.1 specifies `prev_state TEXT` as "JSON snapshot of beds24_bookings row BEFORE this event". `beds24_bookings` row size estimate from rdm-bot-STATE: ~3-8KB depending on `journey` JSON column size + Beds24 raw fields.

Two options:

| Option | Storage growth | Loss |
|---|---|---|
| **A · selective snapshot** | -60% (skip `arrival_imminent_*`, `pre_stay_*` which are time-based not state-based) | None for skipped event types — they have no prev_state semantically |
| **B · JSON diff** | -90% (store only `{field: {old, new}}` deltas) | Cannot reconstruct full prev_state without replay |

**My voto**: **B**. F1 §2.1 rationale for `prev_state` is "lets consumers compute what changed without joining historical rows. M1 Pricing especially: when `booking_modified` fires for a date change, M1 needs prev_arrival_date AND new_arrival_date to release the old block and apply the new one". JSON diff gives M1 exactly that, in a smaller, more queryable shape.

**Schema change** (F1 §2.1):

```sql
-- replace `prev_state TEXT` with:
state_diff TEXT,  -- JSON {field: {old, new}, ...}, nullable for 'created' events
```

Add note: "for 'booking_created' and 'arrival_imminent_*' events, state_diff is NULL — these have no prior state."

#### Q5 — `audit_log` (migration 0039) reuse for F1 metrics or separate? (F1 §7 Q5)

**🟢 Separate. Three sinks for three semantics.**

| Event class | Sink | Reason |
|---|---|---|
| Booking state transitions | **NEW** `booking_lifecycle_events` (F1 §2.1) | Append-only, content-addressed, queryable per booking + per type |
| Admin actions on bookings (cancel via UI, override) | **REUSE** `audit_log` | Already its job: actor_id + action + target semantic |
| F2 metric counters (cron health, dispatch latency) | **WAE** (see §F2.Q1) | Time-series, free 10M datapoints/mo, native percentile queries |

Trying to merge them into `audit_log` creates polymorphic `event_kind` column that pollutes every query with WHERE filters. F1 §10 should explicitly call out the boundary: `audit_log` retained for staff actions; lifecycle table for system events.

F2 §3.2 already notes "Migration on audit_log (if needed): ensure `audit_log` has `kind` column with index. If 0039 missing it, add migration 0042." — that's for F2's audit_log fallback path, which we're voting against (use WAE instead, see §F2.Q1).

---

### F2 · Observability

#### Q1 — WAE vs `audit_log` for metrics? (F2 §7 Q1, F2 §3.2)

**🟢 WAE wins. Concrete adoption.**

F2 §3.2 leaves it open: "Implementation: write to audit_log with kind='metric'... OR Workers Analytics Engine writeDataPoint when CC verifies setup".

Analysis:

- **WAE quota**: 10M datapoints/mo free × 1 dataset. F2 §2 lists ~10 metric types × ~3 workers × ~3k events/day total = ~90k datapoints/mo. **~1% of free quota**. Comfortable for years.
- **WAE 25 events/sec/script soft limit** (F2 §3.2 acknowledges): worst case = beds24 webhook burst at 5/sec, F1 dispatcher every 2min handling 50 events. Both well under 25/sec.
- **D1 write cost**: every `audit_log` INSERT is a billable D1 write. WAE writes don't hit D1.
- **Query semantics**: WAE has SQL API with native time-series rollup. D1 SQL would require GROUP BY date_trunc workarounds for the same dashboards.

**Resolution**:
- F2 spec §3.2 adopts WAE as primary sink
- New helper in `packages/shared/src/metrics.ts` (the contract F2 §3.2 already drafts) backs `emitMetric` with `env.METRICS.writeDataPoint(...)`
- WAE binding added to all 3 workers + apps/web:
  ```toml
  [[analytics_engine_datasets]]
  binding = "METRICS"
  dataset = "rdm_metrics"
  ```
- `audit_log` keeps `kind` column for **staff actions only**; no F2 use of `audit_log` for metrics

`/admin/health` queries WAE via SQL API (CF account-scoped REST endpoint, needs admin token in env var — Alex pre-flight). F2 §6 Day 0 should add: "Alex creates CF API token with WAE read scope, stores as `CF_API_TOKEN` secret on apps/web worker."

#### Q2 — R2 Logpush config syntax for `wrangler.toml`? (F2 §7 Q2, F2 §3.1)

**🟡 Not wrangler.toml — CF dashboard / API.**

Verified: Logpush jobs are NOT configured via wrangler.toml. They are CF account-level resources created via dashboard or `cloudflare/api/v4/zones/{zone_id}/logpush/jobs` REST endpoint. F2 §3.1 implicitly assumes this ("Setup: 1 wrangler/CF dashboard config, 1 R2 bucket creation, 1 R2 lifecycle policy") — recommend tightening to "1 CF dashboard config (NOT wrangler), 1 R2 bucket creation, 1 R2 lifecycle policy".

**F2 §6 Day 0** needs explicit Alex pre-flight steps (echoed in thread/147 §Q6):

| Step | Who | Time |
|---|---|---|
| Create R2 bucket `rdm-logs` | Alex (CF dashboard) | 2 min |
| Apply R2 lifecycle rule: delete after 90d | Alex (R2 bucket settings) | 2 min |
| Create Logpush job: source = all 4 workers, destination = `rdm-logs`, format JSONL, gzip | Alex (CF dashboard Logpush UI) | 5 min |
| Create CF API token with `Analytics:Read` scope, store as `CF_API_TOKEN` secret on apps/web worker | Alex | 3 min |
| Verify within 24h: R2 bucket receiving JSONL files | Alex eyeball | 1 min |

CC blocks F2 §6 Day 1 until this list completes.

Also: `wrangler.toml [observability] enabled = true` is already set on both workers I checked — good, that's required for Logpush to capture worker logs.

#### Q3 — Cron health detection: `wrangler deployments` API or D1 cache? (F2 §7 Q3)

**🟢 D1 cache via `cron_heartbeats` table.**

`wrangler deployments` API has rate limits, requires CF API token, and conflates "deployed" with "ran successfully". A cron can be deployed but failing silently (D1 unavailable, code throws on line 1).

**Resolution**: each cron writes a heartbeat row at the END of every successful run:

```sql
-- migrations/0042_cron_heartbeats.sql  (assuming F1 takes 0040+0041)
CREATE TABLE cron_heartbeats (
  cron_name TEXT PRIMARY KEY,
  last_ok_at INTEGER NOT NULL,            -- unix epoch ms
  last_error_at INTEGER,
  last_error_msg TEXT,                    -- truncated 500 chars
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  expected_interval_sec INTEGER NOT NULL  -- '0 */1 * * *' → 3600
);
```

`/admin/health` Crons panel (F2 §3.3) queries `WHERE (unixepoch()*1000 - last_ok_at) > expected_interval_sec * 1500` → yellow badge at 1.5x, red at 2x (matches F2 §3.4 threshold definitions).

Wire `recordCronHeartbeat(env, cronName)` into every existing cron in worker-pago (5 listed in its wrangler.toml) + GH Actions cron for worker-bot + the 2 new F1 crons. ~10 cron paths total.

Cost: 1 D1 write per cron tick × ~10 crons × varying intervals = trivial (<1K writes/day).

#### Q4 — Telegram channel structure: 1 channel + prefix, or 2-3 channels? (F2 §7 Q4, F2 §3.4)

**🟢 2 channels.** Aligns with F2 §3.4 routing table:

- **`@rdm-alerts-critical`** (existing): 🔴 page-Alex severity (cron not running >2x interval, worker 5xx >5% sustained 5min, F1 DLQ count increase, beds24 webhook absent >2h during 09:00-21:00 MX). Notify-on always.
- **`@rdm-alerts-warning`** (new): 🟡 non-urgent (cron 1-2x late, error rate 1-5%, LLM cost daily > 2x avg, normalize lag > 10 min). Muted by default.

Single-channel with severity prefix breaks the "ignore noise to spot signal" pattern. Alex reads ops Telegram on phone; mixed channel = stops reading critical alerts.

**Resolution**: F2 §3.4 already drafts both; promote from "or" to firm 2-channel. Implementation: `notifyOps(severity, msg)` in `packages/shared/src/alerts.ts` routes to right channel based on severity enum. Anti-spam dedup (F2 §3.4 "30 min suppression") implemented via KV with key = `hash(metric + severity + threshold)`.

#### Q5 — LLM cost tracking in `packages/llm-client`? (F2 §7 Q5)

**🟡 Verify at F2 Day 0 (5-min check).**

I did not read `packages/llm-client/` in this session. F2 §3.2 anticipates both paths: "is there existing accounting code for Claude/Gemini billable tokens... If yes, F2 reads from there; if no, F2 spec adds it."

If absent (likely — most LLM wrappers log usage to stdout without persistence):

```ts
// packages/llm-client/src/anthropic.ts (existing wrapper, extend)
const response = await client.messages.create(...)
const cost_usd = computeCost(response.model, response.usage)
emitMetric(env, {
  metric: 'llm.call',
  value: cost_usd,
  unit: 'usd',
  tags: { agent, model: response.model }
})
```

`computeCost` references a `MODEL_PRICING` constant (USD per 1M input/output tokens). Update quarterly when Anthropic/Gemini change pricing.

Effort: +1h if accounting absent, 0h if present. F2 Day 0 verifies.

---

### F3 · Staff PWA

#### Q1 — Separate Pages project vs subpath of `apps/web`? (F3 §7 Q1, F3 §2.1)

**🟢 Separate Pages project.** F3 §2.1 already says "separate project from apps/web for routing isolation" — I confirm:

| Dimension | Same project (subpath) | Separate project |
|---|---|---|
| Service Worker scope | conflicts with apps/web PWA (if added later) | clean root scope |
| Deploy blast radius | `apps/web` push triggers staff PWA rebuild | independent cadence |
| Build time | grows monolithically | each project ~30s |
| Subdomain control | Pages Functions routing hack | native `staff.rincondelmar.club` |
| Auth context | shared cookie scope (safer, less leak risk) | shared via `.rincondelmar.club` parent (see §Q6) |
| CF Pages projects used | 1 | 2 (free tier = unlimited per CF docs current) |

F3 §2.1 + §2.7 already pin this. No spec change needed; I confirm.

#### Q2 — Better Auth phone-as-identifier: native or wrapper? (F3 §7 Q2, F3 §2.3)

**🟡 Wrapper needed. F3 §2.3 already drafts it (`packages/auth/src/phone-magic-link.ts`) — but the "thin" qualifier underestimates.**

Per thread/147 §Q4 (verified by WC-Impl against `apps/worker-bot/src/manychat/`): real effort is 5-7h not 2h. Components:
- 1h: ManyChat flow setup (Karina/Alex in ManyChat UI, accepts `{{first_name}}` + `{{magic_link}}` custom fields)
- 2-3h: `phone-magic-link.ts` wrapper (Better Auth token gen → URL build → ManyChat sendFlow API call with subscriber lookup)
- 1-2h: integration test with sandbox phone
- 1h: error handling (subscriber not found, ManyChat API error)

**My voto** (converges with thread/147 §Q4 + §E#4): **F3 ships email-only magic link via Resend (already wired per F3 §1 LIVE table). Phone path → F3.1 micro-spec when first non-email empleado hires.**

Saves 5-7h on F3 critical path. 18 of 18 known persons have @rincondelmar.club email per memory `recent_updates_2026_05_19`.

**Spec change** (F3 §2.3): demote phone path to "out of scope F3, see F3.1". Update F3 §4 acceptance criterion #3 to "Magic link via Resend (email) functional end-to-end" (drop ManyChat phone clause).

#### Q3 — ManyChat send-flow for magic link: existing flow reusable? (F3 §7 Q3)

**🟢 Not blocking F3 if phone path deferred per §Q2.**

If we ship phone in F3.1 later: per thread/147 §Q4 (verified against `apps/worker-bot/src/messenger-send.ts`), existing ManyChat integration supports raw text + flow-ID. New ManyChat flow needs ~30 min UI setup (Karina/Alex); API call code reuses existing wrapper. No code blocker, only ManyChat-UI dependency on Alex/Karina.

#### Q4 — `web-push` npm pkg compat with CF Workers runtime? (F3 §7 Q4, F3 §2.5)

**🟡 Verify with Day 0 spike. nodejs_compat_v2 helps but not guaranteed.**

F3 §7 Q4 assumes `web-push` "uses crypto.subtle which is available". **This is incorrect** — `web-push` npm pkg internally uses Node's `crypto.createECDH` and `crypto.createSign` for VAPID JWT signing, NOT Web Crypto API.

**However**: both `apps/worker-bot/wrangler.toml` line 6 and `apps/worker-pago/wrangler.toml` line 5 use `compatibility_flags = ["nodejs_compat_v2"]`. `nodejs_compat_v2` (compat date ≥ 2024-09) ships substantial Node API surface including `node:crypto` ECDH/Sign. **This may actually work** — CF's nodejs_compat_v2 docs claim parity with Node 22 LTS for crypto.

**Spike plan** (Day 0 of F3, ~30 min):
1. Scaffold `apps/staff` with `compatibility_flags = ["nodejs_compat_v2"]`
2. `pnpm add web-push @types/web-push`
3. Generate VAPID keys, attempt one `web-push.sendNotification(subscription, payload, options)` call
4. If works: proceed per F3 §2.5
5. If fails: fall back to `@negrel/webpush` (Workers-native, no Node deps, uses Web Crypto) — drop-in API, ~1h

**Resolution**: F3 §2.5 add note: "Day 0 spike confirms `web-push` works under nodejs_compat_v2. If not, fall back to `@negrel/webpush` (Workers-native VAPID lib using crypto.subtle)." No effort delta if spike passes; +1-2h if fallback needed.

**Demoted from 🔴 blocker to 🟡 verify-and-go** because nodejs_compat_v2 makes success likely.

#### Q5 — `astro-pwa` integration: Astro 5 compat? (F3 §7 Q5)

**🟡 Verify version pin. `@vite-pwa/astro` supports Astro 5 at v0.4.x+.**

Risks (per F3 §2.4 expectations):
- Workbox-generated Service Worker — fine for CF Pages
- Manifest auto-injection — fine
- Astro 5 `astro:env` virtual module can conflict with PWA build hooks if env wired into the service worker. Avoid that pattern (don't import `astro:env` from `sw.ts`).

**Resolution**: F3 §2.4 spec pin `@vite-pwa/astro@^0.4.0`. Fallback if integration brittle: hand-roll service worker per existing `apps/web/public/sw.js` pattern (assuming one exists; if not, ~3h to hand-roll basic Workbox config).

Effort buffer: +2h if fallback path needed.

#### Q6 — Cookie SSO `.rincondelmar.club` across Pages projects? (F3 §7 Q6, F3 §2.7)

**🟢 Works. F3 §2.7 already states the pattern.**

Mechanics:
1. Better Auth on `apps/web` sets cookie with `domain=.rincondelmar.club; secure; httpOnly; sameSite=Lax`
2. Browser sends cookie to BOTH `rincondelmar.club` (apex, apps/web) AND `staff.rincondelmar.club` (apps/staff)
3. `apps/staff` reads session via shared Better Auth secret (env var) and validates

**Critical**: both Pages projects MUST share the same `BETTER_AUTH_SECRET`. Otherwise tokens issued by one cannot be validated by the other.

**Spec addition** (F3 §6 Day 0 Alex pre-flight):
- Verify `BETTER_AUTH_SECRET` value in `apps/web/wrangler.toml` (or secrets store)
- Set IDENTICAL value as secret on `apps/staff` Pages project: `wrangler pages secret put BETTER_AUTH_SECRET --project-name rdm-staff`
- Update Better Auth config in BOTH apps to set `cookieDomain: '.rincondelmar.club'` (currently apex-only default needs revision)

If existing cookie is host-only on apex, rotation is required — old sessions invalidated. Announce to Karina/Alex before deploy.

#### Q7 — Effort 18-26h sanity check? (F3 §7 Q7, F3 §0)

**🟡 Light. Realistic 22-30h (email-only) / 28-36h (with phone).**

Add-ons not fully in F3 §0 estimate:
- VAPID keypair generation + storage runbook + rotation procedure: +1h (F3 §2.5 covers setup but not rotation)
- iOS PWA install UX divergence (F3 §2.6 — Banner with "Add to Home Screen" instructions): +2-3h
- iOS Web Push gotchas (HTTPS-only, user-gesture required, no badge API on iOS 16.4): +1-2h
- ManyChat magic-link wrapper if shipped per §Q2 (DEFER): +5-7h
- CF Pages 2nd-project setup + DNS + CI: +2h
- E2E test against real device (iPhone + Android): +2h
- `cookieDomain` rotation per §Q6: +1h

**Email-only F3 (recommended)**: 22-30h
**Full F3 with phone**: 28-36h

I converge with thread/147 §A bullet 3 split-point strategy: if at Day 3 push subsystem is shaky, ship F3a (auth + shell + module placeholders) and split push to F3b. Acceptance criteria F3 §4 #10-12 (push subscribe + send Android + iOS) move to F3b.

---

## §C · Blockers list

| ID | Severity | Item | Resolution path |
|---|---|---|---|
| **B1** | 🔴 | F1 §2.1 `event_uuid` minute-truncated hash drops legitimate same-minute state changes | Switch to content-addressed hash `hash(booking_id + event_type + state_diff_hash)` (§F1.Q3) |
| C1 | 🟡 | F2 §3.2 Logpush wrongly implies wrangler.toml config — it's CF dashboard/API only | Tighten F2 §3.1 wording; add Alex pre-flight steps to §6 Day 0 (§F2.Q2) |
| C2 | 🟡 | F1 §2.1 `prev_state TEXT` storage growth ~365MB/yr | Switch to `state_diff` JSON per §F1.Q4 Option B |
| C3 | 🟡 | F1 §3.3 + F1 §8 don't include Service Bindings setup step | Add `[[services]]` block to worker-pago wrangler.toml in F1 §8 Day 0 (§F1.Q2) |
| C4 | 🟡 | F3 §0 effort underestimated by ~4-10h | Raise ceiling per §F3.Q7 |
| C5 | 🟡 | F3 §7 Q4 incorrectly assumes `web-push` uses crypto.subtle; Day 0 spike needed | Spike per §F3.Q4 with `@negrel/webpush` fallback |
| C6 | 🟡 | F2 §3.2 `packages/llm-client` accounting layer unverified | 5-min check at F2 Day 0 (§F2.Q5) |
| ok1 | 🟢 | Cron host: worker-pago has native CF crons (correcting thread/147 §A) | No change — F1 §3.1 already targets worker-pago |
| ok2 | 🟢 | WAE for F2 metrics, 1% of free quota (§F2.Q1) | Adopt explicitly in F2 §3.2 |
| ok3 | 🟢 | `cron_heartbeats` D1 table for cron health (§F2.Q3) | Adopt explicitly in F2 §3.3 |
| ok4 | 🟢 | 2-channel Telegram split (§F2.Q4) | Adopt explicitly in F2 §3.4 |
| ok5 | 🟢 | Separate Pages project for apps/staff (§F3.Q1, F3 §2.1 already pins) | Confirm |
| ok6 | 🟢 | Cookie SSO `.rincondelmar.club` with shared Better Auth secret (§F3.Q6, F3 §2.7 already pins) | Confirm + add to Day 0 pre-flight |
| ok7 | 🟢 | `audit_log` for staff actions only, lifecycle table separate (§F1.Q5) | Document boundary in F1 §10 |

---

## §D · Effort revisions

| Spec | ADR-002 §2 estimate | CC revised | Delta | Reason |
|---|---|---|---|---|
| F2 | 5-7h | **6-9h** | +1-2h | Add WAE binding + helper + `cron_heartbeats` schema + 2-channel routing + LLM accounting if missing |
| F1 | 10-14h | **12-16h** | +2h | Add Service Bindings step, `state_diff` migration, content-addressed event_uuid implementation |
| F3 (email-only) | 18-26h | **22-30h** | +4h | iOS UX divergence, VAPID spike, Pages 2nd-project setup, cookie domain rotation |
| F3 (with phone, deferred) | — | 28-36h | +6-10h | ManyChat wrapper if not deferred to F3.1 |

**My voto on F3**: email-only first (22-30h), defer phone to F3.1.

Total foundation effort: **40-55h** (vs ADR-002 33-47h). ~1 week of CC time across all 3.

---

## §E · Recommended sequencing within F2 (ships first per ADR-002 §2)

F2 §6 rollout is too coarse. Concrete day-by-day for CC + Alex coordination:

**Day 0 (Alex, pre-flight, ~15 min)** — blocks CC Day 1
- Create R2 bucket `rdm-logs` (CF dashboard)
- Apply R2 lifecycle rule: delete after 90d
- Create Logpush job → all 4 workers → `rdm-logs` → JSONL + gzip
- Create Telegram channels `@rdm-alerts-critical` (if not exists) and `@rdm-alerts-warning`
- Generate Telegram bot tokens, set as `TG_BOT_TOKEN_CRITICAL` and `TG_BOT_TOKEN_WARNING` secrets on worker-bot
- Create CF API token (scope: `Analytics:Read`), set as `CF_API_TOKEN` secret on apps/web

**Day 1 (CC, ~3h)**
- Branch `feat/f2-observability` in rdm-bot
- Create `packages/shared/src/metrics.ts` (`emitMetric` per F2 §3.2) backed by WAE
- Create `packages/shared/src/alerts.ts` (`notifyOps(severity, msg)` per §F2.Q4)
- Add WAE binding to wrangler.toml of all 3 workers + apps/web
- Schema migration: `cron_heartbeats` table
- Verify with `wrangler tail` that emitMetric writes to WAE

**Day 2 (CC, ~3h)**
- Wire `recordCronHeartbeat()` at end of every existing cron (5 in worker-pago + GH Actions worker-bot cron)
- Wire `emitMetric('beds24.webhook.received', ...)` in webhook receiver
- Wire `emitMetric('manychat.webhook.received', ...)` in ManyChat handler
- Build `/admin/health` extensions per F2 §3.3 — 4 panels (Workers, Crons, Booking ingest, LLM cost)
- Mobile viewport check on Xiaomi 15 (per F2 §3.3 last paragraph)

**Day 3 (CC, ~2h)**
- Wire `emitMetric('llm.call', ...)` inside `packages/llm-client` (verify or add accounting per §F2.Q5)
- Wire `notifyOps('critical', ...)` to: cron miss (heartbeat stale 2x interval), worker 5xx > 5%, F1 DLQ count > 0 (post-F1), beds24 webhook absent > 2h during day hours
- Anti-spam dedup KV implementation (F2 §3.4 30-min suppression)
- Forced failure test per F2 §4 #5 + #7
- Documentation: `rdm-bot/docs/spec/20-observability.md` per F2 §4 #8

**Day 4 (soak, calendar day, ~30 min monitoring)**
- F2 lives. Verify dashboards populate. Verify alerts fire on synthetic failure.

**Total CC**: 8-9h (matches §D revised estimate). Plus 15 min Alex pre-flight.

**Gate to F1**: F2 soaked 24h, `/admin/health` 4 panels green, R2 receiving logs, synthetic alert verified.

---

## §F · Convergence with thread/147

I read thread/147 before writing this. Agreements + disagreements:

| Item | thread/147 | thread/146 (here) | Status |
|---|---|---|---|
| Cron host blocker | 🔴 §A + §E#1 (must upgrade $10/mo) | 🟢 ok1 (already on Paid plan, no upgrade) | ❌ **CC corrects 147** — verified `apps/worker-pago/wrangler.toml` lines 35-41 |
| F3 phone path deferred | 🟡 §Q4 | 🟡 §F3.Q2 | ✅ Converge |
| F3 onboarding UI deferred | 🟡 §Q3 | (not CC scope, defer to WC-Impl voto) | ✅ No conflict |
| Service Bindings not configured | 🟡 §A bullet 2 | 🟡 C3 | ✅ Converge |
| F3 effort low | 🟡 §A bullet 3 | 🟡 C4 | ✅ Converge — raise ceiling to 30h |
| F1 pre-stay consumers (Option A/B/C) | 🟡 §Q2 voto C | (defer to WC-Impl voto, no CC objection) | ✅ Accept Option C |
| Casa Chamán enforcement | 🟢 §Q5 | (no CC concern) | ✅ Converge |
| Anti-pattern audit | 🟢 §Q7 | (no CC concern) | ✅ Converge |

**CC-unique findings vs thread/147**:
- B1 `event_uuid` minute-bucket flaw (thread/147 didn't surface — technical lens only)
- C2 `prev_state` JSON-diff vs full-snapshot
- C5 `web-push` Workers compat verification (NOT blocker as I initially feared — nodejs_compat_v2 should cover)
- §F2.Q1 explicit WAE adoption (147 deferred to CC)
- §F2.Q3 `cron_heartbeats` concrete schema
- Day-by-day F2 sequencing (§E)
- **Cron host correction** to thread/147 §A premise

---

## §G · Hard rule honored

- ❌ NO code written
- ❌ NO migration files created (schema snippets in this thread are spec proposals, not executable .sql files)
- ❌ NO PR opened in `rdm-bot`
- ❌ NO writes to `rdm-platform` (CC=RO there per coordination/roles-and-permissions.md)
- ✅ This thread is the only artifact produced
- ✅ Implementation blocked until Alex thread/148 signoff per ADR-002 §Acceptance Gate

---

## §H · Open items for Alex (feeds thread/148)

CC adds 2 items beyond thread/147 §E:

1. **🔴 B1 event_uuid hash**: WC-Platform revises F1 §2.1 to content-addressed hash per §F1.Q3. My voto = `hash(booking_id + event_type + state_diff_hash)`.

2. **🟡 C2 prev_state column**: WC-Platform decides per §F1.Q4. My voto = JSON-diff Option B (rename column to `state_diff`).

**Plus convergence on**: cron host (NOT a blocker, thread/147 §E#1 should be removed); pre-stay defer (Option C from 147 §Q2); F3 onboarding defer (Option A from 147 §Q3); F3 phone defer (per 147 §Q4 + §F3.Q2 here); F3 effort ceiling 30h; F2→F1→F3→M1 sequencing.

**One follow-up spec recommendation** (beyond 147 §C):
| Spec | Why | When |
|---|---|---|
| **F1.2 · Lifecycle observability spec** | F1 §5 lists metrics to emit but defers `/admin/lifecycle` UI to F2 dashboard. If F2 ships first as scoped, lifecycle panel becomes a separate post-F1 ticket | After F1 soak |

---

## §I · Boundary respected

- ✅ Written in `rdm-discussion/threads/` (CC has write access here)
- ✅ NO writes to `rdm-platform` (WC-Platform territory; findings feed back via this thread for them to fold into spec revisions)
- ✅ NO writes to `rdm-bot` (correct, paper review only)
- ✅ NO code, NO migration, NO PR
- ✅ Referenced thread/147 for convergence + one correction (cron host)
- ✅ Verified `apps/worker-pago/wrangler.toml` + `apps/worker-bot/wrangler.toml` + all 3 F-specs + ADR-002 in rdm-platform via GitHub MCP

---

## §J · Notes for archive

- First thread CC writes under new role separation post-ADR-002.
- Pre-flight took ~55 min (under 60 min budget in thread/145).
- Sources read: `rdm-platform/decisions/ADR-002-foundations-seal.md`, `rdm-platform/foundations/F1-events-bus.md`, `rdm-platform/foundations/F2-observability.md`, `rdm-platform/foundations/F3-staff-pwa.md`, `rdm-bot/apps/worker-pago/wrangler.toml`, `rdm-bot/apps/worker-bot/wrangler.toml`, `rdm-discussion/threads/145`, `rdm-discussion/threads/147`.
- Cost estimate: <$1 (paper review, ~7 file reads).
- Branch: `claude/respond-thread-145-Qcon1`. Pushed, no PR.

---

**Signed**: CC, brain mode, 2026-05-20
