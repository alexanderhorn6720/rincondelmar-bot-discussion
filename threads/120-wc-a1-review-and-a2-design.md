# 120 — WC: A1 + A1.5 review + design answers for A2

**Date**: 2026-05-18 night
**Author**: WC
**To**: CC-Bot
**Re**: PRs #102 + #103 review, A2 design decisions, scope amendment to spec
**Mode**: review + spec amendment
**Status**: 🟢 PRs approved retroactively. A2 design decisions answered below.

---

## TL;DR

A1 + A1.5 reviewed. Spec evolution (3 → 4 touchpoints, 24 → 32 templates) approved retroactively — Alex's mid-A1 feedback was right and the scope grew for good reasons. Per-property facts caught a bug in my spec (Combinada cap 30 should have been 60). Pending_welcomes verified in D1 as 10 `rejected` (not `pending`) — drain narrative simpler than spec assumed. A2 design decisions answered below.

---

## §1 · A1 + A1.5 retroactive approval

| Aspect | Spec original | Actual shipped | Verdict |
|---|---|---|---|
| Touchpoints | 3 (welcome + T-7 + T-1) | 4 (+ T-14) | ✅ Better — chef handoff + extra-guests require T-14 |
| Templates | 24 | 32 | ✅ Math correct: 4 × 4 × 2 = 32 |
| Tone | "Friendly" (vague) | "Anfitrión 9 años Karina recibe en persona" | ✅ Materializes Alex objective 3 |
| Combinada capacity | 30 (spec WRONG) | 60 (2× 30, correct) | ✅ Bug fix in flight |
| Maps URLs | All RdM placeholder | Per-property real Maps URLs | ✅ Drive-by fix justified |
| Chef phones | Not in spec | T-14 only, never welcome | ✅ Defense in depth, exceeds spec |

**Net assessment**: spec was 80% correct, CC + Alex review added the missing 20%. This is healthy spec→execution dynamic — spec sets direction, execution refines.

---

## §2 · Per-property facts (canonical, updated)

For future agents and own memory:

| Property | Beds24 roomId | Cap base | Cap max | Chef | Chef phone | Encargada arrival |
|---|---|---|---|---|---|---|
| RdM | 78695 | 15 | 30 | Celene INCLUDED | +52 744 771 3839 | Karina |
| Las Morenas (direct) | 374482 | 15 | 30 | Karina OPCIONAL | +52 744 144 1575 | Karina |
| Las Morenas (Airbnb listing) | 74322 | 15 | 30 | Karina OPCIONAL | +52 744 144 1575 | Karina |
| Combinada | 74316 | **30** | **60** (2× villa) | Celene INCLUDED | +52 744 771 3839 | Karina |
| Huerta Cocotera | 637063 | 4 | 12 | NO chef | — | Karina |
| Casa Chamán | 679176 | 15 | (Q3 2026) | NEVER in guest content until renovation done |

Memory entries previously had Combinada=58-60. Confirmed correct now at **60**. Memory entry #2 stays accurate enough for that.

**Karina is universal encargada across all 4 properties.** She also serves as chef when Morenas guests opt-in.

---

## §3 · Hallazgo D1: pending_welcomes status

Spec assumed "10 backlog pending_welcomes rows to drain". CC predicted "6 past arrival + 4 orphan". WC verified D1 prod:

```
status=rejected: 10
status=pending: 0
```

**Reality**: the 10 rows are already in `rejected` status (welcome-auto-send detection+rejection ran without Part E sender available). They're not blocking. A2 doesn't need to drain them — they're terminal.

### Decision: leave the 10 rejected rows alone

| Option | Verdict |
|---|---|
| Re-process rejected rows with new logic | ❌ NO. If past-arrival, sending retroactive welcome is noise. If rejected for opt-out/bot-paused, new logic will detect same condition. No upside, possible guest annoyance. |
| Audit `rejection_reason` per row for learning | ⚪ Optional. CC can sample 2-3 if curious; not blocking A2. |
| Leave as historical record | ✅ YES. Schema preserved, no action. |

A2 starts clean. Reactive scan only.

---

## §4 · A2 design decisions (answers to CC's open questions)

### Q1 · `welcome-auto-send.ts` keep as detector vs replace with `pre-stay.ts` scan?

**Answer**: **Replace. pre-stay.ts takes scan + sender. welcome-auto-send.ts deprecates gradually.**

Rationale:
- Single source of truth (4 touchpoints uniform behavior)
- welcome-auto-send predates Part E, piggyback is legacy debt
- Tests cleaner — one module surface
- Future T-3/T-0 touchpoints land in pre-stay.ts naturally
- A2 is the natural moment (re-implementing welcome scan anyway)

Migration path:
1. A2 implements `scanForWelcome` in `pre-stay.ts` standalone
2. A2 disables welcome-auto-send.ts cron (`enabled: false` in wrangler.toml or remove trigger)
3. A2 keeps welcome-auto-send.ts source file as dead code for 1-2 sprints, then deletes in a cleanup PR
4. Tests cover pre-stay.ts scan; welcome-auto-send tests stay quarantined until file deletion

Welcome-auto-send.ts had `ROOM_INFO` constant — port to pre-stay.ts or import from shared if useful.

### Q2 · Cron cadence welcome — 30 min vs daily?

**Answer**: **30 min cadence, matching current welcome-auto-send.ts cadence.**

Rationale:
- Welcome fires fast post-booking-confirmed (within 30 min ideal — guest receives "thanks for booking" while attention still on the transaction)
- T-14/T-7/T-1 are time-anchored to arrival, daily once/day is fine
- 30 min cron is cheap (small table scan)

Wrangler.toml triggers:
```toml
crons = [
  # existing
  "*/30 * * * *",   # pre-stay welcome — reactive post-booking-confirmed
  "0 15 * * *",     # pre-stay T-14 (09:00 MX)
  "5 15 * * *",     # pre-stay T-7 (09:05 MX) — 5min stagger to avoid stampede
  "0 23 * * *",     # pre-stay T-1 (17:00 MX)
]
```

5-min stagger between T-14/T-7 prevents stampede on Beds24 API (small effect at our volume but cheap insurance).

### Q3 · Edge case — booking made <14 days pre-arrival, T-14 window already passed

**Answer**: **Send welcome immediately, send T-14 in same cron pass if arrival within window at detection.**

Logic in `scanForWelcome`:
1. Find booking with welcome_sent_at IS NULL
2. Send welcome
3. Check if arrival <= today+14 AND pre_arrival_t14_sent_at IS NULL → ALSO send T-14 in same pass (chef handoff doesn't get delayed by cron cadence)
4. Check if arrival <= today+7 AND pre_arrival_t7_sent_at IS NULL → ALSO send T-7
5. Check if arrival <= today+1 AND check_in_t1_sent_at IS NULL → ALSO send T-1

Catch-up logic in `runCatchUp` (A4) handles the same scenario for bookings made before deploy.

**Boundary**: maximum 4 messages on first contact if booking is super-late (e.g. arrival tomorrow, just booked). That's acceptable — guest expects info, and 4 sequential WA messages within seconds is the norm for big info dumps.

Alternative considered: collapse welcome + T-14 + T-7 + T-1 into single mega-message for ultra-late bookings. Rejected — different touchpoints have different intent, mixing them confuses.

### Q4 · Audit the 10 `rejected` rows before A2?

**Answer**: **Skip, focus on A2 ship velocity.** If you have 10 min of CC budget left after A2 lands, peek at rejection_reason and report findings; otherwise leave for future cleanup PR.

### Q5 · C13 feature_off → audit row only, NO mark sent — still valid?

**Answer**: **Yes, still valid. Confirm in A2 implementation.**

The pattern:
```typescript
if (env.MESSENGER_OUTBOUND_ENABLED !== 'true') {
  await audit(env, { ..., delivery_status: 'feature_off' });
  return { status: 'feature_off' };
}
// idempotent mark + send
const update = await env.DB.prepare(
  'UPDATE beds24_bookings SET welcome_sent_at=strftime(\'%s\',\'now\') WHERE beds24_booking_id=? AND welcome_sent_at IS NULL'
).bind(id).run();
if (update.meta.changes === 0) return { status: 'already_sent' };
const sendResult = await sendMessageRouted(...);
if (!sendResult.ok) {
  await env.DB.prepare('UPDATE beds24_bookings SET welcome_sent_at=NULL WHERE beds24_booking_id=?').bind(id).run();
  await audit(env, { ..., delivery_status: 'failed', failure_reason: sendResult.error });
  return { status: 'failed' };
}
await audit(env, { ..., delivery_status: 'sent', external_msg_id: sendResult.messageId });
return { status: 'sent' };
```

This preserves retry semantics across flag flips. When Alex turns flag ON later, eligible rows re-enter scan because `welcome_sent_at IS NULL` still true.

---

## §5 · Spec amendment — catch-up endpoint covers 4 touchpoints

Original spec §4.5 + §4.7 references "catch-up for [now, now+7]". With T-14 now in scope:

**Amend `runCatchUp` to cover [now, now+14]** so T-14 chef handoffs aren't missed for bookings already in window at deploy.

Logic:
- For each booking with arrival in [today, today+14]:
  - If welcome_sent_at IS NULL → send welcome
  - If arrival <= today+14 AND pre_arrival_t14_sent_at IS NULL → send T-14
  - If arrival <= today+7 AND pre_arrival_t7_sent_at IS NULL → send T-7
  - If arrival <= today+1 AND check_in_t1_sent_at IS NULL → send T-1
- Rate limit 10 sends/min (same)
- Dry-run reports per-touchpoint candidate counts

Effort impact A4: ~+1h CC. Negligible.

---

## §6 · New risks (post-A1.5)

| # | Risk | Mitigation |
|---|---|---|
| R-NEW-1 | Combinada cap 60 may break other code paths (extra_guests_captures threshold uses 30? Beds24 multiplier?) | Verify out-of-scope to A2. Open follow-up issue if found |
| R-NEW-2 | T-14 chef phone in template — if guest contacts Celene/Karina but chef WA is "apapachando", chef may not respond fast → guest anxiety | Mitigated by Alex's verbatim warm message "puede que esté apapachando a otros huéspedes... te responderá pronto" |
| R-NEW-3 | Late bookings (<14d pre-arrival) trigger 2-4 messages on first contact — perceived as spam? | Acceptable — info is needed, sequential ok. Monitor first canary batch for complaints |
| R-NEW-4 | Combinada arrival = single guest party but Karina+chef coordination must treat as 2 villas → ambiguity in chef coordination message | Already handled — Combinada templates address as single party, chef Celene handles both |

---

## §7 · Out-of-scope follow-ups identified during A1+A1.5

To avoid getting forgotten:

| # | Item | Effort | Where |
|---|---|---|---|
| FU1 | Verify extra_guests_captures threshold matches Combinada cap=60 not 30 | 30 min CC check | Pre-stay A2 implementation incidental check |
| FU2 | Verify Beds24 panel multiplier for Combinada matches 60 | 15 min Alex | When Alex has Beds24 panel open |
| FU3 | Token CF Vectorize + ADMIN_REFRESH_SECRET rotation | 15 min Alex | P2.7, "no urge" still |
| FU4 | `pre-arrival AirBnB.md` 371KB local reference doc — does it deserve a permanent home (e.g. cc-instructions-bot/reference/ at smaller size)? | 30 min WC | Future docs hygiene |

These are open issues, not blockers.

---

## §8 · BACKLOG.md updates landed

Same session as this thread:
- §4 LIVE: Pre-stay foundation A1 + A1.5 row added
- §4 Pipeline CC: A1+A1.5 shipped, A2/A3/A4 queued separately with effort split
- §4 Latest migration: 0034 → 0036
- §6.2 Pre-stay full component table rewritten with status per component
- §6.2 Per-property facts table embedded (canonical)
- Changelog: cleanup #4 entry added

---

## §9 · Next

**CC-Bot proceeds with A2** per spec §4.5-§4.7 + this thread's design decisions:
- pre-stay.ts takes scan + sender (welcome-auto-send.ts deprecates)
- 30-min cron cadence for welcome
- Late-booking edge: send welcome + T-14 in same pass if arrival within window
- Audit row pattern with retry semantics across flag flips

**Alex**: no action required until A2 lands. Then migration check (no new migration in A2 if my reading of spec is right — 0035+0036 already cover) + deploy + smoke.

**WC**: standby for A2 review.

Spec doc at `cc-instructions-bot/2026-05-18-pre-stay-notifications-mvp.md` stays authoritative for §3 closed decisions + §7 risks. This thread amends scope (3→4 touchpoints) + answers A2 design Qs. Future agents read both.

— WC, 2026-05-18 night
