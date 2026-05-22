# A8 — Lost work / orphans identification

**Generated**: 2026-05-22 (CC, thread/176)
**Method**: read-only join of A1/A2/A4/A5 + scratch on filesystem.

Categories (per spec §A8):
1. Threads with halt status, no follow-up
2. Branches stale >60d / dead / orphan
3. PRs draft >7d
4. DoIt-completion threads with no merged PR
5. Spec docs in cc-instructions / wc-instructions
6. Open PRs >7d unmoved
7. Closed-no-merge PRs (abandoned)

## §1 — Halt threads (5)

| Thread | Filename | Status | Last commit |
|---|---|---|---|
| 98 | 98-cc-bot-pr82-halted-typecheck-errors.md |  | 2026-05-17 |
| 130 | 130-cc-bot-a5-halt-chrome-mcp-not-attached.md |  |  |
| 136 | 136-cc-bot-a5-halt-stale-mcp-process.md |  |  |
| 137 | 137-cc-bot-a5-halt-rincondelmar-session-missing.md |  |  |
| 162 | 162-cc-bot-admin-issues-cockpit-halt-preflight.md |  | 2026-05-21 |

**Recommendation**: each halt should either be (a) resolved with a follow-up thread referencing it, or (b) explicitly archived as 'abandoned'. None should remain in limbo.

## §2 — Stale + dead branches (0)

None.

## §3 — Merged branches not deleted (cleanup candidates, all ages) (41)

**Reframing note**: repo is young (≤11 days). Traditional 'stale >60d' / 'dead' categories do not yet apply. The realistic lost-work signal here is **branches whose PR merged but the branch was not deleted** — these accumulate clutter even when young. STATE.md §C says '15+ branches mergeadas sin podar'; actual count is higher.

| Repo | Branch | Age (d) | PRs |
|---|---|---|---|
| rdm-bot | `feat/d1-migrations-0014-0018-guest360` | 9 | #4 |
| rdm-bot | `feat/phase0-reviews-client-bot-a` | 9 | #1 |
| rdm-bot | `fix/web-las-morenas-roomid-cutover` | 9 | #3 |
| rdm-bot | `pr3-track-c-reviews-carousel` | 9 | #2 |
| rdm-bot | `feat/admin-airbnb-content-editor-fase15` | 8 | #10 |
| rdm-bot | `feat/admin-health-page` | 8 | #8 |
| rdm-bot | `feat/admin-placeholders-reviews-host` | 8 | #7 |
| rdm-bot | `feat/data-deterministic-ids` | 6 | #59 |
| rdm-bot | `feat/data-stage0-business-filter` | 6 | #48 |
| rdm-bot | `feat/data-stage-b-funnel-e-temporal` | 6 | #49 |
| rdm-bot | `feat/data-stage-c-operator-playbook` | 6 | #51 |
| rdm-bot | `feat/data-stage-deploy-d1-r2-vectorize` | 6 | #52 |
| rdm-bot | `feat/data-stage-deploy-dedup-emails-phones` | 6 | #58 |
| rdm-bot | `feat/data-stage-deploy-or-ignore-fix` | 6 | #57 |
| rdm-bot | `fix/data-r2-remove-remote-flag` | 6 | #60 |
| rdm-bot | `fix/welcome-status-filter` | 6 | #69 |
| rdm-discussion | `chore/notify-cc-claude-md` | 6 | #2 |
| rdm-discussion | `chore/working-modes-docs` | 6 | #1 |
| rdm-bot | `chore/trigger-pages-redeploy` | 5 | #75 |
| rdm-bot | `chore/vectorize-smoke-script` | 5 | #70 |
| rdm-bot | `docs/vectorize-handoff-and-deploy-runbook` | 5 | #71 |
| rdm-bot | `feat/admin-bookings-gantt` | 5 | #80 |
| rdm-bot | `feat/data-faq-and-content-extraction` | 5 | #81 |
| rdm-bot | `feat/data-stage-c-rerun-12k-and-trim` | 5 | #73 |
| rdm-bot | `feat/greeter-v6-combined` | 5 | #77 |
| rdm-bot | `fix/ci-lint-blockers` | 5 | #72 |
| rdm-bot | `fix/pages-build-prerender-admin-conv` | 5 | #74 |
| rdm-bot | `fix/pet-fee-web-content` | 5 | #78 |
| rdm-bot | `fix/v6-followups-bundled` | 5 | #79 |
| rdm-bot | `feat/admin-nav-phase-2-4` | 2 | #131 |
| rdm-bot | `feat/beds24-proxy-calendar` | 2 | #127 |
| rdm-bot | `feat/role-based-nav-visibility` | 2 | #129 |
| rdm-bot | `feat/thread-141-house-rules-paper-trail` | 2 | #128 |
| rdm-bot | `fix/admin-readonly-test-priority` | 2 | #134 |
| rdm-bot | `fix/reglas-pdf-emoji-sanitize` | 2 | #133,#132 |
| rdm-discussion | `claude/respond-thread-145-Qcon1` | 2 | #4 |
| rdm-bot | `docs/karina-training-v2` | 1 | #135 |
| rdm-bot | `feat/karina-tg-distribution` | 1 | #136 |
| rdm-discussion | `chore/process-improvements-thread-146` | 1 | #8,#6 |
| rdm-discussion | `chore/state-system-and-audit` | 1 | #3 |
| rdm-bot | `feat/mp-webhook-beds24-capture` | 0 | #158 |

**Cause**: auto-delete-on-merge was enabled in thread/146 but does not retroactively delete pre-existing branches. Run `git branch -r --merged main | grep -v main` and delete in batch when appropriate (NOT executing — operator decision).

## §4 — Orphan branches (no PR ever, not active) (0)

None.

## §5 — Stuck open PRs (>7d, not draft) (0)

None.

## §6 — Draft PRs >7d (0)

None.

## §7 — Completion-flagged orphan threads (DoIt/completion topic, no PR) (19)

| # | Filename | Mode | Status |
|---|---|---|---|
| 8 | 08-cc-bug-fix-and-day4-done.md |  |  |
| 9 | 09-cc-sprint1-day5-done.md |  |  |
| 56 | 56-wc-data-v2-prep-complete-and-critical-findings.md |  |  |
| 77 | 77-cc-data-prod-deploy-95-pct-done-vectorize-handoff.md |  |  |
| 93 | 93-cc-bot-status-bookings-build-complete-inbox-paused.md |  |  |
| 93 | 93-wc-ack-cc-feedback-doit-template-v2.md |  |  |
| 94 | 94-wc-ack-clone-paths-doit-template-v3.md |  |  |
| 104 | 104-cc-bot-beds24-backfill-complete.md |  |  |
| 127 | 127-wc-cc-a5-execution-doit.md |  |  |
| 128 | 128-wc-cc-open-items-omnibus-doit.md |  |  |
| 129 | 129-cc-bot-omnibus-doit-report.md |  |  |
| 133 | 133-cc-bot-mobile-inbox-rescue-complete.md |  |  |
| 135 | 135-cc-wc-beds24-proxy-readonly-complete.md |  |  |
| 140 | 140-cc-wc-a6-reglas-adicionales-complete.md |  |  |
| 142 | 142-cc-wc-house-rules-paper-trail-phase1-done.md |  |  |
| 153 | 153-wc-cc-numbering-and-0039-doit.md |  |  |
| 160 | 160-wc-cc-numbering-and-branch-protection-doit.md |  |  |
| 175 | 175-wc-cc-doit-p1-p2-quickwins-strategic.md | DoIt | ready-for-cc-execution |
| 176 | 176-wc-cc-doit-meta-archaeology-pipeline-audit.md |  |  |

## §8 — Spec docs in `cc-instructions*` / `wc-instructions/` (32)

Each is an older DoIt-era spec (before threads stabilized). Many already shipped per [[a6-docs-drift-analysis]] §8 but still in the active directory.

| Directory | File | Size |
|---|---|---|
| cc-instructions | 2026-05-12-greeter-v5-challenge-CONSOLIDATED.md | 12129 |
| cc-instructions | 2026-05-12-review-guest360-phaseb-plan.md | 9419 |
| cc-instructions | 2026-05-13-execute-batch-b-fase-1-5-mvp.md | 4752 |
| cc-instructions | 2026-05-13-review-content-architecture-proposal.md | 11237 |
| cc-instructions | 2026-05-13-review-thread40-content-editor.md | 4367 |
| cc-instructions | 2026-05-14-import-wc-seed-drafts-and-karina-onboarding.md | 11784 |
| cc-instructions | 2026-05-17-platform-wishlist-feedback.md | 5697 |
| cc-instructions-bot | 2026-05-15-greeter-v5-prompt-part1-pra4.md | 19210 |
| cc-instructions-bot | 2026-05-15-greeter-v5-prompt-part2-pra6.md | 26279 |
| cc-instructions-bot | 2026-05-15-greeter-v5-prompt-part3-pra7.md | 16132 |
| cc-instructions-bot | 2026-05-16-admin-bookings-and-inbox-DELTA.md | 21212 |
| cc-instructions-bot | 2026-05-16-admin-bookings-gantt-build-spec.md | 15152 |
| cc-instructions-bot | 2026-05-16-admin-inbox-unified-build-spec.md | 19750 |
| cc-instructions-bot | 2026-05-16-pr-a61-prompt-v6-design.md | 4878 |
| cc-instructions-bot | 2026-05-16-pr-a61-v6-combined.md | 12540 |
| cc-instructions-bot | 2026-05-16-system-prompt-v6-wc.md | 22402 |
| cc-instructions-bot | 2026-05-16-v6-diff-and-deploy-wc.md | 5278 |
| cc-instructions-bot | 2026-05-16-v6-dry-runs-wc.md | 6654 |
| cc-instructions-bot | 2026-05-18-karina-training-deploy-and-screenshots.md | 11212 |
| cc-instructions-bot | 2026-05-18-pre-stay-notifications-mvp.md | 32330 |
| cc-instructions-bot | 2026-05-21-admin-issues-cockpit.md | 30543 |
| cc-instructions-bot | 2026-05-21-i0-welcome-autosend-rebuild.md | 16299 |
| cc-instructions-bot | 2026-05-21-i15-critical-keyword-alert.md | 20891 |
| cc-instructions-bot | 2026-05-21-i21-kill-nav-placeholders.md | 11047 |
| cc-instructions-bot | 2026-05-21-i27-pending-welcomes-badge.md | 12427 |
| cc-instructions-bot | 2026-05-22-booking-detail-quick-dirty.md | 50824 |
| cc-instructions-bot | README.md | 2105 |
| cc-instructions-data | 2026-05-15-data-mining-v2-execute.md | 43837 |
| cc-instructions-data | 2026-05-16-faq-and-content-enrichment-extraction.md | 11131 |
| cc-instructions-data | 2026-05-16-vectorize-handoff.md | 12023 |
| wc-instructions | 2026-05-13-review-cc-thread37-38.md | 7645 |
| wc-instructions | 2026-05-19-deploy-and-build-checklist.md | 14559 |

**Recommendation**: move shipped specs to `archive/cc-instructions/` so the active set is small. No execution from this audit.

## §9 — Closed-no-merge PRs (abandoned, last 180d) (3)

| Repo | PR | Title | Closed |
|---|---|---|---|
| rdm-bot | #76 | docs(v6-prompt): WC review request — Option B recommended | 2026-05-16 |
| rdm-bot | #65 | DRAFT: PR A6.1 prep — Greeter v6 prompt with operator_playbo | 2026-05-16 |
| rdm-bot | #45 | test(greeter-v5): PR A7.8 — anti-loop tests + biome safe-fix | 2026-05-15 |

## §10 — Top recovery candidates (subjective ranking)

From the above, the items most worth resurrecting or formally closing:

1. **A5 Airbnb bulk-approve 67% work** — branch `feat/a5-airbnb-bulk-approve-writeback`, halt threads 130/136/137/138 (untracked locally per STATE.md §C). Either resume or formally archive; do not leave 30% structural skips in limbo.
2. **PR #114 journey templates editor** — open since 2026-05-18, stuck. Either review/merge or close-with-reason.
3. **PR #130 A6 reglas adicionales** — open since 2026-05-19, stuck. Same as above.
4. **`scripts/new-thread.sh` missing** — recurring root cause of 22 thread collisions. Trivial to write (single shell script with `git pull` + atomic next-number + push of stub).
5. **F2/F1/F3 specs accepted but never started** — the longer specs sit, the more the surrounding code drifts; spec needs migration number remap (0042 already consumed).
6. **Old `cc-instructions/2026-05-12 ... 2026-05-17` specs** — most shipped; archive to keep active dir lean.
7. **`OPEN_QUESTIONS.md` 22 KB historical** — archive PR1/2/3 era; start fresh.

