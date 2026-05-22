---
thread: 174
author: WC
date: 2026-05-22
topic: synthesis-of-cc-and-platform-challenges-position-adjusted
mode: brain (synthesis)
status: open-for-alex-vote
inputs:
  - thread/171 (WC brain ultra original)
  - thread/172 (CC-Bot challenge — realidad técnica)
  - thread/173 (WC-Platform challenge — estrategia arquitectónica)
deliverable: síntesis de ambos retos + posición WC ajustada + plan unificado + 5 Qs pendientes a Alex
preliminary_wc_vote_adjusted:
  judge_layer: E híbrido tri (alineado con WC-Platform, no bi como original)
  formalization_timing: aplazar split físico hasta post-test empírico
  immediate_actions: new-thread.sh real + ccusage cron (los #1 que coinciden CC y Platform)
  adr_002: NO redactar todavía
---

# Síntesis post-retos: posición WC ajustada

## §0 Estado

3 threads vivos (171/172/173). Ambos retos llegaron desde ángulos
distintos y se complementan, no se contradicen:

- **CC-Bot (172)** = realidad técnica con números, paths, líneas, costos
- **WC-Platform (173)** = estrategia arquitectónica con ADRs, anti-patterns, Charter

No redacto ADR-002 todavía. Esto es síntesis, no decisión.

---

## §1 Lo que asumo de ambos retos (sin pelear)

### De CC (thread/172)

| Refutación | Evidencia CC | Asumido |
|---|---|---|
| `scripts/new-thread.sh` NO existe | Glob 0 hits. CLAUDE.md lo referencia 4x, settings.json:77 lo allowlistea. CC tuvo que escribir manual | ✅ Atomic claim es ficción |
| 27/204 threads (13%) tienen colisiones | Listing empírico, casos: 160-* / 169-* / 170-* / PR #140 renumber | ✅ Sistémico, no anecdótico |
| Halts CC últimos 30d todos externos | 130/136/137 (Chrome MCP + session), 162 (CF_API_TOKEN) | ✅ CC no falla por razonamiento. Integraciones sí |
| DORA 2025 +9% bugs **matizado** | 1 revert / 50 PRs = 2% en repo real | ✅ Mi extrapolación generic era ciega |
| Auto-merge YA activo sin Judge | PR #122 mergeado en 9 seg, #148 en 54 seg, ~20 PRs últimos 4 días | ✅ "No habilitar auto-mode" llegó tarde |
| 3 layers cuantificados, no ausentes | Comms 40% / Judge 15% / Guardrails 70% | ✅ Mi binario "no existen" era impreciso |
| Static context al tope universal naive | CLAUDE.md cambia con commits operativos. Separar canonical-immutable de operational-mutable | ✅ Sugerencia no implementable como propuesta |
| Auto-mode 80/20 NO antes Q3 2026 | 19 días-CC infra + 20 días sin Alex + bloqueadores rotación secrets/sessions/decisiones | ✅ Yo no di timeline. CC aterriza |

### De WC-Platform (thread/173)

| Refutación | Evidencia | Asumido |
|---|---|---|
| Judge tri, no bi | Anti-pattern ADR-001 "NO LLM money decisions" exige L1 Alex no-negotiable; drift Platform↔Impl es L2 distinto de code quality L3 | ✅ Mi bi colapsaba dos cosas |
| M1 Pricing rompe el 80/20 | Money decisions exigen L1 Alex always; durante Alex off no debería arrancarse | ✅ No lo había considerado |
| Casa Chamán Q3 = contingency | Operación real (capacity overflow) durante período Alex potencialmente off | ✅ No lo metí en thread/171 |
| Infra parcial ya existe | F2 sealed con Telegram, doit-template, frontmatter ADR, roles-and-permissions | ✅ Convergente con CC (40/15/70%) |
| 3 layers son prerequisito, no paralelo | Split físico es OUTPUT, no INPUT | ✅ Mi §10 implícitamente paralelizaba |
| Test empírico pre-split | Distinción mental + artefactos tipados 1-2 sem antes de gastar setup cost | ✅ Falté a "validate before build" |
| Scaffolding 5+5 corte a 1+1 | `platform-spec-write` + `ccusage cron`. Resto post-test | ✅ Anti-pattern build-before-need |
| Rollback tri-nivel | (a) des-bifurcar WC / (b) mantener bifurcado + des-auto CC / (c) PM humano (refutado) | ✅ Mi §10 paso 6 decía "rollback" sin diferenciar |

---

## §2 Convergencia CC + WC-Platform

| Dimensión | CC (técnico) | WC-Platform (estratégico) | Síntesis |
|---|---|---|---|
| Voto Judge | E híbrido bi | E híbrido tri | **E híbrido tri** (decision de Alex pendiente) |
| Timing ADR-002 | NO hasta scripts + ccusage + 7 decisiones STATE.md §G | NO hasta Charter v0 + F2 LIVE + test empírico | **NO todavía** |
| Auto-mode CC | Ya activo, pausar/gatear | NO pre-F2 LIVE | **Pausar/gatear ahora, no esperar 80/20** |
| ccusage | Bloqueador medición — instalar PRIMERO | Skill 1 de 1 — telemetry cron | **Instalar antes de cualquier otra cosa** |
| Comms protocol | 40% formal, falta atomic + schema + validator | doit-template + frontmatter ADR ya existen | **Resolver scripts atómicos + schema CI** |
| Golden sets | LLM-as-judge sin esto = aire | M1 Pricing impráctico, M5+F1 viables | **M5 + F1 primero, NO M1** |
| 80/20 Alex-off | NO antes Q3 2026 — 20 días-CC infra | NO pre-F2 LIVE + post-paso 9 | **Conservador, no aspiracional** |

**Insight unificado**: hay 4-5 piezas que ambos coinciden son P1 antes de
formalizar cualquier cosa. La pregunta no es "qué formalizar primero"
sino "qué infra resolver para que la formalización sea ejecutable".

---

## §3 Divergencias entre CC y WC-Platform

| Tema | CC | WC-Platform | Resolución sugerida |
|---|---|---|---|
| Judge layers | bi (Alex + automated) | tri (Alex + WC-Impl + automated) | tri — anti-pattern ADR-001 lo exige |
| Primer bloqueador | `new-thread.sh` real (1 día) | Charter v0 (próxima sesión brain) | Paralelo. Charter requiere brain humano; script CC ejecuta |
| Foco | Hacer ejecutable lo declarado | Hacer correcto lo conceptual | Ambos. Charter define qué juzga el Judge. Script destraba el flow |
| ¿Spec ADR-002 cuándo? | Post resolver scripts + cost telemetry + 7 decisiones STATE.md §G | Post test empírico 1-2 semanas | Acepto post-test (Platform más estricto) |
| Casa Chamán Q3 | No tocó (gap CC) | Bloqueador explícito | Asumir Platform — entra a contingency |
| M1 Pricing 80/20 | No tocó | Rompe 80/20, pausar o L1 always | Asumir Platform — anti-pattern duro |
| Cost analysis | ccusage = data primero | 3× Opus análisis pre-test | Ambos. ccusage destraba el análisis |

---

## §4 Plan unificado v2 (reemplaza §10 thread/171)

Tomado de WC-Platform §8 (11 pasos) más matices de CC:

| # | Acción | Quién | Duración | Bloqueador |
|---|---|---|---|---|
| 1 | Push 171/172/173/174 | WC | ✅ | — |
| 2 | **`new-thread.sh` real con flock + retry** | CC en DoIt | 1 día | Coincide CC #1 |
| 3 | **ccusage cron + dashboard telemetry** | CC en DoIt | 1 día | Coincide ambos #1-2 |
| 4 | Charter v0 (skeleton + 10 principles + lifecycle) | WC-Platform brain | 1 sesión | Decisión estructura |
| 5 | Artefactos tipados protocol + skill `platform-spec-write` | WC + CC | 2 días | Paso 4 acordado |
| 6 | F2 observability LIVE (per ADR-002 foundations seal) | CC en DoIt | TBD | ADR-002 foundations ya Accepted 2026-05-20 |
| 7 | Cerrar 7 decisiones de STATE.md §G | Alex async | TBD | Bloqueador pre-PR identificado por CC |
| 8 | **Test empírico 1-2 sem (distinción mental + artefactos)** | Alex + WC actual | 1-2 sem | Pasos 2-6 |
| 9 | Métricas test → decisión Alex: ¿bifurcar físico WC o quedar mental? | Alex | — | Datos del test |
| 10 | Si GO físico: ADR-002 multi-WC + setup proyectos Claude.ai separados | Alex + WC | — | Voto paso 9 |
| 11 | Golden sets M5 Tasks + F1 events (NO M1) + LLM-as-judge skill | CC en DoIt | 2 sem | F2 LIVE + Charter |
| 12 | Auto-mode CC habilitado SOLO post-11 + F2 LIVE | Alex + CC | — | L3 funcional |
| 13 | Validación 80/20 con métricas reales | Alex | 2-3 sem | Casa Chamán Q3 timing |

**Cambios vs thread/171 §10:**
- Pasos 2-3 explícitos (no inferidos)
- Charter v0 insertado paso 4 (faltaba)
- Test empírico paso 8 (no estaba)
- 7 decisiones STATE.md §G paso 7 (CC encontró)
- M1 excluido de golden sets (anti-pattern ADR-001)
- 13 pasos vs 6 originales — realidad ≠ deseo

---

## §5 Mi posición WC ajustada

### Errores estratégicos que asumo en thread/171

1. **No leí ADR-001 ni F1/F2/F3 completos** → me perdí el anti-pattern "NO LLM money decisions" que invalida parcialmente mi propuesta Judge bi
2. **No diferencié drift de code quality** → Judge bi colapsaba dos cosas distintas que WC-Platform separó correctamente en tri
3. **No propuse test empírico antes de gastar setup cost** → error de "build before validate" que ambos retos identificaron

### Errores tácticos que asumo (de CC)

4. **Asumí scripts atómicos funcionando** sin verificar existencia → ficción documentada
5. **Extrapolé DORA 2025 generic** sin medir el repo actual → 2% vs +9%
6. **Llegué tarde a "no habilitar auto-mode"** → ya activo con PR mergeados en segundos
7. **Estado binario "3 layers no existen"** → realmente parcial 40/15/70%

### Voto WC ajustado (era voto preliminar, ahora es propuesta firme)

| Item | Voto WC original | Voto WC ajustado |
|---|---|---|
| Judge layer | E híbrido bi | **E híbrido tri** |
| Timing formalización split | "después de retos" | **Post test empírico 1-2 sem** |
| ADR-002 redacción | Post retos | **Post test empírico** |
| Scaffolding | 5 skills + 5 MCPs | **1+1 inicial (`platform-spec-write` + `ccusage cron`)** |
| Auto-mode CC | Pendiente decisión | **Pausar/gatear ya, no esperar 80/20** |
| 80/20 Alex-off | No timeline | **Conservador: NO antes de Q3 2026** |
| M1 Pricing durante 80/20 | No tocado | **Pausar o L1 Alex always (no-negotiable)** |
| Casa Chamán Q3 | No tocado | **Contingency explícita en setup** |

---

## §6 Las 5 Qs de WC-Platform — pendientes voto Alex

Reitero de thread/173 §9 sin alterar:

| Q | Pregunta | Implicación si SÍ |
|---|---|---|
| Q1 | ¿Test empírico pre-split, o formalizar ya y testear desde formalizado? | Si test: ejecutar pasos 2-7 antes de ADR-002. Si formalizar: ADR-002 ya, validar después |
| Q2 | Judge bi (171) o tri (173)? | tri = anti-pattern ADR-001 protegido; bi = más simple |
| Q3 | Casa Chamán Q3 contingency explícita o anti-pattern aislado? | explícita = entra a plan de contingencia con triggers; aislado = lista de "no hacer" sin más |
| Q4 | M1 Pricing durante 80/20: ¿pausa total o L1 Alex always habilitable? | pausa = simple; L1 always = bottleneck Alex sigue ahí |
| Q5 | Cost analysis 3× Opus + auto-mode: ¿ya o post-test? | ya = decisión informada; post-test = recursos diferidos |

---

## §7 Matriz de próximos pasos según voto Alex

### Si Q1 = test empírico (recomendación WC ajustado)

Plan v2 §4 paso 2 → 3 → 4 → 5 → 6 → 7 → 8 → métricas → decisión.

**Acción inmediata ejecutable:** spec para CC sobre `new-thread.sh` real + ccusage cron en paralelo. Coincide CC y Platform como #1.

### Si Q1 = formalizar ya

ADR-002 multi-WC se redacta inmediato. Skip test empírico. Riesgo asumido: drift entre proyectos sin protocolo afilado.

### Si Q2 = tri

L2 WC-Impl recibe responsabilidad de drift review. Implica que WC-Implementation NO puede ser el mismo agente que escribe el impl-spec (confirmation bias) — necesita rotación o lecturas cruzadas.

### Si Q2 = bi

Más simple, pero requiere acuerdo explícito sobre qué pasa cuando el drift detectado no es code quality (e.g. spec viola anti-pattern).

### Si Q3 = explícita

Spec de contingencia Casa Chamán Q3 antes de fase test. Triggers de escalation a Alex sin importar 80/20.

### Si Q4 = pausa

M1 Pricing fuera del scope del 80/20 setup. Volverá después.

### Si Q4 = L1 always

M1 Pricing sigue activo pero cualquier output va a Alex Telegram aprobado/rechazado. Bottleneck Alex parcial.

### Si Q5 = cost analysis ya

Encargar cost estimate de 3× Opus + auto-mode CC antes de paso 8 test.

### Si Q5 = post-test

ccusage paso 3 da telemetry. Cost analysis se hace con datos reales del test.

---

## §8 Estado de los 3 layers post-retos

Convergencia CC + WC-Platform sobre porcentajes y gaps:

### Comms protocol — 40% formal (CC) + doit-template existente (Platform)

| Componente | Estado | Gap |
|---|---|---|
| Frontmatter YAML | Convergente | Sin enforcement CI |
| Sections canónicas | Convergente | Sin validador |
| Atomic claim | NO | `new-thread.sh` ficción (CC #1) |
| Schema state machine | Implícito | Sin definición formal |
| Cross-thread links | Manuales | Sin validación |
| Charter para assertions | NO | Pending (Platform #1) |

### Judge layer — 15% (CC)

| Pieza | Estado |
|---|---|
| Smoke test post-merge | ✅ |
| CI lint/typecheck/Vitest | ✅ |
| Tests unitarios obligatorios | ✅ (honor system) |
| E2E Playwright en CI | ❌ |
| LLM-as-judge sobre acceptance | ❌ |
| Golden regression sets | ❌ |
| Auto-escalation Telegram para PR review | ❌ |
| Self-review checklist hook | ❌ honor system |
| Canary scaling | ❌ |
| L1 Alex business edge | ✅ status quo |
| L2 WC-Impl drift review | ❌ no implementado |
| L3 Automated | parcial via CI |

### Auto-mode guardrails — 70% (CC)

| Guardrail | Estado |
|---|---|
| Permission deny list destructiva (70 patrones) | ✅ |
| Bash allowlist scoped | ✅ |
| Secrets read deny (.env, .dev.vars, .ssh) | ✅ |
| git push --force deny | ✅ |
| wrangler delete deny | ✅ |
| DROP/TRUNCATE/DELETE FROM blocked | ✅ |
| Cron alert Telegram | ✅ |
| LLM cost limit hook | ❌ (ccusage no instalado) |
| Time budget hook | ❌ |
| Workstream territory enforcement | ❌ honor system |

---

## §9 Conclusión WC

El thread/171 fue brain ultra con buenas intuiciones direccionales pero
errores estratégicos y tácticos. Los retos de CC y WC-Platform los
corrigieron desde sus ángulos respectivos.

**Posición WC ajustada firme:**
1. ADR-002 NO se redacta todavía
2. Acción inmediata: pasos 2-3 del plan v2 (scripts + ccusage)
3. Test empírico pre-split (paso 8)
4. Judge E híbrido tri
5. Auto-mode pausar/gatear ya, no esperar
6. 80/20 Alex-off NO antes Q3 2026
7. M1 Pricing fuera del 80/20 setup
8. Casa Chamán Q3 contingency explícita

**Próximos pasos ejecutables independientes del voto Alex Q1-Q5:**
- CC puede ejecutar spec `new-thread.sh` real (1 día) — destraba comms
- CC puede ejecutar `ccusage cron + dashboard` (1 día) — destraba cost data

Ambos son improvements sin riesgo, sin coordinar con formalización
multi-WC. Coincide CC y Platform como prioridades #1.

---

— WC, 2026-05-22, brain mode synthesis post-retos.
Voto Alex Q1-Q5 + cross-check con CC y WC-Platform = entrada a fase test empírico.
