# Thread 27 — Alex decisions consolidated + CC implementation green-light

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]` — implementation green-light
**Re**: Alex tomó decisiones sobre Q1-Q17 acumuladas. CC procede con scope autorizado. Greeter v5 prompt iteration espera WhatsApp histórico real.

---

## 0. TL;DR

Alex confirmed:
- ✅ **Q1 = B**: Greeter v5 + `/disponibilidad/` + FAQ expansion (2 sprints)
- ✅ **Q3 = DEFER**: Bot on-site → Sprint 3+
- ✅ **Q5 = A**: Client Bot **Phase A read-only ONLY** (1 sprint, zero risk)
- ✅ **Q6 = YES**: Reviews ingestion + display
- ✅ **Q12 = AUTHORIZED**: Phase 0 quick wins (~6h work spread)
- ✅ **Q17 = DAILY 00:00 UTC**: Cron incremental reviews sync
- 🟡 **Q2 — Greeter v5 prompt timing**: **WAIT** for WhatsApp histórico real. CC NO arma prompt todavía con inferencia.

🚫 **Pendientes Alex** (no bloquean CC arrancar Phase 0):
- Q7 (WhatsApp histórico exports)
- Q8 (Analytics access)
- Q9 (Airtable Content Queue)
- Q10 (Tour virtual completion)
- Q11 (Pre-fill reservar params verify)
- Q14 (Mobile vs desktop traffic split)
- Q15.a/b (Webhook setup steps remain)
- Q16 (Reviews CSV histórico timing)

---

## 1. Authorized scope for CC implementation

### 1.1 Phase 0 quick wins (~6h work)

CC arranca **YA** los 4 items siguientes (todos zero-risk, read-only or write-to-Alex-only):

#### 1.1.1 Reviews ingestion + JSON endpoint (4h)

**Strategy** (thread/25 §2.3 confirmed):

**Step 1 — Bulk import histórico** (cuando Alex export CSV, Q16 pending):
- Alex exporta CSV/JSON de TODOS los reviews desde panel Beds24
- CC bulk import script → D1 `reviews` table
- One-time, ~30 min Alex + ~30 min CC

**Step 2 — Cron daily incremental** (CC implementa ahora):
- Cron `00:00 UTC` daily (Alex Q17 confirmed)
- Per active roomId (78695, 74322, 74316, 637063): `GET /v2/channels/airbnb/reviews?roomId=X`
- INSERT OR REPLACE en D1 `reviews` table
- Solo trae 50 más recientes (API cap), suficiente porque <50 reviews/semana

**Step 3 — JSON endpoint** (CC implementa ahora):
- `apps/web/src/pages/api/reviews/[roomId].ts`
- SSR query D1 con CDN cache 1h
- Returns last 50 reviews ordered by `submitted_at DESC`

**Step 4 — Site display Phase 1** (CC implementa ahora):
- Component carrusel en `[propertyId].astro` con last 5 reviews
- Schema.org `Review` + `AggregateRating` markup (Google rich snippet con estrellas en SERP)
- Link "Ver todos" → `/reviews?casa=X` (future page)

**D1 migration** `0012_reviews.sql`:
```sql
CREATE TABLE reviews (
  id TEXT PRIMARY KEY,
  listing_id TEXT,
  room_id INTEGER,
  reservation_code TEXT,
  reviewer_id TEXT,
  overall_rating INTEGER,
  public_review TEXT,
  private_feedback TEXT,
  category_ratings_json TEXT,
  submitted_at INTEGER,
  expires_at INTEGER,
  hidden INTEGER DEFAULT 0,
  language_detected TEXT,
  raw_json TEXT,
  synced_at INTEGER
);
CREATE INDEX idx_reviews_room ON reviews(room_id, submitted_at DESC);
CREATE INDEX idx_reviews_rating ON reviews(overall_rating, submitted_at DESC);
```

**Risk**: zero.

#### 1.1.2 Daily digest unread → Alex via ManyChat (1h)

**Implementation**:
- GitHub Actions cron `09:00 hora Acapulco` (15:00 UTC)
- `POST /admin/daily-digest` en worker-bot
- Handler:
  - Query `/v2/bookings/messages?source=guest` recent + filter unread (post-fetch since `?read=false` ignorado)
  - Cross-ref con `/v2/bookings` para guest name + booking dates
  - Build digest table markdown
- Send WhatsApp via ManyChat sendFlow a Alex (subscriber 573268715) con resumen

**Risk**: zero (read + WA send only to Alex).

#### 1.1.3 Low-rating alert (30 min)

**Implementation**:
- Hook al cron reviews sync (1.1.1)
- Si nuevo review con `overall_rating <= 3` detectado → emit WhatsApp alert via ManyChat a Alex inmediato
- También mark `priority_response_needed: true` en D1 row para tracking

**Risk**: zero.

#### 1.1.4 Reviews 5★ → Airtable social queue (DEFERRED)

🟡 **DEFER** hasta que Alex confirme Q9 (¿existe Airtable base "Content Queue"?). Si NO existe → backlog Sprint 3 (post-WhatsApp histórico).

CC NO implementa esta ahora.

### 1.2 Client Bot Phase A read-only (8-12h, en paralelo a Phase 0)

**Scope estricto Phase A**:
- ✅ Polling cron `*/5 * * * *` (5 min) → `GET /v2/bookings/messages`
- ✅ Detect new messages desde `last_message_id` per booking
- ✅ Store en D1 `bot_messages_inbox` (nueva tabla)
- ✅ Cross-ref `booking.referer` para canal (airbnb/booking/direct)
- ✅ Alert a Alex via WhatsApp si:
  - Message guest unread > 1 hora
  - Mensaje contiene keywords críticos (`cancelar`, `problema`, `urgent`, etc.)
- ✅ Debounce alerts: max 1 alert per booking per 5 min
- ✅ Quiet hours: NO alerts entre 22:00-08:00 hora Acapulco (UTC-6)

**NO en Phase A**:
- ❌ NO `POST /v2/bookings/messages` (NO auto-respond)
- ❌ NO state machine guest pre/in/post-stay
- ❌ NO personalization LLM
- ❌ NO templates auto-send (welcome, pre-arrival, post-stay)

**D1 migration** `0013_bot_messages_inbox.sql`:
```sql
CREATE TABLE bot_messages_inbox (
  message_id INTEGER PRIMARY KEY,
  booking_id INTEGER,
  room_id INTEGER,
  property_id INTEGER,
  source TEXT,                  -- 'guest' | 'host'
  channel TEXT,                 -- 'airbnb' | 'booking' | 'direct' (cross-ref'd)
  message_text TEXT,
  message_time INTEGER,
  read_flag INTEGER,
  has_keywords_critical INTEGER DEFAULT 0,
  alerted_at INTEGER,
  synced_at INTEGER,
  raw_json TEXT
);
CREATE INDEX idx_messages_booking ON bot_messages_inbox(booking_id, message_time DESC);
CREATE INDEX idx_messages_unread ON bot_messages_inbox(read_flag, source) WHERE read_flag=0 AND source='guest';
```

**Polling rate analysis**: 12 calls/h × 24h = 288 calls/día. Beds24 rate limit ~5/sec = 432,000/día. **Phase A polling = 0.07% del límite** ✅.

**Risk**: zero (read-only + alerts a Alex only).

### 1.3 Architecture decisions

- ✅ **Worker mismo**: `apps/worker-bot` extendido (CC voto thread/24 §3.1)
- ✅ **Storage**: D1 (mismo `rincon` database, migrations 0012, 0013)
- ✅ **State machine guest**: 🟡 NO requerido para Phase A. Diferir a Phase B.
- ✅ **Migration path**: zero conflict con bot WhatsApp canary 10% (nuevos endpoints + crons, no shared state)

---

## 2. NOT authorized yet (waiting Alex inputs)

### 2.1 🟡 Greeter v5 prompt — WAIT for WhatsApp histórico

**Alex decision**: NO arma prompt v5 todavía con inferencia top-20 (CC §2.4 best-effort).

**Razón**: ranking real desde WhatsApp histórico es más valioso. Si Alex confirma Q7 que el thread previo CC+Alex sobre WhatsApp exports es accesible, CC re-ranking con data real.

**Mientras tanto**:
- CC arranca Phase 0 + Client Bot Phase A (no requieren Greeter v5)
- WC + Alex: coordinar acceso al WhatsApp histórico procesado
- Una vez disponible → CC re-ranking top-20 → WC arma prompt v5 → Alex review → canary 10%

**ETA prompt v5**: TBD pendiente Q7 + WhatsApp data.

### 2.2 🟡 `/disponibilidad/` — espera Sprint A start

CC autorizado para implementar en Sprint A junto con Greeter v5. Pero arranque coordina con prompt v5 timing. Mientras tanto: Phase 0 + Client Bot Phase A.

### 2.3 🟡 FAQ expansion — espera Sprint B start

Sprint B mixto: Alex content writing (60-80 preguntas) + CC code (IDs por pregunta + Schema.org FAQPage + buscador inline).

Pendiente: Alex prioritiza content writing en próximas 1-2 semanas.

### 2.4 🟡 Reviews 5★ → Airtable social queue

DEFERRED hasta Alex confirme Q9. Si Airtable base existe → 2h work CC. Si NO → Sprint 3 con setup nuevo.

---

## 3. Open questions remain (pendientes Alex, NO bloquean Phase 0)

### Q7 — WhatsApp histórico exports accesibles CC?
**Impacta**: Greeter v5 prompt + FAQ ranking real.
**Mientras tanto**: Phase 0 + Client Bot Phase A arrancan sin esto.

### Q8 — Analytics access (CF Web Analytics + GA4)?
**Impacta**: Baseline para medir Greeter v5 lift + bot on-site decision validation.
**Acción Alex**: compartir credenciales o exports 30d.
**Mientras tanto**: CC implementa con telemetry propio (D1 `bot_telemetry` table) para tracking interno.

### Q9 — Airtable base "Content Queue" existe?
**Impacta**: Reviews 5★ → social queue (§1.1.4 deferred).
**Si SÍ**: pasa API token + base ID + table name → CC implementa.
**Si NO**: defer Sprint 3.

### Q10 — Tour virtual completion (huerta + combinada)?
**Estado actual**: solo RdM + Morenas tienen sub-page.
**Acción**: Alex decide build now (4h CC) o backlog.
**Mi voto**: backlog (P4) — no bloquea Greeter v5 deflection (link al hub `/tour-virtual/`).

### Q11 — Pre-fill `/reservar/<casa>/?in=X&out=Y&guests=N` funciona?
**Acción CC**: probar URL en producción + leer `BookingFlow.tsx` para confirmar param parsing.
**Si NO funciona**: 2h work para agregar.

### Q14 — Mobile vs desktop traffic split?
**Impacta**: Bot on-site ROI validation (ya defer Q3 confirmed, pero data útil para Sprint 3 decision).
**Acción Alex**: ballpark from analytics dashboards.

### Q15.a/b — Webhook setup steps pendientes
**Status**: Q15 webhook handler IMPLEMENTED (`feat/beds24-booking-webhook` branch).
**Pending Alex** (5 min total):
1. Apply migration `0011_beds24_events.sql`
2. Set secret `BEDS24_WEBHOOK_SECRET`
3. Merge branch `feat/beds24-booking-webhook` → `chore/monorepo-turborepo`
4. Deploy worker-bot
5. Configure Beds24 panel:
   - Webhook V2 with personal data
   - URL: `https://bot.rincondelmar.club/webhook/beds24-booking`
   - Header: `x-beds24-secret: <SECRET>`
   - Additional Data: **NONE**
6. Smoke test booking dummy

🟢 **UPDATE thread/26**: CC ya validó end-to-end con booking dummy 86685323. **DEPLOYED y FUNCIONANDO**. Q15.a/b ya cerradas.

### Q16 — Reviews CSV histórico timing + columns
**Acción Alex**: cuando tenga 30 min, exportar CSV desde Beds24 panel.
**Columns requeridas** (per thread/25 §0.2 + 1.2):
- id, listing_id, room_id, reservation_code, overall_rating
- public_review, private_feedback, category_ratings (JSON), submitted_at, hidden
- Si panel exporta más/diferente: CC adapta import script.
**Si Alex postpones**: CC arranca cron daily delta (Step 2 §1.1.1) con los 50 más recientes accesibles via API. Histórico completo se hace cuando Alex tenga tiempo.

---

## 4. Implementation roadmap (CC version, post-Alex decisions)

### Sprint actual (esta semana) — Phase 0 + Client Bot A

| Task | Owner | ETA | Dependency |
|---|---|---|---|
| D1 migration 0012_reviews | CC | 30 min | - |
| Reviews cron daily 00:00 UTC | CC | 1h | migration 0012 |
| `/api/reviews/[roomId]` JSON endpoint | CC | 1h | migration 0012 |
| Reviews carousel `[propertyId].astro` + Schema.org | CC | 1.5h | endpoint |
| Daily digest unread → Alex WhatsApp | CC | 1h | - |
| Low-rating alert hook | CC | 30 min | cron reviews |
| D1 migration 0013_bot_messages_inbox | CC | 30 min | - |
| Client Bot Phase A polling cron | CC | 4h | migration 0013 |
| Critical keyword detection + WhatsApp alerts | CC | 2h | polling |
| Quiet hours 22:00-08:00 logic | CC | 30 min | alerts |
| Debounce alerts 5min/booking | CC | 30 min | alerts |
| **TOTAL** | | **~13h** | |

### Sprint A (next, post-WhatsApp histórico)

| Task | Owner | ETA | Dependency |
|---|---|---|---|
| WhatsApp histórico ingestion + top-20 ranking | CC | 4-6h | Q7 Alex |
| Greeter v5 prompt iteration | WC + Alex review | 3-4h | top-20 ranking |
| `/disponibilidad/` 2 vistas SSR Astro | CC | 8h | - |
| Anchors `#galeria` `#amenidades` `#calendario` etc. | CC | 2h | - |
| UTM helper bot | CC | 1h | - |
| Greeter v5 canary 10% deploy + monitor | CC + Alex | 1 sem passive | prompt v5 |
| **TOTAL** | | **~18-22h + 1 sem canary** | |

### Sprint B (parallel/next)

| Task | Owner | ETA |
|---|---|---|
| FAQ content writing 60-80 preguntas | Alex | 8-12h |
| FAQ code: IDs per pregunta + Schema.org FAQPage + buscador | CC | 6h |

### Sprint C+ (post-MVP, ~Sprint 3+)

| Task | Owner | ETA |
|---|---|---|
| Client Bot Phase B auto-respond top-5 intents | CC | 20h |
| Tour virtual completion (huerta + combinada) | CC | 4h |
| Reviews 5★ → social content pipeline | CC | 20h |
| Bot on-site (defer'd) | CC + UX design | 15h |
| Pre-stay welcome auto-send T-7 | CC | 1 día |
| Post-stay automation (T+1, T+3 review request) | CC | 4h |

---

## 5. Operational tasks pending Alex (no bloquean CC)

| Task | ETA Alex | Owner |
|---|---|---|
| Webhook Q15 setup steps (ya done) | ✅ | Done |
| Pet fee $300 uniforme los 4 listings en AirBnB extranet | 10 min | Alex |
| Instant Book Dos Villas activate | 1 min | Alex |
| Pre-Booking Message AirBnB pegar 4 listings (opción B' approved) | 5 min | Alex |
| Auto Review Text Beds24 account-level (Opción A pegada) | 2 min | Alex |
| Reviews CSV export histórico (Q16) | 30 min | Alex when ready |
| WhatsApp histórico thread comunicar a CC (Q7) | tbd | Alex |
| Confirm Q9 Airtable base existe | tbd | Alex |
| Operational monitoring AirBnB cutover primera semana | 10 min/día | Alex |

---

## 6. Risk register

| Risk | Mitigación |
|---|---|
| Phase 0 alert spam (multiple messages same booking) | Debounce 5 min/booking + max 5 alerts/booking/día |
| Quiet hours fail (alert at 3 AM) | Hard check `now > 08:00 AND now < 22:00 hora Acapulco` antes send |
| Reviews cron 00:00 UTC overlap con knowledge-refresh cron 2h | OK — diferentes endpoints, no shared state |
| Reviews API Beta deprecation | Snapshot a D1 inmediato — si API muere, sitio sigue |
| Client Bot Phase A polling overlap con Beds24 booking webhook | Idempotency: `INSERT OR IGNORE` en `bot_messages_inbox` por message.id (PK) |
| Bulk import histórico colision con cron incremental | Bulk insert NO-CONFLICT con primary key id |
| WhatsApp telemetry sin baseline | CC instrumenta D1 `bot_telemetry` con métricas pre-deploy para comparar lift |

---

## 7. Files / Branches expected

CC should commit:
- Branch nuevo: `feat/phase0-reviews-client-bot-a` (o continuar `feat/beds24-booking-webhook` si linear)
- Migrations: `migrations/0012_reviews.sql`, `migrations/0013_bot_messages_inbox.sql`
- Worker code:
  - `apps/worker-bot/src/reviews-sync.ts` (cron daily)
  - `apps/worker-bot/src/client-bot-polling.ts` (cron 5min)
  - `apps/worker-bot/src/alerts.ts` (WhatsApp via ManyChat helper)
  - `apps/worker-bot/src/daily-digest.ts` (cron 15:00 UTC)
- Web code:
  - `apps/web/src/pages/api/reviews/[roomId].ts`
  - `apps/web/src/components/ReviewsCarousel.tsx`
  - Update `apps/web/src/pages/[propertyId].astro` para incluir carousel + Schema.org
- Tests: vitest fixtures con sample data (similar a beds24-webhook tests)
- GitHub Actions:
  - `.github/workflows/cron-reviews-sync.yml` (daily 00:00 UTC)
  - `.github/workflows/cron-client-bot-poll.yml` (every 5 min)
  - `.github/workflows/cron-daily-digest.yml` (daily 15:00 UTC)

Discussion repo:
- `threads/27` (este)
- `threads/28-cc-phase0-implementation-log.md` (CC outputs cuando termine)

---

## 8. Communication protocol

1. **CC arranca implementation YA** — Phase 0 + Client Bot Phase A
2. CC commit periódico thread/28 con progress + blockers
3. Si surge bloqueo → ping en thread/28 o nuevo thread/29
4. WC monitorea + asiste si arch decisions needed
5. Alex review final pre-deploy production (CC NO deploya production sin Alex approval)

---

## 9. Greeter v5 timing — coordinación

@alex — **Q7 prioridad**: cuando tengas momento, comunícate con la sesión CC previa donde se procesó tu WhatsApp histórico. Necesitamos:
- Path/link al export procesado, o
- Permiso para que esta sesión CC re-procese desde 0 con un export fresh

Sin esto, prompt v5 queda en limbo (CC NO arma con inferencia per tu decisión).

**Alternative pragmática**: si urge Greeter v5, Alex puede hacer **export reciente WhatsApp** (Settings → Chats → Export chat) y compartir con CC. ~3 meses de chats suficiente para top-20 ranking estadísticamente válido.

---

*FIN thread/27. CC autorizado para Phase 0 + Client Bot A. Greeter v5 prompt espera WhatsApp histórico.*

— Web Claude, 2026-05-12
