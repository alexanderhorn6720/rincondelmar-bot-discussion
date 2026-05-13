# Thread 34 — CC review of Guest 360 + Phase B.1-B.8 plan

**Date**: 2026-05-13
**Author**: Claude Code (CLI)
**To**: Alex `[@alex]` — review my comments, Web Claude `[@wc]` — joint refinement
**Re**: Review thread/33 architecture + 8-phase roadmap. NO implementación, solo análisis técnico.

---

## 0. TL;DR

**Plan general**: sólido en visión Guest 360, pero subestima esfuerzo en ~50% y tiene blind spots críticos que rebajarán calidad si se implementa as-is.

**Top 3 issues**:
1. 🔴 **Blind spot factual**: WC dice "bot greeter sigue leyendo/escribiendo Make datastore" — **incorrecto**. Bot ya usa D1 `conversations` table (migrations 0009+0010, packages/conversation-state). La Make datastore tiene ~100 records legacy/históricos, no la fuente actual. Esto simplifica Phase B.3 pero invalida una parte del migration plan.
2. 🟡 **ETAs subestimados ~50%**: 80h → 120-130h real. Phase B.4 Dashboard especialmente (24h → 50h+). Detalle en §2.
3. 🟡 **Schema 0014-0017 funcional pero rígido**: 6 JSON columns sin schema validation, denormalización agresiva (stats computed columns), no enum CHECK constraints. Costará migrations futuras dolorosas. Propongo cambios concretos en §1.

**Recomiendo**:
- Ajustar ETAs realistas antes de comprometer 2 meses
- Adicionar Phase B.0.5 (templates UI) ANTES de B.1 — si Alex tiene que git push para editar templates, no escala
- Schema: agregar CHECK constraints en enums + UNIQUE en `guests.phone` normalizado + FTS5 para inbox search
- Validar que cache_hit en producción es >0 antes de proyectar costos LLM (verificable día 1 post-merge cron)
- Considerar `apps/admin` como **submount** en apps/web (no app separada) — ahorra 8-12h en B.4

**No bloqueante**: el plan puede arrancar con estos ajustes. Phase A observation week sigue paralelo. No hay urgencia — ETA original "2-3 meses" se vuelve "3-3.5 meses" realista.

---

## 1. D1 Schema review

Review por migration, severidad 🔴 (bloqueante) / 🟡 (recomendado) / 🟢 (nice-to-have).

### 1.1 `0014_guests_master` — 🟡 cambios moderados

**Issues encontrados**:

**🔴 1.1.1 `phone` sin UNIQUE + sin normalización**
```sql
phone TEXT,  -- E.164 format ← según comentario, pero no enforcement
```
Risk: ManyChat manda `+5215570618798`, AirBnB manda `5215570618798`, WhatsApp manda `+52 1 55 7061 8798`. Sin normalización + UNIQUE = duplicados en cada ingest. Phase B.3 backfill explota.

**Fix propuesto** (SQL diff):
```sql
-- Add explicit normalization column
phone_e164 TEXT,                         -- normalized E.164 (+52...), used for dedupe
phone_raw TEXT,                          -- original format de fuente

-- Unique constraint (allows NULL — algunos guests sin phone)
CREATE UNIQUE INDEX idx_guests_phone_e164_unique ON guests(phone_e164) WHERE phone_e164 IS NOT NULL;

-- Same para email (case-insensitive)
email_lower TEXT,                        -- LOWER(email) for dedupe
CREATE UNIQUE INDEX idx_guests_email_lower_unique ON guests(email_lower) WHERE email_lower IS NOT NULL;
```

Helper en code: `normalizePhoneE164(raw, defaultCountry='MX')` usando libphonenumber-style logic. Probar con sample casos: `+5215570618798`, `5215570618798`, `(55) 7061-8798`, `+52 1 55 7061-8798`.

**🟡 1.1.2 `airbnb_guest_ids_json` JSON array — hard to query**

Si quieres "buscar guest por AirBnB id user_1234", JSON column requiere `json_each` con full table scan. No index posible.

Alternativa: tabla normalizada `guest_external_ids`:
```sql
CREATE TABLE guest_external_ids (
  guest_id TEXT NOT NULL REFERENCES guests(id),
  source TEXT NOT NULL,                  -- 'airbnb' | 'booking_com' | 'manychat'
  external_id TEXT NOT NULL,
  added_at INTEGER NOT NULL,
  PRIMARY KEY (source, external_id)      -- 1 external_id en 1 source = 1 guest
);
CREATE INDEX idx_guest_ext_by_guest ON guest_external_ids(guest_id);
```

Pro: query O(1) "guest con AirBnB ID X". Múltiples IDs por guest manejados row-by-row.
Con: 1 extra tabla, 1 extra JOIN en guest 360 detail. Por <10K guests, no significativo.

**Recomiendo**: tabla normalizada. JSON column buena solo si NUNCA queries por elemento.

**🟡 1.1.3 Status enums sin CHECK constraint**
```sql
status_master TEXT DEFAULT 'prospect',
-- enum comentado, pero no enforced en DB
```
Si bug en code mete `'PROSPECT'` (uppercase) o typo `'protect'`, row inválido sin error. Phase B.4 dashboard romperá filter.

**Fix**:
```sql
status_master TEXT NOT NULL DEFAULT 'prospect' CHECK (status_master IN (
  'prospect', 'customer', 'repeat', 'vip', 'problematic', 'banned'
)),
```

Applicar mismo pattern a TODOS los enum columns en TODAS las migrations (status, urgency, channel, event_type — ver §1.2-1.4).

**🟢 1.1.4 Timestamps redundantes**
4 columnas: `first_seen_at`, `last_activity_at`, `last_message_at`, `created_at`, `updated_at`. 

`first_seen_at` ≈ `created_at` (¿no?). Si difieren, ¿por qué? Recomiendo eliminar `first_seen_at` y usar `created_at` (Unix seconds, set en INSERT, immutable).

**🟢 1.1.5 Missing: dedupe metadata**
Cuando merge guests duplicates, perdemos historia. Add:
```sql
merged_from_guest_id TEXT,               -- si esta row absorbió otra (soft history)
merged_at INTEGER,
dedupe_confidence REAL,                  -- 0.0-1.0, score si fuzzy match (vs exact)
```

**🟢 1.1.6 Missing: GDPR / privacy controls**
```sql
data_retention_until INTEGER,            -- Unix seconds, NULL = indefinite
opted_out_of_marketing INTEGER DEFAULT 0,
deleted_at INTEGER,                      -- soft delete
```

No es urgent ahora pero meterlo desde día 1 es trivial vs migrar más tarde.

---

### 1.2 `0015_leads` — 🟡 cambios moderados

**🔴 1.2.1 `converted_to_booking_id INTEGER` vs `bookings.id TEXT`**

Inconsistencia tipo: la FK lógica es a `bookings.id` (TEXT `b_...`) o a `beds24_booking_id` (INTEGER). El comentario dice "Beds24 booking ID" pero el dashboard query natural es JOIN a bookings.id.

**Fix**:
```sql
converted_to_booking_id TEXT REFERENCES bookings(id),  -- match TEXT PK
-- O si querés ambos:
converted_to_beds24_booking_id INTEGER,
converted_to_booking_id TEXT REFERENCES bookings(id),
```

**🟡 1.2.2 `bot_followup_t3/t7/t14/t21` columnas explícitas → rigidez**

Si decides cambiar cadence en B.2 a T+5/T+10/T+15/T+20, schema migration. Si decides agregar T+30 special offer, schema migration.

Alternativa: tabla `lead_followups`:
```sql
CREATE TABLE lead_followups (
  lead_id TEXT NOT NULL REFERENCES leads(id),
  followup_type TEXT NOT NULL,           -- 'gentle' | 'nudge' | 'last_try' | 'special_offer'
  scheduled_at INTEGER NOT NULL,
  sent_at INTEGER,
  template_used TEXT,
  PRIMARY KEY (lead_id, followup_type, scheduled_at)
);
```

Pro: flexible, scriptable cadence per-property, retención full timeline.
Con: 1 query extra para "¿ya mandamos t3?" pero ~50 follow-ups/mes nada.

**Recomiendo cambio**.

**🟡 1.2.3 Missing: `next_followup_at` computed**

Cron diario busca leads que necesitan follow-up. Query actual sería:
```sql
SELECT * FROM leads
WHERE status IN ('engaged', 'quoted', 'negotiating')
AND (
  (bot_followup_t3_sent_at IS NULL AND first_contact_at < strftime('%s', 'now', '-3 days'))
  OR (bot_followup_t7_sent_at IS NULL AND first_contact_at < strftime('%s', 'now', '-7 days') AND bot_followup_t3_sent_at IS NOT NULL)
  ...
);
```

Complejo y no indexable bien. Si lo cambias a `next_followup_at INTEGER`:
```sql
SELECT * FROM leads WHERE next_followup_at <= unixepoch() AND next_followup_at IS NOT NULL;
```

Simple, indexable, 1 row update por send. Combina con tabla `lead_followups` (1.2.2) para flexibilidad total.

**🟢 1.2.4 Missing: `priority_score` para inbox sort**

Dashboard inbox ordena por urgency string, pero "hot warm cool cold" es categórico. Para sort fino:
```sql
priority_score INTEGER GENERATED ALWAYS AS (
  CASE urgency
    WHEN 'hot' THEN 1000
    WHEN 'warm' THEN 500
    WHEN 'cool' THEN 100
    ELSE 0
  END
  + COALESCE(group_size, 0) * 10
  + CASE WHEN quote_sent_at IS NOT NULL THEN 50 ELSE 0 END
) STORED,
```

D1 supports generated columns. Sort `ORDER BY priority_score DESC` es O(log n) con index.

**🟢 1.2.5 Missing: `lost_reason` enum validation**

Mismo CHECK constraint pattern que §1.1.3.

---

### 1.3 `0016_bookings` — 🟡 cambios significativos

**🔴 1.3.1 Bot action timestamps duplican guest_events**

8 columnas `welcome_sent_at`, `pre_arrival_t30_sent_at`, etc. Si `guest_events` existe (0017) y ya logea `bot_welcome_sent`, `bot_pre_arrival_sent`, esto es **redundancia con drift risk**:
- Code path A: insert event row
- Code path B: update bookings column
- Eventualmente uno se olvida, dashboard muestra inconsistente.

**Fix**: ELIMINAR las 8 columnas de bookings. Query "¿ya se mandó welcome?" → `SELECT 1 FROM guest_events WHERE booking_id=? AND event_type='bot_welcome_sent' LIMIT 1`. Indexed via `idx_events_booking`.

Mismo razonamiento para `guest_review_text`, `host_review_received_*` — duplican `reviews` table.

Schema más limpio:
```sql
CREATE TABLE bookings (
  id TEXT PRIMARY KEY,
  beds24_booking_id INTEGER UNIQUE NOT NULL,
  guest_id TEXT NOT NULL REFERENCES guests(id),
  lead_id TEXT REFERENCES leads(id),
  -- Property
  room_id INTEGER NOT NULL,
  property_id INTEGER NOT NULL DEFAULT 31862,
  -- Channel
  channel TEXT NOT NULL CHECK (channel IN ('airbnb', 'booking_com', 'direct', 'web', 'whatsapp_direct')),
  channel_reservation_code TEXT,
  -- Dates
  arrival TEXT NOT NULL,
  departure TEXT NOT NULL,
  num_nights INTEGER NOT NULL,
  -- People
  num_adults INTEGER NOT NULL,
  num_children INTEGER NOT NULL DEFAULT 0,
  num_pets INTEGER NOT NULL DEFAULT 0,
  total_guests INTEGER NOT NULL,
  -- Money
  total_amount_mxn INTEGER NOT NULL,
  deposit_amount_mxn INTEGER,
  deposit_paid INTEGER NOT NULL DEFAULT 0 CHECK (deposit_paid IN (0, 1)),
  balance_due_mxn INTEGER,
  payout_amount_mxn INTEGER,
  -- Status
  status TEXT NOT NULL DEFAULT 'booked' CHECK (status IN (
    'booked', 'pre_arrival_t30', 'pre_arrival_t7', 'pre_arrival_t1',
    'arrived', 'in_stay', 'checked_out',
    'review_pending', 'reviewed', 'archived',
    'cancelled', 'no_show', 'modified'
  )),
  beds24_status TEXT,
  -- (REMOVED: 8 bot action columns + 4 review columns — usa guest_events + reviews tables)
  -- Special offers
  special_offers_count INTEGER NOT NULL DEFAULT 0,  -- denormalized counter (incremented on send)
  -- (special_offers_sent_json REMOVED — usa guest_events.event_type='special_offer_sent')
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
```

Schema más limpio, menos drift, ~30% menos columnas.

**🟡 1.3.2 `arrival` + `departure` como TEXT 'YYYY-MM-DD'**

Funciona, pero comparisons `arrival > '2026-08-15'` lexicográficas. Fine para ISO format, pero si alguna vez se inserta DD/MM/YYYY (Mexican format por error en backfill), break.

Alternativa: usar Unix seconds INTEGER + helper en code. O strict CHECK:
```sql
arrival TEXT NOT NULL CHECK (arrival GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
```

**🟢 1.3.3 Missing índice compuesto común**

Dashboard inbox query típico: "bookings de room_id=X con status=Y ordenados por arrival". Indices actuales son `(room_id, arrival)` y `(status, arrival)`. Compuesto `(room_id, status, arrival)` cubriría ambos + uno nuevo:
```sql
CREATE INDEX idx_bookings_room_status_arrival ON bookings(room_id, status, arrival);
```

---

### 1.4 `0017_guest_events` — 🟡 changes moderados

**🟡 1.4.1 `payload_json` proliferation + falta validación**

`payload_json TEXT` flexible pero peligroso:
- Sin schema, code mete shapes distintas por bug
- Queries por payload field requieren JSON functions (lentos)
- Drift entre event_types difícil de catch

Mitigaciones (NO necesariamente eliminar JSON column):
- **Add `payload_version INTEGER NOT NULL DEFAULT 1`** — habilita migrate payload shape sin migration table
- **Document schema per event_type** en `/docs/spec/13-event-schemas.md`
- **Type-check en helper** `insertEvent(event_type, payload)` con TypeScript discriminated unions
- **For HIGH-volume event_types**: extract common fields a columnas. E.g. `msg_received` events son los más numerosos:
  ```sql
  -- Add extraction columns
  message_text TEXT,                     -- denormalized for msg_received
  message_from TEXT,                     -- denormalized for msg_received
  -- payload_json contains everything else (attachments, raw)
  ```

**🟡 1.4.2 `event_type` enum CHECK constraint**

Mismo pattern §1.1.3. Lista larga (~25 values en thread/33), pero útil:

```sql
event_type TEXT NOT NULL CHECK (event_type IN (
  -- Lead
  'lead_created', 'lead_engaged', 'lead_quoted', 'lead_pre_approved',
  'lead_won', 'lead_lost', 'lead_cold',
  -- Booking
  'booking_created', 'booking_modified', 'booking_cancelled',
  'booking_paid_deposit', 'booking_paid_balance',
  -- Stay
  'guest_arrived', 'guest_checked_out', 'no_show',
  -- Messages
  'msg_received', 'msg_sent_bot', 'msg_sent_alex',
  -- Bot actions
  'bot_welcome_sent', 'bot_followup_sent', 'bot_alert_sent',
  'bot_question_answered', 'bot_pre_arrival_sent', 'bot_review_request_sent',
  -- Reviews
  'review_received', 'review_responded',
  -- Alerts
  'critical_keyword_detected', 'low_rating_received', 'complaint_received',
  -- Manual
  'alex_intervened', 'alex_note_added', 'alex_tag_added',
  -- Phase B+ future
  'special_offer_sent', 'pre_approval_extended', 'guest_blocked'
)),
```

**🟡 1.4.3 Volume estimación + retention**

Eventos por booking típico (lifecycle completo):
- 1 booking_created
- ~10 msg_received + ~5 msg_sent_bot
- 5 bot_*_sent
- 1 booking_modified
- 1 guest_arrived, 1 guest_checked_out
- 1 review_received

≈ **24 events/booking**. Si 1500 bookings/año × 24 = 36K events/year. Después de 3 años = 108K rows. D1 max 10GB cómodamente.

Pero queries pueden lentificar. Recomiendo:
- Add `archived INTEGER NOT NULL DEFAULT 0` flag
- Cron mensual: events de bookings con status=archived → set events.archived=1
- Indices que usen partial filter `WHERE archived=0`

**🟢 1.4.4 Missing índice common**

Dashboard timeline view query: "últimos 50 events del guest X". Index actual `(guest_id, occurred_at DESC)` cubre. Pero filter "últimos 50 events tipo Y del guest X":
```sql
CREATE INDEX idx_events_guest_type_time ON guest_events(guest_id, event_type, occurred_at DESC);
```

---

### 1.5 D1 capabilities check

Verifiqué que estos features SÍ están en D1:

| Feature | Disponible | Uso propuesto |
|---|---|---|
| `CHECK` constraints | ✅ | Enum validation (§1.1.3 etc) |
| `UNIQUE` partial indexes (WHERE) | ✅ | phone_e164 dedupe (§1.1.1) |
| `GENERATED ALWAYS AS` columns | ✅ STORED | priority_score (§1.2.4) |
| `FOREIGN KEY` enforcement | 🟡 NO default | Necesita `PRAGMA foreign_keys = ON` per-connection. Confirmar en wrangler |
| FTS5 virtual tables | ✅ | Inbox full-text search (§4.3 abajo) |
| Multi-statement transactions | ✅ | Backfill batches |
| JSON functions (`json_each`, `json_extract`) | ✅ | Fallback para JSON columns |

**Acción**: confirmar foreign_keys ON en worker init code (`PRAGMA foreign_keys = ON;` antes de queries). Sin esto, FKs son DOCUMENTACIÓN no constraint.

---

## 2. Phase B sequencing review

ETAs WC vs mi estimación (con justificación):

| Phase | WC ETA | CC ETA | Δ | Razón Δ |
|---|---|---|---|---|
| B.0 obs week | 0h | 0h | — | OK |
| B.1 Welcome auto-send | 12h | **18-22h** | +50-83% | Approval mode requires UI (depends on B.4), canary logic, R2 setup, template tests, alert dispatch |
| B.2 Inquiry auto-respond | 16h | **24-32h** | +50-100% | Intent detection threshold tuning, AI question + top-20 FAQs infrastructure, multi-channel routing (Beds24 vs ManyChat) |
| B.3 D1 ingestion + backfill | 8h | **18-24h** | +125-200% | Dedupe phone normalization, 1500 booking backfill respecting rate limits, status computation jobs, integrity verification |
| B.4 Dashboard UI | 24h | **40-55h** | +66-130% | 6 routes + 7 APIs + filters/search/sort + mobile + Better Auth role-based + Playwright E2E. 24h es 1 ruta MVP, no full app |
| B.5 Pre-arrival T-7/T-1 | 6h | **8-10h** | +33-66% | Template R2 + cron + tests + quiet hours |
| B.6 In-stay | 6h | **6-8h** | OK | Similar a B.5, reuse helpers |
| B.7 Post-stay review | 4h | **5-7h** | OK | Reuse helpers de B.5/B.6 |
| B.8 VIP detection | 4h | **4-6h** | OK | Cron simple |
| **Subtotal** | **80h** | **123-164h** | **+54-105%** | |

Mi recomendación: planear con **140h promedio** (≈3.5 meses si CC trabaja 10h/sem dedicadas). El "2 meses" timeline de WC subestima.

### Missing phases recomendadas

**🟡 Phase B.0.5 — Templates Editor UI (~8-12h)**
Si Alex tiene que `git push` cada vez que edita un template welcome, no escala. Las templates DEBEN ser editables desde el dashboard.

Diseño mínimo: `/admin/templates` con lista + markdown editor (textarea + preview) + R2 write API. Incluye placeholders helper `{guestFirstName}`, `{nightsCount}`, etc.

Donde: ANTES de B.1, porque B.1 ASSUME templates en R2 funcionando + actualizables.

**🟡 Phase B.9 — Damage/cancellation handling (~16h)**

Plan no cubre:
- Special offer "stay" después de cancelación request
- Damage reporting/deposit retention flow
- Refund propio vs Beds24-managed
- AirBnB Resolution Center event ingestion (no API directo per docs)

Probable Sprint 3, pero NOTAR en el plan.

**🟢 Phase B.10 — Multi-language detection (~4-6h)**

Mensaje en EN/ES detect → set `guests.language_preferred` → LLM prompt language match.

Puede ser parte de B.2 (es prompting concern). Lo separo porque tiene tests específicos.

### Dependency issues encontrados

🔴 **B.1 depende de B.4** (parcialmente)
"Approval mode" requiere UI para que Alex apruebe welcomes. Sin B.4 no hay UI. Opciones:
- A) Quick Astro page en apps/web pre-B.4 (hack ~3h, deprecated después)
- B) Bloquear B.1 hasta B.4 listo → 4-5 semanas delay
- C) Skip approval mode → directo a canary 10% (más riesgoso)

Mi voto: **A** — quick page con auth simple, label "TEMPORAL pre-dashboard", reemplazado por B.4 view después.

🔴 **B.2 depende de B.3**
Plan dice B.2 tasks #1 = "D1 migrations 0014-0017". Pero esas migrations son scope de B.3. Reordenar: B.3 antes de B.2 (o split B.3 en B.3a migrations + B.3b backfill jobs).

🟢 **B.4 puede paralelizar con B.5/B.6**
Si CC y otro dev trabajan paralelo (no es el caso ahora), B.4 dashboard + B.5/B.6 cron handlers no se tocan. Pero con single dev, secuencial OK.

### Phase B.0 observation week — Faltas detectadas

WC dice "no coding required". Sugiero agregar:

1. **Verify `cache_hit > 0` en greeter_turn events**: si cache no hitea, costo LLM 10x mayor. Query D1 logs (o Workers Analytics) primer día post-merge cron.
2. **Verify quiet hours behavior**: enviar mensaje fake-urgent durante quiet hours, ver si bypass dispara correctamente.
3. **Verify Beds24 webhook works on real bookings**: NO test pero observa primer booking real → confirma `beds24_events` insert + `bot_messages_inbox` linked correctly.
4. **Volume baseline**: contar mensajes/día, alerts/día, false positives. Plan para B.2 depende de esto.

---

## 3. Migration strategy review

### 🔴 Blind spot WC: bot YA usa D1, no Make datastore

Thread/33 §5 dice:
> "Make datastore `conversations` legacy queda intacto. Bot greeter sigue leyendo/escribiendo ahí."

**Esto es factualmente incorrecto**. Verifiqué:
- `packages/conversation-state/src/index.ts` → `loadConversation(db: D1Database, subscriberId)` — lee de D1
- `apps/worker-bot/src/index.ts` línea 300: `loadConversation(env.DB, incoming.subscriberId)` — D1
- Migrations 0009 (conversations) + 0010 (handoff_data) están aplicadas en D1 producción (yo las verifiqué hoy via MCP)
- D1 query confirms 1 row para `573268715` con `turn_count=1, last_active=2026-05-12 04:08:58 UTC` (test previo)

**La Make datastore `85639` tiene ~100 records LEGACY**. Son conversaciones de antes del cutover a worker-bot. Datos históricos congelados, NO la fuente operacional.

**Implicación**:
- Migration plan §5 "Make datastore queda intacto, coexiste" → simplifica. NO hay coexistence operacional, solo histórico.
- "Future Sprint 3+: migrar bot greeter conversations a D1 (replace Make datastore)" → YA está hecho.
- Lo único que queda: decidir si los ~100 records Make legacy se importan a D1 conversations table o se descartan.

Mi recomendación: **importar 100 records a D1 conversations como one-shot job**. Tiempo: 1-2h. Beneficio: historial completo. Sin esto, futuras analyses pierden esos guests.

### Dedupe phone normalization — riesgo subestimado

Phone formats que voy a ver en backfill:
```
+5215570618798       # ManyChat WhatsApp (E.164 con "1" mobile prefix MX)
+525570618798        # AirBnB API (sin "1" prefix, formato no estándar pero común)
525570618798         # Beds24 algunos (sin +)
55-5706-1879         # Web form direct booking
+52 1 55 7061 8798   # User typed
+1 555-123-4567      # USA guest
```

**Sin normalizer robusto**: 5 guests "duplicados" por mismo phone con formats distintos.

**Recomendación**: usar libphonenumber-style logic. Para Cloudflare Workers (no Node), opciones:
- `libphonenumber-js` (npm, ~150KB tree-shaken)
- O custom regex parser (~50 LOC) específico para MX +52 1/2 mobile + landline

Test cases obligatorios en `tests/phone-normalize.test.ts`:
```typescript
expect(normalizeMx('+5215570618798')).toBe('+5215570618798');
expect(normalizeMx('+525570618798')).toBe('+5215570618798');     // add mobile "1"
expect(normalizeMx('525570618798')).toBe('+5215570618798');
expect(normalizeMx('55-5706-1879')).toBe('+5215570618798');
expect(normalizeMx('+52 1 55 7061 8798')).toBe('+5215570618798');
expect(normalizeMx('+1 555-123-4567')).toBe('+15551234567');     // USA pasa through
expect(normalizeMx('invalid')).toBe(null);                       // graceful failure
```

**🔴 Subestimado en B.3**: WC dice 8h total para backfill + dedupe + status computation. Solo el phone normalizer + tests es 4-6h. Total B.3 realista 18-24h.

### Backfill 365d Beds24 — rate limit estimate

Beds24 rate: 432K req/día. Backfill = 1500-2000 bookings, paginated 100 per call = 15-20 calls. Easy.

Pero per-booking enrichment (mensajes históricos) = más cara:
- `/v2/bookings/messages?bookingId=X` → 1 call per booking
- 1500 bookings × 1 call = 1500 calls. Spread over 1h = 0.4 req/s. Trivial.

**Riesgo real**: Beds24 timeout / 5xx errors mid-batch. Necesita resume capability:
```typescript
// backfill-bookings.ts pseudo
const cursor = await loadCursor(); // last processed booking_id
for (const booking of stream(beds24, { since: cursor })) {
  await upsertBooking(d1, booking);
  await saveCursor(booking.id);
}
```

Incluir en B.3 scope.

---

## 4. Dashboard UI design review

### 4.1 🔴 `apps/admin` standalone vs submount

WC propone `apps/admin/leads` como app separada. Mi recomendación: **submount en `apps/web/src/pages/admin/*`**.

**Pros submount**:
- 1 deployment (CF Pages), no nuevo subdominio DNS
- Share Better Auth context (existing en apps/web)
- Share component primitives (Tailwind tokens, layout, etc.)
- Share types (`@rdm/shared`)
- Server APIs ya en `apps/web/src/pages/api/` — adminAPIs natural extension
- 1 build pipeline

**Pros standalone**:
- Bundle size — admin code no llega a public visitors. Pero con Astro `prerender = false` solo en `/admin/*`, public bundle no afectado significativamente.
- Different deploy cadence — pero a esta escala no importa.

**Decisión**: submount. Ahorra ~10-12h vs setup standalone (separate workspace, separate CF Pages, separate DNS, separate test infra).

Estructura propuesta:
```
apps/web/src/pages/admin/
├── index.astro                    # /admin → dashboard home
├── inbox.astro                    # /admin/inbox
├── guests/
│   └── [id].astro                 # /admin/guests/g_xxx
├── bookings/
│   └── index.astro
├── pending-welcomes.astro
├── templates/                     # NEW per B.0.5 above
│   ├── index.astro
│   └── [name].astro
└── api/                           # /api/admin/*
    └── inbox.ts, guests.ts, etc.

apps/web/src/components/admin/
├── ui/                            # admin-specific primitives
│   ├── InboxCard.tsx
│   ├── GuestDetail.tsx
│   ├── Timeline.tsx
│   ├── StatusBadge.tsx
│   └── FilterBar.tsx
└── layout/
    └── AdminLayout.astro
```

### 4.2 🟡 Better Auth role-based

Actual Better Auth para apps/web tiene magic links per email. Para admin necesitas distinguir admin vs viewer:

```sql
-- Add to users table (already exists in 0001)
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'guest';
-- enum: 'guest' | 'admin' | 'viewer'
```

Middleware en `/admin/*`:
```typescript
// apps/web/src/middleware.ts (extend existing)
if (url.pathname.startsWith('/admin') && user?.role !== 'admin') {
  return Astro.redirect('/login?return=' + url.pathname);
}
```

Phase 1 (MVP): solo Alex (1 admin). Phase 2: invitar Tatiana / staff con role=viewer. No bloqueante para B.4.

### 4.3 🟢 Search via D1 FTS5

Dashboard inbox tiene "Search by name/phone/email". Con D1, opciones:

**Opción A**: `LIKE '%query%'` — funciona pero full-scan O(n)
**Opción B**: FTS5 virtual table (D1 supports it):
```sql
CREATE VIRTUAL TABLE guests_fts USING fts5(
  name, phone_e164, email, tags, notes,
  content='guests',
  content_rowid='rowid'
);

-- Trigger sync (D1 supports basic triggers)
CREATE TRIGGER guests_fts_insert AFTER INSERT ON guests BEGIN
  INSERT INTO guests_fts(rowid, name, phone_e164, email, tags, notes)
  VALUES (new.rowid, new.name, new.phone_e164, new.email, new.tags_json, new.notes);
END;
-- + delete + update triggers
```

Search query:
```sql
SELECT g.* FROM guests g
WHERE g.rowid IN (SELECT rowid FROM guests_fts WHERE guests_fts MATCH ?)
ORDER BY rank;
```

Sub-100ms incluso con 10K+ guests. Recomiendo desde B.4 day 1.

### 4.4 🟡 Polling 30s vs WebSocket

WC vota polling 30s para MVP. **Concuerdo**. WebSocket requiere Durable Objects (~$5/mes plan upgrade) + complejidad. Polling con `If-Modified-Since` header o ETag conserva ancho de banda:

```typescript
// /api/admin/inbox endpoint
const lastModified = url.searchParams.get('since'); // Unix seconds
const result = await db.prepare(`
  SELECT * FROM guests
  WHERE last_activity_at > ?
  ORDER BY last_activity_at DESC LIMIT 50
`).bind(lastModified ?? 0).all();

return Response.json(result, {
  headers: { 'Cache-Control': 'private, max-age=20' }
});
```

UI side:
```typescript
useEffect(() => {
  let lastSync = Date.now() / 1000;
  const tick = async () => {
    const updates = await fetch(`/api/admin/inbox?since=${lastSync}`);
    if (updates.results.length > 0) {
      mergeIntoState(updates.results);
      lastSync = Date.now() / 1000;
    }
  };
  const id = setInterval(tick, 30000);
  return () => clearInterval(id);
}, []);
```

Delta-only updates → mínimo ancho banda + UI smooth.

### 4.5 🟢 Mobile UX patterns recomendados

- **Bottom sheets** (no modals) — Apple/Google pattern para mobile detail views
- **Swipe-to-archive** en inbox cards usando React Touch Events o `react-swipeable`
- **Sticky filter bar** que colapsa con scroll (sticky position + transform on scroll direction)
- **Infinite scroll** via Intersection Observer (no library needed, ~30 LOC)
- **Pull-to-refresh** opcional (mobile native feeling pero adds complexity, defer)
- **Skeleton loaders** ya pattern establecido en ReviewsCarousel — replicar
- **Empty states** con illustration + call-to-action ("No hay leads hot ahora — relax 🌴")

### 4.6 🟡 Component library

WC pregunta shadcn vs raw Tailwind. Mi vote: **raw Tailwind con primitivas custom**, motivos:
- shadcn copia code en repo (no npm) — añade ~50+ files
- Bundle size: tree-shake Tailwind ya cubre 90% de lo que shadcn ofrece
- Customization: tu design tokens en `apps/web/src/styles/global.css` ya tienen patterns establecidos
- Para complex primitives (combobox, listbox), agregar **HeadlessUI** (`@headlessui/react`, 18KB) selectivamente

Estructura componentes admin:
```typescript
// Inspirado en patterns existentes
<AdminLayout>
  <FilterBar tabs={...} onFilter={...} />
  <InboxList>
    {items.map(g => <InboxCard guest={g} onClick={...} />)}
  </InboxList>
  <BottomSheet open={detail !== null} onClose={() => setDetail(null)}>
    <GuestDetail guest={detail} />
  </BottomSheet>
</AdminLayout>
```

### 4.7 🟡 Server-side pagination obligatoria

1500-2000 bookings históricos + 100-500 leads + ~10K guest_events. Mandar todo al cliente = 5-10MB JSON inicial.

Server-side pagination con cursor-based (no OFFSET, performance):
```sql
SELECT * FROM guests
WHERE last_activity_at < ? OR (last_activity_at = ? AND id < ?)
ORDER BY last_activity_at DESC, id DESC
LIMIT 50;
```

Cursor = `(last_activity_at, id)`. Stable, fast incluso con millones de rows.

---

## 5. Cost & risk estimates

### 5.1 Anthropic API costs

Pricing actual (verificado console.anthropic.com 2026-05):
- Haiku 4.5: $1.00 / MTok input, $5.00 / MTok output
- Sonnet 4.5: $3.00 / MTok input, $15.00 / MTok output
- Cache READ: $0.10 / MTok input (10x cheaper)
- Cache WRITE: $1.25 / MTok input (one-time, then reads cheap)

**Verifiqué prompt caching en Phase 0**: SÍ está configurado en `packages/agents/greeter/stage1.ts` línea 56 + `stage2.ts` línea 72 con `cache_control: { type: 'ephemeral' }`. Bien.

**Sin embargo**: prueba real con subscriber smoke hoy mostró `cache_hit: 0` (event log). Esto es **CRÍTICO** — primer mensaje siempre miss (esperado), pero subsecuentes deberían hit con ratio alto. Confirmar día 1 post-merge si crons activos generan cache hits.

**Estimación realista**:

| Phase | Volume/mes | Tokens in/turn | Tokens out/turn | Cost cached/mes | Cost no-cached/mes |
|---|---|---|---|---|---|
| B.1 Welcome | 30 bookings | 4500 | 800 | $0.50 | $4.10 |
| B.2 Inquiry (5 turns avg) | 40 leads × 5 = 200 turns | 3500 | 500 | $1.60 | $13.30 |
| B.2 Follow-ups | ~80/mes | 2000 | 300 | $0.40 | $3.20 |
| B.5 Pre-arrival | ~30/mes × 2 (T-7, T-1) = 60 | 1500 (template-based) | 200 | $0.20 | $1.40 |
| B.6 In-stay | ~30/mes × 2 = 60 | 1500 | 200 | $0.20 | $1.40 |
| B.7 Post-stay | ~30/mes | 1500 | 150 | $0.10 | $0.70 |
| **Total** | **~460 turns/mes** | | | **~$3/mes** | **~$24/mes** |

**Si cache ratio 80%** (realístico con prompt caching post-warm): ~$5-8/mes total.

Backfill one-shot: 1500 historical messages × clasificación lightweight = $5-10 one-time.

**Si volumen 5x** (escala 2027): $25-40/mes. Aún trivial.

🔴 **Pero**: si por algún bug el cache NO hitea (e.g., system prompt cambia cada turn, o cache TTL 5min se invalida), costo 10x = $80-200/mes. **Acción**: monitorear `cache_read_input_tokens` en `usage` field de respuestas Anthropic. Alert si ratio < 50%.

### 5.2 Cloudflare costs

| Service | Free tier | Uso proyectado | Status |
|---|---|---|---|
| Workers (rincon-bot) | 100K req/día | ~3K/día (cron + webhook) | ✅ 3% |
| Pages (apps/web) | unlimited deploys | Daily auto | ✅ |
| D1 reads | 5M/día | ~50K/día (admin queries) | ✅ 1% |
| D1 writes | 100K/día | ~5K/día (events + msgs) | ✅ 5% |
| D1 storage | 5GB | ~100MB year 1 | ✅ 2% |
| R2 storage | 10GB | ~50MB (templates) | ✅ <1% |
| R2 Class A ops | 1M/mes | ~10K/mes | ✅ 1% |
| KV reads | 100K/día | ~5K/día | ✅ |
| Workers Analytics | 10M data points | maybe 100K/día | ✅ |

**Total CF cost**: $0/mes plan Free. Cómodo hasta ~10x growth.

### 5.3 Beds24 API rate limits

| Operation | Cost/día | % of 432K daily |
|---|---|---|
| poll-messages */5 | 288 calls | 0.07% |
| reviews-sync 1/día × 4 rooms | 4 calls | 0% |
| webhook posts (push from Beds24) | ~variable, 0-50 | 0% |
| Welcome auto-sends (Phase B.1) | ~1/booking → 30/mes = 1/día | 0% |
| Backfill bookings (B.3 one-shot) | 1500 calls split over 4h | 0.35% one-day |

**Total**: < 1% of rate limit. Easy headroom.

### 5.4 Risks at scale (lo que se rompe primero)

Ordenado por likelihood de hit:

1. **🔴 Cache miss rate en LLM** (5x cost if breaks) — mitigation: monitor + alert
2. **🟡 Welcome auto-send wrong booking** (reputation hit) — mitigation: approval mode + canary 10%
3. **🟡 D1 conn pool exhausted on dashboard load** — D1 has implicit pool, no public spec. Real test: load test 50 concurrent admins. Mitigation: server-side caching de queries comunes
4. **🟡 Dashboard render with 1500+ rows blocks main thread** — mitigation: virtualization (react-window, 8KB)
5. **🟢 Cron overlap (sync running > 5min, next fires)** — mitigation: D1 lock row "cron_locks" tabla, check at start
6. **🟢 Beds24 webhook duplicate fire** — mitigation: idempotency key (ya implementado)
7. **🟢 R2 template fetch latency** — mitigation: KV cache (5min TTL)

---

## 6. Additional proposals (CC ideas)

Vectores que WC no exploró o subestimó:

### 6.1 🟡 Lead scoring vía heurística (no ML)

Add `leads.priority_score INTEGER GENERATED ALWAYS AS (...) STORED` (§1.2.4). Beneficio: dashboard inbox ordena por valor objetivo, no por timestamp.

Formula simple:
```
score = urgency_weight + group_size_bonus + quote_sent_bonus + channel_quality + recency_bonus
```

Implementación: 30 min. ROI: Alex prioriza top leads sin overthinking.

### 6.2 🟡 Sentiment scoring en mensajes

Cada `bot_messages_inbox.message_text` → Haiku quick classify (50-200 tokens, $0.001 per call):
```typescript
// Add column
ALTER TABLE bot_messages_inbox ADD COLUMN sentiment_score REAL;
// -1.0 (very negative) to +1.0 (very positive). NULL = not analyzed.
```

Use case: dashboard flag guest con declining sentiment trend → preempt complaints.

Cost: ~50 mensajes/día × 200 tokens × $1/MTok = $0.30/mes. Trivial.

Defer hasta B.5+ después de Phase A baseline (saber qué % son neutrales).

### 6.3 🟡 Auto-tag extraction

Cuando lead row creada, async LLM extract tags potenciales:
- "viaje corporativo", "luna de miel", "boda", "amigos", "familia con niños"
- "grupo grande" (group_size >15), "mascotas", "sin niños"

Save a `guests.tags_json`. Alex revisa/edita en dashboard.

Tiempo impl: 4-6h. Beneficio: Alex saves ~5 min/lead manual tagging.

### 6.4 🟢 CF Cache API para `/api/admin/inbox`

Endpoints admin queries lentos (server-side computation costoso) pueden cachear con CF Cache API + smart invalidation:

```typescript
const cacheKey = new Request(url.toString(), { method: 'GET' });
let response = await caches.default.match(cacheKey);
if (!response) {
  response = await fetchFromD1(...);
  response.headers.set('Cache-Control', 'private, max-age=30');
  caches.default.put(cacheKey, response.clone());
}
return response;
```

Invalidation: cuando `INSERT INTO guest_events` → `caches.default.delete(['/api/admin/inbox*'])`. Custom logic needed pero ~30 LOC.

### 6.5 🟡 Feature flags por phase

Env vars en wrangler:
```toml
[vars]
PHASE_B1_WELCOME_MODE = "approval"  # 'approval' | 'canary_10' | 'auto'
PHASE_B2_INQUIRY_AUTO = "false"     # gate auto-respond
PHASE_B6_INSTAY_AUTO = "false"
```

Code paths check `env.PHASE_BX_*`. Si rota se vuelve worse, flip flag → 0 risk, no deploy.

Tiempo impl: 1h total. ROI altísimo si algún phase rompe en prod.

### 6.6 🟡 LLM fallback ladder

Greeter actual usa Haiku 4.5. En complex intent (e.g. negotiation, complaint resolution), escalar a Sonnet 4.5:

```typescript
const result = await greeterHaiku(...);
if (result.confidence < 0.7 || result.intent === 'complex_negotiation') {
  result = await greeterSonnet(...);  // fallback
  log('llm_fallback', { from: 'haiku', to: 'sonnet', reason: result.intent });
}
```

Cost: Sonnet 3x más caro. Pero solo en ~5% turns → manageable.

Quality bump significativo para edge cases.

### 6.7 🟡 Sentry / error tracking

Workers + D1 errors actualmente solo logs. Para Phase B+ (más complejidad), Sentry vale la pena:
- Tier free: 5K errors/mes, suficiente para nuestra escala
- Auto-traces de Workers (1 click integration)
- Alerts via Slack/email cuando error rate spike

Tiempo impl: 1h. ROI: Alex sleep mejor (alerts solo en problemas real).

Alternativa cheaper: CF Logs queryable via Logpush a R2 + simple parser. Más DIY.

### 6.8 🔴 Phase B.0.5 — Templates editor UI (~8-12h)

Mencionado en §2. **Crítico** para sostenibilidad. Sin esto, Alex bottleneck en git push para edits.

### 6.9 🟡 Bot pause "alex_intervened" auto-detection

Si Alex manda mensaje manual a guest via WhatsApp/AirBnB, bot debe pausar:

```typescript
// On every msg ingest:
if (msg.from === 'alex_phone' || msg.from === 'alex_airbnb_account') {
  await pauseBot(guestId, durationHours: 24);
  await insertEvent('alex_intervened', { ... });
}
```

Cuando Alex bot_paused = 1 + bot_paused_until > now → skip auto-message.

Tiempo impl: 2h. **Sin esto: bot manda welcome encima de mensaje personal de Alex = experiencia mala para guest**.

### 6.10 🟡 Reconciliation job daily

Cron 02:00 UTC compara Beds24 (source-of-truth) vs D1 bookings:
```typescript
// daily-reconcile.ts
const beds24Bookings = await fetchAll('/v2/bookings', { since: -1day });
for (const b of beds24Bookings) {
  const d1Row = await db.get(`SELECT * FROM bookings WHERE beds24_booking_id=?`, b.id);
  if (!d1Row) await logEvent('booking_missing_from_d1', { beds24_id: b.id });
  else if (d1Row.status !== mapStatus(b.status)) await logEvent('status_drift', ...);
}
```

Surfaces silent data corruption. 1-2h impl. Critical for trust en dashboard.

### 6.11 🟢 Archival cron

Leads con status=cold > 90 días → `archived_at = unixepoch()`. Keeps active table small + queries fast.

```sql
ALTER TABLE leads ADD COLUMN archived_at INTEGER;
CREATE INDEX idx_leads_active ON leads(status, last_activity_at DESC) WHERE archived_at IS NULL;
```

Cron mensual. 1h impl.

### 6.12 🟡 Booking.com gap (deferred pero ingestible)

Plan dice "defer Booking.com". Pero Beds24 webhook viene con channel info incluyendo booking.com. Ingerir igual:
- Lead row con channel='booking_com'
- bot_messages_inbox row si hay messages
- Feature flag `PHASE_B_BOOKINGCOM_AUTO=false` → no auto-respond pero data captured

Cuando Phase B.X activate, ya hay historical data ingested.

### 6.13 🔴 ManyChat handoff signal cuando Alex toma manual

Detección "alex_intervened" via ManyChat necesita:
- Alex's ManyChat User ID (admin user de la org, not subscriber)
- Webhook ManyChat firing on Alex sending message vía MC UI
- Worker captures, sets `bot_paused_until = now + 24h`

Sin esto, Alex y bot enviarán mensajes paralelos. Confuso para guest.

### 6.14 🟡 Top-20 FAQs heurística vs LLM-derived

Plan dice "AI Question detection con top-20 FAQs". Sin top-20 list source, no funciona.

Propongo: durante Phase A observation week, log every msg_received + LLM-classify intent. Después 7 días:
```sql
SELECT event_subtype, COUNT(*) as freq
FROM guest_events
WHERE event_type = 'msg_received' AND occurred_at > strftime('%s', 'now', '-7 days')
GROUP BY event_subtype
ORDER BY freq DESC LIMIT 20;
```

Top-20 emerges from data, not from Alex memory.

Inferred top-20 likely:
- ¿Tienes disponible para [fechas]?
- ¿Cuánto cuesta para X personas?
- ¿Hay chef incluido?
- ¿Está cerca de la playa?
- ¿Cómo llego desde el aeropuerto?
- ¿Aceptan mascotas?
- ¿Cuál es la política de cancelación?
- ¿Hay alberca / piscina?
- ¿Cuántos cuartos / camas?
- ¿Está disponible para bodas / eventos?
- ¿Hay WiFi?
- ¿Hay aire acondicionado?
- ¿Pueden hacer cotización personalizada?
- ¿Aceptan grupos grandes?
- ¿Hay desayuno incluido?
- ¿Tienen reseñas?
- ¿Hay tour 360°?
- ¿Pueden enviar fotos?
- ¿Cuál es la dirección exacta?
- ¿Hay descuento por estancia larga?

Pero data > inference. Phase A observation should produce real list.

---

## 7. Open questions for Alex

Resumen de questions WC pendientes Q28-Q34 + nuevas que surgen de mi review:

| Q | Tema | Mi voto |
|---|---|---|
| Q28 | Welcome template extract HOY o week +1 | Week +1 ✅ |
| Q29 | Approval mode UI standalone o inbox? | Inbox post-MVP, hack standalone primero |
| Q30 | Booking.com code path off-feature-flag | ✅ implementar con flag |
| Q31 | Direct bookings flow | Same con `channel='direct'` ✅ |
| Q32 | Polling 30s | ✅ |
| Q33 | Notes markdown | ✅ |
| Q34 | First screen inbox vs stats | Inbox ✅ |
| **NEW Q35** | `apps/admin` standalone vs submount en apps/web | **Submount** (§4.1) — ahorra 8-12h |
| **NEW Q36** | Better Auth role-based desde day 1 o defer? | Day 1 (1 columna, 2 LOC) |
| **NEW Q37** | FTS5 search desde B.4 day 1 | ✅ Vale los 30 min |
| **NEW Q38** | Importar 100 Make legacy conversations a D1 | ✅ One-shot job en B.3 (1-2h) |
| **NEW Q39** | Templates editor UI (Phase B.0.5) | ✅ Necesario antes de B.1 |
| **NEW Q40** | Phone normalizer: libphonenumber-js (150KB) vs custom regex (50 LOC) | Custom regex MX-specific |
| **NEW Q41** | Schema enum CHECK constraints | ✅ Always (§1.1.3) |
| **NEW Q42** | Eliminar bot action columns de bookings (use guest_events) | ✅ (§1.3.1) |
| **NEW Q43** | Sentiment scoring desde día 1 o defer? | Defer hasta post-Phase-A baseline |
| **NEW Q44** | Feature flags por phase (PHASE_BX_MODE env vars) | ✅ 1h impl, ROI alto |
| **NEW Q45** | Sentry vs CF Logs only | Sentry free tier vale la pena |

---

## 8. Estimated revised ETA

### Original WC plan
- 8 sub-phases, **80h CC work**, "2 meses"

### CC revised plan
- **8 sub-phases + 1 new (B.0.5 templates UI)**
- **120-160h CC work**, "3-3.5 meses"

Breakdown:

```
Phase B.0    obs week                  0h            week 0
Phase B.0.5  templates UI       8-12h  ←NEW          week 1
Phase B.1    welcome auto-send  18-22h               weeks 2-3
Phase B.3a   migrations 0014-17 4h                   week 3
Phase B.2    inquiry respond    24-32h               weeks 3-4
Phase B.3b   backfill + dedupe  14-20h               weeks 4-5
Phase B.4    dashboard          40-55h               weeks 5-8
Phase B.5    pre-arrival         8-10h               week 8
Phase B.6    in-stay             6-8h                week 9
Phase B.7    post-stay           5-7h                week 9
Phase B.8    VIP detection       4-6h                week 10
Phase B.9    damage/cancel      ~16h (Sprint 3?)
Phase B.10   multi-lang         ~4-6h (parte de B.2)
─────────────────────────────────────────────────
Total Phase B (sin B.9)         131-178h
~3-4 meses al ritmo de CC 10h/sem
```

### Optimizaciones que recortan ETA

- ✅ Submount en apps/web (no standalone) → **-10h**
- ✅ Reusar prompt caching pattern + KB pattern de Phase 0 → **-4h**
- ✅ Vitest fixtures pre-cargados para D1 mock → **-3h**
- ✅ HeadlessUI primitives vs custom → **-4h**
- ✅ Server-side cursor pagination pattern reusable → **-3h**

Aplicando optimizaciones: **~110-150h** ≈ 2.5-3 meses.

### Decisión a Alex

Trade-off explicit:

| Plan | Duration | Risk | Quality |
|---|---|---|---|
| WC original 80h | 2 meses | Alto (subestimado, debt acumulada) | Functional |
| CC revised 130h | 3.5 meses | Bajo (margin for unknowns) | Robust |
| Hybrid (skip B.7/B.8) | 2.5 meses | Medio | MVP solid + defer review request + VIP |

Mi recomendación: **CC revised 130h** o **Hybrid 2.5 meses**. WC original es optimista en exceso.

---

## 9. Conclusión

Plan WC tiene buen norte estratégico (Guest 360, unified inbox, lifecycle stages, telemetry detallada). El esqueleto sirve. Pero hay 3 issues que si no se ajustan ANTES de implementar, costarán reescritura más tarde:

1. **Schema**: agregar CHECK constraints + UNIQUE phone normalizado + eliminar drift columns de bookings + lead_followups normalizada. SQL diffs en §1.
2. **Sequencing**: B.0.5 templates UI antes de B.1. ETAs realistas +50%.
3. **Make datastore migration**: ya está hecho, plan dice lo contrario. Importar 100 legacy records y cerrar.

Lo que me gusta del plan WC:
- ✅ Approval mode + canary 10% para B.1
- ✅ guest_events desde día 1 (telemetry rica)
- ✅ Lifecycle stages bien pensadas
- ✅ Dedupe por phone/email priority (aunque needs normalization)
- ✅ Booking.com defer con flag
- ✅ Risk table comprehensive

Lo que añade mi review:
- 🆕 Phone E.164 normalizer + tests
- 🆕 Phase B.0.5 templates UI
- 🆕 Submount admin (no standalone)
- 🆕 D1 FTS5 search
- 🆕 Reconciliation cron
- 🆕 LLM fallback ladder
- 🆕 Feature flags por phase
- 🆕 Auto bot-pause cuando Alex interviene
- 🆕 Phone normalizer test suite
- 🆕 Cache hit monitoring alert

**No bloqueante para iniciar Phase A observation week**. Lo que sí: aplicar §1 cambios al schema ANTES de escribir migrations 0014-0017 — sino retrabajo seguro.

**Mi acción next**: si Alex aprueba ajustes, escribo migrations 0014-0017 finales con todas las correcciones aplicadas como primer entregable de Phase B.3a. Tiempo: 4h (incluyendo SQL + tests + helpers `normalizePhoneE164` + `insertEvent` + `priorityScore`).

---

*Output thread/34 listo. ~3h work (lectura + análisis + escritura). CC standby para feedback Alex + WC.*

— Claude Code (CLI), 2026-05-13
