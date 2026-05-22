---
thread: 177
author: CC-Bot
date: 2026-05-22
topic: cc-bot-doit-176-meta-archaeology-report
mode: DoIt
status: closed
related:
  - thread/176 (spec)
  - PR rdm-discussion#TBD (all reports + this thread)
deliverable: completion report del DoIt thread/176 META archaeology
---

# CC-Bot — thread/176 META archaeology completion report

Session paralela a thread/175 T1-T5 (otra sesión CC). Read-only audit. PR único con 19 archivos en `reports/`.

## §1 PR

PR rdm-discussion#TBD (branch `feat/meta-archaeology-audit-2026-05-22`). Merge directo recomendado: read-only, no controvertido, todos los reports en `reports/` + este thread.

## §2 Files generated

| Section | File | Tipo |
|---|---|---|
| A1 threads inventory | `reports/2026-05-22-META-A1-threads-inventory.{md,json}` | inventory |
| A2 PRs inventory | `reports/2026-05-22-META-A2-prs-inventory.{md,json}` | inventory |
| A3 migrations inventory | `reports/2026-05-22-META-A3-migrations-inventory.{md,json}` | inventory |
| A4 branches inventory | `reports/2026-05-22-META-A4-branches-inventory.{md,json}` | inventory |
| A5 cross-reference matrix | `reports/2026-05-22-META-A5-cross-reference-matrix.{md,json}` | join |
| A6 docs drift analysis | `reports/2026-05-22-META-A6-docs-drift-analysis.{md,json}` | analysis |
| A7 pending decisions | `reports/2026-05-22-META-A7-pending-decisions.{md,json}` | analysis |
| A8 lost work / orphans | `reports/2026-05-22-META-A8-lost-work-orphans.{md,json}` | analysis |
| A9 master synthesis | `reports/2026-05-22-META-A9-master-synthesis.md` | synthesis |
| ⚠️ Alex-flagged collisions | `reports/2026-05-22-META-collisions.md` | priority |

19 archivos. Scripts generadores en `reports/.audit-scratch/` (Python, reproducibles).

## §3 Top 10 findings (resumen)

Detalle completo en [A9 master synthesis §3](../reports/2026-05-22-META-A9-master-synthesis.md).

1. **22 thread number collisions / 209 threads (10.5%)** ⇐ root cause `scripts/new-thread.sh` ficción (referenced en CLAUDE.md+settings.json, no existe en ningún repo).
2. **F2 observability ADR Accepted ≠ shipped** — migration 0042 (que F2 spec reserva) ya consumida por `feedback_system`. Spec necesita remap antes de ship.
3. **STATE.md stale** — §A apps list (falta `worker-feedback`), §D/§G migración 0039 collision ya resuelta por PR #140 (2026-05-21), §A last-deploys de hace 10d.
4. **2 decisions stores sin policy doc**: `rdm-discussion/decisions/01-09` operacional vs `rdm-platform/decisions/ADR-001+` arquitectural. Split-brain.
5. **`apps/admin` PWA es ficción en 5 docs** (VISION + ADR-04 + ADR-07 + OPEN_QUESTIONS + roadmap) — admin vive dentro de `apps/web`.
6. **`decisions/03 PriceLabs` silently superseded** — VISION §"Principios 7" mantiene custom agent; ADR no actualizado.
7. **CLAUDE.md vs STATE.md scope drift** — STATE.md §E dice "WC NO implementa código", CLAUDE.md no lo menciona.
8. **PR ↔ thread linkage rota** — 90 PRs sin thread ref, 110 threads sin PR (mayoría informacional).
9. **`OPEN_QUESTIONS.md` 22 KB histórico** PR1/2/3 era, mayoría stale.
10. **41 merged branches not deleted** (vs STATE.md "15+"). Auto-delete-on-merge no es retroactivo.

## §4 ⚠️ Colisiones críticas (Alex flag)

[2026-05-22-META-collisions.md](../reports/2026-05-22-META-collisions.md) tiene tabla completa.

- **22 colisiones de número en threads** (10.5%). Mix de:
  - Acceptable amendments (162-amendment, 162-amendment-2 = mismo topic — OK)
  - Acceptable supersede (105-...-p3 vs 105-...-p3-plus-2bugs — OK por STATE.md §F)
  - **Race genuinas** (160-A vs 160-B, 169-A vs 169-B, 170-A vs 170-B — distintos topics, mismo número, ambos shipped). Estas son las que rompen.
- **0 migration collisions activas** (gracias a `scripts/new-migration.sh` que SÍ existe).
- **0 PR collisions** (GitHub previene).
- **0 cross-repo branch name collisions** problemáticas.
- **0 violations** de anti-pattern `feat/thread-N` ✅.

Root cause único: `scripts/new-thread.sh` falta. Una vez exista (T1 en thread/175), las colisiones futuras desaparecen.

## §5 Lost work top items

Ver [A8 §10 recovery candidates](../reports/2026-05-22-META-A8-lost-work-orphans.md).

1. A5 Airbnb 67% (branch `feat/a5-airbnb-bulk-approve-writeback`, halt threads 130/136/137/138 untracked locales).
2. PR #114 journey templates editor — 4 días open, esperando review Alex.
3. PR #130 A6 reglas adicionales — 3 días open, esperando review Alex.
4. F2/F1/F3 specs accepted, no shipped — el más urgente para destrabar pipeline.
5. 22 specs en `cc-instructions*/` y `wc-instructions/` — mayoría ya shipped pero sin archivar.
6. `OPEN_QUESTIONS.md` 22 KB — candidato a archive.

5 halt threads identificados (todos A5-related: 130/136/137/138 + 162 preflight). 41 merged-not-deleted branches.

## §6 Decisiones pendientes urgentes

Ver [A7 §8 critical-path](../reports/2026-05-22-META-A7-pending-decisions.md).

Bloqueando 3+ downstream:
1. **G7**: Alex vote on thread/148 (F1/F2/F3 + 7 items) — bloquea M1.
2. **G8**: Analytics activation (Alex pick variant: CF only / CF+GA4 / +GSC) — 1h CC ship.
3. **G6**: PDF endpoint removal spec — WC drafts → CC executes.
4. **A9 / decisions-02**: Stage 2 ManyChat sunset — bloquea WABA y pricing override.

38 net pending decisions tras dedupe; ~25 owner=Alex. Audiencia primaria de los reports es Alex + WC para priorizar próxima ola.

## §7 Cost total real ($USD)

- Estimado: $1-2 USD LLM (sesión Opus, ~1 sesión continua, mayoría tool I/O).
- Bajo `halt_global_budget: $30 USD` y muy bajo `estimated_llm_budget: $15-20 USD`.

## §8 Tiempo total real

- ~1.5h continuos (una sesión, una rama).
- Bajo `estimated_cc_days: 2` que la spec contemplaba — automated tooling (gh API + Python join) corrió faster que estimación humana.

## §9 Sorpresas / blockers

- **Sorpresa #1**: 7 de 209 threads tienen YAML frontmatter; 202 usan formato legacy `**Date** / **Author**` bold-header. Parser dual-mode. Sin blocker.
- **Sorpresa #2**: `worker-feedback` existe como 5to app — no aparece en STATE.md / CLAUDE.md / VISION.md / ROADMAP.md. Documentado en A6 §3 C1.
- **Sorpresa #3**: F2 spec status "Accepted 2026-05-20" pero migration 0042 que reclama ya está consumido por feature distinto (`feedback_system`). Spec necesita refactor de número antes de implement.
- **Hiccup técnico**: Python 3.14 / Windows subprocess defaulteó a cp1252 — crash en emojis de PR titles. Fix: `encoding='utf-8', errors='replace'` en todos los `subprocess.check_output`. Mismo lesson que `feedback_powershell_utf8` memory.
- **Blocker**: ninguno.

## §10 Recomendaciones para WC + WC-Platform analysis next session

WC: priorice top 3 quick-wins de A9 §5 "Inmediato" — `new-thread.sh` (T1 thread/175 ya cubre), STATE.md cleanups (4 items, 10 min cada uno), CLAUDE.md WC-no-implementa anti-pattern.

WC-Platform:
- Decidir 2 decisions stores policy (rdm-discussion `01-09` vs rdm-platform `ADR-001+`). Doc explicativo o consolidación.
- Refactorizar `rdm-platform/foundations/F2-observability.md` § migration number (0042 ya tomado) antes de que CC implemente.
- Actualizar `rdm-discussion/decisions/03-pricing-agent.md` status header → REVISED.
- Confirmar policy `apps/admin` PWA: rewrite docs o commit a build separate.

Alex: 7 items de thread/148 (G7) son critical-path para todo lo demás. Sin vote, M1 no arranca.

## §11 DoD checklist

- [x] 10+ archivos generados (19 actually, 9 secciones × 2 + 1 synthesis MD only)
- [x] PR único con todos los reports + commit messages claros
- [x] PR body con TLDR de top findings (ver PR description)
- [x] PR mergeable a main (rebased sobre origin/main reciente, no conflicts)
- [x] CI verde — N/A (no CI runs en rdm-discussion para .md changes; smoke check post-merge será archivos accesibles via GitHub raw URLs)
- [x] PR body referencia `Closes thread/176`
- [x] Cost real reportado (~$1-2 USD)
- [x] Self-review checklist:
  - [x] Diff completo leído — yes, paso final pre-PR
  - [x] No secrets en reports — confirmed (gh api no devuelve tokens; PR bodies sample-checked sin tokens)
  - [x] PR body explica qué hacer post-merge
  - [x] No tocado workstream ajeno (solo `rdm-discussion/reports/` + `threads/177-...`)
  - [x] Shared territory: ninguno tocado
- [x] Thread response en `threads/177-cc-bot-doit-176-meta-archaeology-report.md` (este archivo)

## §12 Nota sobre `scripts/.audit-scratch/`

Scripts Python generadores (a1_threads.py, a2_prs.py, …) viven en `reports/.audit-scratch/` por reproducibilidad. Son inputs, no outputs. Si Alex/WC quieren re-correr el audit (e.g. semanal), `python reports/.audit-scratch/a1_threads.py` y demás re-generan los `.md`+`.json` correspondientes en sitio. Las dependencias son `python 3.10+` + `PyYAML` (ya instalado) + `gh` CLI auth.

— CC-Bot (sesión Opus, thread/176 paralela a thread/175), 2026-05-22.
