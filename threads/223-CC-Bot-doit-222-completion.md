---
thread: 223
author: CC-Bot
date: 2026-05-27
type: doit-report
related_spec: thread/222
status: ready_for_alex_deploy
pr: 194
branch: feat/web-checkout-beds24-c1
---

# DoIt 222 completion report — Web checkout → Beds24 C1

## Files modificados (684 inserts / 50 deletes)

| Archivo | Tipo | LoC |
|---|---|---|
| `migrations/0051_bookings_beds24_booking_id.sql` | nuevo | +7 |
| `apps/web/src/lib/beds24-direct.ts` | nuevo | +149 |
| `apps/web/tests/beds24-direct.test.ts` | nuevo | +158 |
| `apps/web/src/lib/bookings.ts` | mod | +11 |
| `apps/web/src/pages/api/hold.ts` | mod | +32 / -10 |
| `apps/web/src/env.d.ts` | mod | +1 |
| `apps/web/src/components/booking/BookingFlow.tsx` | mod | +9 |
| `apps/worker-pago/src/webhook-mp.ts` | mod | +77 / -25 |
| `apps/worker-pago/src/crons.ts` | mod | +11 / -7 |
| `apps/worker-pago/tests/webhook-mp.test.ts` | mod | +113 |

## Tests

- web: 648 tests PASS (incluye 9 nuevos en `beds24-direct.test.ts`)
- worker-pago: 40 tests PASS (incluye 4 nuevos UUID flow en `webhook-mp.test.ts`)
- typecheck web: sólo errores pre-existentes en `reviews-api.test.ts` y `wc-seed-converter.test.ts`
- typecheck worker-pago: CLEAN
- build apps/web: PASS
- build apps/worker-pago: PASS
- migration `0051` aplicada local: PASS
- `BEDS24_TOKEN` verificado en Pages prod secrets: PRESENTE

## Cost

- LLM: ~$2-3 estimado (Sonnet 4.6, sesión ~1.5h)

## Deploy checklist para Alex

1. Review PR #194 en mobile
2. Merge (squash)
3. `cd apps/worker-pago && pnpm wrangler deploy`
4. `cd apps/web && pnpm wrangler pages deploy` (o auto)
5. **`wrangler d1 migrations apply rincon --remote`** ← crítico antes del smoke
6. Verificar `BEDS24_TOKEN` en worker-pago: `wrangler secret list --name rincon-pago` → si falta, `wrangler secret put BEDS24_TOKEN --name rincon-pago`
7. Smoke §5.3 del spec: 2 bookings reales 2027 a $20 MXN
8. Post-smoke: cancelar ambos en Beds24 manualmente

## Smoke instructions (§5.3 del spec)

1. `https://rincondelmar.club/reservar/huerta-cocotera`
2. Fechas: **2027-01-10 → 2027-01-12**
3. Login admin@rincondelmar.club
4. Click Reservar → verificar D1 `bookings` row: `status='hold'`, `beds24_booking_id` poblado
5. Beds24 dashboard: nueva reserva `status='request'`, dates, reference = UUID
6. Pagar $20 con NuBank débito (real)
7. Verificar: D1 `status='paid'` + `mp_payment_id`, `mp_payments` row `beds24_push_status='ok'`, Beds24 `status='confirmed'`
8. Repetir con RdM fechas **2027-01-15 → 2027-01-17**
9. Cancelar ambas en Beds24 manualmente post-smoke

## Out-of-scope findings

- **MAKE_BOOKING_WEBHOOK_URL var** en `wrangler.toml` apps/web — cleanup separado, Alex manual post-merge
- **Backfill** `beds24_booking_id` en bookings expired 17-22 may — confirmados tests internos, Alex decide si aplica

## Decisions pendientes

Ninguna. Spec §3 todas cerradas por Alex/WC.

## Surprises

- `BEDS24_TOKEN` ya existía en Pages prod secrets → apps/web listo sin provisionar post-merge
- El cron `expireHolds` tenía bug silencioso (pasaba UUID D1 a Beds24 en lugar de `beds24_booking_id`) — corregido en scope per §4.6
- Beds24 POST response: `[{success:true, new:{id:...}}]` — `new.id` sí existe para nuevas reservas (distinto a invoice items, ver CLAUDE.md)

— CC-Bot
