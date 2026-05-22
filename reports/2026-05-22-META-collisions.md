# ⚠️ META — Collisions detected

**Generated**: 2026-05-22 (CC, thread/176)
**Alex flag (thread/176)**: "Hay PRs y threads multiplicados con la misma numeración."

## §1 — Thread number collisions (22 numbers affected)

209 threads total. 22 numbers have 2+ files. Confirms Alex flag.

| Number | Files | Notes |
|---|---|---|
| 11 | 11-cc-wc-thread10-implemented.md, 11-wc-beds24-migration-task-for-cc.md | RACE — distinct topics (unresolved) |
| 43 | 43-cc-fase2-merge-guide.md, 43-wc-alex-go-execute-batch-b.md | RACE — distinct topics (unresolved) |
| 44 | 44-cc-pr12-final-state.md, 44-wc-footer-policy-research-morenas-concern.md | RACE — distinct topics (unresolved) |
| 45 | 45-cc-wc-seed-drafts-discovery.md, 45-mvp-live-and-content-drafts-ready.md | RACE — distinct topics (unresolved) |
| 54 | 54-cc-fase-1-progress.md, 54-wc-data-mining-v2-strategy.md | RACE — distinct topics (unresolved) |
| 77 | 77-cc-bot-prs-a761-a763-merged.md, 77-cc-data-prod-deploy-95-pct-done-vectorize-handoff.md | RACE — distinct topics (unresolved) |
| 93 | 93-cc-bot-status-bookings-build-complete-inbox-paused.md, 93-wc-ack-cc-feedback-doit-template-v2.md | RACE — distinct topics (unresolved) |
| 98 | 98-cc-bot-pr82-halted-typecheck-errors.md, 98-wc-cc-autonomy-config-and-workspace.md | RACE — distinct topics (unresolved) |
| 105 | 105-wc-doit-admin-inbox-p3-plus-2bugs.md, 105-wc-doit-admin-inbox-p3.md | ACCEPTABLE — superseded by suffix version |
| 145 | 145-wc-cc-state-tweaks-and-promote-doit.md, 145-wc-platform-foundations-spec-and-adr-002.md | RACE — distinct topics (unresolved) |
| 146 | 146-cc-foundations-preflight.md, 146-wc-cc-process-improvements-AMENDMENT.md, 146-wc-cc-process-improvements-doit.md | ACCEPTABLE — same topic, amendments to same DoIt |
| 149 | 149-followup-day-0-trigger.md, 149-wc-impl-analytics-audit.md, 149-wc-platform-audit-kickoff.md | 3-way collision |
| 151 | 151-wc-impl-karina-training-v2-spec.md, 151-wc-platform-architectural-audit.md | RACE — distinct topics (unresolved) |
| 152 | 152-followup-additional-findings.md, 152-wc-impl-operational-audit.md | RACE — distinct topics (unresolved) |
| 153 | 153-cc-bot-audit-2026-Q2-technical-findings.md, 153-wc-cc-numbering-and-0039-doit.md | RACE — distinct topics (unresolved) |
| 157 | 157-wc-impl-p0-welcome-autosend-broken.md, 157-wc-platform-admin-audit-review.md | RACE — distinct topics (unresolved) |
| 158 | 158-wc-cc-ir-shortlink-resolver-overhaul-doit.md, 158-wc-cc-ir-system-overhaul-spec.md, 158-wc-cc-tech-validation-trigger.md | 3-way collision |
| 159 | 159-cc-wave-1-complete.md, 159-wc-impl-synthesis-bigbang-sealed.md | RACE — distinct topics (unresolved) |
| 160 | 160-karina-ping-prompt-pre-wave-1.md, 160-wc-cc-numbering-and-branch-protection-doit.md | RACE — distinct topics (unresolved) |
| 162 | 162-cc-bot-admin-issues-cockpit-halt-preflight.md, 162-wc-cc-state-repair-AMENDMENT-2.md, 162-wc-cc-state-repair-AMENDMENT.md, 162-wc-cc-state-repair-doit.md | ACCEPTABLE — same topic, amendments to same DoIt |
| 169 | 169-cc-bot-telegram-pago-recibido-spec.md, 169-wc-cc-harness-oss-survey.md | RACE — distinct topics (unresolved) |
| 170 | 170-cc-bot-telegram-pago-notify-pr159.md, 170-wc-bot-factuality-conceptual.md | RACE — distinct topics (unresolved) |

### Distinct cases

- **Acceptable amendments** (e.g. 162-amendment, 162-amendment-2 — same topic): expected pattern.
- **Acceptable supersede** (e.g. 105-...-p3 vs 105-...-p3-plus-2bugs): old version still in tree, new prefix marks supersede. STATE.md §F officially blesses this pattern.
- **Race collisions** (distinct topics, same number): structural failure mode. Could not occur if `scripts/new-thread.sh` atomic-claim had been implemented (it's a fiction per [[a6-docs-drift-analysis]] §5).

## §2 — PR collisions

GitHub enforces unique PR numbers per repo; no in-repo collision possible. Across repos, identical numbers exist trivially (rdm-bot #1, rdm-discussion #1, rdm-platform #1). Cross-repo numbering is not a collision but a naming-without-prefix problem.

**Recommendation**: when referring to PRs in threads, always prefix with repo (`rdm-bot#159`, `rdm-discussion#11`). Thread bodies analyzed in A2 use bare `#N` — ambiguous when CC is reading across repos. Audit found no in-repo duplicate-number incidents.

### Duplicate PR titles detected (2)

| Repo | Title | PR numbers |
|---|---|---|
| rdm-bot | fix(reglas-pdf): sanitize variation selectors + emoji ranges | [133, 132] |
| rdm-bot | test(greeter-v5): pr a7.8 — anti-loop tests + biome safe-fix | [46, 45] |

## §3 — Migration number collisions

**Active (workspace) collisions**: 0

None in current workspace. ✅

### Historical (resolved) collisions

| Number | Files | Resolution |
|---|---|---|
| 0039 | 0039_audit_log.sql, 0039_rules_link_clicks.sql | ✅ Resolved via PR #140 (`dade0d3`, 2026-05-21) — renamed `rules_link_clicks` to 0040 |

### Git log notes mentioning rename / renumber (4)

| File | Subject |
|---|---|
| 0015_leads.sql | 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004) |
| 0016_bookings.sql | 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004) |
| 0017_guest_events.sql | 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004) |
| 0040_rules_link_clicks.sql | dade0d3 chore(audit-wave-1): T2 renumber duplicate migration 0039_rules_link_clicks (#140) |

## §4 — Branch name collisions / near-duplicates

### Cross-repo identical branch names

| Branch | Repos |
|---|---|
| `main` | rdm-bot, rdm-discussion, rdm-platform |

### Near-duplicate branch names (same repo)

| Repo | A | B |
|---|---|---|
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-b-funnel-e-temporal` |
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-c-operator-playbook` |
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-c-rerun-12k-and-trim` |
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-deploy-d1-r2-vectorize` |
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-deploy-dedup-emails-phones` |
| rdm-bot | `feat/data-stage0-business-filter` | `feat/data-stage-deploy-or-ignore-fix` |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | `feat/data-stage-c-operator-playbook` |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | `feat/data-stage-c-rerun-12k-and-trim` |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | `feat/data-stage-deploy-d1-r2-vectorize` |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | `feat/data-stage-deploy-dedup-emails-phones` |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | `feat/data-stage-deploy-or-ignore-fix` |
| rdm-bot | `feat/data-stage-c-operator-playbook` | `feat/data-stage-c-rerun-12k-and-trim` |
| rdm-bot | `feat/data-stage-c-operator-playbook` | `feat/data-stage-deploy-d1-r2-vectorize` |
| rdm-bot | `feat/data-stage-c-operator-playbook` | `feat/data-stage-deploy-dedup-emails-phones` |
| rdm-bot | `feat/data-stage-c-operator-playbook` | `feat/data-stage-deploy-or-ignore-fix` |
| rdm-bot | `feat/data-stage-c-rerun-12k-and-trim` | `feat/data-stage-deploy-d1-r2-vectorize` |
| rdm-bot | `feat/data-stage-c-rerun-12k-and-trim` | `feat/data-stage-deploy-dedup-emails-phones` |
| rdm-bot | `feat/data-stage-c-rerun-12k-and-trim` | `feat/data-stage-deploy-or-ignore-fix` |
| rdm-bot | `feat/data-stage-deploy-d1-r2-vectorize` | `feat/data-stage-deploy-dedup-emails-phones` |
| rdm-bot | `feat/data-stage-deploy-d1-r2-vectorize` | `feat/data-stage-deploy-or-ignore-fix` |
| rdm-bot | `feat/data-stage-deploy-dedup-emails-phones` | `feat/data-stage-deploy-or-ignore-fix` |

## §5 — Anti-pattern check: `feat/thread-N` branches

`rdm-bot/CLAUDE.md` Convenciones table: 'Branches: feat/<topic>, fix/<topic>, chore/<topic>. Nada de `feat/thread-N`.'

| Repo | Branch (violation) |
|---|---|
| rdm-bot | `feat/thread-141-house-rules-paper-trail` |
| rdm-discussion | `chore/process-improvements-thread-146` |
| rdm-discussion | `claude/respond-thread-145-Qcon1` |
| rdm-discussion | `thread/158-final-report` |

## §6 — Root cause analysis

All 22 thread number collisions trace to **one structural fault**: `scripts/new-thread.sh` (referenced in `rdm-bot/CLAUDE.md:65,70,119,127` + `rdm-bot/.claude/settings.json:77`) does not exist in any of the three repos.

Without atomic claim, two parallel sessions (WC or CC) computing 'next thread number' both pick the same `N+1`, write distinct files, and push. Result: 22 number collisions across 209 threads (10.5%).

**Fix scope (not executing — informational)**: 30-line shell script that `git pull`s, computes max N, writes a stub `threads/N+1-<author>-<topic>.md`, pushes immediately, and prints the number. Same pattern as `scripts/new-migration.sh` which DOES exist. The fact that migration collisions resolved cleanly (0039 → 0040 via PR #140) while thread collisions accumulated is direct evidence the atomic-claim pattern works when implemented.

**This audit does not fix the script** — it's [[a7-pending-decisions]] §10 item #4 and out of scope per `rdm-discussion/threads/176-...md §9` (deferred to thread/175 T1-T5).

