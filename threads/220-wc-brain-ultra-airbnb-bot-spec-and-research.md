---
id: 220
author: wc
topic: airbnb-inquiry-bot-spec-and-customer-management-brain-ultra
status: ready-for-doit
mode: brain-ultra
created_at: 2026-05-27
updated_at: 2026-05-27
revision: 3
references:
  - threads/33-guest360-architecture-phase-b-plan.md
  - threads/35-cc-templates-system-for-wc.md
  - threads/89-cc-event-bus-spec.md
  - threads/107-cc-inquiries-auto-close.md
  - threads/110-112-messenger-outbound-feature.md
  - threads/196-inbox-redesign.md
  - threads/217-greeter-v7.1-mega-spec.md
  - knowledge/airbnb-templates-current-2026-05-13.json
  - knowledge/airbnb-listing-fields-current-2026-05-13.md
  - knowledge/airbnb-emoji-blocklist-2026-05-14.md
  - knowledge/whatsapp-kits-current-2026-05-13.md
prs_proposed: PR1 (inquiry-bot infra), PR2 (template + canary), PR3 (lifecycle activation)
estimated_effort: 24-32h CC + 4-6h Alex/Karina (templates) + canary 2-3 semanas
---

# thread/220 — Brain ultra: Airbnb Inquiry Bot + Customer Management

> **Status:** REV 3 — Ready for DoIt CC. Arquitectura cerrada post-feedback Alex.
>
> **Changelog:** REV 1 = brain ultra inicial. REV 2 = corrección precio. **REV 3 = arquitectura webhook+debounce+pause cerrada.**

---

## §0 · TL;DR ejecutivo

**El estado actual:** Beds24 recibe inquiries Airbnb perfectamente (90 en últimas semanas). El sistema D1 las almacena en `beds24_events`. **El bot las ve y NO hace nada** — guest queda esperando respuesta de Alex/Karina manual.

**70% de la infraestructura ya existe.** El gap real son ~12-16h CC para el orchestrator.

**Arquitectura cerrada (REV 3):**

1. **Bot único** con context switch por canal
2. **Webhook push + 5min debounce window** (reset on update si guest manda más msgs)
3. **Cron `*/5min` existente reutilizado** (NO agregar 5to cron)
4. **Human pause time-based 1h:** si Karina/Alex respondió, bot pausa. Si no hay más mensajes humanos en 1h, bot retoma
5. **PR1 → PR2 → PR3** en 4-6 semanas, canary scaling

**Costo:** 24-32h CC, <$5/mes Anthropic, riesgo bajo.

---

## §0.1 · 🔴 CORRECCIÓN REV 2 — `payload.booking.price` NO es lo que ve el guest

El `price` en payload Beds24 es **meta revenue NET** (lo que cobra Alex después de commission Airbnb + taxes guest paga). **NO** es el "Total" del botón Airbnb.

**Verificado con D1:**

| Tipo evento | `price` | `commission` | Interpretación |
|---|---|---|---|
| Inquiry Ana Karen | $28,789.02 | 0 | NET sin desglose |
| Booking confirmado | $6,117.84 | $948.27 | NET + commission separado |
| Lo que ve el guest | **NO viene** | — | Service fee + taxes locales NO en payload |

**Implicación:** bot NUNCA muestra número MXN. Lenguaje canónico: "la tarifa que ya viste en Airbnb...".

---

## §0.2 · 🟢 ARQUITECTURA CERRADA REV 3 — webhook + debounce + 1h pause

**Decisiones de Alex (2026-05-27):**

| # | Decisión | Valor | Razón |
|---|---|---|---|
| 1 | Trigger | **Webhook push + 5min debounce** | Industry standard (Hostaway, Hospitable, Uplisting). Captura 70% bursts (data D1) |
| 2 | Skip si host respondió | **Sí + audit** | Industry standard, evita doble respuesta |
| 3 | Human pause logic | **Time-based 1h** | "Si Karina/Alex respondió, bot pausa 1h. Si no hay más mensajes humanos en 1h, bot retoma normal." Pragmatic, simple, sin LLM extra call |
| 4 | Cron strategy | **Reutilizar `*/5min` existente** | NO agregar 5to cron. Unified worker pattern |
| 5 | Backup sweep | **Cada 3ra ejecución (`*/15min`)** | Defense in depth si webhook se pierde |

**Reasoning H2 1h pause vs H3 LLM re-eval:**
- Alex constraint: "Realmente no quiero que Kari y yo intervengan, serían excepciones por mensajes críticos"
- Por lo tanto: cuando hay intervención humana, es rara y específica
- H2 1h: simple, predecible, sin LLM extra call
- Si guest sigue conversación 1h+ después → bot retoma (asume host no estaba siguiendo)
- Si guest sigue conversación en <1h → respeta intervención activa de Karina

**Industry validation:** Uplisting docs textuales: "Some members prefer to delay up to 60 minutes to allow them to respond manually." Hospitable: "If you have a delay on your message, and you manually replied before the scheduled send time, we will not send it."

---

## §1 · Hallazgo principal — el último mile de Phase B.2

### Plan original B.2 (thread/33, mayo 12) → estado actual

El thread/33 detalló Phase B.2 con 16h CC estimadas. Lo que se construyó vs lo que falta:

| Sub-task del plan B.2 | Status |
|---|---|
| Migrations 0014-0017 (guests + leads + bookings + guest_events) | ✅ aplicadas |
| Lead ingestion handler | ⚠️ parcial — `bot_messages_inbox` recibe pero no crea leads automáticos |
| Auto-respond inquiry handler | 🔴 NO existe |
| Template R2 `inquiry-welcome-<roomId>.md` | 🔴 NO existe en R2 |
| AI question detection | ⚠️ existe `admin-suggest-reply.ts` (manual) |
| Auto follow-ups cron (T+3, T+7, T+14) | 🔴 NO existe |
| Pre-approval detection | 🔴 NO existe |

**Diagnóstico:** B.2 quedó "pausado a 70% completion". Falta solo el orchestrator.

---

## §2 · Discovery summary — la inquiry de Ana Karen como caso real

Booking ID 87381196, RoomId 78695 (RdM), 16 adultos, arrival 2026-08-21. Guest: "Ana Karen". `lang: 'en'` pero escribió ES.

**Precio:** `price: 28789.02` (net Alex). Total que ve el guest NO viene.

Mensaje guest: "Hola Alexander, estoy interesada en la renta de este lugar vi que ofrecen servicio de chef ¿el costo total incluye los víveres para la comida?"

**Alex respondió 2h después.** Industry data: <1h response = +25% conversion. Target post-PR2: <5 min.

### Lo que detecta el sistema actual

| Campo | Sistema sabe | Comentario |
|---|---|---|
| Es inquiry, no booking | ✅ | `status='inquiry'` |
| Villa específica | ✅ | `roomId=78695` → RdM |
| Tamaño grupo (16) | ✅ | Trigger `extra-guests` capture |
| Pregunta concreta del huésped | ⚠️ texto presente | NO parseado |
| Idioma real del huésped | ❌ | `lang='en'` mintió |
| **Precio que ve el guest** | ❌ | **NO viene en payload** |

---

## §3 · Spec del bot — PR1, PR2, PR3 (REV 3)

### §3.1 · PR1 — Infraestructura inquiry-response (REV 3 — arquitectura webhook + debounce + pause)

**Branch:** `feat/inquiry-bot-infra`
**Effort:** 10-14h CC (REV 3 +2h por debounce/pause logic)
**Risk:** muy bajo

#### Archivos a crear

```
apps/worker-bot/src/inquiry-response.ts            // Handler principal
apps/worker-bot/src/inquiry-enqueue.ts             // NEW REV 3 — webhook → PIR enqueue
apps/worker-bot/src/inquiry-templates.ts           // Template loader + composer
apps/worker-bot/src/inquiry-parser.ts              // Haiku question extraction
apps/worker-bot/src/inquiry-pause-check.ts         // NEW REV 3 — 1h pause logic
packages/agents/src/prompts/inquiry-question-parser.ts
migrations/0051_pending_inquiry_replies.sql
apps/web/src/pages/admin/inquiry-replies.astro     // Approval UI
apps/web/src/pages/api/admin/inquiry-replies/[id].ts
apps/worker-bot/tests/inquiry-response.test.ts
apps/worker-bot/tests/inquiry-parser.test.ts
apps/worker-bot/tests/inquiry-pause.test.ts        // NEW REV 3
```

#### Migration 0051 (REV 3 — schema actualizado)

```sql
CREATE TABLE pending_inquiry_replies (
  id TEXT PRIMARY KEY,                              -- ULID
  beds24_event_id INTEGER NOT NULL UNIQUE,          -- idempotency key
  beds24_booking_id INTEGER NOT NULL,
  room_id INTEGER NOT NULL,
  channel TEXT NOT NULL DEFAULT 'airbnb',

  -- Guest snapshot
  guest_first_name TEXT,
  guest_message_text TEXT NOT NULL,
  guest_message_lang_detected TEXT,
  arrival TEXT,
  departure TEXT,
  num_nights INTEGER,
  num_adults INTEGER,
  meta_revenue_net_mxn REAL,                        -- payload.booking.price (INTERNAL ONLY, never shown to guest)

  -- Question extraction (Haiku)
  question_detected INTEGER NOT NULL DEFAULT 0,
  question_topic TEXT,
  question_topics_list TEXT,                        -- JSON array si multiple
  question_extracted TEXT,
  question_confidence REAL,
  question_tone TEXT,
  red_flag TEXT,

  -- Composition
  template_r2_key TEXT,
  template_content_snapshot TEXT,
  message_1_text TEXT,
  message_2_text TEXT,

  -- LLM cost
  llm_model TEXT,
  llm_tokens_in INTEGER,
  llm_tokens_out INTEGER,
  llm_cache_hit INTEGER DEFAULT 0,
  llm_cost_usd REAL,

  -- REV 3: Debounce + pause architecture
  process_at INTEGER NOT NULL,                      -- unix timestamp when ready to process (NOW + 5min on insert)
  last_inbound_msg_at INTEGER NOT NULL,             -- last guest msg time, resets process_at +5min on each new guest msg
  bot_pause_until INTEGER,                          -- nullable. If set, bot will not send until this timestamp
  pause_reason TEXT,                                -- 'host_intervened' | 'manual_pause' | 'red_flag'

  -- Status lifecycle (REV 3 enum extended)
  status TEXT NOT NULL DEFAULT 'awaiting_processing' CHECK (status IN (
    'awaiting_processing',    -- webhook recibió, esperando debounce window
    'approval_pending',       -- Haiku ya procesó, esperando review humano (PR1) o canary auto-send (PR2)
    'approved',               -- approved for send, held in queue
    'sent',                   -- delivered
    'rejected',               -- explicit human rejection
    'expired',                -- 48h sin acción
    'auto_send_eligible',     -- canary % hit, will send sin approval
    'superseded_by_human',    -- host respondió primero, audit only
    'paused'                  -- waiting for bot_pause_until
  )),
  reviewed_by TEXT,
  reviewed_at INTEGER,
  rejection_reason TEXT,

  -- Send result
  sent_at INTEGER,
  send_attempts INTEGER NOT NULL DEFAULT 0,
  send_error_last TEXT,
  external_message_id_1 TEXT,
  external_message_id_2 TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX idx_pir_status ON pending_inquiry_replies(status, process_at);
CREATE INDEX idx_pir_room ON pending_inquiry_replies(room_id, status);
CREATE INDEX idx_pir_ready ON pending_inquiry_replies(process_at)
  WHERE status IN ('awaiting_processing', 'paused');
CREATE INDEX idx_pir_booking ON pending_inquiry_replies(beds24_booking_id, created_at);
```

#### Handler architecture (REV 3 — split en 3 funciones)

**Función 1: `enqueueInquiryReply(env, beds24Event)`** — llamada por webhook handler

```
1. Parse payload, extract booking + messages
2. Filter: only inquiry status + Airbnb referer + NOT Casa Chamán (679176)
3. Check if PIR exists for beds24_event_id:
   - NO existe → INSERT new PIR (process_at = NOW + 5min, status='awaiting_processing')
   - SÍ existe → UPDATE process_at = NOW + 5min, last_inbound_msg_at = NOW
                 (debounce reset: si guest manda otro msg, timer reinicia)
4. NO procesar acá. Solo enqueue.
```

**Función 2: `processReadyInquiries(env)`** — llamada por cron `*/5min` existente

```
1. SELECT PIR rows WHERE status='awaiting_processing' AND process_at <= NOW LIMIT 20
2. For each row:
   a. Check pause logic (función 3)
      - Si bot_pause_until > NOW → status='paused', skip
      - Si bot_pause_until <= NOW pero existe host msg en último 1h → status='paused', extend bot_pause_until
      - Si no hay host msg en último 1h → continuar processing
   b. Check if host respondió DESPUÉS del last_inbound_msg_at:
      - SÍ host_msg_time > last_inbound_msg_at → status='superseded_by_human', audit, skip send
      - NO → continuar
   c. Parse via Haiku
   d. Load template R2
   e. Compose 2 messages
   f. status='approval_pending' (PR1) o aplicar canary % (PR2)
   g. UPDATE PIR row con composition + LLM cost
3. Backup sweep cada 3ra ejecución (cron tick mod 3 == 0):
   - SELECT beds24_events WHERE status='inquiry' AND id NOT IN (SELECT beds24_event_id FROM pending_inquiry_replies)
   - For each missing → call enqueueInquiryReply
```

**Función 3: `checkHumanPause(env, pir)`** — lógica 1h pause time-based

```
1. SELECT bot_messages_inbox 
   WHERE booking_id = pir.beds24_booking_id 
     AND source = 'host' 
     AND message_time > pir.last_inbound_msg_at - 3600  -- ventana de búsqueda extendida
   ORDER BY message_time DESC LIMIT 1
   
2. Si NO existe host msg → no pause, retorna {paused: false}

3. Si existe host msg:
   - last_host_msg_at = found.message_time
   - elapsed_since_host = NOW - last_host_msg_at
   - Si elapsed_since_host < 3600 (1h) → 
       {paused: true, pause_until: last_host_msg_at + 3600, reason: 'host_intervened'}
   - Si elapsed_since_host >= 3600 (1h sin host activity) → 
       {paused: false, audit: 'human_intervention_expired'}
```

**Webhook integration point:**

El handler de Beds24 webhook (ya existente en código actual) debe llamar `enqueueInquiryReply` al recibir status='inquiry' events. Punto de integración: donde actualmente hace `action_taken='skipped_inquiry'`, ahora hace ese log + llama enqueue.

#### Cron schedule (REV 3 — sin agregar cron nuevo)

| Cron actual | Frecuencia | Handler nuevo dentro |
|---|---|---|
| `0 10 * * *` (daily) | 1×/día | (no cambio) |
| `*/5 * * * *` (polling) | Cada 5 min | **+ `processReadyInquiries()` cada tick** |
| `*/30 * * * *` (pre-stay scan) | Cada 30 min | (no cambio) |

**Backup sweep dentro de `*/5min`:** cada 3er tick (mod 3 == 0), también escanea `beds24_events` sin PIR row asociado. Worst case: 15 min hasta detectar webhook lost.

#### Inquiry question parser prompt (Haiku 4.5)

Output JSON: `lang` (es|en|other), `lang_confidence`, `topic` (chef|veveres|precio|mascotas|amenidades|ubicacion|capacidad|evento|fechas|transporte|actividades|ninguna|multiple), `topics_list`, `question_extracted`, `question_confidence`, `tone` (casual|formal|urgent|vip), `red_flag` (null|off_platform_attempt|negotiation_aggressive|complaint).

#### Decisiones cerradas PR1 (REV 3 actualizado)

| Decisión | Valor | Razón |
|---|---|---|
| Idempotencia | Por `beds24_event_id` UNIQUE | Beds24 webhook puede llegar 2x |
| **Trigger architecture** | **Webhook push + 5min debounce + cron processor** | Industry standard, captura 70% bursts |
| **Debounce reset** | **Cada nuevo guest msg resetea `process_at = NOW + 5min`** | Agrupa serie de mensajes |
| **Cron** | **Reutilizar `*/5min` existente** | NO agregar 5to cron |
| **Backup sweep** | **Cada 3er tick (`*/15min` efectivo)** | Defense in depth |
| **Human pause** | **Time-based 1h después de host msg** | Pragmatic, sin LLM extra |
| **Bot retoma** | **Si 1h sin host msg adicional → unpause** | Asume host no estaba siguiendo |
| Window de procesamiento | últimos 24h | Inquiries más viejas pierden valor |
| Estado inicial PR1 | `awaiting_processing` → `approval_pending` | Nunca auto-envía en PR1 |
| Approval UI | `/admin/inquiry-replies` | Separate de `/admin/inbox` |
| Editor en UI | Sí, editan msg1 + msg2 antes de approve | Polish manual |
| Approval timeout | 48h → `expired` | No pending forever |
| Idioma respuesta | El del mensaje guest, NO `payload.lang` | Airbnb mistraduce |
| Multi-mensaje threading | 2-3s delay entre msg 1 y msg 2 | Beds24 wiki |
| Casa Chamán | Filtrar — no responder | Memoria #6 |
| Precio en mensaje | NUNCA mostrar número | `payload.price` = net Alex |

#### Tests PR1 (REV 3 ampliado)

- drafts response for new inquiry with question
- skips inquiry without guest message  
- detects language correctly when payload.lang != actual
- extracts topics correctly
- respects 24h window
- idempotente (mismo beds24_event_id → solo 1 PIR)
- handles malformed payload gracefully
- skips Casa Chamán
- template renders NEVER contains explicit MXN number
- **NEW REV 3:** burst de 3 msgs guest en 90 seg → solo 1 PIR row, process_at se resetea cada UPDATE
- **NEW REV 3:** host respondió 30 min antes de cron tick → PIR status='paused', bot_pause_until = host_msg_at + 1h
- **NEW REV 3:** host respondió hace 2h sin más actividad humana → bot retoma, status='approval_pending'
- **NEW REV 3:** host respondió, después guest msg nuevo dentro de 1h → bot keep paused, bot_pause_until extends
- **NEW REV 3:** backup sweep detecta beds24_event sin PIR → enqueues correctly

#### DoD PR1 (REV 3)

- Migration 0051 applied remote D1
- Webhook handler integrado con `enqueueInquiryReply`
- Cron `*/5min` integrado con `processReadyInquiries` + backup sweep cada 3er tick
- `/admin/inquiry-replies` UI live con edit + approve + reject
- Smoke test: simular inquiry payload → PIR row created status='awaiting_processing' → tras 5min → status='approval_pending'
- Smoke test pause: simular host msg → PIR status='paused' → simular 1h sin host activity → cron unpause
- Tests ≥85% coverage
- Zero auto-sends (canary 0%)
- Documentation en code

---

### §3.2 · PR2 — Templates Phase B.2 enriched + canary

**Branch:** `feat/inquiry-templates-canary`
**Effort:** 8-10h CC + 4-6h Alex/Karina (templates)
**Risk:** medio (sale a producción real con canary)
**Dependency:** PR1 merged + deployed

#### Templates en R2 — 8 totales (4 villas × ES+EN)

`inquiry-rincon-del-mar-es.md`, `inquiry-rincon-del-mar-en.md`, `inquiry-las-morenas-es.md` (chef OPCIONAL), `inquiry-las-morenas-en.md`, `inquiry-combinada-es.md` (58-60 pax), `inquiry-combinada-en.md`, `inquiry-huerta-cocotera-es.md` (sin chef default), `inquiry-huerta-cocotera-en.md`.

#### Template Rincón del Mar ES — propuesta enriched (REV 2 manteniendo, REV 3 sin cambios)

2 mensajes separados por `{{MSG_2_BREAK}}`. Placeholders: `{guestFirstName}`, `{numAdults}`, `{nightsCount}`, `{questionAnswer}`.

**Mensaje 1 (corto, <500 chars):**

```
¡Hola {guestFirstName}! 👋

{questionAnswer}

En un momento te mando la propuesta completa para los {numAdults} huéspedes que mencionaste. 🌊
```

**Mensaje 2 (enriched, <2000 chars):**

```
🏖 Rincón del Mar — para {numAdults} personas, {nightsCount} noches

Es la villa con chef incluido del grupo. Apapacha total desde que llegan.

✅ Lo que ya está incluido en la tarifa de Airbnb:
• Chef Celene + cocinera + mozo (3 personas a su servicio)
• Desayuno, comida y cena preparada
• Bebidas en palapa-bar frente al mar
• Limpieza diaria · WiFi · A/C todas las habs
• 6 habitaciones · 18 camas · 6.5 baños

📍 Pie de playa · zona tranquila
Pacífico al frente. Lejos del bullicio de la bahía pero cerca del malecón si quieren cenar fuera. Vecinos canadienses y americanos.

💰 Cómo funciona la cuenta
• La tarifa que ya viste en Airbnb cubre la villa completa con el equipo de chef
• Personas extras (hasta 30): $300/noche c/u, paga al llegar
• Víveres: cuenta aparte transparente. Compras las hace nuestra chef Celene, pagás al llegar contra recibos. Promedio $250-280/persona/noche

🛎 Servicios opcionales con costo aparte
• Yates, snorkel, pesca, esquí acuático — coordino yo todo
• Masajes en sitio con Michel
• Fogata en la playa, cocos frescos
• Paquete bodas/eventos formales $1,400/persona

👉 Mirá las más de 168 reseñas ⭐ 4.84 en mi perfil:
airbnb.mx/users/95731371/listings

Confirmás {numAdults} huéspedes o vienen más? Cualquier duda más, escribíme.

— Alexander 🏖
```

#### Composer `{questionAnswer}` — determinista (REV 2 maintaining)

```
chef     → "El servicio de chef SÍ está incluido en la tarifa que ya viste en Airbnb (Chef Celene + cocinera + mozo)."
veveres  → "Los víveres NO están incluidos en la tarifa de Airbnb — esos los compramos nosotros, costo transparente, pagás al llegar. Promedio $250-280/persona/noche."
precio   → "La tarifa que ya viste en Airbnb cubre la villa completa con el equipo de chef. Lo único que se paga aparte son las personas extras (>16) a $300/noche y los víveres."
mascotas → "Aceptamos hasta 2 mascotas por reservación, con un cargo único de $300 MXN por estancia (no por noche)."
evento   → "¡Felicidades por el evento! Para bodas/XV años manejamos paquete de $1,400/persona, mínimo 40 invitados."
default  → "Muchas gracias por tu pregunta. Te respondo a detalle en el siguiente mensaje."
```

#### Canary scaling plan

| Fase | % auto-send | Duración | Gate próxima fase |
|---|---|---|---|
| 0% (PR1 baseline) | 0% — todo approval_pending | Indefinido | PR1 mergeado |
| Smoke test | 1 inquiry real manual | 24h | Alex aprueba calidad |
| 10% | 1 de cada 10 | 7 días | <2 false positives |
| 25% | 1 de cada 4 | 7 días | <5% rejection rate |
| 50% | mitad auto-send | 14 días | Sustained <5% issues |
| 100% | todas auto-send | indefinido | — |

**Telegram alert flow:**
- High-stake (evento, complaint, off-platform) → siempre approval_pending + alert Karina
- Canary % NO aplica a high-stake
- Haiku confidence <0.5 → siempre approval_pending

#### Eval cases PR2 (REV 3 — agregados iq011, iq012)

- iq001: Ana Karen real (chef + víveres) — msg2 NO contiene número MXN
- iq002: EN guest mascotas Las Morenas
- iq003: Inquiry sin pregunta concreta
- iq004: Wedding inquiry high-stake
- iq005: Off-platform attempt
- iq006: Complaint pre-booking
- iq007: Multiple topics
- iq008: Precio explícito — bot dice "tarifa que ya viste en Airbnb", NO inventa número
- iq009: Negotiation agresivo
- iq010: Idioma payload incorrecto (FR pero payload dice ES)
- **iq011 (NEW REV 3):** Host respondió 30min antes → PIR status='paused', bot NO envía, audit log claro
- **iq012 (NEW REV 3):** Host respondió hace 2h sin más actividad humana → cron retoma normal, bot procesa Haiku + composer + send

#### DoD PR2

- 8 templates pegados en R2 vía `/admin/templates`
- 12 eval cases ≥90% pass (iq001-iq012)
- Canary scaling logic implementada
- Smoke test 1 inquiry real respondida
- `/admin/inquiry-replies` muestra canary status + pause status
- Telegram alert high-stake LIVE
- Worker deploy (manual `wrangler deploy`)

---

### §3.3 · PR3 — Lifecycle post-booking activation

**Branch:** `feat/lifecycle-activation`
**Effort:** 6-10h CC
**Risk:** medio-alto (touches 25 active bookings)
**Dependency:** PR2 canary 100% sustained 14 días

#### Lo que activa (todo ya construido)

| Stage | Handler existente | Action |
|---|---|---|
| `booked` → `pre_arrival_t30` | `scanForWelcome` en `pre-stay.ts` | Welcome msg |
| pre_arrival_t30 → t14 → t7 → t1 | `runPreArrivalScan` | Touchpoints sequence |
| `pre_arrival_t1` → `arrived` | mismo | Check-in day |
| `arrived` → `in_stay` | cron auto | T+1 check |
| `checked_out` → `review_pending` | `runPostStay` | Review request |

Todos existen. Falta:
1. Pegar templates Phase B.1 en R2 (32 templates)
2. Activar `MESSENGER_OUTBOUND_ENABLED='true'`
3. Canary scaling análogo PR2
4. **REV 3:** Aplicar misma pause logic 1h a lifecycle bot

#### Templates Phase B.1 mínimos

Para PR3 minimum viable:
- `welcome-<slug>-<lang>.md` × 8
- `pre-arrival-t7-<slug>-<lang>.md` × 8
- `pre-arrival-t1-<slug>-<lang>.md` × 8
- `post-stay-review-<slug>-<lang>.md` × 8

Total: 32 templates. ~4-6h Alex/Karina polish.

#### Decisiones cerradas PR3

| Decisión | Valor |
|---|---|
| Activación `MESSENGER_OUTBOUND_ENABLED` | Manual via `wrangler secret put` |
| Canary scaling | 0→10→25→50→100% sobre 4 semanas |
| Order activation | Welcome first, post-stay last |
| Karina notification | Daily digest 09:00 Acapulco |
| Pause flag | Respeta `bookings.pre_stay_skip=1` |
| Quiet hours | NO send 22:00-08:00 Acapulco |
| **(REV 3) Human pause 1h** | **Aplica a todos los touchpoints lifecycle** | Misma lógica que inquiry bot |

---

## §4 · Attachments — qué se puede mandar

### Limits técnicos confirmados (Beds24 wiki)

| Channel | Tipos | Size |
|---|---|---|
| **Airbnb** | JPG, GIF, PNG **únicamente** | 2 MB |
| **Vrbo** | PDF, JPG, GIF, PNG | 2 MB |
| **Booking.com** | Email-based | 2 MB |
| **WhatsApp BSP** | JPG, PNG, PDF, MP4, audio | 16 MB |

**NO PDFs en Airbnb.** Para cotización detallada: texto largo o link a página.

**Voto WC post-PR3:** foto de villa específica desde R2 si Haiku detecta interés alto. Defer.

---

## §5 · Arquitectura: bot único vs separado

**Voto WC final: Bot único con context switch por canal.**

```
worker-bot (Hono, deployed)
├── Greeter (WhatsApp pre-booking, LIVE thread/217)
├── Inquiry Responder (Airbnb pre-booking, NEW PR1-PR2)
├── Lifecycle Bot (post-booking, PR3 activa)
└── Karina Suggest (admin assist, ya LIVE)
```

**Lo común:** KB en KV, `sendMessageRouted`, `messenger_outbound`, kill switch, eval framework, **REV 3:** pause logic 1h.

**Lo diferenciado:** Prompt per use-case, templates per channel, channel-specific rules.

---

## §6 · Best practices research — industry validation (REV 3 ampliado)

### Patrón canónico cross-industry (confirmado en research)

| Plataforma | Trigger | Delay | Human handoff |
|---|---|---|---|
| **Uplisting** | Webhook | **0-60 min configurable** | "If you respond manually, the auto-responder will not trigger" |
| **Hospitable** | Webhook | **0-60 min configurable** | "If you manually replied before scheduled time, we will not send it" |
| **Guesty** | Webhook | **Delay answer field per-rule** | Manual pause per conversation |
| **Hostaway** | Webhook | **Configurable** | "Delayed messages cancelled if new guest msg, AI reprocesses" |
| **OpenClaw (OSS)** | Webhook | Configurable | Time-based resume threshold |
| **RDM (este spec)** | **Webhook + 5min debounce** | **5min default** | **1h time-based unpause** |

**Conclusión:** RDM spec **alineado con industry standard**. 1h pause es middle ground entre Hospitable (sin auto-resume) y OpenClaw (configurable).

### Métricas industry

- <1h response → +25% conversion (Intellihost 5000 properties)
- 89%→100% response rate → +116% instant bookings
- Quick Responder badge (Airbnb)
- Superhost requires ≥90% response rate

**Target RDM:** <10 min auto-send (5min debounce + 5min cron worst case). Vs 2h actual = **mejora 12x**.

---

## §7 · Creatividad — propuestas adicionales (sin cambios REV 3)

15 ideas, mayoría defer post-PR3. Top 3 ya validadas:
- §7.1 Upsells dinámicos post-confirmation
- §7.2 VIP/repeat guest detection
- §7.5 Quote attachment con imagen

Ver thread/220 REV 2 §7 para lista completa.

---

## §8 · Inconsistencias cross-channel (REV 3 sin cambios)

9 inconsistencias detectadas. Ver REV 2 §8 para detalle. Resumen:
1. Servicio Las Morenas chef incluido vs opcional
2. Reseñas count stale
3. Combinada capacity 58 vs 60
4. WiFi Morenas password diferente
5. Clave caja "6720" universal
6. Paquete bodas $1000 vs $1400
7. Cancelación asimétrica
8. Páginas missing /guia-llegada + /eventos
9. (REV 2) "Total Airbnb" no se puede mostrar

---

## §9 · Cost analysis

### Anthropic API budget (REV 3)

| Phase | Volume | Cost per request | Monthly |
|---|---|---|---|
| PR1 test | 5 inquiries | $0.005 | $0 (one-time) |
| PR2 canary 10% | 3/day | $0.005 | ~$0.50/mes |
| PR2 100% | 10/day | $0.005 | ~$1.50/mes |
| PR3 lifecycle 100% | 25 bookings × 5 touchpoints | $0.002 | ~$0.25/mes |
| **Total expected** | ~150 calls/mo | — | **~$2-3 USD/mes** |

**REV 3 nota:** debounce window NO agrega LLM cost (procesa 1 vez después del debounce, no múltiples). Pause logic NO usa LLM (time-based puro).

**Total infrastructure:** <$5 USD/mes. ~$60/año.

---

## §10 · Definition of done global

### PR1 (REV 3)
- Migration 0051 applied remote D1 (con columnas process_at, last_inbound_msg_at, bot_pause_until)
- Webhook handler integrado con `enqueueInquiryReply`
- Cron `*/5min` integrado con `processReadyInquiries` + backup sweep
- Approval UI live
- Smoke test debounce: 3 msgs guest en 90 seg → 1 PIR, process_at se resetea
- Smoke test pause: host msg → PIR paused 1h → 1h sin host → unpause
- Tests ≥85% coverage
- Zero auto-sends

### PR2
- 8 templates in R2
- 12 eval cases ≥90% pass (incluye iq011 + iq012 pause logic)
- Canary 10% smoke test successful
- Telegram alert high-stake LIVE
- Worker deploy
- Karina training (15 min)

### PR3
- 32 lifecycle templates in R2
- `MESSENGER_OUTBOUND_ENABLED='true'` deployed
- Canary 0%→10% smoke test
- Pre-stay + post-stay scans verified
- Quiet hours respected
- Karina daily digest LIVE
- Pause logic 1h aplicada a lifecycle

### Global success metrics
- Inquiry response time: <10 min average (vs 2h current)
- Inquiry response rate: 100%
- Lead conversion rate: maintain or improve (>28% baseline)
- False positive rate: <5%
- Cost: <$10 USD/mes Anthropic

---

## §11 · Risks + mitigations (REV 3 ampliado)

| Risk | Severity | Mitigation |
|---|---|---|
| Bot manda info incorrecta | Alta | Composer determinista + approval mode PR1 + canary |
| Bot promete chef no disponible | Alta | Template "nuestro equipo de chef" genérico |
| Off-platform attempt | Alta | Red flag detection + escalate Karina |
| KB stale | Media | R2→KV pipeline refresh 2h |
| Idioma mistakes payload.lang | Media | Detectar via Haiku |
| Wedding inquiry mal manejada | Alta | High-stake siempre approval_pending |
| Anthropic API outage | Baja | Fallback: template raw |
| Beds24 API rate limit | Baja | 20 per cron run, retry exponential |
| Karina overwhelmed por approvals | Media | Canary scaling auto-reduces load |
| Casa Chamán mencionada por error | Alta | Filter roomId in handler |
| Greeter v7.1 break | Alta | Separate eval framework |
| Bot muestra precio incorrecto | Alta | NUNCA mostrar número, "tarifa que ya viste" |
| **(NEW REV 3)** Bot retoma justo cuando Karina sigue gestionando | Media | **1h window es conservador. Si Karina necesita más, puede mark `bot_pause_until` manual via /admin** |
| **(NEW REV 3)** Webhook lost → inquiry sin PIR row | Media | **Backup sweep cada 3er tick `*/5min` = max 15min detection** |
| **(NEW REV 3)** Debounce reset infinito (guest spam) | Baja | **Cap: process_at no se puede resetear más de 5 veces. Después de 5 → procesa forzado** |

---

## §12 · Recomendación final (REV 3 — arquitectura cerrada)

### Camino propuesto (sin cambios)

1. **PR1 — Esta semana** (8-12h CC + Alex polish templates en paralelo)
2. **PR2 — Próxima semana** (8-10h CC + 4-6h Alex/Karina templates)
3. **PR3 — 2-3 semanas después** (6-10h CC + 4-6h Alex/Karina templates lifecycle)

### Lo que necesito de Alex para arrancar

**Status REV 3: Todas las preguntas cerradas. Listo para DoIt task.**

Preguntas históricas (ya respondidas):
1. ✅ Plan PR1 → PR2 → PR3 en 4-6 semanas
2. ✅ Tono mix costeño + neutral, 2 mensajes, emojis funcionales
3. ⏳ Karina templates polish próxima semana (TBC con Karina)
4. ✅ CC arranca PR1 autónomo
5. ✅ Precio "tarifa que ya viste en Airbnb"
6. ✅ Trigger: webhook + 5min debounce + reset
7. ✅ Skip + audit si host respondió
8. ✅ Human pause 1h time-based unpause

---

## §13 · Appendix — research raw (REV 3)

### Industry quotes (textuales)

**Uplisting:** "Uplisting can respond almost instantly if you like (0-minute time delay), however, some members prefer to delay up to 60 minutes to allow them to respond manually. If you respond manually, the auto-responder will not trigger."

**Hospitable:** "If you have a delay on your message, and you manually replied to the guest before the scheduled send time of the message, then we will not send it. This is to avoid repetition."

**Hostaway:** "Delayed Auto-Reply messages are cancelled (will not be sent) if a new guest message is received during the delay period. Because the new guest message potentially brings new context, AI will take the new guest message into account and reprocess the whole conversation to regenerate a fresh message."

**OpenClaw (OSS):** "When a fromMe message is detected in a DM thread where auto-reply is active, the AI pauses auto-reply for that specific thread. Auto-reply resumes either after [time-based threshold] or [manual resume command]."

### Beds24 payload detalle (REV 2 maintaining)

**En `event_type='booking_created' status='inquiry'`:**
- `price`: ✅ presente (= net Alex)
- Resto: 0/null

**En `event_type='booking_created' status='confirmed'`:**
- `price`: ✅ presente (= net Alex)
- `commission`: ✅ presente
- Resto: typically null

**NUNCA viene:** Total guest, service fee, taxes locales.

### Emoji blocklist Airbnb (sin cambios)

**BLOCKED confirmed:** 🌅 📶
**Suspected BLOCKED:** 🔒 🚨 🍳 🚿
**SAFE confirmed:** 🛏 ✅ 👨‍🍳 🏊 🏖 🧹 🎵 🛻 🛥 🛎 🛒 🍹 🔥 🥥 💆 🐴 🚣 🤿 🎉 🏅 💬 ☀ ⛱ 1️⃣-6️⃣

### D1 schema (REV 3)

```
beds24_events            -- inquiries land here
bot_messages_inbox       -- guest + host messages threaded
beds24_bookings          -- normalized bookings, lifecycle status
booking_captures         -- pets/menu/chef capture
inquiries_closed         -- audit trail auto-closed inquiries
messenger_outbound       -- audit trail outbound, gated by flag
pending_welcomes         -- legacy, deprecated
pending_inquiry_replies  -- NEW PR1 (REV 3 schema con process_at, bot_pause_until)
```

### Cron schedule (REV 3 — sin agregar nuevos)

- `0 10 * * *` — daily cron (sin cambio)
- `*/5 * * * *` — bot polling (+ processReadyInquiries + backup sweep cada 3er tick)
- `*/30 * * * *` — pre-stay welcome scan (sin cambio)

---

## §14 · Status

**Documento status:** REV 3 — Ready for DoIt CC.

**Cambios REV 3 (2026-05-27, post-feedback Alex):**
- Arquitectura webhook + 5min debounce + reset on update CERRADA
- Skip auto-send si host respondió CERRADO
- Human pause time-based 1h CERRADO
- Cron `*/5min` reutilizado, NO agrega 5to cron
- Backup sweep cada 3er tick
- Schema migration 0051 actualizado con process_at, last_inbound_msg_at, bot_pause_until, pause_reason
- Status enum extendido: awaiting_processing, paused, superseded_by_human
- Handler split en 3 funciones: enqueueInquiryReply, processReadyInquiries, checkHumanPause
- Tests PR1 ampliados con 5 escenarios nuevos (burst, pause, unpause, backup sweep)
- Eval cases PR2 ampliados con iq011 + iq012
- §6 ampliado con industry validation textual
- §11 risks: agregados 3 risks REV 3 + mitigations
- §13 industry quotes textuales agregadas

**Próximas acciones:**
- Alex aprueba DoIt task para CC
- CC ejecuta PR1 autónomo con spec REV 3
- WC review pre-merge
- Alex deploy + smoke test

**Sesión WC:** Spec cerrado. Listo para handoff a CC.

---

*FIN thread/220 REV 3. Arquitectura cerrada, ready for DoIt.*

— Web Claude, 2026-05-27
