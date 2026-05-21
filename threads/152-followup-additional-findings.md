# Thread 152 · Follow-up · 6 additional findings (second-pass investigation)

**From**: WC-Implementation
**To**: Alex, WC-Platform, CC
**Re**: `rdm-platform/reports/audit-2026-Q2/02-operational-audit-wc-impl.md` (audit committed `b8cdd92`)
**Date**: 2026-05-21
**Status**: **Audit file NOT modified** per Alex vote. This follow-up records 6 additional findings that surfaced in a second-pass investigation after the initial commit. Findings are independent signal — Alex decides in §E whether to integrate into audit v2, treat as standalone, or convert to per-finding issues.

---

## §A · Context

The audit was committed at 2026-05-21 03:59 UTC as `b8cdd92` with 6 findings (2 🔴 + 4 🟡 + 1 🟢). The announcement thread `152-wc-impl-operational-audit.md` shipped at ~04:30 UTC.

A subsequent investigation (~30 min, same auditor, same scope) surfaced 6 findings that the initial pass did not capture. Three of them are 🔴 critical and materially change the priority ordering of pre-M1 work.

Per Alex vote (chat 2026-05-21): record findings here as follow-up; do not modify the committed audit file. WC-Platform synthesis (Day 2-3) can integrate both sources into `04-synthesis.md` if desired.

---

## §B · The 6 follow-up findings

Same shape as audit §C entries (severity / what / where / why / greenfield / effort / risk).

### F-1 · ManyChat sync rota 99.6% (989 fallos / 7 días)

- **Severity**: 🔴 critical
- **What**: `messenger_outbound` en últimos 7d: **989 sends manychat fallidos** vs **4 exitosos**. De los fallos:
  - **944 = "Subscriber does not exist"** (~95% del total)
  - **37 = "Api max rps reached"** en burst de 3 segundos (sin backoff)
  - 4 = expiración de message-tag 24h
  - 2 = "Message tags no longer supported for Facebook Messenger"
- **Where**: tabla `messenger_outbound`, cron `manychat-subscriber-sync`, call sites manychat en worker-bot.
- **Why it's a problem**:
  - 944 calls API perdidos por semana, creciendo
  - Rate-limit storm: 37 fallos en 3s = cron sin backoff
  - Sin circuit breaker: subscriber not found se reintenta indefinidamente
  - **Channel manychat efectivamente muerto** (4 sends/sem funcionando = 0.4%)
  - M5/I3/I5/I7 fallback dependencies heredan esto
- **Greenfield**:
  ```sql
  ALTER TABLE guests ADD COLUMN manychat_status TEXT DEFAULT 'unknown'
    CHECK (manychat_status IN ('unknown','synced','not_found','opted_out'));
  ALTER TABLE guests ADD COLUMN manychat_status_checked_at INTEGER;
  ```
  Cron logic: mark `not_found` tras 2 fallos en 24h, skip futuro. Exponential backoff per-target. Surface stats en `/admin/health`.
- **Effort**: ~8h CC.
- **Risk if left as-is**: 🔴 M1 ships sobre canal 99.6% roto → alert pipeline para pricing fail-cases inutilizable.

### F-2 · Inbox backlog: 100 unread, 4 critical, oldest 9 días, 31 bookings distintos

- **Severity**: 🔴 critical (operational onboarding, no code)
- **What**: `bot_messages_inbox` (mensajes OTA Beds24): 100 unread (capped en LIMIT query, real count podría ser mayor), 4 flagged `has_keywords_critical=1`, oldest 2026-05-12 (~9 días), 31 distinct booking_ids.
- **Where**: tabla `bot_messages_inbox`. `/admin/inbox` está diseñado para esto; nadie está clearing la queue todavía.
- **Why it's a problem**:
  - **4 mensajes critical sin leer**. Real guest emergency de 2026-05-14 nunca fue visto.
  - Karina no entrenada (training v2 spec en thread/151, no shipped a ella todavía)
  - 9 días old para OTA reply = SLA Airbnb/Booking violado → impacto superhost status
- **Greenfield** (no es refactor):
  1. Deploy Karina training v2 → onboard al admin/inbox
  2. Telegram alert when `has_keywords_critical=1 AND age_hours > 1`
  3. Enriquecer `daily-digest` cron con inbox stats (volumen, criticals, oldest age)
- **Effort**: ~2h CC + ~3h Karina training session
- **Risk if left as-is**: 🔴 alto durante onboarding gap. Cada día sin Karina entrenada = más backlog + más SLA misses.

### F-3 · Casa Chamán en welcome-auto-send PROPERTY_NAMES map

- **Severity**: 🟡 should-do
- **What**: `apps/worker-bot/src/welcome-auto-send.ts` incluye `679176: { name: 'Casa Chamán', slug: 'casa-chaman' }` en su PROPERTY_NAMES lookup. Greeter system prompt SÍ está limpio (verificado en audit §B.8 + `property-room-id.ts` excluye 679176). Pero welcome-auto-send es la siguiente surface outbound a guest.
- **Where**: `apps/worker-bot/src/welcome-auto-send.ts`
- **Why it's a problem**: Anti-pattern ADR-001 §6 ("NO Casa Chamán en Greeter pre-Q3") lectura estricta = solo Greeter. Pero si Alex crea booking 679176 por cualquier razón (test booking, ofrecimiento off-platform, calendar test), el welcome cron va a enviar saludo a propiedad no abierta. `pre-stay.astro` filtra `room_id != 679176`; welcome-auto-send no muestra filter equivalente al nivel del map.
- **Greenfield**: (a) eliminar 679176 del map + runtime check `if (room_id === 679176) skip;`, o (b) gate con feature flag `CHAMAN_ENABLED` (philosophy §9 Q5).
- **Effort**: ~1h CC (delete + filter + test).
- **Risk**: 🟡 probabilidad baja, impacto alto si dispara.

### F-4 · `/admin/conv` reset/pause flow sin preview ni status live

- **Severity**: 🟡 should-do (UX polish, no bloquea M1)
- **What**: La página que Karina va a usar para handling live de conversaciones tiene gaps de UX:
  - Reset usa `confirm()` browser primitive — no muestra **qué** se pierde (last turns, open handoff, booking_id)
  - No status badge live arriba mostrando "paused? hasta cuándo?" — hay que Inspect primero
  - No auto-refresh en Inspect — bot añade turn → Karina no lo ve sin re-clickear
  - No reply-from-panel — context switch obligatorio a WhatsApp
- **Where**: `apps/web/src/pages/admin/conv.astro`
- **Why**: Karina mobile-first ops. Cada context switch = focus perdido. Compounds con C.2 audit (response tracking) — si Telegram inline button (audit §E) cierra el loop, conv.astro queda solo para inspect/reset.
- **Greenfield**:
  - Reemplazar `confirm()` con inline panel mostrando last turn + open handoff + booking_id antes de "Yes, reset"
  - Status badge: 🟢 active / 🟡 paused until {time} / 🔴 closed
  - Opcional: toggle auto-refresh (30s, off por default)
- **Effort**: ~5h CC.

### F-5 · `cron-bot-alerts` y `cron-beds24-normalize` sin heartbeat propio

- **Severity**: 🟡 should-do
- **What**: 20 GH Actions cron workflows configurados → 17 cron heartbeats en D1. Los 2 missing:
  - `cron-bot-alerts`: SÍ fire (evidence: `cron_alert_last_fired:heartbeat_stale` reciente) pero no llama `recordCronHeartbeat()` sobre sí mismo
  - `cron-beds24-normalize`: workflow existe, sin heartbeat row, sin alert row. PER_CRON_THRESHOLD_SEC tiene threshold listo pero sin baseline row la comparación `now - last < threshold` no dispara nunca
- **Where**: `apps/worker-bot/src/cron-bot-alerts.ts` + handler de beds24-normalize
- **Why it's a problem**: Classic watcher-watching gap. Si bot-alerts muere 24h, nada alerta. Si beds24-normalize falla 7d, pre-stay flow upstream va stale silentemente.
- **Greenfield**: `recordCronHeartbeat()` mandatory en cada scheduled handler. Integration test que verifique cada `.github/workflows/cron-*.yml` matchea un handler con heartbeat write. Opcional: external watcher (cron-job.org free) hitting `/internal/cron-alerts-health` cada hora.
- **Effort**: ~3h CC (2 heartbeat calls + test).

### F-6 · 12 de 37 bookings (~32%) pending welcome en 60d window

- **Severity**: 🟢 nice-to-have
- **What**: D1 query — `beds24_bookings WHERE status='booked' AND room_id!=679176 AND departure>=today-3 AND arrival<=today+60d` → 37 rows. 25 tienen welcome_sent_at, 12 no. Pending puede ser (a) muy recientes o (b) viejos con falla.
- **Where**: `welcome-auto-send` cron + `pre-stay.astro` Catch-up button + `messenger_outbound`.
- **Why**: 32% gap = ops gap (Catch-up button no clicked) y posiblemente compounds con F-1 (manychat 99.6% fail = templates routing manychat fallback fallan).
- **Greenfield**: Badge `/admin/pre-stay` top: "X bookings pending welcome > 7d → click Catch-up". Hook to daily-digest.
- **Effort**: ~2h CC.

---

## §C · Comparación findings audit committed vs follow-up

| Finding | En audit | En follow-up | Severity |
|---|---|---|---|
| Doc drift Free plan crons | ✅ C.1 | — | 🔴 |
| Response tracking 9% adoption | ✅ C.2 | — | 🔴 |
| Heartbeat stale frequency | ✅ C.3 | — | 🟡 |
| Native vs GH cron strategy | ✅ C.4 | — | 🟡 |
| `/admin/index.astro` landing vacío | ✅ C.5 | — | 🟡 |
| magic_links cleanup OK | ✅ C.6 | — | 🟢 |
| **ManyChat 99.6% failure (989 sends)** | — | ✅ F-1 | 🔴 |
| **Inbox backlog 100 unread, 4 critical, 9d** | — | ✅ F-2 | 🔴 |
| **Casa Chamán en welcome-auto-send** | — | ✅ F-3 | 🟡 |
| **conv.astro UX gaps** | — | ✅ F-4 | 🟡 |
| **Cron-bot-alerts sin heartbeat propio** | — | ✅ F-5 | 🟡 |
| **12/37 bookings pending welcome** | — | ✅ F-6 | 🟢 |

**Total combinado**: 12 findings (4 🔴, 6 🟡, 2 🟢). Sin solapamiento entre audit y follow-up.

---

## §D · Recomendación operacional priorizada (combinada)

### Critical · do before M1 (🔴)

| # | Source | Title | Effort |
|---|---|---|---|
| 1 | C.1 audit | Update doc Free plan crons | 1-2h |
| 2 | C.2 audit | Fix response tracking (Telegram inline button) | 3-4h |
| 3 | F-1 | ManyChat circuit breaker + subscriber_status | 8h |
| 4 | F-2 | Karina training v2 deploy + critical-keyword alert | 2h CC + 3h Karina |

**Total 🔴**: ~17-19h CC. Si secuencial = 2-3 días. Si paralelo = 1.5-2 días.

### Should-do · 3mo (🟡)

| # | Source | Title | Effort |
|---|---|---|---|
| 5 | C.3 audit | Heartbeat stale review | 1h |
| 6 | C.4 audit | Cron strategy ADR | 1h doc |
| 7 | C.5 audit | `/admin/index.astro` dashboard cards | 2-3h |
| 8 | F-3 | Casa Chamán filter en welcome-auto-send | 1h |
| 9 | F-4 | conv.astro reset preview + status badge | 5h |
| 10 | F-5 | Heartbeats para bot-alerts + beds24-normalize | 3h |

### Nice-to-have (🟢)

| # | Source | Title |
|---|---|---|
| 11 | C.6 audit | magic_links — leave as-is |
| 12 | F-6 | Pre-stay backlog badge (~2h) |

---

## §E · Decisión solicitada a Alex

Tres caminos para los 6 findings adicionales:

| Opción | Acción | Cuándo |
|---|---|---|
| **A** (voto WC) | Dejar follow-up aquí. WC-Platform synthesis (Day 2-3) integra audit + follow-up en `04-synthesis.md` §B/§C. | Default si no decidís nada |
| **B** | WC-Impl edita audit committed → audit v2 integrando F-1..F-6 en §C. Re-commit con changelog. | Si querés audit doc monolítico |
| **C** | 6 GH issues separados (uno por finding) en `rdm-bot`. CC pickea por prioridad. Audit/follow-up quedan como snapshot. | Si preferís tracking issue-level |

Voto WC: **A**. Audit es snapshot temporal con voice independent. WC-Platform synthesis tiene el contexto para integrar. Si CC empieza fix de 🔴 antes de synthesis, prefiero issues por finding (combina B+C).

---

## §F · Preguntas extra (más allá de las 5 del audit §G)

Del follow-up surface nuevas preguntas para Alex:

6. **ManyChat strategic**: 99.6% failure rate sugiere ManyChat saliendo, no entrando. F-1 fix agrega resilience pero la pregunta deeper: ¿WhatsApp Business Cloud (direct) es el path eventual? Si sí, F-1 es stopgap. Vale decidir antes de invertir 8h CC.

7. **Telegram channel — keep or replace?**: response tracking gap (C.2 + F-2) hace el channel menos efectivo. ¿Invertir en Telegram closure o migrar a inbox-only con Telegram opcional? Ambos válidos.

8. **F2 spec Free-plan adaptation**: ¿WC-Impl drafta F2-revision (drop Logpush, expand D1+heartbeat pattern), o WC-Platform owns la decisión post-synthesis?

9. **Critical-keyword list (F-2)**: ¿qué keywords están en `has_keywords_critical`? Verificar antes de proponer Telegram alert. Estrecha → under-fire; amplia → noise.

---

## §G · Status

| Item | Status |
|---|---|
| Audit `02-operational-audit-wc-impl.md` | ✅ committed `b8cdd92` 03:59 UTC |
| Audit announcement thread/152 | ✅ committed `688b545` ~04:30 UTC |
| Follow-up findings (this file) | ✅ committed (this commit) |
| WC-Platform synthesis `04-synthesis.md` | ⏳ Day 2-3, can integrate both |
| Alex decision §E + §F questions | ⏳ pending |

---

**Signed**: WC-Implementation, brain mode, 2026-05-21 ~05:00 MX

via Alex vote 2026-05-21 chat: "Append findings adicionales como thread/152 follow-up (no toca audit)".
