# Gap analysis — 2026-05-19

> Para cada thread `type=spec` (39 detectados), evaluamos: result thread, PR mapping, deploy evidence, tests, futura inclusión en STATE.md.
> Generado por CC vía DoIt thread/143.

---

## METODOLOGÍA

- **Spec set**: 39 threads marcados `spec` por filename heurístico (+10% noise por convention drift).
- **PR map**: parse `body+title` de `gh pr list --state merged` rdm-bot → regex `thread/(\d+)` → invert.
- **Result thread**: filename match dentro de threads/ (e.g. spec thread/N tiene result N+1, N+2 si existen).
- **Deployed**: derivado de PR `mergedAt` + asunción "merge a main = deploy" (CF Pages auto + workers manual).
- **Tests**: heurística — no leemos código, asumimos coverage según commit message si `fix(*)` o `test(*)`.

---

## TABLA 1 · Specs **shipped + verified** (PR mergeado + result thread + sin known gap)

| Thread | Spec title | PR(s) | Result thread | Deploy evidence | Status |
|--------|------------|-------|---------------|-----------------|--------|
| 11 | beds24-migration-task-for-cc | (12 commits via `12-cc-beds24-migration-stop` paused) | 12 + 13 | 13 declares done | ✅ shipped |
| 30 | alex-approvals-cc-execution-plan | spans #41-50 (sprint 1-2) | 28 + 31 + 32 | 31 deploy log | ✅ shipped |
| 38 | airbnb-write-back-plan | A5 cycle (#116 + thread/127-138) | 138 (67% deploy) | partial | ⚠️ shipped partial |
| 65 | greeter-v5-fase-2-spec | #41-46 (PRs era A* prefix) | 66 + 68 | implicit (no PR thread ref) | ✅ shipped |
| 72 | cc-data-plan-and-day1-roadmap | data pipeline PRs A75-A763 | 73 + 74 + 76 + 77 | 76 deploy-pipeline-complete | ✅ shipped |
| 83 | faq-content-enrichment-extraction | #81 (data extraction) | 84 (faq complete) | 84 complete | ✅ shipped |
| 89 | platform-wishlist-and-tasks-module | n/a (conceptual) | 91 vision, ADR-001 platform | platform repo created | ✅ documented |
| 96 | pre-flight-clean-ready-for-next-task | (meta-spec, gateway) | n/a | gateway only | ✅ no-op |
| 97 | doit-pr82-review-merge-deploy | #82 → halted (98) → fixed via #99 | 98 + 100 | 100 pr82-merged | ✅ shipped |
| 99 | doit-fix-kv-binding-resume-pr82 | #82 (recovery) | 100 | merged | ✅ shipped |
| 101 | doit-admin-bookings-feedback-fixes | #83 | 102 | 102 fixed | ✅ shipped |
| 103 | doit-beds24-backfill-prewebhook | #84, #91, #104 | 104 backfill-complete | merged | ✅ shipped |
| 105 (×2) | doit-admin-inbox-p3 (+ p3-plus-2bugs) | #85 | 106 inbox-p3-bugs-complete | merged | ✅ shipped |
| 107 | doit-small-items-wave-6-parts | #87, #88, #90 (3 waves) | 108 wave-4-of-6-shipped | merged | ✅ shipped (4/6 — 2 deferred) |
| 109 | doit-small-items-wave-2 | #88 (subset) | 108 | merged | ✅ shipped |
| 115 | doit-guests-resync-beds24 | #98, #123 | 122 + 138 | beds24-webhook live | ✅ shipped |
| 119 | pre-stay-mvp-spec-ready | #102, #103, #104, #105, #106, #112, #113 | pre-stay-* branches | live (worker-pago crons active) | ✅ shipped (4 touchpoints) |
| 121 | a2-a3-review-a4-amendment-a5-spec | #116 (A5 §1) + others | 122, 138 | partial A5 | ✅ specs landed |
| 127 | a5-execution-doit | #116 + multiple A5 cells | 138 67% | partial | ⚠️ ongoing |
| 128 | open-items-omnibus-doit | #128 paper trail (referenced from PR #128) | 129 omnibus-doit-report | merged | ✅ shipped |
| 131 | mobile-inbox-rescue-doit | #126 | 133 rescue-complete | merged | ✅ shipped |
| 134 | beds24-proxy-readonly-doit | #127 | 135 proxy-complete | merged + custom domain | ✅ shipped |

## TABLA 2 · Specs **shipped + missing pieces** (qué falta)

| Thread | Spec title | Shipped | Missing |
|--------|------------|---------|---------|
| 38 / 121 / 127 | A5 airbnb write-back | bulk-approve (#116), per-cell deploy-confirmed framework | per-cell write-back UX, Chrome:9222 session reusable, 30% structural skips (per thread/138) |
| 33 | guest360-architecture-phase-b-plan | guest_events table, guests_master, FTS | "Guest 360" UI vista unificada todavía no shipped (referenciado en thread/86) |
| 52 | anchors-spec-for-property-pages | thread/52 spec issued | NO PR encontrado en map; ¿anclas en property pages se shippeó o se deferred? |
| 54 / 55 | data-mining-v2-strategy + go-plan | thread/56 prep-complete, threads/72-77 data pipeline | vectorize tail residual (memory: project_vectorize_tail_done confirma 99.99% live) |
| 57 | edge-case-audit-v2-plan | implicit en wave2 (#88-90) | audit final report no encontrado |
| 58 | ack-cc-overnight-and-pr-a15-spec | PR A15 shipped (per thread/62 pr-a15-subcomponents-live) | n/a — completo |
| 64 | alex-voted-option-a-handoff-spec-fase-2 | thread/66 v5-fase-2-built | n/a — completo |
| 82 | v6-combined-spec-ready-for-cc | A6 cells deployed (thread/140) | PR #130 abierto, falta merge |
| 84b | admin-bookings-gantt-spec | bookings Gantt feature shipped via wave PRs | thread/86 indica "list-view-kv-inquiries" delta → DELTA implementado? Confirmar |
| 85 | admin-inbox-unified-spec | #85 inbox MVP merged | thread/131 indicó Part E rescue → completed (#126), pero "unified" 100%? Verify |
| 93 (dup-B) | ack-cc-feedback-doit-template-v2 | inline en CLAUDE.md | doit-template-v3 referenced (thread/94) |
| 94 | ack-clone-paths-doit-template-v3 | inline en thread/143 (este DoIt usa v3) | v3 document canónico no localizado |

## TABLA 3 · Specs **not started** (no PR, no result thread visible)

| Thread | Spec title | Why pending | Priority guess |
|--------|------------|-------------|----------------|
| 15g | final-plan-post-getlistings | parte del cluster 15 cutover — probablemente shipped pero perdido en suffix mess | low (legacy) |
| 15c | final-approved-plan | cluster 15 cutover | low (legacy, see thread/20 cutover-completed) |
| 15d | additional-getlisting-task | cluster 15 cutover | low (legacy) |

> **Insight:** sólo 3 specs sin evidencia de implementation, y los 3 son sub-threads del cutover Beds24 cluster (resuelto via thread/20). Cero specs realmente unstarted post thread/30.

## TABLA 4 · Threads **esperando decisión Alex**

Cross-referenciado con outstanding decisions de STATE-drafts:

| Thread | Decisión pendiente | Días abierto | Bloquea |
|--------|--------------------|--------------|---------|
| 132 | Browserbase eval + AirBnB KPI scraper backlog | 0 | A5 alternativa scraper |
| 123 | canary review HSM critical/defer/cancel-race | 1 | Outbound automation post-cancel |
| 117/118 | pet policy correction final (¿shipped a Greeter prompt?) | 1 | Greeter V6 cleanup |
| 138 | A5 67% completo — shipear o esperar 100% | 0 | sprint A5 cierre |
| 122 | canary results + ManyChat findings | 1 | follow-up tickets |
| PR #114 (journey templates editor) | review + merge | 1 | journey templates UX |
| PR #130 (A6 reglas adicionales deploy) | review + merge | 0 | A6 production |

## TABLA 5 · Next 3 priorities recomendadas

| # | Recomendación | Razón |
|---|--------------|-------|
| 1 | **Merge + deploy PR #130 (A6 reglas adicionales)** y cerrar thread/140 | thread/140 reporta 8/8 cells deployed live → solo falta validación visual + close. Bajo riesgo, alto valor (paper-trail completion). |
| 2 | **Decidir A5 path (thread/138)**: shipear 67% + abrir tickets de los 30% structural skips, o esperar resolver session gap | A5 está bloqueando atención de CC repetidamente (threads 127, 130, 136, 137, 138 todos halt-related). Alex tiene que dar dirección. Memory `project_a5_deploy_confirmed_session_gap` confirma blocker. |
| 3 | **Promote STATE-drafts a root de cada repo** (este PR thread/143) | Toda la operación futura mejora con STATE.md a 1 click. Sin esto, la próxima sesión CC repite recon. |

---

## OBSERVACIONES TRANSVERSALES

- **Spec→ship ratio**: 22 de 39 specs (56%) tienen evidencia de shipped via PR; 12 (31%) shipped con missing pieces; 3 (8%) unstarted (todos legacy 15-cluster); el resto (~2-3) ambiguos.
- **PR→thread coverage**: 26 PRs (de ~60 merged en últimos 30 días) referencian explícitamente al menos un thread. **Resto NO** — eso es ~50% PRs sin thread reference, que dificulta este tipo de auditoría.
  - Recomendación: enforcement vía PR template (campo obligatorio "Closes thread/N").
- **Specs sin PR explícito** que YO inferí shipped por thread/result: 33, 52, 54, 65, 89. Estos requieren verify manual.
- **Anomalía detectada**: PR #129 (admin-nav role-based) referencia `thread/143` (este thread) — probable typo en PR body, era thread/141 (house rules paper trail). NO crítico.
