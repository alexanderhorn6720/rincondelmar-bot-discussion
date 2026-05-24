---
thread: 196
author: wc
topic: inbox-redesign-megaspec
status: ready-for-execution
mode: brain-deep
created: 2026-05-24
related_threads: [195, 191, 192, 193]
related_prs: []
related_decisions: [04-admin-board]
estimated_effort: 33-46h CC (split across CC-A frontend + CC-B backend)
pipeline: 2-CC + 2-WC-judge (Multi-Agent Run)
---

# Thread 196 — Inbox Redesign Megaspec

## §0. TL;DR

`/admin/inbox` está roto operacionalmente. 364 rows, lifecycle mezclado, threading inexistente, in-stay críticos perdidos 4 días. Esta spec redefine el inbox como **2 tabs** (Reservas / Leads), **1 row por cliente** (threading agregado), **readiness score 6-component** para pre-stay, **endpoint nuevo `/admin/conversation/{id}`** WhatsApp-style con LLM suggested reply (Haiku 4.5) + quick replies Kari-defined + drafts persistentes.

Pipeline: **2 CC en paralelo** (CC-A frontend, CC-B backend) + **2 WC judges** (Ops + Strat) reconcilian.

Total estimado: **33-46h CC**. Wave 1 ship target: **2026-05-31**.

---

## §1. Context — Por qué redesign

### 1.1 Estado actual del inbox

`/admin/inbox` actual:

- **364 rows totales** (auditoría 2026-05-24)
- **222 "need attention"** inflated por ruido
- **5 propiedades activas** mezcladas sin filtro útil
- **0 booking context** en rows Beds24 (`#86656366` sin nombre/propiedad/fechas)
- **Cron alerts** (`cron_alert:heartbeat_stale`, `v5_latency_degraded`, `v5_escalate_rate_high`) en queue de Kari (deberían ir a `/admin/health` + Telegram)
- **Duplicación masiva**: 14× "Rincón" (Alex test number 5217441441575), 5× Sandy, 5× Carlos, 5× Fernando — sin threading
- **Display names basura**: `.`, `😎😎👍`, `🦋🌷`, `"`
- **Bug ManyChat**: `{{first_name}}` literal apareciendo en mensajes
- **In-stay crítico perdido 4 días**: Andrea M. — Rincón del Mar día 2/4 — "luz no funciona, pastel echándose a perder" — customer loss real

### 1.2 Customer journey RDM (8 etapas)

| # | Etapa | Días | Acción esperada Kari |
|---|---|---|---|
| 1 | Lead frío | — | Bot maneja, escala si pide asesor |
| 2 | Lead caliente | <24h | Responder rápido, qualifying |
| 3 | Reserva confirmada | T-14+ | Welcome, info inicial |
| 4 | Pre-stay T-3 a T-14 | T-3 a T-14 | Coordinar pax/menu/mascotas/pago |
| 5 | Pre-stay inminente | T-2 a T-0 | ETA, last-mile coord |
| 6 | In-stay | día 1-N | Issue response immediate |
| 7 | Post-stay | T+1 a T+7 | Review nudge, thanks |
| 8 | VIP / repeat | 3+ stays | Trato preferente |

### 1.3 Por qué urgente

- **Reputación AirBnB**: response time <1h = ranking factor. In-stay issues perdidos 4d destruyen reviews.
- **Karina overload**: 222 "need attention" → fatiga decisión → critical issues invisibles.
- **Sin lifecycle clarity**: leads inciertos mezclados con guests in-stay = priorización imposible.
- **F1 events bus** (foundation) bloqueado — pero inbox redesign es ortogonal y se puede shippear primero.

### 1.4 Backlog NO en scope (capturado en thread 197)

- Diseñar flujo bot AirBnB activo (hoy passive mode)
- Flujo AirBnB inquiries respuesta inmediata <1min (ranking)

---

## §2. Scope explícito

### 2.1 IN SCOPE (esta spec)

| # | Feature | Owner |
|---|---|---|
| 1 | 2 tabs: Reservas / Leads | CC-A |
| 2 | 1 row por cliente/lead (threading aggregation) | CC-B |
| 3 | Readiness score 6 components + responsive UI | CC-A + CC-B |
| 4 | Lifecycle sections con headers en Tab Reservas | CC-A |
| 5 | Cron alerts FUERA del inbox (redirect `/admin/health`) | CC-B |
| 6 | CSS role Alex test number (tenue, no funcional) | CC-A |
| 7 | Reply directo desde inbox (AirBnB existing + WA MakeMsg) | CC-A + CC-B |
| 8 | LLM suggested reply Haiku 4.5 | CC-B |
| 9 | Quick replies Kari-defined `/admin/quick-replies` | CC-A + CC-B |
| 10 | Drafts persistentes (focus lost + debounce 2s) | CC-A + CC-B |
| 11 | Auto-pause bot 1h post-reply Kari | CC-B |
| 12 | Auto-mark responded al enviar | CC-B |
| 13 | Endpoint `/admin/conversation/{id}` WhatsApp-style | CC-A + CC-B |
| 14 | Mobile compose full-screen | CC-A |
| 15 | Filters propiedad / lifecycle / sin resp / idioma / canal | CC-A |
| 16 | Quick stats header (check-ins hoy, readiness avg, etc.) | CC-A + CC-B |

### 2.2 OUT OF SCOPE (no aquí)

- AirBnB bot activo / passive mode redesign → thread 197
- AirBnB inquiries auto-response <1min → thread 197
- F1 events bus implementation → ADR-002 foundations
- F2 observability lite → thread 195
- F3 staff PWA shell → ADR-002 foundations
- Casa Chamán surfacing → Q3 2026
- ManyChat → WABA propia migration → Q3+ planning
- M1 Pricing module → post-foundations

### 2.3 NO HACER (anti-patterns explícitos)

- **NO** LLM envía respuesta sin aprobación Kari (ADR-001)
- **NO** filtrar Alex test number de Kari's view (Alex usa bookings reales para testing UX)
- **NO** reemplazar `/admin/conv` legacy todavía — ambos coexisten, `/admin/conv` deprecated en spec posterior
- **NO** auto-import quick replies de WhatsApp/AirBnB existentes — Kari las migra manualmente (decisión explícita)
- **NO** audit trail global, solo en conversation view
- **NO** mostrar pet fee como "/noche" — siempre "/estancia"
- **NO** surfacar Casa Chamán
- **NO** ALTER TABLE durante multi-agent execution
- **NO** force-push, **NO** delete branches sin merge
- **NO** secrets plaintext

---

## §3. Closed decisions

Decisiones tomadas en sesión brain deep (transcript en chat 2026-05-24). Referencia rápida:

| # | Decisión | Fuente |
|---|---|---|
| D1 | 2 tabs: Reservas (~47) / Leads (~12) | brain v2 |
| D2 | AirBnB inquiries van en Tab Reservas (alta intent), NO Leads | brain v2 |
| D3 | 1 row por cliente, badge "N nuevos", preview = último msg | brain v2 |
| D4 | Readiness score 6 components: pax, mascotas, menu, ETA, reglas, pago | brain v3 |
| D5 | Score visual: pills desktop, score+barra mobile, score+tooltip tablet — todo CSS responsive mismo JSON | brain v3 |
| D6 | Ordenamiento: `prio = días_al_checkin DESC × (6 − readiness) ASC` | brain v3 |
| D7 | Lifecycle sections con headers (no flat) | brain v3 |
| D8 | ETA: solo pregunta bot en pre-stay msg T-1, sin workflows extra | brain v4 |
| D9 | Reglas casa: validar si form Pre-stay ya cubre — si sí, mantener componente; si no, ajustar | TBD CC-B |
| D10 | Cron alerts redirect a `/admin/health` (filter por subscriber pattern `cron-bot-alerts` y msg pattern `cron_alert:*`) | brain v2 |
| D11 | Display name basura → mostrar phone parcial | brain v2 |
| D12 | `{{first_name}}` literal → filtrar + log bug ManyChat | brain v2 |
| D13 | Threading: merge mismo phone WA + AirBnB inquiry en 1 row con ambos canales | brain v2 |
| D14 | Lead WA → confirma booking → migra Tab B → Tab A auto | brain v2 |
| D15 | Endpoint `/admin/conversation/{id}` nuevo, coexiste con `/admin/conv` legacy | brain v4 |
| D16 | Canal selector ELIMINADO (canal viene en booking) | brain v5 |
| D17 | Drawer lateral desktop, page mobile, NO toggle | brain v3 |
| D18 | Suggested reply: Haiku 4.5, editable, Kari aprueba siempre | brain v4 |
| D19 | Suggested reply inputs: historial (últimos 20 msgs) + booking ctx + readiness + R2 rdm-knowledge + D1 karina_training | brain v4 |
| D20 | Suggested reply SKIP: triviales (gracias/ok), cron, cold >7d | brain v4 |
| D21 | Quick replies: Kari define + edita las suyas, NO auto-import | brain v5 |
| D22 | Quick replies variables: `{{guest_name}}`, `{{property}}`, `{{checkin_date}}`, `{{pax}}`, `{{checkout_date}}` | brain v5 |
| D23 | Quick replies top 3 sugeridos por keyword match en compose (sin LLM extra call) | brain v5 |
| D24 | Drafts: save on focus lost (blur) + debounce 2s typing + beforeunload | brain v5 |
| D25 | Drafts: banner "📝 Borrador de hace 2h, ¿continuar?" al reabrir | brain v5 |
| D26 | Idioma: detectar guest, Kari siempre responde español, AirBnB traduce auto | brain v5 |
| D27 | Auto-mark responded: sí, al enviar | brain v5 |
| D28 | Auto-pause bot: 1h default post-reply Kari, salvo pause manual (siempre respetar) | brain v5 |
| D29 | Audit trail: solo conversation view, no global | brain v5 |
| D30 | Mobile compose: full-screen al tap Reply, no inline | brain v5 |
| D31 | Alex test number: CSS role tenue (lavanda/azul claro), Kari lo ve igual | brain v4 |
| D32 | Reply directo AirBnB ya funciona (Alex confirmó), reusar | brain v5 |
| D33 | Tab B Leads: 3 categorías por intent (Needs human / Bot falló / Cold), NO por edad | brain v3 |
| D34 | Filters: propiedad, lifecycle, días al check-in, servicio, idioma, sin resp >Xh, asignado, canal | brain v5 |

---

## §4. Implementation — multi-CC pipeline

### 4.1 División CC-A / CC-B

**Principio**: contratos API definidos antes de empezar. Cero overlap en filesystem.

| Workstream | Owner | Filesystem | Branch |
|---|---|---|---|
| Frontend (UI Astro+React) | **CC-A** | `apps/web/src/pages/admin/inbox*`, `apps/web/src/pages/admin/conversation/`, `apps/web/src/pages/admin/quick-replies/`, `apps/web/src/components/inbox/`, `apps/web/src/components/conversation/`, `apps/web/src/components/quick-replies/` | `feat/inbox-redesign-frontend` |
| Backend (Worker Hono + D1) | **CC-B** | `apps/worker-bot/src/routes/admin/inbox.ts`, `apps/worker-bot/src/routes/admin/conversation.ts`, `apps/worker-bot/src/routes/admin/quick-replies.ts`, `apps/worker-bot/src/services/suggested-reply.ts`, `apps/worker-bot/src/services/inbox-threading.ts`, `apps/worker-bot/migrations/00XX-*.sql`, `packages/db/schema/*` | `feat/inbox-redesign-backend` |

**Sync points obligatorios:**
1. **T+0** (start): ambos CC leen este spec + acuerdan API contracts (§4.4)
2. **T+50%**: ambos CC commitean stubs/mocks para integration
3. **T+90%**: integration tests cruzados
4. **T+100%**: PRs paralelos, Alex merge atomic

### 4.2 D1 schema changes (CC-B owns)

Migrations nuevas (reservar `0048-0052` — confirmar último migration aplicado antes):

#### Migration A — `inbox_threading`

```sql
-- Sin ALTER TABLE en multi-agent run. Nuevas tablas only.

-- Para threading aggregation (vista materializada)
CREATE TABLE IF NOT EXISTS inbox_thread_keys (
  thread_key TEXT PRIMARY KEY,
  primary_subscriber_id TEXT,
  primary_booking_id TEXT,
  channels JSON NOT NULL,
  guest_name TEXT,
  property_id TEXT,
  lifecycle_stage TEXT,
  last_msg_at TEXT NOT NULL,
  last_msg_preview TEXT,
  unread_count INTEGER DEFAULT 0,
  readiness_score INTEGER,
  readiness_components JSON,
  is_test BOOLEAN DEFAULT FALSE,
  is_cron_alert BOOLEAN DEFAULT FALSE,
  needs_attention BOOLEAN DEFAULT FALSE,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_inbox_thread_lifecycle ON inbox_thread_keys(lifecycle_stage, last_msg_at);
CREATE INDEX idx_inbox_thread_property ON inbox_thread_keys(property_id);
CREATE INDEX idx_inbox_thread_attention ON inbox_thread_keys(needs_attention, last_msg_at);
```

#### Migration B — `inbox_drafts`

```sql
CREATE TABLE IF NOT EXISTS inbox_drafts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_key TEXT NOT NULL,
  user_id TEXT NOT NULL,
  content TEXT NOT NULL,
  channel TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(thread_key, user_id)
);

CREATE INDEX idx_drafts_user ON inbox_drafts(user_id, updated_at);
```

#### Migration C — `quick_replies`

```sql
CREATE TABLE IF NOT EXISTS quick_replies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  emoji TEXT,
  category TEXT,
  text TEXT NOT NULL,
  channels JSON NOT NULL,
  usage_count INTEGER DEFAULT 0,
  last_used_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_quick_replies_user_active ON quick_replies(user_id, is_active);
CREATE INDEX idx_quick_replies_usage ON quick_replies(user_id, usage_count DESC);
```

#### Migration D — `suggested_reply_log`

```sql
CREATE TABLE IF NOT EXISTS suggested_reply_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_key TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  prompt_tokens INTEGER,
  completion_tokens INTEGER,
  cost_usd REAL,
  suggestion TEXT NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  edited BOOLEAN DEFAULT FALSE,
  regenerated_from_id INTEGER
);

CREATE INDEX idx_suggested_reply_thread ON suggested_reply_log(thread_key, generated_at);
```

**Antes de aplicar:** CC-B verifica número de migration actual con `wrangler d1 migrations list rincon --remote` y ajusta numeración. NO usar `0042` (feedback_system) ni `0046` (cost_telemetry — thread/175 T2).

### 4.3 Threading aggregation logic (CC-B)

```typescript
// apps/worker-bot/src/services/inbox-threading.ts

interface ThreadKey {
  thread_key: string;
  primary_subscriber_id?: string;
  primary_booking_id?: string;
  channels: ('whatsapp' | 'airbnb' | 'booking')[];
}

// Reglas merge:
// 1. WhatsApp subscriber phone → thread_key = `wa:${phone_normalized}`
// 2. Beds24 booking → thread_key = `b24:${booking_id}`
// 3. AirBnB inquiry sin booking → thread_key = `abnb-inq:${inquiry_id}`
// 4. Cross-channel merge: si WA phone aparece en booking guest_phone → unificar thread_key al booking
// 5. Cron alerts → thread_key = `cron:${alert_type}` + is_cron_alert=true (filtered out)

async function rebuildThreadKey(input: SubscriberOrBooking): Promise<ThreadKey>
async function refreshThreads(since: Date): Promise<{updated: number}>
```

**Migration backfill:** primer run procesa todos los `subscribers` + `beds24_bookings` activos (últimos 90 días) y popula `inbox_thread_keys`. Subsequent runs solo incremental.

### 4.4 API contracts (CC-A ↔ CC-B sync)

**Critical**: definir antes de empezar. CC-A mockea responses para desarrollo paralelo.

#### `GET /api/admin/inbox`

Query params: `tab` (reservas|leads), `filter` (property_id, lifecycle, no_response_hours, language, channel, show_test), `limit`, `offset`.

Response: `{ threads: ThreadRow[], stats: {...} }`

```typescript
interface ThreadRow {
  thread_key: string,
  guest_name: string | null,
  guest_name_display: string,
  property_id: string | null,
  property_name: string | null,
  pax: number | null,
  has_pets: boolean,
  lifecycle_stage: LifecycleStage,
  days_to_checkin: number | null,
  days_in_stay: number | null,
  in_stay_day_of: number | null,
  readiness_score: number | null,
  readiness_components: ReadinessComponents | null,
  last_msg_at: string,
  last_msg_preview: string,
  unread_count: number,
  channel_primary: 'airbnb' | 'whatsapp' | 'booking',
  channels: string[],
  is_test: boolean,
  needs_attention: boolean,
  has_issue: boolean,
  bot_paused_until: string | null,
  language_detected: 'es' | 'en' | 'de' | 'fr' | 'unknown',
}

interface ReadinessComponents {
  pax_confirmed: boolean,
  pets_decided: boolean,
  cooking_service: boolean,
  eta_known: boolean,
  rules_accepted: boolean,
  payment_complete: boolean,
}

type LifecycleStage =
  | 'in-stay-issue' | 'in-stay-ok'
  | 'pre-stay-imminent' | 'pre-stay' | 'pre-stay-far'
  | 'airbnb-inquiry'
  | 'post-stay' | 'vip-repeat'
  | 'lead-needs-human' | 'lead-bot-failed' | 'lead-cold';
```

Stats: `total`, `by_lifecycle`, `today_checkins`, `today_checkouts`, `in_stay_count`, `week_arrivals`, `readiness_avg`, `pending_kari: { critical, leads_hot, leads_warm }`.

#### `GET /api/admin/conversation/:thread_key`

Response: `{ thread: ThreadRow, messages: Message[], booking: BookingContext|null, suggested_reply: SuggestedReply|null, draft: Draft|null, quick_replies_top: QuickReply[] }`

```typescript
interface Message {
  id: string,
  thread_key: string,
  channel: 'airbnb' | 'whatsapp' | 'booking',
  direction: 'inbound' | 'outbound',
  sender: 'guest' | 'bot' | 'karina' | 'alex',
  content: string,
  language: string | null,
  created_at: string,
  external_message_id: string | null,
}

interface SuggestedReply {
  id: number,
  text: string,
  model: 'haiku-4.5',
  generated_at: string,
}

interface Draft {
  content: string,
  channel: string | null,
  updated_at: string,
}
```

#### `POST /api/admin/conversation/:thread_key/reply`

Request: `{ content, channel, used_suggestion_id?, edited_suggestion? }`
Response: `{ ok: true, message_id, external_message_id? }`

Side effects: send via Beds24 inbox API (airbnb/booking) or MakeMsg (whatsapp); mark thread responded; auto-pause bot 1h (respeta manual pause); delete draft; update suggested_reply_log.

#### `POST /api/admin/conversation/:thread_key/pause-bot`

Request: `{ duration_hours?, indefinite? }`
Response: `{ ok: true, bot_paused_until }`

#### `POST /api/admin/conversation/:thread_key/regenerate-suggestion`

Response: `{ suggestion: SuggestedReply }`

#### `POST /api/admin/drafts`

Request: `{ thread_key, content, channel? }`
Response: `{ ok: true, updated_at }`

#### `DELETE /api/admin/drafts/:thread_key`

Response: `{ ok: true }`

#### `GET /api/admin/quick-replies`

Response: `{ replies: QuickReply[] }`

```typescript
interface QuickReply {
  id: number,
  name: string,
  emoji: string | null,
  category: string | null,
  text: string,
  channels: string[],
  usage_count: number,
  last_used_at: string | null,
  is_active: boolean,
}
```

#### `POST /api/admin/quick-replies`

Request: `{ name, emoji?, category?, text, channels[] }`
Response: `{ ok: true, id }`

#### `PATCH /api/admin/quick-replies/:id` — partial QuickReply

#### `DELETE /api/admin/quick-replies/:id` — soft delete (is_active=false)

#### `POST /api/admin/quick-replies/:id/use` — track usage_count++

#### `GET /api/admin/cron-alerts` — separate endpoint, NOT in inbox

### 4.5 LLM suggested reply service (CC-B)

```typescript
// apps/worker-bot/src/services/suggested-reply.ts

export async function generateSuggestedReply(input: {
  thread_key: string,
  env: Env,
}): Promise<SuggestedReply | null> {
  // 1. Skip rules:
  //    - last msg trivial: /^(gracias|ok|👍|thanks?|listo|perfecto)$/i
  //    - is_cron_alert
  //    - cold > 7d
  //    Return null → UI shows no suggestion
  
  // 2. Gather context:
  //    - last 20 messages (D1)
  //    - booking context (beds24_bookings)
  //    - readiness components + score
  //    - language of last guest msg
  //    - R2 rdm-knowledge KB (relevant chunks)
  //    - D1 karina_training relevant entries
  
  // 3. System prompt target Kari, NOT guest:
  //    "Eres asistente de Karina, operadora de RDM. Genera borrador en
  //     ESPAÑOL para Kari edite. Tono cálido, profesional, conciso.
  //     Anti-patterns: NUNCA Casa Chamán. Pet fee = $300 MXN/estancia."
  
  // 4. Call Claude Haiku 4.5 with prompt caching enabled
  // 5. Log to suggested_reply_log
  // 6. Return SuggestedReply
}
```

**Cost guardrails:**
- Skip rules evitan 60%+ calls innecesarios
- Prompt caching system prompt + KB chunks (cache hit ~$0.0001)
- Budget alert daily cost > $1 (warning only)
- Log all calls to `suggested_reply_log`

**Estimación:** 100 suggestions/día × ~1500 tokens × Haiku 4.5 → ~$0.10/día → $3/mes.

### 4.6 Frontend structure (CC-A)

```
apps/web/src/
├── pages/admin/
│   ├── inbox/
│   │   ├── index.astro                    # /admin/inbox (default tab=reservas)
│   │   └── [tab].astro                    # /admin/inbox/leads
│   ├── conversation/
│   │   └── [threadKey].astro              # /admin/conversation/:key
│   └── quick-replies/
│       └── index.astro                    # /admin/quick-replies
├── components/inbox/
│   ├── InboxTabs.tsx
│   ├── InboxStatsHeader.tsx
│   ├── InboxFilters.tsx
│   ├── InboxList.tsx                      # virtualized
│   ├── ThreadRow.tsx                      # responsive
│   ├── ThreadRowDesktop.tsx
│   ├── ThreadRowMobile.tsx
│   ├── LifecycleSectionHeader.tsx
│   ├── ReadinessPills.tsx
│   ├── ReadinessScore.tsx
│   └── styles.module.css
├── components/conversation/
│   ├── ConversationPage.tsx
│   ├── ConversationDrawer.tsx             # desktop drawer
│   ├── MessageTimeline.tsx                # WhatsApp-style
│   ├── MessageBubble.tsx                  # bot=distinct
│   ├── BookingContextSidebar.tsx
│   ├── ComposeBox.tsx
│   ├── ComposeMobileFullscreen.tsx
│   ├── SuggestedReplyCard.tsx
│   ├── QuickRepliesInline.tsx             # top 3
│   ├── DraftBanner.tsx
│   └── styles.module.css
└── components/quick-replies/
    ├── QuickRepliesList.tsx
    ├── QuickReplyEditor.tsx
    ├── VariablesPicker.tsx                # {{guest_name}}
    └── styles.module.css
```

**Responsive breakpoints:**
- `<768px`: mobile (full-screen compose, score+barra, drawer→page)
- `768-1023px`: tablet (score+tooltip, compose ancho moderado)
- `≥1024px`: desktop (pills inline, drawer lateral)

**CSS role Alex test number:**

```css
[data-thread-test="true"] {
  background: linear-gradient(90deg, transparent 0%, #e8e4ff 100%);
  border-left: 3px solid #8b7ec8;
}
[data-thread-test="true"]::before {
  content: "🧪 Alex (owner)";
  font-size: 0.7em;
  color: #8b7ec8;
}
```

### 4.7 Threading sync cron

`apps/worker-bot/src/crons/refresh-inbox-threads.ts`

- Schedule: cada 5 min (`*/5 * * * *`)
- Acción: query `subscribers` + `beds24_bookings` + `messages` updated since last refresh
- Idempotent
- Log to existing observability

### 4.8 Readiness score logic

```typescript
// packages/db/services/readiness.ts

export function computeReadiness(booking: Booking, messages: Message[]): {
  score: number,
  components: ReadinessComponents,
} {
  const components = {
    pax_confirmed: booking.pax_confirmed_at != null,
    pets_decided: booking.pets_response != null,
    cooking_service: booking.cooking_response != null,
    eta_known: booking.eta != null || (booking.days_to_checkin <= 0),
    rules_accepted: booking.rules_accepted_at != null,
    payment_complete: booking.balance_due === 0,
  };
  return {
    components,
    score: Object.values(components).filter(Boolean).length,
  };
}
```

**Sources de cada componente** (CC-B implementa lookups):

| Componente | Fuente |
|---|---|
| pax_confirmed | `beds24_bookings.num_adult + num_child` confirmado |
| pets_decided | `bookings_extras.pets` o conversación parseo |
| cooking_service | `bookings_extras.cooking` o coord con Celene |
| eta_known | `bookings_extras.eta` o mensaje guest "llegamos a las X" |
| rules_accepted | `pre_stay_form_submissions.rules_accepted_at` |
| payment_complete | `worker-pago` payment_status |

Si alguna columna no existe, CC-B usa tabla auxiliar `booking_readiness_state` (NO ALTER TABLE de existentes).

---

## §5. Tests

### 5.1 Backend tests (CC-B owns)

```
apps/worker-bot/test/
├── inbox-threading.test.ts                 # threading aggregation
├── suggested-reply.test.ts                 # LLM service (mock Claude)
├── api-inbox.test.ts
├── api-conversation.test.ts
├── api-quick-replies.test.ts
├── api-drafts.test.ts
├── readiness.test.ts                       # computeReadiness
└── reply-side-effects.test.ts              # auto-pause, mark responded, delete draft
```

Coverage mínimo: 80% services nuevos, 100% thread aggregation logic.

### 5.2 Frontend tests (CC-A owns)

```
apps/web/test/
├── inbox/
│   ├── ThreadRow.test.tsx                  # responsive
│   ├── ReadinessPills.test.tsx
│   ├── InboxFilters.test.tsx
│   └── LifecycleSection.test.tsx
├── conversation/
│   ├── MessageTimeline.test.tsx
│   ├── ComposeBox.test.tsx                 # draft autosave
│   ├── SuggestedReplyCard.test.tsx
│   └── DraftBanner.test.tsx
└── quick-replies/
    ├── QuickRepliesList.test.tsx
    └── QuickReplyEditor.test.tsx           # var interpolation
```

### 5.3 Integration tests (cross)

```
test/integration/
├── inbox-end-to-end.test.ts                # mock Beds24+D1, render, filters
├── reply-flow.test.ts                      # Kari clicks reply → API → side effects
└── threading-merge.test.ts                 # WA + AirBnB same phone → 1 row
```

Run en sync point T+90%.

### 5.4 Manual smoke checklist (Alex post-merge)

1. `/admin/inbox` carga sin errores, default Tab Reservas
2. Tab Leads switch funciona, 3 categorías visibles
3. Filter por propiedad funciona
4. Click row Beds24 → `/admin/conversation/b24:XXXX` abre WhatsApp-style
5. Suggested reply aparece para mensaje no-trivial
6. Click "Usar sugerencia" → compose pre-llenado
7. Edit + send → message sent via canal correcto, draft eliminado, bot pausado 1h
8. Quick reply click → texto en compose con variables interpoladas
9. Drafts: escribir, perder focus, recargar → banner aparece
10. Cron alerts NO aparecen en inbox principal
11. Mobile (cell): row colapsado, tap → conversation full-screen
12. CSS role Alex test number visible pero tenue

---

## §6. Definition of Done

### 6.1 D1 + Backend (CC-B)

- [ ] 4 migrations aplicadas a remote D1 sin error
- [ ] `inbox_threading.ts` service + cron 5min activo
- [ ] Backfill ejecutado últimos 90 días bookings
- [ ] `suggested-reply.ts` service con skip rules
- [ ] `GET /api/admin/inbox` responde con stats + threads
- [ ] `GET /api/admin/conversation/:key` responde con messages + suggestion + draft
- [ ] `POST /api/admin/conversation/:key/reply` envía mensaje + side effects
- [ ] `POST /api/admin/conversation/:key/pause-bot` actualiza bot_paused_until
- [ ] `POST /api/admin/conversation/:key/regenerate-suggestion`
- [ ] CRUD `quick-replies` completo
- [ ] CRUD `drafts` upsert por thread+user
- [ ] Cron alerts filtrados + separate endpoint `/api/admin/cron-alerts`
- [ ] Readiness computation correct (manual spot-check 5 bookings)
- [ ] All tests pass (vitest)
- [ ] Cost telemetry: suggested_reply_log populated

### 6.2 Frontend (CC-A)

- [ ] `/admin/inbox` renderiza Tab Reservas default
- [ ] 2 tabs switch sin reload
- [ ] Lifecycle sections con headers (8 categorías cuando aplican)
- [ ] Filters bar funcional (propiedad, lifecycle, sin resp, idioma, canal, test toggle)
- [ ] ThreadRow renderiza desktop/tablet/mobile correcto
- [ ] Readiness pills inline desktop, score+barra mobile
- [ ] Click row → drawer desktop / page mobile
- [ ] `/admin/conversation/:key` WhatsApp-style timeline
- [ ] Bot messages visualmente distintos
- [ ] Booking context sidebar derecha (desktop) / collapsible (mobile)
- [ ] SuggestedReplyCard: sugerencia + [Usar][Editar][Regenerar][Skip]
- [ ] Quick replies top 3 visible en compose, click → texto interpolado
- [ ] ComposeBox: textarea + send + auto-save draft
- [ ] DraftBanner al reabrir con draft existente
- [ ] Mobile compose full-screen al tap Reply
- [ ] `/admin/quick-replies` lista + editor funcional
- [ ] Variables interpolación correcta
- [ ] CSS role Alex test number aplica solo a esa subscriber
- [ ] All component tests pass

### 6.3 Integration + Smoke

- [ ] Cross-tests integration pasan
- [ ] Smoke checklist §5.4 (12 items) pasa
- [ ] PR descriptions mobile-friendly
- [ ] STATE.md updated en rdm-bot
- [ ] No regressions en otros admin endpoints

### 6.4 Documentation

- [ ] Comment header en cada nuevo service
- [ ] D1 schema documented en `packages/db/README.md`
- [ ] API contracts documented en thread reply post-merge
- [ ] Decisions diferidas logged como follow-up issues

---

## §7. Risks + Mitigations

| # | Risk | Prob | Impact | Mitigation |
|---|---|---|---|---|
| R1 | CC-A y CC-B scope collision | Media | Alta | Filesystem split §4.1, sync points T+0/50/90 |
| R2 | API contract drift entre paralelo | Alta | Alta | Mock server CC-A consume, integration tests T+90% |
| R3 | Threading migration corrupts data | Baja | Alta | CREATE TABLE only, backfill idempotente, rollback = drop |
| R4 | LLM cost overrun | Media | Media | Skip rules, prompt caching, budget alert $1/día |
| R5 | Beds24 inbox rate limit | Baja | Media | Reusar polling existente |
| R6 | Quick reply var interpolation breaks | Media | Baja | Fallback strings: "el huésped", "su propiedad" |
| R7 | Threading falsos positivos (mismo phone diferentes personas) | Baja | Media | Merge solo si phone + nombre coinciden O misma propiedad activa |
| R8 | Suggested reply genera anti-patterns | Media | Alta | System prompt hardcodea anti-patterns + post-gen regex check |
| R9 | Mobile compose rompe back nav | Media | Media | Test en device pre-ship, history.pushState |
| R10 | Karina abrumada cambios drásticos | Media | Media | Walkthrough pre-rollout, fallback toggle "Vista clásica" si necesario |
| R11 | Cron refresh-inbox se atora | Baja | Media | Timeout 30s, log slow runs, alert si stuck |
| R12 | Drafts D1 explota | Baja | Baja | Cleanup cron diario: delete drafts > 30d |
| R13 | Multi-CC topa weekly cap | Media | Alta | Estimate 24-36h Sonnet, monitor 5h block hits, halt si próximo |
| R14 | Alex no merge atomic ambos PRs | Baja | Alta | PR descriptions con cross-reference "MERGE WITH PR #X" |

---

## §8. Multi-CC Pipeline Run — instrucciones Alex

### 8.1 Setup

1. **Verificar branches limpias**:
   ```bash
   cd c:/dev/rdm/dev/bot && git status && git pull
   cd c:/dev/rdm/dev/discussion && git status && git pull
   ```

2. **Confirmar último migration number**:
   ```bash
   wrangler d1 migrations list rincon --remote | tail -5
   ```

3. **Provisionar secrets** (si no existen):
   - `CLAUDE_API_KEY` worker-bot (suggested-reply)
   - `BEDS24_API_KEY` write (Alex confirmó)
   - `TG_BOT_TOKEN` ya existe

### 8.2 Run config

| Slot | Workstream | CC instance | WC judge |
|---|---|---|---|
| 1 | Frontend (apps/web) | CC-A Sonnet 4.6 | WC Judge-Strat (product fit + UX) |
| 2 | Backend (worker-bot + D1) | CC-B Sonnet 4.6 | WC Judge-Ops (execution + anti-patterns) |

Ambos CC consumen thread 196 + thread 197 (backlog reference).

### 8.3 Sync protocol

**T+0**: ambos CC postean reply en este thread:
```
CC-X starting. API contracts §4.4 confirmed. Mock server: <link>.
Estimated effort: Xh. First commit ETA: Tn.
```

**T+50%**: cada CC commit stubs + mocks, status update.

**T+90%**: integration tests cruzados, postear resultados.

**T+100%**: PRs paralelos, status "ready for Alex merge".

### 8.4 Halt conditions

- API contract divergencia → halt ambos, escalate Alex
- Migration error → CC-B halt, escalate
- Weekly cap próximo (5h block hit 2x consecutivo) → halt sesión
- Anti-pattern violation detected → halt + report
- Cost > $20 single CC sesión → escalate Alex

### 8.5 Comando lanzamiento (post-merge thread 196)

```bash
# Después de merge PR thread 196:
cd c:/dev/rdm/dev/discussion && git checkout main && git pull

# Worktrees paralelos en rdm-bot:
cd c:/dev/rdm/dev/bot
git worktree add ../bot-frontend feat/inbox-redesign-frontend
git worktree add ../bot-backend feat/inbox-redesign-backend

# Terminal 1 (frontend):
cd c:/dev/rdm/dev/bot-frontend
claude --model sonnet
> Lee threads/196 en rdm-discussion. Eres CC-A Frontend. Empezar §4.6.

# Terminal 2 (backend):
cd c:/dev/rdm/dev/bot-backend
claude --model sonnet
> Lee threads/196 en rdm-discussion. Eres CC-B Backend. Empezar §4.2.

# WC Judges (async, en este chat web o sesión nueva):
# - Judge-Ops: monitorea commits CC-B vs anti-patterns + DoD §6.1
# - Judge-Strat: monitorea commits CC-A vs UX Karina + DoD §6.2
```

---

## §9. Out-of-scope items → thread 197

Ver `threads/197-wc-airbnb-flows-backlog.md`:

- Backlog A: Diseñar flujo bot AirBnB activo
- Backlog B: Flujo AirBnB inquiries respuesta inmediata <1min

---

## §10. References

- **Brain deep transcript**: chat session 2026-05-24 (5 mockups iterados)
- **Memorias**: D1 UUID `d81622d7-…`, stack Astro+Hono+Drizzle, Haiku 4.5 bot, Beds24 v2, ManyChat BSP
- **Anti-patterns**: ADR-001 NO LLM money, Casa Chamán Q3, pet fee /estancia
- **Related threads**: 195 (F2 postponed), 191/192/193 (PR reviews paralelo)
- **PR template**: thread/175 ship, thread/183 report style
- **GitHub MCP audit completado**: último thread 195 verificado 2026-05-24

---

**Status: READY FOR EXECUTION**
**Author: WC (Claude.ai web, Opus 4.7)**
**Mode: brain-deep**
**Pipeline: 2-CC + 2-WC-judge**
**ETA ship: 2026-05-31**
