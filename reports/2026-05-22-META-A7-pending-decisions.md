# A7 — Pending decisions consolidated

**Generated**: 2026-05-22 (CC, thread/176)
**Sources**: `rdm-bot/STATE.md §G`, `rdm-bot/OPEN_QUESTIONS.md`, `rdm-discussion/STATE.md §E`, `rdm-discussion/QUESTIONS.md`, `rdm-platform/STATE.md §C`, threads 145-176.

Categories used:
- **provisioning**: blocked on Alex doing CF dashboard / API key / DNS / etc.
- **business**: requires Alex business judgment
- **technical**: requires WC/CC technical choice
- **stale**: raised >30 days ago, no movement

---

## §1 — Overview

| Source | Items |
|---|---|
| `rdm-bot/STATE.md §G` | 7 |
| `rdm-bot/OPEN_QUESTIONS.md` PR1/PR2/PR3 conservative decisions | 28 (mostly historical) |
| `rdm-discussion/STATE.md §E` | 7 |
| `rdm-discussion/QUESTIONS.md` Alex queue (A1–A10) | 10 |
| `rdm-discussion/QUESTIONS.md` CC queue (CC1–CC10) | 10 (mostly already-answered) |
| `rdm-discussion/QUESTIONS.md` Open research (R1–R6) | 6 |
| `rdm-platform/STATE.md §C` | 11 |
| Threads `*-question-*` / `status: open-for-alex-vote` style | <see A1> |

After deduplication and filtering out items already shipped/answered: **~38 net pending items**. The dominant audience is Alex (~25 of them).

---

## §2 — Pending decisions from `rdm-bot/STATE.md §G` (canonical, 2026-05-20)

| ID | Topic | Days open (raised → 2026-05-22) | Owner | Category | Blocks |
|---|---|---|---|---|---|
| G1 | A5 Airbnb bulk-approve writeback — 67% completion | ~3 d (since 2026-05-19) | Alex provision Better Auth session in Chrome:9222 + per-cell deploy-confirmed | provisioning | A5 100% completion |
| G2 | Browserbase AirBnB KPI scraper backlog | ~3 d (thread/132) | Alex | business | scraper start |
| G3 | A6 reglas_adicionales deploy — PR #130 review pending | ~3 d (since 2026-05-19) | Alex | business | PR #130 merge |
| G4 | Journey templates editor — PR #114 review pending | ~4 d (since 2026-05-18) | Alex | business | PR #114 merge |
| G5 | Casa Chamán renovation timeline — unhide in Greeter | open until Q3 2026 | Alex | business | Greeter content for Casa Chamán |
| G6 | PDF endpoint removal spec for CC | ~3 d (since 2026-05-19) | WC drafts spec → CC executes | technical | cleanup of broken `/reglas/{slug}/pdf` |
| G7 | F1/F2/F3 foundations + ADR-002 vote (thread/148) | ~3 d (since 2026-05-19) | Alex on 7 items in thread/148 | business + technical | M1 Pricing start |
| G8 | Analytics activation (thread/149) | ~3 d (since 2026-05-19) | Alex (cookieless CF only / CF+GA4 / +GSC) | business + provisioning | tracker emit + GA4 events readout |
| G9 | D1 migration 0039 collision rename | RESOLVED 2026-05-21 PR #140 | n/a | RESOLVED | — |

**G1, G6, G8 are also blocked on Alex provisioning.** G7 is the highest-impact pending: foundations seal blocks F2 ship which blocks F1 which blocks M1.

---

## §3 — Pending decisions from `rdm-discussion/STATE.md §E`

Largely duplicates STATE.md §G but framed slightly differently. Net-new items:

| ID | Topic | Notes |
|---|---|---|
| D1 | A5 Airbnb 67% (= G1) | dup |
| D2 | Browserbase vs Chrome DevTools MCP (= G2) | dup |
| D3 | PR #130 review (= G3) | dup |
| D4 | PR #114 review (= G4) | dup |
| D5 | Canary HSM critical path (thread/123) — Alex aprobar defer + cancel-race fix | NEW |
| D6 | STATE-drafts promotion thread/143 | RESOLVED 2026-05-20 |
| D7 | Casa Chamán timeline (= G5) | dup |

**D5** (canary HSM) is a net-new pending not in `rdm-bot/STATE.md §G`.

---

## §4 — Pending decisions from `rdm-platform/STATE.md §C`

| ID | Topic | Effort estimate | Status |
|---|---|---|---|
| P1 | ADR-002 charter / foundations seal | written | **Accepted 2026-05-20** ✅ |
| P2 | F1 events bus spec final + Service Bindings | 12-16h CC | spec accepted (ADR-002), implementation NOT started |
| P3 | F2 observability lite | 6-9h CC | spec accepted, **NOT shipped — see [[a6-docs-drift-analysis]] §10 #2** |
| P4 | F3 staff PWA shell | 22-30h CC (email-only) | spec, NOT shipped |
| P5 | M1 Pricing Agent deep spec | unspecified | not started (blocked on P2-P4) |
| P6 | M2 Menu spec | unspecified | placeholder only |
| P7 | M3 Inventory spec | unspecified | placeholder |
| P8 | M4 Staff scheduling spec | unspecified | depends F3 |
| P9 | M5 Tasks module spec | unspecified | placeholder |
| P10 | Casa Chamán launch coordinator spec | unspecified | Q3 2026 trigger, no doc |
| P11 | I1-I19 ideas — none expanded | unspecified | conceptual backlog |

**Critical path**: P3 (F2) → P2 (F1) → P4 (F3) → P5 (M1). All four block M1 Pricing.

---

## §5 — Pending decisions from `rdm-discussion/QUESTIONS.md` Alex queue

Most of these were raised 2026-05-10/11 (the seed era) and have been silently superseded. Status estimated from current state.

| ID | Topic | Probable status |
|---|---|---|
| A1 | Repo público / privado mid-migration | resolved (rdm-bot still private; rdm-discussion public) |
| A2 | PriceLabs vs alternativas | **SUPERSEDED** — custom agent kept per VISION §"Principios 7"; ADR not updated |
| A3 | Timing 4.5 meses (20h/sem Alex) | partly answered (work is happening, slower than plan) |
| A4 | WABA propia Stage 2 (número WA dedicated) | **OPEN** — pending Stage 2 |
| A5 | Pricing override layer Stage 2 | **OPEN** — depends on Stage 2 |
| A6 | Magic link único sin password | resolved YES — Better Auth shipped |
| A7 | Roles iniciales | resolved — 7 roles shipped per PR #129 |
| A8 | APK timing | **OPEN** — PWA Day 1 not delivered; APK farther |
| A9 | Sunset ManyChat completo | **OPEN** — pending Stage 2 cutover |
| A10 | Domain destinations finales | partly resolved — bot/pago/tours active subdomains; admin.rincondelmar.club not realized |

Net-new pending: A4, A5, A8, A9 (all Stage 2 dependent).

---

## §6 — `OPEN_QUESTIONS.md` (rdm-bot) — historical PR1/2/3 conservative decisions

`rdm-bot/OPEN_QUESTIONS.md` is 22 KB of decisions taken during PR1/PR2/PR3 (2026-05-08 era) with "Verificar:" markers. Most are stale; some still open.

### Net still-pending (from a 22 KB doc):

| ID | Topic | Status |
|---|---|---|
| Q3 | R2 binding + Make scenario `Knowledge_Refresh_v2` writes to R2 | partially resolved — R2 buckets exist |
| Q4 | Photos pipeline real fotos + CF Images variants | unclear status |
| Q5 | RESEND_API_KEY + RESEND_FROM_DOMAIN | resolved (Resend shipped) |
| Q6 | Turnstile sitekey + secret | unclear — may not be in use |
| Q7 | CF Web Analytics token | **OPEN — = G8** (analytics activation) |
| Q8 | CF Images hash | unclear status |
| Q10 | Lighthouse CI ≥ 95 | unclear — placeholder JSON |
| Q11 | Matterport URL canónico | partially resolved (tour 360 shipped) |
| Q14 | Worker cron triggered confirmation | resolved (5 crons live in worker-pago) |
| Q17 | Account merge UI | **OPEN — never implemented** |
| Q19 | EN translations review by Alex | unclear |
| T26-T31 | Tour 360 sprint 1+2 decisions | LIVE (tour 360 shipped) |

> Recommendation: archive `OPEN_QUESTIONS.md` to `docs/archive/OPEN_QUESTIONS-2026-05-08-PR1-PR3.md` and start a fresh `OPEN_QUESTIONS.md` for active items only.

---

## §7 — Pending decisions from threads 173–176 (latest)

These are recent threads with declared open decisions:

| Thread | Topic | Owner |
|---|---|---|
| 173 (WC-Platform) | Charter draft + ADR-001 §02 NO LLM money anti-pattern | WC-Platform |
| 174 (WC synthesis) | Test empírico multi-WC pre-formalize (Q1), Judge BI (Q2), Casa Chamán ignorar (Q3) | already voted by Alex in thread/175 frontmatter |
| 175 (WC DoIt P1+P2 quickwins) | T1-T5 execution (separate CC session, parallel to this audit) | CC (paralela) |
| 176 (this thread) | META archaeology (this report) | CC (this session) |

No net-new pending decisions from these threads beyond what's already captured above.

---

## §8 — Critical-path items (blocking 3+ downstream)

| ID | Item | Blocks |
|---|---|---|
| G7 / P3 | F2 observability ship | F1 ship, F3 ship, M1 Pricing, M5 Tasks, F2.1 daily digest |
| G7 / P2 | F1 events bus ship | M1 Pricing dispatcher, M5 notifications, I3/I5/I7/I8 ideas |
| G7 / P4 | F3 staff PWA ship | M3/M4/M5 modules, Casa Chamán launch coord |
| G8 / Q7 | Analytics activation | A/B tests readout, GA4 events readout, conversion tracking, GSC verify |
| G6 | PDF endpoint removal spec | cleanup, prevents bad-PR loop |
| G1 | A5 Airbnb session + writeback | content sync to Airbnb listings |
| A9 / 02 | Stage 2 ManyChat sunset | A4 WABA, A5 pricing override, true ownership of WA channel |

---

## §9 — Stale items (>30 d open)

| ID | Topic | Days |
|---|---|---|
| A2 (PriceLabs) | 12 d (since 2026-05-10) — superseded silently | flag for ADR-03 update |
| A4 (WABA) | 12 d | strategic, Stage 2 dependent |
| A8 (APK) | 12 d | strategic |
| A9 (ManyChat sunset) | 12 d | strategic |
| Q17 account merge UI | 14 d | never re-raised |

(None ≥30 d in this dataset because rdm-discussion repo's earliest entries are 2026-05-10, only 12 days ago. The codebase is young.)

---

## §10 — Recommendation summary (NO executing)

1. **Resolve G7 (Alex vote on thread/148)** — it gates the entire foundations and M1 path.
2. **Close G6 (PDF removal spec)** — WC drafts, CC executes; one PR.
3. **Resolve G8 (analytics activation)** — Alex picks variant; CC adds 2 env vars; ships in 1h.
4. **Archive `OPEN_QUESTIONS.md`** — too much noise; net-new pending items can re-emerge as threads.
5. **Update `decisions/03` (PriceLabs) status** — mark superseded by VISION §"Principios 7"; cite custom agent kept.
6. **Add an Anti-pattern ADR for "WC does not implement code in rdm-bot/rdm-platform"** — to propagate from STATE.md §E to CLAUDE.md.

(All recommendations are advisory — this report does not execute fixes.)

---

## §11 — Linked reports

- [[a1-threads-inventory]]
- [[a5-cross-reference-matrix]]
- [[a6-docs-drift-analysis]]
- [[a8-lost-work-orphans]] (next)
- [[a9-master-synthesis]] (next)
