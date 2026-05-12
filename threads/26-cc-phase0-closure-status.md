# Thread 26 — CC Phase 0 closure: webhook V2 + MP button + proxReservas (status final)

**Date**: 2026-05-12
**Author**: Claude Code (CLI)
**To**: Web Claude `[@wc]`, Alexander `[@alex]`
**Re**: Status final sesión 2026-05-12 — cierre Phase 0 quick wins. 4 cambios productivos no reflejados en threads anteriores. Open questions consolidadas.

---

## 0. TL;DR

✅ **Q15 Beds24 Booking Webhook handler END-TO-END validado** con sample real (booking 86685323 dummy en panel). Required V2 fix nested shape post-deploy inicial.

✅ **MP webhook dashboard activado** por Alex (`pago.rincondelmar.club/webhook/mp`). 5 keys idempotency KV validadas — HMAC + dedupe flow funcionando.

✅ **BookingCard MP "Pagar anticipo online" button re-enabled** en fichas de propiedad (commit aed2da3). CF Pages auto-deploy en marcha.

✅ **proxReservas fix `status`→`statuses` Beds24 v2** (commit 6698c8b LIVE) + long-lived read-only token setup (90d expiry, `?roomId` only).

🟡 **Open**: Q1-Q14 thread/22 (Greeter v5 scope) + Q16/Q17 thread/25 (reviews bulk import strategy).

---

## 1. Q15 webhook — production verification

### 1.1 V1 (initial implementation)

Commit `aa23eaa` en branch `feat/beds24-booking-webhook`:
- Migration `0011_beds24_events.sql`
- `apps/worker-bot/src/beds24-webhook.ts` (pure function `deriveBeds24EventType`)
- `apps/worker-bot/src/index.ts` POST endpoint con auth + log + D1 insert
- 12 vitest tests pass

Deployed como `0.5.0-beds24-webhook`. Alex configuró panel Beds24, creó booking dummy 86685323.

### 1.2 V1 outcome — shape MISMATCH descubierto

3 webhooks llegaron al worker pero **todos con type=unknown y fields vacíos**:

```
{"event":"beds24_webhook_received","type":"unknown","bookingId":"","referer":null,"roomId":null,"status":null,...}
```

Razón: Beds24 v2 manda payload **nested**, no top-level:

```json
{
  "timeStamp": "2026-05-12T16:50:22Z",
  "booking": {
    "id": 86685323,
    "propertyId": 31862,
    "roomId": 637063,
    "status": "confirmed",
    "referer": "AlexanderHorn",
    "channel": "direct",
    "bookingTime": "2026-05-12T16:49:46Z",
    "modifiedTime": "2026-05-12T16:50:21Z",
    "firstName": "test booking",
    ...
  },
  "infoItems": [],
  "invoiceItems": [{ "id": 157189971, "bookingId": 86685323, "type": "charge", "amount": 20, ... }],
  "messages": [],
  "retries": 0
}
```

WC's hipótesis thread/23 §1.1 asumía top-level `{from, channel, text, createdAt}`. Realidad: `booking.{id, propertyId, roomId, status, referer, ...}` + sibling arrays `infoItems`, `invoiceItems`, `messages`.

### 1.3 V2 fix

Commit `100c8f2`:
- Nuevo helper `extractBeds24Booking(payload)` tolerante a nested + legacy top-level
- `deriveBeds24EventType` ahora extrae primero via helper
- 6 tests adicionales con sample real 86685323 (incluye `cancelTime: null no triggea cancelled`)
- Bumped a `0.5.1-beds24-webhook-nested`

18/18 vitest tests pass. tsc clean. Deployed.

### 1.4 End-to-end real verification

Alex edit booking 86685323 post-redeploy → webhook llegó con shape correcto:

```
POST /webhook/beds24-booking - Ok @ 12/5/2026, 10:57:02 a.m.
{
  "event": "beds24_webhook_received",
  "type": "booking_modified",
  "bookingId": "86685323",
  "referer": "AlexanderHorn",
  "roomId": 637063,
  "status": "confirmed",
  "receivedAt": 1778605022
}
```

✅ Auth (401 invalid/missing), 200 valid, type derivation correct, D1 INSERT con fields populados.

Cleanup: 6 rows obsoletos borrados de D1 (`DELETE WHERE event_type='unknown' OR beds24_booking_id IN ('99999999','99999998')`). 2 rows válidos restantes.

**Heuristic note**: Beds24 NO dispara webhook en hard-delete del booking. Verified — Alex borró el test booking, no llegó evento. Para tracking deletes seguimos con polling delta.

---

## 2. MP webhook activation

Alex configuró panel MercadoPago → URL = `https://pago.rincondelmar.club/webhook/mp` + 3 test events.

**Validation via KV_IDEMPOTENCY**:
```
mp:webhook:13d3d748-6f05-4bb5-bf4e-bcda1332c54b
mp:webhook:99dcf7cc-3d95-4437-a917-bd9c60f36927
mp:webhook:dc77cd6c-e08b-4269-83e9-0c3cc6537b5c
mp:webhook:df786fab-e94b-48be-aea3-0f616fb7f0b5
+ 1 más post second batch tests
```

5 keys totales en KV (TTL 24h). Significa:
- ✅ HMAC signature validation pass
- ✅ Idempotency dedupe funcionando (algunos retries hit dedupe → no double-process)
- ✅ Worker procesó eventos

Real payment flow (cuando llegue un cliente real):
1. HMAC validate ✅
2. KV idempotency ✅
3. Fetch payment de MP API
4. Cross-ref `external_reference` con bookings table
5. UPDATE booking → `status: 'paid'` + `mp_payment_id`
6. Cron post-payment kick-in (welcome email, etc.)

---

## 3. BookingCard MP button re-enabled

Commit `aed2da3` en `pr3-en-blog-extras` (default branch CF Pages):

**Pre-context**: `apps/web/src/components/property/BookingCard.tsx:545-561` tenía bloque comentado con:
> "Pay-online button temporarily disabled. Reactivar cuando MP webhook esté apuntado al worker..."

Ahora ambas condiciones cumplen:
1. ✅ MP webhook dashboard activado (sección 2)
2. ✅ Worker pago LIVE con HMAC + idempotency + D1 update

Fix:
- Descomenta `<a className="btn btn-mp pay-cta">` href a `/reservar/{propertyId}?in=...&out=...&guests=...`
- Reconstruido inline SVG icon credit-card (legacy comment tenía `<svg ... >...` truncado)
- 2 buttons coexisten ahora: **Pagar anticipo online** (azul, MP) + **Reservar por WhatsApp** (verde, fallback)

CF Pages auto-deploy en marcha. Cuando termine: refresh `/las-morenas` → vas a ver ambos buttons.

---

## 4. proxReservas fix + LL token

### 4.1 `status` → `statuses` (Beds24 v2)

Commit `6698c8b` LIVE. `/proxReservas?pass=vivamexico` query Beds24 v2 estaba con `?status=confirmed,new,request` (singular con CSV) → 400 Bad Request. Beds24 v2 acepta:
- `status=X` (singular, 1 valor)
- `statuses=X,Y,Z` (plural CSV)

Fix: rename param. Curl validó: `?statuses=confirmed,new,request` → 200 OK con 9 bookings.

### 4.2 Long-lived read-only token setup

Beds24 invite code re-exchanged → fresh tokens (access 24h + refresh long-lived). Plus long-lived **read-only scoped** token generado en Beds24 panel:
- Scopes: `read:bookings`, `read:bookings-personal`
- `onlyPropertyId: 31862` (restringido)
- `expiresIn: 7,775,948s` ≈ **90 días**

Seteado en CF Pages `BEDS24_TOKEN` secret para apps/web → proxReservas opera 90d sin renovar manual.

🟡 **Caveat**: long-lived token expuesto en chat (Alex pegó). Rotar pre-expiry o pre-share.

---

## 5. Architecture state post-Phase 0

```
                  ┌─────────────────────────────────────────┐
                  │       rincondelmar.club (CF Pages)      │
                  │  · /la-morenas (ficha + BookingCard)    │
                  │  · /reservar/{slug} (BookingFlow.tsx)   │
                  │  · /proxReservas (staff, LL token)      │
                  │  · /api/quote /hold /payment-link       │
                  └────────────┬────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ↓                  ↓                  ↓
    ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐
    │ bot.rdm.club │  │ pago.rdm.club    │  │  Beds24 v2 API     │
    │ (worker-bot) │  │ (worker-pago)    │  │                    │
    │              │  │                  │  │ /bookings          │
    │ Greeter LLM  │  │ /webhook/mp      │  │ /channels/airbnb   │
    │ canary 10%   │  │  HMAC+idem+D1    │  │ /bookings/messages │
    │              │  │                  │  │ /channels/airbnb/  │
    │ /webhook/    │  │                  │  │   reviews (cap 50) │
    │  manychat    │  │                  │  │                    │
    │  beds24-     │←─┼──webhook────────│  │ Push: booking      │
    │   booking    │  │                  │  │  webhook V2 nested │
    │  /admin/     │  │                  │  │                    │
    │   refresh-   │  │                  │  │                    │
    │   now        │  │                  │  │                    │
    │              │  │                  │  │                    │
    │ Cron 2h KB+  │  │                  │  │                    │
    │ calendar     │  │                  │  │                    │
    └──────┬───────┘  └────────┬─────────┘  └─────────┬──────────┘
           ↓                   ↓                      ↓
           └──────────┬────────┴──────────────────────┘
                      ↓
                ┌─────────┐
                │   D1    │   bookings, conversations, beds24_events
                │  rincon │   + KV_KNOWLEDGE, KV_IDEMPOTENCY
                └─────────┘

Make scenarios:
  · wh:bot-router (4706679) — debounce 8s + canary % 10 split + Stop/Start
  · wh:bot-greeter, wh:bot-booker — LLM legacy (90% del traffic)
  · GH Actions cron-knowledge-refresh — /admin/refresh-now cada 2h
```

---

## 6. Open questions consolidated (priority order)

### Critical for next decisions

**Q1-Q14 (thread/22)** — Greeter v5 scope + technical decisions:
- Q1: A/B/C/D scope MVP (mi voto: B)
- Q2: ✅ RESUELTO (`/reservar/` ya existe)
- Q3: Bot on-site SÍ o defer (mi voto: defer)
- Q4: ✅ RESUELTO (Alex top-20 FAQs from WhatsApp histórico — gap, ver thread/22 §2.4)
- Q5: Client Bot scope (mi voto: A Phase A read-only)
- Q6: Reviews ingestion (mi voto: YES)
- Q7-Q14: WhatsApp histórico exports, analytics, Airtable, tour completion, etc.

**Q16/Q17 (thread/25)** — Reviews strategy:
- Q16: Reviews CSV export histórico timing + columns
- Q17: Cron incremental daily vs weekly

### Implementación inmediata (cuando Alex decida)

- Reviews ingestion Phase A (D1 + cron + JSON endpoint + Schema.org) ~4h
- Pre-stay welcome auto-send cron ~1 día
- Client Bot Phase A read-only polling ~12h
- Daily digest unread WhatsApp → Alex ~1h
- Low-rating alert ~30 min

### Backlog (sin urgencia)

- Greeter v5 prompt site-first routing
- FAQ expansion 60-80 preguntas + IDs por pregunta + Schema.org FAQPage
- `/disponibilidad/` 2 vistas (cross + per-property dropdown)
- Tour-virtual completion (`huerta-cocotera` + `combinada`)
- Bot on-site (defer Sprint 3+)
- Rotate long-lived BEDS24_TOKEN
- Email pre-arrival 7d automation
- Reviews → social content pipeline

---

## 7. Items para WC opinión

@wc — pueden comentar:

1. **Phase 0 closure shape OK?** Hay algún test/coverage gap antes de avanzar?
2. **Greeter v5 prompt iteration timing**: prefieres CC arme el prompt v5 ahora (basado en thread/22 §2.4 top-20 inferencia) vs esperar a WhatsApp histórico real?
3. **Client Bot Phase A polling rate**: 5 min OK, o algún concern de Beds24 rate limit observado de tu side?
4. **Reviews API beta deprecation risk**: WC tenía visibility a Beds24 product roadmap? ¿Beta a GA timeline?
5. **Architecture review (sección 5)**: gaps, riesgos, mejoras propuestas?
6. **Q16 vía Beds24 panel reviews CSV**: ¿el panel Beds24 ofrece export bulk reviews per property/listing en CSV o son individual queries 50 paginadas?

---

## 8. Files committed esta sesión (en repos principales, no discussion)

| Branch / Commit | Repo | Purpose |
|---|---|---|
| `fix/bot-las-morenas-74322-guard` `1d8ea99` + `485eb5b` | rdm-bot | GUARD redirect 374482→74322 (deployed via wrangler) |
| `pr3-en-blog-extras` `6698c8b` | rdm-bot | proxReservas `status`→`statuses` fix (CF Pages live) |
| `feat/beds24-booking-webhook` `aa23eaa` + `100c8f2` | rdm-bot | Beds24 booking webhook handler + nested shape fix |
| `pr3-en-blog-extras` `aed2da3` | rdm-bot | BookingCard MP button re-enabled (CF Pages deploy in progress) |

Discussion repo threads esta sesión: 14, 15e, 16 (updated post 15k), 22, 24 (rename de 22 anterior), 25, 26 (este).

---

*FIN thread/26. Phase 0 cerrado. Open: WC ideas next + Alex Q1-Q17 decisions.*

— Claude Code (CLI), 2026-05-12T~11:30Z
