# Spec: /admin/issues — GitHub Operations Cockpit

**Type**: brain deep — full spec
**Author**: WC (Web Claude)
**Date**: 2026-05-21
**Target**: CC-Bot (single batch execution, one-run)
**Estimate**: 31-45h CC
**Thread ref**: `threads/161-wc-cc-admin-issues-cockpit-doit.md`
**Branch**: `feat/admin-issues-cockpit`
**Spec path target**: `rdm-discussion/cc-instructions-bot/2026-05-21-admin-issues-cockpit.md`

---

## 1. Context

### Why

Alex está overwhelmed con approval cognitive load: bashes, PRs, deploys, issues, feedback de Karina, todo fragmentado entre 3 repos (`rdm-bot`, `rdm-platform`, `rdm-discussion`) + GitHub app + chat web. La carga de orientarse antes de decidir consume más tiempo que la decisión misma.

Karina (content_editor) tiene insight operativo diario crítico pero no usa GitHub. Hoy el feedback de ella entra vía WhatsApp / chat fragmentado, sin tracking.

### Problem

1. **Visibilidad**: sin vista única, abrir 3 repos × N issues × N PRs para saber "qué necesita mi atención hoy" toma 15-30min cada mañana
2. **Entry friction**: Karina sin acceso GitHub bloquea su capacidad de reportar bugs en tiempo real
3. **Context loss**: cuando discuto un issue contigo en chat web, copiar manualmente título + body + screenshot + threads relacionados toma 2-3min de fricciones
4. **Multi-session collisions**: paralelizar CC sessions sin visibilidad de "quién toca qué ahora" causó colisiones threads 145-154

### Current state

- Issues live en `rdm-discussion` mezclados con threads/specs
- PRs distribuidos en `rdm-bot` y `rdm-platform`
- GitHub mobile app es la única UI móvil disponible (genérica, no aware del workflow RdM)
- Karina onboarding al sistema bloqueado
- Approval flow funciona pero requiere context-switching constante

### Goal

Wrapper visual sobre GitHub que da: **visibilidad + estructura + smart submit**. NO duplica approval logic. NO reescribe flujo Git. Respeta convenciones RdM (threads, buckets, anti-patterns) y reglas Claude (territories, modos de trabajo).

---

## 2. Explicit scope

### YES — in scope

- Nuevo Worker `apps/worker-feedback` en repo `rdm-bot`
- D1 migration con 3 tablas: `feedback_items`, `github_cache`, `cc_sessions`
- R2 bucket nuevo: `rdm-feedback-attach` (signed URLs 7d)
- UI nueva en `apps/admin` (rdm-platform) bajo `/admin/issues/*`
- Submit form con paste/upload screenshot (desktop-optimized, mobile-functional)
- Unified Inbox view (mobile-first) agrupada por status
- Smart Grouping view por `thread/XXX` reference
- CC Activity Tracker (poll-based, 60s interval)
- Daily Brief generator (cron mañana 6am MX, render on-demand)
- Context Cards expand-inline en cada issue/PR
- Smart Clipboard button: copia markdown estructurado al clipboard del navegador
- GitHub webhook receiver: sync issues/PRs events → D1 cache
- Cron daily reconcile: detecta drift D1 ↔ GitHub
- Labels creation en `rdm-discussion`: `kind/feedback`, `bucket/*`, `status/*`, `priority/*`
- Auth integration: `admin` (Alex) full, `content_editor` (Karina) submit+comment, scaffold `feedback_only` role
- Tests E2E happy paths + unit tests críticos
- Karina onboarding doc 1-page

### NO — out of scope (hard line)

- ❌ Approval buttons que actúan en GitHub
- ❌ Bash trigger / deploy trigger / migration trigger desde UI
- ❌ Chat inline con Anthropic API
- ❌ Deep-link a Claude.ai
- ❌ Telegram push / email push
- ❌ Notificaciones del navegador / VAPID push
- ❌ Guest CRM / guest feedback
- ❌ Asociar feedback a `booking_id` o `guest_id`
- ❌ Make.com integration
- ❌ Multi-language UI (ES only)
- ❌ Drag-drop kanban entre status
- ❌ Bashes/scripts execution

### Decision deferred (future scope)

- `feedback_only` role para empleados futuros (scaffold solo)
- `/admin/feedback` para huéspedes — F5+
- Capacitor.js wrap-to-APK — F5+
- Integration con `booking_lifecycle_events` (F1 foundation) — automatic

---

## 3. Closed decisions (20 items)

| # | Decisión | Resolución |
|---|---|---|
| 1 | Mobile vs desktop primary | Desktop para submit, mobile solo view + tap Open GitHub |
| 2 | Approval logic | Delegar 100% a GitHub. Solo informativa. |
| 3 | Chat inline con bot | NO. Smart Clipboard only. |
| 4 | Deep-link a Claude.ai | NO. |
| 5 | Repo issues | Reusar `rdm-discussion` con `kind/feedback` |
| 6 | Worker location | Nuevo `apps/worker-feedback` |
| 7 | UI location | `apps/admin` en rdm-platform |
| 8 | Notification channel | Solo UI |
| 9 | Screenshot storage | R2 `rdm-feedback-attach`, signed URLs 7d, refresh on access |
| 10 | Ruta principal | `/admin/issues` |
| 11 | Submit roles | admin + content_editor. Scaffold feedback_only |
| 12 | Buckets | admin, web, bot, beds24, content, infra |
| 13 | Priority | low, normal, high |
| 14 | Big-bang o fases | One-run single CC session |
| 15 | Tests coverage | ≥80% |
| 16 | Cron daily brief | 6am MX |
| 17 | CC poll interval | 60s |
| 18 | Status state machine | inbox → triaged → approved → spec-ready → in-pr → done; rejected |
| 19 | Worker URL | `worker-feedback.{cf-account}.workers.dev` (no custom domain) |
| 20 | CC identity mapping | **Branch-based** NO email-based |

---

## 4. Implementation

### 4.1 Files

```
rdm-bot/
  apps/worker-feedback/                       [NEW]
    wrangler.toml, package.json, tsconfig.json
    src/
      index.ts                                # Hono router
      routes/
        feedback.ts                           # POST/GET /api/feedback*
        issues.ts                             # GET /api/issues*
        cc-sessions.ts
        brief.ts
        webhooks.ts                           # POST /api/webhooks/github
        r2.ts                                 # GET /api/r2/sign
        clipboard.ts                          # GET /api/feedback/:n/clipboard
      lib/
        github-client.ts
        d1-sync.ts
        reconcile.ts
        clipboard-template.ts
        smart-grouping.ts
        brief-generator.ts
        cc-branch-map.ts                      # Branch → CC session_id rules
      types.ts
    tests/ (feedback, issues, webhooks, clipboard, grouping, brief)
  migrations/0040_feedback_system.sql         [NEW]

rdm-platform/apps/admin/src/
  pages/admin/issues/
    index.astro                               # Unified Inbox
    new.astro                                 # Submit form
    [number].astro                            # Detail + Copy + Open
    cc-activity.astro
    brief.astro
    grouped.astro
  components/issues/
    InboxList, IssueCard, ContextCard, SubmitForm,
    ScreenshotUpload, SmartClipboardButton, OpenInGitHubButton,
    StatusBadge, BucketBadge, GroupedThreadView,
    CCSessionCard, DailyBriefSection
  lib/api-client.ts, clipboard.ts

rdm-discussion/
  cc-instructions-bot/2026-05-21-admin-issues-cockpit.md (this)
  docs/karina-issues-guide.md                 [NEW]
  docs/issues-cockpit-architecture.md         [NEW]
```

### 4.2 D1 schema (migration 0040)

```sql
CREATE TABLE feedback_items (
  github_issue_number INTEGER PRIMARY KEY,
  repo TEXT NOT NULL DEFAULT 'rdm-discussion',
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL,
  bucket TEXT,
  priority TEXT,
  submitter TEXT NOT NULL,
  attachments JSON DEFAULT '[]',
  related_threads JSON DEFAULT '[]',
  related_prs JSON DEFAULT '[]',
  wc_proposal TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_feedback_status ON feedback_items(status, updated_at DESC);
CREATE INDEX idx_feedback_bucket ON feedback_items(bucket, status);
CREATE INDEX idx_feedback_priority ON feedback_items(priority, status);

CREATE TABLE github_cache (
  cache_key TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  number INTEGER NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  state TEXT NOT NULL,
  author TEXT,
  labels JSON DEFAULT '[]',
  branch TEXT,
  base_branch TEXT,
  closes_issues JSON DEFAULT '[]',
  thread_refs JSON DEFAULT '[]',
  ci_status TEXT,
  ci_url TEXT,
  files_changed INTEGER,
  additions INTEGER,
  deletions INTEGER,
  url TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_synced_at TEXT NOT NULL
);
CREATE INDEX idx_cache_repo_type ON github_cache(repo, type, state);
CREATE INDEX idx_cache_thread_state ON github_cache(state, last_synced_at DESC);
CREATE INDEX idx_cache_state_updated ON github_cache(state, updated_at DESC);

CREATE TABLE cc_sessions (
  session_id TEXT PRIMARY KEY,
  repo TEXT,
  branch TEXT,
  last_commit_sha TEXT,
  last_commit_message TEXT,
  last_commit_at TEXT,
  active_pr_number INTEGER,
  active_pr_repo TEXT,
  status TEXT,
  detected_at TEXT NOT NULL
);
CREATE INDEX idx_cc_status ON cc_sessions(status, detected_at DESC);
```

### 4.3 Worker API contracts

Base URL: `worker-feedback.{cf-account}.workers.dev`

| Method | Path | Body/Query | Returns |
|---|---|---|---|
| POST | `/api/feedback` | `{title, body, bucket, priority, attachments[], related_threads[]}` | `{github_issue_number, github_url, status, attachments[]}` |
| GET | `/api/feedback` | `?status&bucket&priority&limit&offset` | `{items[], total}` |
| GET | `/api/feedback/:n` | — | `{...item, github_cache_data, screenshots_signed[]}` |
| GET | `/api/feedback/:n/clipboard` | — | `{markdown, screenshot_urls_refreshed_7d[]}` |
| GET | `/api/issues` | `?repo&type&state&needs_attention` | `{items[], total}` |
| GET | `/api/issues/grouped` | — | `{groups: [{thread_ref, title, items[]}], ungrouped[]}` |
| GET | `/api/issues/needs-attention` | — | `{items[], counts: {prs, issues}}` |
| GET | `/api/cc-sessions` | — | `{sessions[]}` |
| GET | `/api/brief/today` | `?regenerate=true` | `{markdown, generated_at, sections{}}` |
| POST | `/api/webhooks/github` | webhook payload + `X-Hub-Signature-256` | `{ok, action_taken}` |
| GET | `/api/r2/sign` | `?filename&content_type` | `{upload_url, file_url_after_upload, expires_at}` |

`/api/issues/needs-attention` logic:
- PRs open + CI passing + no requested-changes review
- Issues status=triaged (WC proposal pending Alex)
- Issues priority=high + status=inbox

Auth: Better Auth session cookie validated server-side. R2 sign requires admin or content_editor.

### 4.4 Smart Clipboard template (canonical)

`GET /api/feedback/:n/clipboard` returns markdown:

```markdown
## Issue #{n} · {repo} · bucket/{bucket} · priority/{priority}

**Title**: {title}
**Submitter**: {submitter} (via /admin/issues)
**Created**: {YYYY-MM-DD HH:mm CST}
**Status**: {status}

### Body
{body verbatim}

### Screenshots
{for each attachment}
{i}. {signed_url_7d} (expires {date})
{end}

### Related context
- Threads: {related_threads}
- Open PRs: {related_prs}
- Related closed issues: {auto-detected from cache}

---

**GitHub URL**: https://github.com/alexanderhorn6720/{repo}/issues/{n}

---

Hey WC, traje este issue para discutir contigo en el WC project RdM.

Propón triage:
1. Causa raíz probable
2. Bucket de impacto
3. Estimate CC
4. Si hay items relacionados que agrupar
```

Signed URLs refresh on every `/clipboard` call → ventana 7d siempre fresca.

### 4.5 GitHub webhook event handling

Eventos suscritos en `rdm-bot`, `rdm-discussion`, `rdm-platform`:

| Event | Action | D1 update |
|---|---|---|
| `issues.opened` | Upsert github_cache + feedback_items si label `kind/feedback` | both |
| `issues.edited` | Update body/title | both |
| `issues.labeled` | Update labels + recalc status si `status/*` | both |
| `issues.closed` | state='closed', status='done'/'rejected' | both |
| `pull_request.opened` | Upsert cache + parse closes_issues | github_cache |
| `pull_request.synchronize` | Update files/additions/deletions | github_cache |
| `pull_request.closed` merged=true | state='merged', cascade close feedback en closes_issues | both |
| `pull_request_review.submitted` | Update review state | github_cache |
| `check_suite.completed` | Update ci_status | github_cache |
| `push` (default branch) | Update cc_sessions | cc_sessions |

HMAC SHA256 con `X-Hub-Signature-256` y `GITHUB_WEBHOOK_SECRET` Worker secret.

### 4.6 CC Activity detection (BRANCH-BASED)

Worker cron cada 60s:

1. Por cada repo, fetch commits últimos 5min
2. Extraer branch name de cada commit
3. Mapear branch → session_id via rules:
   - `feat/greeter-*`, `feat/canary-*`, `fix/bot-*`, `feat/booker-*` → **cc-bot**
   - `feat/data-*`, `fix/data-*`, `feat/mining-*` → **cc-data**
   - `feat/state-*`, `feat/numbering-*`, `feat/process-*`, `feat/admin-issues-*` → **cc-strategy**
4. Fallback repo-based si branch no matchea:
   - rdm-bot → cc-bot
   - rdm-discussion → cc-strategy
   - rdm-platform → cc-platform
5. Update `cc_sessions` con: session_id, repo, branch, last_commit_sha/message/at
6. Identificar PRs activos por session (head branch matchea rules)
7. Status: active (≤30min), idle (30min-4h), done (>4h)

Mapping config en `lib/cc-branch-map.ts`:

```typescript
export const CC_BRANCH_RULES: Array<{ pattern: RegExp; session_id: string }> = [
  { pattern: /^feat\/greeter-/, session_id: "cc-bot" },
  { pattern: /^feat\/canary-/, session_id: "cc-bot" },
  { pattern: /^feat\/booker-/, session_id: "cc-bot" },
  { pattern: /^fix\/bot-/, session_id: "cc-bot" },
  { pattern: /^feat\/data-/, session_id: "cc-data" },
  { pattern: /^feat\/mining-/, session_id: "cc-data" },
  { pattern: /^fix\/data-/, session_id: "cc-data" },
  { pattern: /^feat\/state-/, session_id: "cc-strategy" },
  { pattern: /^feat\/numbering-/, session_id: "cc-strategy" },
  { pattern: /^feat\/process-/, session_id: "cc-strategy" },
  { pattern: /^feat\/admin-issues-/, session_id: "cc-strategy" },
];

export const REPO_FALLBACK: Record<string, string> = {
  "rdm-bot": "cc-bot",
  "rdm-discussion": "cc-strategy",
  "rdm-platform": "cc-platform",
};
```

NO requiere configurar git identities separadas. Cualquier autor commitea en feat/canary-* → clasifica como cc-bot work.

### 4.7 Smart Grouping algorithm

`GET /api/issues/grouped`:

1. Fetch all open items from `github_cache`
2. Extraer thread refs de:
   - Body via `thread/(\d+)` regex
   - Branch via `(?:feat|fix|chore)/(?:.*-)?thread-(\d+)`
   - Labels pattern `thread/*`
3. Agrupar por thread_ref (un item puede pertenecer a múltiples grupos)
4. Por grupo: fetch thread title del file en rdm-discussion (cache 24h)
5. Items sin thread → "ungrouped"
6. Sort: groups con más actividad reciente primero

### 4.8 Daily Brief generator (rule-based, no LLM)

`GET /api/brief/today` regenerado 6am MX:

```markdown
# 📋 Daily Brief · {DATE}

## YESTERDAY ({yesterday_date})
- Merged: {count} PRs ({list_links})
- Closed: {count} issues
- Opened: {count} new feedback items

## WAITING ON YOU ({total})
- {type} #{n} {repo} — {title}
  ↳ CI {ci_status}, {age_humanized}

## WAITING ON CC ({total})
- {thread_ref}: {title} ({assigned_cc}, {age})

## NEW RISKS DETECTED
- {risk_text}

## SUGGESTED PRIORITY (top 3)
1. {action} → {expected_outcome}
2. ...
```

Risk heuristics:
- PR touches >10 files
- Issue open >7 days no activity
- Migration en unmerged PR
- Production deploy late Friday (>5pm Fri)

Impact_score = priority_weight × urgency × unblocks_count.

### 4.9 UI views (mobile-first wireframes)

#### `/admin/issues` (Unified Inbox)

```
┌─────────────────────────────────────┐
│ Issues · Alex                       │
│ [+ New] [CC] [Brief] [Grouped]      │
├─────────────────────────────────────┤
│ 🔴 Needs you (3)                ▾   │
│ ┌─────────────────────────────────┐ │
│ │ PR #128 rdm-bot                 │ │
│ │ feat/canary-25%                 │ │
│ │ CI ✅ · 5 files · Closes #47,51 │ │
│ │ [Open in GitHub]                │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Issue #67 rdm-discussion        │ │
│ │ "Bot responde EN a guest ES"    │ │
│ │ karina · bucket/bot · 🔴        │ │
│ │ status/inbox · 2h ago           │ │
│ │ [Open] [Copy WC ctx]            │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 🟡 Awaiting CC (5)              ▸   │
│ 🟢 In progress (8)              ▸   │
│ ⚪ Recently done (12, 7d)       ▸   │
└─────────────────────────────────────┘
```

#### `/admin/issues/new` (desktop primary)

```
┌─────────────────────────────────────────────┐
│ New Issue                       [Cancel] [✓]│
├─────────────────────────────────────────────┤
│ Title*    [_______________________________] │
│ Bucket*   [bot ▾]     Priority [high ▾]    │
│ Body      [textarea, paste screenshots 📋]  │
│ Screenshots [📎] [📎] (paste/drag/upload)   │
│ Related threads (optional) [thread/127] [+] │
│                                             │
│ Submit → GitHub issue en rdm-discussion     │
│ Labels: kind/feedback · bucket/bot ·        │
│ priority/high · status/inbox                │
└─────────────────────────────────────────────┘
```

#### `/admin/issues/:n` (Detail)

```
┌─────────────────────────────────────────────┐
│ ← Issue #67                                 │
│ Bot responde EN a guest ES                  │
│ karina · 2h ago · status/inbox              │
│ bucket/bot · priority/high                  │
├─────────────────────────────────────────────┤
│ Body: {full body}                           │
│ Screenshots: [📷] [📷]                      │
│ Related: thread/127, thread/89; closed #54  │
│                                             │
│ ── WC Proposal (cuando status=triaged) ──   │
│ Root cause: ...                             │
│ Fix path: ...                               │
│ Estimate: 2-3h. Risk: low.                  │
│ Suggested grouping: con #58, #62 (lang)     │
│                                             │
│ [📋 Copy WC context]                        │
│ [↗ Open in GitHub]                          │
└─────────────────────────────────────────────┘
```

#### `/admin/issues/grouped`

```
🧵 thread/134 Beds24 read-only proxy
  ├─ Issue #45 spec ✅ done
  ├─ PR #129 phase 1 calendar 🟡 CI run
  └─ Issue #46 phase 2 (blocked by #129)

🧵 thread/131 Mobile inbox follow-ups
  ├─ Issue #58 perf iPhone SE
  ├─ Issue #59 dark mode bubble bug
  └─ PR #130 fix bubble ✅ merged

── Ungrouped (3) ──
  └─ ...
```

#### `/admin/issues/cc-activity`

```
🟢 cc-bot · active 11m ago
  Repo: rdm-bot · Branch: feat/canary-25%
  Last: "feat: ramp to 25%"
  Active PR: #128 (draft → ready, CI ✅)

⚪ cc-data · idle 4h
  Last: thread/142 data mining v2

🟢 cc-strategy · active 24m ago
  Repo: rdm-discussion
  Last: "feat: thread/153 numbering"

⚠️ Collision: cc-bot y cc-strategy
   both touched rdm-discussion in last 1h
```

#### `/admin/issues/brief`

Rendered output del Daily Brief generator (§4.8).

### 4.10 Auth integration

Better Auth existing en `apps/admin`:

- `admin` (Alex): full access
- `content_editor` (Karina): submit + view (no cc-activity detallado)
- `feedback_only` (scaffold): future role empleados, solo /new + own items

Worker valida session cookie en cada API call. R2 sign requires admin o content_editor.

### 4.11 R2 bucket setup

```
Bucket: rdm-feedback-attach
Region: auto
Public access: NO
URL signing: enabled, 7d TTL
Refresh: every /clipboard call re-signs
Max file: 10MB
Allowed: image/png, jpeg, webp, gif
Naming: {YYYY}/{MM}/{issue_n}/{timestamp}-{random}.{ext}
Retention: 1 year, archive flag (no auto-delete)
```

Worker secrets: `R2_FEEDBACK_ACCESS_KEY`, `R2_FEEDBACK_SECRET_KEY`.

### 4.12 GitHub labels (19 to create)

Via `gh label create -R alexanderhorn6720/rdm-discussion`:

```
kind/feedback         #d4f0d4   "Submitted via /admin/issues"
bucket/admin          #c1d9f0   "Admin UI / backoffice"
bucket/web            #c1d9f0   "Public site"
bucket/bot            #c1d9f0   "Greeter / Booker / WhatsApp"
bucket/beds24         #c1d9f0   "Beds24 integration / sync"
bucket/content        #c1d9f0   "Listings / KB / reviews"
bucket/infra          #c1d9f0   "CF / D1 / R2 / Workers"
priority/low          #e0e0e0   "Nice to have"
priority/normal       #ffeb99   "Normal queue"
priority/high         #ffc1c1   "Needs prompt attention"
status/inbox          #f0f0f0   "Awaiting WC triage"
status/triaged        #fff4b3   "WC proposed, awaiting Alex"
status/approved       #b3e6ff   "Alex approved, spec pending"
status/spec-ready     #b3d9ff   "Thread/spec exists, CC pull"
status/in-pr          #c3a8e0   "PR open referencing this"
status/done           #b3e6b3   "Closed via merged PR"
status/rejected       #e0b3b3   "Closed, won't fix"
```

Setup en `scripts/setup-labels.sh` parte del setup phase.

---

## 5. Tests

### E2E (7 happy paths)

1. **Submit → GitHub → UI**: Karina submits con screenshot → R2 upload → GitHub issue creado con body+image → labels aplicados → webhook fires → D1 sync → aparece en `/admin/issues` <5s
2. **Smart Clipboard**: tap Copy → markdown estructurado en clipboard → screenshot URLs accesibles 7d
3. **Approval externo refleja**: label `status/inbox → status/triaged` en GitHub → webhook → D1 update → UI refresh
4. **PR cierra issue**: PR merged con `Closes #67` → webhook → issue closes → status=done en D1
5. **Smart Grouping**: 3 issues `thread/134` + 1 PR branch `feat/thread-134-phase2` → grupo retornado con 4 items
6. **Daily Brief**: cron 6am MX → markdown con 5 secciones → top-3 priority ranked
7. **CC Activity branch-based**: commit en `feat/canary-test-x` → cc-bot=active; commit en `feat/data-test-y` → cc-data=active

### Unit (8 critical)

- R2 sign URL: signature válida, expira 7d exactly
- GitHub webhook HMAC: rechaza inválidos
- Smart Clipboard template: markdown consistente
- Thread regex: extrae múltiples threads de un body
- CC branch mapping: unknown branch → repo-based fallback
- Drift reconcile: detecta cuando D1 diverge de GitHub
- Brief heuristics: PR>10 files flagged, issue>7d flagged, late Friday deploy flagged
- Status state machine: solo transiciones válidas (no done→inbox)

### Coverage target: ≥80% statements + branches. Vitest + happy-dom.

---

## 6. Definition of Done (20 items checkable)

1. ☐ Migration 0040 applied to D1 rincon (`wrangler d1 execute rincon --command "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('feedback_items','github_cache','cc_sessions')"`)
2. ☐ R2 bucket `rdm-feedback-attach` creado (`wrangler r2 bucket list`)
3. ☐ Worker `worker-feedback` deployed (`wrangler tail worker-feedback`)
4. ☐ GitHub webhooks configured en 3 repos (Settings > Webhooks)
5. ☐ Worker secrets set: R2 access/secret, GITHUB_WEBHOOK_SECRET, GITHUB_PAT (`wrangler secret list`)
6. ☐ 19 labels creados en rdm-discussion (`gh label list -R alexanderhorn6720/rdm-discussion`)
7. ☐ Todas las 6 UI routes live:
   - ☐ `/admin/issues` Unified Inbox
   - ☐ `/admin/issues/new` Submit form
   - ☐ `/admin/issues/:n` Detail
   - ☐ `/admin/issues/grouped` Smart Grouping
   - ☐ `/admin/issues/cc-activity`
   - ☐ `/admin/issues/brief`
8. ☐ Desktop submit con paste: copy → paste → preview muestra
9. ☐ Mobile submit functional: tap upload → file picker → preview → submit
10. ☐ Mobile inbox view OK: status groups collapsible, items tappable, filtros
11. ☐ Smart Clipboard endpoint retorna markdown válido con R2 URLs accesibles via curl
12. ☐ Karina UAT: ella submits 2 test items con screenshots desde iPhone → aparecen en /admin/issues → Copy + Open funcionan
13. ☐ Daily brief endpoint genera markdown 5 secciones sin errores
14. ☐ CC Activity classifies por branch: commit `feat/canary-test` → cc-bot, commit `feat/data-test` → cc-data
15. ☐ Drift reconcile cron nightly detecta drift artificial
16. ☐ Tests pass ≥80% coverage (`pnpm test:coverage`)
17. ☐ Self-review del diff: no out-of-scope, no secrets, no hardcoded paths
18. ☐ Spec archivado en `cc-instructions-bot/2026-05-21-admin-issues-cockpit.md`
19. ☐ Architecture doc en `docs/issues-cockpit-architecture.md`
20. ☐ Karina guide en `docs/karina-issues-guide.md` (1 pag, ES, screenshots)

---

## 7. Risks + mitigations

| # | Riesgo | Prob | Impact | Mitigación |
|---|---|---|---|---|
| R1 | Sync drift D1↔GitHub | media | media | Webhook primary + cron daily reconcile 6am MX + `/api/admin/reconcile` manual |
| R2 | Worker cae | baja | media | UI banner "Worker offline, use GitHub" + link directo |
| R3 | Scope creep guest CRM | alta | alta | Hard line spec §2. Karina guide explícita. Reject guest items. |
| R4 | R2 URL expira mid-discussion | media | baja | Refresh-on-access en /clipboard. 7d window. |
| R5 | GitHub rate limits | baja | media | D1 cache absorbe 99% reads. Webhook reduce polling. Exponential backoff. |
| R6 | Karina UX confusion | media | alta | UAT + 1pg guide + Alex acompaña primera semana |
| R7 | WC inunda inbox con comentarios | media | baja | Auto-batch convention: 3-5 items por sesión triage |
| R8 | Mobile paste flaky iOS Safari | media | baja | Desktop-primary submit. Mobile = view only. File input fallback. |
| R9 | CC misclassification | media | baja | Branch rules conservadoras + repo fallback. Rules expandibles en cc-branch-map.ts |
| R10 | Brief stale si cron falla | baja | baja | UI muestra "last generated at X" + manual refresh + banner si >24h stale |
| R11 | Auth bypass via URL directa | baja | crítica | Better Auth middleware + worker valida cookie cada API call. Tests cubren. |
| R12 | Webhook DoS no-GitHub | media | baja | HMAC validation + rate limit 100req/min |
| R13 | R2 storage cost runaway | baja | baja | 10MB max/file. Karina ~3 files/issue. ~$0.015/GB/mo. |
| R14 | Spec changes mid-execution | media | alta | Out-of-scope → issue separado, NO inline. Cambio significativo → halt + new spec |
| R15 | Karina submits info sensible | media | media | Guide explica qué NO incluir. UI placeholder warning. Long-term scrub regex. |
| R16 | Multi-session WC colisiona | media | media | Convention: una WC session edita threads a la vez. UI no requiere cambio WC. |

---

## 8. Execution notes for CC

### Order (additive-first, target 35h)

1. **Setup** (2h): branch `feat/admin-issues-cockpit`, `scripts/setup-labels.sh`, R2 bucket, worker-feedback skeleton
2. **D1 schema** (2h): Migration 0040 local first → verify → remote
3. **Worker API** (12h): r2.ts → feedback.ts → webhooks.ts → issues.ts → clipboard.ts → cc-sessions.ts → brief.ts (cada uno con tests)
4. **GitHub webhooks** (3h): configurar 3 repos via gh CLI, test signature con ngrok local antes de live
5. **UI components** (10h): ScreenshotUpload → SubmitForm → InboxList → IssueCard → SmartClipboardButton → ContextCard → grouped/cc-activity/brief views (mobile-first responsive)
6. **Integration tests** (4h): E2E §5
7. **Docs** (1h): architecture.md + karina-guide.md
8. **Self-review** (1h): full diff, no out-of-scope, no secrets, mobile responsive via DevTools

### Halt conditions (>30min blocked)

- Webhook HMAC failing repeatedly
- D1 migration remote fails despite local success
- R2 signed URL returns 403
- Better Auth session not propagating to worker
- Karina UAT confusion not solvable inline

STOP, comenta en thread 161, espera Alex.

### Out-of-scope guardrails

Si encuentras durante ejecución:
- Bug en `apps/worker-bot` no relacionado → issue, NO fix
- Pet policy `/noche` residual → issue separado
- Karina training 500 pendiente → NO tocar (PR fix/karina-training-input-self-close)
- Cambios Greeter prompt → fuera scope, issue
- thread/127 A5 Chrome MCP → fuera scope

### Hard halt: 45h

Si excedes 45h, halt y comenta. NO grindear hasta 60h.

---

## 9. Post-merge follow-ups (Alex side, no CC)

1. Verify webhook delivery cada repo (Settings > Webhooks > Recent Deliveries)
2. Karina UAT 30min con Alex acompañando, 2 test items
3. Distribuir Karina guide (PDF + WhatsApp)
4. Smoke test daily brief 1 semana
5. Monitor R2 + worker logs primeras 72h
6. Si OK: announce Karina + bookmark `/admin/issues` mobile

---

## 10. Future iterations (NOT in this spec)

F5+: booking_id/guest_id association, push notifications opcional, multi-language UI, drag-drop kanban reorder, WC auto-triage proactivo (>24h items), M5 Tasks integration, metrics dashboard time-to-triage/resolution/throughput.

---

**End of spec.**

Numbering: thread asignado **161** (`threads/161-wc-cc-admin-issues-cockpit-doit.md`). Verified: thread/160 was last sequential at spec push time.
