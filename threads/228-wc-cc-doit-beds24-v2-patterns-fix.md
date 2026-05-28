# Thread/228 — Fix Beds24 v2 API patterns + cron retry filter + invoiceItem charge

**Type**: DoIt (autonomous)
**Estimated**: 1.5-2h CC Sonnet
**Cost**: $3-5
**Prerequisite**: Threads 222 / 224 / 226 deployed and validated. Smoke test 2 (booking 87427566) showed Beds24 status='Solicitud' instead of 'confirmed', triggering this audit.

---

## §1 Contexto

Smoke test del thread/226 reveló 3 bugs adicionales en el código de integración Beds24, todos relacionados con asunciones incorrectas sobre la API v2.

### B1 — PATCH /v2/bookings/{id} no existe en Beds24 v2

Verificado contra el spec oficial `https://beds24.com/api/v2/apiV2.yaml` (descargado 2026-05-27, 263KB):

```
/bookings:        GET, POST, DELETE  (NO PATCH)
/bookings/messages
/bookings/invoices
```

**No existe path `/v2/bookings/{id}`. No existe método PATCH en ningún endpoint de bookings.**

El patrón canónico para modificar bookings (cambio de status, comments, etc.) es:

```http
POST /v2/bookings
Content-Type: application/json
token: ...

[
  { "id": 7654321, "status": "cancelled", "comment": "..." }
]
```

Documentado en el yaml oficial bajo `multipleNewBookings.value[2]`:
> "This is an existing booking that will be cancelled"

**Sitios actualmente rotos (PATCH sin efecto, error silencioso solo loggeado)**:

| Archivo | Función | Llamado en prod | Impacto |
|---|---|---|---|
| `apps/worker-pago/src/webhook-mp.ts` | confirm inline post-payment (~línea 250) | ✅ SÍ | Post-pago: D1='paid' pero Beds24 sigue 'request' |
| `apps/worker-pago/src/beds24-release.ts` | `releaseBeds24Hold` | ✅ SÍ (cron `*/30`) | Holds expirados no se liberan en Beds24 → inventario bloqueado |
| `apps/web/src/lib/beds24-direct.ts` | `confirmBeds24Booking` | ❌ dead code | Función expuesta no llamada |
| `apps/web/src/lib/beds24-direct.ts` | `cancelBeds24Booking` | ❌ dead code | Función expuesta no llamada |

**Por qué pasaron los tests**: los tests mockean `fetch` y solo verifican que se llame con un URL/method consistente. Nunca validaron el patrón contra Beds24 real.

**Evidencia visible**: booking 87427566 (smoke 2 del thread/226) muestra Pagos $1,000 (✅) pero Estado="Solicitud" (❌) en panel Beds24.

### B2 — createBeds24Request no crea invoiceItem type='charge'

`apps/web/src/lib/beds24-direct.ts::createBeds24Request` envía `price` como metadata del body, pero **NO crea un invoiceItem `type='charge'`**. Beds24 v2 separa `price` (informativo) de invoiceItems (líneas reales que cuentan al balance).

**Evidencia visible**: booking 87427566 muestra "Cargos totales: 0 MXN" cuando el guest debería estar cargado con $2,030 (2 noches × $1,015).

Schema oficial (yaml línea 3771-3800):
```yaml
invoiceItemPost:
  properties:
    type:
      enum: [charge, payment]
    qty: integer  # can be negative
    amount: number
    description: string (max 250)
```

Ejemplo oficial (yaml línea 481-497):
```json
{
  "roomId": 322790,
  "arrival": "2022-06-29",
  "departure": "2022-07-09",
  "invoiceItems": [
    { "type": "charge", "qty": 2, "amount": 50 }
  ]
}
```

### B3 — Cron mpPaymentRetry empuja pagos refunded

**Bug confirmado en producción**: payment `160883911972` (Karina, $20 del 24-may) tuvo este flujo:

1. 2026-05-25: pago approved → push falló (BEDS24_TOKEN expirado) → `push_status='error', attempts=1`
2. 2026-05-25: refund llegó → branch refund vio `push_status='error'` → no compensó (defensivo OK)
3. mp_payments quedó con `status='refunded', push_status='error', attempts=1`
4. 2026-05-28 01:30:48: cron retry corrió post-deploy thread/226 → SELECT `WHERE push_status='error' AND attempts<5` agarró este row → **lo empujó como si fuera approved** ($20 positive payment) → status='ok'

Resultado: **Beds24 booking 86981862 tiene un payment fantasma de $20 que MP ya devolvió**.

Causa raíz en `apps/worker-pago/src/crons.ts::mpPaymentRetry`:

```typescript
SELECT mp_payment_id, ... FROM mp_payments
WHERE beds24_push_status = 'error'
  AND beds24_push_attempts < ?
// ↑ NO filtra por status: ignora si MP ya marcó refunded/charged_back/cancelled
```

---

## §2 Scope

### IN

1. **Fix B1** — Reemplazar `PATCH /v2/bookings/{id}` → `POST /v2/bookings` con body array `[{id, status, comment}]` en:
   - `apps/worker-pago/src/webhook-mp.ts` (confirm post-payment inline call)
   - `apps/worker-pago/src/beds24-release.ts::releaseBeds24Hold`
   - `apps/web/src/lib/beds24-direct.ts::confirmBeds24Booking`
   - `apps/web/src/lib/beds24-direct.ts::cancelBeds24Booking`

2. **Fix B2** — Agregar invoiceItem `type='charge'` en `createBeds24Request`:
   - Calcular nights = (departure - arrival) en días
   - Calcular pricePerNight = round(total_amount_mxn / nights)
   - Push invoiceItem `{type: 'charge', qty: nights, amount: pricePerNight, description: 'Hospedaje N noches {property}'}` en el array body
   - **No tocar `price` y `deposit` metadata** — se mantienen como están

3. **Fix B3** — Filtrar pagos refunded del cron retry:
   - `apps/worker-pago/src/crons.ts::mpPaymentRetry`: añadir `AND status = 'approved'` al WHERE
   - Razón: refunded/charged_back/cancelled/pending/in_process no deben re-empujarse como payment positivo

4. **Tests robustos** — Actualizar tests existentes para validar el shape correcto (NO solo que se llame fetch):
   - Para B1: assert body es array con `[{id, status, comment}]`
   - Para B2: assert body incluye invoiceItems con type='charge', qty=nights, amount calculado
   - Para B3: assert query NO devuelve rows refunded/charged_back

5. **Self-review** pre-PR: validar diff completo, confirmar no scope creep, payment-flow lock list respetada.

### OUT

- Cleanup de payment fantasma de Karina en Beds24 86981862 — **Alex hace manual en dashboard**
- Backfill confirmar status='confirmed' de Olivia (87419757) + Jesús (86748088) + smoke 2 (87427566) — **Alex hace manual**
- Refactor a `@rdm/beds24` shared package (Wave 2)
- Cambiar el comportamiento defensivo del refund branch en webhook-mp.ts (sigue siendo correcto: si push del approved falló, no compensa con negativo)
- Casa Chamán en hold.ts enum (deuda Q3 2026)
- Deploy (Alex post-merge)
- Smoke test (Alex post-deploy)

---

## §3 Decisiones cerradas

| # | Decisión | Razón |
|---|---|---|
| D1 | 1 solo PR | Mismo dominio (Beds24 v2 patterns), mismo lock list (payment-flow), mergear separados es más fricción |
| D2 | invoiceItem charge usa `qty=nights, amount=pricePerNight` | Beds24 multiplica internamente. lineTotal = qty × amount. Permite ver "2 noches × $1,015" en panel |
| D3 | Description del charge: `Hospedaje N noches {property_name}` | Útil en panel + factura. Property name de PROPERTY_NAMES si existe, fallback a property_id |
| D4 | No agregar charge separado para limpieza/extras | Quote actual no desglosa cleaning fee en `apps/web`. Si se desglosa en futuro, abrir followup |
| D5 | mpPaymentRetry filtra solo status='approved' | Conservador. pending/in_process/authorized podrían cambiar pero no deben empujarse pre-aprobación |
| D6 | Tests validan body shape contra example oficial Beds24 | Evita regresión silenciosa. Reference: yaml oficial líneas 415-440 (multipleNewBookings) y 481-497 (modifyInvoiceItem) |
| D7 | No tocar `pushMpPayment` ni `postPayment` | Ya usan patrón POST correcto. Auditado y verificado |
| D8 | apps/web confirm/cancel se arreglan aunque sean dead code | Trivial, mismo patrón, evita el bug si alguien las llama en futuro |

---

## §4 Implementación

### 4.1 Patrón canónico modify booking (helper opcional)

CC puede crear un helper compartido o inline el patrón en cada sitio. Recomendación: helper inline por archivo (sin shared package, mantiene Wave 2 pendiente).

```typescript
// Patrón canónico para modify booking status en Beds24 v2:
async function modifyBeds24BookingStatus(
  env: AuthEnv,
  beds24Id: number,
  status: 'confirmed' | 'cancelled' | 'request',
  comment: string
): Promise<{ ok: boolean; httpStatus?: number; error?: string }> {
  let token: string;
  try {
    token = await getBeds24AccessToken(env);
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }

  let res: Response;
  try {
    res = await fetch('https://api.beds24.com/v2/bookings', {
      method: 'POST',
      headers: { token, accept: 'application/json', 'content-type': 'application/json' },
      body: JSON.stringify([{ id: beds24Id, status, comment }]),
    });
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    return { ok: false, httpStatus: res.status, error: `beds24 ${res.status}: ${text.slice(0, 300)}` };
  }

  const json = (await res.json().catch(() => null)) as Array<{ success?: boolean; errors?: unknown }> | null;
  if (!json?.[0]?.success) {
    return { ok: false, httpStatus: res.status, error: `beds24 non-success: ${JSON.stringify(json).slice(0, 300)}` };
  }
  return { ok: true, httpStatus: res.status };
}
```

CC decide si lo inline en cada sitio o lo factoriza. Si factoriza, sugiero `apps/worker-pago/src/beds24-modify.ts` y `apps/web/src/lib/beds24-modify.ts` (no compartido, separado por workspace — mismo razonamiento Wave 2 que beds24-auth.ts).

### 4.2 Cambios específicos por archivo

#### `apps/worker-pago/src/webhook-mp.ts` (~líneas 245-265)

**Antes**:
```typescript
const confirmToken = await getBeds24AccessToken(env);
const patchRes = await fetch(`https://api.beds24.com/v2/bookings/${beds24BookingId}`, {
  method: 'PATCH',
  headers: { token: confirmToken, 'content-type': 'application/json', accept: 'application/json' },
  body: JSON.stringify({
    status: 'confirmed',
    comments: `Auto-confirmed via MP ${paymentId}`,
  }),
});
if (!patchRes.ok) {
  console.error(JSON.stringify({ event: 'mp_webhook', sub: 'beds24_confirm_failed', ... }));
}
```

**Después**:
```typescript
const confirmResult = await modifyBeds24BookingStatus(env, beds24BookingId, 'confirmed',
  `Auto-confirmed via MP ${paymentId}`);
if (!confirmResult.ok) {
  console.error(JSON.stringify({
    event: 'mp_webhook',
    sub: 'beds24_confirm_failed',
    paymentId,
    beds24BookingId,
    httpStatus: confirmResult.httpStatus,
    error: confirmResult.error?.slice(0, 200),
  }));
}
```

Comportamiento sigue best-effort (no bloquea retorno 200).

#### `apps/worker-pago/src/beds24-release.ts`

**Cambiar `releaseBeds24Hold` completo** a usar el patrón POST. Mantener firma `(env, beds24BookingId, reason) => Promise<ReleaseResult>` para compat con caller en crons.ts.

```typescript
export async function releaseBeds24Hold(
  env: ReleaseEnv,
  beds24BookingId: string | number | null | undefined,
  reason: string,
): Promise<ReleaseResult> {
  if (beds24BookingId === null || beds24BookingId === undefined || beds24BookingId === '') {
    return { ok: false, error: 'beds24BookingId required' };
  }
  const id = Number(beds24BookingId);
  if (!Number.isInteger(id) || id <= 0) {
    return { ok: false, error: 'beds24BookingId must be positive integer' };
  }
  return modifyBeds24BookingStatus(env, id, 'cancelled', `Auto-cancelled: ${reason}`);
}
```

Actualizar docstring del archivo: removed "PATCH /bookings/:id" reference, replace con "POST /v2/bookings [{id, status:cancelled}]".

#### `apps/web/src/lib/beds24-direct.ts`

**`confirmBeds24Booking` y `cancelBeds24Booking`**: refactor al patrón POST. Mantener firma original.

**`createBeds24Request`**: agregar invoiceItem charge al body. Cambios:

```typescript
export async function createBeds24Request(
  env: Beds24Env,
  input: CreateBeds24RequestInput,
): Promise<Beds24Result<{ beds24_booking_id: number }>> {
  // ... token logic igual ...

  // Calcular charge breakdown (B2 fix)
  const arrivalDate = new Date(input.arrival);
  const departureDate = new Date(input.departure);
  const nights = Math.round((departureDate.getTime() - arrivalDate.getTime()) / (1000 * 60 * 60 * 24));
  if (nights <= 0) {
    return { ok: false, error: 'departure must be after arrival' };
  }
  const pricePerNight = Math.round(input.total_amount_mxn / nights);
  const propertyName = PROPERTY_NAMES_BY_ROOM[input.room_id] ?? `Room ${input.room_id}`;

  const body = [
    {
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
      price: input.total_amount_mxn,        // metadata, sigue
      deposit: input.deposit_amount_mxn,    // metadata, sigue
      notes: input.notes ?? '',
      reference: input.channel_reservation_code ?? '',
      referer: 'rincondelmar.club',
      invoiceItems: [                       // ← NUEVO B2
        {
          type: 'charge',
          qty: nights,
          amount: pricePerNight,
          description: `Hospedaje ${nights} ${nights === 1 ? 'noche' : 'noches'} ${propertyName}`.slice(0, 250),
        },
      ],
    },
  ];

  // ... fetch igual ...
}
```

`PROPERTY_NAMES_BY_ROOM` se puede importar de `@rdm/shared` si existe ahí; si no, crear constante local. CC verifica primero.

Nota: el `total_amount_mxn / nights` puede generar decimales. Beds24 acepta amount como number. Round a entero pesos para evitar decimales. **Edge case**: si `total = 4500` y `nights = 2`, `pricePerNight = 2250` → lineTotal = $4,500 ✅. Si `total = 4501` y `nights = 2`, `pricePerNight = 2251` → lineTotal = $4,502 (overshooting $1). Aceptable: el price metadata es la fuente de verdad para tarifa total, el charge desglosa por noche.

#### `apps/worker-pago/src/crons.ts::mpPaymentRetry`

**Antes**:
```typescript
const result = await env.DB.prepare(
  `SELECT mp_payment_id, beds24_booking_id, amount_mxn, paid_at,
          payment_method_id, beds24_push_attempts
     FROM mp_payments
    WHERE beds24_push_status = 'error'
      AND beds24_push_attempts < ?
    ORDER BY beds24_push_attempts ASC, paid_at ASC
    LIMIT ?`
).bind(MAX_RETRY_ATTEMPTS, RETRY_BATCH_LIMIT).all();
```

**Después**:
```typescript
const result = await env.DB.prepare(
  `SELECT mp_payment_id, beds24_booking_id, amount_mxn, paid_at,
          payment_method_id, beds24_push_attempts
     FROM mp_payments
    WHERE beds24_push_status = 'error'
      AND beds24_push_attempts < ?
      AND status = 'approved'                                  -- ← B3 fix
    ORDER BY beds24_push_attempts ASC, paid_at ASC
    LIMIT ?`
).bind(MAX_RETRY_ATTEMPTS, RETRY_BATCH_LIMIT).all();
```

Una sola línea. Agregar comentario corto sobre por qué: "Excluye refunded/charged_back/cancelled/pending — solo aprobados deben retried".

### 4.3 Tests

#### Test B1 (worker-pago + apps/web)

Cada función modificada debe tener test que valide:

```typescript
expect(fetchMock).toHaveBeenCalledWith(
  'https://api.beds24.com/v2/bookings',  // ← URL exacta SIN /{id}
  expect.objectContaining({
    method: 'POST',                       // ← NO PATCH
    body: expect.stringMatching(/"id":\s*\d+.*"status":/),  // ← array con id+status
  })
);

// Parse body para verificar shape exacto:
const body = JSON.parse(fetchMock.mock.calls[0][1].body);
expect(Array.isArray(body)).toBe(true);
expect(body[0]).toMatchObject({
  id: expect.any(Number),
  status: 'cancelled',  // o 'confirmed'
  comment: expect.stringContaining('Auto-cancelled'),
});
```

#### Test B2 (apps/web)

```typescript
it('crea booking con invoiceItem charge para nights x pricePerNight', async () => {
  fetchMock.mockResolvedValue({
    ok: true,
    json: async () => [{ success: true, new: { id: 12345 } }],
  });

  await createBeds24Request(env, {
    room_id: 637063,
    arrival: '2026-07-28',
    departure: '2026-07-30',
    num_adults: 4,
    total_amount_mxn: 2030,
    deposit_amount_mxn: 1000,
    // ...
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1].body);
  expect(body[0].invoiceItems).toEqual([
    {
      type: 'charge',
      qty: 2,
      amount: 1015,
      description: expect.stringContaining('Hospedaje 2 noches'),
    },
  ]);
});
```

#### Test B3 (worker-pago crons)

```typescript
it('mpPaymentRetry excluye pagos refunded', async () => {
  // Setup: insertar 1 row approved+error y 1 row refunded+error
  await db.exec(`INSERT INTO mp_payments VALUES ('PAY1', 12345, 'b24-12345', 1000, 'MXN', 'approved', ...)`);
  await db.exec(`INSERT INTO mp_payments VALUES ('PAY2', 12346, 'b24-12346', 500, 'MXN', 'refunded', ...)`);

  await mpPaymentRetry({ DB: db, ... });

  // PAY1 debe ser intentado, PAY2 NO
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const body = JSON.parse(fetchMock.mock.calls[0][1].body);
  expect(body[0].id).toBe(12345);  // beds24_booking_id de PAY1
});
```

### 4.4 Diff de líneas estimado

| Archivo | LoC | Tipo |
|---|---|---|
| `apps/worker-pago/src/beds24-modify.ts` | +50 | NEW (helper, opcional) |
| `apps/web/src/lib/beds24-modify.ts` | +50 | NEW (helper, opcional) |
| `apps/worker-pago/src/webhook-mp.ts` | ~20 modificado | |
| `apps/worker-pago/src/beds24-release.ts` | ~50 reescrito | |
| `apps/web/src/lib/beds24-direct.ts` | ~80 modificado | (confirm, cancel, createRequest) |
| `apps/worker-pago/src/crons.ts` | +2 | (WHERE clause + comentario) |
| Tests | +150 | |
| **Total** | **~400 LoC** | |

---

## §5 Definición de Done

- [ ] B1: 4 sitios usan POST `/v2/bookings` con body `[{id, status, comment}]`
- [ ] B2: `createBeds24Request` envía invoiceItem charge con qty=nights, amount=pricePerNight
- [ ] B3: `mpPaymentRetry` query incluye `AND status='approved'`
- [ ] Tests robustos: validan body shape contra patrón Beds24 oficial (no solo "se llamó fetch")
- [ ] `pnpm -w typecheck` PASS
- [ ] `pnpm -w lint` PASS
- [ ] `pnpm -w build` PASS
- [ ] `pnpm -w test` PASS (40 worker-pago + 649 web + cualquier test nuevo)
- [ ] Self-review pre-merge: diff esperado, sin scope creep, payment-flow lock respetada
- [ ] PR creado con descripción mobile-friendly incluyendo checklist deploy para Alex
- [ ] Reporte final en thread/229

---

## §6 Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | Cambio de `status` en POST /v2/bookings podría tener efecto secundario (notify guest, send confirmation email Beds24-side) | Verificar en Beds24 booking 87427566 post-merge si el switch a 'confirmed' dispara emails. Si sí, anotar en deploy notes para Alex. Beds24 docs no mencionan autoaction triggers en API change |
| R2 | `comment` overwrite vs append | Doc no aclara. Comportamiento conservador: cada PATCH→POST envía un comment nuevo. Si Beds24 sobrescribe, perdemos historial. Si append, OK. **Test manual post-deploy con booking de prueba** |
| R3 | invoiceItem charge falla si Beds24 rechaza shape | Schema oficial yaml líneas 3771-3800 valida shape. Si rechaza, el booking create completo falla → `createBeds24Request` retorna ok:false → rollback D1 existente kicks in. Defensa en profundidad |
| R4 | `pricePerNight` rounding deja $1-2 de diferencia | Acceptable. Aclarar en description "subtotal aproximado, ver Total Booking". Si Alex quiere precisión exacta, abrir followup post-merge |
| R5 | mpPaymentRetry filter rompe edge case raro de pagos `pending` que cambian a approved | Pago pending NO debe pushearse aún. Si llega webhook approved después, el flujo principal en webhook-mp.ts lo procesa con INSERT/UPDATE + push directo. Cron retry es solo para approved cuyo push falló. Comportamiento correcto |
| R6 | Tests mockean fetch — podrían validarse pero fallar en producción si Beds24 cambia API | Aceptable. Spec oficial yaml es la fuente de verdad al momento de spec. Si cambia, abrir followup. Tests deben referenciar URL exacta + method + shape mínimo del body |
| R7 | Helper `modifyBeds24BookingStatus` introduce import circular o tipo mismatch | CC verifica antes de inline vs factorizar. Si hay riesgo, inline en cada sitio (4 copias casi idénticas pero independientes) |
| R8 | apps/web confirm/cancel siendo dead code podría tener consumidores futuros que esperan firma actual | Mantener firma `(env, beds24Id, reason)` idéntica. Solo cambia internal implementation. Backward compat asegurada |

---

## §7 Post-merge (Alex)

### 7.1 Deploy

```powershell
# apps/web auto-deploya via CF Pages al mergear (rincondelmar-bot project)
# worker-pago requiere manual deploy:
cd C:\dev\rdm\dev\bot\apps\worker-pago
npx wrangler deploy
```

### 7.2 Cleanup manual de bookings en limbo

**Karina booking 86981862**: tiene payment fantasma de $20 (B3 antiguo). Eliminar manualmente:
- Beds24 dashboard → booking 86981862 → tab Cargos & Pagos
- Localizar payment con descripción `MP/debvisa 160883911972 [2026-05-24]` fecha 2026-05-28
- Click delete (X) → confirmar

**Smoke 2 booking 87427566**: necesita corregirse manualmente post-deploy:
- Cambiar Estado: Solicitud → Confirmado
- Agregar Cargo: type=Charge, qty=2, amount=1015, description="Hospedaje 2 noches Huerta Cocotera"

**Olivia booking 87419757 (22-25 nov)**: verificar Estado. Si en "Solicitud", cambiar manual a "Confirmado". Verificar payment de $8,000 visible.

**Jesús booking 86748088 (20-22 ago)**: verificar Estado. Si en "Solicitud", cambiar manual a "Confirmado". Verificar payment de $8,000 visible.

### 7.3 Smoke test 3 (validación end-to-end completa)

1. Crear hold fresh: fechas nuevas (ej. 2026-09-10 a 12), Huerta Cocotera, 2 huéspedes
2. **Verificar pre-pago vía MCP**:
   - D1 `bookings` row creada con `beds24_booking_id`
   - Beds24 dashboard: nuevo booking con Estado="Solicitud", **Cargos visibles** (2 noches × pricePerNight), Pagos=0
3. Pagar anticipo (NO refundear)
4. **Verificar post-pago vía MCP**:
   - D1 `bookings.status='paid'`
   - D1 `mp_payments.beds24_push_status='ok'`
   - Beds24 booking Estado="Confirmado", Cargos $X, Pagos $X, Balance $X
5. Cancelar booking en Beds24 dashboard

### 7.4 Forzar retry del pago atascado (opcional)

Si querés validar B3 + B1 en el pago smoke 2 (87427566) atascado:

```sql
UPDATE mp_payments
SET beds24_push_attempts = 0,
    beds24_push_error = NULL,
    updated_at = unixepoch()
WHERE mp_payment_id = '161311704536';
```

(no requerido — el booking 87427566 ya tiene push='ok' por el código del thread/226. Solo confirma manualmente el status en Beds24.)

---

## §8 Pre-flight CC

```bash
cd /c/dev/rdm/dev/bot
git checkout main
git pull --rebase origin main
git log --oneline -3
# Esperado: top commits incluyen PR #196 (thread/226)

# Branch
git checkout -b fix/beds24-v2-patterns-and-cron-filter

# Verifica archivos críticos existen
test -f apps/worker-pago/src/webhook-mp.ts
test -f apps/worker-pago/src/beds24-release.ts
test -f apps/worker-pago/src/crons.ts
test -f apps/web/src/lib/beds24-direct.ts
test -f apps/worker-pago/src/beds24-auth.ts
test -f apps/web/src/lib/beds24-auth.ts

# Verifica los PATCH actualmente presentes (debe encontrar 4)
grep -rn "method: 'PATCH'" apps/worker-pago/src apps/web/src/lib
# Esperado: 4 matches (webhook-mp.ts confirm, beds24-release.ts, beds24-direct.ts confirm, beds24-direct.ts cancel)

# Verifica el SELECT del cron retry actual (debe NO tener status='approved')
grep -A 3 "WHERE beds24_push_status = 'error'" apps/worker-pago/src/crons.ts
# Esperado: SELECT sin filtro status

# Verifica createBeds24Request NO tiene invoiceItems (B2)
grep -c "invoiceItems" apps/web/src/lib/beds24-direct.ts
# Esperado: 0 (la función no las usa todavía)
```

Si cualquier check falla → HALT, reportar en thread.

---

## §9 Reporte final (thread/229)

```markdown
# Thread/229 — DoIt 228 completion report

**Spec**: thread/228
**Branch**: fix/beds24-v2-patterns-and-cron-filter
**PR**: #XXX

## Files changed
- apps/worker-pago/src/beds24-modify.ts (NEW helper, opcional)
- apps/web/src/lib/beds24-modify.ts (NEW helper, opcional)
- apps/worker-pago/src/webhook-mp.ts (PATCH→POST confirm)
- apps/worker-pago/src/beds24-release.ts (PATCH→POST cancel)
- apps/web/src/lib/beds24-direct.ts (PATCH→POST confirm + cancel, + invoiceItem charge)
- apps/worker-pago/src/crons.ts (+ status='approved' filter)
- Tests: validación body shape

## Bugs fixed
- B1: PATCH /bookings/{id} no existía → POST /bookings [{id, status, comment}]
- B2: Cargos=0 en Beds24 → invoiceItem charge en createBeds24Request
- B3: cron retry empujaba pagos refunded → AND status='approved'

## Gates
- typecheck: PASS
- lint: PASS
- build: PASS
- test: XXX PASS

## Validación shape contra spec oficial Beds24
Reference: yaml https://beds24.com/api/v2/apiV2.yaml descargado 2026-05-27
- /bookings: GET, POST, DELETE (no PATCH) ✓
- invoiceItemPost.type enum: [charge, payment] ✓
- multipleNewBookings example: array con {id, status} ✓

## Cost LLM
$X.XX

## Out-of-scope identificado
- Cleanup manual del payment fantasma Karina 86981862
- Backfill confirmado de Olivia/Jesús/smoke 2
- Refactor @rdm/beds24 shared package (Wave 2)
```

---

## §10 Notas

- Este DoIt cierra la auditoría iniciada con el smoke test del thread/226.
- Los 3 bugs fueron silenciosos: log-only errors, tests con mocks débiles, sin alertas en producción.
- Después de este merge, **todo el flujo end-to-end debería funcionar limpio**: hold→pago→confirm→panel Beds24 con cargos y pagos visibles correctos.
- Reference oficial Beds24 v2: `docs/beds24-api-v2.yaml` en el repo (263KB completo).
- 0 daño financiero real: Karina sabe que el pago fantasma de $20 es del smoke setup, no real revenue.
