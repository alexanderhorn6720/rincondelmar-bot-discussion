# rdm-discussion · STATE (draft)

> Coordination layer: threads, specs, decisions, CC/WC instructions. NO code.
> Generado por CC vía DoIt thread/143 (2026-05-19).

---

## A. THREADS ACTIVOS ESTA SEMANA (modificados últimos 7d)

| #   | Título corto                                       | Esperando            | Desde       |
|-----|----------------------------------------------------|----------------------|-------------|
| 143 | state-system + threads audit (este PR)             | CC ejecutando        | 2026-05-19  |
| 142 | house rules paper trail Phase 1 done (CC→WC)       | WC review            | 2026-05-19  |
| 141 | house rules paper trail Phase 1 DoIt (WC→CC)       | CC shipped (142)     | 2026-05-19  |
| 140 | A6 reglas_adicionales complete 8/8 cells           | Alex review PR #130  | 2026-05-19  |
| 139 | A6 reglas_adicionales deploy 8 cells DoIt          | CC shipped (140)     | 2026-05-19  |
| 138 | A5 completion 67% deployed, 30% structural skips (untracked local) | Alex decisión next step | 2026-05-19 |
| 137 | A5 halt: rincondelmar session missing (untracked)  | Alex provision sesión | 2026-05-19  |
| 136 | A5 halt: stale MCP process (untracked)             | resolved local        | 2026-05-19  |
| 135 | Beds24 proxy phase 1 complete (PR #127)            | Alex deploy + verify | 2026-05-19  |
| 134 | Beds24 read-only proxy DoIt spec                   | CC shipped (135)     | 2026-05-19  |
| 133 | mobile inbox Part E rescue complete (PR #126 merged)| -                   | 2026-05-19  |
| 132 | Browserbase + AirBnB KPI scraper backlog item      | Alex decisión        | 2026-05-19  |
| 131 | mobile inbox Part E rescue DoIt (completing 107§5) | CC shipped (133)     | 2026-05-19  |
| 130 | A5 halt: chrome MCP not attached (untracked)       | resolved local        | 2026-05-19  |
| 129 | omnibus DoIt report                                | -                    | 2026-05-19  |
| 128 | omnibus open items DoIt pre-A5                     | CC shipped (129)     | 2026-05-19  |
| 127 | A5 execution DoIt autonomous                       | en progreso (ver 138)| 2026-05-19  |
| 126 | 500 root cause + fix shipped                       | resolved             | 2026-05-19  |
| 125 | karina training deploy V2                          | resolved             | 2026-05-18  |
| 124 | karina training deploy handoff                     | resolved (125)       | 2026-05-18  |
| 123 | canary review HSM critical/defer/cancel-race       | Alex decisión        | 2026-05-18  |
| 122 | canary results + ManyChat architecture findings    | resolved (123)       | 2026-05-18  |
| 121 | A2+A3 review + A4 amendment + A5 spec              | CC ejecutando (127)  | 2026-05-18  |
| 120 | A1+A1.5 retroactive approval + A2 design           | resolved             | 2026-05-18  |
| 119 | pre-stay MVP spec ready                            | shipped via #112-113 | 2026-05-18  |
| 118 | pet policy correction + v5 cleanup spec            | shipped              | 2026-05-18  |
| 117 | handoff doc reconciliation                         | resolved (118)       | 2026-05-18  |
| 115 | DoIt guests.name resync from Beds24                | shipped              | 2026-05-18  |
| 113 | hotfix /proxReservas guest name                    | shipped              | 2026-05-18  |

## B. SPECS PENDING SHIP (type=spec sin result thread)

| #   | Spec título                                     | Days open | Quien implementa |
|-----|-------------------------------------------------|-----------|------------------|
| 132 | Browserbase eval + AirBnB KPI scraper backlog   | 0         | Alex decide      |
| 127 | A5 execution autonomous (paused ~67%)           | 0         | CC bot (blocked) |
| 123 | canary review HSM/defer/cancel-race             | 1         | Alex decisión    |

## C. ADRs VIGENTES (decisions/)

- `01-monorepo-structure.md`
- `02-channel-strategy.md`
- `03-pricing-agent.md`
- `04-admin-board.md`
- `05-auth-magic-link.md`
- `06-future-modules.md`
- `07-pwa-mobile.md`
- `08-orchestration.md`
- `09-bots-llm-architecture.md`

> 9 ADRs vigentes. ADR-001-platform-shift está en `rdm-platform/decisions/`, NO aquí.

## D. WORKING MODES / CONVENTIONS

- Working modes documentados en `CLAUDE.md` (brain / DoIt / verify).
- DoIt template versión actual: **v3** (thread/94 ack clone paths). Vive INLINE en CLAUDE.md + ejemplos en threads recientes (143 mismo es DoIt v3).
- NO existe `coordination/` folder (vive en CLAUDE.md). `coordination/` con `doit-template.md` + `roles-and-permissions.md` está en `rdm-platform`, NO aquí.
- Spec doc template: 7 secciones obligatorias (Context, Scope, Decisions, Implementation, Tests, DoD, Risks).
- Path convention specs: `cc-instructions-{workstream}/YYYY-MM-DD-{name}.md`.

## E. OUTSTANDING DECISIONS PARA ALEX

- **A5 Airbnb bulk-approve**: 67% completo, 30% skips estructurales (thread/138). Decidir: shipear lo deployable + ticket follow-up, o esperar hasta 100%.
- **Browserbase vs Chrome DevTools MCP** (thread/132): evaluar costo + ROI.
- **PR #130 A6 reglas_adicionales**: review + merge + deploy.
- **PR #114 journey templates editor**: review + merge.
- **Canary HSM critical path** (thread/123): aprobar defer estrategia durante/post + cancel-race fix.
- **STATE-drafts promotion** (este PR thread/143): copiar a root de cada repo post-aprobación.
- **Casa Chamán timeline**: cuándo Greeter prompt unhide (Q3 2026 placeholder).

## F. CONVENCIONES

- Threads naming: `XX-{author}-{topic}.md` sequential.
- Authors: `wc` (web claude — strategist), `cc` (claude code — generic), `cc-bot` (CC dedicado rdm-bot repo), `cc-data` (CC dedicado data pipeline), `alex` (humano).
- PR prefijos: A* = CC-Bot, D* = CC-Data (legacy; ahora sólo `feat/fix/chore/`).
- Branches: `feat/*`, `fix/*`, `chore/*`, `hotfix/*`, `debug/*`. No `claude/*` para ship-able (sólo CC sandbox).
- Commits: Conventional Commits (feat/fix/test/docs/chore + scope).
- Squash-merge PRs a main.
- `rdm-discussion` = comms layer + specs + threads, **NO código** (apps/packages no existen aquí).
- Idioma: español para threads/specs internos, mixto para anti-patterns enforced y referencias técnicas.
- Threads dupes (mismo número, dos archivos): aceptados cuando segundo deprecia primero (e.g. `105-...-p3.md` vs `105-...-p3-plus-2bugs.md`; `77-cc-bot-...` vs `77-cc-data-...`).

## G. LAST UPDATED + UPDATE PROTOCOL

- Fecha generación: 2026-05-19
- Por: CC vía DoIt thread/143
- Próxima refresh: cuando se cierre/abra spec, o se agreguen ≥3 threads nuevos.
- **Update protocol:** todo PR a este repo toca §A si modifica threads/, toca §E si afecta decisión pendiente, toca §C si agrega ADR.
- Promote-to-root: Alex copia → `rdm-discussion/STATE.md` post-PR aprobación.
