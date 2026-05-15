# Thread 64 — CC: Alex votó Opción A — handoff a WC para spec PR A4 + A6 + A7

**Date**: 2026-05-15 morning
**Author**: Claude Code (CC-Bot)
**To**: WC `[@wc]` + Alex `[@alex]`
**Re**: thread/63 §Q-63-1 + Fase 2 trigger
**Status**: 🟢 GO Opción A — CC standby para WC spec

---

## Decisión Alex

**Q-63-1**: ✅ **Opción A — Greeter v5 ya esta semana**

Razones (paráfrasis Alex + análisis CC):
- Bot actual sigue problemático (vueltas, escala-no-responde, alucinaciones)
- Cada día delay = ~20+ leads procesados por bot v4 con bugs
- PR A6.1 post-Data-v2 es upgrade incremental, no rewrite

---

## Handoff: WC entrega specs PR A4 + A6 + A7

CC standby. Cuando WC publique en `cc-instructions-bot/2026-05-XX-greeter-v5-prompt.md`, CC arranca.

### Spec esperada (per thread/63 §3.2 + thread/50 §4 + thread/52 §4)

#### PR A4 — Catálogo intent → URL via tool-use enforcement (~4h CC + 2h WC)

CC ya tiene listo:
- `apps/worker-bot/src/intent-resolver.ts` (PR #29 — 26 intents ES + 26 EN, validation tipada)
- `apps/worker-bot/src/lang-detection.ts` (PR #33 — heurística stop-words sticky)
- `apps/worker-bot/src/click-tracking.ts` (PR #29 — endpoint /r/bot/[slug])

Falta de WC spec:
- Nuevo Anthropic tool definition: `route_user_to_url` con args `{intent_slug, opening_line, optional: property, dates, guests}`
- Tool-use enforcement: forced tool call vs optional
- Cómo el Greeter consume `intent-resolver.resolveIntent()` y emite final URL via `/r/bot/{slug}` wrapper
- Guardarrails para `opening_line` (regex o prompt rules)

#### PR A6 — Greeter v5 system prompt (~3h CC + 3h WC)

Falta de WC:
- System prompt completo v5 (Spanish + English bilingual)
- 3-5 few-shot examples (de content-drafts existentes ya que Data v2 no listo)
- Guardarrails específicos (per thread/50 §2 P2):
  - "NUNCA en opening_line: precios concretos / disponibilidad / 'Karina te contesta en X min' / amenidades específicas"
  - "SIEMPRE: 1-2 frases máximo + reconoce pregunta + link hace trabajo pesado"
- Pet policy actualizado ($300/noche max 2 per Q-56-1 ✅)
- Saludo template para 'hola' / 'buenas' (per thread/50 P3)

#### PR A7 — Canary rollout + dashboard (~2h CC, no WC spec needed)

CC autonomous:
- Canary feature flag: 10% → 25% → 50% → 100% via subscriber_id hash
- Dashboard `/admin/bot-metrics` reading `bot_link_clicks` + `human_handoff_log` D1
- Telegram notif Alex cuando canary stage cambia

---

## Greeter actual (CC discovery para preempt info)

`packages/agents/greeter/`:
- `index.ts` — orchestrator (loadKnowledge → Stage1 → calendar → Stage2 → output)
- `stage1.ts` — `extract_intent` Anthropic Haiku (max 400 tokens, temp 0.0)
- `stage2.ts` — `respond_to_user` Haiku (max 800, temp 0.3)
- `calendar.ts` — deterministic availability check
- `handoff.ts` — booker handoff logic

Output schema actual:
```typescript
interface GreeterResult {
  reply: string;          // texto a sender
  intent: 'info'|'quote'|'videos'|'handoff_booking'|'escalate'|'bot_loop';
  shouldHandoff: boolean; // → routes to Booker
  bookingData: {...};
  metadata: { tokens..., cache... };
}
```

**Cambios esperados Greeter v5** (basado en threads 50-58):
- Eliminar Stage 2 generation libre → reemplazar con tool-call enforcement
- Output incluye `recommended_url` (resolved via intent-resolver)
- `reply` = template "{opening_line}\n\n→ {recommended_url}" con click tracking wrap
- intent set expandido: agregar 'fotos', 'tour-360', 'precios', 'capacidad', 'chef', 'mascotas', 'reservar', 'contacto', 'humano' (matchea intent-resolver catalog)
- Booker handoff sigue solo para intent='reservar' (ahora deflecta a `/reservar/{property}` directo)
- pet policy contexto: $300/noche max 2 hardcoded en system prompt (no LLM hallucination)

---

## Pendientes de Alex (paralelo a WC writing spec)

🟡 No urgente — pueden ir mientras WC trabaja:
1. Visual smoke test PRs #31 + #34 + #35 (~10 min)
2. PR #32 BookingCard URL params review + merge si OK (~5 min)
3. AirBnB listings update consistency `$300/mascota` (Karina action item)

---

## Timing esperado

| Etapa | Owner | ETA |
|---|---|---|
| WC writes cc-instructions-bot/...greeter-v5-prompt.md | WC | 2-3h |
| CC reads + clarifying Q | CC | ~30min |
| CC implementa PR A4 (catálogo + tool-use) | CC | ~4h |
| CC implementa PR A6 (prompt v5 + tests) | CC | ~3h |
| CC implementa PR A7 (canary + dashboard) | CC | ~2h |
| Alex visual review canary 10% | Alex | ~1h observación |
| Canary scale 25%/50%/100% | CC | distributed días |

**Total elapsed**: 2-3 días desde WC spec ready hasta canary 100%.

---

**FIN thread/64**. WC: tu turno con cc-instructions. CC: standby.

— Claude Code, 2026-05-15 morning
