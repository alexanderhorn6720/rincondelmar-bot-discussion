# Pre-stay notifications MVP — brain deep spec

**Date**: 2026-05-18
**Author**: WC (brain deep)
**To**: CC-Bot (executor) + Alex (canary/approver)
**Re**: thread/118+119 sequence — Alex objective "todos los huéspedes que arriven en próximas 4 semanas reciben pre-arrival info" + ↓ workload Alex + handoff a Karina
**Mode**: brain deep → DoIt-ready spec
**Estimated effort**: ~35-50h CC across 4-7 PRs

---

## TL;DR

Pre-stay automation MVP: tres touchpoints (welcome, T-7, T-1) outbound via multi-canal (Beds24 messages para OTA, ManyChat para direct), piggyback de la infra Part E (`sendMessageRouted` + `MESSENGER_OUTBOUND_ENABLED` flag) validada en prod 2026-05-18 (audit row `delivery_status='sent'`, Beds24 msg ID 148091343). Universo inmediato: **19 bookings** en window próximas 4 semanas. Welcome auto-send pipeline ya detecta + queue (10 rows históricas en `pending_welcomes`) — solo necesita wire al sender. Catch-up cron one-shot para los 6 bookings ya en window T-7. Admin override en `/admin/bookings` drawer (skip, send-now per booking) para que Karina opere.

---

## §1 · Context

### 1.1 · Por qué

Alex (2026-05-18) define 3 objetivos corto plazo:

1. ↓ drásticamente workload personal en WhatsApp + Airbnb
2. Handoff operativo a Karina
3. Asegurar que próximos huéspedes (próximas 4 semanas) reciben toda la info que necesitan

Hoy ~99% de bookings (los que entran via AirBnB+OTA) **no reciben ninguna comunicación automatizada pre-stay**. La cobertura existente es solo `bookings` direct table (5 rows históricos) vía `preArrivalReminder` cron en `worker-pago`. AirBnB bookings (que constituyen el grueso) terminan en `beds24_bookings` (miles de rows post-backfill+webhook) y **ningún cron los procesa para outbound proactivo**.

### 1.2 · Estado prior-art relevante

| Componente | Status | Reuso |
|---|---|---|
| `MESSENGER_OUTBOUND_ENABLED` flag | ✅ Validated 2026-05-18 (Beds24 ID 148091343 entregado) | Mismo flag gates pre-stay |
| `messenger-send.ts` `sendMessageRouted()` | ✅ Live (PR #90 + #94 body shape fix) | Sender único multi-canal |
| `messenger_outbound` audit table | ✅ Live (migration 0032) | Re-use para audit pre-stay |
| `welcome-auto-send.ts` detección + queue | ✅ Live; 10 rows `pending_welcomes` rejected porque sender estaba deferred | Wire al sendMessageRouted |
| `ROOM_INFO` constant en `welcome-auto-send.ts` | ✅ Live (4 propiedades activas, Casa Chamán excluida) | Re-use shape |
| R2 `rdm-knowledge` + KV cached welcome-kb | ✅ Live (`welcome-kb.ts` refresh cada 2h) | Template source per property + lang |
| Greeter v6 prompt con pet policy `/estancia` | ✅ Live, canary 100% | Source consistency |
| Beds24 messages API outbound | ✅ Validated en canary | Primary channel |
| ManyChat sendContent ACCOUNT_UPDATE tag | ✅ Live (PR #90) | Direct booking fallback |

### 1.3 · Universo actual

Query D1 prod 2026-05-18 14:50 UTC:

| Window arrival | Bookings activos |
|---|---|
| Mañana (T-1) | 1 |
| Días 2-7 (T-7 window) | 5 |
| Días 8-14 | 4 |
| Días 15-28 | 8 |
| **Total 4 sem** | **18** |

Manejable. Single canary batch safe. Volumen mensual estimado 30-50 bookings (Alex 2026-05-18).

### 1.4 · Constraints no-negociables

| Constraint | Source |
|---|---|
| **Canales**: solo WhatsApp (ManyChat) + Beds24 messages. **NO email** | Alex 2026-05-18 |
| Casa Chamán (679176) **NO** en pre-stay templates hasta post-renovation Q3 2026 | CLAUDE.md anti-pattern |
| Pet policy `$300/estancia, máx 2` (NO /noche) en cualquier mención | thread/118 lock |
| Beds24 sync mode `Prices & Availability` only (NUNCA `Everything`) | CLAUDE.md anti-pattern |
| Flag `MESSENGER_OUTBOUND_ENABLED` default-OFF; Alex aprueba ON manual | Sprint E pattern |
| LLM NO en money path (sin precios concretos dinámicos en pre-stay) | CLAUDE.md anti-pattern |
| Karina puede operar override per booking sin Alex aprobación | Objetivo 2 handoff |

---

## §2 · Explicit scope

### 2.1 · YES (in scope v1)

| # | Item |
|---|---|
| Y1 | Wire `welcome-auto-send.ts` outbound del estado "deferred" a `sendMessageRouted()`. Drena los 10 rows actuales de `pending_welcomes` + ongoing detection |
| Y2 | New cron `preStayT7` daily 09:00 MX (15:00 UTC): detecta bookings con arrival = today+7, status='booked', envía pre-arrival kit |
| Y3 | New cron `preStayT1` daily 17:00 MX (23:00 UTC): detecta arrival = today+1, envía check-in instructions |
| Y4 | One-shot catch-up endpoint `POST /admin/pre-stay/catch-up`: para todos los bookings en window [now, now+7] al deploy, envía variante condensed pre-arrival; rate-limited 10 sends/min |
| Y5 | Templates per touchpoint × per property × per lang (3 × 4 × 2 = 24 templates), hardcoded en TS module por ahora (no KV/R2 indirection v1) |
| Y6 | Idempotency via nuevas columns en `beds24_bookings`: `welcome_sent_at`, `pre_arrival_t7_sent_at`, `check_in_t1_sent_at`, `pre_stay_skip` (migration 0035) |
| Y7 | Admin endpoints worker: `POST /admin/pre-stay/scan`, `POST /admin/pre-stay/:beds24_booking_id/:touchpoint/send`, `POST /admin/pre-stay/:beds24_booking_id/skip` |
| Y8 | Admin UI: drawer en `/admin/bookings` row → buttons "Send Welcome / Send T-7 / Send T-1 / Skip pre-stay" + visual indicators which sent |
| Y9 | Audit log: cada send escribe row en `messenger_outbound` (re-use Part E table) con `conversation_source` + `routed_to` correctos |
| Y10 | Routing reuse: `resolveRoute()` de messenger-send.ts. OTA bookings → beds24_booking_id (6-12d) → Beds24 API. Direct bookings → phone E.164 (13-15d) → ManyChat |
| Y11 | Language detection: heuristic from `booking_source` URL pattern (airbnb.com.mx / .com.br → es, airbnb.com / booking.com → en lang inference) + explicit `guests.lang` override si existe |
| Y12 | Feature flag gate: si `MESSENGER_OUTBOUND_ENABLED !== 'true'` → audit row `delivery_status='feature_off'`, no external send, marca `pre_stay_skip=1`? **No** — solo audit, no skip (permite retry post flip) |
| Y13 | Telegram alert si cron fails > 3 consecutive runs (re-use bot-alerts infra) |
| Y14 | Tests: unit (scan eligibility, route resolution, template render, idempotency, flag gate) + integration (send writes audit + marks column + re-run idempotent) |
| Y15 | GitHub Actions cron-pre-stay-{welcome,t7,t1}.yml workflows (offset times to not stampede) |

### 2.2 · NO (out of scope v1)

| # | Item | Razón / dónde va |
|---|---|---|
| N1 | T-3 chef menu request | Property-specific (solo RdM/Combinada con chef incluido). Postponed v2 |
| N2 | T-0 day-of welcome message | Postponed v2 (marginal value vs T-1) |
| N3 | In-stay touchpoints (día 1-2 check-in, mid-stay) | Client Bot Phase A scope separate |
| N4 | Reply handling (cuando guest contesta pre-arrival) | Out-of-scope; humans handle via `/admin/inbox` |
| N5 | Email channel | Alex 2026-05-18: solo WA + Beds24 |
| N6 | Auto-upsell embedded (tours, masajes, paseo laguna) | P3-C ideas; spec separado post pre-stay live |
| N7 | LLM personalization (variar texto por guest) | v2 después de validar templates planos. v1 = deterministic render |
| N8 | Per-property timing differences (eventos T-30) | Postponed; v1 = uniform T-7/T-1 |
| N9 | Configurable touchpoints from admin UI | Hardcoded en TS v1; UI config v2 |
| N10 | Casa Chamán (679176) templates | Excluded hasta Q3 2026 renovation |
| N11 | Operator playbook v6 patterns integration | Greeter v6 ya consume via prompt; pre-stay no necesita |
| N12 | Vectorize index `rdm-conversations-v2` runtime query | Separate scope CC-Data (§Appendix A) |
| N13 | Booking.com / Expedia / VRBO specific templates | All OTA share Beds24 route + generic templates v1 |
| N14 | A/B testing templates | v2 después de baseline |
| N15 | Per-guest delivery time customization | Cron-based fixed; v2 |

---

## §3 · Closed decisions

Voted, no re-litigate:

| # | Decisión | Source |
|---|---|---|
| C1 | Multi-channel WA + Beds24 messages, NO email | Alex 2026-05-18 chat |
| C2 | Re-use `MESSENGER_OUTBOUND_ENABLED` flag from Part E (no new flag) | Reduce surface |
| C3 | Idempotency via columns en `beds24_bookings` (no separate `pre_stay_sends` table) | Simpler; mirrors existing `pre_arrival_sent_at` pattern en `bookings` table |
| C4 | Audit via re-use `messenger_outbound` table | Single audit surface |
| C5 | Templates hardcoded en TS module v1 (no R2/KV indirection) | Velocity; KV/R2 indirection adds caching + sync complexity premature |
| C6 | 3 touchpoints v1 (welcome, T-7, T-1). T-3 + T-0 v2 | Scope minimization |
| C7 | Catch-up via manual admin endpoint (Karina/Alex trigger), not auto on deploy | Safety: avoid mass-send accidente |
| C8 | Rate limit catch-up 10 sends/min | Beds24 API friendly + spreads guest receipt |
| C9 | Casa Chamán excluded explicitly via room_id check (not template absence) | Defensive |
| C10 | Pet policy mention only via "consulta pre-arrival website" link, not embedded fee | Avoid mention drift |
| C11 | NO LLM personalization v1 | Determinism + cost + Alex no quiere overhead |
| C12 | Karina puede skip per booking sin escalate Alex | Objetivo handoff |
| C13 | Feature flag OFF → audit row only, NO mark sent (allow retry post flip) | Recovery path |
| C14 | Single migration 0035 for all 4 columns + minor indexes | Avoid multi-migration race |
| C15 | Per-property template lookup via slug + lang, fail loud if missing (not silent generic) | Quality gate |
| C16 | Language inference: explicit guest.lang > booking_source domain > default 'es' | Predictable |

---

## §4 · Implementation

### 4.1 · Migration 0035

```sql
-- Migration 0035: pre_stay_columns
--
-- Add idempotency + skip flag columns to beds24_bookings for pre-stay
-- automation. Mirror pattern from bookings.pre_arrival_sent_at but for the
-- beds24-derived table (which carries OTA bookings, the actual volume).

ALTER TABLE beds24_bookings ADD COLUMN welcome_sent_at INTEGER;
ALTER TABLE beds24_bookings ADD COLUMN pre_arrival_t7_sent_at INTEGER;
ALTER TABLE beds24_bookings ADD COLUMN check_in_t1_sent_at INTEGER;
ALTER TABLE beds24_bookings ADD COLUMN pre_stay_skip INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_beds24_bookings_arrival_status
  ON beds24_bookings(arrival, status);

-- No data backfill; existing rows treat all *_sent_at as null = "not sent",
-- which is correct. Catch-up endpoint will trigger sends explicitly.
```

### 4.2 · New module `apps/worker-bot/src/pre-stay.ts`

Functions (export signatures):

```typescript
export interface PreStayEnv {
  DB: D1Database;
  KV_KNOWLEDGE: KVNamespace;
  MESSENGER_OUTBOUND_ENABLED?: string;
  BEDS24_TOKEN: string;
  MANYCHAT_API_TOKEN?: string;
  // ... and Anthropic key NOT needed (no LLM)
}

export type Touchpoint = 'welcome' | 't7' | 't1';

export interface ScanResult {
  touchpoint: Touchpoint;
  eligible: number;
  sent: number;
  feature_off: number;
  failed: number;
  skipped: number;
}

// One scan per touchpoint, idempotent
export async function scanForWelcome(env: PreStayEnv): Promise<ScanResult>;
export async function scanForT7(env: PreStayEnv): Promise<ScanResult>;
export async function scanForT1(env: PreStayEnv): Promise<ScanResult>;

// Manual fire single booking single touchpoint (from drawer)
export async function sendPreStay(
  env: PreStayEnv,
  beds24BookingId: number,
  touchpoint: Touchpoint,
  byUser: string,
): Promise<SendMessageResult>;

// Catch-up: scan window [now, now+7], send consolidated pre-arrival to all
// not-yet-sent. Rate-limited internally to 10/min.
export async function runCatchUp(
  env: PreStayEnv,
  byUser: string,
  dryRun: boolean,
): Promise<{ candidates: number; sent: number; rate_limited_waited_ms: number }>;

// Template rendering — pure function (no I/O)
export function renderTemplate(input: {
  property_slug: 'rincon-del-mar' | 'las-morenas' | 'combinada' | 'huerta-cocotera';
  touchpoint: Touchpoint;
  lang: 'es' | 'en';
  guest_first_name: string | null;
  arrival: string;          // YYYY-MM-DD
  departure: string;        // YYYY-MM-DD
  num_adults: number;
  num_children: number;
  channel: 'airbnb' | 'booking' | 'direct' | string;
}): string;
```

### 4.3 · Template structure

Inline TS module pattern (re-using copy de `wc-seed-drafts/{slug}.{lang}.json` field `kit_bienvenida`):

```typescript
// apps/worker-bot/src/pre-stay-templates.ts
//
// 3 touchpoints × 4 properties × 2 langs = 24 templates.
// Stays in TS so renderTemplate is pure + testable.
// When Karina edits content via /admin/airbnb-content, ship via PR (cycle <24h
// is fine for content edits; not high-cadence enough to justify R2 indirection).

const T_WELCOME_RDM_ES = `¡Hola {guestFirstName}! 👋

Recibimos tu reserva en Villa Rincón del Mar 🌅 para {arrivalFmt} — {departureFmt}.

Próximos pasos:
• Te escribimos 1 semana antes con el kit de bienvenida completo.
• 1 día antes con instrucciones de check-in.
• Cualquier duda, contesta este mensaje.

— Alexander 🌅
· rincondelmar
· club`;

const T_T7_RDM_ES = `¡Hola {guestFirstName}! 🌅

Tu llegada a Villa Rincón del Mar es el {arrivalFmt}. Aquí tu kit pre-llegada:

📍 Ubicación: https://maps.app.goo.gl/GEHJDhXvcTGcqxRv9
🚗 Recomendado: libramiento Acapulco-Zihuatanejo desde caseta 'La Venta'

🍳 Chef Celene + cocinera + mozo INCLUIDOS
• 2 semanas antes te conectamos con Celene para menú
• 5 días antes envías el menú → lista de compras lista para tu llegada
• Promedio víveres: $250-280/persona/noche

🐾 Mascotas (si aplica): $300 MXN por mascota por estancia, máx 2

Toda la info detallada en: rincondelmar.club/welcome

¿Algo que quieras preparar antes? Avísame por aquí.

— Alexander 🌅`;

const T_T1_RDM_ES = `¡Hola {guestFirstName}! 🌅

Mañana es tu día. Detalles check-in:

📍 Llegada desde 3 PM
🗺️ https://maps.app.goo.gl/GEHJDhXvcTGcqxRv9
📶 WiFi al llegar: te lo damos en persona
🆘 Si hay cualquier emergencia llegando, este mismo chat

Pronóstico mañana: revisa Google Weather "Pie de la Cuesta Acapulco" (estamos en costa Pacífico, brisa garantizada 🌊).

¡Te esperamos!

— Alexander 🌅`;

// ... 21 more variants
// Per-property differences:
//   - RdM: chef included (above)
//   - Morenas: chef OPCIONAL $1k/d ≤16 o $1.5k/d 17-30 (mention)
//   - Combinada: ambas villas + chef Celene incluida (mention)
//   - Huerta: NO chef, mention animals (chivos, La Prieta), tip mascotas si llevan
//
// Per-language: ES + EN literal translation, kept short

const TEMPLATES: Record<string, string> = {
  'welcome:rincon-del-mar:es': T_WELCOME_RDM_ES,
  'welcome:rincon-del-mar:en': T_WELCOME_RDM_EN,
  // ... 22 more keys
};

export function renderTemplate(input: TemplateInput): string {
  const key = `${input.touchpoint}:${input.property_slug}:${input.lang}`;
  const tpl = TEMPLATES[key];
  if (!tpl) {
    throw new Error(`No template for ${key}`);
  }
  return tpl
    .replaceAll('{guestFirstName}', input.guest_first_name ?? 'hola')
    .replaceAll('{arrivalFmt}', formatDate(input.arrival, input.lang))
    .replaceAll('{departureFmt}', formatDate(input.departure, input.lang));
}
```

### 4.4 · Cron wiring `apps/worker-bot/src/cron.ts`

```typescript
// Existing crons preserved. Add 3 new dispatchers.

export async function runScheduledPreStayWelcome(env: PreStayEnv): Promise<void> {
  await recordCronHeartbeat(env, 'pre-stay-welcome');
  const result = await scanForWelcome(env);
  console.log(JSON.stringify({ event: 'pre_stay_welcome_complete', ...result }));
}

export async function runScheduledPreStayT7(env: PreStayEnv): Promise<void> {
  await recordCronHeartbeat(env, 'pre-stay-t7');
  const result = await scanForT7(env);
  console.log(JSON.stringify({ event: 'pre_stay_t7_complete', ...result }));
}

export async function runScheduledPreStayT1(env: PreStayEnv): Promise<void> {
  await recordCronHeartbeat(env, 'pre-stay-t1');
  const result = await scanForT1(env);
  console.log(JSON.stringify({ event: 'pre_stay_t1_complete', ...result }));
}
```

`wrangler.toml` worker-bot triggers — add to existing `[triggers]`:

```toml
crons = [
  # ... existing ...
  "*/30 * * * *",    # pre-stay welcome (same cadence as detection in welcome-auto-send)
  "0 15 * * *",      # pre-stay T-7 (09:00 MX)
  "0 23 * * *",      # pre-stay T-1 (17:00 MX, evening before)
]
```

GitHub Actions cron workflows: `.github/workflows/cron-pre-stay-{welcome,t7,t1}.yml` mirror existing pattern from `cron-extra-guests-scan.yml`.

### 4.5 · Admin endpoints worker

```typescript
// apps/worker-bot/src/index.ts add routes:

app.post('/admin/pre-stay/scan', x_admin_secret, async (c) => {
  const touchpoint = c.req.query('touchpoint') as Touchpoint;
  if (!['welcome', 't7', 't1'].includes(touchpoint)) {
    return c.json({ ok: false, error: 'bad_touchpoint' }, 400);
  }
  const result =
    touchpoint === 'welcome' ? await scanForWelcome(c.env) :
    touchpoint === 't7' ? await scanForT7(c.env) :
    await scanForT1(c.env);
  return c.json({ ok: true, ...result });
});

app.post('/admin/pre-stay/:bookingId/:touchpoint/send', x_admin_secret, async (c) => {
  const bookingId = Number(c.req.param('bookingId'));
  const touchpoint = c.req.param('touchpoint') as Touchpoint;
  const body = await c.req.json();
  const result = await sendPreStay(c.env, bookingId, touchpoint, body.sent_by_user);
  return c.json({ ok: true, ...result });
});

app.post('/admin/pre-stay/:bookingId/skip', x_admin_secret, async (c) => {
  const bookingId = Number(c.req.param('bookingId'));
  await c.env.DB.prepare(
    'UPDATE beds24_bookings SET pre_stay_skip=1 WHERE beds24_booking_id=?'
  ).bind(bookingId).run();
  return c.json({ ok: true });
});

app.post('/admin/pre-stay/catch-up', x_admin_secret, async (c) => {
  const body = await c.req.json();
  const result = await runCatchUp(c.env, body.sent_by_user, body.dry_run === true);
  return c.json({ ok: true, ...result });
});
```

### 4.6 · Web proxy + Admin UI

```
apps/web/src/pages/api/admin/pre-stay/[bookingId]/[action].ts  ← proxy strict
apps/web/src/pages/api/admin/pre-stay/catch-up.ts              ← proxy strict
apps/web/src/pages/admin/pre-stay.astro                        ← list + catch-up button
```

In `/admin/bookings` row drawer (existing component): add per-row buttons:

```
[ Welcome ✓ 2d ago ] [ Send T-7 ] [ Send T-1 ] [ Skip pre-stay ]
```

Buttons enabled/disabled based on `*_sent_at` not null + `pre_stay_skip`. Status pill shows last send timestamp.

### 4.7 · Scan SQL templates

```sql
-- Welcome: detected via existing welcome-auto-send pipeline + pending_welcomes
-- table. New step is wire post-Part-E sender. Eligible = pending_welcomes rows
-- with status='pending' AND beds24_bookings.welcome_sent_at IS NULL AND
-- pre_stay_skip=0 AND status='booked'.

-- T-7:
SELECT bb.beds24_booking_id, bb.room_id, bb.arrival, bb.departure,
       bb.num_adults, bb.num_children, bb.channel,
       g.name AS guest_name, g.phone_e164, g.email_lower, g.lang
FROM beds24_bookings bb
JOIN guests g ON g.id = bb.guest_id
WHERE bb.status = 'booked'
  AND bb.arrival = date('now', '+7 days')
  AND bb.pre_arrival_t7_sent_at IS NULL
  AND bb.pre_stay_skip = 0
  AND bb.room_id != 679176;  -- Casa Chamán excluded

-- T-1: same shape, arrival = date('now', '+1 day'), col = check_in_t1_sent_at
```

### 4.8 · Routing logic

Re-use `resolveRoute()` from `messenger-send.ts`. For each eligible row:

| Booking source | conversation_id supplied | Route output |
|---|---|---|
| AirBnB / Booking.com / OTA | `bb.beds24_booking_id` (8 digits typical) | `beds24_api` |
| Direct con phone E.164 | `guests.phone_e164` (13-15 digits) | `manychat` |
| Direct sin phone | — | SKIP, log warning, mark pre_stay_skip=1, surface in admin |

### 4.9 · Idempotency contract

```sql
-- UPDATE column inside same transaction as send, before write.
UPDATE beds24_bookings
SET pre_arrival_t7_sent_at = strftime('%s','now')
WHERE beds24_booking_id = ? AND pre_arrival_t7_sent_at IS NULL;
-- meta.changes = 0 → already sent (concurrent runner), skip rest

-- If changes = 1, proceed with sendMessageRouted. If sendMessageRouted fails:
-- → reset column to NULL so next run retries
-- → audit row in messenger_outbound captures the failure regardless
```

Recovery: feature_off NEVER marks `*_sent_at`. Failed real sends DO reset for retry.

### 4.10 · File changes summary

| Action | Path |
|---|---|
| Create | `apps/worker-bot/src/pre-stay.ts` |
| Create | `apps/worker-bot/src/pre-stay-templates.ts` |
| Create | `apps/worker-bot/tests/pre-stay.test.ts` |
| Create | `apps/worker-bot/tests/pre-stay-templates.test.ts` |
| Create | `migrations/0035_pre_stay_columns.sql` |
| Create | `apps/web/src/pages/api/admin/pre-stay/[bookingId]/[action].ts` |
| Create | `apps/web/src/pages/api/admin/pre-stay/catch-up.ts` |
| Create | `apps/web/src/pages/admin/pre-stay.astro` |
| Create | `.github/workflows/cron-pre-stay-welcome.yml` |
| Create | `.github/workflows/cron-pre-stay-t7.yml` |
| Create | `.github/workflows/cron-pre-stay-t1.yml` |
| Modify | `apps/worker-bot/src/cron.ts` (add 3 dispatchers) |
| Modify | `apps/worker-bot/src/welcome-auto-send.ts` (wire to sendMessageRouted) |
| Modify | `apps/worker-bot/src/index.ts` (add 4 admin routes) |
| Modify | `apps/worker-bot/wrangler.toml` (3 cron triggers) |
| Modify | `apps/web/src/pages/admin/bookings.astro` or related (drawer buttons) |

### 4.11 · PR sequencing recommendation

Suggest CC-Bot ship as **4 PRs** (atomic, reviewable):

| PR | Scope | Effort |
|---|---|---|
| **A1** | Migration 0035 + `pre-stay.ts` skeleton + `renderTemplate` + 24 templates + unit tests templates only | 8-12h |
| **A2** | `scanForWelcome` + wire `welcome-auto-send.ts` to `sendMessageRouted` + integration tests + drain backlog of 10 pending_welcomes rows | 8-12h |
| **A3** | `scanForT7` + `scanForT1` + cron dispatchers + wrangler.toml + GitHub Actions workflows + tests | 8-12h |
| **A4** | Admin endpoints (4) + web proxy + drawer UI + `/admin/pre-stay` page + catch-up button + tests | 10-14h |

Total ~35-50h. PRs land in order; each is shippable + canary-able independently.

---

## §5 · Tests

### 5.1 · Unit tests (vitest)

| Suite | Coverage |
|---|---|
| `pre-stay-templates.test.ts` | All 24 templates render; missing key throws loudly; placeholders all substituted; no `{guestFirstName}` leak; pet policy never says `/noche`; Casa Chamán never appears |
| `pre-stay.test.ts: scanForWelcome` | Idempotent (mark+send race-safe); excludes pre_stay_skip=1; excludes Casa Chamán 679176; respects status='booked' only |
| `pre-stay.test.ts: scanForT7` | Date arithmetic correct in UTC (cron runs UTC); arrival=today+7 inclusive; null sent_at filter works |
| `pre-stay.test.ts: scanForT1` | Same shape T-1 |
| `pre-stay.test.ts: sendPreStay` | Routes correctly via resolveRoute; happy path writes audit + marks column; feature_off path writes audit only (column null); failed path resets column null |
| `pre-stay.test.ts: runCatchUp` | Rate limit 10/min enforced; dry-run no sends; respects skip flag; window inclusive |
| `pre-stay.test.ts: language inference` | airbnb.com.mx → es; airbnb.com → en; booking.com → en; explicit guest.lang overrides; default es |

Target: **30+ tests passing**, mirror density of messenger-send (11) + extra-guests (16).

### 5.2 · Integration smoke (Alex post-deploy)

| Step | Command | Expected |
|---|---|---|
| 1 | `wrangler d1 execute rincon --remote --command "SELECT name FROM sqlite_master WHERE name LIKE 'beds24%';"` | List shows beds24_bookings with new columns |
| 2 | `wrangler d1 execute rincon --remote --command "PRAGMA table_info(beds24_bookings);"` | 4 new columns present |
| 3 | `curl POST /admin/pre-stay/scan?touchpoint=t7 -H 'x-admin-secret:...'` | JSON `{ok:true, eligible:N, sent:0, feature_off:N}` while flag off |
| 4 | Flip flag ON, repeat step 3 | `sent:N` |
| 5 | Query `messenger_outbound` order by sent_at desc limit 10 | Last N rows pre-stay context |
| 6 | Catch-up dry-run | Reports candidates count, sends 0 |
| 7 | Catch-up real run | Sends N, audit rows match |

### 5.3 · Canary playbook

| Stage | Action | Stop criterion |
|---|---|---|
| 0 | Deploy worker, flag OFF, smoke endpoints | All return 200 with feature_off in audit |
| 1 | Flag ON, send via drawer to Alex's own booking (sandbox 86496769) for one touchpoint | Beds24 message lands in your AirBnB app |
| 2 | Send 3 more to Alex sandbox bookings (different touchpoint each) | All 3 land + audit shows sent |
| 3 | Trigger `/admin/pre-stay/catch-up?dry_run=true` | Returns candidates count = expected (~6 from 19 active) |
| 4 | Trigger catch-up real with Karina supervising | All 6 sends OK, audit clean |
| 5 | Let cron T-7 run next morning autonomous | 0-3 sends typical; verify audit |
| 6 | Let cron T-1 run that evening | Same shape |
| 7 | 24h observation | No guest complaints, no failed sends |
| 8 | Steady state | Flag stays ON |

### 5.4 · Rollback

| Trigger | Action |
|---|---|
| Wrong template content shipped | `wrangler secret put MESSENGER_OUTBOUND_ENABLED` → enter `false`. All sends stop. Fix template, ship, flip back ON |
| Idempotency bug duplicating sends | Same: flag OFF + investigate. `messenger_outbound` audit + `*_sent_at` columns let us reconstruct what was sent |
| Beds24 API rate limit hit | Catch-up has rate-limit; cron is daily-only. Unlikely. If happens: pause via flag + adjust rate limit |
| Karina sends manually to wrong booking | Per-row send: low blast radius. Audit row helps trace |

---

## §6 · Definition of done

CC-Bot ships A1-A4 PRs. After PR A4 merge + Alex deploy:

- [ ] Migration 0035 applied to prod D1 (verify columns exist)
- [ ] Worker deployed with 3 new crons in wrangler.toml
- [ ] GitHub Actions cron workflows present + scheduled
- [ ] All unit tests pass (30+ new tests)
- [ ] All integration smoke steps from §5.2 pass
- [ ] Canary stage 0-2 complete (Alex sandbox sends verified)
- [ ] Catch-up dry-run shows expected candidates count
- [ ] Catch-up real run successful for 6 bookings in T-7 window
- [ ] T-7 cron runs autonomous 1+ time without alert spam
- [ ] T-1 cron runs autonomous 1+ time
- [ ] Welcome cron drains backlog of 10 `pending_welcomes` rows (or marks them rejected with reason)
- [ ] `/admin/bookings` drawer shows per-row pre-stay status + buttons
- [ ] `/admin/pre-stay` page shows last 50 sends + catch-up button
- [ ] Telegram alert configured if cron stale > threshold
- [ ] Karina trained on drawer buttons (skip / send-now per booking)
- [ ] **Objetivo cumplido**: 100% of bookings arriving in [T-1, T-28] have received at least one pre-stay touchpoint within 4 weeks of deploy

---

## §7 · Risks + mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Send to wrong language (guest speaks en, gets es) | Med | Low | Default to es (most reliable for MX market); explicit guest.lang override; per-row admin edit lang if needed in v2 |
| R2 | Send to cancelled booking after status change race | Low | Med | Cron filter `status='booked'`; `lifecycle != 'cancelled'`; window narrow |
| R3 | Duplicate send due to cron + manual fire race | Low | Med | `UPDATE ... WHERE *_sent_at IS NULL` atomic; idempotent guard |
| R4 | Wrong template per property (RdM template sent to Huerta) | Low | High | Slug derived from `ROOM_INFO[room_id]` deterministic; renderTemplate throws on missing key |
| R5 | Mass send on catch-up (overwhelm guests) | Med | Med | Rate limit 10/min; manual trigger required; Karina supervises stage 4 |
| R6 | Beds24 API rate limit hit during cron | Low | Low | Cron daily, max ~20 sends/day; well under limits |
| R7 | ManyChat 24h window block | Med | Med | Use `ACCOUNT_UPDATE` tag (allowed outside 24h); existing infra |
| R8 | Karina overrides → some guest gets duplicate manually + cron | Low | Low | Idempotent UPDATE prevents; drawer shows sent status before button click |
| R9 | Casa Chamán surfaced accidentally | Low | High | Explicit `room_id != 679176` SQL filter + template lookup throws if 679176 |
| R10 | Greeter v6 + pre-stay both write to same conversation, confusing guest | Med | Med | Pre-stay is outbound only; Greeter only reacts to inbound. If guest replies to pre-stay → handled by `/admin/inbox`. Document for Karina |
| R11 | Catch-up sends to booking that already received manual message | Med | Low | Audit `messenger_outbound` last 7d per booking → skip if any prior outbound + add admin flag |
| R12 | Test booking sandbox 86496769 receives real pre-stay accidentally during cron | Low | Low | Mark `pre_stay_skip=1` on Alex test bookings as setup step |
| R13 | Template typo / dead link goes out at scale | Med | High | All templates reviewed Alex + Karina pre-launch; A/B observable; rollback via flag |
| R14 | Volume sneaks higher than 30-50/mo (temporada alta) | Med | Low | Volume manageable up to 500/mo at current cron rates; resize if approaches |
| R15 | Beds24 messages API body shape regression (recall PR #94) | Low | Med | Re-use `sendMessageRouted`; same code path validated 2026-05-18; tests cover |

---

## Appendix A · Vectorize tail (paralelo, NO en este spec)

CC-Data scope. Pre-stay no depende. Status:

| Item | Status |
|---|---|
| 17,023 conversation embeddings | Generated, parquet awaiting upsert |
| Index `rdm-conversations-v2` | NOT created |
| CF API token scoped (Workers AI Edit + Vectorize Edit) | Alex creates 5 min |
| `scripts/data-mining/stage_vectorize.py --execute` | 2-3h wall time, ~$0.19 paid tier |
| Greeter v6 consume index | NOT wired (future PR A6.x) |

Handoff doc: `cc-instructions-data/2026-05-16-vectorize-handoff.md`. Pre-req only: Alex scoped token. Run anytime parallel to pre-stay sprint. Closes Data Mining v2 entirely.

---

## Appendix B · Catch-up plan for objetivo "próximas 4 semanas"

19 bookings activos en window. Cronograma:

| Día post-deploy | Acción | Bookings cubiertos |
|---|---|---|
| Day 1 (deploy) | Migration + worker deploy + smoke | 0 |
| Day 1 evening | Canary stage 1-2 (Alex sandbox) | 0 real guests |
| Day 2 morning | Catch-up dry-run via admin | Reveals 6 candidates |
| Day 2 morning | Catch-up real run con Karina supervising | 6 bookings receive pre-arrival kit |
| Day 2 evening | T-1 cron auto-runs | 1 booking T-1 |
| Day 3+ | Crons T-7 + T-1 daily autonomous | ~1 per day rolling forward |
| Day 28 | All 18 covered via natural cron rotation | 100% objetivo met |

Welcome cron + drain de 10 pending_welcomes opcional pre-existing rows runs in parallel; doesn't affect catch-up.

---

## Appendix C · Karina training checklist

Post-deploy, walkthrough con Karina (~30 min Alex):

| # | Tema |
|---|---|
| 1 | `/admin/bookings` drawer: pre-stay status indicators (Welcome ✓ / T-7 pending / etc) |
| 2 | Cuándo usar "Send now" button (guest urgente, fuera de cadencia normal) |
| 3 | Cuándo usar "Skip pre-stay" (eventos/bodas que Alex maneja personal, guest VIP, etc) |
| 4 | `/admin/pre-stay` page: last 50 sends, catch-up button (NUNCA presionar sin Alex) |
| 5 | Si guest contesta pre-arrival → handled via `/admin/inbox` (existing flow) |
| 6 | Si template tiene error → reportar Alex, NO editar inline |
| 7 | Pet policy reminder: `$300/estancia, máx 2` (no /noche) |

---

**Spec listo para CC-Bot. Atomic PRs A1-A4 sequencing recommended. Estimated 35-50h CC autonomous + Alex canary windows.**

— WC, 2026-05-18
