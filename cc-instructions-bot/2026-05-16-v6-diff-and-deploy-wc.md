# V5 → V6: Diff resumido + Deploy plan

## Cambios principales

### Reglas existentes — MODIFICADAS

| Regla | V5 | V6 |
|---|---|---|
| §3 opening_line longitud | "1-2 oraciones (~30-50 palabras)" | "Hasta 150 palabras según tipo, 5 zonas opcionales" |
| §3 emojis | "1 opcional, sin abusar" | "Hasta 4 por mensaje, posición y tipo regulados" |
| §3 estructura | (no specificada) | "3 formatos: A/B/C con reglas específicas" |
| §3 voz | (genérica "WhatsApp natural") | "Anfitrión culto que vive en la costa; sí/no permitidos explícitos" |
| §3 formato WhatsApp | (no mencionado) | "Negrita `*` max 3, cursiva `_` max 2, `~` prohibido" |

### Reglas existentes — MANTENIDAS sin cambios

- §1 SIEMPRE usa tool
- §2 NO inventes URLs
- §4 Pet policy hardcoded
- §6 Idioma
- §7 Anti-loop
- §8 Booker handoff con datos completos
- §9 No promesas falsas
- §10 NUNCA Casa Chamán
- §11 BIAS contra escalate

### NUEVAS adiciones

1. **§3B Estructura de mensaje** — 5 zonas opcionales (saludo/contexto/cuerpo/cierre/url)
2. **§3C Formato A/B/C** — guía explícita de cuándo usar lista vs prosa vs bullets
3. **§3D Reglas duras de presentación** — emojis, negrita, saltos de línea, longitud
4. **§3E PROHIBIDO en opening_line** — explícito y consolidado
5. **§5 Plantilla saludo** — ACTUALIZADA con formato emoji-bullet + negrita
6. **10 ejemplos few-shot** — saludo (ES/EN), precios, disponibilidad, mascotas, bodas, como-llegar, queja, escalate, comparación

### REMOVIDAS

- Plantilla genérica saludo EN antigua ("Hi! I'm Felix, the Rincón del Mar assistant 🌅. Looking for info on our houses, dates, prices, or something specific?") — reemplazada por plantilla con 4 villas estructuradas

---

## Stats comparativas

| Métrica | V5 | V6 | Delta |
|---|---|---|---|
| Líneas | 290 | 558 | +93% |
| Chars | 12,688 | 21,075 | +66% |
| Tokens estimados | ~3,172 | ~5,268 | +66% |
| Few-shot examples | 1 (saludo) | 10 | +9 |
| Costo extra por turno (sin cache) | base | +~$0.002 | trivial |
| Costo extra por turno (con cache) | base | +~$0.0002 | nulo |

Con prompt caching activo (que ya tienen per V5 stack), el costo extra es despreciable.

---

## Plan de deploy

### Pre-requisitos

- [ ] Tú aprobaste el V6 completo
- [ ] CC-Bot tiene acceso al repo `rincondelmar-bot`
- [ ] Worker `rincon-bot` en producción tiene canary infrastructure (per memory: canary 50% live)

### Pasos para CC

1. **Crear archivo** `packages/agents/greeter/system-prompt-v6.ts`:
   ```typescript
   export const GREETER_SYSTEM_PROMPT_V6 = `...contenido del MD...`;
   ```
   (escapar backticks como `\``)

2. **Update import** donde se usa `GREETER_SYSTEM_PROMPT_V5`:
   - Mantener V5 import (no borrarlo todavía)
   - Agregar V6 import
   - Lógica: si `KV_BOT_CONFIG` flag `greeter_prompt_version === 'v6'` → usa V6, else V5

3. **KV config**:
   - Agregar key `greeter_prompt_version` a `rdm-bot-config` KV
   - Initial value: `"v5"` (sin cambio en producción)

4. **Test local** con `wrangler dev`:
   - Trigger 8 dry-run scenarios via curl
   - Verificar tool_calls correctos

5. **Deploy a producción**:
   - `wrangler deploy`
   - V5 sigue activo (KV flag = v5)

6. **Cutover gradual via KV**:
   - **Fase A**: KV flag = v6 solo para suscriptor de prueba (Alex) durante 24h
   - **Fase B**: KV flag = v6 para 10% tráfico vía hash(subscriber_id) — 48h observación
   - **Fase C**: 50% — 48h observación
   - **Fase D**: 100% si métricas OK

### Métricas a monitorear (en cada fase)

- `tool_calls` distribución (route/clarify/handoff/escalate) — should ~match V5 pattern
- `escalate_rate` — should stay < 2% (target del prompt)
- `avg_opening_line_chars` — esperado ~250-500 (vs V5 ~80-150)
- Mensajes que excedan 150 palabras — should = 0
- User replies positivos (proxy: % de conversaciones con 3+ turnos = engagement)

### Rollback

Si métricas degradadas:
```
wrangler kv:key put --namespace-id=<id> greeter_prompt_version v5
```
Instant rollback sin redeploy.

---

## Riesgos residuales documentados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Modelo inventa amenities | Media | Medio | Few-shot adicional post-launch si se observa |
| `\n\n\n` triple breaks | Baja | Bajo (estético) | Post-processing en worker que normalice |
| Emojis > 4 | Baja | Bajo (visual) | Counter visual en logs |
| Slang costeño excesivo | Baja | Medio (brand) | Few-shot enseña el dial, monitorear muestras |
| Sobreuso de negrita | Media | Bajo | Post-processing limit en worker |

---

## Definition of Done

V6 está "done" cuando:

- [x] System prompt V6 escrito y revisado
- [x] 10 few-shot examples cubren intents críticos
- [x] Dry runs simulados pasan 8/8 tests
- [ ] Tú aprobaste el contenido completo
- [ ] CC implementa en branch `feat/greeter-v6-prompt`
- [ ] Tests locales pasan (8 scenarios)
- [ ] Deploy a producción con flag KV en v5 (no impact yet)
- [ ] Fase A canary (Alex only) 24h sin issues
- [ ] Fase B 10% canary 48h, métricas OK
- [ ] Fase D 100% — V6 reemplaza V5 completamente
- [ ] V5 archived en `system-prompt-v5.ts.bak`
