# A6 — Docs META drift analysis

**Generated**: 2026-05-22 (CC, thread/176)
**Scope**: META docs across `rdm-bot`, `rdm-discussion`, `rdm-platform`
**Method**: Read-only diff-by-eye of canonical docs vs. filesystem reality. Citations format `path:section` for traceability.

---

## §1 — Inventario docs por repo

### rdm-bot (code repo)

| Doc | Size (bytes) | Last commit (best effort) | Purpose |
|---|---|---|---|
| `CLAUDE.md` | 7 826 | recent | CC-Bot operating manual (anti-patterns, workstream territories, bucket guidance) |
| `STATE.md` | 11 197 | 2026-05-20 | Current stack snapshot (deploys, branches, migrations, pending decisions) |
| `OPEN_QUESTIONS.md` | 22 178 | 2026-05-08 onwards | Historical conservative decisions from PR1/PR2/PR3 — many no longer apply |
| `README.md` | n/a | recent | Project README |
| `PROPUESTA-CLAUDE-CODE.md` | 18 KB | older | Original Claude Code proposal |
| `PROPUESTA-TOUR-360.md` | 18 KB | older | Tour 360 proposal |
| `.claude/settings.json` | 7 KB | 2026-05-19 | CC permission allow/ask/deny lists + referenced scripts |
| `.mcp.json` | — | recent | MCP server config |
| `docs/secrets-inventory.md` | — | recent | Canonical secrets catalog (no values) |
| `docs/beds24-api-v2.yaml` | large | 2026-05-22 | Mirror of Beds24 v2 OpenAPI spec |
| `docs/DEPLOY_RUNBOOK.md` | — | recent | Deploy steps |
| `docs/karina-onboarding.md` | — | recent | Karina onboarding |
| `docs/spec/` | many | recent | Per-feature specs (auth, architecture, etc.) |

### rdm-discussion (comms repo)

| Doc | Lines | Notes |
|---|---|---|
| `CLAUDE.md` | 63 | Discussion-repo CC instructions |
| `CONTEXT.md` | 222 | Verified context 2026-05-11 (oldest of the canonical docs) |
| `STATE.md` | 86 | Updated 2026-05-20 (top 15 threads, ADR list, decisions for Alex) |
| `VISION.md` | 226 | Architecture target v2 — updated 2026-05-11 |
| `ROADMAP.md` | 205 | Draft, 2026-05-10 — phase 0-4 (~6 months) |
| `BACKLOG.md` | 467 | Living backlog with changelog 2026-05-18 |
| `QUESTIONS.md` | 179 | Open questions early-2026-05 era, mostly unupdated |
| `airbnb-cutover-handoff-cc.md` | 486 | Specific cutover handoff |
| `README.md` | 94 | Repo README |
| `decisions/` | 9 ADRs (01-09) | All "operational"-flavor (monorepo, channels, pricing, admin, auth, future-modules, pwa, orchestration, bots-llm) |
| `cc-instructions/` | 7 specs (2026-05-12 → 2026-05-17) | Path A specs |
| `cc-instructions-bot/` | 10 specs (2026-05-15/16 era) | Pre-thread era specs |
| `cc-instructions-data/` | 3 specs | Data-pipeline specs |
| `wc-instructions/` | 2 specs | WC self-instructions |
| `templates/` | `bot-claude-settings.json` only | Template store |
| `threads/` | 209 files | The main artifact ([[a1-threads-inventory]]) |
| `reports/` | 3 prior + 10 new (this PR) | Audit reports archive |

> Note: `rdm-discussion/decisions/` (operational ADRs 01-09) is a parallel decisions store to `rdm-platform/decisions/` (architectural ADR-001/002/003). [Source: `rdm-discussion/STATE.md` §C, `rdm-platform/STATE.md` §B.]

### rdm-platform (conceptual repo)

| Doc | Purpose |
|---|---|
| `README.md` | Repo charter |
| `STATE.md` | "What's live conceptually" snapshot — last 2026-05-21 |
| `decisions/ADR-001-platform-shift.md` | Accepted 2026-05-17 — platform shift |
| `decisions/ADR-002-foundations-seal.md` | Accepted 2026-05-20 — F1/F2/F3 seal |
| `decisions/ADR-003-cron-strategy-plan-stance.md` | — |
| `decisions/README.md` | Index |
| `foundations/00-platform-constraints.md` | Constraints doc |
| `foundations/F1-events-bus.md` | F1 spec (events bus) — **not implemented** |
| `foundations/F2-observability.md` | F2 spec (observability) — **not implemented** |
| `foundations/F3-staff-pwa.md` | F3 spec (staff PWA) — **not implemented** |
| `foundations/README.md` | Index |
| `vision/01-philosophy.md` | Spirit + Alex mental model |
| `vision/02-wishlist.md` | 5 modules + 19 ideas |
| `modules/{admin-tools,bot,content,data-pipeline,inventory,menu,pricing,staff-scheduling,tasks}/README.md` | 9 module placeholders |
| `coordination/README.md` + `doit-template.md` + `roles-and-permissions.md` | Coordination layer |
| `ideas/README.md` | I1-I19 referenced |
| `work/wave-1-audit-fixes.md` | Active work doc |
| `reports/` | platform audit reports |

---

## §2 — Cross-references graph (adjacency)

Direction: A → B = doc A references / depends-on doc B.

| From | To | Type |
|---|---|---|
| `rdm-bot/CLAUDE.md` | `rdm-bot/STATE.md` | "consulta STATE.md para vigente" |
| `rdm-bot/CLAUDE.md` | `rdm-bot/scripts/{new-thread,new-migration,safe-deploy,sync-secret}.sh` | hard dependency for atomic claims |
| `rdm-bot/CLAUDE.md` | `rdm-bot/docs/secrets-inventory.md` | canonical secrets table |
| `rdm-bot/STATE.md` | `rdm-bot/migrations/`, `apps/`, `packages/` | factual claims |
| `rdm-bot/STATE.md` | `rdm-discussion/threads/{134..149}` | threads cited for context |
| `rdm-bot/STATE.md` | `rdm-platform/decisions/ADR-002` | foundations seal |
| `rdm-discussion/CLAUDE.md` | `rdm-discussion/STATE.md`, `cc-instructions-*/` | mode descriptions |
| `rdm-discussion/STATE.md` | `rdm-discussion/threads/*` + `decisions/01-09` | |
| `rdm-discussion/VISION.md` | `rdm-discussion/decisions/01..09` | each principle cites a decision |
| `rdm-discussion/ROADMAP.md` | `rdm-discussion/VISION.md` + `decisions/*` | |
| `rdm-discussion/BACKLOG.md` | `rdm-discussion/threads/{115,121,...}` + `apps/*` | active backlog |
| `rdm-platform/STATE.md` | `rdm-discussion/threads/{89,91,143,145,146,147,148}` | |
| `rdm-platform/STATE.md` | `rdm-platform/coordination/roles-and-permissions.md` | RW/RO matrix |
| `rdm-platform/decisions/ADR-002` | `rdm-platform/foundations/F{1,2,3}-*.md` + `rdm-discussion/threads/{145..148}` | seal cite |
| `rdm-platform/foundations/F2-observability.md` | `rdm-bot/migrations/0042` (claim), `rdm-bot/packages/shared/src/{metrics,alerts,cron-heartbeat}.ts` (claim) | **drift — see §5** |

---

## §3 — Contradictions detected (Doc A vs Doc B)

### C1. STATE.md `apps/` list (bot) vs filesystem

`rdm-bot/STATE.md` §A claims 4 apps: `web`, `worker-bot`, `worker-pago`, `worker-tours`.
Filesystem: 5 apps — `web`, `worker-bot`, `worker-pago`, `worker-tours`, **`worker-feedback`**.

Impact: STATE.md is stale by one worker. `worker-feedback` was added but not propagated to STATE.md §A.

> Verifiable: `ls c:/dev/rdm/dev/bot/apps/` returns `worker-feedback`.

### C2. Migration 0039 collision (STATE.md vs filesystem)

`rdm-bot/STATE.md` §D claims:
- `0039_audit_log.sql` pending ⚠️
- `0039_rules_link_clicks.sql` pending ⚠️ (collision con 0039_audit_log)
- §G calls this an open Alex decision: "renombrar la segunda a 0040..."

Filesystem (as of 2026-05-22) shows `0039_audit_log.sql` AND `0040_rules_link_clicks.sql` (distinct numbers). Git log: PR #140 (`dade0d3`, 2026-05-21) renamed the duplicate.

Impact: STATE.md §D/§G are stale — the collision has already been resolved. Both entries should be removed.

### C3. ROADMAP.md `apps/` (target) vs STATE.md (current)

`rdm-discussion/VISION.md` proposes 9 apps (`site`, `bot`, `admin`, `api`, `pricing`, `webhooks`, `tours`, `disponibilidad`, `worker-pago`).
Reality: 5 apps (`web`, `worker-bot`, `worker-feedback`, `worker-pago`, `worker-tours`).

VISION explicitly tags some as "Sprint 2-3-4" so the gap is not literal drift — but VISION has not been updated since 2026-05-11 and now diverges from delivered architecture (e.g., `worker-feedback` not foreseen, `worker-pago` keeps both webhook + cron + auth — not deprecated as VISION suggested).

### C4. `apps/admin` PWA — claimed in VISION/QUESTIONS/decisions, never built

- `VISION.md` §"Apps": `admin.rincondelmar.club` Sprint 2.
- `decisions/04-admin-board.md`: React + shadcn + TanStack + PWA.
- `decisions/07-pwa-mobile.md`: PWA Day 1.
- `bot/OPEN_QUESTIONS.md` PR3 §24: manifest.json + service worker basic.

Reality:
- No `apps/admin` directory.
- Admin pages live in `apps/web/src/pages/admin/`.
- No `apps/web/public/manifest.json` (but `sw.js` exists).

Impact: VISION/decisions describe a fundamentally different shape than what was built. Either VISION needs to be rewritten to reflect "admin = subpages of web" (true), or the migration to `apps/admin` is a real backlog item that's gone unspoken for months.

### C5. Decisions store split (rdm-discussion vs rdm-platform)

- `rdm-discussion/decisions/01-09` (operational): monorepo, channels, pricing, admin, auth, future modules, pwa, orchestration, bots-llm. No formal status header.
- `rdm-platform/decisions/ADR-001/002/003`: numbered, frontmatter-styled, "Accepted" status, "Supersedes" lines.

`rdm-discussion/STATE.md` §C explicitly disambiguates: "ADR-001-platform-shift está en `rdm-platform/decisions/`, NO aquí." But there is no doc that explains the two-store policy. Two readers of the codebase will struggle to know which decision store is canonical for what.

### C6. CC role in rdm-platform — boundary stated, not enforced

`rdm-platform/STATE.md` §B: "CC: RO + feedback/ subfolder cuando se le pida. CC NO escribe aquí sin invitación explícita."

There is no `feedback/` folder yet in rdm-platform. The thread/176 spec also defers all platform writes — but the policy is recent and not propagated to `rdm-bot/CLAUDE.md` (which lists CC-Platform as WC-RDM-Strategy territory and never declares the RO+feedback boundary).

### C7. WC vs CC implementation territories (CLAUDE.md vs STATE.md)

`rdm-bot/STATE.md` §E: "WC NO implementa código en rdm-bot ni rdm-platform (2026-05-19 Alex correction). WC = specs + threads + reviews + brain mode. CC reta + implementa."

`rdm-bot/CLAUDE.md` does not say this anywhere — it lists CC workstream territories but does not constrain WC. Net effect: anti-pattern enforced by one doc only; new sessions reading CLAUDE.md alone could miss it.

### C8. STATE.md vs §"Last deploys" reality

`rdm-bot/STATE.md` §A: "Last deploys captured 2026-05-20". `worker-pago` last deploy 2026-05-12. But thread/170 reports Telegram pago-notify PR #159 merged 2026-05-22. Either the deploy didn't happen or §A is stale by 10+ days. **STATE.md is the canonical recency claim and should be updated whenever a worker deploys.**

---

## §4 — Decisions stated in one doc, missing from others

| Decision (source) | Should propagate to | Status |
|---|---|---|
| ADR-001 platform shift (`rdm-platform/decisions/`, 2026-05-17 Accepted) | `rdm-discussion/STATE.md` §C — references but does not summarize | partially propagated |
| ADR-002 foundations seal (2026-05-20) | `rdm-bot/STATE.md` §G mentions thread/147/148 but does not name ADR-002 | partially propagated |
| ADR-003 cron strategy | not mentioned in either STATE.md | NOT propagated |
| "F2 ships first in F2→F1→F3 order" (ADR-002 §2) | `rdm-bot/STATE.md` §G mentions "Alex thread/148 vote pending" — does not state the order is sealed | stale |
| "WAE primary, audit_log reserved for staff actions" (F2 §3.2 + Alex 148 §A#9) | `rdm-bot/CLAUDE.md` anti-patterns — does not record | not propagated |
| "WC does not implement code in rdm-bot/rdm-platform" (2026-05-19 Alex correction) | `rdm-bot/CLAUDE.md` says nothing; only `STATE.md §E` records it | docs split |
| "CC = RO in rdm-platform" (rdm-platform/STATE.md §B) | `rdm-bot/CLAUDE.md` Multi-CC table mentions CC-Platform = WC-RDM-Strategy territory but does not state CC-from-bot has RO access | partially propagated |
| Q3 voto Casa Chamán "ignorar" (thread/175 §alex_votes_constraints) | `rdm-bot/CLAUDE.md` Casa Chamán reminder still says "NO surfacar en Greeter prompt hasta Q3 2026" — consistent, BUT thread/175 records Alex saying "ignorar" for now | aligned but no record in STATE |
| Q4 ranking (operativo → foundations → M1-M5) per Alex in thread/171→174 chain | not in any STATE.md or ADR | not formalized — captured only in threads |

---

## §5 — Ficciones detected (referenced but absent)

| Item | Referenced in | Actual status | Impact |
|---|---|---|---|
| `scripts/new-thread.sh` | `bot/CLAUDE.md:65,70,119,127` + `.claude/settings.json:77` | **Does not exist** in any of the 3 repos | HIGH — CLAUDE.md instructs CC to use it for "atomic claim" of thread numbers; without it, the very race condition CLAUDE.md warns about (collision of thread numbers) is structurally guaranteed. 22 thread number collisions detected ([[collisions]]). |
| `scripts/next-thread-number.sh` | `bot/.claude/settings.json:80` | **Does not exist** | HIGH — same problem. Settings.json allow-lists a script that does not exist. |
| `apps/admin` PWA | `VISION.md` §"Apps"; `decisions/04`; `decisions/07`; `OPEN_QUESTIONS.md` PR3 §24 | **Does not exist** as separate app; admin pages live under `apps/web/src/pages/admin/`; no `manifest.json` | MEDIUM — recurring confusion between "admin = subpages" (current) vs "admin = separate PWA app" (target). 5+ docs claim the latter. |
| Migration 0042 = `cron_heartbeats` | `rdm-platform/foundations/F2-observability.md` §3.3 | Migration 0042 in workspace is `0042_feedback_system.sql` (thread/161 admin issues cockpit) | MEDIUM — F2 spec writes "migrations/0042_cron_heartbeats.sql" as if reserved; reality consumed 0042 for a different purpose. F2 ship needs to claim 0046+ via `scripts/new-migration.sh` and update the spec. |
| `packages/shared/src/metrics.ts` | F2 §3.2 spec block (`emitMetric` helper) | **Does not exist** | MEDIUM — F2 not implemented. Spec is the deliverable; absence is expected pre-ship, but spec readers may assume it shipped because ADR-002 says "Accepted". |
| `packages/shared/src/alerts.ts` | F2 §3.5 | **Does not exist** | same as above |
| `packages/shared/src/cron-heartbeat.ts` | F2 §3.3 | **Does not exist** | same as above |
| `cron_heartbeats` D1 table | F2 §3.3 | **Does not exist** in any migration | same as above |
| WAE binding `METRICS` in workers | F2 §3.2 | Not in `apps/worker-*/wrangler.toml` | same as above |
| F1 outbox / dispatcher / DLQ | `rdm-platform/foundations/F1-events-bus.md` | **Not implemented** in `apps/` | EXPECTED — pre-ship spec |
| F3 staff PWA shell | `rdm-platform/foundations/F3-staff-pwa.md` | **Not implemented** | EXPECTED |
| `rdm-platform/foundations/00-charter.md` | `rdm-platform/STATE.md` §A ("Charter document referenciado en foundations/README como pendiente") | **Does not exist** | LOW — explicitly tracked as pending; not a ficción, just unwritten |
| `apps/pricing`, `apps/api`, `apps/webhooks`, `apps/disponibilidad` | `VISION.md` §"Apps" table | **Do not exist** (logic absorbed into `worker-pago`, `worker-bot`, `web`) | LOW — VISION explicitly labels each as Sprint 2/3/4 — roadmap, not current state. But absence of "Sprint 2 deferred" note creates confusion. |
| `packages/beds24`, `packages/pricing-agent`, `packages/ui` | `VISION.md` §"Stack final" packages diagram | **Do not exist** as separate packages | LOW — Beds24 logic lives across `apps/worker-bot` + agents; pricing not split out yet |
| `apps/web/public/manifest.json` | `OPEN_QUESTIONS.md` PR3 §24 (claimed shipped) | **Does not exist** (but `sw.js` does) | LOW — PR3 conservative-decision claim is invalidated; no functional impact since PWA install was never wired |
| `audit_log` D1 table | `rdm-bot/STATE.md` §D mentions migration 0039_audit_log applied | LIVE — migration 0039 applied, table exists ✅ | n/a — included as positive verification |
| ID `KV_IDEMPOTENCY` | `rdm-bot/CLAUDE.md` Stack snapshot | Reality: `KV_KNOWLEDGE` in STATE.md §A | LOW — KV binding rename or naming drift between docs |
| `KV_KNOWLEDGE` ID `033ee15acf3744c096e83342d2e81dd4` | `rdm-bot/STATE.md` §A | Confirmable via wrangler — assume true | n/a |

---

## §6 — VISION vs reality drift

| Component | VISION says | Reality | Gap |
|---|---|---|---|
| `apps/site` (renamed from `apps/web`) | renamed to `apps/site` (semántica) | still `apps/web` | rename never executed; cosmetic only |
| `apps/admin` PWA on `admin.rincondelmar.club` | Sprint 2 — separate Worker Static Assets | admin lives in `apps/web/src/pages/admin/*`, no separate worker | drift acknowledged but not closed; need to rewrite VISION or actually split |
| Stage 2 WhatsApp Cloud API direct | Fase 3 (mes 3-4) | Still ManyChat BSP only | on roadmap, not started |
| `apps/pricing` Worker cron | Sprint 3 | not implemented | on roadmap |
| `apps/webhooks` Worker for MP/Meta/Beds24 | Sprint 3 | logic still in `worker-pago` (MP) + `worker-bot` (Beds24) | drift — webhooks centralization not done |
| Better Auth as canonical | `decisions/05` proposes magic-link + Better Auth | LIVE in production ✅ | aligned |
| PriceLabs $100/mes | `decisions/03` recommends buy | Custom pricing agent kept (per VISION principle 7 + STATE) | aligned with revision |
| Monorepo Turborepo + pnpm | `decisions/01` | LIVE ✅ | aligned |
| F1 events bus LIVE | foundations claims "spec only, not implemented" | matches | aligned (negative) |
| F2 observability LIVE | ADR-002 "Accepted 2026-05-20" suggests CC will ship | not started (no `cron_heartbeats`, no `metrics.ts`) | clear gap — ADR acceptance does NOT mean implementation |
| F3 staff PWA LIVE | foundations "not implemented" | matches | aligned (negative) |
| Stage 1 ManyChat BSP active | yes | yes | aligned |
| 5 propiedades activas + Casa Chamán Q3 2026 | yes | yes | aligned |
| Cron triggers in `worker-pago` (5+ active) | acknowledged | yes (CF Free plan 5-cron cap reached) | aligned |
| Telegram alerts | not formal in VISION | LIVE via `worker-pago` notifications (PR #159, thread/170) | shipped but not back-ported to VISION |
| `audit_log` table | not in VISION | LIVE (migration 0039) | shipped but not in VISION; semantic boundary clarified by F2 spec |
| Beds24 v2 API canonical | not in VISION | spec mirror at `docs/beds24-api-v2.yaml`; `invoiceItems` via `POST /v2/bookings` (CLAUDE.md note) | aligned — CLAUDE.md is the source of truth here |

---

## §7 — `decisions/` (rdm-discussion) — current status check

`rdm-discussion/STATE.md` §C lists ADRs 01-09. Each ADR has no formal "Accepted" status header. Spot check 5 of the 9:

| ADR | Topic | Effective status | Evidence |
|---|---|---|---|
| `01-monorepo-structure` | Turborepo + pnpm | LIVE / Accepted-de-facto | repo is Turborepo + pnpm |
| `02-channel-strategy` | Two-stage, ManyChat BSP Stage 1 | LIVE Stage 1; Stage 2 not started | matches roadmap |
| `03-pricing-agent` | Buy PriceLabs | REVISED / Rejected | `decisions/03` says buy; VISION §"Principios 7" says custom agent kept; reality: no PriceLabs subscription. ADR not updated to reflect revision. |
| `04-admin-board` | React + shadcn + TanStack + PWA at `admin.rincondelmar.club` | PARTIAL / drift | admin pages exist but inside `apps/web`, no separate PWA, no `admin.rincondelmar.club` |
| `05-auth-magic-link` | Better Auth extended | LIVE | Better Auth in production |
| `06-future-modules` | structural | conceptual / superseded by rdm-platform `vision/02-wishlist.md` + modules/ | not removed but content has migrated |
| `07-pwa-mobile` | PWA Day 1 | PARTIAL | `sw.js` exists but no manifest, no install prompt |
| `08-orchestration` | Workflows + Queues + DOs replace Make | PARTIAL | Make sunset in progress; no Workflows in `wrangler.toml` |
| `09-bots-llm-architecture` | port + clean refactor | LIVE | Greeter/Booker shipped |

Pattern: ADRs lack formal status fields. Several are stale or have been silently revised in newer threads/ADRs.

---

## §8 — Discussion repo `cc-instructions*` — historical specs not closed

Spec docs in `cc-instructions/`, `cc-instructions-bot/`, `cc-instructions-data/` are essentially old DoIt specs from before the thread system stabilized. Many do not have a corresponding "result thread" or PR-merged confirmation:

| Spec | Closed? |
|---|---|
| `cc-instructions/2026-05-12-greeter-v5-challenge-CONSOLIDATED.md` | LIVE (Greeter v5 prompt deployed) |
| `cc-instructions/2026-05-13-execute-batch-b-fase-1-5-mvp.md` | mostly LIVE |
| `cc-instructions/2026-05-14-import-wc-seed-drafts-and-karina-onboarding.md` | partial — Karina onboarding doc exists |
| `cc-instructions/2026-05-17-platform-wishlist-feedback.md` | migrated to `rdm-platform/vision/02-wishlist.md` |
| `cc-instructions-bot/2026-05-16-admin-bookings-and-inbox-DELTA.md` | shipped (admin bookings + inbox merged) |
| `cc-instructions-bot/2026-05-16-pr-a61-v6-combined.md` | shipped (Greeter v6 prompt) |
| `cc-instructions-data/2026-05-16-vectorize-handoff.md` | LIVE per BACKLOG.md 2026-05-18 changelog |

Recommendation (NOT executing): mark each spec doc as "closed" or move to `archive/` so the active set is small.

---

## §9 — Stack snapshot drift (CLAUDE.md vs STATE.md)

`rdm-bot/CLAUDE.md` "Stack actual" lists:
> apps/: web, worker-bot, worker-pago, worker-tours

`rdm-bot/STATE.md` §A lists same 4. Reality: 5 apps (adds `worker-feedback`).

`CLAUDE.md` says: "consulta STATE.md para vigente" — but STATE.md itself is stale on this point. Both should be updated, with CLAUDE.md narrowing to "see STATE.md" rather than restating.

---

## §10 — TL;DR drift summary

1. **`scripts/new-thread.sh` is fiction.** CLAUDE.md instructs its use; allowlist permits it; the file does not exist. Result: 22 thread number collisions ([[collisions]]).
2. **F2 ADR-002 "Accepted" ≠ implemented.** Spec claims migration 0042 = `cron_heartbeats`; reality 0042 = `feedback_system`. No `metrics.ts`, no `alerts.ts`, no cron_heartbeats table. ADR acceptance is a paper milestone, not a code milestone.
3. **STATE.md `apps/` list stale.** `worker-feedback` shipped, never added to STATE.md or CLAUDE.md.
4. **Migration 0039 collision still listed in STATE.md §D/§G.** Already resolved by PR #140 (2026-05-21). Remove.
5. **`apps/admin` PWA is a 5-doc fiction.** VISION + ADR-04 + ADR-07 + OPEN_QUESTIONS + roadmap claim a separate PWA app; the admin lives inside `apps/web`. Either rewrite docs or accept this as known backlog.
6. **Two parallel decisions stores (`rdm-discussion/decisions/01-09` and `rdm-platform/decisions/ADR-001+`)** with no doc explaining the split. New reader confusion.
7. **`decisions/03 PriceLabs` and `decisions/04 admin-board` are silently superseded** — never updated; readers will follow stale guidance.
8. **CLAUDE.md operating manual drift** — STATE.md §E ("WC NO implementa código en rdm-bot/rdm-platform") is not in CLAUDE.md; CC sessions reading only CLAUDE.md could miss it.
9. **209 threads, 7 with YAML frontmatter, 202 in legacy markdown-bold-header format** — no consistent metadata; cross-referencing is fragile.
10. **`OPEN_QUESTIONS.md` (22 KB) is mostly historical** — PR1/PR2/PR3 conservative decisions from 2026-05-08 era. Should be archived or summarized.

---

## §11 — Linked reports

- [[a1-threads-inventory]] (`2026-05-22-META-A1-threads-inventory.{md,json}`)
- [[a2-prs-inventory]] (`2026-05-22-META-A2-prs-inventory.{md,json}`)
- [[a3-migrations-inventory]] (`2026-05-22-META-A3-migrations-inventory.{md,json}`)
- [[a4-branches-inventory]] (`2026-05-22-META-A4-branches-inventory.{md,json}`)
- [[a5-cross-reference-matrix]] (`2026-05-22-META-A5-cross-reference-matrix.{md,json}`)
- [[a7-pending-decisions]] (next)
- [[a8-lost-work-orphans]] (next)
- [[a9-master-synthesis]] (next)
- [[collisions]] (`2026-05-22-META-collisions.md`)
