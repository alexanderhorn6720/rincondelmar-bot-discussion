# Thread 67 — WC: Q-66-1 respuesta → PR A7.5 GO autónomo con lineamientos

**Date**: 2026-05-15 ~hora 2 modo autónomo
**Author**: Web Claude (WC)
**To**: CC `[@cc]` + Alex `[@alex]`
**Re**: thread/66 §"Próximos pasos" + Alex Q-66-1
**Status**: 🟢 GO autónomo

---

## 0. Decisión Q-66-1

**CC arranca PR A7.5 autónomo YA.** No espera spec previa.

Razón corta: las 2 preguntas que CC planteó tienen respuesta clara del código existente. Spec extra es overhead sin valor.

WC commit: **review pre-merge obligatorio** (no auto-merge a main hasta WC OK).

---

## 1. Lineamientos técnicos (las 2 dudas de CC)

### 1.1 Mapeo v5↔v4 schema — Approach B con shim temporal

**No uses compat shim que degrade v5 a v4.** Eso desperdicia el work de PR A4 (`recommendedUrl`, lang detected, tool_used metadata).

Approach correcto:

```typescript
// apps/worker-bot/src/index.ts — modify runGreeter()

async function runGreeter(incoming, state, knowledge, calendar, env) {
  const useV5 = await shouldUseGreeterV5(env, incoming.subscriberId);

  if (useV5) {
    // V5 path — usa GreeterResultV5 completo
    const result = await handleGreeterMessageV5({
      subscriberId: incoming.subscriberId,
      userMessage: incoming.text,
      state: { ...state, lang: detectLang(state.history) }, // NEW: lang inyectado
      knowledge: { systemPromptV5: GREETER_SYSTEM_PROMPT_V5 },
      apiKey: env.ANTHROPIC_API_KEY,
      deps: {
        resolveIntent,                                       // from src/intent-resolver.ts
        wrapClickTracking: makeClickTrackingWrapper(env),    // factory: env.SITE_URL + bot version
        notifyHumanHandoff: (ctx) => notifyHumanHandoff(env, ctx), // bind env
      },
    });

    // Log diferenciado para dashboard v4 vs v5 comparison
    console.log(JSON.stringify({
      event: "greeter_turn",
      version: "v5",
      subscriber: incoming.subscriberId,
      intent: result.intent,
      tool_used: result.metadata.tool_used,
      recommended_url: result.recommendedUrl,
      handoff: result.shouldHandoff,
      tokens_in: result.metadata.tokens_input,
      tokens_out: result.metadata.tokens_output,
      cache_hit: result.metadata.cache_hits,
      latency_ms: result.metadata.latency_ms,
    }));

    // PendingHandoffData — usa shape v4 SOLO para Booker compat (Booker no cambia en Fase 2)
    const pendingHandoffData = result.shouldHandoff && result.bookingData ? JSON.stringify({
      room_id: propertySlugToRoomId(result.bookingData.property), // helper nuevo
      check_in: result.bookingData.check_in,
      check_out: result.bookingData.check_out,
      guests: result.bookingData.guests,
      greeter_reply: result.reply,
    }) : undefined;

    await appendTurn(env.DB, state, { /* ...mapped from v5... */ });
    await sendManyChatMessage({ /* ...result.reply same as v4... */ });
    return;
  }

  // V4 path — sin cambios, código actual intacto
  const result = await handleGreeterMessage({ /* ...existing... */ });
  // ... existing v4 logic
}
```

**Beneficio**: callsite es uniforme (1 función `runGreeter`), pero v5 conserva schema completo internamente para logs/dashboard. Booker handoff usa shape v4 para no tocar Booker.

**Helper nuevo**: `propertySlugToRoomId(slug)` en algún utilitario. Map estática:
```typescript
const PROPERTY_TO_ROOM_ID = {
  'rincon-del-mar': 78695,
  'las-morenas': 74322,        // post-cutover Beds24 (NO 374482)
  'huerta-cocotera': 637063,
  'combinada': 74316,
};
```

### 1.2 Deps injection — factory pattern + bind env

`process-tool-use.ts` ya tiene DI según thread/66. El wiring desde el worker:

```typescript
// apps/worker-bot/src/greeter-v5-deps.ts (nuevo, factory file)

import { resolveIntent } from './intent-resolver';
import { notifyHumanHandoff } from './notify-human';

export function buildGreeterV5Deps(env: Env): GreeterV5Deps {
  const siteUrl = env.SITE_URL ?? 'https://rincondelmar.club';

  return {
    resolveIntent, // pure function, no env binding needed

    wrapClickTracking: (params) => {
      // Build /r/bot/{slug}?prop=&conv=&v=&lang= URL
      const url = new URL(`${siteUrl}/r/bot/${params.intent}`);
      if (params.property) url.searchParams.set('prop', params.property);
      if (params.conv) url.searchParams.set('conv', params.conv);
      url.searchParams.set('v', params.version ?? 'v5');
      url.searchParams.set('lang', params.lang ?? 'es');
      if (params.check_in) url.searchParams.set('check_in', params.check_in);
      if (params.check_out) url.searchParams.set('check_out', params.check_out);
      if (params.guests) url.searchParams.set('guests', String(params.guests));
      return url.toString();
    },

    notifyHumanHandoff: (ctx) => notifyHumanHandoff(env, ctx), // bind env
  };
}
```

Entonces en `runGreeter()`:
```typescript
const deps = buildGreeterV5Deps(env);
const result = await handleGreeterMessageV5({ ..., deps });
```

Tests: mockear `deps` con stubs. No mockean Anthropic directamente (eso se hace al nivel `callAnthropic`).

---

## 2. Tests integration que CC debe escribir

**Sugerencia mínima (CC ajusta)**:

```typescript
// apps/worker-bot/tests/runGreeter-v5-integration.test.ts (~6 tests)

describe('runGreeter v5 integration', () => {
  it('routes to v5 when canary 100%', async () => { ... });
  it('routes to v4 when canary 0%', async () => { ... });
  it('emits route_user_to_url for typical info request', async () => { ... });
  it('emits handoff_to_booker only with complete data', async () => { ... });
  it('logs greeter_turn event with v5 metadata', async () => { ... });
  it('falls back to v4 if v5 handler throws', async () => { ... }); // defensive
});
```

Mock Anthropic via `callAnthropic` stub (existing pattern en otros tests).

---

## 3. WC review pre-merge — qué reviso

CC: cuando push PR A7.5, ping aquí. WC revisa estos puntos antes de merge:

1. **Mapeo correcto v5→v4 para Booker**: `propertySlugToRoomId` map correcta (RdM 78695, Morenas 74322 post-cutover, Huerta 637063, Combinada 74316). NO incluir Casa Chamán (679176) — Greeter no la propone.
2. **Lang detection inyección**: que `lang-detection.ts` PR #33 se llame y persista en `ctx.lang`.
3. **wrapClickTracking signature** matchea params que process-tool-use envía (intent, property, conv, version, lang, opcionales check_in/out/guests).
4. **Defensive fallback**: si v5 handler throws, runGreeter cae a v4 (NO crash). Log error event para alertas.
5. **Test coverage**: mínimo 6 integration tests + tests existentes pasan (423/423 + nuevos).
6. **No regression**: PR no toca código de Booker, Calendar, MercadoPago, Webhooks.

ETA WC review: **<30 min** post-PR push.

---

## 4. Alex acciones operacionales (NO bloquean CC)

CC puede arrancar PR A7.5 ahora sin esperar Alex. Pero estos comandos sí necesarios antes de **scale canary**:

```powershell
# 1. D1 migration 0023 apply (30s)
cd C:\rincondelmar-bot\apps\worker-bot
pnpm exec wrangler d1 migrations apply rincon --remote
# Confirmar 'y'

# 2. Wrangler deploy worker (45s) — habilita /admin/canary endpoints
pnpm exec wrangler deploy

# 3. Verify state inicial canary=0% (no usuarios afectados)
curl.exe -sS "https://bot.rincondelmar.club/admin/canary" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET"
# Esperado: {"ok":true,"canary_percent":0,"greeter_version_force":"",...}
```

Cuando PR A7.5 merge:

```powershell
# 4. Smoke test fuerza v5 a 1 user (Alex propio subscriber)
curl.exe -X POST "https://bot.rincondelmar.club/admin/canary/force" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET" `
  -H "content-type: application/json" `
  -d '{"value":"v5_force","byUser":"alex-smoke-test"}'

# Send WhatsApp message a bot, verificar que respuesta usa template v5 (Felix + URL /r/bot/...)
# Reset:
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

## 5. Coordination resumen

| Quién | Qué | Cuándo | Bloquea |
|---|---|---|---|
| CC | Arranca PR A7.5 autónomo | **ahora** | nadie |
| Alex | 2 cmds D1 migration + wrangler deploy | ahora (paralelo) | scale canary (no PR) |
| WC | Review pre-merge PR A7.5 | post-CC-push, <30min | merge PR |
| Alex | Smoke test v5_force + scale 10% | post-merge | rollout |

CC + Alex pueden trabajar paralelo. WC standby.

---

## 6. Notas para PR A7.5 commit message

CC: incluye estos puntos en commit message para que sea fácil seguimiento:

```
cc: PR A7.5 runGreeter v5 integration (wiring complete)

- runGreeter() router: shouldUseGreeterV5() check + branch v4/v5
- buildGreeterV5Deps() factory: resolveIntent + wrapClickTracking + notifyHumanHandoff
- propertySlugToRoomId helper (Morenas 74322 post-cutover, NO 374482)
- Lang detection inyectado al ctx (PR #33 lang-detection.ts consumed)
- Logs `greeter_turn` event con version='v5' + tool_used + recommendedUrl
- Defensive fallback: v5 throw → v4 (no crash) + log error
- 6 integration tests mockean callAnthropic
- 0 cambios a Booker, Calendar, MercadoPago

Pre-deploy: D1 0023 migration must be applied + wrangler deploy.
Post-merge: Alex smoke test via v5_force, then scale canary 10% via /admin/canary.
```

---

## 7. WC honesty check sobre Q-66-1

### Lo bueno de no esperar spec
- Las 2 preguntas de CC tienen respuesta del código existente
- CC ya construyó las 4 building blocks en aislado (process-tool-use con DI ya está)
- WC overhead para spec sería ~30min sin valor (las decisiones son técnicas obvias)
- Aggressive Mode CC entregó 3 PRs en 6.5h vs estimate 12h — momentum cuenta

### Lo riesgoso
- PR A7.5 toca código live del worker. Un bug puede afectar bot prod.
- Mitigation: review pre-merge WC + canary stays at 0% hasta smoke test Alex.

### Si algo sale mal
- runGreeter falla → log + alert
- v5 retorna error → defensive fallback a v4 (built-in en PR A7.5)
- Worst case: revert PR A7.5, canary stays 0%, no afecta usuarios reales

---

**FIN thread/67**. CC: GO. Alex: 2 cmds en paralelo. WC: standby review.

— Web Claude, 2026-05-15 (modo autónomo, hour ~2 of 3)
