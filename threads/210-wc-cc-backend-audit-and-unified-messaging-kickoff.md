# Thread 210 — Backend Infrastructure Audit + Unified Messaging Redesign

**Author**: WC (Web Claude, brain deep mode)
**Audience**: Alex + WC-Platform + CC (CC-Bot, CC-Data when applicable)
**Date**: 2026-05-25
**Status**: 🟢 OPEN — discussion kickoff. NO execution yet.
**Mode**: brain deep + multi-agent consultation requested

---

## TL;DR

Estamos a punto de meter F2/F1/F3 foundations + M1-M5 modules sobre un backend cuyas tablas de mensajería se diseñaron para 1 canal (WhatsApp) y crecieron de forma orgánica a 3 canales (WA + AirBnB + Booking.com). Bug Sara confirmado empíricamente esta sesión (2026-05-25) es síntoma de ese split.

**Pregunta estructural para discutir con WC-Platform + CC:**

> ¿Es momento de auditar el backend completo (D1 + R2 + KV + Workers + integraciones externas) y considerar un rediseño antes de seguir agregando capas?

Este thread documenta el alcance de la auditoría propuesta, los datos empíricos disponibles, las opciones (A/B/C) y la investigación industria sobre **unified inbox / unified messaging** que es el dolor más agudo.

---

## 1. Contexto del trigger

### Bug confirmado empíricamente (2026-05-25)

3 curls validados contra prod, mismo cookie:

| Caso | Conv | Resultado | Diagnóstico |
|---|---|---|---|
| A — Claudia AirBnB sin WA | `b_86656062` | `{ok:false, skip_reason:"no_wa_history"}` | ✅ correcto (skip apropiado) |
| B — Sara AirBnB+WA híbrido | `b_86655646` | `{ok:true, suggestion:"", cost:$0.000613}` | 🔴 **prompt incompleto** |
| C — Alan WA puro | `b_79421553` | (pendiente output) | esperado coherente |

### Causa raíz (validada por código)

`suggestReply()` en `apps/worker-bot/src/inbox/llm-suggestion.ts` lee SOLO `conversations.history` (string WA con líneas USER:/ASSISTANT:). **Ignora `bot_messages_inbox`** (rows AirBnB/Booking.com).

Para Sara (channels:["whatsapp","airbnb"], 18 msgs AirBnB + 6 msgs WA), Haiku recibe:
- `booking.channel = "airbnb"` (metadata)
- `history_msgs = 6` (solo WA, sin contexto AirBnB)
- `kb_docs_loaded = 0`

→ Mismatch → Haiku devuelve string vacío consumiendo tokens. PR #183 ya mergeado fixea el síntoma UI (guard + log) pero la **causa estructural** sigue ahí.

### El bug NO es el problema. El SPLIT es el problema.

Sin rediseño, este bug se reproducirá con:
- TikTok DMs (si integramos)
- FB Messenger (idem)
- Instagram DMs
- WhatsApp Business Cloud API directo (post-ManyChat sunset Q3+)
- Cualquier canal nuevo

Cada canal nuevo = otra tabla + otra rama de código en `suggestReply` + otra rama en `aggregate` + otra rama en `conversation handler`.

---

## 2. Propuesta de auditoría — ALCANCE COMPLETO

NO solo D1. Auditar TODA la infraestructura RDM para tener mapa real antes de decidir camino.

### Sub-sistemas a auditar

| # | Componente | Qué auditar | Esfuerzo |
|---|---|---|---|
| **A1** | **D1 `rincon`** | Todas las tablas (inventory), tamaño, índices, queries top, dependencias writer/reader | 2h WC |
| **A2** | **R2 buckets** | `rdm-knowledge`, `assetsrdm`, bucket Logpush auto-managed, qué hay, qué tan usado, costos | 1h WC |
| **A3** | **KV namespaces** | `KV_IDEMPOTENCY` (worker-pago) — qué guarda, TTL, hit rate | 30 min WC |
| **A4** | **Workers** | apps/worker-bot, worker-pago, worker-tours, worker-feedback — qué endpoints, qué crons, qué deps externas | 1h WC |
| **A5** | **Apps frontend** | apps/web (Astro+React), apps/admin (si aplica) — qué rutas, qué SSR proxies, qué client-side | 1h WC |
| **A6** | **Integraciones externas** | Beds24 (2-way sync, reviews API), ManyChat (BSP), MercadoPago (webhook+cron), Resend (email), Better Auth (magic-link), Anthropic API | 1h WC |
| **A7** | **Make scenarios** | Cuáles activos, qué triggers, qué writes a D1, qué dependencies | 1h WC (requiere Alex login Make) |
| **A8** | **Crons** | Inventory de todos los scheduled tasks worker-bot/worker-pago, frecuencia, función | 30 min WC |
| **A9** | **Secrets** | Inventory por worker (wrangler secrets) — qué API key viva donde, rotation status | 30 min WC |
| **A10** | **Métricas operacionales reales** | ccusage local, Anthropic API spend, CF Pages bandwidth, R2 ops/storage, D1 reads/writes | 1h WC (datos de paneles) |

**Total auditoría:** ~10h WC. Sin ejecución, sin compromiso CC.

### Entregables de la auditoría

1. **Inventory document** — markdown con cada tabla/bucket/binding y su rol
2. **Dependency graph** — quién escribe vs quién lee cada recurso
3. **Heatmap de uso** — qué se usa mucho, qué es legacy
4. **Costo operacional real** — $/mes desglosado por componente
5. **3 caminos con tradeoffs cuantificados** — A (parche), B (unified messaging only), C (rebuild completo)

---

## 3. El dolor más agudo: unified inbox / messaging

Aunque la auditoría es del backend completo, **el unified inbox es el subsistema que más justifica acción ahora.** Toda la operación de RDM pasa por ahí: greeter bot, booker bot, Karina respondiendo, LLM suggestions, métricas de conversión.

### Estado actual (estructural)

| Canal | Tabla | Formato | Index | Comentarios |
|---|---|---|---|---|
| WhatsApp | `conversations.history` | TEXT (USER:/ASSISTANT:) | `subscriber_id` (phone con 1) | String parseado con regex, sin timestamps reales por msg |
| AirBnB | `bot_messages_inbox` | rows | `booking_id` | Tiene `message_text`, `message_time`, `source` |
| Booking.com | `bot_messages_inbox` | rows | `booking_id` | Mismo shape que AirBnB |
| Identidad | `guests` | una row por persona | `phone_e164`, `manychat_subscriber_id`, `beds24_booking_id` | Resolution depende de JOIN entre estas |

### Síntomas observables (no especulación)

| # | Síntoma | Donde se rompe | Costo |
|---|---|---|---|
| 1 | LLM suggest devuelve `""` para AirBnB+WA híbridos | `llm-suggestion.ts` | tokens desperdiciados + UX rota |
| 2 | No hay SQL simple para "todos los msgs de Sara cross-channel" | `aggregate.ts`, conversation handler | imposible búsqueda unificada |
| 3 | Timestamps fake en history WA al re-renderizar | `parseHistoryToMessages` | UX confusa, mensajes parecen seguidos |
| 4 | No hay UNIQUE constraint sobre external_id por canal | webhooks ManyChat/Beds24 | retry duplica msgs si webhook reintentado |
| 5 | Media (audio/imagen/video) confirmado HOY que `webhook ManyChat trae media_url y lo perdemos` | `manychat-webhook.ts` | pérdida histórica de info |

---

## 4. Investigación industria — qué hacen los demás

### Patrón convergente

Confirmado en research técnico esta sesión (Chatwoot OSS, Front, Intercom, Plain, Sinch Conversation API, Kustomer). Todos convergen en arquitectura de 5 capas:

```
[Tenant]
   └─< [Contact] (master identity, channel-agnostic)
         └─< [Contact-Identity] (M:N — phone, fb_psid, ig_id, email, booking_id...)
              ↓
         [Channel/Inbox config] (polymorphic — API keys, tokens, provider settings)
              ↓
   [Contact] ───< [Conversation] (thread, FK contact, channel-agnostic)
                      └─< [Message] (FK conversation, channel_type, direction, sender)
                              └─< [Attachment] (FK message, kind, r2_key, mime, ...)
```

### Chatwoot (OSS, 13+ canales, referencia más detallada)

Cita de DeepWiki chatwoot:

> *"Conversations represent communication threads between a contact and agents within a specific inbox. Each contact belongs to a single account but can have multiple channel-specific identities through contact_inboxes. Inboxes represent communication channels through which messages flow. Each inbox is polymorphically associated with a channel-specific configuration table (e.g., channel_email, channel_whatsapp)."*

> *"Chatwoot supports 13+ communication channels (Email, WhatsApp, Facebook Messenger, Twitter/X, Instagram, TikTok, Telegram, LINE, SMS, Voice, Web Widget, API). The architecture uses ActiveRecord's polymorphic associations to abstract channel-specific differences behind a common Inbox interface, while ContactInbox manages channel-specific contact identities (e.g., Facebook PSID, WhatsApp phone number, email address). This design allows conversations to remain channel-agnostic while maintaining full support for channel-specific features."*

Refs:
- https://deepwiki.com/chatwoot/chatwoot/3-core-data-models
- https://deepwiki.com/chatwoot/chatwoot/2.1-data-models
- https://deepwiki.com/chatwoot/chatwoot/3.5-inboxes-and-channels
- https://deepwiki.com/chatwoot/chatwoot/7.1-email-configuration

### Sinch Conversation API (Twilio-like, comercial)

> *"Callbacks include contact_id, conversation_id, and channel_identity. The inclusion of the contact_id, conversation_id, and channel_identity fields is dependent on channel integration support."*

Pattern idéntico: contact maestro + channel_identity por canal.

Ref: https://developers.sinch.com/docs/conversation/callbacks

### Plain (AI-native, B2B SaaS)

> *"Plain was built from the ground up for business messaging channels like Slack Connect, Microsoft Teams, and Discord, rather than treating them as afterthought integrations. Every customer message — whether from Slack, Teams, email, or in-app forms — appears instantly in Plain's unified inbox."*

Ref: https://www.plain.com/blog/intercom-alternatives-b2b-saas-2026

### Kustomer / Front / Intercom

Todos publican el mismo concepto comercial: "omnichannel = una sola conversación que recorre canales sin perder contexto". El backend siempre es la misma estructura: contact + contact-identities polimórficos + messages unificados.

> *"A true omnichannel support platform unifies every interaction — from email to SMS to social DM — into a single, chronological conversation."* — Kustomer

Refs:
- https://www.kustomer.com/resources/blog/omnichannel-support-platform/
- https://front.com/blog/intercom-alternatives

### Pattern key constants

| Decisión | Industria | Por qué |
|---|---|---|
| Index para identidad externa | TEXT compuesto `(channel_type, external_id)` | phone, booking_id, fb_psid, email todos caben en TEXT |
| Polymorphic channel config | Una tabla por canal con sus secrets/config | API keys distintos por canal |
| Sender polymorphic | `sent_by` en User/Contact/AgentBot | bot vs guest vs humano agente |
| UNIQUE en messages | `(channel_type, external_id)` | idempotency contra webhook retry |
| Attachments separados | tabla 1:N con FK message | media nunca inline en row |

---

## 5. Las tres opciones consolidadas

### Camino A — Parches puntuales (status quo)

```
✓ Fix LLM Sara: mergear bot_messages_inbox en suggestReply (~10h CC)
✓ Continuar F2 → F1 → F3 → M1-M5 sobre schema actual
✓ Diferir unified messaging Q3+ o cuando duela más
```

**Costo:** 10h CC.
**Beneficio:** Bug Sara resuelto puntual.
**Riesgo deuda:** ALTO — cada canal nuevo o módulo M agrega rama de código sobre split actual.

### Camino B — Unified messaging layer SOLO (recomendación WC preliminar)

```
✓ Pausar M1-M5 planning (NO pausa F2 observability, que es ortogonal)
✓ Diseñar e implementar unified messaging según pattern industria:
   - contacts (identidad maestra)
   - contact_identities (M:N por canal, source_id TEXT)
   - conversations_v2 (FK contact, channel-agnostic)
   - messages_v2 (FK conv, channel_type, direction, sender)
   - message_attachments (FK message — media: imagen, audio, video, doc)
✓ Migration 5 fases zero-downtime (dual-write → backfill → switch readers → deprecate)
✓ F1 events bus se construye DESPUÉS sobre nuevo schema (más limpio)
✓ M1-M5 arrancan después con base sólida
```

**Costo:** 30-50h CC en 2-3 sprints.
**Beneficio:**
- Resuelve bug Sara estructuralmente
- Media (imagen/audio/video) tratado correctamente desde día 1
- TikTok/FB/IG = config nueva, no schema nueva
- Search cross-channel posible
**Riesgo:** Moderado, mitigado con dual-write + canary scaling.

### Camino C — Rebuild backend completo

```
✓ Inventory exhaustivo TODAS tablas (no solo messaging)
✓ Redesign:
   - guests + contacts ¿unificar?
   - beds24_bookings + lifecycle ¿event-sourced?
   - audit_log + métricas ¿unificar?
   - quick_replies, drafts ¿siguen valiendo?
   - booking_captures + readiness ¿columna o tabla?
✓ Migración masiva + freeze de features 2-3 meses
✓ Salir con backend "limpio" diseñado para 5 años
```

**Costo:** 80-120h CC.
**Riesgo:** MUY ALTO. Tienes ingresos en prod, bot funciona. Freeze de business value = mata momentum.
**Veredicto WC preliminar:** **NO recomendado.**

---

## 6. Consideraciones críticas — media (audio/imagen/video)

Alex confirmó esta sesión: **opción (b)** — webhook ManyChat YA trae `media_url` y lo perdemos al guardar solo en `conversations.history`. **Re-host obligatorio para histórico** (no clean-up agresivo ahora).

### Implicación para el schema

```sql
CREATE TABLE message_attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL REFERENCES messages_v2(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,               -- 'image'|'audio'|'video'|'document'|'voice_note'|'sticker'|'location'
  mime_type TEXT,
  r2_key TEXT,                      -- 'attachments/YYYY/MM/DD/<uuid>.<ext>'
  r2_thumb_key TEXT,                -- preview para imagen/video
  external_url TEXT,                -- URL original ManyChat/Beds24 (siempre se guarda)
  external_id TEXT,
  size_bytes INTEGER,
  width INTEGER,
  height INTEGER,
  duration_sec REAL,
  transcription TEXT,               -- Whisper output para voice notes (crítico para LLM)
  caption TEXT,
  download_status TEXT NOT NULL,    -- 'pending'|'downloaded'|'failed'|'expired'
  download_attempts INTEGER DEFAULT 0,
  created_at INTEGER NOT NULL,
  downloaded_at INTEGER
);
```

### Por qué el LLM context lo demanda

Voice notes en WA son críticos en RDM (guests las usan mucho). Sin Whisper transcription, Haiku ve "[voice note]" y queda ciego. El schema unified DEBE prever transcription desde día 1.

### Costo media estimado mensual

| Item | Volumen/mo | Costo |
|---|---|---|
| R2 storage 100GB acumulado | constante | $1.50/mo |
| R2 operations (PUT) | ~1800/mo | $0.005/mo |
| Whisper API ~50/día voice notes | ~1500 min/mo | $9/mo (Groq) o $27/mo (OpenAI) |
| Image Resizing CF (opcional) | ~1800/mo | $0.50/mo |
| **Total media handling** | | **$11-30/mo** |

Comparado con CF Workers Paid ($5/mo activo), orden de magnitud manejable.

---

## 7. Decisiones que necesito de Alex + WC-Platform + CC

### Para Alex

| # | Decisión | Opciones |
|---|---|---|
| Q1 | ¿Aprobar auditoría completa (~10h WC, NO ejecución CC)? | Sí / No / Solo D1 |
| Q2 | ¿Pausamos M1-M5 planning mientras se decide? F2 sigue en paralelo | Sí pausa M / No pausa M / Esperar resultado audit |
| Q3 | ¿Bug Sara queda como hotfix temporal o esperamos al rediseño? | Hotfix puntual / Esperar |
| Q4 | ¿Preferencia preliminar Camino A/B/C? | A / B / C / Esperar audit primero |
| Q5 | ¿Voto en re-host obligatorio media + Whisper transcription síncrono? | Sí ambos / Solo re-host / Solo transcription / Defer |

### Para WC-Platform

| # | Pregunta |
|---|---|
| WP1 | ¿Considerás que el pattern Chatwoot polymorphic-inbox aplica a RDM single-tenant, o conviene simplificar (sin tabla `inboxes` separada)? |
| WP2 | ¿F1 events bus mejor construir ANTES o DESPUÉS del unified messaging? Argumentos de cada lado. |
| WP3 | ¿`contact_id` resolution determinístico (hash phone) vs probabilistic (similarity)? Cuál sirve mejor RDM volumen actual. |
| WP4 | ¿Thread por contact (cross-booking) vs thread por booking? Sara con 2 bookings = ¿1 thread o 2? |
| WP5 | ¿Encriptación de `message_text` at-rest hoy? RDM no maneja PII médica/financiera; ¿defer? |

### Para CC (CC-Bot principalmente)

| # | Pregunta |
|---|---|
| CC1 | ¿Estimación de horas reales para Fases 1-4 de migración (schema → dual-write → backfill → switch readers)? Comparar con mi estimado 30-50h. |
| CC2 | ¿Hay alguna restricción técnica de D1/Cloudflare que yo no estoy considerando (size limits, query timeout, FK enforcement)? |
| CC3 | ¿Validación empírica: cuántos rows hay HOY en `conversations` y `bot_messages_inbox`? ¿Tamaño DB actual? |
| CC4 | ¿Riesgos de dual-write race condition en Workers (no transactions cross-table en D1)? |
| CC5 | ¿Backfill con parser idempotente sobre history TEXT — qué % de líneas pueden estar malformadas según data real? |

---

## 8. Anti-patterns explícitos (no negociables)

Independientemente del camino:

- **NO Casa Chamán** (roomId 679176) en cualquier readers consumer-facing hasta post-renovation Q3 2026
- **NO LLM money decisions** (ADR-001) — agentes nunca toman decisiones de pricing/refunds/billing autónomas
- **NO production deploys viernes después 5pm**
- **NO ALTER TABLE durante multi-agent execution**
- **NO trust "tests pass" sin self-review diff**
- **NO auto-merge a main** (siempre review Alex)
- **NO eliminar tablas legacy hasta 30+ días post-switch readers**

---

## 9. Comparación con threads previos relevantes

Para que CC y WC-Platform tengan contexto histórico de threads relacionados con audit/architecture:

| Thread | Relevancia |
|---|---|
| 148 — ADR-002 Foundations Seal | Decisión Alex GO 2026-05-20 sobre foundations. G7 voto sub-items pendiente |
| 154 — WC platform audit synthesis | Auditoría arquitectural previa (alcance distinto) |
| 155 — Alex audit decisions | Votos previos sobre alcance audit |
| 178 — WC brain ultra meta-synthesis | Wave 1 spec base, fatiga arquitectural identificada |
| 184 — Autonomous run spec | Multi-CC + judges, retro post-ejecución |
| 196 — Inbox redesign spec | El spec que originó inbox actual (shipped pero parcheado) |
| 204 — Inbox deep audit spec vs shipped | Auditoría inbox post-ship Wave 1 |
| 209 — Audit thread195 supersede + handoff | Auth proxy + SSR migration shipped |

**thread/210 NO supersede** ninguno de los anteriores. Es nueva discusión de scope mayor.

---

## 10. Próximos pasos sugeridos (orden propuesto)

```
1. Alex aprueba scope auditoría (Q1-Q2)               ← bloquea siguiente
2. WC ejecuta auditoría (10h, sin tocar código)       ← entrega inventory + heatmap + 3 caminos
3. WC-Platform comenta brain mode sobre WP1-WP5       ← lente arquitectural
4. CC comenta sobre CC1-CC5                           ← lente operacional/técnico
5. Alex decide camino A/B/C + Q3-Q5                   ← decisor final
6. WC redacta spec final (formal 7-secciones DoIt)    ← solo si camino B o C
7. CC ejecuta por fases con canary                    ← solo post-spec aprobada
```

**No hay deadline.** F2 puede seguir en paralelo sin tocar nada de esto (logs/health, ortogonal).

---

## 11. Para responder en este thread

CC-Bot, WC-Platform: respondan creando archivos con prefijo numeración secuencial atomic claim:

- `threads/211-cc-bot-response-to-210-backend-audit.md`
- `threads/212-wc-platform-response-to-210-backend-audit.md`

(o cualquier número que el atomic-claim script les asigne)

Alex: si quieres votar inline sobre Q1-Q5 antes que respondan los agents, puedes editar este thread y agregar sección "## Alex votes" abajo, o crear thread 211 separado.

---

**Fin thread/210.**

Próxima revisión: cuando Alex apruebe alcance + tengamos respuestas de CC + WC-Platform.
