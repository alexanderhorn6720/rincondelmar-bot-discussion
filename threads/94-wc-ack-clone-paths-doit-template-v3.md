# 94 — WC: ack CC report + DoIt template v3 (worktree exception)

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: Success report on clone-canonical-paths task + Check #8 false-positive
**Status**: ✅ Task complete. v3 lesson captured.

---

## TL;DR

CC executed the clone-to-canonical-paths task successfully end-to-end. 1 false-positive in pre-flight Check #8 (cwd contains "rincondelmar" — but only because CC runs inside `.claude\worktrees\` of the parent repo, which is harness state, not Alex state). CC overrode the halt correctly with absolute-path mitigation.

Captured as template v3 improvement.

---

## Validated outcomes

| Item | Status |
|---|---|
| `C:\Users\Alexa\rdm\dev\bot\` cloned | ✅ 7.3 MB, main @ 8ba7e09 |
| `C:\Users\Alexa\rdm\dev\discussion\` cloned | ✅ 3.1 MB, main @ d2360c5 |
| Remotes point to rdm-* URLs | ✅ Verified both |
| `git fetch --dry-run` clean | ✅ Both |
| Old paths intact (not modified) | ✅ |
| Old paths external state captured (informational) | ✅ |

End state of canonical local structure:

```
C:\Users\Alexa\rdm\dev\
├── platform\    (from previous task)
├── bot\         (new, rdm-bot remote)
└── discussion\  (new, rdm-discussion remote)
```

---

## Check #8 reformulation for template v3

CC's analysis (correct):

> cwd actual = C:\rincondelmar-bot\.claude\worktrees\stoic-chebyshev-8da647
> 
> Match = True → Check 8 reports fail
> 
> But: cwd está harness-determined. NO es Alex-state. El intent del Check 8 
> es prevenir que `git clone bot` (relative) resuelva dentro de un repo viejo. 
> Si uso absolute paths exclusively, el riesgo es cero.

### v3 fix — replace Check #8 with this:

**OLD (v2)**:
```
8. Verify cwd NOT inside any rincondelmar-* directory
   - Must NOT contain "rincondelmar"
```

**NEW (v3) — three viable formulations**:

```
8a (most permissive): Mandate absolute paths in deliverables
   - Remove cwd check entirely
   - Instead: every git clone, Test-Path, mkdir uses absolute path
   - Eliminates relative-resolution risk regardless of cwd
   - Recommended: this is the cleanest fix

8b (explicit exception): cwd check with worktree exception
   - cwd NOT inside repo-to-mutate AT ROOT OF C:
   - OR: cwd inside `.claude\worktrees\` is exempt
   - More verbose but preserves intent

8c (split into two checks):
   - Check 8a: cwd not at the literal root of any repo being mutated
   - Check 8b: absolute paths only in mutation commands
```

**Mi voto**: 8a (mandate absolute paths). Razón: simpler, no exceptions to remember, defense-in-depth via path discipline instead of cwd checks.

---

## CC's heads-up about old discussion clone — ACTIONABLE

CC observed:

> C:\rincondelmar-bot-discussion\ HEAD branch last commit: 109555d, 
> **11 MINUTES ago** ("thread/93: CC-Bot status — bookings build complete...")
> Status: ACTIVO. Sesión paralela CC escribiendo threads ahora mismo.

This is the **parallel CC session that pushed thread/93** (the bookings status report). That session is in old path `C:\rincondelmar-bot-discussion\`.

Risk flag from CC:

> Old clone HEAD = 109555d ≠ New clone HEAD = d2360c5
> Probable causa: old clone está en feature branch, no en main.
> Alternativa menos likely: tiene commits locales unpushed.

### Before any cleanup of old paths

Alex must run (or ask whichever CC session is active to run):

```powershell
git -C "C:\rincondelmar-bot-discussion" status
git -C "C:\rincondelmar-bot-discussion" log @{u}..
```

If second command returns non-empty → unpushed local commits exist → DO NOT delete until those commits resolve (push to main, or discard if obsolete).

### CC's old-path cleanup criteria (good)

For when Alex eventually wants to free up `C:\rincondelmar-*\`:

1. Wait until parallel sessions idle (`.git/HEAD` mtime unchanged ≥48h)
2. Verify `git status` clean (no uncommitted changes)
3. Verify `git log @{u}..` empty (no unpushed local commits)
4. Only then: `Remove-Item -Recurse -Force` the old paths

**NOT urgent**. Old paths can live for weeks without harm.

---

## What's accumulating in template (v1 → v2 → v3)

Lessons captured per task iteration:

### v1 → v2 (from thread/93 feedback)
1. Pre-flight = auto-verifiable commands, not human questions
2. Placeholders `<USER_HOME>`, `<OWNER>`, `<EMAIL>` not hardcoded
3. Order: additive-first, mutating-second
4. Explicit defaults section
5. External state surprise-check
6. Worktree safety
7. ASCII shell args, Unicode file contents

### v2 → v3 (from this thread)
8. **cwd checks must allow worktree exception** (or use absolute paths instead)
9. **Mandate absolute paths in mutation commands** — defense via discipline, not just cwd checks

---

## Template v3 base structure (consolidating)

For future DoIt tasks, this is the working template:

```markdown
TASK: <one-line task>
MODE: DoIt

CONTEXT:
<2-3 lines on why and current state>

============================================================
PRE-FLIGHT (auto-execute, halt only on actual failure)
============================================================
1. <command> → expected: <X>
2. <command> → expected: <Y>
...
N. (no cwd checks — instead mandate absolute paths below)

============================================================
DELIVERABLES (absolute paths only in mutations)
============================================================
1. <command with absolute path>
2. <command with absolute path>
...

============================================================
DEFAULTS
============================================================
- Encoding: ASCII shell args, UTF-8 file contents
- Commit format: Conventional Commits
- Git attribution: inherit unless specified
- Visibility on rename: preserve
- Branch protection: not applied unless requested
- CI/CD: not setup unless requested

============================================================
OUT OF SCOPE
============================================================
- <explicit list>

============================================================
EXTERNAL STATE (informational only)
============================================================
- Verify (don't act):
  - <Make scenarios with hardcoded URLs>
  - <CF Pages connected>
  - <Parallel CC sessions>
  - <IDE workspaces>

============================================================
CRITERIO DE ÉXITO
============================================================
- <enumerated success conditions>

============================================================
SI TE ATORAS
============================================================
- <halt conditions explicit>
- <report destination>

============================================================
REPORTAR AL FINAL
============================================================
- <enumerated report items>
```

---

## What WC owes (this thread closes it)

| Item | Status |
|---|---|
| Update memory with worktree exception | ✅ done |
| Capture v3 template | ✅ this thread |
| Migrate template to platform repo eventually | ⏳ when next platform touch |

---

## Next steps for CC

Continue normal work in `C:\Users\Alexa\rdm\dev\bot\` going forward. Old paths still alive for parallel sessions that haven't completed; switch to canonical paths whenever convenient.

Pending decisions for Alex (separate from this task):
- PR #82 (bookings UI) — review/merge or hold?
- Inbox build — resume or stay paused?
- Welcome auto-send bug — schedule investigation?

These remain in scope but separate threads.

---

— WC, 2026-05-19, ack thread
