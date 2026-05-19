# Thread 135 · CC → WC + Alex · Beds24 read-only proxy complete

**From:** CC autonomous
**To:** WC + Alex
**Date:** 2026-05-19
**Type:** DoIt completion report (responds to thread/134)
**Status:** Phase A–E done · Phase F pending Alex merge · Phase G snippet below

---

## TLDR

`feat/beds24-proxy-calendar` branch shipped to **PR #127**:
https://github.com/alexanderhorn6720/rdm-bot/pull/127

Phase 1 calendar endpoint live in code + 32 vitest tests passing + typecheck
clean + build clean. Blocked on Alex for secret + migration + DNS + deploy
(checklist in PR description).

Time spent: ~1h (well under 4-6h budget — spec was extremely tight and
existing `beds24-auth.ts` + Hono patterns dropped right in).

---

## Phase results

| Phase | Status | Notes |
|---|---|---|
| Pre-flight | ✅ | Repos synced. `beds24-auth.ts` + `KV_KNOWLEDGE` binding verified. `audit_log` table NOT in D1 prod (only `admin_import_logs` + `human_handoff_log` exist). No file collision with thread/127 (different files entirely). |
| A · Ground truth | ✅ | `getBeds24AccessToken(env)` exported. Hono setup confirmed. `audit_log` missing → migration 0039 added in this PR; audit insert wrapped in `try/catch` so request still succeeds pre-migration. |
| B · Handler | ✅ | `apps/worker-bot/src/proxy-beds24.ts` (354 lines). Constant-time bearer compare via byte XOR. `ACTIVE_ROOMS` whitelist (Casa Chamán 679176 intentionally excluded). Cleaned schema + `?raw=true` escape hatch. KV cache 30-min TTL with `?fresh=true` bypass. All Beds24 error paths (429 / 5xx / network / malformed JSON / auth-fail) covered. |
| C · Route + CORS | ✅ | `apps/worker-bot/src/index.ts`: `BEDS24_PROXY_TOKEN` added to `Env`, `handleProxyCalendar` imported, `OPTIONS /proxy/beds24/*` preflight + `app.use('/proxy/beds24/*')` middleware injecting CORS headers + GET route registered. |
| D · Tests | ✅ | `apps/worker-bot/tests/proxy-beds24.test.ts` — **32 tests** (target was ≥15). Coverage: auth 6, params 7, cache 5, Beds24 paths 5, schema transform 7, CORS 1, audit resilience 1. Full worker-bot suite 739/739 pass. `pnpm typecheck` clean. `pnpm build` clean (506 KiB / 107 KiB gzip). |
| E · PR + wait | ⏳ | PR #127 opened with explicit Alex action checklist. Awaiting "thread/134 merged" signal from Alex. |
| F · Smoke | ⏳ | Pending Alex deploy. Curl commands ready (see PR description). |
| G · Docs | ✅ | `apps/worker-bot/README.md` created with endpoint table, error codes, cache details, audit pattern, Phase 2+ blueprint. Project knowledge snippet below. |

---

## Final test counts (spec §5.1-§5.6 coverage)

| Section | Tests |
|---|---|
| §5.1 Auth (no header, wrong prefix, mismatch, length diff, token unconfigured, valid) | 6 |
| §5.2 Params (missing, invalid roomId, Casa Chamán block, invalid date, start>end, range>365, `roomId=all`) | 7 |
| §5.3 Cache (miss, hit + age, `?fresh=true` bypass, `?raw=true` no cache, stale entry >30min refetch) | 5 |
| §5.4 Beds24 (429+Retry-After, 500→502, malformed JSON, auth throws, network fail) | 5 |
| §5.5 Schema transform (full map, unknown roomId, available=false, available=true, missing minStay, full response meta, `?raw=true` shape) | 7 |
| §5.6 CORS (OPTIONS 204 + headers) | 1 |
| Resilience (audit_log throws → request still 200) | 1 |
| **Total** | **32** |

All green: `pnpm vitest run tests/proxy-beds24.test.ts → 32 passed`.

---

## Alex action checklist (also in PR #127 description)

- [ ] `openssl rand -hex 32` → generate token locally
- [ ] `cd apps/worker-bot && pnpm wrangler secret put BEDS24_PROXY_TOKEN` → paste value
- [ ] `cd apps/worker-bot && pnpm wrangler d1 execute rincon --remote --file=../../migrations/0039_audit_log.sql` → apply audit_log migration
- [ ] CF Dashboard → Workers & Pages → `rincon-bot` → Settings → Triggers → Custom Domains → Add `beds24.rincondelmar.club`
- [ ] Review PR #127 code diff
- [ ] Merge PR
- [ ] `cd apps/worker-bot && pnpm wrangler deploy` (manual per CLAUDE.md hard rule)
- [ ] Ping CC with "thread/134 merged" → CC runs Phase F smoke tests

---

## Smoke test plan (Phase F — runs after merge + deploy)

```bash
# 1. Health (should reach existing worker-bot)
curl -i https://beds24.rincondelmar.club/health

# 2. Unauthed → 401
curl -i "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"

# 3. Authed cold → 200 + X-Cache-Hit: false
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"

# 4. Authed warm → 200 + X-Cache-Hit: true
# (repeat #3 immediately)

# 5. Invalid room → 400 invalid_room_id
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=99999&startDate=2026-12-20&endDate=2026-12-25"

# 6. Casa Chamán block → 400 invalid_room_id (anti-pattern memory #3)
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=679176&startDate=2026-12-20&endDate=2026-12-25"

# 7. audit_log rows
cd apps/worker-bot && pnpm wrangler d1 execute rincon --remote --command \
  "SELECT kind, json_extract(payload_json,'$.endpoint') AS endpoint, created_at FROM audit_log ORDER BY id DESC LIMIT 5"
```

---

## Project knowledge snippet — markdown ready to paste

Paste into each Claude project that should reach the proxy (WC web project,
CC autonomous projects, mobile/desktop, external tools):

```markdown
## Beds24 Proxy Access (Phase 1)

Base URL: https://beds24.rincondelmar.club/proxy/beds24/

Authentication: bearer token. Ask Alex for the current `BEDS24_PROXY_TOKEN`
value — rotated on demand via `wrangler secret put`.

Available endpoint:

- `GET /calendar?roomId={id}&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`
  - `roomId`: `78695` (Rincón del Mar), `374482` (Las Morenas direct),
    `74322` (Las Morenas Airbnb), `637063` (Huerta Cocotera),
    `74316` (Combinada), or `all` to query all rooms.
  - Optional: `&fresh=true` (bypass 30-min KV cache),
    `&raw=true` (Beds24 passthrough, no transform, no cache).
  - Date range max 365 days; `endDate >= startDate`; format strict `YYYY-MM-DD`.
  - Returns: `{ ok, cached, cache_age_seconds, rooms: [{ room_id, room_name,
    dates: [{ date, available, price_mxn, min_stay }] }], meta }`.
  - Response headers: `X-Cache-Hit`, `X-Cache-Age`, `Retry-After` (on 429).

Usage from web_fetch:

  fetch(
    "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25",
    { headers: { "Authorization": "Bearer <TOKEN>" } }
  )

Errors: 400 (params), 401 (auth), 429 (rate limit bubble), 502
(beds24_error / beds24_auth_failed / beds24_fetch_failed / beds24_malformed_json),
503 (proxy_token_not_configured).

Casa Chamán (679176) is intentionally excluded until Q3 2026 — requests
return 400 invalid_room_id.

Cache: 30 minutes per (roomIds, startDate, endDate). Beds24 rate limit
~5 req/sec; cache absorbs typical query loads. Use `?fresh=true` sparingly.

Read-only by design — no write endpoints will ever be added to this proxy.
```

---

## Suggested order for Phase 2 endpoints

Recommendation: order by **value-to-effort** for self-serve WC sessions.

| # | Endpoint | Why first | Approx effort | Notes |
|---|---|---|---|---|
| 1 | `/proxy/beds24/bookings` | Highest WC use-case (re-search Alex's "what bookings arrive next week?", arrival reports, occupancy summaries). Cleanest pattern fit. | 1-2h | Reuse `proxy-beds24.ts` skeleton; new params (propertyId, status, modifiedSince). Cache TTL probably shorter (5-10 min) since bookings mutate. |
| 2 | `/proxy/beds24/messages` | Second most asked-for ("what did guest X say last?"). | 1.5-2h | Requires `bookingId` param. Cache very short (1 min) since chat is real-time. Need to think about PII redaction policy — current bot pulls raw, but a proxy exposed broader. |
| 3 | `/proxy/beds24/reviews` | Already shipped via `reviews-sync.ts` writing to D1 — proxy version could be **D1 read** rather than live Beds24 to save quota. | 1h (D1 read) or 2h (live Beds24 fallback) | Decide D1 vs live; D1 is fine for most WC needs. |
| 4 | `/proxy/beds24/properties` | Static-ish reference data (property names, roomIds, max occupancy). Cache 24h. | 1h | Phase 1 already hardcodes `ACTIVE_ROOMS`; this endpoint could surface that map + Beds24 metadata. |

Each endpoint requires its **own spec thread** (per thread/134 §11 "Do NOT
add other endpoints inline"). Recommend WC writes thread/136 (bookings)
when ready.

---

## Out-of-scope findings (logged, NOT fixed inline)

1. **`audit_log` table doesn't exist in D1 prod.** Anticipated by thread/134
   §7 R4. Resolved by adding migration `0039_audit_log.sql` in this PR
   (table is generic enough for future audit needs, not just proxy). Audit
   insert in handler is wrapped in `try/catch`, so the proxy works even
   if migration is somehow not applied.

2. **`apps/worker-bot/README.md` did not exist before this PR.** Spec said
   "append section" but file was missing; created from scratch with proxy
   docs as the seed content. Future work in `worker-bot` can grow this
   README (existing other patterns — debounce, ManyChat webhook flow,
   admin endpoints — could be documented later).

3. **CORS is open (`Access-Control-Allow-Origin: *`).** Acceptable per
   thread/134 §2 for read-only Phase 1. Phase 4 should lock down to
   specific Claude project origins once those are known.

4. **`temp-mcp-config` branch surfaced during pre-flight.** A parallel
   session (thread/127 A5) committed `.mcp.json` (chrome-devtools-mcp
   config) on its own branch. No collision with thread/134 work — `.mcp.json`
   is correctly untracked from `feat/beds24-proxy-calendar` and was never
   staged into this PR.

5. **Beds24 calendar `from`/`to` ranges.** `cron.ts refreshCalendar` expands
   Beds24's range cells into per-day entries. The proxy follows spec §4.5
   literally and emits one date per cell (`cell.from`). If Beds24 ever
   returns multi-day ranges, the proxy under-reports per-day data.
   Recommend Phase 2 PR adds range expansion if observed in real traffic.

6. **No worker-bot deploy in GH Actions.** `deploy.yml` deploys `apps/web`
   only (Cloudflare Pages). Worker-bot deploys are manual via
   `pnpm wrangler deploy` — already part of Alex's checklist. Phase 4
   could add a worker-bot deploy workflow gated on protected branch.

---

## Working notes for future CC sessions

- **Constant-time bearer compare**: the spec showed a simple XOR-accumulator
  pattern. That's what shipped. If you're tempted to use `crypto.subtle`,
  note that for short fixed-length tokens (64 hex chars) the XOR loop is
  perfectly adequate and avoids an extra await per request.
- **`noUncheckedIndexedAccess: true`** in `tsconfig.json` means
  `aBytes[i] ^ bBytes[i]` returns `number | undefined`. The shipped code
  uses `(aBytes[i] ?? 0) ^ (bBytes[i] ?? 0)` to satisfy TS.
- **D1 mock shape** for handler tests: tests stub `prepare(...).bind(...).run()`
  inline rather than using the more elaborate `BotAlertsEnv` mock from
  `cron-bot-alerts.test.ts`. Keep it minimal — the handler only does one
  INSERT, no SELECTs.

CC out.

🚀 Phase 1 done in 1h. Ready for Alex to wire secrets + DNS and ship.
