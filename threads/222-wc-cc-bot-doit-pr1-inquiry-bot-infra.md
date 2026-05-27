---
id: 222
author: wc
topic: cc-bot-doit-pr1-inquiry-bot-infra
status: ready-for-execution
mode: doit-handoff
created_at: 2026-05-27
target_workstream: CC-Bot
references:
  - threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md (REV 3 — spec source of truth)
  - threads/33-guest360-architecture-phase-b-plan.md (context Phase B)
  - threads/35-cc-templates-system-for-wc.md (templates system existente)
estimated_effort: 10-14h CC autonomous
estimated_cost: $1-3 USD Anthropic (PR1 testing only, no canary auto-sends)
---

# thread/222 — DoIt CC-Bot: PR1 inquiry-bot infra

## CONTEXT

PR1 de la mega-spec thread/220 REV 3 — infraestructura del Airbnb inquiry response bot.

**Source of truth:** `threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md` REV 3. Leer §3.1 completo antes de empezar. Esta task es el handoff ejecutable.

**El gap real:** 70% de la infra existe. Falta el orchestrator que escuche `beds24_events.status='inquiry'` y dispare flujo: webhook enqueue → debounce 5min → Haiku parser → composer → approval UI.

**Approval mode:** PR1 NUNCA auto-envía. Todo va a `pending_inquiry_replies` con `status='approval_pending'`. Karina/Alex revisan en `/admin/inquiry-replies` y aprueban manualmente.

## SCOPE EXPLÍCITO

### YES (hacer en PR1):

1. **Migration 0051:** crear tabla `pending_inquiry_replies` con schema REV 3 (ver §3.1 thread/220 — incluye process_at, last_inbound_msg_at, bot_pause_until)
2. **Handler `inquiry-enqueue.ts`:** llamado por webhook al recibir inquiry, hace INSERT/UPDATE PIR con `process_at = NOW + 5min`
3. **Handler `inquiry-response.ts` (`processReadyInquiries`):** llamado por cron `*/5min` existente, procesa rows ready, calls Haiku parser + composer, sets `approval_pending`
4. **Handler `inquiry-pause-check.ts`:** lógica 1h time-based pause (skip si host msg en última hora)
5. **Backup sweep:** cada 3er tick del `*/5min`, escanea `beds24_events` sin PIR row asociado
6. **Haiku parser prompt:** `packages/agents/src/prompts/inquiry-question-parser.ts` con output JSON spec'd en §3.1
7. **Approval UI `/admin/inquiry-replies`:** astro page + API endpoint, lista PIRs con edit msg1/msg2 + approve/reject/expire
8. **Tests Vitest ≥85% coverage** — incluye los 11 tests listados en §3.1 PR1 tests (REV 3)
9. **Integration con webhook Beds24 existente:** donde actualmente hace `action_taken='skipped_inquiry'`, ahora hace ese log + llama `enqueueInquiryReply`
10. **NO templates content** — PR1 usa template stub minimal. PR2 hace polish.

### NO (NOT hacer en PR1, fuera de scope):

- ❌ Templates Phase B.2 enriched (eso es PR2, Alex polish + Karina training)
- ❌ Canary scaling logic (PR2)
- ❌ Auto-send a guests reales (PR1 = approval mode estricto)
- ❌ Lifecycle bot activation (PR3)
- ❌ Touchpoints follow-ups T+3/T+7/T+14 (defer)
- ❌ Pre-approval auto-send (defer)
- ❌ VIP detection (Phase B.8)
- ❌ Image attachments (post-PR3)
- ❌ Sentiment tracker (defer)
- ❌ Cambiar cron schedule (REUTILIZAR `*/5min` existente, NO agregar nuevo cron)

### OUT-OF-SCOPE FINDINGS:

Si CC encuentra algo fuera de scope durante ejecución → **abrir issue en rdm-bot, NO arreglar inline**. Reportar en thread response al final.

## PRE-FLIGHT (auto-verifiable, halt only on actual failure)

```bash
# 1. Verify en rama main, working tree clean
cd /c/dev/rdm/dev/bot
git status
# Expected: "On branch main, nothing to commit, working tree clean"

# 2. Verify Wrangler installed + auth
npx wrangler whoami
# Expected: alex@... email

# 3. Verify D1 binding existe
npx wrangler d1 list | grep rincon
# Expected: rincon (UUID d81622d7-...)

# 4. Verify migrations dir + último número
ls apps/worker-bot/migrations/ | sort -V | tail -5
# Expected: 0050_... como último. Crear 0051_... nuevo.

# 5. Verify Greeter v7.1 eval baseline (no romper)
cd apps/worker-bot
pnpm test -- --run greeter
# Expected: tests greeter pasan (no regresion)

# 6. Verify .dev.vars existe (no exponer)
test -f /c/dev/rdm/dev/bot/.dev.vars && echo "OK"
# Expected: "OK"
```

## DELIVERABLES (en orden ejecutable, absolute paths)

### Step 1: Branch + setup
```bash
cd /c/dev/rdm/dev/bot
git checkout -b feat/inquiry-bot-infra
```

### Step 2: Migration 0051

Crear `/c/dev/rdm/dev/bot/apps/worker-bot/migrations/0051_pending_inquiry_replies.sql` con schema REV 3 completo del thread/220 §3.1.

Apply local:
```bash
cd /c/dev/rdm/dev/bot/apps/worker-bot
npx wrangler d1 migrations apply rincon --local
```

NO apply remote todavía. Alex aplica manual post-review.

### Step 3: Handlers (en orden de dependencia)

3a. `packages/agents/src/prompts/inquiry-question-parser.ts` — Haiku system prompt + Zod schema output
3b. `apps/worker-bot/src/inquiry-parser.ts` — call Haiku, validate output
3c. `apps/worker-bot/src/inquiry-templates.ts` — load R2 template + composer determinista
3d. `apps/worker-bot/src/inquiry-pause-check.ts` — query bot_messages_inbox host msgs, 1h logic
3e. `apps/worker-bot/src/inquiry-enqueue.ts` — webhook entry point, INSERT/UPDATE PIR
3f. `apps/worker-bot/src/inquiry-response.ts` — cron entry point `processReadyInquiries` + backup sweep

### Step 4: Webhook integration

Modificar handler existente Beds24 webhook (buscar `action_taken='skipped_inquiry'`) — agregar call a `enqueueInquiryReply` antes del skip log.

### Step 5: Cron integration

Modificar handler del cron `*/5min` existente — agregar call a `processReadyInquiries`. Detectar tick mod 3 para backup sweep.

### Step 6: Approval UI

6a. `apps/web/src/pages/admin/inquiry-replies.astro` — list view con filtros por status
6b. `apps/web/src/pages/api/admin/inquiry-replies/[id].ts` — GET, PATCH (edit msg1/msg2), POST approve/reject

### Step 7: Tests Vitest

Crear los 11 test cases del §3.1 PR1 tests (REV 3). Coverage objetivo ≥85% para los nuevos handlers.

### Step 8: Self-review pre-commit

- Diff completo via `git diff --stat`
- Run `pnpm typecheck` (TS5 strict)
- Run `pnpm biome check`
- Run `pnpm test` (todos pasan)
- Verify NO secrets plaintext via grep

### Step 9: Smoke test local

Simular inquiry payload con curl POST al webhook local. Verify:
- PIR row creado con status='awaiting_processing', process_at = NOW + 5min
- Después de 5min (o trigger manual cron) → status='approval_pending'
- UI `/admin/inquiry-replies` muestra el PIR
- Edit msg1 → guarda
- Approve → status='approved'

### Step 10: Commit + PR

Commits semánticos (conventional):
- `feat(inquiry-bot): migration 0051 pending_inquiry_replies table`
- `feat(inquiry-bot): Haiku question parser + Zod schema`
- `feat(inquiry-bot): enqueue handler with 5min debounce`
- `feat(inquiry-bot): cron processor with 1h pause check`
- `feat(inquiry-bot): backup sweep every 3rd tick`
- `feat(inquiry-bot): admin approval UI`
- `test(inquiry-bot): 11 test cases incluyendo pause + debounce`
- `docs(inquiry-bot): handler README en apps/worker-bot/src/`

PR body:
- Lead with what changed + what to verify (mobile-first)
- Reference thread/220 REV 3 §3.1
- Reference thread/222 (esta task)
- Migration 0051 apply remote pendiente Alex (manual)
- Tests pass: ≥85% coverage
- Zero auto-sends (canary 0%)
- Worker version bumped + manual deploy required post-merge (memoria #5)

## DEFAULTS (aplicar unless overridden)

- Encoding: ASCII shell args, UTF-8 file contents
- Commit format: Conventional Commits (feat/fix/chore/test/docs)
- Git attribution: inherit alex@... unless specified
- Branch: `feat/inquiry-bot-infra` (consistente con spec)
- TS5 strict
- Biome formatter
- Vitest + happy-dom
- D1 binding: `DB` (consistent con existing)
- R2 binding: `R2_KNOWLEDGE` (consistent)
- KV binding: `KV_KNOWLEDGE` (consistent)
- Modelo Haiku: `claude-haiku-4-5-20251001`
- Prompt caching: ON (ephemeral cache para system prompt)

## EXTERNAL STATE (verify don't act)

- Beds24 webhook ya está LIVE → integration point, NO recrear
- `bot_messages_inbox` ya recibe guest+host msgs → query existing schema
- `messenger_outbound` audit table ya existe → no recrear
- `MESSENGER_OUTBOUND_ENABLED` flag global → NO tocar (PR3 activation)
- Worker version `879b186f` LIVE post-thread/217 → no romper Greeter eval

## CRITERIO DE EXITO

- [ ] Migration 0051 applied local D1
- [ ] 6 handlers creados (parser, templates, pause-check, enqueue, response, prompt)
- [ ] Webhook integration con `enqueueInquiryReply` LIVE local
- [ ] Cron integration con `processReadyInquiries` + backup sweep LIVE local
- [ ] Approval UI `/admin/inquiry-replies` LIVE local con edit + approve + reject
- [ ] 11 tests pasan, coverage ≥85%
- [ ] Typecheck + Biome + tests verde
- [ ] Smoke test local end-to-end exitoso
- [ ] PR abierto con body mobile-first + references a thread/220 REV 3 + thread/222
- [ ] Zero secrets plaintext en commits
- [ ] Zero auto-sends a Airbnb real

## SI TE ATORAS

- **Halt >30 min en sub-task** → para + reporta en thread response
- **Spec ambigüedad** → leer thread/220 REV 3 sección relevante. Si sigue ambiguo, halt + reporta con 3 opciones (A/B/C) y voto preliminar tuyo
- **Test fails ≥5 intentos consecutivos** → halt + reporta
- **Schema D1 incompatibility** → halt, NO ALTER TABLE producción
- **Beds24 webhook handler hard to find** → halt + reporta (Alex puede apuntar al archivo)
- **Cualquier cosa fuera de scope** → abrir issue en rdm-bot, NO inline fix

## REPORTAR AL FINAL

Crear `threads/NNN-cc-bot-doit-222-pr1-inquiry-bot-report.md` con:

1. **Summary:** ¿completado o halt?
2. **Files created/modified:** lista
3. **PR URL:** GitHub link
4. **Test coverage:** % final
5. **Smoke test result:** ¿pasó end-to-end?
6. **Migration status:** local applied, remote pendiente
7. **Tiempo real CC:** vs estimate 10-14h
8. **Costo Anthropic:** $X.XX
9. **Issues abiertos (out-of-scope findings):** lista
10. **Followups recomendados pre-PR2:** lista
11. **Lecciones aprendidas:** lista

## NOTAS IMPORTANTES

### Anti-patterns documentados (no violar)

- NO usar `{airbnbPriceMxn}` placeholder (REV 2 fix)
- NO mostrar número MXN del payload (es net Alex, no total guest)
- NO `payload.lang` para idioma respuesta (mintió ej Ana Karen)
- NO incluir Casa Chamán (roomId 679176) en cualquier filtro
- NO romper Greeter v7.1 eval (verificar baseline antes y después)
- NO agregar cron nuevo (reutilizar `*/5min` existente)
- NO auto-send a Airbnb real en PR1 (approval mode estricto)
- NO emojis Airbnb blocked: 🌅 📶
- NO commits con secrets plaintext
- NO ALTER TABLE durante multi-agent execution

### Pattern matches (validar con código existente)

- `sendMessageRouted` ya abstrae channel — usar
- `messenger_outbound` audit table ya existe — usar para audit `superseded_by_human`
- R2 binding pattern existente — copiar de welcome handler
- KV_KNOWLEDGE refresh 2h pattern — heredar
- Drizzle ORM patterns — consistente con migrations existentes
- Test pattern Vitest + happy-dom — copiar de Greeter tests

### Performance budget

- Haiku call: ~800 tokens in + 200 out = ~1500ms latencia
- D1 query: <50ms
- R2 fetch template: <100ms
- Total `processReadyInquiries` por PIR: <2sec
- Worker CPU per cron tick: <5000ms (paid plan 50sec hard limit)

### Cost budget PR1

- Testing dev: ~5-10 Haiku calls = $0.05
- Smoke test: ~3-5 calls = $0.02
- **Total estimate PR1: <$1 USD**
- Si excede 1.5× = $1.50 → halt + reporta

---

*FIN thread/222. DoIt task ready. CC arranca cuando Alex apruebe.*

— WC, 2026-05-27
