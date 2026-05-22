---
thread: 178
author: WC
date: 2026-05-22
topic: brain-ultra-deep-dive-meta-archaeology-synthesis-and-wave-1-spec
mode: brain ultra (deep dive)
status: open-for-alex-vote-and-spec-execution
inputs:
  - reports/2026-05-22-META-A1..A9 (CC audit en PR rdm-discussion#12)
  - reports/2026-05-22-META-collisions.md (Alex flag)
  - thread/176 (META audit spec)
  - thread/177 (CC audit completion report)
  - threads 171-175 (synthesis chain)
deliverable: análisis estructural del audit + priorización impacto×esfuerzo + 3 specs ready-to-execute para Wave 1 + lista de decisiones Alex bloqueantes
preliminary_wc_vote:
  - Wave 1 cleanup (10 items, ~3-4h CC total) ejecutable inmediato vía spec separada
  - F2 spec refactor migration remap (1 spec WC-Platform)
  - Decisions stores policy doc (1 spec WC-Platform)
  - G7 thread/148 sigue siendo bottleneck #1 — sin voto Alex, M1 no arranca
---

# Brain ultra deep dive — META archaeology synthesis + Wave 1 spec

## §0 Contexto

CC en thread/176/177 entregó 19 archivos de audit. Lectura completa: A9 master, META-collisions, A6 docs drift, A7 pending decisions, A8 lost work. No re-litigo lo que CC ya cuantificó. Mi aporte aquí es:

1. **Patrón estructural que CC no articuló** (no es su layer)
2. **Priorización por impacto × esfuerzo** (matriz operable)
3. **3 specs ready-to-execute para Wave 1** (sin esperar Alex decisions)
4. **Lista de decisiones Alex bloqueantes** ordenada por downstream impact
5. **Meta-aprendizajes** (estimate calibration + spec defects)

Alex dio 2h para brain. Output denso, mobile-friendly, tablas > prosa.

---

## §1 Lo que CC encontró bien (no rehacer)

Resumen ejecutivo de findings que asumo como hechos:

| # | Finding | Source |
|---|---|---|
| 1 | 22 thread collisions / 209 (10.5%), root cause `new-thread.sh` ficción | A6 §5, collisions §6 |
| 2 | F2 ADR Accepted (2026-05-20) ≠ shipped. Migration 0042 ya consumida por feedback_system | A6 §5/§10, A7 §4 |
| 3 | STATE.md stale: §A apps list (falta worker-feedback), §D/§G migración 0039 collision ya resuelta (PR #140), §A last-deploys de hace 10d | A6 §3 C1/C2/C8 |
| 4 | 2 decisions stores sin policy doc: discussion/decisions/01-09 operacional vs platform/decisions/ADR-001+ arquitectural | A6 §3 C5 |
| 5 | apps/admin PWA es ficción en 5 docs (VISION + ADR-04 + ADR-07 + OPEN_QUESTIONS + roadmap) — admin vive en apps/web | A6 §3 C4 |
| 6 | decisions/03 PriceLabs silently superseded (VISION §Principios 7 dice custom agent kept; ADR no actualizado) | A6 §7 |
| 7 | CLAUDE.md vs STATE.md scope drift: §E dice "WC NO implementa código en rdm-bot/rdm-platform", CLAUDE.md no lo menciona | A6 §3 C7 |
| 8 | 90 PRs sin thread ref / 110 threads sin PR | A5 |
| 9 | OPEN_QUESTIONS.md 22KB histórico (PR1/2/3 era, mostly stale) | A7 §6 |
| 10 | 41 merged branches not deleted (vs STATE.md "15+") | A8 §3 |
| 11 | 7/209 threads YAML frontmatter, 202 legacy bold-header (parser dual-mode) | A9 §2 |
| 12 | worker-feedback existe como 5to app — no aparece en STATE/CLAUDE/VISION/ROADMAP | A6 §3 C1 |

---

## §2 Patrón estructural que CC no articuló — "STATE como contrato"

CC reportó factualmente. Lo que falta articular: **el problema raíz no es las colisiones, ni los STATE.md stale, ni las ficciones individuales. Es ausencia de disciplina de "STATE como contrato".**

### Mecanismo del drift

Cada doc canonical (CLAUDE.md, STATE.md, VISION.md, ADRs, OPEN_QUESTIONS, decisions/) tiene reglas implícitas sobre **cuándo se actualiza y por quién**. Pero esas reglas no están codificadas. Resultado:

| Trigger técnico | Update doc esperado | Realidad |
|---|---|---|
| `worker-feedback` shipped | STATE.md §A apps list + CLAUDE.md Stack | NO propagado |
| Migration 0039 collision resuelta PR #140 | Remove entry STATE.md §D + §G | NO propagado |
| F2 ADR Accepted | Verify migration 0042 libre antes de Accept | NO verificado — 0042 ya tomado |
| `scripts/new-thread.sh` agregado a CLAUDE.md + settings.json | El archivo debe existir | NO existe — ficción |
| `apps/admin` PWA descrito en VISION + ADR-04 + ADR-07 + OPEN_QUESTIONS | Build apps/admin/ o rewrite docs | NI uno ni otro — 5-doc fiction |
| PriceLabs decision/03 obsolete por custom agent | Mark decisions/03 status: SUPERSEDED | NO marcado |
| Alex 2026-05-19: "WC NO implementa código" | Propagate to CLAUDE.md anti-patterns | Solo en STATE.md §E |
| Auto-delete-on-merge habilitado (thread/146) | Pre-existing merged branches retroactively cleaned | NO retroactivo — 41 acumuladas |

### Causa estructural común

**Writes a docs canonical no tienen verificación ni propagation hook.** Specs "Accepted" no tienen gate de implementación. Cambios técnicos no tienen update obligatorio de docs canonical.

### Implicación

Cada finding individual del audit es un síntoma. La cura es:

1. **Status field machine-readable en docs canonical** (Accepted/Implemented/Live/Superseded/Stale)
2. **Update obligatorio en self-review checklist**: si tu PR cambia X, debes actualizar Y
3. **CI check de drift**: validador que confronta claims vs filesystem (e.g. STATE.md §A apps list vs `ls apps/`)
4. **ADR lifecycle explícito**: Accepted ≠ Shipped. Status separados

Esto va más allá de Wave 1 cleanup — es work foundations sobre cómo el proyecto se documenta a sí mismo. Lo flageo aquí pero NO lo meto a Wave 1.

### Por qué CC no lo articuló

CC ejecutó audit READ-ONLY. Encontrar el patrón requiere síntesis cross-finding + propuesta estructural — eso es WC brain mode territory.

---

## §3 Matriz impacto × esfuerzo

Voy a clasificar los 12 findings + decisiones pendientes en una matriz operable:

### Cuadrante 1: alto impacto + bajo esfuerzo (HAGAMOS YA)

| # | Acción | Esfuerzo | Impacto |
|---|---|---|---|
| Q1.1 | `scripts/new-thread.sh` real (T1 thread/175 ya cubre) | 20 min CC | Cierra futuras colisiones (no las históricas). Estructural |
| Q1.2 | STATE.md cleanup: +worker-feedback, -0039 collision, +last-deploys actuales | 10 min CC | Stop misinforming new sessions |
| Q1.3 | CLAUDE.md: añadir anti-pattern "WC NO implementa en bot/platform" | 5 min CC | Propagation gap fix |
| Q1.4 | decisions/03 PriceLabs: añadir status header REVISED + cite VISION §7 | 2 min CC | Stop stale guidance |
| Q1.5 | Archive cc-instructions/ shipped specs → cc-instructions/archive/ | 30 min CC | -90% noise en active dir |
| Q1.6 | OPEN_QUESTIONS.md split: archive PR1/2/3 era → start fresh con net-pending | 20 min CC | 22KB → ~5KB activo |
| Q1.7 | Batch delete 41 merged branches (después de verificar último PR cerrado) | 15 min CC | Limpieza repo |

Total Q1: ~2h CC. Estos van **agrupados en una spec única** Wave 1.

### Cuadrante 2: alto impacto + medio esfuerzo (PRÓXIMO)

| # | Acción | Esfuerzo | Impacto |
|---|---|---|---|
| Q2.1 | F2 spec refactor — migration número 0042 → 0046+ libre | 1h WC-Platform brain + 30 min CC | Desbloquea F2 ship |
| Q2.2 | Decisions stores policy doc — split-brain solution | 1h WC-Platform brain | Stop split-brain risk |
| Q2.3 | apps/admin decision — rewrite VISION/ADR-04/07 OR commit a build | 1h Alex + WC-Platform | Stop 5-doc fiction |
| Q2.4 | Thread metadata format: adopt YAML frontmatter universal + one-shot migrator | 2h CC | Cross-referencing reliable |

### Cuadrante 3: alto impacto + alto esfuerzo (ESTRATÉGICO)

| # | Acción | Esfuerzo | Impacto |
|---|---|---|---|
| Q3.1 | G7 thread/148 Alex vote (F1/F2/F3 + 7 items) | 30 min Alex vote → unlocks ~10 días CC downstream | M1 path bloqueado sin esto |
| Q3.2 | Resume A5 Airbnb 67% — branch + halt threads 130/136/137 | 5-10 días CC + Alex coord | Content sync to Airbnb |
| Q3.3 | F2 → F1 → F3 ship secuencial (post Q2.1, post Q3.1) | ~30 días CC total | Foundations para M1-M5 |
| Q3.4 | "STATE como contrato" — status field + drift validator | 5-10 días CC | Estructural — fundamenta wave 2+ |

### Cuadrante 4: bajo impacto + bajo esfuerzo (FILLERS)

| # | Acción | Esfuerzo |
|---|---|---|
| Q4.1 | PR #114 journey templates review/merge or close-with-reason | 30 min Alex |
| Q4.2 | PR #130 A6 reglas adicionales review | 20 min Alex |
| Q4.3 | KV binding rename `KV_IDEMPOTENCY` vs `KV_KNOWLEDGE` cross-doc fix | 5 min CC |
| Q4.4 | 4 branch antipattern violations (`feat/thread-N`) — flag, no fix automático | 5 min Alex |

### Cuadrante 5: bajo impacto + alto esfuerzo (NO HACER)

- Manual fix retrospectivo de 22 colisiones históricas de threads (renombrar files retroactivamente). Romperia links históricos sin beneficio.
- Cross-reference todas las 110 threads sin PR. Mayoría son informacionales legítimas.

---

## §4 Spec 1 — Wave 1 cleanup (ready-to-execute)

Bundling Q1.1-Q1.7 en una spec única para CC en DoIt. Esta spec se redacta como thread/179 separado para que CC pueda ejecutar inmediato.

### Headline
- 7 sub-tasks W1-W7
- Total ~2h CC en serie, 1h con paralelización
- Budget LLM <$5 (corrigiendo mi sesgo previo — son edits cortos)
- 1 PR único (todos los cleanup juntos, no fragmentar)
- Halt rules estrictas
- Read-only excepto edits puntuales declarados

### Tasks

| ID | Path | Acción | Verificación |
|---|---|---|---|
| W1 | `rdm-discussion/scripts/new-thread.sh` + `rdm-bot/scripts/new-thread.sh` (wrapper) | Implementar real (= thread/175 T1) | Test atomic claim 2 concurrent invocations |
| W2 | `rdm-bot/STATE.md` | §A apps list: +worker-feedback / §D: remove 0039 collision / §G: remove G9 (resuelto) / §A last-deploys: refrescar fechas reales | Diff matches A6 §3 C1/C2/C8 findings |
| W3 | `rdm-bot/CLAUDE.md` | Añadir anti-pattern: "WC NO implementa código en rdm-bot ni rdm-platform — solo specs + threads + brain mode (Alex correction 2026-05-19)" | Grep CLAUDE.md returns the anti-pattern |
| W4 | `rdm-discussion/decisions/03-pricing-agent.md` | Añadir header `status: REVISED 2026-05-XX` + nota citando VISION §"Principios 7" (custom agent kept, PriceLabs NOT purchased) | Doc tiene status field |
| W5 | `rdm-discussion/cc-instructions/`, `cc-instructions-bot/`, `cc-instructions-data/`, `wc-instructions/` | Mover specs shipped (per A6 §8) a `cc-instructions/archive/` (etc) | Active dir tiene solo specs pendientes |
| W6 | `rdm-bot/OPEN_QUESTIONS.md` | Split: archive a `docs/archive/OPEN_QUESTIONS-2026-05-08-PR1-PR3.md` (full 22KB), create new `OPEN_QUESTIONS.md` con solo net-pending de A7 §6 | Active OPEN_QUESTIONS.md <5KB |
| W7 | Repo cleanup branches | `gh api /repos/<owner>/<repo>/branches` + cross-ref A8 §3 lista → batch delete 41 merged branches | `git branch -r --merged main` muestra solo main+dev branches actuales |

### Halt
- Si W1 falla en atomic claim test → halt + reporta
- Si W6 archive split rompe links existentes (git log refs) → halt + reporta
- Si W7 delete intenta tocar branch con PR open → halt + skip
- Cost >$10 → halt

### Definition of done
- 1 PR mergeable a `main` de rdm-discussion (W1 también afecta rdm-bot — 2 PRs si requiere)
- Verificaciones de cada W pasa
- Thread response report al final con counts antes/después

**Esta spec la pusheo como thread/179 separado tras este brain. Opcional: Alex aprueba primero.**

---

## §5 Spec 2 — F2 spec refactor (migration remap)

Quick-target medium-impact. Pre-req para Q3.3 (F2 ship).

### Problema
`rdm-platform/foundations/F2-observability.md` reserva migration 0042 = `cron_heartbeats`. Reality 0042 = `feedback_system` (thread/161, ya en filesystem). F2 no puede shippearse sin remap.

### Spec scope
- Audit qué números de migration están libres post-0042 (0043, 0044, 0045 también pueden estar tomados)
- F2 spec update: cron_heartbeats claims migration `0046+` (TBD por CC al ejecutar via `new-migration.sh`)
- Verificar otras claims de F2 (metrics.ts, alerts.ts, cron-heartbeat.ts paths) siguen vigentes
- NO ejecutar F2 implementation. Solo refactor del spec.

### Quién
WC-Platform brain mode (1h) → spec update directo en `rdm-platform/foundations/F2-observability.md`. CC no necesitado para este step.

### Bloqueador
Ninguno — esto se puede hacer ahora. Tras refactor, F2 sigue bloqueado por Q3.1 (G7 Alex vote).

---

## §6 Spec 3 — Decisions stores policy doc

Medio-impacto. Pre-req conceptual para evitar futuros split-brain.

### Problema
`rdm-discussion/decisions/01-09` (operacional, sin formal status) vs `rdm-platform/decisions/ADR-001+` (architectural, con frontmatter). No hay doc que explique split.

### Opciones (WC-Platform vote needed)

| Opción | Acción | Pro | Con |
|---|---|---|---|
| A | Freeze rdm-discussion/decisions/ as "v1 legacy". Todo nuevo va a rdm-platform/decisions/ | Simple. Una sola fuente forward | rdm-discussion stale forever, requires migration of active references |
| B | Migrar formato YAML a rdm-discussion/decisions/01-09 + mantener split por scope (operational vs architectural) | Preserve historia. Clear scope | Más mantenimiento. Split-brain persiste pero documentado |
| C | Consolidar todo en rdm-platform/decisions/. Move 01-09 a rdm-platform/decisions/legacy/ | Single source of truth | Effort medio, may break references en STATE.md / VISION |

**Mi voto preliminar**: Opción A (freeze legacy). 10 min spec, no migration burden. Simple.

### Quién
WC-Platform brain (30 min) → spec doc en `rdm-platform/decisions/00-policy.md` declarando opción.

---

## §7 Decisiones Alex bloqueantes (ordenadas por downstream impact)

| ID | Item | Downstream bloqueado | Tipo | Esfuerzo Alex |
|---|---|---|---|---|
| 🔴 G7 | Vote sobre thread/148 (F1/F2/F3 + 7 items) | F2 ship → F1 ship → F3 ship → M1 Pricing → M5 Tasks → I3/I5/I7/I8 | technical + business | 30 min lectura + voto |
| 🟡 G8 | Analytics activation variant (CF only / CF+GA4 / +GSC) | tracker emit + GA4 events readout | provisioning | 5 min voto |
| 🟡 G6 | PDF endpoint removal — confirmar WC drafts spec → CC executes | Cleanup broken /reglas/{slug}/pdf | technical | 5 min ack |
| 🟡 G3 | PR #130 A6 reglas adicionales review | PR merge | business | 20 min review |
| 🟡 G4 | PR #114 journey templates editor review | PR merge | business | 30 min review |
| 🟢 G1 | A5 Airbnb writeback: continue o archivar 67% | content sync stuck | business + provisioning | 1h coord |
| 🟢 G2 | Browserbase AirBnB KPI scraper start | scraper for KPIs | business | 30 min decide |
| 🟢 G5 | Casa Chamán renovation timeline | Greeter unhide post-Q3 | business | n/a hasta Q3 |
| 🟢 — | apps/admin PWA: rewrite docs vs commit to build | 5-doc fiction | strategic | 1h decision |
| 🟢 — | A9/02 Stage 2 ManyChat sunset path + WABA propia | A4/A5 Stage 2 ideas | strategic | 1h decision |

**G7 es el #1 crítico**. Sin voto Alex, M1 no arranca y las foundations quedan en limbo. Q3.3 (F2→F1→F3 ship) imposible sin G7.

---

## §8 Meta-aprendizajes

Sin auto-flagelarme. Datos que valen para próximas specs.

### M1 — Mi estimate vs realidad CC

| Spec | Mi estimate | CC real | Factor off |
|---|---|---|---|
| thread/176 META audit | 2 días CC + $15-20 | 1.5h + $1-2 | **10-15× over** |
| thread/175 P1+P2 (5 tasks) | 8 días CC + $35-50 | TBD (CC ejecutando) | TBD |

**Corrección heuristic forward**: dividir mis estimates futuros entre 10-15× hasta tener data calibrada. Aplicar especialmente a tareas que son shell + git + parse (CC velocidad máxima). Mantener factor más conservador (3-5×) para tareas que requieren código nuevo no trivial.

### M2 — Spec defects que detecté

Thread/175 y thread/176 omitieron `git pull --rebase origin main` en pre-flight obligatorio. CC en thread/176 halt-eó por clone stale. Adopto: **paso 0 universal en todas las specs DoIt** = `git pull --rebase origin main` en repos relevantes.

### M3 — Mis errores en thread/171 (anclaje)

CC validó/refutó en thread/172, WC-Platform en thread/173. Mi posición ajustada en thread/174. Lo nuevo de este audit:
- `scripts/new-thread.sh` que asumí existente: CC ya lo cuantificó (4 references en CLAUDE.md, allowlist en settings.json, no existe). Confirmado.
- "Operational antes de foundations" Q4 Alex: el audit valida con datos — Wave 1 cleanup ataca operativo, no foundations.

### M4 — Patron de spec que no había documentado

CC implementó scripts Python reproducibles en `reports/.audit-scratch/` para que el audit se pueda re-correr. Pattern: **specs DoIt analyticas deberían incluir scripts reproducibles como deliverable**, no solo output. Esto vale capturar como template update.

---

## §9 Plan v3 — siguiente ola

Reemplaza plan v2 de thread/174 §4.

| # | Acción | Quién | Bloqueador | Tiempo |
|---|---|---|---|---|
| 1 | Push esta brain ultra (thread/178) | WC | — | ✅ ejecutando |
| 2 | **Wave 1 cleanup spec → thread/179** (W1-W7) | WC drafts → CC ejecuta | — | WC 20 min + CC 2h |
| 3 | **F2 spec refactor migration remap** | WC-Platform brain | — | 1h |
| 4 | **Decisions stores policy** (opción A o vote) | WC-Platform brain → Alex confirma | — | 30 min |
| 5 | **G7 thread/148 Alex vote** (F1/F2/F3 + 7 items) | Alex | — | 30 min Alex |
| 6 | Post-G7: F2 ship (CC en DoIt) | CC | Q3.1 + Q2.1 | TBD |
| 7 | Post-F2: F1 ship | CC | F2 ship | TBD |
| 8 | Post-F1: F3 ship | CC | F1 ship | TBD |
| 9 | M1 Pricing arranque | WC-Platform brain → impl | Q3.3 completo | TBD |
| 10 | Resumen mensual del pipeline (audit re-run) | CC | scripts ya existen en .audit-scratch | <1h |

**Cambios vs plan v2**:
- Inserto Wave 1 cleanup como paso 2 (no estaba)
- F2 spec refactor como pre-req explícito (paso 3)
- Plan v2 paso 8 "test empírico 1-2 sem" se DIFIERE — primero ordenamos operativo per Q4 Alex
- Plan v2 paso 9 "golden sets" se DIFIERE — son para M1-M5, no para Wave 1
- Plan v2 paso 13 "validación 80/20" → ya no es Q3 2026 sino post-foundations LIVE

---

## §10 Próximo paso ejecutable

**Inmediato:** push thread/179 con spec Wave 1 cleanup detallada (W1-W7). 20 min WC. Sin esperar Alex.

**Paralelo:** WC-Platform escribe spec F2 refactor (Q2.1) en próxima sesión brain.

**Bloqueado por Alex:** G7 thread/148 vote. Sin esto, paso 6+ del plan v3 no avanza.

**Para Alex en este momento — votos optativos sin obligación de comprometerse hoy:**
- Wave 1 cleanup → spec lista, ¿push thread/179 y arranco CC ahora o esperas review?
- F2 spec refactor → ¿WC-Platform lo escribe ya, o esperas G7 voto?
- Decisions stores policy → mi voto preliminar Opción A. ¿OK o prefieres B/C?
- G7 thread/148 → si tienes 30 min hoy, desbloqueas todo el path. Si no, no problem — Wave 1 avanza independiente

---

## §11 Costo real del brain ultra

- Tokens leídos: ~80KB (5 reports completos + thread/177 + threads/175-176 verify)
- Tokens output: ~16KB (este thread)
- Modelo: Opus 4.7
- Cost estimate: $1-2 USD (sin telemetry real, igual que CC)
- Tiempo wall-clock: ~25 min lectura + ~20 min síntesis y escritura = ~45 min total (Alex me dio 2h, sobré tiempo)

---

**Fin brain ultra.** Próximo: push thread/179 Wave 1 cleanup spec si Alex aprueba.

— WC, 2026-05-22, brain ultra deep dive post-META archaeology audit.
