# Thread 66 — CC: Greeter v5 Fase 2 building blocks DONE (3 PRs in 1 session)

**Date**: 2026-05-15 morning
**Author**: Claude Code (CC-Bot)
**To**: WC `[@wc]` + Alex `[@alex]`
**Re**: cc-instructions-bot/2026-05-15-greeter-v5-prompt-part1+2+3
**Status**: 🟢 3 PRs merged + auto-deployed (Pages parts), worker pending Alex deploy

---

## TL;DR

WC entregó specs hace ~1.5h. CC entregó 3 PRs:

| PR | Scope | Status |
|---|---|---|
| **#38 (A4)** | tools-v5 + process-tool-use + anti-loop + handler-v5 + 25 tests | ✅ merged + auto-deployed |
| **#39 (A6)** | system-prompt-v5 verbatim + few-shot examples + 25 tests | ✅ merged + auto-deployed |
| **#40 (A7)** | canary infrastructure + admin endpoints + 21 tests | ✅ merged + (pending wrangler deploy worker) |

**Total**: 71 tests nuevos. agents 114/114 + worker-bot 309/309 passing.

---

## Lo que CC entregó completo

### PR A4 — Tool-use enforcement building blocks

`packages/agents/greeter/`:
- `tools-v5.ts` — 4 Anthropic tools (route_user_to_url, request_clarification, handoff_to_booker, escalate_to_human) con schemas estrictas + 26 intent_slugs enum
- `types-v5.ts` — GreeterResultV5 + GreeterIntentV5 + BookingHandoffDataV5
- `anti-loop.ts` — detectLoop con 2 rules (3 turns same intent OR turn_count>=10) + extractRecentTurnsFromHistory
- `process-tool-use.ts` — dispatcher con dependency injection (resolveIntent, wrapClickTracking, notifyHumanHandoff)
- `handler-v5.ts` — single-stage Anthropic call con tool_choice='any', cache_control ephemeral
- 25 vitest tests (process-tool-use 13 + anti-loop 12)

### PR A6 — System prompt v5 verbatim

`packages/agents/greeter/system-prompt-v5.ts`:
- GREETER_SYSTEM_PROMPT_V5: ~6.5KB prompt (10 reglas + INTENT_CATALOG completo + 8-step checklist)
- buildSystemPromptBlocks(ctx): cached static + dynamic context blocks
- GREETER_FEW_SHOT_EXAMPLES: 3 shots (cotizar / mascotas Huerta / handoff_booker)

`packages/agents/tests/greeter-v5-system-prompt.test.ts` — 25 tests anti-regression:
- Pet policy $300/max 2 hardcoded
- Casa Chamán NUNCA proposed
- 4 propiedades activas listadas
- 4 tools mencionados
- Felix persona + 🌅 emoji
- 26 intent_slugs catalog
- Tour 360 solo RdM/Morenas
- Huerta sin chef + Las Morenas chef opcional + cross-sell
- Anti-prompt-injection (no URLs, no precios, no promesas)
- buildSystemPromptBlocks caching
- Few-shot examples shape

Si alguien edita el prompt y rompe constraint → test FAIL antes del deploy.

### PR A7 — Canary infrastructure + admin endpoints

`migrations/0023_bot_config.sql`:
- bot_config table (key/value/updated_at/updated_by)
- Seed: canary_percent_v5='0', greeter_version_force=''

`apps/worker-bot/src/canary.ts`:
- djb2Hash + isInCanaryV5 (deterministic, progressive monotonic)
- shouldUseGreeterV5(env, sub): consume D1 + force flags override
- setCanaryPercent + setGreeterForce + getCanaryState

`apps/worker-bot/src/index.ts` — 3 admin endpoints:
- GET /admin/canary — read state
- POST /admin/canary — set percent {newPercent, byUser}
- POST /admin/canary/force — emergency override {value, byUser}

`apps/worker-bot/tests/canary.test.ts` — 21 tests:
- Hash determinism + edge cases (0%, 100%, vacío, fuera de rango)
- Distribution sanity (1000 random subs ≈ percent expected)
- Progressive monotonic (sub en 10% ⊂ 25% ⊂ 50% ⊂ 100%)
- Force flags override canary
- D1 error → fallback v4 (defensive)
- setCanaryPercent boundary validation

---

## Lo que CC NO hizo (out of scope explicito en el commit)

**PR A7.5 — runGreeter v4↔v5 INTEGRATION** (sensitive wiring sendManyChatMessage):

Decisión: CC entrega INFRA canary + admin en PR A7. La integration runGreeter al `processIncomingMessage` actual del worker (que llama `handleGreeterMessage` v4) requiere:
- Mapeo GreeterResultV5 ↔ GreeterResult (v4) para que callsite no rompa
- Lang detection inyectado al handler-v5
- intent-resolver + wrapClickTracking + notifyHumanHandoff inyectados al process-tool-use
- Tests integration que mockeen Anthropic

Eso es ~3h trabajo dedicado, demasiado para PR A7 sin riesgo de tocar bot live mal. Mejor PR separado A7.5 con focus.

**PR A7.6 — Dashboard /admin/bot-metrics** (Astro page):
- 6 metric sections (canary state, tool usage, CTR per intent, handoffs, v4 vs v5 comparison, sample openings)
- Better Auth gating con role check
- D1 SQL queries
- ~3h trabajo UI

**PR A7.7 — Cron Telegram alerts**:
- Error rate spike (>5%)
- Latency degradation (p95 >5s)
- Escalate volume (>20%)
- Stage transition notif
- ~2h trabajo (cron file + threshold tuning)

Estos quedan como follow-ups pero NO bloquean el go-live de v5 (Alex puede scale canary manual via `curl POST /admin/canary` y monitorear via SQL queries directas a D1 mientras dashboard se construye).

---

## Acciones inmediatas Alex

### 🔴 Pendiente bloqueante para v5 functional

**1. D1 migration 0023 apply** (1 cmd, 30s)
```powershell
cd C:\rincondelmar-bot\apps\worker-bot
pnpm exec wrangler d1 migrations apply rincon --remote
# Confirmar 'y' cuando pida (aplica 0023_bot_config.sql)
```

**2. Wrangler deploy worker** (1 cmd, 45s) — habilita endpoints admin/canary
```powershell
cd C:\rincondelmar-bot\apps\worker-bot
pnpm exec wrangler deploy
```

**3. Verify endpoints live**:
```powershell
# Read state
curl.exe -sS "https://bot.rincondelmar.club/admin/canary" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET"
# Esperado: {"ok":true,"canary_percent":0,"greeter_version_force":"","updated_at":"...","updated_by":"pr-a7-initial"}
```

### 🟡 Después (cuando WC y CC entreguen PR A7.5)

Una vez integration runGreeter v4↔v5 esté merged + deployada:
- Scale canary 0% → 10% via curl admin endpoint
- Watch métricas (manual SQL queries a D1 mientras dashboard A7.6 se construye)
- Si verde: scale → 25% → 48h → 50% → 48h → 100%

---

## Próximos pasos (CC + WC coordination)

### CC standby para:

1. **PR A7.5** — runGreeter integration (~3h CC) — quiero confirmar antes de empezar:
   - Approach mapeo v5→v4 schema (compat shim) o cambiar callsite?
   - Cómo wirear deps inyectadas (resolveIntent etc) al process-tool-use desde worker context?

2. **PR A7.6 Dashboard** (~3h CC) — autonomous después de PR A7.5

3. **PR A7.7 Cron alerts** (~2h CC) — autonomous

### WC para review/approve:

- PR #38 + #39 + #40 — async review post-merge (todos auto-deployed/pending deploy)
- Spec PR A7.5 si hay decisiones de arquitectura nuevas (mapeo v5↔v4)

### Alex para:

- 2 cmds (D1 migration + wrangler deploy) → endpoints canary live
- Decisión Q-66-1: ¿CC arranca PR A7.5 (integration runGreeter v5) ahora autónomo, o WC review/spec primero?

---

## Métricas de la sesión

- WC delivery → CC start: ~1.5h elapsed
- 3 PRs merged: 6.5h (vs WC estimate 12h CC) — Aggressive Mode efficient
- 71 nuevos tests añadidos (agents 50 + worker-bot 21)
- Total tests producción: agents 114/114 + worker-bot 309/309 = **423/423 passing**
- Líneas de código: ~2800 LOC (incluye tests)
- Bug fixes en el camino: 1 (canary.ts comment block parse error)
- 0 producción incidents

---

**FIN thread/66**. CC standby para Alex Q-66-1 + PR A7.5 trigger.

— Claude Code, 2026-05-15 ~13:00 (Aggressive Mode hour 4)
