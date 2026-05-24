# 196 — WC — Inbox Redesign Spec (Reservas + Leads + LLM suggestions + threading)

> **Status:** SPEC ready for multi-CC execution
> **Pipeline:** 2 CC paralelos (CC-A frontend, CC-B backend) + 2 WC judge (Ops, Strat)
> **Total estimated effort:** 33–46h CC, target wall-clock ~1–2 días concurrent
> **Prerequisites:** zero-auth liberal aplicado (commit `7ffdfe3` rdm-bot ✅)
> **Wave:** standalone, no F1/F2 dependency
> **Backlog captured separately:** thread/197 (AirBnB bot activation + inquiry auto-response)

---

## 0. Meta

| Field | Value |
|---|---|
| Author | WC |
| Date | 2026-05-23 |
| Discussion source | WC brain deep session, 5 mockup iterations v1→v5 con Alex |
| CC-A territory | `apps/web/**` (admin frontend + conversation endpoint + quick replies UI) |
| CC-B territory | `apps/worker-bot/**` + `packages/db/migrations/**` + `packages/agents/**` |
| Judge-Ops focus | scope creep, file boundary respect, anti-patterns (mem rules), tests pass without diff review |
| Judge-Strat focus | product fit Karina UX, lifecycle alignment, mobile usability |
| Alex role | merges, smoke tests, owns business decisions during run |
| Sync gates | 3 (contracts frozen, integration test, final verification) |

---

## 1. Context (why)

### 1.1 Pain del inbox actual `/admin/inbox`

Estado verificado anoche (2026-05-23):

| Métrica | Valor | Problema |
|---|---|---|
| Total rows | 364 | Inflado, ruido masivo |
| "Need attention" | 222 | Imposible triagear |
| Cron alerts | 14× `cron_alert:heartbeat_stale`, `v5_latency_degraded`, `v5_escalate_rate_high` | NO debe ir a queue Karina → `/admin/health` |
| Self-tests Alex | 14× "Rincón" (5217441441575) | Owner number contaminando queue |
| Duplicación | 5× Sandy, 5× Carlos, 5× Fernando (mismo phone) | Cero threading, 1 row por mensaje |
| Display names basura | `.`, `😎😎👍`, `🦋🌷`, `"` | Imposible identificar guest |
| Placeholder bug | `{{first_name}}` literal | Template ManyChat no renderizó |
| In-stay crítico perdido | Andrea M. "luz no funciona + pastel echándose a perder" 4 días en queue | Customer loss directo |
| Booking context | Solo `#86656366`, sin nombre/propiedad/fechas | Karina abre conv para entender qué es |

### 1.2 Modelo mental cliente RDM (lifecycle definido)

| Etapa | Trigger | Acción esperada |
|---|---|---|
| Lead frío (Tab B) | WA inbound, no booking confirmado | Bot maneja, escalación solo si needs human |
| Lead caliente (Tab B) | WA inbound + intent claro de reserva | Bot maneja, escalación si bot falla |
| Reserva confirmada (Tab A) | Beds24 booking creado | Aparece en Tab A |
| Pre-stay T-3 a T-14 | Booking confirmado, días al check-in en rango | Llenar readiness score, ping si falta data |
| Pre-stay inminente T-2 a T-0 | Días al check-in ≤2 | Prioridad alta, todo armado |
| In-stay | check_in ≤ today ≤ check_out | Monitor issues, atención inmediata si problema |
| Post-stay T+1 a T+7 | check_out pasó | Thx + review nudge |
| VIP/repeat | 3+ stays históricos | Trato especial |

### 1.3 Por qué un row por cliente, no por conversación

Karina abre el inbox y ve a Sandy 5 veces (mismo phone, 5 msgs en 30 min). Pierde 4× tiempo decidiendo qué responder. Necesita: 1 row Sandy, badge "5 nuevos", preview último msg, expand para historial completo.

---

## 2. Explicit scope

### 2.1 YES (in scope)

| # | Feature | Owner |
|---|---|---|
| 1 | 2 tabs: Reservas / Leads (counters live) | CC-A |
| 2 | 1 row por cliente/lead (threading agregado D1 view) | CC-B query + CC-A render |
| 3 | Readiness score 6 components + responsive UI (pills desktop / score mobile / hybrid tablet) | CC-B calc + CC-A render |
| 4 | Tab Reservas: 8 lifecycle sections con headers (in-stay issue, in-stay OK, ≤48h, T-3 a T-14, AirBnB inquiries, T-15+, post-stay, VIP) | CC-A render + CC-B categorize |
| 5 | Tab Leads: 3 intent sections (Needs human, Bot falló, Cold >24h) | CC-A render + CC-B categorize |
| 6 | Filter `cron_alert:*` + `{{first_name}}` literals out of inbox (visible only in `/admin/health` and logs) | CC-B |
| 7 | Filter display name basura → mostrar phone parcial | CC-B util |
| 8 | Test number `5217441441575` CSS role tenue (lavanda + border-left), Kari lo ve como cliente normal | CC-A CSS |
| 9 | New endpoint `/admin/conversation/[id]` WhatsApp-style (bubbles, timeline, booking sidebar) | CC-A page + CC-B endpoint |
| 10 | Reply directo desde inbox: AirBnB/Booking (Beds24 API existente) + WhatsApp (MakeMsg ManyChat) | CC-B routing + CC-A compose |
| 11 | LLM suggested reply (Haiku 4.5, pre-cargada editable) — inputs: hist 20 msgs + booking + readiness + R2 KB + karina_training | CC-B endpoint + CC-A render |
| 12 | New endpoint `/admin/quick-replies` con CRUD Kari-defined (variables: `{{guest_name}}`, `{{property}}`, `{{checkin_date}}`, `{{pax}}`, `{{checkout_date}}`) | CC-A UI + CC-B CRUD |
| 13 | Drafts persistentes (focus lost blur + 2s typing debounce + `beforeunload` final save) | CC-A textarea wiring + CC-B `inbox_drafts` table |
| 14 | Auto-pause bot 1h post-reply manual de Kari (respetar pause manual indefinido) | CC-B |
| 15 | Auto-mark responded al enviar | CC-B |
| 16 | Audit trail solo en conversation view (no global) | CC-B query + CC-A render |
| 17 | Idioma detectado guest (badge), Kari siempre responde ES, AirBnB traduce auto | CC-B detection + CC-A badge |
| 18 | Mobile compose full-screen al tap Reply (no inline cramped) | CC-A responsive |
| 19 | Booking context sidebar derecha en conversation view (fechas, pax, propiedad, servicios, readiness) | CC-A render + CC-B join |
| 20 | Quick replies top 3 sugeridos por keyword match (regex/string match en nombres) en compose | CC-A |

### 2.2 NO (out of scope, NO inline fix — open issue si CC encuentra)

| # | Item | Razón |
|---|---|---|
| N1 | Migration/redirect `/admin/conv` → `/admin/conversation/[id]` | Coexisten por ahora, `/conv` queda como raw debug |
| N2 | Embedding-based quick reply suggestions | Regex/keyword match es suficiente Wave 1 |
| N3 | Cron alerts UI redesign (`/admin/health`) | Out of scope, ya existe |
| N4 | AirBnB bot activation (hoy passive mode) | → thread/197 §1 |
| N5 | AirBnB inquiry auto-response <1min | → thread/197 §2 |
| N6 | Booking.com reply directo si Beds24 no lo soporta nativo | Verificar Beds24 API caps; si no, skip y `[disabled]` button |
| N7 | Casa Chamán (roomId 679176) | Renovation Q3 2026 — exclude from properties filter, NO surface |
| N8 | LLM suggestion para mensajes triviales ("gracias", "ok", emoji solo) | Skip silently (waste) |
| N9 | LLM suggestion para conversaciones cold >7d | Stale context, skip |
| N10 | LLM suggestion para cron alerts | N/A (filtered out anyway) |
| N11 | Global notification system (toast/email a Kari de nueva conv) | Separate spec |
| N12 | Bulk actions (mark N as resolved) | Separate spec |
| N13 | Stats dashboard separado | Quick stats header en inbox basta |
| N14 | Search semántica inbox | Filters + text search basta Wave 1 |
| N15 | Multi-user (Kari + Alex viendo simultáneo con cursor presence) | Last-write-wins drafts, no presence Wave 1 |

---

## 3. Closed decisions (no re-debate durante run)

| # | Decisión | Razón |
|---|---|---|
| D1 | Readiness score = 6 components: pax final, mascotas decidido, menu/cocina, ETA, reglas aceptadas, pago liquidado | Discussion con Alex v3 |
| D2 | Score render: pills inline desktop ≥1024px, score numérico tablet 768–1024 con tooltip, score + barra mobile <768 + pills en expand | Discussion v3, responsive same JSON |
| D3 | Ordenamiento Tab Reservas pre-stay: `días_al_checkin DESC × (6 − readiness) ASC` | T-1 con 3/6 sube; T-12 con 5/6 baja |
| D4 | ETA pregunta SOLO en pre-stay msg T-1, sin workflows extra. Si guest no responde, ETA queda incompleto, score se ve, Kari decide | Alex v4: "no es tan importante" |
| D5 | Tab Reservas incluye AirBnB inquiries sin confirmar (alta intent, no leads inciertos) | Discussion v2 |
| D6 | Tab Leads ordena por intervención necesaria (Needs human / Bot falló / Cold), NO por edad | Discussion v3 |
| D7 | 1 row por cliente (threading agregado), badge "N nuevos" | Mismo phone + mismo channel = 1 row |
| D8 | Cross-channel merge: mismo phone WA + AirBnB inquiry → 1 row merged, ambos canales visibles | Discussion v2 |
| D9 | Lead WA confirma booking → migra Tab B → Tab A automático | D1 trigger o query unión |
| D10 | Test number `5217441441575` (Alex owner) = trato normal, CSS role tenue, sin filter especial | Discussion v4 |
| D11 | Cron alerts (`cron_alert:*`, `cron-bot-alerts` subscriber) → filter out de inbox, surface en `/admin/health` | Discussion v2 |
| D12 | Placeholder bug `{{first_name}}` literal → filter out + log a `bot_errors` table | Discussion v2 |
| D13 | Display name basura (1-2 chars, solo emojis, comilla suelta, punto solo) → mostrar `phone parcial (...XXX-YYYY)` | Discussion v2 |
| D14 | Endpoint conversación nuevo `/admin/conversation/[id]` (NO reemplaza `/admin/conv`, coexisten) | Discussion v4 |
| D15 | Drawer lateral desktop vs página full mobile | Drawer mantiene queue visible desktop |
| D16 | Channel selector eliminado en compose (canal viene en booking, no opción) | Discussion v5 |
| D17 | Reply directo AirBnB/Booking YA FUNCIONA (Beds24 API tested) — reusar | Alex v5 confirmó pruebas OK |
| D18 | LLM suggested reply = Haiku 4.5 (rápido, barato, ya en stack) | ~$0.001/suggestion, ~$3/mes |
| D19 | LLM suggestion NUNCA envía sola, siempre Kari aprueba/edita en compose box | Anti-pattern: bot manda directo |
| D20 | Skip LLM suggestion casos: triviales (gracias/ok), cron, cold >7d | Discussion v5 |
| D21 | Quick replies Kari-defined en `/admin/quick-replies`, no pre-built RDM | Alex tiene WA/AirBnB existentes |
| D22 | Quick replies migración manual (Kari pega desde WA/AirBnB) | No auto-import Wave 1 |
| D23 | Quick replies variables: `{{guest_name}}`, `{{property}}`, `{{checkin_date}}`, `{{pax}}`, `{{checkout_date}}` | Fix list Wave 1 |
| D24 | Top 3 quick replies sugeridos en compose por keyword match en nombre (sin LLM extra call) | Cheap, fast |
| D25 | Drafts: blur + 2s debounce + `beforeunload`, banner "Borrador de hace 2h, ¿continuar?" al reabrir | Discussion v5 |
| D26 | Idioma: bot detecta + persiste `subscriber.detected_lang`, Kari ALWAYS responde ES, AirBnB traduce auto | Discussion v5 |
| D27 | Auto-pause bot 1h post-reply manual (`bot_paused_until = now + 1h`). Si Kari hace pause manual con toggle → respetar duración manual indefinida (no auto-resume) | Discussion v5 |
| D28 | Auto-mark responded al enviar (no botón Replied separado para caso common path) | Discussion v5 |
| D29 | Audit trail solo en conversation view (no global). Trail muestra: `sent_by: karina | alex | bot`, timestamp, canal, external msg ID | Discussion v5 |
| D30 | Mobile compose full-screen al tap Reply, después back → vuelve al inbox | Discussion v5 |
| D31 | Pet fee canónico: `$300 MXN por mascota por estancia` (NO `/noche`), máx 2/booking — todos los textos LLM y quick replies validan esta forma | Memoria canónica |
| D32 | Casa Chamán excluida del filter properties + LLM suggestion knowledge | Renovation Q3 2026, NO surface to Kari ni guests |

---

## 4. Implementation

### 4.1 Territory split (HARD boundary, multi-CC parallel)

**CC-A Frontend (apps/web only):**

```
apps/web/src/
├── pages/admin/
│   ├── inbox.astro                          [REWRITE, NO new file]
│   ├── conversation/
│   │   └── [id].astro                       [NEW]
│   └── quick-replies/
│       ├── index.astro                      [NEW]
│       └── [id].astro                       [NEW edit page]
├── components/
│   ├── inbox/
│   │   ├── InboxTabs.tsx                    [NEW]
│   │   ├── InboxRow.tsx                     [NEW]
│   │   ├── ReadinessScore.tsx               [NEW responsive component]
│   │   ├── LifecycleSection.tsx             [NEW collapsible header]
│   │   ├── QuickStatsHeader.tsx             [NEW today/week stats]
│   │   └── InboxFilters.tsx                 [NEW property/etapa/idioma/canal]
│   ├── conversation/
│   │   ├── ConversationView.tsx             [NEW WhatsApp-style]
│   │   ├── MessageBubble.tsx                [NEW bot vs guest vs kari]
│   │   ├── ComposeBox.tsx                   [NEW with LLM + quick replies]
│   │   ├── LLMSuggestion.tsx                [NEW pre-loaded editable]
│   │   ├── QuickRepliesPanel.tsx            [NEW top 3 + see all]
│   │   ├── BookingContextSidebar.tsx        [NEW right sidebar]
│   │   └── AuditTrail.tsx                   [NEW timeline events]
│   └── quick-replies/
│       ├── QuickRepliesList.tsx             [NEW grid]
│       └── QuickReplyEditor.tsx             [NEW form + variables]
├── styles/
│   ├── inbox.css                            [NEW responsive breakpoints]
│   └── conversation.css                     [NEW WhatsApp-style]
└── lib/
    └── inbox-client.ts                      [NEW fetch helpers, no business logic]
```

**CC-B Backend (apps/worker-bot + packages/db + packages/agents):**

```
apps/worker-bot/src/
├── api/admin/
│   ├── inbox.ts                             [NEW GET endpoints]
│   ├── conversation.ts                      [NEW GET + POST endpoints]
│   ├── quick-replies.ts                     [NEW CRUD]
│   └── drafts.ts                            [NEW upsert + read]
└── inbox/
    ├── aggregate.ts                         [NEW threading 1 row/cliente]
    ├── readiness.ts                         [NEW 6-component score calc]
    ├── lifecycle.ts                         [NEW Reservas section categorization]
    ├── lead-intent.ts                       [NEW Tab Leads 3-bucket categorization]
    ├── filters.ts                           [NEW cron/placeholder/test/garbage filter]
    ├── llm-suggestion.ts                    [NEW Haiku wrapper, system prompt]
    ├── auto-pause.ts                        [NEW set bot_paused_until logic]
    └── lang-detect.ts                       [NEW detect_lang, persist subscriber]

packages/db/migrations/
├── 0032_inbox_drafts.sql                    [NEW]
├── 0033_quick_replies.sql                   [NEW]
└── 0034_inbox_indexes.sql                   [NEW indexes for threading queries]

packages/agents/src/prompts/
└── admin-suggest-reply.ts                   [NEW system prompt for Kari suggestion]
```

**Out-of-territory for either CC:** Si CC-A o CC-B necesita tocar archivos fuera de su territory, ABRE ISSUE en rdm-discussion (no inline fix). Excepciones permitidas:
- `apps/web/src/env.d.ts` (CC-B puede agregar env vars si needed)
- `wrangler.toml` (CC-B puede agregar bindings con descriptive commit)

### 4.2 API contracts (frozen, both CC respect, NO renegotiation mid-run)

#### 4.2.1 `GET /api/admin/inbox`

```typescript
// Query params
type InboxQuery = {
  tab: 'reservas' | 'leads'
  property?: string  // roomId filter
  etapa?: string     // lifecycle stage filter
  idioma?: 'es' | 'en' | 'de'
  unanswered_h?: number  // sin respuesta > N horas
  channel?: 'whatsapp' | 'airbnb' | 'booking'
}

// Response
type InboxResponse = {
  ok: true
  tab: 'reservas' | 'leads'
  counters: { reservas: number, leads: number }
  quick_stats: {
    today_checkins: number
    today_checkouts: number
    today_instay: number
    week_arrivals: number
    week_readiness_avg: number  // 0-6
    pending_critical: number
    pending_leads_hot_warm: number
  }
  sections: Section[]  // see below
}

type Section = {
  id: string          // e.g. "in_stay_issue", "needs_human"
  label: string       // human-friendly header
  color: string       // tailwind color hint
  count: number
  rows: InboxRow[]
}

type InboxRow = {
  id: string                        // canonical row id (per cliente/lead)
  subscriber_id: string             // primary phone or AirBnB user
  guest_name: string                // real name OR phone parcial fallback
  display_name_was_garbage: boolean // flag for tooltip
  property: { roomId: number, name: string } | null
  pax: number | null
  has_pet: boolean
  channels: ('whatsapp' | 'airbnb' | 'booking')[]
  preview: string                   // last msg, truncated 100 chars
  last_msg_at: string               // ISO
  hours_since_last_response: number // since Kari/bot replied
  unread_count: number              // badge "N nuevos"
  lifecycle_stage: LifecycleStage
  days_to_checkin: number | null    // negative = post-stay
  readiness: ReadinessScore | null  // null if not pre-stay
  priority_score: number            // computed, for ordering
  detected_lang: 'es' | 'en' | 'de' | null
  is_test_number: boolean           // 5217441441575
  // for Tab Leads only
  escalation_reason: string | null  // "pidió asesor", "frustración", "fecha sin dispo"
  bot_paused_until: string | null   // ISO if paused
}

type LifecycleStage =
  | 'in_stay_issue' | 'in_stay_ok'
  | 'pre_stay_imminent'   // T-2 a T-0
  | 'pre_stay_active'     // T-3 a T-14
  | 'pre_stay_distant'    // T-15+
  | 'airbnb_inquiry_unconfirmed'
  | 'post_stay'
  | 'vip_repeat'
  // Tab Leads
  | 'lead_needs_human' | 'lead_bot_failed' | 'lead_cold'

type ReadinessScore = {
  pax_confirmed: boolean
  pet_decided: boolean
  menu_decided: boolean
  eta_known: boolean
  rules_accepted: boolean
  paid: boolean
  score: number  // 0-6
}
```

#### 4.2.2 `GET /api/admin/conversation/[id]`

```typescript
type ConversationResponse = {
  ok: true
  conversation: {
    id: string
    subscriber: { id: string, name: string, phone: string, detected_lang: string }
    channels: string[]
    bot_paused_until: string | null
    messages: Message[]  // ordered ASC by sent_at
  }
  booking: BookingContext | null
  audit_trail: AuditEvent[]
}

type Message = {
  id: string
  channel: 'whatsapp' | 'airbnb' | 'booking'
  direction: 'inbound' | 'outbound'
  sent_by: 'guest' | 'bot' | 'karina' | 'alex'
  text: string
  sent_at: string  // ISO
  external_id: string | null
}

type BookingContext = {
  beds24_booking_id: number
  property: { roomId: number, name: string }
  check_in: string
  check_out: string
  pax: number
  has_pet: boolean
  services: string[]  // ["cocinera", "limpieza extra"]
  readiness: ReadinessScore
  total_amount_mxn: number
  paid_amount_mxn: number
  channel: string
}

type AuditEvent = {
  at: string
  actor: 'guest' | 'bot' | 'karina' | 'alex' | 'system'
  action: 'message_sent' | 'message_received' | 'bot_paused' | 'bot_resumed'
         | 'snoozed' | 'resolved' | 'marked_vip' | 'note_added'
  detail: string
}
```

#### 4.2.3 `POST /api/admin/conversation/[id]/reply`

```typescript
type ReplyRequest = {
  channel: 'whatsapp' | 'airbnb' | 'booking'  // resolved from booking, not user-selected
  text: string
  used_suggestion: boolean    // analytics: did Kari use LLM suggestion?
  used_quick_reply_id: string | null
}

type ReplyResponse = {
  ok: true
  message_id: string
  external_id: string
  bot_paused_until: string  // auto-pause 1h set
  auto_marked_responded: true
}
```

#### 4.2.4 `POST /api/admin/conversation/[id]/suggest-reply`

```typescript
type SuggestRequest = {
  // empty body, all inputs derived server-side
}

type SuggestResponse = {
  ok: true
  suggestion: string         // editable draft text
  inputs_used: {
    history_msgs: number
    booking_loaded: boolean
    readiness_loaded: boolean
    kb_docs_loaded: number
    karina_training_examples: number
  }
  cost_usd: number           // logging
  cached: boolean            // Haiku prompt caching hit?
} | {
  ok: false
  skip_reason: 'trivial' | 'cron' | 'cold_7d' | 'rate_limit'
}
```

#### 4.2.5 `POST /api/admin/conversation/[id]/pause-bot`

```typescript
type PauseRequest = {
  until: string | 'indefinite'  // ISO or sentinel
  reason: 'manual_kari' | 'auto_post_reply' | 'manual_alex'
}

type PauseResponse = {
  ok: true
  bot_paused_until: string | null
}
```

#### 4.2.6 `POST /api/admin/conversation/[id]/snooze`

```typescript
type SnoozeRequest = { hours: number }
type SnoozeResponse = { ok: true, reappears_at: string }
```

#### 4.2.7 `POST /api/admin/conversation/[id]/resolve`

```typescript
// idempotent; reopens if guest sends new msg
type ResolveResponse = { ok: true, resolved_at: string }
```

#### 4.2.8 `GET / POST / PUT / DELETE /api/admin/quick-replies`

```typescript
// GET → list
type QuickRepliesResponse = {
  ok: true
  items: QuickReply[]
}

type QuickReply = {
  id: string
  emoji: string             // single emoji, e.g. "🐕"
  name: string              // "Pet policy"
  category: 'reglas' | 'servicios' | 'logistica' | 'precios' | 'eventos' | 'otros'
  text: string              // with {{variables}}
  available_channels: ('whatsapp' | 'airbnb' | 'booking')[]
  usage_count: number
  last_used_at: string | null
  created_at: string
  updated_at: string
}

// POST / PUT body
type QuickReplyMutate = Omit<QuickReply, 'id' | 'usage_count' | 'last_used_at' | 'created_at' | 'updated_at'>
```

#### 4.2.9 `POST /api/admin/conversation/[id]/draft`

```typescript
type DraftRequest = { text: string }
type DraftResponse = { ok: true, saved_at: string }
// GET on same path returns latest draft for current user
```

### 4.3 D1 schema (migrations)

#### 4.3.1 `0032_inbox_drafts.sql`

```sql
-- Drafts persistentes por conversation + user
CREATE TABLE inbox_drafts (
  id TEXT PRIMARY KEY,                  -- format: "{conv_id}:{user_email}"
  conv_id TEXT NOT NULL,
  user_email TEXT NOT NULL,
  text TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_inbox_drafts_conv ON inbox_drafts(conv_id);
CREATE INDEX idx_inbox_drafts_updated ON inbox_drafts(updated_at DESC);
```

#### 4.3.2 `0033_quick_replies.sql`

```sql
CREATE TABLE quick_replies (
  id TEXT PRIMARY KEY,
  emoji TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('reglas','servicios','logistica','precios','eventos','otros')),
  text TEXT NOT NULL,
  available_channels TEXT NOT NULL,    -- JSON array
  usage_count INTEGER NOT NULL DEFAULT 0,
  last_used_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_by TEXT NOT NULL              -- email
);

CREATE INDEX idx_quick_replies_category ON quick_replies(category);
CREATE INDEX idx_quick_replies_usage ON quick_replies(usage_count DESC);
```

#### 4.3.3 `0034_inbox_indexes.sql`

```sql
-- Indexes para queries threading + lifecycle
-- (verify existence before CREATE, use IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_conversations_subscriber_lastmsg
  ON conversations(subscriber_id, last_active DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conv_sent
  ON messages(conv_id, sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_beds24_bookings_checkin
  ON beds24_bookings(check_in);

-- Subscriber-level columns (may not exist; CC-B verify before ALTER)
-- Anti-pattern: ALTER TABLE during multi-agent run
-- Solution: SELECT pragma_table_info('subscribers') and create new cols ONLY if missing
-- If missing, CREATE separate migration 0035_subscriber_lang.sql for ALTER
```

**Note CC-B:** `ALTER TABLE` durante multi-agent run es anti-pattern (mem rule). Si subscribers necesita columna `detected_lang`, hacer en migration aparte (0035) y aplicarla pre-merge en off-window, no durante CC paralelo.

### 4.4 Algoritmos críticos

#### 4.4.1 Threading aggregation (CC-B `inbox/aggregate.ts`)

```typescript
// Pseudocode
function aggregateInbox(tab: Tab, filters: Filters): InboxRow[] {
  // 1. Pull all conversations matching tab + filters
  //    Tab Reservas: WHERE beds24_booking_id IS NOT NULL
  //                  OR (airbnb_inquiry AND NOT confirmed)
  //    Tab Leads: WHERE beds24_booking_id IS NULL AND NOT airbnb_inquiry
  // 2. Group by subscriber_id (cross-channel: phone OR airbnb_user_id matched)
  // 3. For each group:
  //    - Pick representative (most recent active conv)
  //    - Aggregate unread_count = sum across channels
  //    - Aggregate preview = last msg across channels
  //    - Merge channels[] = unique
  //    - Compute lifecycle_stage (see 4.4.2)
  //    - Compute readiness (see 4.4.3)
  //    - Compute priority_score = lifecycle_priority + (days_to_checkin × (6 - readiness))
  // 4. Filter out cron/placeholder/garbage (see 4.4.4)
  // 5. Sort by priority_score DESC, then last_msg_at DESC
  // 6. Group into sections per lifecycle_stage
}
```

#### 4.4.2 Lifecycle categorization

```typescript
function categorizeLifecycle(row: RawRow, now: Date): LifecycleStage {
  if (!row.booking) {
    // Tab Leads
    if (row.escalation_reason?.match(/asesor|frustración|handoff/)) return 'lead_needs_human'
    if (row.escalation_reason?.match(/sin disponibilidad|edge case|loop/)) return 'lead_bot_failed'
    if (hoursSince(row.last_msg_at) > 24) return 'lead_cold'
    return 'lead_bot_failed'  // default catch-all if escalated
  }
  // Tab Reservas
  const days = daysBetween(now, row.booking.check_in)
  const inStay = now >= row.booking.check_in && now <= row.booking.check_out
  if (inStay) {
    return row.has_critical_keyword ? 'in_stay_issue' : 'in_stay_ok'
  }
  if (days < 0) {
    return Math.abs(days) <= 7 ? 'post_stay' : 'vip_repeat_check'
  }
  if (row.is_airbnb_inquiry_unconfirmed) return 'airbnb_inquiry_unconfirmed'
  if (days <= 2) return 'pre_stay_imminent'
  if (days <= 14) return 'pre_stay_active'
  return 'pre_stay_distant'
}
```

#### 4.4.3 Readiness score (CC-B `inbox/readiness.ts`)

```typescript
function computeReadiness(booking: Beds24Booking, conv: Conversation): ReadinessScore {
  return {
    pax_confirmed: booking.notes?.match(/pax final|N personas confirmadas/) != null
                || booking.pax === booking.notes_extracted_pax,
    pet_decided: booking.has_pet !== null  // ternary: true, false, or null=undecided
                || conv.messages.some(m => /mascota|perro|gato|sin pet/i.test(m.text)),
    menu_decided: conv.messages.some(m => /menu|cocinera celene|sin cocina/i.test(m.text))
                || booking.services.includes('cocinera_confirmed'),
    eta_known: conv.messages.some(m =>
                  /llegamos|llegando|hora|pm|am|tarde|noche/i.test(m.text)
                  && messageWasAfter(m, booking.check_in - 2*DAY)),
    rules_accepted: booking.rules_form_submitted_at != null,
    paid: booking.paid_amount_mxn >= booking.total_amount_mxn,
  } as Partial<ReadinessScore> & { score: number }
  // compute score = count of true booleans
}
```

CC-B may refine the heuristics; what matters is the contract (6 booleans + score 0-6) and consistent persistence (cache in `beds24_bookings.readiness_cached` updated on each conversation change OR computed live with budget <50ms).

#### 4.4.4 Filters (CC-B `inbox/filters.ts`)

```typescript
function shouldFilterOut(row: RawRow): { filter: boolean, reason?: string } {
  // Cron alerts
  if (row.subscriber_id === 'cron-bot-alerts') return { filter: true, reason: 'cron' }
  if (row.last_msg_text?.startsWith('cron_alert:')) return { filter: true, reason: 'cron' }
  // Placeholder bug
  if (row.last_msg_text?.includes('{{first_name}}')) {
    logBugToErrors(row)
    return { filter: true, reason: 'placeholder_bug' }
  }
  return { filter: false }
}

function normalizeDisplayName(raw: string, phone: string): { name: string, was_garbage: boolean } {
  const trimmed = raw.trim()
  // Heuristic garbage: 1-2 chars, only emojis, lone quote/period
  const isGarbage = trimmed.length <= 2
                 || /^[\p{Emoji}\s]+$/u.test(trimmed)
                 || /^["'.…]+$/.test(trimmed)
  if (isGarbage) {
    return { name: `...${phone.slice(-7)}`, was_garbage: true }
  }
  return { name: trimmed, was_garbage: false }
}
```

#### 4.4.5 LLM suggestion (CC-B `inbox/llm-suggestion.ts`)

```typescript
async function suggestReply(convId: string, env: Env): Promise<SuggestResponse> {
  const conv = await loadConversation(convId, { lastMsgs: 20 })
  const booking = await loadBooking(conv.subscriber_id)
  const readiness = booking ? computeReadiness(booking, conv) : null
  const lastGuestMsg = conv.messages.findLast(m => m.direction === 'inbound')

  // Skip rules
  if (isTrivial(lastGuestMsg.text)) return { ok: false, skip_reason: 'trivial' }
  if (conv.subscriber_id === 'cron-bot-alerts') return { ok: false, skip_reason: 'cron' }
  if (hoursSince(lastGuestMsg.sent_at) > 7 * 24) return { ok: false, skip_reason: 'cold_7d' }

  const kbDocs = await searchKB(env.R2_KNOWLEDGE, lastGuestMsg.text, { topK: 3 })
  const trainingExamples = await loadKarinaTrainingExamples(lastGuestMsg.text, env.DB, { topK: 3 })

  const systemPrompt = buildAdminSuggestPrompt({
    booking, readiness, kbDocs, trainingExamples, petPolicy: PET_POLICY_CANONICAL,
  })

  const response = await callHaiku45(env.ANTHROPIC_API_KEY, {
    system: systemPrompt,
    messages: conv.messages.map(toAnthropicFormat),
    cache_control: { type: 'ephemeral' }  // prompt caching
  })

  return { ok: true, suggestion: response.text, inputs_used: {...}, cost_usd: ..., cached: ... }
}
```

System prompt template (admin-suggest-reply.ts):

```
Eres un asistente que ayuda a Karina, encargada de operaciones de Rincón del Mar (RdM),
a responder mensajes de huéspedes y leads.

Tu salida es un BORRADOR editable para Karina, NO es la respuesta final ni se envía sola.
Karina la revisará, ajustará y enviará.

CONTEXTO:
- Negocio: 5 propiedades vacacionales en Pie de la Cuesta, Acapulco
- Propiedades activas: Rincón del Mar, Las Morenas, Huerta Cocotera, Combinada
- Política mascotas: $300 MXN por mascota por estancia (NO por noche), máx 2 por reserva
- Idioma: SIEMPRE responde en español. AirBnB traducirá automáticamente si el huésped es de otro idioma
- Check-in 3pm. Antes de 3pm solo en excepciones acordadas

BOOKING ACTUAL: {booking_summary}
READINESS SCORE: {readiness_summary}
KARINA TRAINING EXAMPLES: {training_examples}
KB DOCS RELEVANTES: {kb_docs}

INSTRUCCIONES:
- Borrador conciso, tono amable y profesional como Karina
- Si falta info en readiness, sugiere qué preguntar al guest
- NUNCA prometas algo fuera de la política (precios extra, descuentos, fechas no disponibles)
- Si no estás seguro, di "Karina te confirma esto pronto" en lugar de inventar
- NO incluyas saludos genéricos si la conversación ya está en curso
```

#### 4.4.6 Auto-pause bot (CC-B `inbox/auto-pause.ts`)

```typescript
async function autoPause(convId: string, reason: PauseReason, env: Env) {
  const conv = await loadConversation(convId)
  if (reason === 'auto_post_reply') {
    // Check if already manually paused with longer/indefinite duration
    if (conv.bot_paused_until === null || conv.bot_paused_until === 'indefinite') return  // respect manual
    const manualEnd = conv.bot_paused_until ? new Date(conv.bot_paused_until) : null
    const newEnd = new Date(Date.now() + 60 * 60 * 1000)
    if (manualEnd && manualEnd > newEnd) return  // manual is longer, keep
    await db.execute(`UPDATE conversations SET bot_paused_until = ? WHERE id = ?`, [newEnd.toISOString(), convId])
  } else if (reason === 'manual_kari') {
    // Manual = indefinite by default unless explicit duration
    await db.execute(`UPDATE conversations SET bot_paused_until = NULL, manual_pause = 1 WHERE id = ?`, [convId])
  }
}
```

#### 4.4.7 Test number CSS (CC-A inbox.css)

```css
.inbox-row[data-test="true"] {
  background: linear-gradient(90deg, transparent 0%, #ebe8ff 100%);
  border-left: 3px solid #8b7ec8;
}
.inbox-row[data-test="true"]::after {
  content: "🧪 owner test";
  font-size: 0.65em;
  color: #8b7ec8;
  position: absolute;
  right: 8px;
  top: 4px;
  opacity: 0.7;
}
```

### 4.5 Responsive breakpoints

| Breakpoint | Width | Inbox row | ReadinessScore | ComposeBox |
|---|---|---|---|---|
| Desktop | ≥1024px | Multi-line, pills inline | Pills (6 individual) | Inline drawer |
| Tablet | 768-1023px | Compact, score + tooltip | Score num + hover detail | Inline drawer narrower |
| Mobile | <768px | Single-line + expand `▼` | Score + barra in row, pills in expand | **Full-screen modal** at tap Reply |

---

## 5. Tests

### 5.1 CC-A frontend tests (vitest + happy-dom)

| Component | Tests minimum |
|---|---|
| `InboxTabs` | Counter render, active tab class, click switches tab |
| `InboxRow` | Renders name/property/preview, garbage name fallback, badge unread count, lifecycle color |
| `ReadinessScore` | Renders 6 pills desktop, score+barra mobile (matchMedia mock), tooltip tablet |
| `LifecycleSection` | Collapsible, count badge, sort within section |
| `ConversationView` | Bubbles direction, timestamps relative, bot vs human visual distinction |
| `ComposeBox` | Textarea + send, disabled when empty, channel hidden (auto-resolved), auto-save draft on blur |
| `LLMSuggestion` | Renders suggestion, "Usar" copies to compose, "Regenerar" calls endpoint, "Skip" hides |
| `QuickRepliesPanel` | Top 3 sugeridos render, click inserts text with variable interpolation |
| `BookingContextSidebar` | Renders booking fields, readiness component, hide sidebar mobile |
| `AuditTrail` | Renders events chronological, actor color-coded |
| `QuickRepliesList` | CRUD operations, filter by category |
| `QuickReplyEditor` | Form validates required, variable picker insert at cursor |

Target: minimum **80 tests passing** for CC-A scope.

### 5.2 CC-B backend tests (vitest)

| Module | Tests minimum |
|---|---|
| `aggregate.ts` | Threading dedupes 5 Sandy msgs to 1 row, cross-channel merge WA+AirBnB same phone, unread count correct |
| `readiness.ts` | All 6 components compute correctly on fixture bookings (full 6/6, partial 3/6, fresh 0/6) |
| `lifecycle.ts` | Categorize covers all 11 stages (8 Reservas + 3 Leads) |
| `filters.ts` | Cron alerts filtered, placeholder filtered + logged, garbage names → phone parcial |
| `llm-suggestion.ts` | Skip rules (trivial, cron, cold_7d), inputs assembled correctly, response shape valid, cost logged |
| `auto-pause.ts` | Manual pause respected, 1h auto on reply, no override of longer manual |
| `quick-replies CRUD` | Create/read/update/delete, usage_count increments, variable interpolation correct |
| `drafts` | Upsert by `{conv_id}:{user}`, latest version wins |
| `API inbox` | Query params parsed, response shape valid, counters match |
| `API conversation` | Returns conv + booking + audit_trail, paginates messages |
| `API reply` | Routes WA via MakeMsg, AirBnB via Beds24, marks responded, sets bot_paused_until |

Target: minimum **60 tests passing** for CC-B scope.

### 5.3 Integration tests (Alex executes manually post-merge)

Smoke test checklist en thread/196 §6 (Definition of Done).

---

## 6. Definition of Done (checkable)

CC-A:

- [ ] `/admin/inbox` muestra 2 tabs con counters live
- [ ] Tab Reservas muestra 8 secciones lifecycle correctas (con datos reales D1)
- [ ] Tab Leads muestra 3 secciones intent correctas
- [ ] 1 row por cliente (verificar Sandy 5 msgs → 1 row badge "5 nuevos")
- [ ] Readiness pills desktop, score mobile, tooltip tablet (test 3 viewports manualmente)
- [ ] Test number `5217441441575` muestra CSS tenue lavanda
- [ ] Cron alerts NO aparecen en inbox
- [ ] `{{first_name}}` rows NO aparecen
- [ ] Display name basura muestra phone parcial
- [ ] `/admin/conversation/[id]` renderiza WhatsApp-style con bubbles
- [ ] Compose box muestra LLM suggestion editable
- [ ] Quick replies top 3 sugeridos aparecen en compose
- [ ] `/admin/quick-replies` permite CRUD completo
- [ ] Variables `{{guest_name}}` etc se interpolan en preview editor
- [ ] Mobile (<768px) compose abre full-screen al tap Reply
- [ ] Booking context sidebar visible desktop, oculto mobile
- [ ] Drafts persisten (test: escribir, refresh, banner aparece)
- [ ] Audit trail visible solo en conversation view
- [ ] Quick stats header muestra today/week stats
- [ ] Filters property/etapa/idioma/canal funcionan

CC-B:

- [ ] Migration `0032_inbox_drafts.sql` applied
- [ ] Migration `0033_quick_replies.sql` applied
- [ ] Migration `0034_inbox_indexes.sql` applied (skip if exists)
- [ ] `GET /api/admin/inbox?tab=reservas` retorna response con shape correcto
- [ ] `GET /api/admin/inbox?tab=leads` retorna response correcto
- [ ] `GET /api/admin/conversation/[id]` retorna conv + booking + audit
- [ ] `POST /api/admin/conversation/[id]/reply` envía via WA (MakeMsg) o AirBnB (Beds24) según booking.channel
- [ ] Reply auto-pausa bot 1h
- [ ] Reply auto-marca responded
- [ ] `POST /api/admin/conversation/[id]/suggest-reply` retorna Haiku suggestion <2s p95
- [ ] Skip rules suggest-reply funcionan (trivial, cron, cold_7d)
- [ ] `POST /api/admin/conversation/[id]/pause-bot` respeta manual vs auto
- [ ] `POST /api/admin/conversation/[id]/snooze` reaparece en N horas
- [ ] `POST /api/admin/conversation/[id]/resolve` idempotente
- [ ] CRUD `/api/admin/quick-replies` completo
- [ ] Drafts upsert + read funcionan
- [ ] Cron alerts filtrados del aggregate
- [ ] Test number visible (no filtrado, solo flagged `is_test_number`)
- [ ] Display name garbage normalizado a phone parcial
- [ ] Lang detection persiste a `subscribers.detected_lang` (si col existe, sino skip y reportar)
- [ ] LLM cost logged a `bot_metrics` o tabla equivalente

Alex smoke test (post-merge, 30 min):

- [ ] Login admin → `/admin/inbox` carga <2s
- [ ] Counter Reservas/Leads matches gut estimate
- [ ] Open Carlos (T-3 cumpleaños) → ver readiness ~2/6, conversation view OK
- [ ] LLM suggestion aparece y se ve coherente
- [ ] Click Quick reply "Pet policy" inserta texto correcto
- [ ] Reply test en una conv test → llega a WA/AirBnB
- [ ] Verificar bot_paused_until = +1h después de reply
- [ ] Verificar audit trail tracking
- [ ] Move to mobile → compose abre full-screen
- [ ] Verificar test number Alex aparece con tinte lavanda
- [ ] Crear quick reply nueva → aparece en compose

---

## 7. Risks + mitigations

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | CC-A y CC-B scope overlap (e.g. cross territory edit) | Media | Alto (merge conflicts) | Hard boundary §4.1, judge-ops vigila |
| R2 | Threading aggregation tiene edge cases (3 channels mismo phone, antiguos sin subscriber match) | Alta | Medio (rows duplicados) | Tests fixtures explícitos §5.2, ship 80% accuracy, refinar |
| R3 | LLM suggestion costos overrun (>$10/día imprevisto) | Baja | Bajo | Skip rules § 4.4.5, cost log, kill switch env var `LLM_SUGGESTIONS_ENABLED` |
| R4 | Beds24 reply API rate limit hit | Baja | Medio (Kari frustration) | Retry exponential, surface error a UI claramente |
| R5 | Migration 0034 indexes lentos en D1 con datos producción | Media | Bajo | `IF NOT EXISTS`, run en off-window, verificar query plan |
| R6 | ALTER TABLE conflicto multi-CC | Alta si se hace | Alto | ZERO ALTER en migrations Wave 1, postpone subscriber.detected_lang col a Wave 1.5 si needed |
| R7 | Drafts collision usuario navega entre conversations rápido | Baja | Bajo | Upsert by `{conv_id}:{user}`, last-write-wins |
| R8 | Karina abruma con LLM suggestions equivocadas | Media | Medio | "Skip" botón visible, kill switch, training examples calibrate |
| R9 | Quick replies sin variables → texto pegado tal cual | Baja | Bajo | UI editor valida variables sintácticas |
| R10 | Test number Alex aparece raro a Karina | Baja | Bajo | CSS tenue, "🧪 owner test" badge, Alex puede explicar |
| R11 | Conversation timeline > 200 msgs lenta carga | Baja | Bajo | Paginate lastMsgs=50 default, "Load more" UI |
| R12 | Mobile full-screen compose se siente disruptive | Baja | Bajo | Standard pattern (WhatsApp), back button vuelve al inbox |
| R13 | Lifecycle categorization clasifica mal in_stay_issue (false positive) | Media | Medio | Keywords list mantenible, Kari override manual con "Mark resolved" |
| R14 | Audit trail growing unbounded | Baja | Bajo | Solo se renderiza per-conv, paginate si >50 events |
| R15 | Casa Chamán surfaces accidentally | Baja | Alto | Filter properties WHERE roomId != 679176, test fixture asegura |
| R16 | Idioma detection wrong → guest recibe respuesta en EN cuando Kari escribe ES (vía AirBnB) | Baja | Bajo | AirBnB traduce a target lang del guest, Kari escribe ES, no nuestro problema |

---

## 8. Multi-CC orchestration

### 8.1 Sync gates

| Gate | When | Required artifact | Blocker if missing |
|---|---|---|---|
| G1: Contracts frozen | First 60 min | Both CC review §4.2, raise ANY ambiguity via comment thread/196 | Don't proceed implementation |
| G2: Backend endpoints deployed to preview | CC-B ~6h in | wrangler dev or CF preview URL alive responding 200 to all endpoints in §4.2 | CC-A can't integrate |
| G3: Integration handshake | Both CC ~70% in | CC-A wires real endpoints (replaces mocks), at least 1 happy-path flow E2E | Required for Alex smoke |

### 8.2 Communication channels

- **rdm-discussion PR comments** = ground truth, async durable
- **`threads/196-cc-status.md`** (CC may create) = running log, optional
- **Telegram alerts** (Logpush via worker-pago) = ops-only, NO product discussion
- **Out-of-scope finds** → open issue, comment in PR, NO inline fix
- **Spec ambiguities** → comment in PR thread/196, WC will adjudicate ASAP

### 8.3 Branches

```
main
├── feat/inbox-redesign-spec       # this thread, WC initiated
├── feat/inbox-frontend            # CC-A branch
└── feat/inbox-backend             # CC-B branch
```

CC-A and CC-B keep their own branches, rebase on main as needed. Final integration via:

- CC-B PR first → merge to main
- CC-A rebase on main → integrate against deployed endpoints → PR → merge

### 8.4 Commit conventions

`feat/fix/chore(scope): description` (mem rule). Squash merge each PR.

CC-A scope: `feat(admin-web): ...`
CC-B scope: `feat(worker-bot): ...` or `feat(db): ...` for migrations

---

## 9. Judge protocol

### 9.1 Judge-Ops (anti-pattern + execution correctness)

| Check | Anti-pattern flagged |
|---|---|
| CC-A touched files outside `apps/web/` | Boundary violation §4.1 |
| CC-B touched files outside `apps/worker-bot/`, `packages/db/migrations/`, `packages/agents/` | Boundary violation §4.1 |
| ALTER TABLE in any migration | Mem hard anti-pattern |
| Pet fee written as `/noche` anywhere | Mem hard anti-pattern |
| Casa Chamán surfaced in any UI text or LLM context | Mem hard anti-pattern |
| Beds24 sync mode changes anywhere | Out of scope + mem hard anti-pattern |
| Plaintext secrets in commits | Mem hard anti-pattern |
| "Tests pass" claim without self-review of diff | Mem hard anti-pattern |
| Windows path hardcoded | Mem hard anti-pattern |
| "Alexa" instead of "Alex" | Mem hard anti-pattern |
| Friday after 5pm deploy | Mem hard anti-pattern (today is Saturday so OK) |
| Out-of-scope find fixed inline instead of issue opened | Mem rule violation |
| LLM cost not declared if expected >$10 | Mem cost discipline |
| Subagent context not reset between unrelated tasks | Subagent best practice |

### 9.2 Judge-Strat (product fit + UX)

| Check | Question |
|---|---|
| Lifecycle stages cover all real RdM cases | Walk through 5 real bookings from `/admin/bookings`, do all map cleanly? |
| Readiness score components accurate | Test fixtures match Alex's mental model? |
| Karina mobile workflow viable | Can Karina respond from phone in <2 min? |
| Test number Alex not disruptive to Karina | Subjective: does it pull her attention? |
| LLM suggestion tone matches RdM voice | Sample 5 suggestions, do they sound like Karina would write? |
| Quick replies categories cover real ops needs | Reglas/Servicios/Logística/Precios/Eventos/Otros enough? |
| Filter sensible defaults | Default view shouldn't be empty nor overwhelming |
| Casa Chamán hidden everywhere | Search codebase for 679176, only allowed in exclusion logic |
| Pet policy text canonical everywhere | `$300 MXN/mascota/estancia`, NEVER `/noche` |

### 9.3 Judge output format

Each judge writes comment on the CC's PR with:

```
## Judge-Ops review

✅ Pass: [items]
❌ Block: [items, must fix before merge]
⚠️ Warn: [items, can ship but note]
```

Alex merges only after both judges = no ❌.

---

## 10. Estimated effort breakdown

| Workstream | Hours CC | Hours wall (parallel) |
|---|---|---|
| CC-A frontend scaffold + InboxRow/Tabs/Sections | 6h | |
| CC-A ReadinessScore responsive + CSS | 3h | |
| CC-A ConversationView WhatsApp-style | 6h | |
| CC-A ComposeBox + LLM + Quick replies wiring | 4h | |
| CC-A `/admin/quick-replies` CRUD UI | 4h | |
| CC-A drafts wiring + mobile compose | 2h | |
| CC-A tests | 3h | |
| **CC-A total** | **~28h** | ~1 día concurrent |
| CC-B migrations + indexes | 1h | |
| CC-B aggregate + threading | 4h | |
| CC-B readiness + lifecycle + filters | 3h | |
| CC-B LLM suggestion + prompt + skip rules | 3h | |
| CC-B reply routing (WA + AirBnB) | 2h | |
| CC-B quick replies + drafts CRUD | 3h | |
| CC-B auto-pause + auto-respond | 1h | |
| CC-B tests | 3h | |
| **CC-B total** | **~20h** | ~1 día concurrent |
| Integration + smoke + Judge reviews | 4h | |
| **Grand total** | **~52h CC** | **~2 días wall-clock concurrent** |

Note: estimates trend high. Recent thread/184 ran 98% under estimate (PR #166 in 4 min vs 1h budgeted). Trust the team.

---

## 11. Kickoff command (Alex executes)

After merge of this spec:

```bash
# 1. Launch CC-A (terminal 1)
cd ~/dev/rdm/rdm-bot
git checkout main && git pull
claude code --session inbox-frontend
# In CC: "Read threads/196-wc-inbox-redesign-spec.md. You are CC-A (frontend territory).
#         Execute §4.1 CC-A territory only. Sync gates §8.1. Commit conventions §8.4."

# 2. Launch CC-B (terminal 2)
cd ~/dev/rdm/rdm-bot
claude code --session inbox-backend
# In CC: "Read threads/196-wc-inbox-redesign-spec.md. You are CC-B (backend territory).
#         Execute §4.1 CC-B territory only. Sync gates §8.1. Commit conventions §8.4."

# 3. After CC-B PR opens, WC Judge-Ops + Judge-Strat review (Alex pings WC in chat)
# 4. After CC-A PR opens (post CC-B merge), same judge sweep
# 5. Alex merges both, runs smoke checklist §6
```

---

## 12. Closing

Esta spec absorbe 5 iteraciones de mockup + decisión cerrada con Alex en sesión brain deep. Todo lo que está aquí es scope; todo lo que NO está aquí es out of scope (judges enforce).

Si CC encuentra ambigüedad, **comenta en PR thread/196 antes de asumir**. WC adjudica.

Backlog AirBnB (bot activation + inquiry auto-response) capturado en thread/197 — NO scope este sprint.

Si Alex aprueba este spec, merge atómico y kickoff.

— WC, 2026-05-23
