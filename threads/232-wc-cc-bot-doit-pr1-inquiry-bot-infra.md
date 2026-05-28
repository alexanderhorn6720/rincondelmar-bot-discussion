---
id: 232
author: wc
topic: cc-bot-doit-pr1-inquiry-bot-infra
status: ready-for-execution
mode: doit-handoff
created_at: 2026-05-28
supersedes: thread/222 (renumbered — collision with web-checkout megaspec + stale post payment-flow merges)
target_workstream: CC-Bot
references:
  - threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md (REV 3 — spec source of truth)
  - threads/33-guest360-architecture-phase-b-plan.md (context Phase B)
  - threads/35-cc-templates-system-for-wc.md (templates system existente)
estimated_effort: 10-14h CC autonomous
estimated_cost: $1-3 USD Anthropic (PR1 testing only, no canary auto-sends)
---

# thread/232 — DoIt CC-Bot: PR1 inquiry-bot infra

> **Renumerado de thread/222 → 232** post-verificación de estado del repo. Razón: mientras se escribía el spec, una cadena de PRs payment-flow P0 (PRs #194-#198, threads 222-231) avanzó y mergeó. Esto invalidó 3 supuestos del task original. Esta versión los corrige.

## ⚠️ CAMBIOS POST-MERGE PAYMENT-FLOW (leer primero)

La cadena payment-flow (threads 222/224/226/228/230, PRs #194-#198) **ya está mergeada a main** (2026-05-27 21:39 → 2026-05-28 03:25). Impacto en este task:

| Supuesto original (thread/222) | Realidad post-merge | Fix en thread/232 |
|---|---|---|
| Migration 0051 disponible | 🔴 PR #194 creó `0051_bookings_beds24_booking_id.sql` | **Usar 0052** (audit primero) |
| Webhook handler integration point genérico | 🟢 Es `runBeds24Normalize` en `beds24-normalize.ts` | **Integration point preciso** (ver §Integration) |
| Beds24 modify = PATCH | 🔴 PR #197 cambió a `POST /v2/bookings [{id,status}]` | **N/A para PR1** (solo mandamos messages, no modificamos bookings) |
| (no contemplado) | 🔴 Incident 2026-05-18: cada msg saliente dispara `booking_modified` webhook de vuelta (~3s) | **Anti-loop guard obligatorio** (ver §Anti-Loop) |

## CONTEXT

PR1 de la mega-spec thread/220 REV 3 — infraestructura del Airbnb inquiry response bot.

**Source of truth:** `threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md` REV 3. Leer §3.1 completo antes de empezar.

**El gap real:** 70% de la infra existe. Falta el orchestrator que escuche `beds24_events` con `status='inquiry'` y dispare: enqueue → debounce 5min → Haiku parser → composer → approval UI.

**Approval mode:** PR1 NUNCA auto-envía. Todo va a `pending_inquiry_replies` con `status='approval_pending'`. Karina/Alex revisan en `/admin/inquiry-replies` y aprueban manualmente.

## INTEGRATION POINT (preciso — verificado en código real)

El integration point NO es el webhook HTTP directo. Es el **cron normalizer** `runBeds24Normalize` en `apps/worker-bot/src/beds24-normalize.ts`.

Flujo actual (verificado):
```
Beds24 webhook → INSERT beds24_events (action_taken=NULL)
Cron → runBeds24Normalize() → SELECT events WHERE action_taken IS NULL
  → parseBeds24Booking(payload)
  → shouldNormalize(status):
      status='inquiry' → { normalize: false, reason: 'skipped_inquiry' }
      → markEvent(action_taken='skipped_inquiry')   ← AQUÍ inyectar enqueue
```

**Integration:** en `runBeds24Normalize`, cuando `decision.reason === 'skipped_inquiry'` Y `parsed.channel === 'airbnb'`, llamar `enqueueInquiryReply(env, parsed, ev)` ANTES del `markEvent`. Reutilizar el `parsed` ya disponible (no reparsear).

**Reutilizar:** `parseBeds24Booking()` ya existe y entrega `ParsedBooking` con todos los campos (roomId, channel, arrival, firstName, etc.). NO crear parser nuevo de payload.

## ANTI-LOOP GUARD (obligatorio — incident 2026-05-18)

**Incident documentado en `beds24-normalize.ts`:** cada mensaje que el bot manda a Beds24 dispara un `booking_modified` webhook de vuelta (~3s después). Esto causó 17 welcomes duplicados en mayo. La mitigación fue `ON CONFLICT DO UPDATE` que preserva campos de automation state.

**Mi inquiry bot MANDA mensajes → mismo riesgo.** Guard obligatorio:

1. **Idempotencia por `beds24_event_id` UNIQUE** ya cubre el caso "mismo evento procesado 2x".
2. **PERO** un `booking_modified` posterior tiene OTRO `event_id` con el mismo `booking_id`. El enqueue debe deduplicar por `booking_id` también: si ya existe PIR para ese `beds24_booking_id` con status NOT IN ('expired','rejected') → NO crear nuevo PIR, solo UPDATE debounce si sigue en `awaiting_processing`.
3. **El processor NUNCA debe responder a un `booking_modified` que el propio bot causó.** Filtro: solo enqueue desde eventos `booking_created` con `status='inquiry'`, NO desde `booking_modified`.

## SCOPE EXPLÍCITO

### YES (hacer en PR1):

1. **Migration 0052** (NO 0051 — ya tomado): crear tabla `pending_inquiry_replies` con schema REV 3 (ver §3.1 thread/220 — process_at, last_inbound_msg_at, bot_pause_until). **Audit primero:** `ls migrations/ | sort -V | tail -3` y tomar siguiente número real (probablemente 0052, verificar).
2. **Handler `inquiry-enqueue.ts`:** llamado desde `runBeds24Normalize`, INSERT/UPDATE PIR con `process_at = NOW + 5min`. Incluye anti-loop dedup por booking_id.
3. **Handler `inquiry-response.ts` (`processReadyInquiries`):** llamado por cron, procesa rows ready, Haiku parser + composer, sets `approval_pending`.
4. **Handler `inquiry-pause-check.ts`:** 1h time-based pause (skip si host msg en última hora, query `bot_messages_inbox source='host'`).
5. **Backup sweep:** cada 3er tick, escanea `beds24_events` con `status='inquiry'` + `action_taken='skipped_inquiry'` sin PIR row.
6. **Haiku parser prompt:** `packages/agents/src/prompts/inquiry-question-parser.ts` output JSON spec'd en §3.1.
7. **Approval UI `/admin/inquiry-replies`:** astro page + API endpoint, lista PIRs con edit msg1/msg2 + approve/reject/expire.
8. **Tests Vitest ≥85% coverage** — 11 tests del §3.1 + anti-loop test.
9. **Integration con `runBeds24Normalize`:** inyectar `enqueueInquiryReply` en el branch `skipped_inquiry` (channel airbnb only).
10. **NO templates content** — PR1 usa template stub minimal. PR2 hace polish.

### NO (fuera de scope PR1):

- ❌ Templates Phase B.2 enriched (PR2)
- ❌ Canary scaling logic (PR2)
- ❌ Auto-send a guests reales (approval mode estricto)
- ❌ Lifecycle bot activation (PR3)
- ❌ Touchpoints follow-ups T+3/T+7/T+14 (defer)
- ❌ Pre-approval auto-send (defer)
- ❌ VIP detection (Phase B.8)
- ❌ Image attachments (post-PR3)
- ❌ Sentiment tracker (defer)
- ❌ Agregar cron nuevo (REUTILIZAR el cron que llama `runBeds24Normalize`)
- ❌ Tocar código payment-flow (`webhook-mp.ts`, `beds24-direct.ts`, `beds24-release.ts`, `crons.ts` de worker-pago) — recién mergeado, NO tocar

### OUT-OF-SCOPE FINDINGS:

Si CC encuentra algo fuera de scope → **abrir issue en rdm-bot, NO arreglar inline**. Reportar en thread response.

## PRE-FLIGHT (auto-verifiable, halt only on actual failure)

```bash
# 1. Pull latest (CRÍTICO — payment-flow recién mergeado)
cd /c/dev/rdm/dev/bot
git checkout main
git pull --rebase origin main
git log --oneline -5
# Expected: top commits incluyen PRs #194-#198 (payment-flow + email)

# 2. Working tree clean
git status
# Expected: "nothing to commit, working tree clean"

# 3. Wrangler auth
npx wrangler whoami

# 4. D1 binding
npx wrangler d1 list | grep rincon

# 5. AUDIT migration number (NO asumir 0051)
ls apps/worker-bot/migrations/ | sort -V | tail -5
# Expected: 0051_bookings_beds24_booking_id.sql es el último.
# → Crear 0052_pending_inquiry_replies.sql (verificar que 0052 NO exista)

# 6. Verify integration point existe
grep -n "skipped_inquiry" apps/worker-bot/src/beds24-normalize.ts
# Expected: línea en shouldNormalize() retornando reason:'skipped_inquiry'

# 7. Verify parseBeds24Booking exportado (reutilizable)
grep -n "export function parseBeds24Booking" apps/worker-bot/src/beds24-normalize.ts
# Expected: match

# 8. Greeter v7.1 eval baseline (no romper)
cd apps/worker-bot && pnpm test -- --run greeter
# Expected: greeter tests pasan

# 9. .dev.vars existe
test -f /c/dev/rdm/dev/bot/.dev.vars && echo "OK"
```

Si cualquier check falla → HALT, reportar.

## DELIVERABLES (orden ejecutable, absolute paths)

### Step 1: Branch
```bash
cd /c/dev/rdm/dev/bot
git checkout -b feat/inquiry-bot-infra
```

### Step 2: Migration 0052 (verificar número real primero)

Crear `/c/dev/rdm/dev/bot/apps/worker-bot/migrations/0052_pending_inquiry_replies.sql` con schema REV 3 completo del thread/220 §3.1. (Si audit del pre-flight muestra que 0052 ya existe, usar el siguiente disponible.)

```bash
cd /c/dev/rdm/dev/bot/apps/worker-bot
npx wrangler d1 migrations apply rincon --local
```

NO apply remote. Alex aplica manual post-review.

### Step 3: Handlers (orden de dependencia)

3a. `packages/agents/src/prompts/inquiry-question-parser.ts` — Haiku system prompt + Zod schema
3b. `apps/worker-bot/src/inquiry-parser.ts` — call Haiku, validate output
3c. `apps/worker-bot/src/inquiry-templates.ts` — load R2 template + composer determinista
3d. `apps/worker-bot/src/inquiry-pause-check.ts` — query bot_messages_inbox host msgs, 1h logic
3e. `apps/worker-bot/src/inquiry-enqueue.ts` — entry desde runBeds24Normalize, INSERT/UPDATE PIR + anti-loop dedup
3f. `apps/worker-bot/src/inquiry-response.ts` — cron entry `processReadyInquiries` + backup sweep

### Step 4: Integration en runBeds24Normalize

En `apps/worker-bot/src/beds24-normalize.ts`, dentro de `runBeds24Normalize`, en el branch donde `decision.reason === 'skipped_inquiry'`:

```typescript
// ANTES de markEvent(skipped_inquiry):
if (decision.reason === 'skipped_inquiry' && parsed.channel === 'airbnb' && ev.event_type === 'booking_created') {
  try {
    await enqueueInquiryReply(env, parsed, ev);
  } catch (err) {
    console.error('[beds24-normalize] enqueueInquiryReply failed', ev.id, err);
    // best-effort — no rompe el batch normalize
  }
}
// existing markEvent continues
```

Nota: el filtro `event_type === 'booking_created'` es el anti-loop guard (NO responder a booking_modified).

### Step 5: Cron integration

Localizar el cron handler que llama `runBeds24Normalize` (buscar `runBeds24Normalize(` en `apps/worker-bot/src/index.ts` o el scheduled handler). Agregar después:

```typescript
await processReadyInquiries(env);
// backup sweep cada 3er tick (usar minute % 15 < 5 o contador)
```

NO agregar cron schedule nuevo.

### Step 6: Approval UI

6a. `apps/web/src/pages/admin/inquiry-replies.astro` — list view con filtros por status
6b. `apps/web/src/pages/api/admin/inquiry-replies/[id].ts` — GET, PATCH (edit msg1/msg2), POST approve/reject

### Step 7: Tests Vitest

11 tests del §3.1 PR1 (REV 3) + 1 anti-loop test ("booking_modified posterior NO crea segundo PIR"). Coverage ≥85% para nuevos handlers.

### Step 8: Self-review pre-commit

- `git diff --stat`
- `pnpm typecheck` (TS5 strict)
- `pnpm biome check`
- `pnpm test` (todos pasan, incluido greeter — no regresión)
- grep secrets plaintext

### Step 9: Smoke test local

Simular inquiry event en `beds24_events` (INSERT directo o curl webhook). Trigger `runBeds24Normalize`. Verify:
- enqueueInquiryReply crea PIR status='awaiting_processing', process_at = NOW+5min
- Trigger processReadyInquiries (manual) tras simular 5min → status='approval_pending'
- UI `/admin/inquiry-replies` muestra el PIR
- Edit msg1 → guarda; Approve → status='approved'
- **Anti-loop:** simular booking_modified del mismo booking → NO crea segundo PIR

### Step 10: Commit + PR

Commits semánticos:
- `feat(inquiry-bot): migration 0052 pending_inquiry_replies table`
- `feat(inquiry-bot): Haiku question parser + Zod schema`
- `feat(inquiry-bot): enqueue from normalize with anti-loop dedup`
- `feat(inquiry-bot): cron processor with 1h pause check`
- `feat(inquiry-bot): backup sweep + admin approval UI`
- `test(inquiry-bot): 12 tests incluyendo anti-loop + pause`

PR body (mobile-first):
- Lead con what changed + what to verify
- Reference thread/220 REV 3 §3.1 + thread/232
- Migration 0052 apply remote pendiente Alex
- Tests ≥85% coverage + greeter no regresión
- Zero auto-sends (canary 0%)
- Worker manual deploy required post-merge (memoria #5: worker-bot NO auto-deploy)

## DEFAULTS

- Encoding: ASCII shell args, UTF-8 file contents
- Conventional Commits
- Branch: `feat/inquiry-bot-infra`
- TS5 strict, Biome, Vitest + happy-dom
- D1 binding: `DB`
- R2 binding: verificar nombre real (`R2_KNOWLEDGE` o `RDM_KNOWLEDGE` — grep wrangler.toml)
- KV binding: `KV_KNOWLEDGE`
- Modelo Haiku: `claude-haiku-4-5-20251001`
- Prompt caching: ON

## EXTERNAL STATE (verify don't act)

- Payment-flow PRs #194-#198 recién mergeados → NO tocar webhook-mp.ts, beds24-direct.ts, beds24-release.ts, worker-pago/crons.ts
- `runBeds24Normalize` es el integration point → extender, no reescribir
- `bot_messages_inbox` schema: source ('guest'|'host'), booking_id, message_time, channel
- `messenger_outbound` audit table existe → usar para audit superseded_by_human
- `MESSENGER_OUTBOUND_ENABLED` flag → NO tocar (PR3)
- Greeter v7.1 LIVE → no romper eval

## CRITERIO DE EXITO

- [ ] Migration 0052 (o siguiente real) applied local D1
- [ ] 6 handlers creados
- [ ] Integration en runBeds24Normalize (branch skipped_inquiry + airbnb + booking_created)
- [ ] Anti-loop dedup por booking_id funcional
- [ ] Cron integration con processReadyInquiries + backup sweep
- [ ] Approval UI live local con edit + approve + reject
- [ ] 12 tests pasan (11 + anti-loop), coverage ≥85%
- [ ] Greeter v7.1 eval sin regresión
- [ ] Typecheck + Biome + tests verde
- [ ] Smoke test local end-to-end + anti-loop verificado
- [ ] PR abierto, body mobile-first, references thread/220 REV 3 + thread/232
- [ ] Zero secrets plaintext
- [ ] Zero auto-sends a Airbnb real

## SI TE ATORAS

- **Halt >30 min en sub-task** → para + reporta
- **Spec ambigüedad** → leer thread/220 REV 3. Si sigue ambiguo → halt + 3 opciones (A/B/C) + voto preliminar
- **Test fails ≥5x consecutivos** → halt + reporta
- **runBeds24Normalize integration unclear** → halt + reporta (el branch skipped_inquiry está en la función, línea con `decision.reason`)
- **R2/KV binding name mismatch** → grep wrangler.toml, usar nombre real
- **Cualquier cosa fuera de scope** → issue, NO inline fix
- **Tentación de tocar payment-flow code** → STOP. Es P0 recién mergeado, fuera de scope

## REPORTAR AL FINAL

Crear `threads/NNN-cc-bot-doit-232-pr1-inquiry-bot-report.md` (verificar siguiente número libre). Incluir:

1. Summary (completado o halt)
2. Files created/modified
3. Migration number usado (0052 o cuál)
4. PR URL
5. Test coverage %
6. Smoke test result (incluido anti-loop)
7. Greeter eval: ¿sin regresión?
8. Tiempo real CC vs estimate 10-14h
9. Costo Anthropic $X.XX
10. Issues abiertos (out-of-scope)
11. Followups pre-PR2
12. Lecciones aprendidas

## NOTAS IMPORTANTES

### Anti-patterns (no violar)

- NO usar `{airbnbPriceMxn}` placeholder (es net Alex, no total guest)
- NO mostrar número MXN del payload
- NO `payload.lang` para idioma respuesta (detectar via Haiku)
- NO incluir Casa Chamán (roomId 679176)
- NO romper Greeter v7.1 eval
- NO agregar cron nuevo
- NO auto-send a Airbnb real en PR1
- NO emojis Airbnb blocked: 🌅 📶
- NO commits con secrets plaintext
- NO ALTER TABLE producción durante multi-agent
- NO tocar payment-flow code (recién mergeado)
- NO responder a eventos booking_modified (anti-loop)

### Pattern matches (reutilizar código existente)

- `parseBeds24Booking()` en beds24-normalize.ts → reutilizar, NO reparsear
- `sendMessageRouted` abstrae channel → usar (PR2, no PR1)
- `messenger_outbound` audit → usar para superseded_by_human
- ON CONFLICT DO UPDATE pattern (ver upsertBooking) → mismo patrón anti-loop
- `findOrCreateGuest` pattern → referencia para queries D1
- R2 binding pattern (welcome handler) → copiar
- Test pattern Vitest (greeter tests) → copiar

### Performance budget

- Haiku call: ~800 in + 200 out = ~1500ms
- D1 query: <50ms
- Total processReadyInquiries por PIR: <2sec
- Worker CPU per tick: <5000ms (paid 50sec límite)

### Cost budget PR1

- Dev testing: ~5-10 Haiku calls = $0.05
- Smoke: ~3-5 calls = $0.02
- **Total estimate: <$1 USD**
- Exceeds 1.5× ($1.50) → halt + reporta

---

*FIN thread/232. DoIt task ready, ajustado post payment-flow merge. CC arranca cuando Alex apruebe.*

— WC, 2026-05-28
