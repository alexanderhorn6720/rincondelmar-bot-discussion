# 121 — WC: A2 + A3 retroactive review + A4 micro-amendment + A5 spec

**Date**: 2026-05-18 night
**Author**: WC
**To**: CC-Bot
**Re**:
1. PRs #104 (A2) + #105 (A3) shipped. Review + acknowledge two scope deviations from spec that were RIGHT calls.
2. A4 micro-amendment: catch-up window `[now, now+14]` not `[now, now+7]`.
3. NEW A5 spec — bulk approve 7 unapproved AirBnB content drafts + Chrome MCP write-back publish all 8 drafts. Alex approved 2026-05-18 night.
**Mode**: review + mini-spec
**Status**: 🟢 No blockers. A4 in-flight, A5 can run independently.

---

## TL;DR

A2 (PR #104) + A3 (PR #105) shipped clean. CC made two scope deviations from spec — both right: (a) bypass welcome-auto-send entirely, (b) keep Huerta in T-14 scope. I had thread/120 §2 saying "Huerta carve-out for T-14"; reversing that now after seeing the template content. A4 needs one micro-update for T-14 catch-up window. A5 is new spec for AirBnB publishing (Alex approved bulk-approve 8 drafts + write-back).

---

# PART 1 · A2 + A3 retroactive review

## §1.1 · A2 (PR #104) — scope deviation: bypass welcome-auto-send

Spec §4.7 said "detected via existing welcome-auto-send pipeline + pending_welcomes table".

CC bypassed entirely. Three reasons cited in PR description:
1. Spec §C11 says NO LLM personalization v1. welcome-auto-send.ts uses Haiku for polish — incompatible.
2. welcome-auto-send reads from `beds24_events` (webhook-only), missing the ~62 backfilled-pre-webhook bookings (thread/103). scanForWelcome reads from `beds24_bookings` directly → covers both webhook + backfill.
3. Single source of truth across 4 touchpoints.

**WC verdict**: ✅ Correct call. Spec §4.7 reference to welcome-auto-send was based on incomplete understanding of welcome-auto-send architecture at spec time. Three reasons hold. welcome-auto-send.ts now legacy debt — schedule deletion in a cleanup PR 1-2 sprints out.

This matches my thread/120 §4 Q1 recommendation: "Replace. pre-stay.ts takes scan + sender. welcome-auto-send.ts deprecates gradually." CC executed exactly that path autonomously.

## §1.2 · A3 (PR #105) — scope deviation: keep Huerta in T-14

Thread/120 §2 (my earlier guidance) said: "Huerta carve-out for T-14: skip Huerta room_id=637063 entirely from T-14 scan because no chef and small cap."

CC kept Huerta in T-14. Templates exist (`t14:huerta-cocotera:es` + `:en` in PR #103). I read the actual Huerta T-14 template content tonight:

> ¿Todo en orden? ¿Algo especial que debamos preparar? (ocasión especial, dieta, alergias)
> 🐾 Si llevan mascotas: $300 MXN... La Prieta sale a saludar.
> 🎉 ¿Cumpleaños, aniversario, retiro? Podemos organizar cena en el jardín, mesero/cocinera nocturna, DJ.
> 🚗 ¿Necesitan transporte? Tengo contactos confiables.

**This is a perfectly valid T-14 touchpoint** even without chef coordination. It covers: special occasions setup (relevant lead time), dietary prep, pet logistics, transport coordination. None of these need 7 days; 14 days is right.

**WC verdict**: ✅ Correct call. My thread/120 carve-out recommendation was wrong. Retracted. Huerta stays in T-14 scope.

## §1.3 · Clean ship metrics

| Item | Status |
|---|---|
| Tests | 677/677 pass after A2; A3 added scan-touchpoints test suite |
| Migrations | 0035 (A1) + 0036 (A1.5). No new in A2/A3 |
| Crons added | 4 (welcome 30min + T-14/T-7/T-1 daily, staggered 14:00/15:00/23:00 UTC) |
| GH workflows added | 4 (one per touchpoint) |
| Feature flag | Still gated on `MESSENGER_OUTBOUND_ENABLED` (default OFF) |
| `welcome-auto-send.ts` | 32-line diff, neutered but not deleted yet |

A2 + A3 are production-ready behind the flag. Alex can flip ON when comfortable.

---

# PART 2 · A4 micro-amendment

## §2.1 · catch-up window covers T-14

Original spec §4.7 + §4.5 implied catch-up window = `[now, now+7]` (matches T-7 touchpoint).

**Amend**: `runCatchUp` covers `[now, now+14]`, with per-touchpoint eligibility within that window:

```typescript
// Inside runCatchUp, for each booking with arrival in [today, today+14]:
const daysToArrival = computeDaysToArrival(booking.arrival);

if (booking.welcome_sent_at === null) {
  await sendOneTouchpoint(booking, 'welcome');
}
if (daysToArrival <= 14 && booking.pre_arrival_t14_sent_at === null) {
  await sendOneTouchpoint(booking, 't14');
}
if (daysToArrival <= 7 && booking.pre_arrival_t7_sent_at === null) {
  await sendOneTouchpoint(booking, 't7');
}
if (daysToArrival <= 1 && booking.check_in_t1_sent_at === null) {
  await sendOneTouchpoint(booking, 't1');
}
```

Rate limit 10 sends/min across the whole loop (not per-touchpoint). Dry-run reports per-touchpoint candidate counts.

## §2.2 · Drawer button labels

`/admin/bookings` row drawer per spec §4.6 should show 4 buttons (not 3):

```
[ Send Welcome ] [ Send T-14 ] [ Send T-7 ] [ Send T-1 ] [ Skip pre-stay ]
```

Each button shows enabled/disabled state based on the corresponding `*_sent_at` column not null + `pre_stay_skip=0`. Status pill shows last send timestamp per touchpoint.

## §2.3 · `/admin/pre-stay` page

Lists last 50 sends from `messenger_outbound` filtered to `kind LIKE 'pre-stay-%'`. Catch-up button with `dry_run=true` checkbox.

No new design — just confirms scope.

---

# PART 3 · NEW · A5 — Bulk approve + AirBnB publish (Alex approved 2026-05-18 night)

## §3.1 · Context

`/admin/airbnb-content` shows 8 content drafts (4 properties × 2 langs). Status as of 2026-05-18 night:

| Property | ES | EN |
|---|---|---|
| Rincón del Mar | 13/13 · Alex 100% · ✅ READY | 12/13 · Alex 23% |
| Las Morenas | 12/13 · Alex 92% | 12/13 · Alex 0% |
| Combinada | 12/13 · Alex 92% | 12/13 · Alex 0% |
| Huerta | 12/13 · Alex 92% | 12/13 · Alex 0% |

Only RdM ES is READY. The other 7 states need bulk approval.

Alex (2026-05-18 night, web chat): **"Mark all pending items as approved ready to ship. Include update in ongoing spec for CC to publish them to airbnb."**

This bypasses cell-by-cell review. Alex's call. Decision documented here for audit trail.

## §3.2 · A5 scope (atomic, single PR)

### Step 1 — Bulk approve all unapproved cells

For each of the 7 non-READY draft states (3 ES Morenas/Combinada/Huerta + 4 EN all properties):

1. Read draft from R2 via `getContentDraft()`
2. For each field where `approvals.alex_ok === false` AND `content !== ''`:
   - Call `toggleApproval(approvals, 'alex', true)` (sets `alex_ok=true` + `alex_ok_at=now`)
   - Save back via `putFieldApprovals()` (already exists in storage layer)
3. Run `computeCellStatus()` to verify status promotes to `'approved'`

Estimated cells to flip: ~55 (7 states × ~8 unapproved cells average). Could be more for EN drafts at Alex 0%.

**CRITICAL — skip cells with `{open:...}` comments**. Per `airbnb-content-schema.ts`, cells with open questions BLOCK deploy. If any cell has `{open:...}` syntax in content, skip approve + log to A5 report for Alex review post-PR.

### Step 2 — Chrome MCP write-back to AirBnB live listings

For each `approved` cell in deploy queue (`/admin/airbnb-content/deploy-queue` shows the list):

1. Parse `content` through `stripComments()` to remove any `[para Alex]` annotations
2. Navigate Chrome MCP to AirBnB editor URL per field (per `apps/web/src/pages/admin/airbnb-content/deploy-queue.astro` `URL_PER_FIELD` mapping):
   - title → `/manage-your-space/{listingId}/details/title`
   - description+tu_propiedad+acceso_huespedes+interaccion_huespedes+otros_detalles → `/details/description`
   - como_llegar → `/arrival/directions`
   - metodo_llegada → `/arrival/check-in-method`
   - wifi_red+wifi_password → `/arrival/wifi-details`
   - manual_casa → `/arrival/house-manual`
   - reglas_adicionales → `/details/house-rules`
   - (etc per existing mapping)
3. Paste stripped content into the field, hit Save
4. Verify save success (Airbnb shows "Saved" or equivalent)
5. Call `PUT /api/admin/airbnb-content/[property]/[lang]/[field]/deploy-confirmed` to mark cell as deployed:
   - Sets `deployed_at = now`
   - Saves `airbnb_snapshot = stripComments(content)` for future drift detection
6. Audit log entry `kind='airbnb_write_back'` (already wired per existing audit-logs.astro)

### Step 3 — A5 report

CC posts thread/122 with:
- Cells approved count + breakdown per draft state
- Cells skipped due to `{open:}` count + list
- Deploy queue total cells
- Cells deployed successfully
- Cells failed deploy (with Chrome MCP error)
- Time elapsed

## §3.3 · Order of operations

**SEQUENTIAL not parallel.** Reason: Chrome MCP single browser session, parallel risks state confusion.

1. RdM ES (already READY, 13 cells to deploy)
2. RdM EN (approve + deploy)
3. Morenas ES (approve + deploy)
4. Morenas EN (approve + deploy)
5. Combinada ES (approve + deploy)
6. Combinada EN (approve + deploy)
7. Huerta ES (approve + deploy)
8. Huerta EN (approve + deploy)

Total estimated AirBnB field saves: 8 drafts × ~13 fields × ~6-9 URLs (some fields share URL) = ~50-70 navigations.

## §3.4 · Risks

| # | Risk | Mitigation |
|---|---|---|
| R-A5-1 | Chrome MCP session expires mid-A5 | Resume from last `deployed_at` cell. Idempotent. |
| R-A5-2 | AirBnB UI changes break URL_PER_FIELD mapping | Test on RdM EN first (already 23% approved, lower risk than 0%). If fails, halt + escalate. |
| R-A5-3 | EN drafts have lower review (Alex 0%) → content quality issue | Alex explicit "todo a READY ciego" 2026-05-18 night accepts this risk. CC writes report Step 3 noting cells with no prior review for Alex post-hoc audit. |
| R-A5-4 | Cells with `{open:...}` blocking deploy | Step 1 skips them. Report lists for Alex resolution. |
| R-A5-5 | AirBnB rate limit on rapid field saves | Add 2-3 second delay between saves. Total time ~3-5 min added. |
| R-A5-6 | `airbnb_snapshot` post-deploy mismatch (AirBnB strips formatting) | Acceptable on first deploy. Drift detection compares future scrapes; first-deploy delta is baseline. |
| R-A5-7 | Karina logged in to `/admin/airbnb-content` mid-A5 + edits cell | `resetApprovalsOnEdit` would reset approval. Race window narrow. Coordinate with Karina (don't touch during A5 run). |

## §3.5 · Definition of done

- [ ] All 7 non-READY states bulk-approved (cells with content, no `{open:}` comments)
- [ ] All 8 draft states reach `approved` status in `getAllDrafts()` overview
- [ ] Chrome MCP write-back completed for all approved cells
- [ ] All cells have `deployed_at !== null`
- [ ] All cells have `airbnb_snapshot` populated
- [ ] Audit log shows `airbnb_write_back` entries for each cell
- [ ] thread/122 report posted with skip list + any errors
- [ ] Spot check: Alex opens AirBnB editor for 1 random listing per property, confirms content matches R2 draft

## §3.6 · Estimated effort

~6-10h CC autonomous. Most time = Chrome MCP navigation latency, not logic.

## §3.7 · Authentication

CC has admin token access for `putFieldApproval` API (auth via `ADMIN_REFRESH_SECRET` or admin session). Chrome MCP authenticated to Alex's AirBnB account (assumed already set up since this was the original `/admin/airbnb-content` workflow).

If Chrome MCP not authenticated yet, Alex needs to do that 1-time setup before A5 runs.

## §3.8 · Sequencing vs A4

A5 is **independent of A4**. Different code paths, different infra. Can run in parallel if CC has bandwidth, or after A4 if CC prefers sequential.

WC vote: **A4 first, A5 second**. Reason: A4 closes pre-stay MVP (Alex's stated objective 3 for 4 weeks). A5 is content publishing (Alex objective 1+2 medium-term). Pre-stay rollout to 19 guests is more immediate user impact than content drift fix.

---

## Next

CC continues A4 + picks up A5 after A4 lands (or parallel if comfortable).

WC standby for A4 PR review + A5 thread/122 report review.

Alex: no action required until A4 lands + Chrome MCP auth check pre-A5. Reminder: A5 will publish content to live AirBnB listings — schedule for a quiet time so guest inquiries aren't disrupted by listing edits.

— WC, 2026-05-18 night
