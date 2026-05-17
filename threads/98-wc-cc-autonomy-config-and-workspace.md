# 98 — WC: CC autonomy config + workspace setup (lunes onboarding)

**Date**: 2026-05-19
**Author**: WC
**To**: Alex (read in browser when ready) + CC (gets local instruction)
**Re**: CC auto-approve config + VS Code workspace + bot repo special case
**Status**: 🟢 2 of 3 settings pushed. Bot needs local creation (gitignored). Workspace file is local-only.

---

## TL;DR

WC pushed `.claude/settings.json` to 2 of 3 repos:

| Repo | Status |
|---|---|
| `rdm-discussion` | ✅ Pushed (e8a0f70) |
| `rdm-platform` | ✅ Pushed (37111da) |
| `rdm-bot` | ⚠️ Cannot push — `.claude/` in `.gitignore` (by design). CC creates locally. |

Local-only files (CC creates from templates):
- `<USER_HOME>\rdm\rdm-workspace.code-workspace` (multi-root workspace)
- `<USER_HOME>\rdm\dev\bot\.claude\settings.json` (bot CC config)

This thread captures both templates + DoIt task for CC to apply.

---

## §1 — Why the 3-tier permission model

Brain mode session decision: maximize CC autonomy WITHOUT compromising safety.

| Category | Behavior | Examples |
|---|---|---|
| **allow** | Auto-execute, no prompt | tests, lint, build, git read, gh read, wrangler read-only |
| **ask** | Y/N once per session | deploy, push, merge, kv put, d1 migrations apply |
| **deny** | NEVER execute, even if asked | force push, rm -rf, db delete, repo delete |

Rationale: 90% of CC work is in `allow` (no friction). The 10% in `ask` are high-impact decisions where Alex's 1-click Y/N protects against bad pushes. `deny` is hard line — even if CC has reason, these are catastrophic.

---

## §2 — Bot repo special case (gitignore decision)

`rdm-bot/.gitignore` line 65: `.claude/` — entire directory ignored.

**Why this is correct** (don't override):
- Per-developer config (different machines, different preferences)
- May contain session state, caches
- Different CCs/sessions may need different rules
- Anthropic convention: `.claude/settings.json` is local, `.claude/settings.local.json` super-local

**WC voto firme**: respect gitignore. Bot settings created locally per machine, NOT committed.

**Tradeoff**: settings don't sync across CC sessions or devices.
**Mitigation**: template lives in `rdm-discussion/templates/` for reproducibility. Anytime CC starts fresh on new machine, runs DoIt task in §4 below.

---

## §3 — Workspace multi-root file

Local-only (in `<USER_HOME>\rdm\rdm-workspace.code-workspace`):

```json
{
  "folders": [
    { "path": "dev/bot", "name": "🔧 bot" },
    { "path": "dev/discussion", "name": "💬 discussion" },
    { "path": "dev/platform", "name": "📐 platform (read-only)" }
  ],
  "settings": {
    "claude.autoSaveBeforeEdit": true,
    "claude.confirmDestructiveOps": true,
    "git.confirmSync": false,
    "git.autofetch": true,
    "terminal.integrated.cwd": "${workspaceFolder:🔧 bot}",
    "files.exclude": {
      "**/.claude/sessions/**": true,
      "**/node_modules": true,
      "**/.next": true,
      "**/dist": true
    }
  },
  "extensions": {
    "recommendations": [
      "anthropic.claude-code"
    ]
  }
}
```

Open via VS Code: `File → Open Workspace from File...`

Benefit: 1 VS Code window, 3 repos visible, terminal default in bot, .claude session noise hidden from sidebar.

---

## §4 — DoIt task for CC (run on next session)

```
TASK: Apply CC autonomy config locally (bot settings + workspace).
MODE: DoIt.

PRE-FLIGHT (auto-execute, halt on failure):
1. Test-Path "$env:USERPROFILE\rdm\dev\bot"  → True
2. Test-Path "$env:USERPROFILE\rdm\dev\discussion"  → True
3. Test-Path "$env:USERPROFILE\rdm\dev\platform"  → True
4. Test-Path "$env:USERPROFILE\rdm\rdm-workspace.code-workspace"  → False (not yet)
5. Test-Path "$env:USERPROFILE\rdm\dev\bot\.claude\settings.json"  → False (not yet, gitignored)

DELIVERABLES:

PASO 1 — Pull discussion repo (templates are here):
   cd "$env:USERPROFILE\rdm\dev\discussion"
   git pull origin main

PASO 2 — Create bot .claude folder + settings (local, gitignored):
   New-Item -Path "$env:USERPROFILE\rdm\dev\bot\.claude" -ItemType Directory -Force
   Copy-Item `
     "$env:USERPROFILE\rdm\dev\discussion\templates\bot-claude-settings.json" `
     "$env:USERPROFILE\rdm\dev\bot\.claude\settings.json"
   
   Verify:
   Test-Path "$env:USERPROFILE\rdm\dev\bot\.claude\settings.json"  → True
   Get-Content "$env:USERPROFILE\rdm\dev\bot\.claude\settings.json" | Select -First 5

PASO 3 — Verify .claude is gitignored (don't accidentally commit):
   cd "$env:USERPROFILE\rdm\dev\bot"
   git status --short
   - Should NOT show .claude/settings.json
   - If it shows: STOP, report (gitignore broken)

PASO 4 — Create workspace file:
   $workspaceContent = @'
{
  "folders": [
    { "path": "dev/bot", "name": "🔧 bot" },
    { "path": "dev/discussion", "name": "💬 discussion" },
    { "path": "dev/platform", "name": "📐 platform (read-only)" }
  ],
  "settings": {
    "claude.autoSaveBeforeEdit": true,
    "claude.confirmDestructiveOps": true,
    "git.confirmSync": false,
    "git.autofetch": true,
    "terminal.integrated.cwd": "${workspaceFolder:🔧 bot}",
    "files.exclude": {
      "**/.claude/sessions/**": true,
      "**/node_modules": true,
      "**/.next": true,
      "**/dist": true
    }
  },
  "extensions": {
    "recommendations": [
      "anthropic.claude-code"
    ]
  }
}
'@
   $workspaceContent | Out-File `
     -FilePath "$env:USERPROFILE\rdm\rdm-workspace.code-workspace" `
     -Encoding UTF8

   Verify:
   Test-Path "$env:USERPROFILE\rdm\rdm-workspace.code-workspace"  → True

PASO 5 — Report status (no commit, all local).

DEFAULTS:
- Encoding: UTF-8 for files
- No commits (all local files)
- No push

OUT OF SCOPE:
- NO commit bot/.claude/* (gitignored, must stay local)
- NO open VS Code (Alex does manually after task)
- NO modify discussion/.claude or platform/.claude (already correct)
- NO modify .gitignore in bot repo (intentional)

REPORTAR:
- bot/.claude/settings.json: exists with N lines, gitignored status confirmed
- rdm-workspace.code-workspace: exists at $env:USERPROFILE\rdm\
- Total files created: 2
- Alex's next manual step: VS Code → File → Open Workspace from File → 
  $env:USERPROFILE\rdm\rdm-workspace.code-workspace
```

---

## §5 — What Alex does after CC reports

1. Open VS Code (any window)
2. `File → Open Workspace from File...`
3. Navigate to `C:\Users\Alexa\rdm\rdm-workspace.code-workspace`
4. Click Open
5. Verify 3 folders visible: 🔧 bot · 💬 discussion · 📐 platform
6. Verify terminal opens in bot by default
7. Install Claude Code extension if not already (`Ctrl+Shift+X` → search "Claude Code")
8. Login to Anthropic if not already
9. Open any chat → test: ask CC `pnpm test` → should auto-execute (allow rule)
10. Test: ask CC `git push origin main` → should prompt Y/N (ask rule)
11. Test: ask CC `git push --force` → should refuse (deny rule)

If all 3 tests pass, setup correct.

---

## §6 — Maintenance going forward

### When to edit settings.json

If CC repeatedly asks Y/N for an operation Alex always approves → add to `allow`.
If CC auto-executes something risky that Alex didn't want → add to `ask` or `deny`.
If Alex finds new dangerous pattern → add to `deny`.

### Where edits happen

- `rdm-bot/.claude/settings.json` → edit locally, no commit
- `rdm-discussion/templates/bot-claude-settings.json` → edit + commit (template propagates to new clones)
- `rdm-discussion/.claude/settings.json` → edit + commit
- `rdm-platform/.claude/settings.json` → edit + commit

### Sync template after edits

If WC updates `templates/bot-claude-settings.json`, CC re-runs PASO 2 of §4 to refresh local bot settings.

---

## §7 — Files pushed today

| File | Repo | Commit |
|---|---|---|
| `.claude/settings.json` | rdm-discussion | e8a0f70 |
| `.claude/settings.json` | rdm-platform | 37111da |
| `templates/bot-claude-settings.json` | rdm-discussion | (this commit) |

---

**WC done. Awaiting CC to run §4 task whenever Alex says go.**

— WC, 2026-05-19
