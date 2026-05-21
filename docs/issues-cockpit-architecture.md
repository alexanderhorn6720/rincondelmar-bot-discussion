# /admin/issues — GitHub Operations Cockpit · Architecture

> Companion to spec `cc-instructions-bot/2026-05-21-admin-issues-cockpit.md`.
> Read the spec first if you want the *why*; this doc is the *how*.

## 1. System map

```
┌──────────────────────────┐        ┌──────────────────────────┐
│ apps/admin (rdm-platform)│        │   GitHub (3 repos)       │
│  /admin/issues/*         │        │  rdm-bot                 │
│   - inbox     - new      │        │  rdm-discussion          │
│   - detail    - grouped  │        │  rdm-platform            │
│   - cc-activity - brief  │        │                          │
└────────────┬─────────────┘        └────────┬───────┬─────────┘
             │ HTTPS (Better Auth cookie)     │ REST  │ webhooks
             ▼                                ▼       │
┌──────────────────────────────────────────────┐      │
│ worker-feedback (this PR)                    │◄─────┘
│  POST /api/feedback         → GitHub createIssue + D1 insert
│  GET  /api/feedback*        → D1 read
│  GET  /api/feedback/:n/clipboard → render + R2 sign
│  GET  /api/issues*          → D1 cache read
│  GET  /api/cc-sessions      → D1 read + status recompute
│  GET  /api/brief/today      → D1 aggregate → markdown
│  POST /api/webhooks/github  → verify HMAC + dispatch
│  GET  /api/r2/sign          → presigned PUT/GET
└───┬────────────────────────────────┬─────────┘
    │                                │
    ▼                                ▼
┌──────────────┐          ┌────────────────────────┐
│ D1 `rincon`  │          │ R2 `rdm-feedback-attach` │
│ migration    │          │  10MB/file max         │
│ 0042         │          │  signed PUT 1h         │
│ feedback_items│         │  signed GET 7d (refresh│
│ github_cache │          │   on every clipboard)  │
│ cc_sessions  │          └────────────────────────┘
└──────────────┘
```

## 2. Data flow

### 2.1 Submit (Karina or Alex via UI)

1. Browser calls `GET /api/r2/sign?content_type=image/png` per screenshot
   → returns `{upload_url, file_url_after_upload, key, expires_at}`
2. Browser PUTs file directly to R2 (using `upload_url`, 1h expiry).
3. Browser calls `POST /api/feedback` with `{title, body, bucket, priority,
   attachments: [key,...], related_threads: [...]}`.
4. Worker calls GitHub REST `POST /repos/{owner}/rdm-discussion/issues` with
   labels `kind/feedback, bucket/{x}, priority/{y}, status/inbox`.
5. Worker inserts `feedback_items` row with the issue number.
6. (Async) GitHub webhook fires `issues.opened` → worker upserts `github_cache`
   for the same issue (idempotent — same number).

### 2.2 Webhook sync (GitHub events)

Worker is subscribed to 3 repos. Each delivery:

1. Read raw body, verify `X-Hub-Signature-256` HMAC against
   `GITHUB_WEBHOOK_SECRET`. Reject 401 if invalid.
2. Switch on `X-GitHub-Event`:
   - `issues` → upsert cache; if `kind/feedback` also upsert feedback row.
   - `pull_request` → upsert cache; if merged, cascade `Closes #N` → set
     feedback status `done` for each ref.
   - `check_suite` → update `ci_status` / `ci_url` on associated PRs.
   - `push` → upsert `cc_sessions` row, branch-mapped to session_id.

All upserts use SQLite `ON CONFLICT(key) DO UPDATE` so redelivery is safe.

### 2.3 Smart Clipboard (paste-to-WC handoff)

1. Alex taps "Copy WC context" in the UI on issue #67.
2. UI calls `GET /api/feedback/67/clipboard`.
3. Worker reads feedback row + cache + open PRs that mention #67.
4. Worker re-signs every R2 attachment for a fresh 7d window.
5. Worker calls `renderClipboard()` → returns markdown.
6. UI writes the markdown to `navigator.clipboard`.

The 7d window restarts every call — no broken links if the user opens the
clipboard a week later, as long as they re-press Copy.

### 2.4 Daily Brief

1. Worker exposes `GET /api/brief/today`.
2. Aggregator queries:
   - `github_cache` merged PRs since 24h
   - `github_cache` closed issues since 24h
   - `feedback_items` opened since 24h
   - "Needs attention" view (PRs CI=success + issues status/triaged)
   - "Waiting on CC" view (status/spec-ready)
   - Open + recently-merged items for risk scan
3. Pure renderer (`lib/brief-generator.ts`) builds markdown with:
   - Yesterday counts
   - Waiting-on-you list with age
   - Waiting-on-CC list with thread refs
   - Risks (large PR / stale / unmerged migration / late-Friday deploy)
   - Top 3 priority (impact_score = priority × urgency × unblocks)
4. (Future) Cron trigger every 6am MX caches the result; for now query-on-demand.

## 3. Bindings + secrets

| Binding | Type | Value |
|---|---|---|
| `DB` | D1 | `rincon` (shared with worker-bot, web) |
| `FEEDBACK_ATTACH` | R2 | `rdm-feedback-attach` |
| `R2_S3_ENDPOINT` | var | `https://{account}.r2.cloudflarestorage.com` |
| `R2_BUCKET_NAME` | var | `rdm-feedback-attach` |
| `GITHUB_OWNER` | var | `alexanderhorn6720` |
| `GITHUB_PAT` | secret | PAT with `repo` scope, 3 repos |
| `GITHUB_WEBHOOK_SECRET` | secret | random hex, shared with all 3 webhooks |
| `R2_FEEDBACK_ACCESS_KEY` | secret | R2 → Manage API Tokens → S3-compat |
| `R2_FEEDBACK_SECRET_KEY` | secret | (paired with above) |
| `BETTER_AUTH_SECRET` | secret | shared with `apps/admin` session validation |

## 4. Database schema (migration 0042)

3 tables, all created with `IF NOT EXISTS`:

### feedback_items

| Column | Type | Notes |
|---|---|---|
| github_issue_number | INTEGER PK | matches the GitHub number |
| repo | TEXT | default `rdm-discussion` (all submits go there) |
| title, body | TEXT | mirror GitHub state |
| status | TEXT | `inbox\|triaged\|approved\|spec-ready\|in-pr\|done\|rejected` |
| bucket, priority | TEXT nullable | label-derived |
| submitter | TEXT | submitter email (admin) or GH login (synced) |
| attachments | JSON | array of R2 keys |
| related_threads | JSON | `["thread/127", ...]` |
| related_prs | JSON | `["rdm-bot#128", ...]` |
| wc_proposal | TEXT nullable | filled later by WC triage |
| created_at, updated_at | TEXT (ISO) | from GitHub |

Indexes: `(status, updated_at DESC)`, `(bucket, status)`, `(priority, status)`.

### github_cache

Denormalized mirror of GitHub issues + PRs across 3 repos. PK = `repo#number`.
Used to avoid GitHub API calls in hot paths and to support cross-cutting
queries (Smart Grouping, Needs Attention, Brief).

### cc_sessions

One row per CC session id (`cc-bot`, `cc-data`, `cc-strategy`, `cc-platform`).
Updated by `push` webhook events via branch-based mapping
([`lib/cc-branch-map.ts`](../../bot/apps/worker-feedback/src/lib/cc-branch-map.ts)).

## 5. Auth model

- **Better Auth** (in `apps/admin`) issues a session token, writes a row to
  the shared `session` table, sets the cookie `better-auth.session_token`.
- The worker reads that cookie, looks up `session JOIN user`, derives the
  user's role.
- Middleware:
  - `requireSession` — any logged-in user
  - `requireSubmitRole` — `admin | content_editor | feedback_only`
  - `requireOpsRole` — `admin` only (cc-sessions, brief)

The worker does **not** issue its own tokens. Single source of truth.

## 6. Idempotency + drift handling

- **Webhook redelivery**: every D1 write is `ON CONFLICT DO UPDATE` with
  `excluded.*`. Redelivery is a no-op (last writer wins on `updated_at`).
- **Webhook miss**: nightly reconcile cron (future work) compares
  `github_cache.last_synced_at` against GitHub's `updated_at` and refetches.
  Manual trigger: `POST /api/admin/reconcile` (TBD).
- **R2 URL expiry**: clipboard refreshes URLs on every call; no broken links
  as long as the user re-clicks Copy after the 7d window.
- **Better Auth session expiry**: worker checks `expiresAt < now` before
  trusting the session row.

## 7. Tests

| Layer | Tool | What's covered |
|---|---|---|
| Unit | Vitest | 91 tests in `tests/*.test.ts` |
| Build smoke | `wrangler deploy --dry-run` | bundle compiles, bindings resolve |
| Integration | (TBD) | mock D1 + R2, exercise full router |
| E2E | (TBD) | Karina UAT — submit + clipboard round-trip |

Coverage targets in spec §5 (≥80%) — current unit coverage is high on pure
modules (brief, clipboard, grouping, signatures, signer) but route handlers
need integration tests to verify D1 query shapes against the real schema.

## 8. Known deferrals (out of scope for first PR)

- Nightly reconcile cron (drift detect D1 ↔ GitHub)
- Webhook secret rotation flow
- Per-session role mapping for `feedback_only` (scaffolded, not enforced UI-side)
- Cron-triggered brief caching (currently render-on-demand)
- D1 backups specific to feedback tables (relies on `rincon`-level backup)

## 9. Spec deviations

Two from the spec, both documented in
[`threads/162-cc-bot-admin-issues-cockpit-halt-preflight.md`](../threads/162-cc-bot-admin-issues-cockpit-halt-preflight.md):

1. **Migration slot 0040 → 0042**. Spec hardcodes 0040 four times; slot
   was taken by `0040_rules_link_clicks.sql` (thread/141) and
   `0041_bot_short_links.sql` (thread/158). Renamed mechanically.

2. **Label count: 17 instead of 19**. Spec §4.12 header says "19 labels"
   but enumerates 17 (1 `kind/feedback` + 6 buckets + 3 priorities +
   7 statuses). Created what was enumerated.
