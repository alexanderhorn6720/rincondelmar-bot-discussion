# Thread 148 · Alex · Foundations Seal decision · ADR-002 → Accepted

**From**: Alex
**To**: WC-Platform + WC-Implementation + CC
**Re**: ADR-002 §Acceptance Gate, thread/146 + thread/147 reviews
**Date**: 2026-05-20
**Status**: ✅ **GO** — ADR-002 moves Proposed → Accepted. Implementation starts with F2.

---

## §A · Vote summary

Voted go on all 12 items per WC-Platform synthesis. Both reviews (146 CC, 147 WC-Impl) read in full. Convergence is strong, the one divergence (cron host) was decided by CC's evidence-based correction.

| # | Decision | Vote | Source |
|---|---|---|---|
| 1 | 🔴 `event_uuid` → content-addressed hash | ✅ Go | CC 146 §F1.Q3 |
| 2 | 🟡 `prev_state` → `state_diff` JSON-diff | ✅ Go | CC 146 §F1.Q4 Option B |
| 3 | 🟡 `web-push` Day 0 spike + `@negrel/webpush` fallback | ✅ Go | CC 146 §F3.Q4 |
| 4 | 🟡 F1 pre-stay → Option C (defer migration to F1.1) | ✅ Go | WC-Impl 147 §Q2, CC 146 converged |
| 5 | 🟡 F3 onboarding → Option A (Alex provisions via wrangler.toml) | ✅ Go | WC-Impl 147 §Q3, CC 146 converged |
| 6 | 🟡 F3 phone path → email-only F3, F3.1 for phone | ✅ Go | WC-Impl 147 §Q4, CC 146 §F3.Q2 |
| 7 | 🟡 F3 effort ceiling → 22-30h email-only | ✅ Go | Both converged |
| 8 | 🟢 Cron host → NO Workers Paid upgrade (worker-pago already on Paid) | ✅ Go | CC 146 §F1.Q1 (corrects 147 §A) |
| 9 | 🟢 F2 metrics → WAE primary | ✅ Go | CC 146 §F2.Q1 |
| 10 | 🟢 Sequencing F2 → F1 → F3 → M1 | ✅ Go | Both confirmed |
| 11 | 🟢 Charter decoupled | ✅ Go | ADR-002 §3 |
| 12 | Follow-up specs (F1.1 pre-stay, F1.2 lifecycle UI, F3.1 phone, F3.2 onboarding UI) | ✅ Acknowledged | When triggers hit |

---

## §B · Resolution of the cron host divergence

Thread/147 §A + §E#1 flagged this as 🔴 BLOCKER requiring $10/mo Workers Paid upgrade.

Thread/146 §F1.Q1 + §F (Convergence table) corrected the premise by reading `apps/worker-pago/wrangler.toml` lines 35-41 directly and confirming worker-pago **already has 5 native CF crons running**, which only Workers Paid plan allows. The Free-plan + GH Actions workaround in thread/147 applies to **worker-bot only**, not worker-pago.

**Decision**: NO upgrade needed. F1 dispatcher every-2-min + hourly scanner ride on worker-pago. WC-Platform F1 spec §3.1 already targets worker-pago — spec is correct as written.

WC-Impl: when revising your operational picture going forward, please verify wrangler.toml state via MCP rather than assuming. Same lesson I'm learning when WC-Platform invented gaps that didn't exist (per the spec-rewrite earlier in this conversation).

**Update 2026-05-24**: Alex upgraded the WHOLE account to Workers Paid plan ($5/mo) during F2 pre-flight execution (see §H below). Worker-bot can now use native crons too, eliminating the GH Actions workaround mentioned above. F1 dispatcher can definitively use native cron on worker-pago.

---

## §C · What happens next

### Step 1 — WC-Platform revises 4 specs in rdm-platform (this session)

Per WC-Platform synthesis, the following changes land in this same session via additional MCP commits:

**F1-events-bus.md**:
- §2.1: `event_uuid` definition becomes content-addressed: `hash(booking_id + event_type + state_diff_hash)` where `state_diff_hash = hash(prev_state_json + new_state_json)`. Rationale revised: "two distinct transitions = different hashes; echo with bit-identical state = same hash → blocked correctly".
- §2.1: rename `prev_state TEXT` → `state_diff TEXT`, JSON object `{field: {old, new}, ...}`, NULL for `booking_created` + `arrival_imminent_*`. Storage est revised: ~30-50MB/yr (~10x smaller).
- §3.3: pre-stay consumers (`pre_stay_t14/t7/t1`, `manychat_sync`) `enabled: false` in initial F1; F1.1 spec carries migration.
- §3.3: Service Bindings setup explicit in §8 Day 0:
  ```toml
  # apps/worker-pago/wrangler.toml addition
  [[services]]
  binding = "WORKER_BOT"
  service = "rincon-bot"
  ```
- §4: `event_uuid` mechanism revised in dispatcher dedup discussion.
- §6 AC #6: "pre-stay consumers wired" → "pre-stay consumers registered with `enabled: false`; migration covered by F1.1".
- §8 Day 0: add Service Bindings step.
- §10: add "audit_log boundary" note (staff actions in audit_log, system events in lifecycle table).
- §0: effort revised 10-14h → 12-16h.

**F2-observability.md**:
- §3.1: tighten Logpush wording — "1 CF dashboard config (NOT wrangler), 1 R2 bucket creation, 1 R2 lifecycle policy".
- §3.2: WAE adopted as primary metrics sink, audit_log reserved for staff actions. Concrete wrangler binding:
  ```toml
  [[analytics_engine_datasets]]
  binding = "METRICS"
  dataset = "rdm_metrics"
  ```
- §3.3: add `cron_heartbeats` D1 schema (CC 146 §F2.Q3 verbatim).
- §3.4: 2 Telegram channels firm (was "or") — `@rdm-alerts-critical` + `@rdm-alerts-warning`. 30-min KV dedup spelled out.
- §6: rewrite as Alex pre-flight checklist (Day 0) + CC day-by-day (Days 1-4) per CC 146 §E sequencing.
- §0: effort 5-7h → 6-9h.

**F3-staff-pwa.md**:
- §0: effort 18-26h → 22-30h (email-only path).
- §2.3: phone path demoted to "out of scope F3, see F3.1". Magic link path becomes email-only via Resend.
- §2.5: add note about `web-push` Day 0 spike, with `@negrel/webpush` fallback procedure.
- §2.7: explicit `cookieDomain: '.rincondelmar.club'` requirement on BOTH apps/web AND apps/staff Better Auth config. Note that existing apps/web sessions may need rotation.
- §3.2: onboarding flow clarified — Alex provisions via wrangler.toml env vars, no admin UI in F3 (F3.2 spec covers later).
- §4 AC #3: "Magic link via Resend (email) functional end-to-end". AC #10-12 (push) marked "Day-0 spike required before guaranteeing".
- §6 Day 0: explicit Alex pre-flight (DNS, CF Pages project, `BETTER_AUTH_SECRET` mirror, VAPID keys).
- §7: Q4 + Q5 answers folded into spec body (web-push compat verified path, astro-pwa pinning).

**ADR-002**:
- §4: add "F1 includes Service Bindings setup as additive wrangler change".
- §Acceptance gate: mark satisfied — 146 + 147 + 148 done.
- Status header: Proposed → **Accepted (2026-05-20)**.
- Add §10 "Implementation triggers" linking to:
  - F1.1 (post-F1 soak): pre-stay migration to lifecycle bus
  - F1.2 (post-F1 ship): `/admin/lifecycle` UI panel
  - F3.1 (when first non-email empleado hires): phone magic-link path
  - F3.2 (when hiring cadence > 1/mo): `/admin/staff-onboarding` UI

### Step 2 — Alex pre-flight for F2 (≤ 20 min, CF dashboard work)

Before CC starts F2 Day 1 code work, I commit to completing per CC 146 §E Day 0 checklist:

| Step | Detail | Time |
|---|---|---|
| 1 | Create R2 bucket `rdm-logs` | 2 min |
| 2 | R2 lifecycle rule: delete after 90 days | 2 min |
| 3 | Logpush job: 4 workers → `rdm-logs` → JSONL + gzip | 5 min |
| 4 | Create or verify Telegram channels `@rdm-alerts-critical` + `@rdm-alerts-warning` | 3 min |
| 5 | Telegram bot tokens as `TG_BOT_TOKEN_CRITICAL` + `TG_BOT_TOKEN_WARNING` secrets on worker-bot | 3 min |
| 6 | CF API token (scope: `Analytics:Read`) as `CF_API_TOKEN` secret on apps/web | 3 min |

When done, I post a follow-up in this same thread (148) with ✅ per step. CC blocks on that confirmation.

### Step 3 — CC ships F2 (6-9h CC time, 3-4 calendar days)

Sequence per CC 146 §E. F2 lives, soaks 24h on `/admin/health` 4 panels + R2 receiving + synthetic alert verified.

### Step 4 — Confirm PR queue cleared before F2 starts

Per WC-Impl 147 §Q1: PR #130 and PR #114 should clear from open queue first.
- PR #130 (A6 reglas adicionales): merge or close before F2 Day 1
- PR #114 (journey templates editor 3042 LOC): merge, revise, or close — sitting open creates merge-conflict risk

Estimated 1-2 calendar days. WC-Implementation owns this gate.

### Step 5 — CC ships F1 (12-16h)

Begins after F2 soak day done. Sequence per F1 §8 (revised). M1 Pricing brain session by WC-Platform can run in parallel during this window.

### Step 6 — CC ships F3 (22-30h, email-only)

Sequence per F3 §6 (revised). Alex pre-flight checklist for F3 (DNS + CF Pages + BETTER_AUTH_SECRET mirror + VAPID keys) commits in advance.

### Step 7 — M1 Pricing implementation kickoff

ADR-002 §2 #4: M1 starts the day F3 merges. WC-Platform spec ready by then.

---

## §D · Calendar (target, not commitment)

```
Week 1 (2026-05-19 → 2026-05-25)
├─ WC-Platform revises F1/F2/F3/ADR-002 specs (this session, ~1h)
├─ Alex pre-flight F2 (≤20 min, CF dashboard)
├─ PR #130 + #114 clear queue
└─ CC starts F2

Week 2 (2026-05-26 → 2026-06-01)
├─ F2 soak day + verification
├─ CC starts F1 (Service Bindings + state_diff + content-addressed event_uuid)
└─ WC-Platform M1 brain session (in parallel)

Week 3 (2026-06-02 → 2026-06-08)
├─ F1 soak day
├─ Alex pre-flight F3 (DNS, Pages, secrets)
└─ CC starts F3 email-only

Week 4 (2026-06-09 → 2026-06-15)
├─ F3 soak day
├─ M1 spec finalized (WC-Platform)
└─ M1 implementation kickoff (CC)

Total ~3 weeks foundations + week 4 M1 start.
```

---

## §E · Boundary respected

- ✅ This thread is the only artifact I produce here. Decision document, not implementation.
- ✅ Spec revisions land in `rdm-platform` (WC-Platform territory) via additional commits this session.
- ✅ No writes to `rdm-bot` (CC territory until they pick up F2).
- ✅ No new ADR needed — ADR-002 status flips from Proposed to Accepted in same file.

---

## §F · One direct note to each peer

**WC-Implementation (thread/147 author)**: thank you for the operational review. The cron host miscall is a useful reminder for all of us (myself included from earlier today): verify wrangler.toml state via MCP before assuming infrastructure constraints. Your other findings (Karina onboarding reality, ManyChat magic-link real effort, PR queue sequencing) are exactly what I needed from operational lens.

**CC (thread/146 author)**: technical pre-flight was thorough and the `event_uuid` flaw catch is the kind of thing that would have shipped silently and caused incidents in 6 months. That single catch justifies the entire review process. Also the cron host correction with file evidence — that's how technical disagreements should resolve.

**WC-Platform**: thank you for the synthesis and for making the boundary visible (you write specs, you don't write threads here unless announcing). Specs were good enough that both reviewers had concrete things to push back on; that's the right level of detail for paper review. Now revise the 4 specs per §C Step 1 and we're done.

---

## §G · ADR-002 status flip

Per ADR-002 §Acceptance Gate:

1. ✅ CC pre-flight in thread/146
2. ✅ WC-Impl review in thread/147
3. ✅ Alex decision in thread/148 (this thread)

**Status**: `Proposed` → `Accepted (2026-05-20)`. WC-Platform updates the header in ADR-002 file as part of spec revision pass.

CC: begin F2 Day 1 when (a) WC-Platform spec revisions land in rdm-platform main, AND (b) Alex pre-flight checklist completed and posted in this thread, AND (c) PR queue cleared (WC-Impl signals).

---

**Signed**: Alex, 2026-05-20

via WC-Platform on behalf, with explicit Alex approval on all 12 items per session 2026-05-20.

---

## §H · Pre-flight F2 COMPLETE (2026-05-24, via WC-web)

Alex executed pre-flight checklist in real-time session with WC-web. Result: all 6 steps satisfied, with deviations from original spec noted below. Audit trail in `thread/190` (WC MCP audit) + `thread/194` (CC wrangler CLI supplement) + this section.

### Step-by-step result

| # | Spec Step | Status | Actual outcome |
|---|---|---|---|
| 1 | Create R2 bucket `rdm-logs` | ✅ DONE (pre-existing 2026-05-21) | Bucket already existed from earlier work. **Deviation**: Logpush wizard created additional `cloudflare-managed-90a63a4b` bucket via one-click setup (Mar 2025 feature). F2 spec §3.1 path reference needs update to point to the auto-managed bucket. |
| 2 | R2 lifecycle 90d | ✅ DONE 2026-05-24 | Applied `delete-logs-after-90d` rule on `cloudflare-managed-90a63a4b` bucket (the active Logpush destination). Note: `rdm-logs` bucket from original spec is now unused, free for other purposes. |
| 3 | Logpush job 4 workers → R2 | ✅ DONE 2026-05-24 | Created via Logpush wizard one-click setup. Dataset: Workers Trace Events. Destination: R2 `cloudflare-managed-90a63a4b`. Folder organization: daily subfolders (e.g. `20260524/`). Logs flowing within minutes of creation. |
| 4 | TG channels critical + warning | ✅ DECIDED Opción 1 | Alex chose to **reuse 1 existing Telegram channel** with severity prefix emoji (🚨 for critical, ⚠️ for warning) instead of splitting into 2 channels. Mitigation: F2.1 micro-spec can split later if warning volume becomes noise (~30 min CC work). F2 spec §3.5 `notifyOps()` helper requires minor update to use single `TG_BOT_TOKEN` + `TG_CHAT_ID_ALERTS`. |
| 5 | TG bot tokens as secrets | ✅ REUSE existing | `TG_BOT_TOKEN` already provisioned on worker-bot AND worker-pago (per thread/194 §A.3 CC audit). No new secrets needed. With single-channel decision from Step 4, `TG_CHAT_ID_ALERTS` is the only secret needed if not already present (CC verifies during F2 Day 1). |
| 6 | CF_API_TOKEN scope Analytics:Read | ✅ DONE 2026-05-24 | Created custom API token `rdm-analytics-read` with single permission `Account → Account Analytics → Read`. TTL: forever. Provisioned via `wrangler pages secret put CF_API_TOKEN --project-name rincondelmar-bot`. Confirmed in `wrangler pages secret list` output. |
| 7 | Verify R2 receiving 24h post-deploy | ⏳ PENDING | Standard post-deploy eyeball check. Not blocking F2 Day 1. |

### Additional pre-flight outcomes (not in original checklist)

| Item | Status | Notes |
|---|---|---|
| **Workers Paid plan upgrade** | ✅ DONE 2026-05-24 | Alex upgraded account from Workers Free to Workers Paid ($5/month) to enable Logpush. **Side benefits**: unlimited cron triggers (vs 5 cap), Service Bindings now available (F1 §3.4 unblocked), 50ms CPU per request (vs 10ms). This eliminates the GH Actions workaround referenced in §B for worker-bot crons — F1 dispatcher can use native cron on worker-pago. |
| **Yolo B Liberal settings.json** | ✅ DONE 2026-05-24 | Applied across rdm-bot, rdm-discussion, rdm-platform repos. Active for next CC sessions. Deny list preserved for destructive operations (rm -rf, force-push, wrangler delete, DROP/TRUNCATE/DELETE FROM, .env/.ssh files). |
| **PR #18 (F1 spec) merged** | ✅ 2026-05-24 | Alex vote applied: NNNN placeholder + dual-path soak + cron count verification. WC-Platform follow-up: §6 patch to canonical F1 spec in rdm-platform. |
| **PR #19 (F3 spec) merged** | ✅ 2026-05-24 | Alex vote applied: separate user_roles table + VAPID rotation + `/yo/instalar` page + Alex coordinates Karina re-login in person (NOT 24h pre-deploy comms). WC-Platform follow-up: §7 patch to canonical F3 spec in rdm-platform. |

### Open spec amendments for WC-Platform to apply post-pre-flight

1. **F2 §3.1**: Update Logpush destination from `rdm-logs` → `cloudflare-managed-90a63a4b` (or note "destination bucket auto-managed by CF Logpush wizard, name varies"). 
2. **F2 §3.5 + §6.4/5**: Update Telegram routing to use single `TG_BOT_TOKEN` + `TG_CHAT_ID_ALERTS` with severity prefix emoji, per Alex Opción 1 decision. Drop `TG_BOT_TOKEN_CRITICAL/WARNING` + 2-channel split. F2.1 micro-spec can split later if needed.
3. **F1 §3.1**: Per Workers Paid upgrade, dispatcher can use native cron on worker-pago without GH Actions workaround. Spec already targets worker-pago — confirm and remove any "if Workers Free" conditionals.

These amendments are non-blocking for F2 Day 1. CC works against amended spec; WC-Platform applies in parallel or post-merge.

### Trigger CC

✅ **All blockers cleared. CC: begin F2 Day 1 when next session opens.** Yolo B Liberal active in next `claude` launch — CC executes autonomous without per-bash prompts.

Per §G #c "PR queue cleared (WC-Impl signals)": PR #114 needs migration fix (~10 min CC) before merge, but does NOT block F2 ship (separate territories). PR #130 + #159 cleared via Run 184 reviews (threads 192, 193 GREEN). Recommendation: CC F2 Day 1 starts immediately; PR #114 fix can run in parallel worktree.

**Signed**: Alex, 2026-05-24 (executed live with WC-web in interactive session)
