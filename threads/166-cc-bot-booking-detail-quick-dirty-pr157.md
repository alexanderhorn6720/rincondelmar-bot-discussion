# 166 · CC-Bot · Booking Detail Quick & Dirty completion (PR #157)

**Author**: CC-Bot (DoIt session 2026-05-22)
**Type**: completion report
**Spec**: [`cc-instructions-bot/2026-05-22-booking-detail-quick-dirty.md`](../cc-instructions-bot/2026-05-22-booking-detail-quick-dirty.md)
**PR**: https://github.com/alexanderhorn6720/rdm-bot/pull/157
**Branch**: `feat/booking-detail-quick`

---

## Status

🟢 **Single PR ready for Alex review + merge**. 5 semantic commits, 4960 insertions / 101 deletions, 40 files.

All 17 spec smoke-test steps deferred to post-deploy (Alex executes). Tests pass green locally:

| Suite | Tests |
|---|---|
| `apps/worker-bot` | 871 ✅ (incl. 14 new `booking-detail.test.ts`) |
| `apps/web` | 477 ✅ (incl. 7 new `mp.test.ts` + 4 new inbox query-param cases) |
| `packages/shared` | 13 ✅ (new `booking-readiness.test.ts`) |
| `packages/auth` | 7 ✅ |
| **Total** | **1368 ✅** |

`tsc --noEmit` clean on worker-bot + packages/shared + net-new web files (10 pre-existing apps/web errors in `middleware.ts` + auth route + 3 test files untouched).

`biome check` clean on net-new files (2 non-null-assertion warnings remain, safe — they follow `if (!m) return iso` regex match guards).

---

## What landed

### Migrations (atomic-claimed via `scripts/new-migration.sh`)
- `0043_booking_captures.sql` — 1:1 with `beds24_bookings`, captures mascotas/evento/morenas/menu/compras/notas + readiness cache + Beds24 sync status. LLM-detected flags exist but no populate loop in v1.
- `0044_outreach_templates.sql` — seeds 'unified' template per Alex iteration 4 (single textarea, 4 placeholders).

Spec said 0042+0043 but PR #155 took 0042; renumbered to 0043+0044.

### Shared package
- `@rdm/shared/booking-readiness` — pure formula (30 mandatory + 50 captures + 20 welcome) + status tiering (T-3 critical gap → red; T-14 + <80 → yellow; else by score). Used by worker-bot server (cache write) + React island client (real-time on form change).

### Worker-bot (`apps/worker-bot/`)
- New `src/booking-detail.ts` module + 12 routes:
  - `GET/PUT /admin/booking-captures/:id`
  - `POST /admin/booking-captures/:id/push-beds24`
  - `GET /admin/bookings/:id/invoice-snapshot`
  - `POST /admin/bookings/:id/invoice-item`
  - `DELETE /admin/bookings/:id/invoice-item/:itemId`
  - `POST /admin/bookings/:id/payment`
  - `GET /admin/bookings/:id/bill-text`
  - `GET /admin/outreach-templates`
  - `PUT /admin/outreach-templates/:key`
  - `POST /admin/outreach-fire`
  - `GET /admin/conversation-link/:beds24Id`
- All gated by `x-admin-secret`. Casa Chamán (679176) filtered defensively.
- Beds24 push uses `[{ id, infoItems, notes }]` array body to `/v2/bookings` (raw array, not `{data:[...]}`).
- Beds24 invoice items use `{data:[...]}` wrapper (existing `extra-guests.ts` pattern).
- `postPayment` tries `/v2/inventory/bookings/payments` first; falls back to `invoiceItems` with `type='payment'` on 404/405.

### Web (`apps/web/`)
- New `src/lib/mp.ts` — `createMpPreference()` extracted from `payment-link.ts`. Existing hold flow refactored to use it; output shape preserved for direct-booking callers.
- New `src/lib/worker-proxy.ts` — server-side `x-admin-secret` bridge used by all booking-detail proxies.
- New `/api/admin/booking-payment-link` — admin-only, 5-day MP preference + writes Patrón B short-link row (`rincondelmar.club/ir/pay-<guest>-<YYMMDD>-<rand3>`).
- 13 new admin API proxies routing to worker-bot.
- New `/admin/bookings/[id].astro` + `components/admin/BookingDetailView.{tsx,css}` — 3 tabs (General / Capturas / Cargos & Pagos), mobile-first 320px CSS.
- Enhanced `/admin/extra-guests` — new columns (Listo pill, Capturas icons, 💬, 📋, 🏨) + LLM 🤖 badges + collapsible unified outreach template editor.
- Enhanced `/admin/bookings?view=list|gantt` — Listo + 💬 columns + `→` detail link + Gantt stripe overlay + modal "Ver detalles →" / "💬 Conversación →".
- InboxView `readConvIdFromHash()` now accepts `?conv=` query param as fallback (hash still wins). 4 new test cases.

---

## PRE-CHECK §5.1 findings

| # | Check | Result |
|---|---|---|
| 1 | `/admin/inbox?conv=X` support | ❌ existing only supports `#conv=` hash; ✅ added `?conv=` query fallback in `readConvIdFromHash` |
| 2 | Beds24 `/v2/bookings/payments` endpoint | ⚠️ shape uncertain; `postPayment` tries new endpoint first, falls back to invoiceItem with `type='payment'` if 404/405. Validation deferred to live smoke. |
| 3 | `bot_short_links` exists prod | ✅ migration 0041 applied. Schema differs from spec (`id` PK not `slug`, no `subscriber_name`/`created_via`). Adapted INSERT. |
| 4 | `MP_ACCESS_TOKEN` in apps/web | ⚠️ must verify before deploy. Helper returns 503 `mp_not_configured` if missing. |

---

## Scope deviations from spec

- **Migration path**: spec said `apps/worker-bot/migrations/`, actual repo uses root `./migrations/` (both wrangler.toml's point there).
- **Column names**: spec referenced `pre_arrival_t1_sent_at` and `total_amount`/`balance_due`; actual columns are `check_in_t1_sent_at` and `_mxn`-suffixed. Used real names.
- **`bot_short_links` schema**: adapted INSERT to actual columns.

---

## Surprises / non-obvious decisions

- `/admin/inbox?conv=` query support added inline — spec offered option to ship without it and open an issue; chose to add it (~10 LOC) for cleaner deep links.
- `morenas_svc_confirmed` auto-credits readiness for non-Morenas rooms (else every RdM booking would surface as "Pendiente" forever). Test pinned this.
- Beds24 v2 API is inconsistent: messages use raw array, invoiceItems use `{data:[...]}` wrapper. Followed existing patterns per-endpoint instead of normalizing.
- `notes_karina` whitespace-only ("   ") does NOT satisfy notas readiness — test pinned.
- `menu_status === 'declined'` satisfies compras requirement (no menu = no grocery list) — test pinned.

---

## Cost + time

- LLM cost: ~$6-7 estimated (well under $10 default budget per CLAUDE.md)
- Time: ~3-4h DoIt continuous (well under 28h spec estimate; spec was conservative on Astro/React island time)
- No halt events. No 30-min stuck loops.

---

## Decisions pending Alex

| # | Decision | Recommended | Why |
|---|---|---|---|
| 1 | Deploy order | apply migrations first (`d1 migrations apply rincon --remote`), then deploy worker-bot, then merge to main (auto-deploys web) | Migrations are additive (no ALTER on existing tables), can run before code deploy without breaking |
| 2 | `MESSENGER_OUTBOUND_ENABLED` for outreach-fire | leave OFF until Karina trained on UI | `/admin/outreach-fire` 503s when off — UI handles gracefully |
| 3 | Smoke test booking | use a real Erika García booking or Alex's own | Spec §5.3 step 1 referenced 86850930; need a known real ID |

---

## Post-merge actions (Alex)

1. Apply migrations 0043 + 0044 prod
2. Deploy worker-bot (`bash scripts/safe-deploy.sh worker-bot` or `cd apps/worker-bot && npx wrangler deploy`)
3. Apps/web auto-deploys via CF Pages on main merge
4. Verify `MP_ACCESS_TOKEN` in apps/web Pages env
5. Smoke test (17 steps from spec §5.3) with real booking ID
6. If smoke green → optional 15min Karina walkthrough

---

## Outstanding items (post-ship)

- WC append `vision/02-wishlist.md` with M6/M7 sections per spec §10
- Monitor `beds24_push_status='failed'` count weekly (Alex)
- Monitor readiness 🔴 distribution after 2 weeks; if >50% red → relax formula thresholds
- ManyChat directo path (`/admin/outreach-fire` for channel=direct) returns 503 until workstream F-1 lands

---

**End report.** PR https://github.com/alexanderhorn6720/rdm-bot/pull/157 ready for Alex review.
