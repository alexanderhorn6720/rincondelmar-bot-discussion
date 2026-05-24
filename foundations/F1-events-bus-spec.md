# F1 Events Bus — Spec Expansion & Migration Audit (Draft)

**Status**: Draft (open-for-alex-vote). WC preliminary recommendations marked. Alex final.

**Relation**: Companion draft to canonical [rdm-platform/foundations/F1-events-bus.md](../../../platform/foundations/F1-events-bus.md) (Accepted per ADR-002 2026-05-20).

**Purpose**:
1. Audit F1 spec migration claims (0040/0041) against rdm-bot filesystem reality (analog to thread/186 B1 remap for F2).
2. Surface staged amendments for WC-Platform to fold into canonical spec post-Alex vote.
3. Confirm cron design + consumer registry config remain valid against present rdm-bot infrastructure.

**Boundary**: This draft lives in rdm-discussion (CC territory). It does NOT modify `rdm-platform/foundations/F1-events-bus.md` (CC read-only on rdm-platform per thread/184 §6). WC-Platform applies merged amendments post-vote.

**Authoría**: CC worktree B (Opus 4.7), run thread/184, task B4. Asume F2 reservation 0047 per thread/186 B1.

---

## §0. Why this draft exists

The canonical F1 spec is 481 lines and covers schema, detector, dispatcher, observability hooks, acceptance criteria, rollout, and design rationale comprehensively. It is **not lacking content** — what triggered this expansion task (per thread/184 §3 B4) was the assumption that detail was thin.

Reality check shows the gap is narrower:

| Aspect requested by spec/184 B4 | Status in canonical F1 |
|---|---|
| SQL migration | Present (§2.1 + §2.2 — schemas for `booking_lifecycle_events` + `lifecycle_outbox`) |
| Cron design | Present (§3.1 — synchronous + backfill + time-based modes; §4 — dispatcher cron `*/2`) |
| Consumer registry config | Present (§3.3 — `LIFECYCLE_CONSUMERS` declarative TS, 8 consumers, all `enabled: false` at ship) |

**True open issue**: migration slot numbering. F1 reserves slots `0040` and `0041`, both already consumed.

This draft documents the gap, proposes the patch, and surfaces small additional findings.

---

## §1. Migration slot audit (analog to thread/186 B1)

### F1 spec claims (rdm-platform)

| Slot | Table | Spec ref |
|---|---|---|
| 0040 | `booking_lifecycle_events` | `F1-events-bus.md` §2.1 |
| 0041 | `lifecycle_outbox` | `F1-events-bus.md` §2.2 |

### Filesystem reality (rdm-bot/migrations/, 2026-05-23)

| Slot | Reality | Origen |
|---|---|---|
| 0040 | `rules_link_clicks` | shipped |
| 0041 | `bot_short_links` | shipped |
| 0042 | `feedback_system` | shipped (thread/161) |
| 0043 | `booking_captures` | shipped |
| 0044 | `outreach_templates` | shipped |
| 0045 | `mp_payments` | shipped |
| 0046 | `cost_telemetry` | shipped (thread/175 T2) |
| 0047 | **RESERVED** for `cron_heartbeats` (F2 per thread/186) | pending F2 ship |
| 0048 | **LIBRE** | — |
| 0049 | **LIBRE** | — |

### Proposed remap

| F1 spec original | Proposed new slot | Conditional |
|---|---|---|
| 0040 → `booking_lifecycle_events` | **0048** | If thread/186 B1 Opción A confirmed (F2 takes 0047) |
| 0041 → `lifecycle_outbox` | **0049** | Sequential after 0048 |

**Voto WC preliminar**: take 0048 and 0049. *WC preliminary, Alex final.*

Razón:
- Sequential allocation after F2 reservation (0047).
- Both F1 migrations are additive (no destructive ALTER on existing tables), so re-numbering carries zero functional risk.
- F1 ship order (post-F2 per ADR-002 §2) guarantees 0047 is consumed first.

If F2 spec adopts a different remap (e.g., Opción B from thread/186 keeps F2 without dedicated migration), F1 slots should shift up accordingly. F1 takes the next two sequential available at the time of F1 ship.

---

## §2. Cron design — verification against rdm-bot reality

F1 spec proposes 2 new crons in `apps/worker-pago`:

| Cron | Schedule | Purpose |
|---|---|---|
| Outbox dispatcher | `*/2 * * * *` (every 2 min) | Pick `lifecycle_outbox` pending/failed rows, call consumer endpoints |
| Time-based scanner | `0 */1 * * *` (hourly) | Emit `arrival_imminent_t14/t7/t1`, `arrived`, `departed` |

### Verification

| Check | Result |
|---|---|
| `apps/worker-pago` exists | YES (filesystem `rdm-bot/apps/worker-pago/`) |
| Worker plan | Workers Paid (per ADR-003 §2.1) |
| Current cron slot usage | 5 native crons (verified per spec §3.1 + ADR-003 reference) |
| F1 adds | 2 → total 7 |
| CF documented cron cap | Not documented (CC 146 §F1.Q1 noted; spec §3.1 says "if dashboard warns at 7, F1 §8 includes verification step") |
| Service Binding `WORKER_BOT` | Spec §3.4 proposes addition to `wrangler.toml`; not currently in repo (validated) |

**Risk**: cron count growth approaches plan boundaries silently. F2 also proposes crons (cron-heartbeats writes, dashboard refresh? — F2 spec §3.3 has only the heartbeat reads, no new cron, just one-line-per-existing-cron heartbeat). Net: post-F2+F1, worker-pago has 7 native crons.

**Additional finding**: an external `cron-bot-alerts.ts` runs in worker-bot (verified `apps/worker-bot/src/cron-bot-alerts.ts:160-198`) checking heartbeat staleness. F1 dispatcher and F2 heartbeats both touch this; needs to be in F1 acceptance criterion to verify NO crontab conflict.

**Voto WC preliminar**: add this verification step to F1 §6 acceptance criteria as #13:
> "13. ✅ Cron count post-F1 in `apps/worker-pago/wrangler.toml`: 7 native crons (5 existing + 2 new). Deploy succeeds without CF dashboard warning. If warning surfaces, halt + escalate (cron count limit decision needed)."

---

## §3. Consumer registry config — verification

F1 spec §3.3 declares 8 consumers in `LIFECYCLE_CONSUMERS` TS const, ALL `enabled: false` at ship time:

| consumer_id | Events subscribed | Endpoint | enabled at ship |
|---|---|---|---|
| `m1_pricing` | `booking_created`, `booking_modified`, `booking_cancelled` | `service:m1-pricing/handle` | false |
| `m5_tasks` | `arrived`, `departed`, `arrival_imminent_t1` | `service:m5-tasks/handle` | false |
| `i3_in_stay` | `arrived` | `service:worker-bot/i3/start` | false |
| `i5_post_stay` | `departed` | `service:worker-bot/i5/request-review` | false |
| `manychat_sync` | `booking_created`, `manychat_subscriber_created` | `service:worker-bot/manychat/sync` | false |
| `pre_stay_t14` | `arrival_imminent_t14` | `service:worker-bot/pre-stay/t14` | false |
| `pre_stay_t7` | `arrival_imminent_t7` | `service:worker-bot/pre-stay/t7` | false |
| `pre_stay_t1` | `arrival_imminent_t1` | `service:worker-bot/pre-stay/t1` | false |

### Verification

- File `packages/db/src/lifecycle/consumers.ts` does NOT exist (verified). F1 ship creates it.
- Service `service:m1-pricing` does NOT exist (no `apps/m1-pricing/` directory). M1 ships LATER per ADR-002 sequencing.
- Service `service:m5-tasks` does NOT exist (no `apps/m5-tasks/`). M5 ships LATER.
- Routes `service:worker-bot/i3/start`, `/i5/request-review`, `/manychat/sync`, `/pre-stay/t{14,7,1}` — these routes do NOT exist in `apps/worker-bot/src/index.ts` (validated).

**Implication**: F1 ships the bus + 8 consumer placeholders disabled. Each future spec (M1, M5, I3, I5, F1.1 pre-stay) is responsible for:
1. Creating the consumer endpoint
2. Flipping `enabled: false` → `enabled: true` in the registry config

**Voto WC preliminar**: this matches spec §3.3 design — no change requested. Surface explicit note in F1 acceptance criterion #6 (already there: "all consumers `enabled: false`; dispatcher runs no-op").

### Additional consumer candidate not currently in registry

Spec §11 mentions `F1.1 · Pre-stay migration to lifecycle bus` will replace existing cron-scan pre-stay handlers with event-driven consumers. The registry already accommodates this via `pre_stay_t14/t7/t1` placeholders.

But there is also today `apps/worker-bot/src/pre-stay.ts` running cron-scan. F1 ship requires F1.1 to immediately follow OR keep cron-scan running in parallel (dual path) until canary confirms. Spec §8 covers this:
> "Day 3-7 (soak): once F1.1 ready, pre-stay consumers flip to enabled: true one at a time with canary observation."

**Voto WC preliminar**: F1 ship leaves `apps/worker-bot/src/pre-stay.ts` intact (no deletion). F1.1 spec authored AFTER F1 ships, executes canary in dedicated PR. Confirmed alignment, no spec amendment needed here.

---

## §4. Integration with F2 (post-thread/186 remap)

F1 spec §5 declares F2 metrics emission via WAE:

- `lifecycle_events_written_count`
- `lifecycle_outbox_pending_count`
- `lifecycle_outbox_dlq_count`
- `lifecycle_dispatcher_duration_ms`
- `lifecycle_consumer_latency_ms`
- `lifecycle_consumer_error_rate`

This requires F2's `emitMetric` helper (per F2 §3.2) to be available, which requires F2 ship. F1 ship order is post-F2 per ADR-002. Sequence holds.

**Cross-spec dependency**: F1 §5 references `packages/shared/src/metrics.ts` (F2 deliverable). If F2 ship is delayed, F1 ship is delayed.

**Open question for Alex**: if F2 vote (Opción B in thread/186 — reuse bot_config, no migration) is chosen, then F1 takes 0047 and 0048 instead of 0048 and 0049. **Recommendation**: F1 remap notes a `slot_after_f2` placeholder rather than hardcoding 0048+0049; CC ships F1 reading the latest free slots via `scripts/new-migration.sh` (existing per CLAUDE.md).

**Voto WC preliminar**: amend F1 spec §2.1 and §2.2 SQL comments to say:
> `-- migrations/NNNN_booking_lifecycle_events.sql` (slot determined via `scripts/new-migration.sh` at ship time; expected 0048 if thread/186 Opción A confirmed)

This makes the slot future-proof against any earlier feature taking 0048.

---

## §5. Other findings (verified during audit)

### `journey` columns on `beds24_bookings`

F1 spec §1 ("Already in place") references `journey` columns LIVE per PR #117. Verification:

- `apps/web/src/lib/journey-events.ts` exists (validated)
- Migration `0035_pre_stay_columns.sql` exists (matches PR #117 timing)
- F1 consumer `pre_stay_t14/t7/t1` will read journey state to skip already-fired guests

**No spec amendment needed**. Cross-reference is current.

### `audit_log` boundary

F1 spec §10 reserves `audit_log` (migration 0039) for staff actions only. F2 spec §3.2 echoes this (WAE for metrics, audit_log for actions).

Verification: `audit_log` table LIVE since 0039. Currently only written by admin actions (validated via grep `INSERT INTO audit_log`).

**No spec amendment needed**.

### Beds24 webhook receiver path

F1 spec §3.1 says detector wired into "Beds24 webhook receiver in `apps/worker-bot`". File `apps/worker-bot/src/beds24-webhook.ts` (or similar) — needs CC to confirm at implementation time. Not in scope for this draft.

---

## §6. Summary: amendments to canonical F1 spec

Patch to apply by WC-Platform in `rdm-platform/foundations/F1-events-bus.md` post-Alex vote:

| Sección | Cambio |
|---|---|
| §2.1 SQL comment | `migrations/0040_booking_lifecycle_events.sql` → `migrations/NNNN_booking_lifecycle_events.sql` with note: "slot determined via `scripts/new-migration.sh` at ship time; expected 0048 if thread/186 Opción A confirmed" |
| §2.2 SQL comment | Same pattern: `0041_lifecycle_outbox.sql` → `NNNN_lifecycle_outbox.sql`, expected 0049 |
| §1 "What F1 adds" | Update migration column: 0040/0041 → 0048/0049 (or NNNN with footnote) |
| §6 acceptance | Add criterion #13 (cron count verification per §2 above) |
| §3.4 Service Binding | Add note: "CC verifies `apps/worker-pago/wrangler.toml` post-F2 still has correct cron count and Service Binding to worker-bot pre-deploy." |

---

## §7. Bloqueador downstream

- F1 ship hard-blocked by F2 ship (per ADR-002 §2)
- F1 ship hard-blocked by Q3.1 G7 Alex vote (thread/148)
- This draft itself does NOT block anything — its purpose is to surface amendments for inclusion when F1 ship slot opens

If Alex chooses to defer F1 indefinitely, this draft sits dormant. If Alex confirms F1 ship after F2, WC-Platform folds these amendments into the canonical spec, then CC ships against the amended spec.

---

## §8. Definition of done — B4

- [x] Read canonical F1 spec (481 lines, comprehensive)
- [x] Audit migration slot collision (0040/0041 already consumed; remap to 0048/0049 proposed)
- [x] Verify cron design against rdm-bot infrastructure (verified)
- [x] Verify consumer registry endpoints against rdm-bot files (verified — none exist yet, expected)
- [x] Document integration dependencies with F2 (post-thread/186)
- [x] List amendments to apply post-Alex vote (§6)
- [x] Status `open-for-alex-vote` (no se cierra sin voto Alex)
- [x] Boundary respected: NO modification to rdm-platform/foundations/F1-events-bus.md

**Next action**: PR review + Alex vote. Post-vote, WC-Platform applies §6 patch to canonical F1 spec in rdm-platform.

---

## §9. Open questions for Alex

1. **Migration slot strategy**: hardcode 0048/0049 NOW in F1 spec, OR use `NNNN` placeholder + `new-migration.sh` at ship time?
   - WC preliminary: NNNN placeholder. More future-proof.
2. **F1.1 Pre-stay migration timing**: ship F1 first with cron-scan pre-stay still active (dual-path) for soak window, then F1.1?
   - WC preliminary: yes, per spec §8 Day 3-7 plan.
3. **Cron count limit**: if `worker-pago` reaches 7 native crons (post-F1+F2), is that OK?
   - WC preliminary: ADR-003 §2.1 confirms 5/5 is current; CF doesn't publish hard cap. Add §6 acceptance #13 to verify at deploy time.

---

## See also

- [rdm-platform/foundations/F1-events-bus.md](../../../platform/foundations/F1-events-bus.md) (canonical, Accepted)
- [rdm-platform/foundations/README.md](../../../platform/foundations/README.md) §F1 (summary)
- [threads/186-CC-f2-migration-remap.md](../threads/186-CC-f2-migration-remap.md) (sibling B1 work — F2 remap)
- [threads/148](../threads/148) (Alex vote context)
- [threads/146](../threads/146) (CC pre-flight, F1.Q1-Q5)
- [rdm-platform/decisions/ADR-002-foundations-seal.md](../../../platform/decisions/ADR-002-foundations-seal.md) §4 + §10
- [thread/184](../threads/184) §3 B4 (task parent)
