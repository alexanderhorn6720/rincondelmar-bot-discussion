# Thread 33 — Alex Q25+Q26+Q27 confirmed · Guest 360 plan + Phase B.1-B.8

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]` — review + implement Phase B post-observation, Alex `[@alex]` — visibility
**Re**: Alex confirmó modelo Guest 360 con tablas separadas + UI unificada. Plan completo Phase B.1 → B.8 + Sprint roadmap.

---

## 0. Alex decisions consolidated

| Q | Decisión | Status |
|---|---|---|
| Q21 | `apps/admin/leads` AVANZAR a Sprint 2 (no Sprint 3) | ✅ |
| Q22 | WhatsApp ya cubre hot lead alerts, PWA push después | ✅ |
| Q23 | Backfill AirBnB existing inquiries últimos 30 días | ✅ |
| Q24 | Booking.com DESPUÉS (casi nula reservación) | ✅ |
| Q25 | Backend tablas separadas, UI unificada single dashboard | ✅ |
| Q26 | Lifecycle stages cubren 95%, agregar `cancelled` + `no_show` | ✅ |
| Q27 | `guest_events` desde día 1 (telemetry detallada) | ✅ |

Bot maneja 100% automático. Alex interviene cuando quiere (mensaje personal, special offer manual), nunca requerido.

---

## 1. Status actual del stack (post-thread/31-32)

### ✅ Deployed hoy (Phase 0 + Client Bot A)
- `rincon-bot` worker v0.6.1 (commit `f754d67`, branch `feat/phase0-reviews-client-bot-a`)
- D1 migrations 0011 (beds24_events) + 0012 (reviews) + 0013 (bot_messages_inbox)
- 167 reviews ingested · 48 messages polled · 3 critical alerts a Alex ✅ funcionando
- ReviewsCarousel apps/web pending PR (CC committed C track)

### 🟡 Pending Alex inmediato
- **Rotar `ADMIN_REFRESH_SECRET` en GH Actions repo secret** (CC rotó worker-side, GH disconnected)
- Decidir activación crons GH Actions (CC propone branch separado `cron/main`)
- Aprobar PR ReviewsCarousel cuando CC lo abra

### 🟡 Pending observación 1 semana
- Phase A telemetry colectada day 1-7
- Decisión Phase B.1 arranque post-review patterns

---

## 2. Guest 360 — Schema D1 completo

### Master tables

```sql
-- ============================================================
-- 0014_guests_master.sql
-- ============================================================

CREATE TABLE guests (
  id TEXT PRIMARY KEY,                    -- 'g_<ulid>'
  
  -- Identity (1 person = 1 row, dedupe via phone/email)
  name TEXT,
  phone TEXT,                             -- E.164 format
  email TEXT,
  
  -- External identifiers (cross-channel)
  manychat_subscriber_id TEXT,
  airbnb_guest_ids_json TEXT,             -- ['user_1234', ...]
  booking_com_guest_id TEXT,
  
  -- Aggregate stats (computed, updated by triggers/jobs)
  total_bookings INTEGER DEFAULT 0,
  total_revenue_mxn INTEGER DEFAULT 0,
  total_leads INTEGER DEFAULT 0,
  total_reviews INTEGER DEFAULT 0,
  avg_rating_received REAL,               -- review host gave to guest
  avg_rating_given REAL,                  -- review guest gave to host
  
  -- Master status (computed)
  status_master TEXT DEFAULT 'prospect',
  -- enum: 'prospect' | 'customer' | 'repeat' | 'vip' | 'problematic' | 'banned'
  
  -- Tags & notes
  tags_json TEXT,                         -- ['grupo-grande', 'sept-2026', 'sin-mascotas']
  notes TEXT,                             -- Alex internal notes
  language_preferred TEXT,                -- 'es' | 'en'
  
  -- Bot control
  bot_paused INTEGER DEFAULT 0,
  bot_paused_until INTEGER,
  bot_paused_reason TEXT,
  
  -- Timestamps
  first_seen_at INTEGER NOT NULL,
  last_activity_at INTEGER NOT NULL,
  last_message_at INTEGER,
  
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX idx_guests_phone ON guests(phone);
CREATE INDEX idx_guests_email ON guests(email);
CREATE INDEX idx_guests_manychat ON guests(manychat_subscriber_id);
CREATE INDEX idx_guests_status ON guests(status_master, last_activity_at DESC);
CREATE INDEX idx_guests_activity ON guests(last_activity_at DESC);
```

### Lead table

```sql
-- ============================================================
-- 0015_leads.sql
-- ============================================================

CREATE TABLE leads (
  id TEXT PRIMARY KEY,                    -- 'l_<ulid>'
  guest_id TEXT NOT NULL REFERENCES guests(id),
  
  -- Source
  channel TEXT NOT NULL,
  -- enum: 'whatsapp' | 'airbnb' | 'booking_com' | 'instagram' | 'facebook' | 'web' | 'tiktok' | 'direct'
  channel_thread_id TEXT,                 -- airbnb_inquiry_id / manychat_subscriber / etc.
  
  -- Interest
  property_interest_room_id INTEGER,      -- 78695 | 74322 | 74316 | 637063 | NULL
  property_interest_text TEXT,            -- "rincón del mar" or fuzzy
  
  dates_check_in TEXT,                    -- 'YYYY-MM-DD'
  dates_check_out TEXT,
  group_size INTEGER,
  pets_count INTEGER DEFAULT 0,
  
  -- Quote (if sent)
  quote_amount_mxn INTEGER,
  quote_breakdown_json TEXT,              -- {base, extra_pax, cleaning, total, breakdown}
  quote_sent_at INTEGER,
  pre_approval_sent_at INTEGER,           -- AirBnB pre-approval timestamp
  pre_approval_expires_at INTEGER,        -- +24h from sent
  
  -- Lifecycle
  status TEXT NOT NULL DEFAULT 'new',
  -- enum: 'new' | 'engaged' | 'quoted' | 'negotiating' | 'pre_approved'
  --       | 'won' (became booking) | 'lost_declined' | 'lost_no_response'
  --       | 'cold' (no response 21d) | 'duplicate'
  urgency TEXT,
  -- enum: 'hot' (<2h) | 'warm' (<1d) | 'cool' (<14d) | 'cold' (>14d)
  
  -- Bot actions taken
  bot_welcome_sent_at INTEGER,
  bot_followup_t3_sent_at INTEGER,
  bot_followup_t7_sent_at INTEGER,
  bot_followup_t14_sent_at INTEGER,
  bot_last_try_t21_sent_at INTEGER,
  
  -- Conversion
  converted_to_booking_id INTEGER,        -- Beds24 booking ID
  
  -- Lost reason (if status=lost_*)
  lost_reason TEXT,                       -- 'price' | 'dates' | 'capacity' | 'other'
  lost_notes TEXT,
  
  -- Timestamps
  first_contact_at INTEGER NOT NULL,
  last_activity_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX idx_leads_guest ON leads(guest_id);
CREATE INDEX idx_leads_status ON leads(status, last_activity_at DESC);
CREATE INDEX idx_leads_urgency ON leads(urgency, last_activity_at DESC);
CREATE INDEX idx_leads_channel ON leads(channel, last_activity_at DESC);
CREATE INDEX idx_leads_room ON leads(property_interest_room_id, last_activity_at DESC);
CREATE INDEX idx_leads_followup_pending ON leads(status, bot_followup_t3_sent_at, bot_followup_t7_sent_at, bot_followup_t14_sent_at)
  WHERE status IN ('engaged', 'quoted', 'negotiating');
```

### Bookings table (sync con Beds24)

```sql
-- ============================================================
-- 0016_bookings.sql
-- ============================================================

CREATE TABLE bookings (
  id TEXT PRIMARY KEY,                    -- 'b_<beds24_booking_id>'
  beds24_booking_id INTEGER UNIQUE NOT NULL,
  guest_id TEXT NOT NULL REFERENCES guests(id),
  lead_id TEXT REFERENCES leads(id),      -- NULL if direct booking sin lead previo
  
  -- Property
  room_id INTEGER NOT NULL,
  property_id INTEGER NOT NULL,           -- 31862 always
  
  -- Channel
  channel TEXT NOT NULL,
  -- enum: 'airbnb' | 'booking_com' | 'direct' | 'web' | 'whatsapp_direct'
  channel_reservation_code TEXT,          -- HM3D2N5K (airbnb confirmation code)
  
  -- Dates
  arrival TEXT NOT NULL,                  -- 'YYYY-MM-DD'
  departure TEXT NOT NULL,
  num_nights INTEGER NOT NULL,
  
  -- People
  num_adults INTEGER NOT NULL,
  num_children INTEGER DEFAULT 0,
  num_pets INTEGER DEFAULT 0,
  total_guests INTEGER NOT NULL,
  
  -- Money
  total_amount_mxn INTEGER NOT NULL,
  deposit_amount_mxn INTEGER,
  deposit_paid INTEGER DEFAULT 0,         -- boolean
  balance_due_mxn INTEGER,
  payout_amount_mxn INTEGER,              -- after channel fees
  
  -- Lifecycle (sequential)
  status TEXT NOT NULL DEFAULT 'booked',
  -- enum: 'booked' | 'pre_arrival_t30' | 'pre_arrival_t7' | 'pre_arrival_t1'
  --       | 'arrived' | 'in_stay' | 'checked_out'
  --       | 'review_pending' | 'reviewed' | 'archived'
  --       | 'cancelled' | 'no_show' | 'modified'
  beds24_status TEXT,                     -- raw beds24 status
  
  -- Bot actions taken (auto-message timeline)
  welcome_sent_at INTEGER,
  pre_arrival_t30_sent_at INTEGER,
  pre_arrival_t7_sent_at INTEGER,
  pre_arrival_t1_sent_at INTEGER,
  in_stay_checkin_sent_at INTEGER,
  in_stay_midstay_sent_at INTEGER,
  checkout_reminder_sent_at INTEGER,
  review_request_sent_at INTEGER,
  
  -- Reviews
  guest_review_text TEXT,                 -- what host wrote about guest
  guest_review_rating INTEGER,
  host_review_received_text TEXT,         -- what guest wrote about host
  host_review_received_rating INTEGER,
  
  -- Special offer history (if applies)
  special_offers_sent_json TEXT,          -- timeline of offers
  
  -- Timestamps
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE UNIQUE INDEX idx_bookings_beds24 ON bookings(beds24_booking_id);
CREATE INDEX idx_bookings_guest ON bookings(guest_id);
CREATE INDEX idx_bookings_room_arrival ON bookings(room_id, arrival);
CREATE INDEX idx_bookings_status ON bookings(status, arrival);
CREATE INDEX idx_bookings_arrival_upcoming ON bookings(arrival)
  WHERE status IN ('booked', 'pre_arrival_t30', 'pre_arrival_t7', 'pre_arrival_t1');
CREATE INDEX idx_bookings_in_stay ON bookings(status, departure)
  WHERE status = 'in_stay';
```

### Events timeline (Q27 — desde día 1)

```sql
-- ============================================================
-- 0017_guest_events.sql
-- ============================================================

CREATE TABLE guest_events (
  id TEXT PRIMARY KEY,                    -- 'e_<ulid>'
  guest_id TEXT NOT NULL REFERENCES guests(id),
  lead_id TEXT REFERENCES leads(id),
  booking_id TEXT REFERENCES bookings(id),
  
  -- Event classification
  event_type TEXT NOT NULL,
  -- enum: 
  --   Lead: 'lead_created', 'lead_engaged', 'lead_quoted', 'lead_pre_approved',
  --         'lead_won', 'lead_lost', 'lead_cold'
  --   Booking: 'booking_created', 'booking_modified', 'booking_cancelled',
  --            'booking_paid_deposit', 'booking_paid_balance'
  --   Stay: 'guest_arrived', 'guest_checked_out', 'no_show'
  --   Messages: 'msg_received', 'msg_sent_bot', 'msg_sent_alex'
  --   Bot actions: 'bot_welcome_sent', 'bot_followup_sent', 'bot_alert_sent',
  --                'bot_question_answered', 'bot_pre_arrival_sent', 'bot_review_request_sent'
  --   Reviews: 'review_received', 'review_responded'
  --   Alerts: 'critical_keyword_detected', 'low_rating_received', 'complaint_received'
  --   Manual: 'alex_intervened', 'alex_note_added', 'alex_tag_added'
  
  event_subtype TEXT,                     -- e.g. msg_received.subtype='question_pets'
  
  -- Channel context
  channel TEXT,                           -- where event originated
  
  -- Content (flexible JSON)
  payload_json TEXT,
  -- examples:
  --   msg_received: {text, from, timestamp, attachments}
  --   bot_followup_sent: {template, t_days, scheduled_time}
  --   booking_created: {arrival, departure, amount, channel_code}
  --   critical_keyword: {category, matched_keywords, message_id}
  
  -- Idempotency (avoid double-logging)
  idempotency_key TEXT UNIQUE,            -- e.g. 'msg:<message_id>' or 'booking:<id>:created'
  
  -- When did it happen (vs created_at when logged)
  occurred_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_events_guest_time ON guest_events(guest_id, occurred_at DESC);
CREATE INDEX idx_events_type_time ON guest_events(event_type, occurred_at DESC);
CREATE INDEX idx_events_booking ON guest_events(booking_id, occurred_at DESC);
CREATE INDEX idx_events_lead ON guest_events(lead_id, occurred_at DESC);
```

### Relación con tablas existentes

```
guests (NEW)
  ├── leads (NEW)
  ├── bookings (NEW, sync from beds24)
  ├── guest_events (NEW)
  └── (links to existing)
      ├── bot_messages_inbox.booking_id → bookings.beds24_booking_id
      ├── reviews.room_id + reservation_code → bookings.beds24_booking_id
      └── beds24_events.booking_id → bookings.beds24_booking_id
```

🟡 **No re-write de tablas existentes**. Solo `JOIN` y migrations data fill.

---

## 3. Phase B.1 → B.8 detailed roadmap

### Phase B.0 — Observation week (NOW → +7 days)

**Owner**: WC + Alex passive review of Phase A data

Tareas:
- Cron daily 00:00 UTC (reviews-sync) + cron 5min (poll-messages) corriendo (post GH Actions activation)
- Alex review WhatsApp digests + critical alerts diarios
- Day +7: WC + Alex review patterns:
  - Volume mensajes/día
  - Critical keyword false positives?
  - Top-asked questions (heurística para top-20 FAQs)
  - Tiempos de respuesta Alex manual
  - Welcome template current (Alex provee versión 4068-char)

**No coding required**. Sólo observation.

### Phase B.1 — Welcome auto-send post-booking (~12h work)

**Trigger**: `beds24_events.event_type = 'booking_created'` (de Q15 webhook ya deployado)

**Owner**: CC

**Tasks**:
1. D1 migration `0018_phase_b_welcome.sql` — agrega `bookings.welcome_template_used`, `bookings.welcome_personalization_json`
2. R2 storage `welcome-templates/<roomId>.md` — Alex pega 4068-char template + placeholders (`{guestFirstName}`, `{arrivalDate}`, `{nightsCount}`, `{groupSize}`, `{chefIncluded}`, etc.)
3. Worker handler `apps/worker-bot/src/welcome-handler.ts`:
   - Subscribe to `beds24_events` insert via D1 trigger or polling
   - Fetch template R2
   - Personalize via Claude Haiku 4.5 (cache system prompt)
   - Send via Beds24 Messages API `POST /v2/bookings/messages`
   - Log to `guest_events` (type=`bot_welcome_sent`)
4. **Approval mode primero** (1 semana):
   - Welcome NO se envía, se guarda en D1 `pending_welcomes`
   - Astro page `/admin/pending-welcomes` Alex approve manual
5. **Auto-send canary 10%** (1 semana):
   - Random 10% bookings auto-send
   - 90% siguen approval mode
   - Alex valida calidad
6. **Auto-send 100%** post-canary success

**Tests**: vitest fixtures con sample bookings, mock Claude API responses.

**Risk**: bot manda welcome incorrecto. Mitigación: approval mode + canary 10%.

### Phase B.2 — Inquiry auto-respond + follow-ups (~16h work)

**Trigger**: nuevo mensaje guest detected en `bot_messages_inbox` con `lead_id != NULL` y status=`new`

**Owner**: CC

**Tasks**:
1. D1 migrations 0014-0017 (guests + leads + bookings + guest_events)
2. **Lead ingestion handler**:
   - Cron 5min ya detecta mensajes nuevos (existing)
   - NEW: classify si es lead (no booking previo) vs guest existing
   - Match phone/email/manychat_id contra `guests` table
   - Create lead row con status=`new`, link to guest (or create new guest)
   - Log event `lead_created`
3. **Auto-respond inquiry**:
   - Template R2 `inquiry-welcome-<roomId>.md` (Alex provee)
   - Includes: thanks for interest, cotización transparente con extra guest fee desglosado, "tómense su tiempo para decidir", AI question detection (top FAQs)
   - Personalize via Claude Haiku
   - Send via Beds24 Messages API (si es AirBnB) o ManyChat (si es WhatsApp)
4. **AI Question detection** (cuando top-20 FAQs estén disponibles):
   - Claude Haiku detecta intent + topic
   - Si topic ∈ top-20 con high confidence → auto-respond
   - Si no → no responder (escalate via daily digest)
5. **Auto follow-ups cron daily 09:00 Acapulco**:
   - T+3 días sin response: gentle "¿alguna duda?"
   - T+7 días sin response: nudge "Mantenemos disponibilidad..."
   - T+14 días sin response: last try "Última nota..."
   - T+21 días sin response: mark `status=cold`, stop messaging
6. **Pre-approval detection**:
   - Detect intent "quiero apartar" / "me lo aparta" / "ok confirmo"
   - Send Alex WhatsApp alert con sugerencia: "Lead caliente, manda pre-approval a guest X desde AirBnB panel" + link directo

**Tests**: vitest cover lead creation, dedupe by phone, follow-up timing logic, intent detection.

**Risk**: misclassify lead intent. Mitigación: conservador, escalate cuando duda.

### Phase B.3 — D1 Guest 360 ingestion (~8h work)

**Owner**: CC

**Tasks**:
1. **Backfill scripts**:
   - `apps/worker-bot/src/jobs/backfill-bookings.ts`: pull últimos 365 días + próximos 365 días de Beds24 → upsert bookings table
   - `apps/worker-bot/src/jobs/backfill-guests.ts`: dedupe across `bot_messages_inbox` + bookings → create guests rows
   - `apps/worker-bot/src/jobs/backfill-events.ts`: replay timeline desde existing tables → guest_events
2. **Incremental sync**:
   - Cron daily 02:00 UTC reconcilia Beds24 ↔ D1 bookings
   - Handles modifications, cancellations, payments
3. **Status computation jobs**:
   - Cron daily 03:00 UTC actualiza `guests.status_master` based en total_bookings
   - Cron hourly actualiza `leads.urgency` based en last_activity_at
   - Cron hourly transitions `bookings.status` based en dates (booked → pre_arrival_t30 → t7 → t1 → in_stay → checked_out → review_pending)

**Tests**: backfill idempotency, status transitions, dedupe correctness.

### Phase B.4 — Dashboard UI `apps/admin/leads` (~24h work)

**Owner**: CC

**Tasks**:

1. **Routes & layout** (Astro 5 + React 19):
   - `/admin` — dashboard home (stats + alerts)
   - `/admin/inbox` — unified guest list with filters
   - `/admin/guests/[id]` — guest 360 detail view
   - `/admin/bookings` — bookings view (filtered by stage)
   - `/admin/pending-welcomes` (Phase B.1 approval queue)
   - Better Auth (ya integrado per apps/web)
   - Mobile-first responsive (Tailwind)

2. **Inbox component** (main view):
   - Filter tabs: Todos · Leads · Pre-arrival · In-stay · Post-stay · Cold · VIP
   - Search by name/phone/email
   - Sort by urgency / last activity
   - Bulk actions (mark cold, add tag)
   - Real-time updates (CF Pages Realtime via polling cada 30s o WebSocket future)

3. **Guest 360 detail view**:
   - Header: name, channel, status_master badge, tags
   - Stats: total bookings, total revenue, avg rating
   - Active lead/booking card (status + actions)
   - Conversation thread (last 20 messages, link "ver completa")
   - Timeline (guest_events) — chronological
   - Action buttons: pause bot, mark cold, send personal msg, add note, add tag

4. **APIs** (Astro endpoints in apps/web or new apps/admin):
   - `GET /api/admin/inbox` — paginated, filtered
   - `GET /api/admin/guests/[id]` — full guest 360
   - `GET /api/admin/guests/[id]/timeline` — events
   - `POST /api/admin/guests/[id]/note` — add note
   - `POST /api/admin/guests/[id]/tag` — add/remove tag
   - `POST /api/admin/guests/[id]/pause` — pause bot
   - `POST /api/admin/guests/[id]/send-message` — send via bot (Beds24/ManyChat)

5. **Stats dashboard**:
   - Hot leads count (urgency=hot)
   - Bookings arriving this week
   - In-stay actives
   - Avg bot response time
   - Conversion rate inquiry → booking (last 30d)
   - Lost reasons clustering

**Tests**: Playwright E2E para inbox flow + detail view.

**Risk**: scope creep. Mitigación: ship MVP version primero (inbox + detail), iterate.

### Phase B.5 — Pre-arrival automation T-7/T-1 (~6h work)

**Owner**: CC

**Tasks**:
1. R2 templates `pre-arrival-t7.md` + `pre-arrival-t1.md` (Alex provee, propiedad-aware)
2. Cron daily 10:00 UTC busca `bookings.status = 'booked'` con `arrival - now = 7 days` → status `pre_arrival_t7` + send
3. Same para T-1
4. Personalización LLM si Alex quiere (opcional, basic templates suficientes para start)
5. Log events

### Phase B.6 — In-stay check-in + mid-stay (~6h work)

**Owner**: CC

**Tasks**:
1. Template `in-stay-arrival.md` (welcome al llegar, WiFi, gas, contacto staff)
2. Template `in-stay-midstay.md` (T+stay_days/2: "¿todo bien?")
3. Cron daily 12:00 UTC transitions bookings → in_stay
4. Auto-send con quiet hours respect

### Phase B.7 — Post-stay review request (~4h work)

**Owner**: CC

**Tasks**:
1. Template `checkout-reminder.md` (T-1 antes departure)
2. Template `post-stay-review-request.md` (T+1 después departure)
3. AirBnB tiene Auto Review Text (Beds24) — bot complementa con WhatsApp si guest era directo

### Phase B.8 — VIP/repeat detection + tagging (~4h work)

**Owner**: CC

**Tasks**:
1. Cron daily 04:00 UTC computa `guests.status_master`:
   - `total_bookings >= 3` → `vip`
   - `total_bookings == 2` → `repeat`
   - `total_bookings == 1` → `customer`
   - `total_bookings == 0` → `prospect`
2. Auto-tag: `recurring`, `last-stay-rdm`, `prefers-morenas`, etc.
3. UI dashboard surface VIP guests prominently

---

## 4. Timing & dependencies

```
Week 0 (current)
├── Phase 0 + Client Bot A deployed ✅
├── Phase A observation begins
└── Phase B.1 prep (Alex extract welcome template)

Week 1 (post-observation)
├── Phase B.1 implementation (12h) — Welcome auto-send
├── Phase B.2 starts inquiry auto-respond
└── Approval mode B.1

Week 2
├── Phase B.2 complete (16h)
├── Phase B.3 backfill scripts (8h)
└── B.1 canary 10%

Week 3-4
├── Phase B.4 Dashboard UI (24h split 2 weeks)
└── B.1 auto-send 100%

Week 5
├── Phase B.5 Pre-arrival T-7/T-1
└── Dashboard MVP shipped

Week 6
├── Phase B.6 In-stay check-in
└── Iteration based en Alex feedback

Week 7
└── Phase B.7 Post-stay review request

Week 8
└── Phase B.8 VIP/repeat detection + sprint 3 planning
```

**Total: ~2 meses para Guest 360 end-to-end completo.**

ETA total CC work: ~80h spread across 8 weeks.

---

## 5. Migration strategy — desde estado actual

### Existing data hoy

| Source | Records | Format |
|---|---|---|
| Make datastore `85639 conversations` | ~100 records `s-<id>` | history TEXT, turn_count, last_active |
| Beds24 `/bookings` | ~1500 históricos | Beds24 API JSON |
| D1 `bot_messages_inbox` | 48+ (live) | structured |
| D1 `reviews` | 167 | structured |
| D1 `beds24_events` | live | webhook payloads |

### Migration steps (Phase B.3)

1. **Create guests from bot_messages_inbox + Beds24 bookings + Make conversations**:
   - Dedupe by phone (priority) → email → manychat_subscriber_id
   - Build initial `guests` rows con stats computed
2. **Create leads retroactively**:
   - Cada conversation Make sin booking → 1 lead row con status=`cold`
   - AirBnB inquiries pasados sin booking → 1 lead row con status=`lost_no_response`
3. **Create bookings from Beds24**:
   - Backfill 365 días atrás + 365 días adelante
   - Link a guest_id por phone/email matching
4. **Replay events**:
   - Cada msg en `bot_messages_inbox` → event `msg_received` o `msg_sent_*`
   - Cada booking event → event `booking_created` etc.
   - Cada review → event `review_received`
5. **Verify integrity**:
   - `guests.total_bookings` == `COUNT(bookings WHERE guest_id=X)`
   - No orphan leads/bookings
   - All events have valid guest_id

🟡 **Make datastore `conversations` legacy** queda intacto. Bot greeter sigue leyendo/escribiendo ahí. D1 es sumario, NO source of truth para bot conversations todavía.

🟢 **Future Sprint 3+**: migrar bot greeter conversations a D1 (replace Make datastore). Por ahora coexisten.

---

## 6. Risks & mitigations

| Risk | Mitigación |
|---|---|
| Dedupe guests cross-channel mal | Score-based matching: phone exact = high, email exact = high, manychat = medium, fuzzy name = low. Alex review duplicates UI flag |
| LLM personalización welcome mala | Approval mode 1 semana + canary 10% before 100% |
| Bot manda follow-up irrelevante | Check `bot_paused` flag siempre. Alex puede pausar bot per-guest desde UI |
| Cost LLM Phase B explota | Already burned today, Auto-recharge configured. Monitor diario primera semana B.2 |
| Beds24 webhook lost messages | Cron 5min polling es fallback. Idempotency `INSERT OR IGNORE` por message_id |
| Dashboard mobile UX rota | Mobile-first design + manual test iOS/Android |
| Pre-arrival timing wrong (timezone) | Use guest's booking property timezone (Acapulco UTC-6 todos los listings) |
| Guest receives 2 welcomes (Alex + bot) | Check `bookings.welcome_sent_at` antes de send. Mark Alex's manual messages via "alex_intervened" event |

---

## 7. Open questions remaining (no bloquean implementación)

| Q | Tema | Mi voto |
|---|---|---|
| Q28 | Phase B.1 template — ¿Alex extract HOY o week +1? | Week +1 está bien, no urgencia |
| Q29 | Approval mode UI: where lives? `/admin/pending-welcomes` standalone o integrated into inbox? | Standalone primero, integrate after MVP |
| Q30 | Booking.com handling: implementar igual que AirBnB pero defer activate? | Implementar code path (low marginal cost) pero feature flag OFF |
| Q31 | Direct bookings (web `/reservar/` o WhatsApp confirmation manual): ¿flow same? | Sí — channel='direct' pero same template + lifecycle |
| Q32 | Dashboard real-time updates: polling 30s o WebSocket? | Polling 30s para MVP (más simple) |
| Q33 | Notes per guest: markdown or plain text? | Markdown (mejor UX) |
| Q34 | Phase B.4 Dashboard — primer screen al login: stats overview o inbox? | Inbox (más accionable) |

---

## 8. Acción inmediata Alex

| Prioridad | Task | Tiempo |
|---|---|---|
| 🔴 P0 | Rotar `ADMIN_REFRESH_SECRET` en GH Actions repo secret | 2 min |
| 🔴 P0 | Decidir activación crons GH Actions (CC propuso branch `cron/main` separado) | 5 min |
| 🟡 P1 | Approve PR ReviewsCarousel cuando CC lo abra | 10 min revisión |
| 🟢 P2 | Extract welcome template current (4068 chars) → markdown con placeholders | Week +1, 1h |
| 🟢 P2 | Confirm Q28-Q34 votes | Cuando tengas momento |

---

## 9. CC arranca cuando Alex confirme

### Now (esta semana — observation)
- Alex completes operational pending (rotación secret, GH Actions)
- CC monitor Phase A telemetry
- CC abre PR ReviewsCarousel

### Week +1 (post-observation)
- Alex extracts welcome template
- WC + CC review week's data + Alex provee top-20 FAQs ranking from WhatsApp histórico (si Q7 destrabado)
- CC arranca Phase B.1 implementation

### Subsequent
- CC commits weekly thread (B.1 → B.8) con progress + blockers
- WC reviews each phase pre-deploy
- Alex final approve before production

---

## 10. Summary

**Confirmed**:
- ✅ Modelo Guest 360: guests + leads + bookings + guest_events tablas separadas, UI unificada
- ✅ Lifecycle stages cubren pre-booking + post-booking + post-stay
- ✅ `guest_events` desde día 1 (telemetry detallada)
- ✅ Alex interviene cuando quiere, nunca requerido
- ✅ Booking.com defer, focus AirBnB + WhatsApp + directos
- ✅ Backfill 30 días AirBnB históricos al ir live

**Plan**:
- 4 migrations D1 nuevas (0014 guests, 0015 leads, 0016 bookings, 0017 events)
- 8 Phase B sub-phases (B.1 welcome → B.8 VIP detection)
- 2 meses timeline, ~80h CC work
- Dashboard `apps/admin/leads` Sprint 2 (post B.1+B.2)

**Pending Alex inmediato** (esta semana):
- Rotar secret
- Activar crons
- Approve ReviewsCarousel PR

**Pending Alex week +1**:
- Welcome template extract
- Top-20 FAQs ranking (Q7)
- Confirm Q28-Q34

---

*FIN thread/33. Plan completo Guest 360 + Phase B.1-B.8. CC standby para Phase A observation week, arranca B.1 post-observation.*

— Web Claude, 2026-05-12
