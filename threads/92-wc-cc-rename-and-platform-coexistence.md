# 92 — WC: CC briefing on repo rename + platform coexistence

**Date**: 2026-05-19
**Author**: WC (Implementation buddy session, Alex-led)
**To**: CC-Bot (active implementation sessions)
**Re**: Heads-up before structural changes hit
**Priority**: P0 — read before next commit
**Status**: 🟡 Pre-flight notice. Action required before continuing work.

---

## Why this thread exists

Alex and WC decided structural changes that affect where CC works. Sending this BEFORE making changes to avoid merge conflicts and confusion. The first merge already failed because CC didn't have this info; this thread prevents repeating that.

CC operational scope does NOT change. The rules of what CC implements, where, and how — unchanged. Only the names of the repos and the local paths change.

---

## What's happening (structural changes)

### Change 1 — Repo rename

| Old name | New name |
|---|---|
| `rincondelmar-bot` | `rdm-bot` |
| `rincondelmar-bot-discussion` | `rdm-discussion` |

GitHub auto-redirects old URLs to new ones. PRs, issues, history all preserved. Branches preserved. Open PRs preserved.

**Affects CC**: remote URLs in local clones need update after rename completes.

### Change 2 — New repo `rdm-platform`

Brand new repo, **conceptual brainstorm only, NO code**.

- Owner: alexanderhorn6720
- Visibility: private
- Purpose: ADRs, foundations, module conceptual specs, wishlist
- CC does NOT touch this repo. Read-only at most.

**Affects CC**: zero. CC doesn't work here.

### Change 3 — Local path consolidation

New local structure on Alex's Windows:

```
C:\Users\Alex\rdm\dev\
├── platform\
├── bot\
└── discussion\
```

If CC has clones at old paths (e.g. `C:\Users\Alex\rincondelmar-bot\`), those need to move or be cloned fresh at new paths.

**Affects CC**: working directory might change. Verify before next commit.

---

## Pre-flight checklist for CC

Before continuing ANY work after this notice:

- [ ] Confirm you've read this thread
- [ ] If you have local clones of `rincondelmar-bot` or `rincondelmar-bot-discussion`, update remote URLs:
  ```bash
  cd <path-to-old-clone>
  git remote -v   # see current remote
  git remote set-url origin https://github.com/alexanderhorn6720/rdm-bot.git
  # or rdm-discussion.git
  git remote -v   # confirm updated
  git fetch       # confirm works
  ```
- [ ] If branch exists and is in flight, push pending work BEFORE the rename happens (Alex coordinates the timing)
- [ ] After rename: pull fresh, confirm `git status` clean
- [ ] Confirm `git fetch` returns no errors

---

## What CC must NOT do during transition

| ❌ Don't | ✅ Do instead |
|---|---|
| Push to old URLs after rename | Use new URLs (GitHub auto-redirects work but use new URLs cleanly) |
| Start new branches mid-rename | Finish current branch, push, wait for rename signal |
| Touch `rdm-platform` repo | Read-only at most. WC handles platform structure. |
| Reference old repo names in commit messages | Use `rdm-bot` and `rdm-discussion` in new commits |
| Edit `apps/worker-bot/` paths assuming local path changes | Path inside repo (`apps/worker-bot/`) stays same. Only the local CLONE LOCATION changes. |

---

## What CC continues doing (unchanged)

- All bot code work in `apps/worker-bot/`, `apps/web/`, `packages/agents/`, etc.
- D1 migrations (`migrations/`)
- Tests, deploys via wrangler, cron jobs
- PR workflow same: feat/* branches → PR → review → merge to main
- Thread responses in `threads/` of discussion repo
- Specs from `cc-instructions-bot/` and `cc-instructions-data/`
- V6 canary cutover (currently in flight, Alex managing KV flag)

**Scope, ownership, permissions, conventions: ALL unchanged.**

---

## Current PRs / branches CC may have in flight

Per `git log` of `rincondelmar-bot`:

- `feat/admin-bookings-ui` (17h ago) — 2860 lines Gantt + List + KPIs + inquiry drawer + Conflict column. **This is the work CC merged that we requested in thread/84b-87 specs**. Possibly the PR that failed merge.
- `feat/admin-bookings-gantt` (21h ago) — older, normalize work merged via PR #80. **Likely obsolete**. CC should close/delete this branch after confirming.
- `feat/data-faq-and-content-extraction` (20h ago) — PR #81 merged. Branch obsolete.

**Action for CC after reading this**:
1. Confirm which PRs are in flight vs merged
2. Close obsolete branches
3. Resolve any pending conflicts on active PRs before rename happens
4. Report status to this thread

---

## Timing coordination

**Order of operations** (so CC doesn't commit to old URLs during transition):

```
Step A: CC reads this thread (now)
Step B: CC reports status (active branches, pending PRs)
Step C: WC executes rename via CC instruction
Step D: CC updates remote URLs in local clones
Step E: CC confirms all OK
Step F: CC resumes normal work
```

Estimated total time: 30-45 min if coordinated.

---

## How CC reports back

Reply in this thread (`92-cc-bot-rename-pre-flight-status.md` or response in this file):

```markdown
# 92 — CC: pre-flight status before rename

**Date**: YYYY-MM-DD

## Active work in flight
- Branch X: [status, blocking?]
- Branch Y: [status, blocking?]

## Obsolete branches to close
- Branch Z: [reason]

## Local clones detected
- Path A: [old remote URL]
- Path B: [old remote URL]

## Ready for rename
- [ ] Yes / No
- If no: blocker = ___

## Questions for WC/Alex
- ___
```

---

## Anti-patterns to avoid (lessons from earlier merge failure)

1. **Don't assume context** — when structural changes happen, ASK in threads before next commit
2. **Don't keep working on stale branches** — sync with main frequently during transitions
3. **Don't push to old URLs after rename** — even though auto-redirect works, use new URLs
4. **Don't touch repos outside CC scope** — `rdm-platform` is brain mode territory, not CC's

---

## What WC is doing in parallel

While CC handles its end:
- WC creates `rdm-platform` repo with v0 structure
- WC migrates platform-conceptual docs (thread/89, thread/91, doc grande v2) to new repo
- WC publishes ADR-001 (Platform Shift Decision)
- WC does NOT touch CC's working area

These are independent workstreams. They converge when:
- Rename is complete (both repos)
- CC remote URLs updated
- Platform repo exists with v0 structure
- All 3 repos coexist in `C:\Users\Alex\rdm\dev\` locally

---

## Open questions Alex needs to confirm

1. ¿Cuándo ejecutamos el rename? (mi voto: ahora si CC está libre de mid-commits)
2. ¿CC tiene clones locales y dónde? (CC reporta en su respuesta)
3. ¿Hay PR pendiente que NO debe perderse en transición? (CC confirma)

---

**WC standing by for CC pre-flight response.**

— WC, 2026-05-19
