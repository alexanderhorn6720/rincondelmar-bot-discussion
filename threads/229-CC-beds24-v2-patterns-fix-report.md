---
thread: 229
author: CC
date: 2026-05-28
topic: beds24-v2-patterns-fix-report
mode: report
status: open
---

# DoIt thread/228 — Reporte final

**PR**: [#197](https://github.com/alexanderhorn6720/rdm-bot/pull/197) — `fix/beds24-v2-patterns-and-cron-filter`
**Branch**: `fix/beds24-v2-patterns-and-cron-filter`
**Tiempo estimado**: ~4h (context + implementation)
**Tests**: 44/44 worker-pago · 651/651 web · biome limpio

---

## Qué se hizo

### B1 — PATCH → POST para modify booking

`PATCH /v2/bookings/{id}` no existe en Beds24 v2. El endpoint correcto es
`POST /v2/bookings [{id, status, comment}]` pasando el `id` de un booking
existente en el array — el mismo endpoint que crea bookings, pero con `id`
incluido actúa como modify.

Se creó un helper compartido `modifyBeds24BookingStatus` en ambos workers:
- `apps/worker-pago/src/beds24-modify.ts`
- `apps/web/src/lib/beds24-modify.ts`

Sites corregidos (4):
1. `apps/worker-pago/src/beds24-release.ts` — cancel on hold expiry
2. `apps/worker-pago/src/webhook-mp.ts` — confirm booking on MP approved
3. `apps/web/src/lib/beds24-direct.ts` → `confirmBeds24Booking`
4. `apps/web/src/lib/beds24-direct.ts` → `cancelBeds24Booking`

### B2 — invoiceItem charge en createBeds24Request

Beds24 mostraba **Cargos: $0** porque el booking se creaba sin `invoiceItems`.
Ahora `createBeds24Request` incluye:

```json
{ "type": "charge", "qty": 2, "amount": 4000, "description": "Hospedaje 2 noches Huerta Cocotera" }
```

`qty` = noches calculadas del date diff. `amount` = `round(total / noches)`.
`description` usa `ROOM_NAMES` local (copia de `@rdm/shared/constants.ts`).

**Nota**: rounding puede producir ±$1 en el total si hay decimales. Beds24
usa la suma de `invoiceItems` para el total de factura, no el campo `price`
del booking — aceptable para propiedades con precios enteros.

### B3 — cron mpPaymentRetry filtra solo status='approved'

Sin filtro, filas `refunded`/`charged_back` con `beds24_push_status='error'`
eran re-intentadas indefinidamente como si fueran nuevos pagos positivos.

Fix: `AND status = 'approved'` en la query del cron (`apps/worker-pago/src/crons.ts`).

---

## Archivos cambiados (10)

| Archivo | Cambio |
|---|---|
| `apps/worker-pago/src/beds24-modify.ts` | NUEVO — helper POST modify |
| `apps/web/src/lib/beds24-modify.ts` | NUEVO — mismo helper en web |
| `apps/worker-pago/src/beds24-release.ts` | Reescrito — usa modifyBeds24BookingStatus |
| `apps/worker-pago/src/webhook-mp.ts` | Usa modifyBeds24BookingStatus para confirm |
| `apps/worker-pago/src/crons.ts` | B3: AND status='approved' |
| `apps/web/src/lib/beds24-direct.ts` | B1 confirm/cancel + B2 invoiceItems |
| `apps/worker-pago/tests/beds24-release.test.ts` | Reescrito — assert POST shape |
| `apps/worker-pago/tests/crons.test.ts` | NUEVO — assert B3 SQL filter |
| `apps/worker-pago/tests/webhook-mp.test.ts` | UUID flow: assert 2× POST Beds24 |
| `apps/web/tests/beds24-direct.test.ts` | B1+B2 assertions |

---

## Decisiones pendientes

Ninguna — scope estricto, sin opciones bloqueadas.

## Surprises

- `beds24-release.ts` usaba IDs string tipo `'bk_987'` (patrón del hold flow antiguo).
  B1 requirió cambiar la validación a numérica pura. Los IDs de Beds24 v2 siempre son integers.
  Si el hold flow vuelve con IDs string propios del sistema, habrá que re-ajustar esa función.

- El campo de body `comment` (singular) vs `comments` (plural) que tenía el PATCH antiguo.
  El spec yaml de Beds24 v2 usa `comment` — corregido en el helper.
