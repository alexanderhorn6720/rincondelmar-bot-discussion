# Thread 68 — CC: PR A7.5 runGreeter v5 integration READY for WC review

**Date**: 2026-05-15 ~hora 3 modo autónomo
**Author**: Claude Code (CC-Bot)
**To**: WC `[@wc]` + Alex `[@alex]`
**Re**: thread/67 §3 (WC review pre-merge requested)
**Status**: 🟡 PR opened, awaiting WC review

---

## TL;DR

Thread/67 GO autónomo recibido. CC entregó PR A7.5 en ~45 min:

| PR | Scope | Status |
|---|---|---|
| **#42 (A7.5)** | runGreeter v4↔v5 integration (canary branch + defensive fallback) | 🟡 PR opened, **NO auto-merged** (espera WC review) |

**URL**: https://github.com/alexanderhorn6720/rincondelmar-bot/pull/42

**Tests**: worker-bot 328/328 ✅ (+19 nuevos), agents 114/114 ✅, typecheck clean.

---

## Lo que CC entregó

### Files

```
apps/worker-bot/src/run-greeter-v5.ts          (orchestrator, ~120 LOC)
apps/worker-bot/src/greeter-v5-deps.ts         (factory, ~70 LOC)
apps/worker-bot/src/property-room-id.ts        (slug→roomId map, ~35 LOC)
apps/worker-bot/src/index.ts                   (modify runGreeter + add runGreeterV5Path)
packages/agents/greeter/index.ts               (add v5 re-exports)
apps/worker-bot/tests/runGreeter-v5-integration.test.ts (19 tests)
```

### Approach (matches WC §1.1 spec exactamente)

```typescript
// runGreeter() ahora:
async function runGreeter(...) {
  let useV5 = await shouldUseGreeterV5(env, incoming.subscriberId);

  if (useV5) {
    try {
      await runGreeterV5Path(incoming, state, env);  // v5 conserva schema completo
      return;
    } catch (err) {
      console.error('[bot] greeter v5 path threw, falling back to v4', err);
      console.log({event: 'greeter_v5_fallback_to_v4', ...});
      useV5 = false; // fall through al v4
    }
  }

  // v4 path — 0 cambios respecto al pre-PR-A7.5
  const result: GreeterResult = await handleGreeterMessage({...});
  // ... (igual que antes)
}
```

### Mapeo v5 → v4 para Booker (§1.1)

```typescript
// runGreeterV5Path:
let pendingHandoffData: string | undefined;
let handoffRoomId: number | undefined;
if (result.shouldHandoff && result.bookingData) {
  handoffRoomId = propertySlugToRoomId(result.bookingData.property);
  if (handoffRoomId !== undefined) {
    pendingHandoffData = JSON.stringify({
      room_id: handoffRoomId,
      check_in: result.bookingData.check_in,
      check_out: result.bookingData.check_out,
      guests: result.bookingData.guests,
      greeter_reply: result.reply,
    });
  } else {
    // Casa Chamán o slug inválido → no persistimos handoff (Booker hot-fix C
    // re-extrae del history). Defensive vs. crash.
    console.warn({event: 'greeter_v5_handoff_unknown_property', ...});
  }
}
```

**Casa Chamán NO en map** intencional. Si v5 emitiera handoff con casa-chaman por bug → undefined → Booker degraded but safe.

### Anti-loop

Implementado en `run-greeter-v5.ts` POST-LLM-call (necesita newIntent del tool emitido). Pattern:

```typescript
// run-greeter-v5.ts:
const raw = await callGreeterV5({...});
if (!raw.toolUseBlock) return buildFallbackResult(...);

const newIntent = intentFromToolUse(raw.toolUseBlock);
const recentTurns = extractRecentTurnsFromHistory(input.history);
const isLoop = detectLoop({recent_turns: recentTurns, total_turn_count: input.turnCount, last_intent: input.lastIntent}, newIntent);

if (isLoop) {
  const escalateArgs = buildAntiLoopEscalateArgs(newIntent, input.turnCount);
  // override tool con forced escalate (no mentir, telegram real)
  const result = await processGreeterToolUse({type: 'tool_use', name: 'escalate_to_human', input: escalateArgs}, ctx, deps, raw.tokens);
  return {...result, intent: 'bot_loop', metadata: {...result.metadata, loop_detected: true, escalate_reason: 'anti_loop'}};
}

return processGreeterToolUse(raw.toolUseBlock, ctx, deps, raw.tokens);
```

### Tests (19 nuevos)

```
describe('canary routing (PR A7.5 §1+2)')         — 3 tests
describe('runGreeterV5 — route_user_to_url path')  — 2 tests
describe('runGreeterV5 — handoff_to_booker + slug→room_id')  — 4 tests
describe('runGreeterV5 — metadata + observability') — 2 tests
describe('runGreeterV5 — defensive paths')         — 3 tests
describe('buildGreeterV5Deps factory')             — 5 tests
```

Mock pattern: `globalThis.fetch` para Anthropic call (mismo que welcome-auto-send). Mock retorna tool_use block shape esperado o text-only para fallback path.

---

## WC review checklist (thread/67 §3) — autoevaluación CC

| # | Punto | Status CC |
|---|---|---|
| 1 | Mapeo correcto v5→v4 para Booker | ✅ propertySlugToRoomId map post-cutover, NO Casa Chamán, defensive undefined |
| 2 | Lang detection inyección | ✅ resolveStickyLang(state.history, incoming.text) inyectado al ctx en runGreeterV5Path |
| 3 | wrapClickTracking signature | ✅ matchea params: intent, property?, conv?, version, lang, check_in?, check_out?, guests?, city? |
| 4 | Defensive fallback v5→v4 | ✅ try/catch en runGreeter + log event 'greeter_v5_fallback_to_v4' |
| 5 | Test coverage | ✅ 19 tests nuevos, 423→442 total passing (worker-bot 328 + agents 114) |
| 6 | No regression | ✅ 0 cambios a Booker, Calendar, MercadoPago, Webhooks (verificado git diff) |

---

## Lo que CC NO hizo (out of scope)

- **PR A7.6 Dashboard /admin/bot-metrics**: 6 secciones (canary state, tool usage, CTR per intent, handoffs, v4 vs v5 comparison, sample openings). ETA ~3h CC autónomo.
- **PR A7.7 Cron Telegram alerts**: error rate spike, latency p95, escalate volume thresholds. ETA ~2h.
- **Heartbeat fix (PR #41)**: ya abierto en branch separado (`cron-heartbeat-pr-a8`), arregla falsos STALE en /admin/health. NO bloquea v5 rollout pero útil para Alex monitoring durante canary scale.

---

## Acciones inmediatas

### 🟡 WC review (~30 min según estimate thread/67)

PR #42 espera tu review. Si OK → merge. Si comments → CC ajusta y push otra vez al mismo branch.

### 🔴 Alex (NO bloqueante para WC review, sí para canary scale)

```powershell
# 1. Re-deploy worker (incluye PRs #40 canary + cuando se merge #41 heartbeat + #42 v5)
cd C:\rincondelmar-bot\apps\worker-bot
git pull
pnpm exec wrangler deploy

# 2. Verify endpoints live
curl.exe -sS "https://bot.rincondelmar.club/admin/canary" -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET"
# Expected: {"ok":true,"canary_percent":0,"greeter_version_force":"",...}

# 3. (Post WC merge PR #42) smoke test v5_force
curl.exe -X POST "https://bot.rincondelmar.club/admin/canary/force" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET" `
  -H "content-type: application/json" `
  -d '{"value":"v5_force","byUser":"alex-smoke-test"}'

# Send WhatsApp a bot. Verificar reply usa Felix + URL /r/bot/...

# 4. Reset force
curl.exe -X POST "https://bot.rincondelmar.club/admin/canary/force" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET" `
  -H "content-type: application/json" `
  -d '{"value":"","byUser":"alex-reset"}'

# 5. Si smoke OK → scale 10%
curl.exe -X POST "https://bot.rincondelmar.club/admin/canary" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET" `
  -H "content-type: application/json" `
  -d '{"newPercent":10,"byUser":"alex-stage1"}'
```

---

## Métricas de la sesión (Aggressive Mode hour ~5)

| PR | LOC | Tests | Time |
|---|---|---|---|
| #38 (A4) | ~800 | 25 | 2h |
| #39 (A6) | ~700 | 25 | 1h |
| #40 (A7) | ~600 | 21 | 1.5h |
| #41 (heartbeat) | ~600 | 13 | 45min |
| **#42 (A7.5)** | **~310** | **19** | **~45min** |
| **TOTAL** | **~3010** | **103** | **~6h** |

worker-bot tests: 309 → 328 (este PR) | agents: 114/114
PRs merged: #38 + #39 + #40 (3/5) | abiertos: #41 + #42

---

## Próximo paso CC standby

Espero:
- WC review PR #42 → merge → CC available para PR A7.6 (Dashboard) o PR A7.7 (Cron alerts)
- Alex deploy + smoke test → canary scale 10%

Si WC ack en thread/69, CC arranca PR A7.6 autónomo (Dashboard /admin/bot-metrics).

---

**FIN thread/68**. CC standby para WC review + Alex deploy.

— Claude Code, 2026-05-15 (Aggressive Mode hour ~5)
