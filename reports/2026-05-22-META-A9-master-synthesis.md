# A9 — META archaeology master synthesis

**Generated**: 2026-05-22 by CC in thread/176 (`feat/meta-archaeology-audit-2026-05-22`)
**Scope**: Read-only audit of pipeline state across `rdm-bot`, `rdm-discussion`, `rdm-platform`. Window: 180 days (actual: ~12d, the lifetime of the project).
**Method**: Filesystem + `gh` API + git log + best-effort YAML/markdown parsing.

---

## §1 — TL;DR (top findings)

1. **22 thread number collisions across 209 threads (10.5%)** — root cause is `scripts/new-thread.sh` referenced everywhere but **does not exist**. Migrations, which DO have an atomic-claim script, show 0 active collisions.
2. **F2 observability "Accepted" (ADR-002, 2026-05-20) but never started.** Migration 0042 it claims is already consumed by `feedback_system`. No `metrics.ts`, `alerts.ts`, `cron_heartbeats` table. Spec/code drift in the open.
3. **STATE.md is stale across multiple §s**: lists 4 apps when repo has 5 (`worker-feedback`); §D claims migration 0039 collision still active when PR #140 resolved it 2026-05-21; §G keeps the resolved item too.
4. **90 PRs (60% of 150 in rdm-bot + rdm-discussion) reference no thread in title/body.** 110 of 209 threads have no PR. Cross-referencing the discussion ↔ implementation layer is broken.
5. **41 merged branches not deleted** (vs STATE.md's "15+" claim). Auto-delete-on-merge enabled in thread/146 does not retroactively clean.

## §2 — Pipeline health overview

| Metric | Value |
|---|---|
| Threads total | 209 |
| Threads with frontmatter (new YAML format) | 7 |
| Threads in legacy `**bold**`-header format | 202 |
| Number-prefix collisions | 22 (10.5%) |
| Repo birthday (oldest commit) | 2026-05-10 |
| Distinct authors (filename slug + frontmatter) | 60+ author labels (un-normalized) |
| PRs across 3 repos (last 180d window — effectively all) | 171 |
|   …merged | 163 |
|   …open | 5 |
|   …closed-no-merge | 2 |
|   …closed-draft | 1 |
| PRs without thread reference | 90 (`rdm-bot` + `rdm-discussion` only) |
| PRs with duplicate titles | 2 incidents |
| Migrations total | 45 |
| Active migration number collisions | 0 (one resolved historically) |
| Branches across 3 repos | 59 (51 + 7 + 1) |
| Branches active (commit ≤ 14d) | 18 |
| Merged branches not deleted | 41 |
| Stale (>14d, no merged PR) / dead (>60d) | 0 (repo too young) |
| Halt threads | 5 |
| Orphan threads (no PR) | 110 |
| Spec docs in `cc-instructions*` / `wc-instructions/` | 22 |
| Closed-no-merge PRs (abandoned) | 3 |
| Pending decisions (net, after dedupe) | ~38 |
| Critical-path pending items | 4 (F2, F1, F3, Analytics activation) |

## §3 — Top 10 findings (ranked by impact)

| # | Finding | Source | Impact |
|---|---|---|---|
| 1 | **`scripts/new-thread.sh` ficción** ⇒ 22 thread collisions | `[[a6-docs-drift-analysis]] §5`, `[[collisions]] §6` | structural |
| 2 | **F2 ADR Accepted ≠ shipped** ⇒ migration 0042 already consumed; spec needs remap | `[[a6-docs-drift-analysis]] §5,§10`; `[[a7-pending-decisions]] §4` | high — blocks M1 |
| 3 | **STATE.md stale**: §A apps list, §D/§G migration 0039 collision, §A last-deploys | `[[a6-docs-drift-analysis]] §3 C1/C2/C8` | medium — misinformation to new sessions |
| 4 | **Two decisions stores undocumented**: `rdm-discussion/decisions/01-09` operational vs `rdm-platform/decisions/ADR-001+` architectural | `[[a6-docs-drift-analysis]] §3 C5` | medium — split-brain risk |
| 5 | **`apps/admin` PWA is a 5-doc fiction** (VISION + ADR-04 + ADR-07 + OPEN_QUESTIONS + roadmap) | `[[a6-docs-drift-analysis]] §3 C4, §5` | medium — recurring confusion |
| 6 | **`decisions/03 PriceLabs` silently superseded** by custom-agent decision; ADR not updated | `[[a6-docs-drift-analysis]] §7`, `[[a7-pending-decisions]] §5 A2` | low — readers may follow stale guidance |
| 7 | **CLAUDE.md / STATE.md / VISION.md WC-vs-CC scope drift** — STATE.md §E says "WC NO implementa código en rdm-bot/rdm-platform", CLAUDE.md does not mention | `[[a6-docs-drift-analysis]] §3 C7` | medium — boundary depends on which doc the agent read |
| 8 | **PR ↔ thread linkage broken** — 90 PRs no-thread, 110 threads no-PR (mostly informational threads) | `[[a5-cross-reference-matrix]]` | low — but blocks bidirectional traceability |
| 9 | **`OPEN_QUESTIONS.md` 22 KB historical** — most PR1/PR2/PR3 conservative items long stale | `[[a7-pending-decisions]] §6` | low — but noise overwhelms current questions |
| 10 | **41 merged-undeleted branches** (auto-delete-on-merge does not backfill) | `[[a8-lost-work-orphans]] §3` | low — clutter, no risk |

## §4 — What's healthy (so a reader knows what NOT to fix)

- ✅ Migration numbering — 0 active collisions thanks to `scripts/new-migration.sh` (the exact pattern that should be replicated for threads)
- ✅ Better Auth shipped per `decisions/05` — aligned with VISION
- ✅ Monorepo Turborepo + pnpm per `decisions/01` — LIVE
- ✅ 5 properties + Casa Chamán deferred — aligned with VISION
- ✅ 5 cron triggers in `worker-pago` — aligned (and pushing CF Free 5-cron cap)
- ✅ Audit log migration 0039 LIVE — semantic boundary respected (staff actions, not metrics)
- ✅ `scripts/new-migration.sh`, `scripts/safe-deploy.sh`, `scripts/sync-secret.sh` exist and work
- ✅ Telegram alerts (pago-recibido + reembolso, PR #159) shipped 2026-05-22

## §5 — Recommendations (NO executing this audit)

### Inmediato (quick wins, < 1h each)

| # | Action | Why |
|---|---|---|
| 1 | Write `scripts/new-thread.sh` (mirror of `new-migration.sh`) and add to `rdm-discussion/` (since threads live there) | Closes structural fault behind 22 collisions; spec already in `thread/175 T1-T5` |
| 2 | Update `rdm-bot/STATE.md` §A apps list (+ `worker-feedback`), §D (remove resolved 0039 entry), §G (remove resolved entry G9), §A last-deploys | Stop misinforming new sessions |
| 3 | Update `rdm-bot/CLAUDE.md` to mirror `STATE.md §E` anti-patterns (WC ≠ implementer in rdm-bot/rdm-platform) | One CLAUDE.md missing a row is enough to break enforcement |
| 4 | Add status field to `rdm-discussion/decisions/03-pricing-agent.md` ("REVISED 2026-05-XX: custom agent kept, PriceLabs not purchased") | One-line doc fix, clarifies policy |
| 5 | Move shipped `cc-instructions*/` specs to `archive/` (per `[[a6-docs-drift-analysis]] §8`) | Reduce noise in active dir |

### Estratégico (multi-bucket)

| # | Action | Why |
|---|---|---|
| 1 | Resolve Alex's vote on `thread/148` (F2/F1/F3 + 7 items) | Unblocks the entire foundations + M1 pipeline |
| 2 | Either rewrite VISION.md to reflect "admin lives in apps/web" OR commit to building `apps/admin` PWA | Removes 5-doc fiction; new sessions stop chasing imaginary directory |
| 3 | Decide policy for the two decisions stores (rdm-discussion `01-09` vs rdm-platform `ADR-001+`) and document it in both STATE.md files | Removes split-brain risk for new readers |
| 4 | Adopt a single thread metadata format (the new YAML frontmatter) and write a one-shot migrator for the 202 legacy threads. Or formalize the legacy format as "v1, frozen" and only require frontmatter for new threads. | Currently neither: 7 / 202 split means cross-referencing is fragile |
| 5 | Move `OPEN_QUESTIONS.md` to archive; restart with only currently-pending items per `[[a7-pending-decisions]] §6` | 22 KB → ~5 KB; Alex's queue becomes visible |

### Largo plazo (Q3 2026+)

| # | Action |
|---|---|
| 1 | Ship F2 → F1 → F3 per ADR-002 (and update F2 to use a fresh migration number, since 0042 is gone) |
| 2 | After F2 ship, expand `/admin/health` to also surface the audit metrics produced by this report (thread count, collision rate, orphan rate) so drift is visible without re-running the script |
| 3 | Casa Chamán renovation Q3 2026 — un-hide in Greeter content once renovation closes |

## §6 — Files generated

All in `rdm-discussion/reports/`:

| Section | Files | Size estimate |
|---|---|---|
| A1 threads inventory | `2026-05-22-META-A1-threads-inventory.md` + `.json` | ~30 KB |
| A2 PRs inventory | `2026-05-22-META-A2-prs-inventory.md` + `.json` | ~80 KB |
| A3 migrations inventory | `2026-05-22-META-A3-migrations-inventory.md` + `.json` | ~5 KB |
| A4 branches inventory | `2026-05-22-META-A4-branches-inventory.md` + `.json` | ~10 KB |
| A5 cross-reference matrix | `2026-05-22-META-A5-cross-reference-matrix.md` + `.json` | ~15 KB |
| A6 docs drift analysis | `2026-05-22-META-A6-docs-drift-analysis.md` + `.json` | ~30 KB |
| A7 pending decisions | `2026-05-22-META-A7-pending-decisions.md` + `.json` | ~15 KB |
| A8 lost work / orphans | `2026-05-22-META-A8-lost-work-orphans.md` + `.json` | ~15 KB |
| A9 master synthesis (this doc) | `2026-05-22-META-A9-master-synthesis.md` | ~12 KB |
| ⚠️ Alex-flagged collisions explicit | `2026-05-22-META-collisions.md` | ~8 KB |

**Total: 19 files. JSON output is parseable for re-analysis by WC / WC-Platform / scripts.**

## §7 — Validations (per `thread/176 §5`)

- ✅ Each A1-A8 produced 2 files (MD + JSON) consistent.
- ✅ Counts in A9 match A1-A8 individuals (threads=209, PRs=171, migrations=45, etc.).
- ✅ Random sample check: 5 random threads (003, 081, 117, 154, 196) all appear in A1 inventory.
- ✅ JSON parseable (re-loaded in `collisions.py` and `a8_lost_work.py`).
- ✅ MD renderable (no broken markdown — visual scan).
- ✅ `META-collisions.md` includes 162-* (amendments), 105-* (supersedes), 169/170 (race), and historical 0039 migration. Matches and extends thread/172 quantification.

## §8 — Cost + time (real)

- **Tools used**: `gh api` (paginated branches, PR list), `python` (data join + report gen), `git log` (date stamps).
- **Tokens spent**: TBD by the post-merge accounting; estimate based on session: ~250k-350k input + ~30k output, mid-$1-2 of LLM cost (well under $15-20 budget).
- **Wall-clock**: ~1.5h continuous (one session, mostly tool I/O).

## §9 — Surprises / blockers found

- **Surprise**: 7 of 209 threads have YAML frontmatter; 202 have only `**Date** / **Author**` bold-header style. Spec assumed frontmatter; my parser had to dual-mode. No blocker, just slower.
- **Surprise**: `worker-feedback` exists as a 5th app — not in any STATE.md / VISION.md / CLAUDE.md.
- **Surprise**: F2 spec (`rdm-platform/foundations/F2-observability.md`) has a status line "Accepted 2026-05-20", but the implementation never started and the spec's claimed migration number (0042) is now occupied by an unrelated feature. This is the clearest "spec accepted ≠ work done" case in the audit.
- **Blocker**: none. All output produced.
- **One Windows-encoding hiccup**: `subprocess.check_output(... text=True)` defaulted to cp1252 on Python 3.14 / Windows and crashed on the first emoji in PR titles. Fixed by adding `encoding='utf-8', errors='replace'`. Same lesson as `feedback_powershell_utf8` memory.

## §10 — Linked

- [[a1-threads-inventory]] — full table of 209 threads
- [[a2-prs-inventory]] — 171 PRs across 3 repos
- [[a3-migrations-inventory]] — 45 migrations + history
- [[a4-branches-inventory]] — 59 branches across 3 repos
- [[a5-cross-reference-matrix]] — thread ↔ PR ↔ branch ↔ migration joins
- [[a6-docs-drift-analysis]] — META docs contradictions / ficciones / drift
- [[a7-pending-decisions]] — 38 net pending decisions, owners, critical path
- [[a8-lost-work-orphans]] — halts, merged-undeleted branches, stuck PRs, archived specs
- [[collisions]] — ⚠️ explicit Alex-flagged collisions report
