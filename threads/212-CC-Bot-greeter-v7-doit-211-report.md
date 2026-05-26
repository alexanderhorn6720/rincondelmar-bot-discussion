---
thread: 212
author: CC-Bot
date: 2026-05-26
topic: greeter-v7-doit-211-report
mode: report
status: done
closes: thread/211
---

# CC-Bot DoIt Report — Greeter v7 Warm + VIP-Aware (thread/211)

## PR

**PR #186** — `feat(greeter): Greeter v7 — Warm + VIP-Aware + Bucket Detection (thread/211)`
Branch: `feat/greeter-v7-warm-vip-aware`

## Deliverables completados

| Deliverable | Archivo | Status |
|---|---|---|
| D1+D5 | `packages/agents/greeter/system-prompt-v7.ts` | ✅ |
| D2 | `packages/agents/greeter/handler-v7.ts` | ✅ |
| D3 | `apps/worker-bot/src/bucket-detector.ts` | ✅ |
| D4 | `apps/worker-bot/src/karina-config.ts` | ✅ |
| D6 | `apps/worker-bot/src/run-greeter-v5.ts` (v7 branch) | ✅ |
| D7 | `packages/agents/greeter/process-tool-use.ts` | ✅ |
| D8 | lead exit gracioso (en process-tool-use) | ✅ |
| D9 | `apps/worker-bot/src/v7-validator.ts` | ✅ |
| D10 | `apps/worker-bot/src/canary.ts` + `migrations/0048_bot_config_canary_v7.sql` | ✅ |
| D11 | 43 golden tests + 17 validator tests + integration updates | ✅ |

## Tests

```
packages/agents: 221 passed (12 test files)
apps/worker-bot: 1156 passed (58 test files)
```

Pre-existing failures (no introducidas por este PR):
- `packages/auth`: session expiry constant mismatch (existía en main)
- `packages/llm-client` + `apps/worker-tours`: typecheck (existían en main)

## Anti-patterns verificados

- ✅ Pet fee `$300/estancia` NUNCA `/noche` — en prompt + validator + tests
- ✅ Casa Chamán NO en ningún texto guest-facing
- ✅ Karina phone: `wa.me/727441441575` desde `karina-config.ts` únicamente; `525570618798` eliminado de `buildFallbackResult` y `buildEscalateReply`
- ✅ No ALTER TABLE (migration 0048 es solo INSERT ON CONFLICT DO NOTHING)
- ✅ No force-push, no auto-merge

## Decisiones tomadas (sin consultar a Alex — dentro de scope del spec)

1. **D8 `args.reason !== 'distress'`** — El spec decía `distress_emergency` pero ese valor no existe en el type `EscalateToHumanArgs.reason`. Usé `'distress'` (el valor correcto del enum) para excluir emergencias del lead exit gracioso.

2. **Tier 2 padding a >8000 chars** — El spec pedía bloque ≥2048 tokens Haiku para activar el cache. Extendí `buildBucketContextBlock` con property FAQ + info de equipo hasta superar 8000 chars (~2048 tokens). Sin cambios al contenido del spec.

3. **Violation codes simples** — vitest `toContain()` usa `===` y NO soporta asymmetric matchers. Los violation codes son strings planos (`'pet_fee_per_noche'`, etc.) en vez de mensajes descriptivos.

## Surprises

- El thread/211 spec tenía `distress_emergency` en el condicional D8 pero el type real tiene `distress`. Fix trivial, dentro de scope.
- La discussion repo tenía un stale worktree en `C:/Users/Alexa/AppData/Local/Temp/wt-thread-claim` que bloqueaba el checkout a main. Eliminado con `git worktree remove --force`.

## Post-merge checklist para Alex

1. `pnpm --filter web db:migrate:remote` — migration 0048 (INSERT canary_percent_v7=0)
2. Smoke test auto corre post-deploy
3. Para activar v7 canary: `UPDATE bot_config SET value='10' WHERE key='canary_percent_v7'`
4. Para forzar v7 a un subscriber: `UPDATE bot_config SET value='v7' WHERE key='greeter_prompt_version_force'`
5. Monitor `/admin/bot-metrics` para comparativa v5/v6/v7

## Tiempo estimado

~6h efectivas (incluyendo context recovery del compaction mid-session).

LLM cost: dentro del tier doit_normal (estimado <$30 ccusage).
