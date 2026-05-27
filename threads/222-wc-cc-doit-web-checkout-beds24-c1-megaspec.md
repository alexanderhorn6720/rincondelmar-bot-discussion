# Megaspec: Web checkout → Beds24 source-of-truth (Opción C1)

**Thread**: 222
**Author**: WC
**Date**: 2026-05-27
**Type**: spec (DoIt)
**Priority**: P0 — payment flow broken in production
**Estimated effort**: 6-10h CC Sonnet
**Estimated cost**: $8-15 USD
**Status**: ready_for_cc
**Related**: threads 158, 167, 168 (b24- flow shipped); bookings reconciled today: Olivia (D1 `1f07a5f8...` → B24 `87419757`), Jesús Olguin (D1 `cf7bae80...` → B24 `86748088`)

---

## §1 Contexto

### 1.1 Problema descubierto 2026-05-27 14:00 MX

El flujo `/reservar` (apps/web) lleva ~10 días roto en producción. Síntoma: clientes pagan vía MercadoPago, reciben confirmación de MP, pero el sistema RDM nunca registra el pago. La reserva en D1 queda en `pending_payment`, expira a las 24h (`status='expired'`), y Beds24 nunca recibe la reserva. Resultado: pagos cobrados sin reserva en calendar = riesgo real de overbooking.

### 1.2 Víctimas confirmadas hoy (reconciliadas manualmente por Alex + WC)

| Booking D1 | Guest | Pago MP | Booking Beds24 manual |
|---|---|---|---|
| `1f07a5f8-f5de-4673-8e4d-4661de04f219` | Olivia Zuiga (le_bore@hotmail.com) | 160471230899 ($8,000) | 87419757 |
| `cf7bae80-31ba-44f4-a58a-5ad94fa3d2c2` | Jesús Olguin (embutidosolguin@hotmail.com) | 159856409495 ($8,000) | 86748088 |

Ambas D1 ya tienen `status='paid'` + `mp_payment_id` poblado vía UPDATE manual (WC 2026-05-27 14:15). Resto de bookings legacy en `bookings` (10 expired desde 17-may) eran tests internos o reintentos no completados — confirmado por Alex.

### 1.3 Root cause

El worker-pago (`apps/worker-pago/src/webhook-mp.ts`) tiene un branch único que **solo procesa pagos con `external_reference` formato `b24-{beds24_id}`**:

```ts
// webhook-mp.ts línea ~120
if (!externalRef.startsWith("b24-")) {
  console.warn({ sub: "unsupported_external_ref", paymentId, externalRef });
  return c.text("ok", 200);   // ← silenciosamente botado
}
```

Pero `apps/web/src/pages/api/payment-link.ts` envía `external_reference: booking.id` (UUID v4 sin prefijo). Resultado: webhook llega, worker-pago lo bota silenciosamente con 200 OK, y MP nunca reintenta.

### 1.4 Por qué el flujo legacy (b24-) funciona

Cuando Karina cobra extras desde `/admin/bookings/{beds24_id}`, la reserva Beds24 YA existe (vino por canal Airbnb/Booking.com). El admin genera link MP con `external_reference=b24-86656366`. Worker-pago añade invoice item al booking Beds24 existente. Funciona porque Beds24 ya es source-of-truth.

### 1.5 Decisión arquitectural (Alex 2026-05-27 14:30)

**Opción C1** votada: Beds24 como source-of-truth desde el momento del hold. `apps/web` crea la reserva en Beds24 con `status='request'` (slot bloqueado pero cancelable) en el momento de POST `/api/hold`. Guarda `beds24_booking_id` en columna nueva de `bookings`. Al pagar, PATCH a Beds24 → `status='confirmed'`. Al expirar hold, PATCH a Beds24 → `status='cancelled'`.

**Make scenario `MAKE_BOOKING_WEBHOOK_URL`** (fire-and-forget actual): **sunset**. apps/web llama Beds24 API directo.

**Casa Chamán** (`room_id=679176`): permanece en enum `propertyId` pero NO surfacea en frontend ni en quote. Anti-pattern de memoria respetado.

### 1.6 Por qué NO C2 (solo al pagar)

C2 dejaría ventana de 24h con riesgo de overbooking real: si una reserva entra por Airbnb en la misma fecha mientras el hold de apps/web está pendiente en D1, Beds24 no se entera. C1 cierra esa ventana.

---

## §2 Scope

### 2.1 IN SCOPE

#### Backend (apps/web)
1. **Schema D1**: agregar columna `beds24_booking_id INTEGER` a `bookings` (migration nueva)
2. **Library nueva** `apps/web/src/lib/beds24-direct.ts` con:
   - `createBeds24Request(env, input)` — POST `/v2/bookings` con `status: 'request'`
   - `confirmBeds24Booking(env, beds24_id, reason)` — PATCH `status: 'confirmed'`
   - `cancelBeds24Booking(env, beds24_id, reason)` — PATCH `status: 'cancelled'`
3. **Endpoint refactor** `apps/web/src/pages/api/hold.ts`:
   - Después de `createHoldRaceSafe` exitoso, llamar `createBeds24Request` **síncrono** (no fire-and-forget)
   - Si Beds24 falla: rollback D1 (status='cancelled' reason='beds24_create_failed') + return 502
   - Si Beds24 ok: UPDATE `bookings.beds24_booking_id`
   - REMOVER call a `MAKE_BOOKING_WEBHOOK_URL` (sunset)
4. **Library** `apps/web/src/lib/bookings.ts`: agregar `updateBeds24BookingId(db, bookingId, beds24Id)`

#### Backend (apps/worker-pago)
5. **Refactor** `apps/worker-pago/src/webhook-mp.ts`:
   - Detectar UUID v4 (regex) vs `b24-{n}` (existente)
   - Branch UUID: lookup `bookings` D1 por `id`; tomar `beds24_booking_id` de la row
   - UPDATE `bookings` D1 → `status='paid'`, `mp_payment_id`, `paid_at`
   - PATCH Beds24 → `status='confirmed'`
   - Mantener branch `b24-` sin cambios
6. **Cron `expireHolds`** en `apps/worker-pago/src/crons.ts`:
   - **Bug fix**: línea ~150 actualmente pasa `b.id` (UUID D1) a `releaseBeds24Hold`. Debe ser `b.beds24_booking_id`
   - Si la row no tiene `beds24_booking_id` (legacy), skip Beds24 release con warn

#### Frontend (apps/web)
7. **Manejo de error 502 en /reservar UI**: mostrar "No pudimos bloquear las fechas en el sistema. Inténtalo de nuevo o contáctanos por WhatsApp."

### 2.2 OUT OF SCOPE

- Reescritura schema bookings (solo ADD COLUMN)
- Migrar pagos históricos huérfanos del 17-22 may (confirmado: pruebas internas)
- Cambiar flujo admin `/admin/bookings/{id}` (b24- branch intacto)
- Modificar quote, availability, race-safe insert
- UI changes más allá del mensaje de error 502
- Telegram notify changes
- Tests E2E automatizados (smoke manual sí — §5)
- Refactor mp.ts (sigue enviando UUID como external_reference)
- Borrar columnas obsoletas
- Casa Chamán: queda en enum, no se surfacea (memoria respetada)

### 2.3 OUT OF SCOPE pero importante (issues separados)

- Borrar Make scenario MAKE_BOOKING_WEBHOOK_URL en make.com (Alex manual post-merge)
- Eliminar var en wrangler.toml apps/web
- Backfill `beds24_booking_id` en rows expired legacy (no critical, Alex decide)

---

## §3 Decisiones cerradas (no re-litigar)

| # | Decisión | Confirmado por |
|---|---|---|
| D1 | Opción C1 (Beds24 source-of-truth desde hold) | Alex 14:30 |
| D2 | Make MAKE_BOOKING_WEBHOOK_URL → sunset | Alex 14:30 |
| D3 | Casa Chamán dejar en enum, frontend no la surfacea | Alex 14:30 |
| D4 | apps/web llama Beds24 API directo, NO Service Binding | WC 14:35 |
| D5 | Hold = Beds24 `status='request'` (confirmar en docs durante CC; si no existe, fallback `inquiry` o `new`) | WC 14:35 |
| D6 | `bookings.beds24_booking_id` NULL allowed (no UNIQUE) — legacy expired tiene NULL | WC 14:35 |
| D7 | UUID detection regex `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` | WC 14:35 |
| D8 | Sync (no fire-and-forget) en hold.ts → Beds24. Silent failure es lo que nos trajo aquí | WC 14:35 |
| D9 | Smoke test: 2 bookings 2027 reales a $20 MXN end-to-end | Alex 14:35 |

---

## §4 Implementación

### 4.1 Migration D1

CC ejecuta audit primero:
```bash
ls apps/worker-bot/migrations/ | sort | tail -5
```

Reservar siguiente número. Contenido:

```sql
-- thread/222 - Web checkout creates Beds24 reservation at hold time
ALTER TABLE bookings ADD COLUMN beds24_booking_id INTEGER;

-- Backfill manual reconcile 2026-05-27
UPDATE bookings SET beds24_booking_id = 87419757 WHERE id = '1f07a5f8-f5de-4673-8e4d-4661de04f219';
UPDATE bookings SET beds24_booking_id = 86748088 WHERE id = 'cf7bae80-31ba-44f4-a58a-5ad94fa3d2c2';

CREATE INDEX IF NOT EXISTS idx_bookings_beds24_booking_id ON bookings(beds24_booking_id);
```

Aplicar local: `wrangler d1 migrations apply rincon --local`. Remote: Alex post-merge.

### 4.2 `apps/web/src/lib/beds24-direct.ts` (nuevo)

```ts
const BEDS24_BASE = 'https://api.beds24.com/v2';

interface Beds24Env { BEDS24_TOKEN?: string }

export interface CreateBeds24RequestInput {
  room_id: number;
  property_id?: number;   // default 31862
  arrival: string;         // YYYY-MM-DD
  departure: string;
  num_adults: number;
  guest_first_name?: string;
  guest_last_name?: string;
  guest_email?: string;
  guest_phone?: string;
  total_amount_mxn: number;
  deposit_amount_mxn: number;
  notes?: string;
  channel_reservation_code?: string;  // = bookings.id UUID
}

export type Beds24Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; httpStatus?: number };

export async function createBeds24Request(
  env: Beds24Env,
  input: CreateBeds24RequestInput,
): Promise<Beds24Result<{ beds24_booking_id: number }>> {
  if (!env.BEDS24_TOKEN) return { ok: false, error: 'BEDS24_TOKEN not configured' };

  const body = [{
    roomId: input.room_id,
    propertyId: input.property_id ?? 31862,
    status: 'request',
    arrival: input.arrival,
    departure: input.departure,
    numAdult: input.num_adults,
    firstName: input.guest_first_name ?? '',
    lastName: input.guest_last_name ?? '',
    email: input.guest_email ?? '',
    phone: input.guest_phone ?? '',
    price: input.total_amount_mxn,
    deposit: input.deposit_amount_mxn,
    notes: input.notes ?? '',
    reference: input.channel_reservation_code ?? '',
    referer: 'rincondelmar.club',
  }];

  let res: Response;
  try {
    res = await fetch(`${BEDS24_BASE}/bookings`, {
      method: 'POST',
      headers: { token: env.BEDS24_TOKEN, accept: 'application/json', 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    return { ok: false, httpStatus: res.status, error: `beds24 ${res.status}: ${text.slice(0, 300)}` };
  }

  const json: unknown = await res.json().catch(() => null);
  if (!Array.isArray(json) || !json[0]?.success || !json[0]?.new?.id) {
    return { ok: false, httpStatus: res.status, error: `beds24 non-success: ${JSON.stringify(json).slice(0, 300)}` };
  }

  const beds24Id = Number(json[0].new.id);
  if (!Number.isInteger(beds24Id) || beds24Id <= 0) {
    return { ok: false, httpStatus: res.status, error: `beds24 returned invalid id: ${JSON.stringify(json[0].new)}` };
  }
  return { ok: true, data: { beds24_booking_id: beds24Id } };
}

export async function confirmBeds24Booking(env: Beds24Env, beds24Id: number, reason: string): Promise<Beds24Result<void>> {
  if (!env.BEDS24_TOKEN) return { ok: false, error: 'BEDS24_TOKEN not configured' };
  if (!Number.isInteger(beds24Id) || beds24Id <= 0) return { ok: false, error: 'invalid beds24_booking_id' };
  let res: Response;
  try {
    res = await fetch(`${BEDS24_BASE}/bookings/${beds24Id}`, {
      method: 'PATCH',
      headers: { token: env.BEDS24_TOKEN, accept: 'application/json', 'content-type': 'application/json' },
      body: JSON.stringify({ status: 'confirmed', comments: `Auto-confirmed: ${reason}` }),
    });
  } catch (err) { return { ok: false, error: String(err) }; }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    return { ok: false, httpStatus: res.status, error: `beds24 ${res.status}: ${text.slice(0, 300)}` };
  }
  return { ok: true, data: undefined };
}

export async function cancelBeds24Booking(env: Beds24Env, beds24Id: number, reason: string): Promise<Beds24Result<void>> {
  // Same shape as confirm but status='cancelled'
  if (!env.BEDS24_TOKEN) return { ok: false, error: 'BEDS24_TOKEN not configured' };
  if (!Number.isInteger(beds24Id) || beds24Id <= 0) return { ok: false, error: 'invalid beds24_booking_id' };
  let res: Response;
  try {
    res = await fetch(`${BEDS24_BASE}/bookings/${beds24Id}`, {
      method: 'PATCH',
      headers: { token: env.BEDS24_TOKEN, accept: 'application/json', 'content-type': 'application/json' },
      body: JSON.stringify({ status: 'cancelled', comments: `Auto-cancelled: ${reason}` }),
    });
  } catch (err) { return { ok: false, error: String(err) }; }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    return { ok: false, httpStatus: res.status, error: `beds24 ${res.status}: ${text.slice(0, 300)}` };
  }
  return { ok: true, data: undefined };
}
```

### 4.3 `apps/web/src/lib/bookings.ts` — agregar

```ts
export async function updateBeds24BookingId(db: D1Database, bookingId: string, beds24BookingId: number): Promise<void> {
  const now = Math.floor(Date.now() / 1000);
  await db.prepare(`UPDATE bookings SET beds24_booking_id = ?, updated_at = ? WHERE id = ?`)
    .bind(beds24BookingId, now, bookingId).run();
}
```

### 4.4 `apps/web/src/pages/api/hold.ts` — refactor

Reemplazar bloque `MAKE_BOOKING_WEBHOOK_URL` con:

```ts
const now = Math.floor(Date.now() / 1000);

const beds24Result = await createBeds24Request(env, {
  room_id: roomId,
  arrival: input.checkIn,
  departure: input.checkOut,
  num_adults: input.guests,
  guest_first_name: user.name ?? '',
  guest_email: user.email,
  guest_phone: user.phone ?? '',
  total_amount_mxn: quote.total,
  deposit_amount_mxn: quote.depositAmount,
  notes: input.notes ?? '',
  channel_reservation_code: localBookingId,
});

if (!beds24Result.ok) {
  await env.DB.prepare(
    `UPDATE bookings SET status='cancelled', cancelled_at=?, cancellation_reason='beds24_create_failed', updated_at=? WHERE id=?`,
  ).bind(now, now, localBookingId).run();
  console.error('[hold] beds24 create failed', { bookingId: localBookingId, error: beds24Result.error });
  return Response.json(
    { error: 'beds24_create_failed', details: beds24Result.error?.slice(0, 200) },
    { status: 502 },
  );
}

await updateBeds24BookingId(env.DB, localBookingId, beds24Result.data.beds24_booking_id);

// REMOVE: old `if (env.MAKE_BOOKING_WEBHOOK_URL)` block
```

Imports:
```ts
import { createBeds24Request } from '@/lib/beds24-direct';
import { updateBeds24BookingId } from '@/lib/bookings';
```

### 4.5 `apps/worker-pago/src/webhook-mp.ts` — refactor

Línea ~120 (rechazo `unsupported_external_ref`), reemplazar:

```ts
const externalRef = payment.external_reference ?? '';
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

let beds24BookingId: number;
let webBookingId: string | null = null;

if (externalRef.startsWith('b24-')) {
  beds24BookingId = Number.parseInt(externalRef.slice(4), 10);
  if (!Number.isInteger(beds24BookingId) || beds24BookingId <= 0) {
    console.warn(JSON.stringify({ event: 'mp_webhook', sub: 'bad_external_ref', paymentId, externalRef }));
    return c.text('ok', 200);
  }
} else if (UUID_REGEX.test(externalRef)) {
  const webRow = await env.DB.prepare(
    `SELECT id, beds24_booking_id FROM bookings WHERE id = ? LIMIT 1`,
  ).bind(externalRef).first<{ id: string; beds24_booking_id: number | null }>();

  if (!webRow) {
    console.warn(JSON.stringify({ event: 'mp_webhook', sub: 'web_booking_not_found', paymentId, externalRef }));
    return c.text('ok', 200);
  }
  if (!webRow.beds24_booking_id) {
    console.error(JSON.stringify({ event: 'mp_webhook', sub: 'web_booking_missing_beds24_id', paymentId, externalRef }));
    return c.text('ok', 200);
  }
  beds24BookingId = webRow.beds24_booking_id;
  webBookingId = webRow.id;
} else {
  console.warn(JSON.stringify({ event: 'mp_webhook', sub: 'unsupported_external_ref', paymentId, externalRef }));
  return c.text('ok', 200);
}
```

En el bloque `payment.status === 'approved'`, después de `pushMpPayment` exitoso:

```ts
if (push.ok && webBookingId) {
  await env.DB.prepare(
    `UPDATE bookings SET status='paid', mp_payment_id=?, paid_at=?, updated_at=? WHERE id=?`,
  ).bind(paymentId, paidAt ?? now, now, webBookingId).run();

  // PATCH Beds24 status='request' → 'confirmed' (inline, no shared lib between workers)
  try {
    const patchRes = await fetch(`https://api.beds24.com/v2/bookings/${beds24BookingId}`, {
      method: 'PATCH',
      headers: { token: env.BEDS24_TOKEN!, 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify({ status: 'confirmed', comments: `Auto-confirmed via MP ${paymentId}` }),
    });
    if (!patchRes.ok) {
      console.error(JSON.stringify({ event: 'mp_webhook', sub: 'beds24_confirm_failed', paymentId, beds24BookingId, httpStatus: patchRes.status }));
      // Don't fail webhook — payment persisted, status lagging is recoverable
    }
  } catch (err) {
    console.error('[mp_webhook] beds24 confirm threw', err);
  }
}
```

### 4.6 `apps/worker-pago/src/crons.ts` — fix expireHolds bug

Línea actual:
```ts
const released = await releaseBeds24Hold(env, b.id, 'hold_expired');
```

`b.id` es UUID D1, NO el ID Beds24. Refactor:

```ts
for (const b of expired) {
  await env.DB.prepare(
    `UPDATE bookings SET status='expired', cancelled_at=?, cancellation_reason='hold_expired', updated_at=? WHERE id=?`,
  ).bind(now, now, b.id).run();

  if (b.beds24_booking_id) {
    try {
      const released = await releaseBeds24Hold(env, b.beds24_booking_id, 'hold_expired');
      if (!released.ok) {
        console.error('[cron:expireHolds] beds24 release failed', {
          booking_id: b.id,
          beds24_booking_id: b.beds24_booking_id,
          httpStatus: released.httpStatus,
          error: released.error,
        });
      }
    } catch (err) {
      console.error('[cron:expireHolds] beds24 release threw', b.id, err);
    }
  } else {
    console.warn('[cron:expireHolds] no beds24_booking_id', b.id);
  }
  // existing email notification logic
}
```

### 4.7 Frontend mensaje 502

Localizar componente que llama `/api/hold`. Cuando response 502 + `error === 'beds24_create_failed'`:

```
"No pudimos bloquear las fechas en el sistema. Por favor inténtalo de nuevo en unos minutos, o contáctanos por WhatsApp: +52 744 144 1575 (Karina)."
```

### 4.8 BEDS24_TOKEN en apps/web

Verificar `wrangler secret list` en apps/web. Si falta, documentar en reporte. Alex provisiona post-merge:

```bash
cd apps/web && wrangler secret put BEDS24_TOKEN
```

### 4.9 MAKE_BOOKING_WEBHOOK_URL sunset

- Remover bloque fire-and-forget en `hold.ts` línea ~95
- Var en wrangler.toml: dejar (cleanup separado por Alex)

---

## §5 Tests + Smoke

### 5.1 Unitarios

- `apps/web/src/lib/beds24-direct.test.ts` — mock fetch, validar POST shape
- `apps/web/src/pages/api/hold.test.ts` — rollback D1 si Beds24 falla
- `apps/worker-pago/src/webhook-mp.test.ts` — UUID flow encuentra/not found/missing beds24_id

### 5.2 Quality gates

```bash
cd apps/web && pnpm typecheck && pnpm lint && pnpm build
cd apps/worker-pago && pnpm typecheck && pnpm lint && pnpm build
```

### 5.3 Smoke test (Alex ejecuta post-deploy)

1. `https://rincondelmar.club/reservar/huerta-cocotera`
2. Fechas: **2027-01-10 → 2027-01-12** (precio ~bajo)
3. Login admin@rincondelmar.club
4. Click Reservar → verificar D1 `bookings` row: `status='hold'`, `beds24_booking_id` poblado
5. Beds24 dashboard: nueva reserva `status='request'`, fechas, comments con UUID
6. Pay $20 con NuBank débito (real, no sandbox)
7. Verify:
   - D1 `bookings.status='paid'`, `mp_payment_id` poblado
   - D1 `mp_payments` row nueva con `beds24_push_status='ok'`
   - Beds24 booking `status='confirmed'` con invoice item
   - Telegram notification
8. Repetir con RdM fechas **2027-01-15 → 2027-01-17**
9. Cancelar ambas en Beds24 manualmente post-smoke

### 5.4 Test expireHolds

1. Crear hold sin pagar
2. `UPDATE bookings SET hold_expires_at = unixepoch() - 60 WHERE id = '...'`
3. Esperar próximo cron `*/30` (o invocar manual)
4. Verificar D1 `expired`, Beds24 `cancelled`

---

## §6 Definición de Done

- [ ] Migration creada y aplicada local
- [ ] `beds24-direct.ts` creado con 3 funciones, typecheck pass
- [ ] `bookings.ts` tiene `updateBeds24BookingId`
- [ ] `hold.ts` refactorizado: sync Beds24, rollback, NO Make
- [ ] `webhook-mp.ts` UUID branch funcional
- [ ] `webhook-mp.ts` UPDATE bookings + PATCH Beds24 confirmed en UUID flow
- [ ] `crons.ts` expireHolds bug fix
- [ ] Frontend 502 user-friendly
- [ ] Tests unitarios pasan
- [ ] typecheck + lint + build pass apps/web + apps/worker-pago
- [ ] PR creado, descripción mobile-friendly
- [ ] Self-review pre-merge: sin scope creep, mp.ts intacto
- [ ] Reporte final thread/223

---

## §7 Riesgos + mitigaciones

| # | Riesgo | Prob | Sev | Mitigación |
|---|---|---|---|---|
| R1 | Beds24 v2 rechaza `status='request'` | Media | Alta | Consultar docs Beds24. Si no, fallback `inquiry`/`new`. Halt >30 min y reportar |
| R2 | apps/web sin BEDS24_TOKEN | Media | Alta | CC verifica + documenta. Alex provisiona post-merge ANTES de deploy |
| R3 | Beds24 rate limit en sync hold | Baja | Media | Try-catch + 502 al user. Manual retry |
| R4 | Race: hold D1 → Beds24 falla → otro user hold en mismas fechas (200ms) | Muy baja | Media | `createHoldRaceSafe` post-check + rollback rápido. Aceptamos |
| R5 | Migration ALTER TABLE bloquea D1 | Baja | Media | ADD COLUMN non-blocking en SQLite 3.35+. Aplicar off-peak |
| R6 | webhook-mp procesa antes que hold escriba D1 | Muy baja | Alta | MP no envía webhook antes de cobrar. Si pasa, MP reintenta naturalmente |
| R7 | CC modifica mp.ts external_reference accidentalmente | Baja | Crítica | Self-review pre-merge: diff de mp.ts debe estar vacío |
| R8 | Cost LLM excede budget | Media | Baja | Hard stop $22 (1.5x). Sonnet default activo |
| R9 | Tests E2E faltantes | Alta | Media | Aceptamos. Smoke manual cubre |
| R10 | Alex cambia cuenta MP de nuevo | Baja | Alta | Documentar: rotar MP_WEBHOOK_SECRET en TODOS workers |

---

## §8 Cost budget

| Item | Estimado |
|---|---|
| CC Sonnet (6-10h) | $8-15 |
| Beds24 API smoke | $0 |
| MP smoke fees | $0.66 (commission x 2 pagos $20) |
| **Total** | **$8-16** |

Hard stop: $22.

---

## §9 Deploy plan

CC NO deploys. Alex ejecuta:

1. Review PR en mobile
2. Merge PR
3. `cd apps/worker-pago && pnpm wrangler deploy`
4. `cd apps/web && pnpm wrangler pages deploy` (o auto)
5. `wrangler d1 migrations apply rincon --remote`
6. `cd apps/web && wrangler secret list` → si falta `BEDS24_TOKEN`, `wrangler secret put BEDS24_TOKEN`
7. Smoke §5.3
8. Post-smoke: cleanup Make scenario (separate issue)

---

## §10 Out-of-scope findings

CC abre issues NO arregla inline:
- Otros lugares con Make webhook
- Casa Chamán refs frontend
- Bookings legacy cleanup
- Tests faltantes

---

## §11 Self-review pre-PR

1. `git diff main..feat/web-checkout-beds24-c1 --stat` — solo archivos en scope
2. `mp.ts` diff vacío ✓
3. No secretos plaintext ✓
4. No ALTER TABLE runtime ✓
5. Migration additive ✓
6. Conventional Commits ✓
7. No viernes post-5pm (hoy miércoles 27-may, OK) ✓

---

## §12 Reporte final (thread/223)

```markdown
---
thread: 223
author: cc-bot
date: 2026-05-27
type: doit-report
related_spec: thread/222
status: ready_for_alex_deploy
---

## DoIt 222 completion report

### Files modified
[list with LoC]

### Tests
typecheck/lint/test/build: PASS

### Cost
LLM: $X; Time: Xh

### Deploy checklist for Alex
[copy §9]

### Out-of-scope findings
[list issues]

### Smoke instructions
[copy §5.3]
```

---

## §13 Pre-flight CC

```bash
cd /c/dev/rdm/dev/bot && git status                       # clean?
git checkout main && git pull --rebase origin main        # latest
git checkout -b feat/web-checkout-beds24-c1               # branch
ls apps/worker-bot/migrations/ | sort | tail -3           # next migration #
cd apps/web && wrangler secret list                       # BEDS24_TOKEN present?
```

Si falla → STOP, reportar thread.

---

## §14 Estimación final

| Métrica | Valor |
|---|---|
| Effort | 6-10h CC Sonnet |
| Files | ~6 |
| LoC delta | ~400-600 |
| Cost | $8-15 |
| Risk | Medium (production payment, rollback-safe) |
| Reversibility | High |

**Done**: CC reporta en thread/223. Alex deploy + smoke. Si smoke pasa, spec cerrado. Si falla, thread/224 findings.

— END SPEC —
