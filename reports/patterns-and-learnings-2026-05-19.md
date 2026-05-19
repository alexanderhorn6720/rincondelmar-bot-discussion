# Patterns & Learnings — 2026-05-19

> Derivado de D4 (threads-audit) + D5 (gap-analysis) + git log de rdm-bot (últimos 60d).
> Generado por CC vía DoIt thread/143.

---

## A. CYCLE TIME

Medido sobre las **13 specs con PR mergeado y thread/N en body** (subset auditable):

| Métrica | Valor |
|---------|-------|
| Spec → first PR merged (avg) | **0.38 días** (~9h) |
| Spec → first PR merged (median) | **0 días** (mismo día) |
| Spec → first PR merged (max) | **2 días** (thread/85 → PR #85) |
| Outliers >3 días | **0** |

**Halt → resume** (eventos halt detectados: 4 threads en A5 cluster 130/136/137/138 = mismo día 2026-05-19, resume vía thread/138). Otros halts: thread/98 pr82-halted → thread/99 doit-fix → thread/100 merged = 0 días.

**Spec → result thread**: median 0 días (CC reporta mismo día que ship). Anomalía: PR #114 (journey templates) abierto desde 2026-05-18 sin result thread → 1 día abierto, esperando Alex review.

**Interpretación**: El ciclo es extremadamente rápido. Esto es porque (a) repo es joven (~40 días), (b) WC genera DoIt specs autocontenidos que CC ejecuta autónomo (≥36h sin intervención humana per thread/71), (c) la mayoría de PRs son <1 día de trabajo.

**Riesgo de la velocidad**: <0.5 días promedio significa que la spec→test→review→merge loop es informal. Cuando se rompe (e.g., thread/97-99 ciclo PR #82 typecheck → fix → merge), se rompe ruidosamente (3 threads consecutivos para 1 PR).

---

## B. THREADS ABANDONADOS

Specs sin movimiento >30 días sin ship: **0** (repo demasiado joven).

Specs sin PR claro (potencial abandono futuro):
- `33-guest360-architecture-phase-b-plan` — shipped parcial (guests_master, FTS) pero "Guest 360 UI unificada" referenciada en thread/86 sin PR final.
- `52-wc-anchors-spec-for-property-pages` — sin PR en map; verificar manualmente.
- `15g/15h/15i/15j` (cluster cutover) — superseded por thread/20 cutover-completed pero docs huérfanos.

**Patrón común**: los abandonos tienden a ser **sub-threads dentro de un cluster** (15-cluster, A5-cluster en formación). El thread "padre" se shippea, los sub-threads quedan como traza histórica.

---

## C. DECISIONES REVERTIDAS

| Original | Reversión | Aprendizaje |
|----------|-----------|-------------|
| thread/117 §1 (pet policy) | thread/118 retract + canonical | Pet fee `/noche` → `/estancia` confusión repetida (también memoria `feedback_morenas_chef_opt_in`). Necesita doc canónico permanente. |
| thread/124 karina training V1 | thread/125 karina training V2 | V1 tenía issues HTML escape + void elements → 2 iterations (#122, #124, #125). Pattern: deploy → 500 → retract → rewrite. |
| thread/119 pre-stay = 3 touchpoints | memoria `project_pre_stay_4_touchpoints` corrige a **4** (welcome + T-14 + T-7 + T-1) | WC redacta specs rápido y se le escapan números. Memoria guardada para futuras refs. |
| PR #119 revert(cf-pages) | revert del `root wrangler.toml` causaba prod auth 500 | Lesson: cualquier cambio en root wrangler/cf-pages config requiere canary específico. |
| pet fee `/noche` en multiple lugares | fixed en PR #78 (`100850f`) y PR #97 (`5b864f5`) | Anti-pattern enforced ya en STATE-drafts §E. |

**Total decisiones revertidas explícitamente: 5+** en 40 días. No es señal de mal proceso — es señal de iteración rápida con feedback loop sano.

---

## D. ANTI-PATTERN LEAKS

Grep en `main` últimos 60d:

| Leak pattern | Encontrado en | Status |
|--------------|---------------|--------|
| `/noche` en pet context | PRs #78, #97 (fix commits visibles) | ✅ fixed, no actual leak en código actual |
| `Casa Chamán` en Greeter prompt | `packages/agents/greeter/system-prompt-v5.ts` línea "10. NUNCA menciones Casa Chamán" + `route_user_to_url` fallback | ✅ explícitamente enforced ("Casa Chamán abre Q3 2026") |
| `Everything` en beds24 sync | grep en `packages/` y `apps/worker-*` no encontró calls a Beds24 con `Everything` flag | ✅ no leak |
| paths `C:\Users\Alex\` hardcoded | grep en commits últimos 60d = 0 matches | ✅ no leak |
| Beds24 horizon >365d | no encontrado en código | ✅ no leak |

**Observación importante**: Greeter prompt SÍ menciona "Casa Chamán" pero solo en negative context ("NUNCA menciones"). Esto es intencional — el LLM necesita la instrucción explícita. NO contar como leak.

Booker prompt SÍ contiene `679176` (Casa Chamán room_id) — esto es ESPERADO (booker tiene mayor scope que greeter, ver memoria reference_rdmbot_prod_ops_scope si aplicaba).

---

## E. RECURRING BLOCKERS

Patrones detectados de halt-report / question threads:

| Blocker recurrente | Frecuencia | Threads |
|--------------------|------------|---------|
| **Chrome MCP / session attach** | 3 en 24h | 130, 136, 137 (A5 cluster) |
| **Spec ambiguity → CC questions** | 1 explícito + ≥3 implícitos | 110 (questions c+e+d+p2), 117 (handoff doc reconciliation), 67 (q-66 pr-a75 go) |
| **Pet policy correction** | 2 iterations | 117/118 |
| **Karina training deploy** | 2 iterations | 124/125 |
| **PR82 typecheck halt** | 1 incident, 3 threads | 97 (review request), 98 (halt typecheck), 99 (resume) |
| **Pre-stay scope adjustments** | 3+ amendments | 119 (initial 3 touchpoints), then 120/121 (a1/a2 retro review + a3 amend + a5 new spec) |

**Categorización por causa raíz**:
- **External infra blockers** (40%): Chrome MCP, session lifetime, Cloudflare Pages config
- **Spec ambiguity** (30%): pet policy, pre-stay touchpoints, content editor architecture
- **TS/lint errors mid-PR** (15%): biome ignore vendor CSS (#118), typecheck halt PR82
- **Auth/permissions** (15%): karina admin emails (#120, #121, #122), allowContentEditor prop (#122)

---

## F. CONVENTION DRIFT

### Threads que rompen `NN-{author}-{topic}.md`

**10 threads** (detallados en threads-audit.md §"Convention drift table"):
- Todos pre thread/40 (early sprint cuando convention aún no firme)
- Pattern: thread escrito durante "burst" colaborativo donde nadie ownes el filename
- Solución: si retroactive rename causa link breakage, dejar; pero **a partir de thread/40 convention es 100%**.

### Branches que rompen `feat/fix/chore`

Sobre `feat/admin-nav-phase-2-4`, `feat/beds24-proxy-calendar`, etc. (lista en STATE-drafts/rdm-bot §C): **todas siguen convention**. EXCEPCIONES:
- `claude/compassionate-franklin-238c62`, `claude/zen-payne-ac1349` — CC sandbox worktrees con names auto-generados.
  - **Recomendación**: poda estas branches sandbox post-DoIt completion. Si CC necesita worktree, usar `feat/scratch-NNN` o `chore/sandbox-{taskid}`.
- `debug/resync-error-samples`, `hotfix/mojibake-guest-names` — `debug/` y `hotfix/` no están explícitamente en convention. Aceptables semánticamente pero formalizar.

### PRs sin Conventional Commit

Sample git log últimos 60d:
- PR #128 título "Feat/thread 141 house rules paper trail" — **mal formato** (debería ser `feat(rules): thread/141 house rules paper trail`)
- PR #130 título "Feat/a6 reglas adicionales deploy" — **mal formato**

**2 de los últimos ~30 PRs (~6%) rompen Conventional Commit title.** Aceptable pero corregible vía PR template enforcement.

### Threads sin "Result thread:" header

De los 39 specs, ninguno tiene un header formal "Result thread: N+x". CC reporta resultado vía thread con filename `NN-cc-(bot|data)-{topic}-complete.md` por convención implícita. Funciona pero requiere búsqueda full-text para verificar.

---

## G. RECOMMENDED PROCESS CHANGES (top 3)

### 1. PR template con campo obligatorio "Closes thread/N"

- **Problema**: ~50% PRs no referencian thread → gap analysis manual.
- **Propuesta**: agregar `.github/pull_request_template.md` con sección:
  ```
  ## Threads
  Closes: thread/__
  References: thread/__
  ```
- **Costo**: 30 min setup. Adopción opt-in (no bloqueante).
- **ROI**: futuras auditorías cross-ref automáticas. STATE.md auto-updateable.

### 2. Convención "Result thread: thread/N+x" en spec frontmatter

- **Problema**: CC ship → result thread inferido por filename, no documentado en spec.
- **Propuesta**: Spec template añadir línea al top:
  ```
  Spec: thread/N
  Result thread: TBD (CC fills upon completion)
  PR(s): #__
  ```
- **Costo**: 5 min cambio en `doit-template.md` (en rdm-platform/coordination).
- **ROI**: 100% trazabilidad spec → result → PR. Sin búsqueda full-text.

### 3. STATE.md auto-refresh skill / hook

- **Problema**: STATE-drafts generado manualmente es snapshot. Próxima refresh = manual.
- **Propuesta**: skill / Claude Code hook que post-PR-merge:
  - Actualiza §B (PRs open), §C (branches activas), §F (última semana shipped) en `STATE.md`
  - Sólo si el PR referencia thread/N
- **Costo**: 2-4h CC implementation (script en `.github/scripts/refresh-state.sh` + GH Actions trigger).
- **ROI**: STATE.md siempre fresh sin intervención manual. Reduce drift entre snapshot y realidad.

---

## H. SURPRISES / NON-OBVIOUS FINDINGS

1. **Cycle time es 0-2 días**: faster than expected. Implica que el bottleneck no es velocity sino review/decisión Alex (PR #114 abierta desde 2026-05-18, PR #130 desde 2026-05-19).

2. **W3 (May 15-18) tuvo 78 threads** (48 WC + 30 CC variants) — pico de productividad coincide con split cc → cc-bot/cc-data y formalización de DoIt v3. La separación de roles desbloqueó volumen.

3. **Convention drift estabilizado**: post thread/40 NO HAY drift de filename. Sugiere que la convention emerge naturalmente sin enforcement formal.

4. **PR thread-reference rate ~50%**: significativamente bajo. Asumiendo que el costo es ~10s por PR para escribir "Closes thread/N", esto es low-hanging fruit con alto ROI auditoría.

5. **0 specs realmente abandonados**: los 3 candidatos del cluster 15 son superseded por thread/20, no abandonados. Esto es notable — todas las specs encuentran ship-path o die explícito.
