# Thread 134 · WC handoff CC · Beds24 read-only proxy spec

**From:** WC
**To:** CC-Bot
**Date:** 2026-05-19
**Type:** DoIt handoff · brain deep spec
**Mode:** Full autonomous · CC ejecuta sin permiso step-by-step
**Order:** Independent · puede ejecutarse paralelo con thread/127, /131
**Output thread:** thread/135

---

## TLDR

Construir un **proxy read-only para Beds24 v2 API** en `worker-bot` que múltiples clientes Claude pueden consumir vía bearer token, sin necesidad de tokens Beds24 ni acceso al refresh flow.

**Clientes objetivo:** WC web (Claude.ai chat), CC autonomous (CLI), other Claude apps (mobile/desktop), tools externos.

**Phase 1**: `/proxy/beds24/calendar` (este DoIt)
**Phase 2-3**: bookings, messages, reviews, properties (future threads, NO en scope ahora)

**Estimated CC effort**: 4-6h autonomous.

---

## 1 · Context

### Use case

Alex quiere que sesiones Claude consuman datos Beds24 (calendar, availability, prices, etc.) **sin handle Beds24 auth/refresh tokens/rate limits/refresh tokens manualmente**.

Hoy:
- `worker-bot/src/beds24-auth.ts` maneja auth + token refresh
- Múltiples scripts/endpoints internos llaman Beds24 v2 via `getBeds24AccessToken()`
- Pero **NO hay endpoint público para consultar datos**

Lo que queremos: bearer-token-gated HTTP API que:
1. Reuse el auth machinery existente
2. Cache agresivo via KV (Beds24 rate-limited)
3. Whitelist explícito de endpoints (no open proxy)
4. Clean response schema (vs raw Beds24)
5. Audit log per request
6. CORS-enabled (para browser Claude clients)

### Use cases servidos (confirmed Alex 2026-05-19)

| Client | Cómo consume |
|---|---|
| **WC web** (Claude.ai chat) | Project knowledge tiene base URL + bearer token, WC usa `web_fetch` |
| **CC autonomous** (CLI) | `.dev.vars` o environment variable con bearer token |
| **Other Claude apps** (mobile, desktop) | Project knowledge igual que WC web |
| **External tools** | Bearer token compartido con tools tuyos |

Bearer token único compartido (Phase 1). Multi-token + audit per-client viene en Phase 4 (future).

### Why now

- Q5 reviews-sync/calendar/availability ya están en D1/R2 vía crons internos. Pero esos son **historic/cached snapshots**, no live.
- Algunas operations WC requieren live data: "¿está disponible RdM del 20 al 25 de diciembre?"
- Hoy WC tendría que pedirme yo manually hit Beds24 → spec → CC ejecuta. Slow loop.
- Proxy permite WC self-serve.

---

## 2 · Decisions (closed, per Alex 2026-05-19)

| Decision | Value |
|---|---|
| Q1 · Reuse vs new worker | **A · Reuse worker-bot** — add new routes, no separate worker |
| Q2 · Auth | **A · Bearer token shared** — single secret `BEDS24_PROXY_TOKEN` for Phase 1 |
| Q3 · Cache | **KV per endpoint** with explicit TTLs |
| Q4 · Schema | **B · Cleaned** default + `?raw=true` for raw Beds24 passthrough |
| Q5 · Surface | **Whitelist** — each endpoint requires code, no open proxy |
| Q6 · Hosting | **B · Subdomain dedicated** — `beds24.rincondelmar.club` CNAME to worker-bot custom domain |
| Multi-client support | Single bearer token Phase 1, multi-token Phase 4 |
| CORS | Enabled with `Access-Control-Allow-Origin: *` for read-only Phase 1 |
| Output format | JSON only |
| Rate limit handling | Bubble Beds24's 429 to caller with retry-after header |
| Logging | audit_log entries `kind='beds24_proxy_read'` |
| Phase 1 endpoint | `/proxy/beds24/calendar` only |

---

## 3 · Explicit scope

### ✅ YES — en scope (Phase 1)

1. New Worker route `app.get('/proxy/beds24/calendar', handler)` en worker-bot
2. Bearer token auth via `Authorization: Bearer <token>` header
3. New secret `BEDS24_PROXY_TOKEN` en worker-bot
4. KV cache via existing `KV_KNOWLEDGE` binding, key namespace `proxy:calendar:*`
5. Cache TTL 30 min con `?fresh=true` query param para bypass
6. Reuse `beds24-auth.ts` para acceso Beds24
7. Clean response schema (per §4 below)
8. Optional `?raw=true` para passthrough debug
9. CORS preflight + headers
10. Audit log entry per request
11. DNS setup: `beds24.rincondelmar.club` CNAME a custom domain del worker-bot
12. Tests con vitest + happy-dom (auth, params validation, cache hit/miss, error paths)
13. Documentation en `apps/worker-bot/README.md` para futuras additions de endpoint

### ❌ NO — out of scope (Phase 2+)

- NO `/proxy/beds24/bookings` (Phase 2)
- NO `/proxy/beds24/messages` (Phase 2)
- NO `/proxy/beds24/reviews` (Phase 3)
- NO `/proxy/beds24/properties` (Phase 3)
- NO write endpoints (NUNCA — proxy is read-only by design)
- NO multi-token + per-client audit (Phase 4)
- NO rate limiting per-client (Phase 4)
- NO documentation / OpenAPI schema en sitio público (Phase 4)
- NO dashboard de uso analytics (Phase 4)
- NO automatic Beds24 schema evolution detection (Phase 4)

Si encuentras un endpoint Beds24 útil fuera de scope: log a thread/135, NO add inline.

---

## 4 · Implementation

### 4.1 Schema clean output

Beds24 raw response (per `apps/worker-bot/src/welcome-kb.ts` referencias):

```jsonc
// Beds24 /v2/inventory/rooms/calendar response
{
  "data": [
    {
      "roomId": 78695,
      "calendar": [
        { "from": "2026-12-20", "to": "2026-12-20", "numAvail": 1, "price1": 5500, "minStay": 2 },
        // ...
      ]
    }
  ]
}
```

**Clean schema target**:

```jsonc
// GET /proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25
{
  "ok": true,
  "cached": true,
  "cache_age_seconds": 1234,
  "rooms": [
    {
      "room_id": 78695,
      "room_name": "Rincón del Mar",          // resolved from roomId mapping
      "dates": [
        {
          "date": "2026-12-20",
          "available": true,
          "price_mxn": 5500,
          "min_stay": 2
        },
        // ...
      ]
    }
  ],
  "meta": {
    "queried_at": "2026-05-19T16:30:00Z",
    "beds24_endpoint": "/v2/inventory/rooms/calendar",
    "rate_limit_remaining": 295    // bubble from Beds24 headers if present
  }
}
```

**Per `?raw=true`**: pass-through del raw Beds24 response en `data` field, sin clean.

### 4.2 Room ID → name mapping

Hardcoded en proxy (reuse de patrón existente en `reviews-sync.ts`):

```ts
const ACTIVE_ROOMS: Record<number, string> = {
  78695: 'Rincón del Mar',
  374482: 'Las Morenas (direct)',
  74322: 'Las Morenas (Airbnb)',
  637063: 'Huerta Cocotera',
  74316: 'Combinada',
  // 679176 Casa Chamán — NOT included in proxy until Q3 2026 (anti-pattern memory #3)
};
```

Si `roomId` no en map → response includes warning pero NO bloquea (puede ser nuevo listing).

### 4.3 Request validation

| Param | Type | Required | Validation |
|---|---|---|---|
| `roomId` | int | YES | Must be in ACTIVE_ROOMS map OR `all` to query all rooms |
| `startDate` | ISO date `YYYY-MM-DD` | YES | Must be valid, not in past beyond 30 days |
| `endDate` | ISO date `YYYY-MM-DD` | YES | Must be >= startDate, max 365 days from startDate |
| `fresh` | bool | NO | `true` bypasses cache |
| `raw` | bool | NO | `true` returns raw Beds24 passthrough |

**Auth**:
- Header `Authorization: Bearer <BEDS24_PROXY_TOKEN>`
- Constant-time comparison via `crypto.subtle` or string compare slow path
- Missing/wrong → 401 `{ ok: false, error: 'unauthorized' }`

**Errors**:
- 400 `invalid_room_id` | `invalid_date_format` | `date_range_too_large` | `start_after_end`
- 401 `unauthorized`
- 502 `beds24_error` (with code passthrough)
- 429 `rate_limited` (bubble Beds24's retry-after)
- 500 `internal_error`

### 4.4 Cache strategy

| Aspect | Value |
|---|---|
| KV binding | `KV_KNOWLEDGE` (existing) |
| Key pattern | `proxy:calendar:{roomId}:{startDate}:{endDate}` |
| TTL | 1800 seconds (30 min) |
| Bypass | `?fresh=true` query param |
| Cache value | Clean schema response (JSON stringified) |
| Cache headers | `X-Cache-Hit: true/false`, `X-Cache-Age: <seconds>` |

**Don't cache 4xx/5xx errors**, solo 200 successful responses.

### 4.5 Handler skeleton (TypeScript)

```ts
// apps/worker-bot/src/proxy-beds24.ts
import type { Context } from 'hono';
import { getBeds24AccessToken } from './beds24-auth';

interface ProxyEnv {
  KV_KNOWLEDGE: KVNamespace;
  BEDS24_PROXY_TOKEN: string;
  BEDS24_TOKEN?: string;
  BEDS24_REFRESH_TOKEN?: string;
  DB: D1Database;
}

const ACTIVE_ROOMS: Record<number, string> = {
  78695: 'Rincón del Mar',
  374482: 'Las Morenas (direct)',
  74322: 'Las Morenas (Airbnb)',
  637063: 'Huerta Cocotera',
  74316: 'Combinada',
};

const CACHE_TTL_SECONDS = 1800; // 30 min
const MAX_DATE_RANGE_DAYS = 365;

export async function handleProxyCalendar(c: Context<{ Bindings: ProxyEnv }>) {
  // 1. Auth
  const auth = c.req.header('Authorization');
  if (!auth?.startsWith('Bearer ')) {
    return c.json({ ok: false, error: 'unauthorized' }, 401);
  }
  const token = auth.slice(7);
  if (!c.env.BEDS24_PROXY_TOKEN) {
    return c.json({ ok: false, error: 'proxy_token_not_configured' }, 503);
  }
  // Constant-time compare via crypto
  const expected = new TextEncoder().encode(c.env.BEDS24_PROXY_TOKEN);
  const got = new TextEncoder().encode(token);
  if (expected.length !== got.length) {
    return c.json({ ok: false, error: 'unauthorized' }, 401);
  }
  let mismatch = 0;
  for (let i = 0; i < expected.length; i++) mismatch |= expected[i] ^ got[i];
  if (mismatch !== 0) {
    return c.json({ ok: false, error: 'unauthorized' }, 401);
  }

  // 2. Parse + validate params
  const roomIdParam = c.req.query('roomId');
  const startDate = c.req.query('startDate');
  const endDate = c.req.query('endDate');
  const fresh = c.req.query('fresh') === 'true';
  const raw = c.req.query('raw') === 'true';

  if (!roomIdParam || !startDate || !endDate) {
    return c.json({ ok: false, error: 'missing_params', required: ['roomId', 'startDate', 'endDate'] }, 400);
  }

  // Validate roomId
  let roomIds: number[];
  if (roomIdParam === 'all') {
    roomIds = Object.keys(ACTIVE_ROOMS).map(Number);
  } else {
    const rid = Number.parseInt(roomIdParam, 10);
    if (!Number.isFinite(rid) || !(rid in ACTIVE_ROOMS)) {
      return c.json({ ok: false, error: 'invalid_room_id', valid: Object.keys(ACTIVE_ROOMS) }, 400);
    }
    roomIds = [rid];
  }

  // Validate dates (ISO YYYY-MM-DD)
  const dateRe = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRe.test(startDate) || !dateRe.test(endDate)) {
    return c.json({ ok: false, error: 'invalid_date_format', format: 'YYYY-MM-DD' }, 400);
  }
  if (startDate > endDate) {
    return c.json({ ok: false, error: 'start_after_end' }, 400);
  }
  const startMs = new Date(startDate + 'T00:00:00Z').getTime();
  const endMs = new Date(endDate + 'T00:00:00Z').getTime();
  const rangeDays = (endMs - startMs) / (1000 * 60 * 60 * 24);
  if (rangeDays > MAX_DATE_RANGE_DAYS) {
    return c.json({ ok: false, error: 'date_range_too_large', max_days: MAX_DATE_RANGE_DAYS }, 400);
  }

  // 3. Cache lookup (unless fresh)
  const cacheKey = `proxy:calendar:${roomIds.join(',')}:${startDate}:${endDate}`;
  if (!fresh && !raw) {
    const cached = await c.env.KV_KNOWLEDGE.get(cacheKey, 'json') as any;
    if (cached) {
      const ageSec = Math.floor((Date.now() - cached.queried_at_ms) / 1000);
      if (ageSec < CACHE_TTL_SECONDS) {
        c.header('X-Cache-Hit', 'true');
        c.header('X-Cache-Age', String(ageSec));
        return c.json({ ...cached.body, cached: true, cache_age_seconds: ageSec });
      }
    }
  }

  // 4. Beds24 API call
  let accessToken: string;
  try {
    accessToken = await getBeds24AccessToken(c.env);
  } catch (err) {
    return c.json({ ok: false, error: 'beds24_auth_failed', detail: String(err) }, 502);
  }

  const url = new URL('https://api.beds24.com/v2/inventory/rooms/calendar');
  url.searchParams.set('roomId', roomIds.join(','));
  url.searchParams.set('startDate', startDate);
  url.searchParams.set('endDate', endDate);
  url.searchParams.set('includePrices', 'true');
  url.searchParams.set('includeNumAvail', 'true');
  url.searchParams.set('includeMinStay', 'true');

  let res: Response;
  try {
    res = await fetch(url.toString(), {
      headers: { token: accessToken, accept: 'application/json' },
    });
  } catch (err) {
    return c.json({ ok: false, error: 'beds24_fetch_failed', detail: String(err) }, 502);
  }

  if (res.status === 429) {
    const retryAfter = res.headers.get('Retry-After');
    if (retryAfter) c.header('Retry-After', retryAfter);
    return c.json({ ok: false, error: 'rate_limited', retry_after: retryAfter }, 429);
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    return c.json({
      ok: false,
      error: 'beds24_error',
      status: res.status,
      detail: body.slice(0, 500),
    }, 502);
  }

  const beds24Json = await res.json();

  // 5. Audit log
  try {
    await c.env.DB.prepare(`
      INSERT INTO audit_log (kind, payload_json, created_at)
      VALUES (?, ?, ?)
    `).bind(
      'beds24_proxy_read',
      JSON.stringify({
        endpoint: 'calendar',
        roomIds,
        startDate,
        endDate,
        fresh,
        raw,
        beds24_status: res.status,
      }),
      Math.floor(Date.now() / 1000),
    ).run();
  } catch (err) {
    // Audit log fail = log internally but don't block response
    console.error('audit_log insert failed', err);
  }

  // 6. Raw passthrough mode
  if (raw) {
    c.header('X-Cache-Hit', 'false');
    return c.json({ ok: true, raw: true, data: beds24Json });
  }

  // 7. Clean schema transform
  const cleaned = cleanCalendarResponse(beds24Json, roomIds, ACTIVE_ROOMS);
  const responseBody = {
    ok: true,
    cached: false,
    cache_age_seconds: 0,
    rooms: cleaned,
    meta: {
      queried_at: new Date().toISOString(),
      beds24_endpoint: '/v2/inventory/rooms/calendar',
      rate_limit_remaining: res.headers.get('X-RateLimit-Remaining') ?? null,
    },
  };

  // 8. Cache write (only if 200)
  if (!fresh) {
    await c.env.KV_KNOWLEDGE.put(
      cacheKey,
      JSON.stringify({ queried_at_ms: Date.now(), body: responseBody }),
      { expirationTtl: CACHE_TTL_SECONDS },
    );
  }

  c.header('X-Cache-Hit', 'false');
  return c.json(responseBody);
}

function cleanCalendarResponse(
  beds24: any,
  roomIds: number[],
  roomMap: Record<number, string>,
): Array<{ room_id: number; room_name: string; dates: any[] }> {
  const data = beds24.data ?? [];
  return data.map((room: any) => ({
    room_id: room.roomId,
    room_name: roomMap[room.roomId] ?? `Room ${room.roomId} (unknown)`,
    dates: (room.calendar ?? []).map((cell: any) => ({
      date: cell.from,
      available: (cell.numAvail ?? 0) > 0,
      price_mxn: cell.price1 ?? null,
      min_stay: cell.minStay ?? null,
    })),
  }));
}
```

### 4.6 Route registration

En `apps/worker-bot/src/index.ts`:

```ts
import { handleProxyCalendar } from './proxy-beds24';

// CORS preflight para todos los /proxy/* paths
app.options('/proxy/beds24/*', (c) => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Authorization, Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
});

// Add CORS headers to all /proxy/* responses
app.use('/proxy/beds24/*', async (c, next) => {
  await next();
  c.header('Access-Control-Allow-Origin', '*');
  c.header('Access-Control-Expose-Headers', 'X-Cache-Hit, X-Cache-Age, Retry-After');
});

// The route
app.get('/proxy/beds24/calendar', handleProxyCalendar);
```

### 4.7 Secret generation

```bash
# Generate token (do this LOCALLY, NOT in commit)
openssl rand -hex 32
# Output: e.g. 'a7f3...' (64 hex chars = 256 bit)

# Set as Worker secret
cd apps/worker-bot
pnpm wrangler secret put BEDS24_PROXY_TOKEN
# Paste the token

# Verify
pnpm wrangler secret list | grep BEDS24_PROXY_TOKEN
# Should show key (not value)
```

### 4.8 DNS + custom domain

`beds24.rincondelmar.club` debe apuntar a worker-bot:

| Step | Acción | Quien |
|---|---|---|
| 1 | CF Dashboard → Workers & Pages → rdm-bot → Settings → Triggers → Custom Domains | Alex (2 min) |
| 2 | Add Custom Domain: `beds24.rincondelmar.club` | Alex |
| 3 | CF auto-creates CNAME en zone rincondelmar.club | Auto |
| 4 | Wait for propagation (~30 sec) | — |
| 5 | Test: `curl https://beds24.rincondelmar.club/health` should hit worker | CC |

Note: Worker name probable es `rdm-bot` o `rincondelmar-bot` — verify via `pnpm wrangler whoami` o dashboard.

### 4.9 Project knowledge integration

Después de deploy + DNS, Alex agrega a project knowledge de cada Claude project relevante:

```markdown
## Beds24 Proxy Access

Base URL: https://beds24.rincondelmar.club/proxy/beds24/

Authentication: Bearer token (ask Alex for BEDS24_PROXY_TOKEN value)

Available endpoints:
- GET /calendar?roomId={id}&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
  - roomId: 78695 (RdM) | 374482 (Morenas direct) | 74322 (Morenas Airbnb)
           | 637063 (Huerta) | 74316 (Combinada) | 'all'
  - Optional: ?fresh=true (bypass cache), ?raw=true (raw Beds24 passthrough)
  - Returns: available + price + min_stay per date

Usage from WC web (via web_fetch):
  fetch("https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25", {
    headers: { "Authorization": "Bearer <TOKEN>" }
  })

Cache TTL: 30 minutes.
Rate limits: bubble from Beds24 (typically 5 req/sec).
```

---

## 5 · Tests

### 5.1 Auth tests

| Test | Expected |
|---|---|
| No Authorization header | 401 |
| Wrong bearer prefix (`Token X` instead of `Bearer X`) | 401 |
| Token mismatch | 401 |
| Valid token + valid params | 200 |
| BEDS24_PROXY_TOKEN not configured | 503 |

### 5.2 Params validation

| Test | Expected |
|---|---|
| Missing roomId | 400 `missing_params` |
| Invalid roomId (not in map, not 'all') | 400 `invalid_room_id` |
| Invalid date format (`2026/12/20`) | 400 `invalid_date_format` |
| startDate > endDate | 400 `start_after_end` |
| Date range > 365 days | 400 `date_range_too_large` |

### 5.3 Cache behavior

| Test | Expected |
|---|---|
| First call (cache miss) | X-Cache-Hit: false |
| Second call same params | X-Cache-Hit: true, X-Cache-Age > 0 |
| Call with ?fresh=true | X-Cache-Hit: false (bypass) |
| Call with ?raw=true | NOT cached (force fresh) |
| Cache entry > 30 min old | treated as miss |

### 5.4 Beds24 integration

| Test | Expected |
|---|---|
| Beds24 returns 429 | proxy returns 429 with Retry-After |
| Beds24 returns 500 | proxy returns 502 `beds24_error` |
| Beds24 returns malformed JSON | proxy returns 502 |
| getBeds24AccessToken throws | proxy returns 502 `beds24_auth_failed` |

### 5.5 Schema transform

| Test | Expected |
|---|---|
| Raw response has `data: [{roomId, calendar}]` | clean response has `rooms: [{room_id, room_name, dates}]` |
| Unknown roomId in response | `room_name: 'Room X (unknown)'` |
| numAvail = 0 | `available: false` |
| numAvail = 1 | `available: true` |
| Missing minStay | `min_stay: null` |

### 5.6 CORS

| Test | Expected |
|---|---|
| OPTIONS /proxy/beds24/calendar | 204 + CORS headers |
| GET con Origin header | CORS headers in response |

---

## 6 · Definition of done

- [ ] New file `apps/worker-bot/src/proxy-beds24.ts` with handler
- [ ] Route registered in `apps/worker-bot/src/index.ts`
- [ ] CORS middleware applied
- [ ] Secret `BEDS24_PROXY_TOKEN` set via wrangler (Alex does this)
- [ ] DNS custom domain `beds24.rincondelmar.club` configured (Alex does this)
- [ ] Test suite passes (vitest, ≥15 tests covering §5.1-§5.6)
- [ ] Smoke test from CC:
  - `curl -H "Authorization: Bearer <TOKEN>" "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"` returns 200
  - Second curl same params shows `X-Cache-Hit: true`
- [ ] `apps/worker-bot/README.md` documents proxy section
- [ ] Project knowledge snippet ready para Alex (in thread/135 report)
- [ ] audit_log entries visible in D1 post-test
- [ ] thread/135 posted with completion report

---

## 7 · Risks + mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | Token leak via project knowledge | Bearer token rotable via `wrangler secret put`. Audit log catches abuse. Phase 4 adds per-client tokens. |
| R2 | Beds24 rate limit (5/sec) exhausted by Claude clients | KV cache 30 min reduces calls dramatically. Bubble 429 to caller. Monitor X-RateLimit headers. |
| R3 | Cache stale data | TTL 30 min reasonable for calendar. `?fresh=true` escape hatch. |
| R4 | audit_log table doesn't exist or schema differs | Verify in Phase 1 of execution. If missing, defer audit + open issue separate. |
| R5 | CORS too permissive (`*`) | Acceptable for read-only Phase 1. Phase 4 lock to specific origins. |
| R6 | Worker custom domain not available / DNS issue | Test setup first. If fails, fallback `<worker-name>.<account>.workers.dev` URL acceptable for Phase 1. |
| R7 | KV namespace eviction during stress | TTL = 30 min, low risk. Worst case: extra Beds24 call. |
| R8 | Beds24 schema change breaks clean transform | Tests catch via fixtures. `?raw=true` always works as escape hatch. |
| R9 | Worker deploy adds load to existing worker-bot | Read-only, cached aggressively. Estimated +10 req/min max. Negligible. |
| R10 | Casa Chamán roomId (679176) leaks in error msg if Alex tests with it | NOT in ACTIVE_ROOMS map. Returns 400 `invalid_room_id` with valid list. Anti-pattern memory #3 protected. |

---

## 8 · Pre-flight checklist

```bash
# Step 1 — sync rdm-discussion
cd <rdm-discussion>
git pull origin main
ls threads/134*.md

# Step 2 — sync rdm-bot
cd <rdm-bot>
git fetch origin
git log origin/main --oneline -3
# main should be current

# Step 3 — verify Beds24 auth machinery exists
ls apps/worker-bot/src/beds24-auth.ts
grep -n "getBeds24AccessToken" apps/worker-bot/src/beds24-auth.ts

# Step 4 — verify KV_KNOWLEDGE binding exists
grep -n "KV_KNOWLEDGE" apps/worker-bot/wrangler.toml

# Step 5 — verify audit_log table exists
wrangler d1 execute rincon --remote --command "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log';"

# Step 6 — verify Hono setup
grep -n "import.*Hono\|new Hono" apps/worker-bot/src/index.ts

# Step 7 — verify wrangler is current version
pnpm wrangler --version
```

If any pre-flight fails → halt + Telegram Alex.

---

## 9 · Execution phases

### Phase A · Verify ground truth (15 min)

1. Read `apps/worker-bot/src/beds24-auth.ts` end-to-end
2. Read `apps/worker-bot/src/welcome-kb.ts` to understand Beds24 calendar API usage pattern
3. Verify `audit_log` schema:
   ```bash
   wrangler d1 execute rincon --remote --command "PRAGMA table_info(audit_log);"
   ```
4. Check existing similar endpoints (e.g., `/admin/sync-reviews`) for auth pattern reference
5. Verify Wrangler can deploy worker (no `wrangler.toml` issues)

### Phase B · Implement handler (1.5-2h)

1. Create `apps/worker-bot/src/proxy-beds24.ts` per §4.5
2. Add ACTIVE_ROOMS map per §4.2
3. Implement cleanCalendarResponse per §4.5

### Phase C · Wire route + CORS (15 min)

Register route in `apps/worker-bot/src/index.ts` per §4.6.

### Phase D · Tests (1-1.5h)

Create `apps/worker-bot/tests/proxy-beds24.test.ts` covering §5.1-§5.6.

Run: `pnpm vitest apps/worker-bot/tests/proxy-beds24.test.ts`

### Phase E · Deploy + DNS coordination (Alex 5 min + CC 15 min)

1. CC: commit + push to feature branch
2. CC: open PR with description summarizing what changed
3. Alex: review PR
4. Alex: generate token (`openssl rand -hex 32`) + set via `wrangler secret put BEDS24_PROXY_TOKEN`
5. Alex: configure custom domain `beds24.rincondelmar.club` in CF Dashboard
6. Alex: merge PR + deploy.yml ships to prod
7. CC: smoke test via curl

### Phase F · Smoke test (10 min)

```bash
# Health check
curl -i https://beds24.rincondelmar.club/health 2>&1 | head -5
# Expected: 200 (existing worker-bot health endpoint)

# Auth check (should 401)
curl -i "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"
# Expected: 401 unauthorized

# Authed check (should 200)
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"
# Expected: 200 + JSON + X-Cache-Hit: false

# Cache check (should be cache hit)
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=78695&startDate=2026-12-20&endDate=2026-12-25"
# Expected: 200 + X-Cache-Hit: true

# Invalid room
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=99999&startDate=2026-12-20&endDate=2026-12-25"
# Expected: 400 invalid_room_id

# Casa Chamán block test (anti-pattern)
curl -i -H "Authorization: Bearer $BEDS24_PROXY_TOKEN" \
  "https://beds24.rincondelmar.club/proxy/beds24/calendar?roomId=679176&startDate=2026-12-20&endDate=2026-12-25"
# Expected: 400 invalid_room_id (Chamán not in ACTIVE_ROOMS map per memory #3)
```

### Phase G · Docs + project knowledge snippet (15 min)

1. Update `apps/worker-bot/README.md`:
   - Section "Beds24 Proxy" with auth pattern + endpoint table
2. Write thread/135 with:
   - Phase A-F results
   - Project knowledge snippet for Alex
   - Suggested next endpoints (Phase 2 backlog)

---

## 10 · Communication

| Trigger | Mensaje |
|---|---|
| Pre-flight done, starting Phase A | "thread/134 Beds24 proxy starting. ETA 4-6h." |
| Phase B complete (handler implemented) | "Handler done. Tests next." |
| Phase D complete (tests passing) | "Tests green. PR ready. Need Alex for secret + DNS." |
| Phase E blocked | "Blocked on Alex: BEDS24_PROXY_TOKEN secret + DNS custom domain. See PR description." |
| Phase F smoke passes | "Smoke green. Project knowledge snippet in thread/135." |
| Halt | "thread/134 halted at Phase X. Reason: Y." |
| Complete | "Proxy live at beds24.rincondelmar.club/proxy/beds24/calendar. thread/135 posted." |

---

## 11 · Working notes

- **Stuck > 30 min**: halt + Telegram Alex
- **Out of scope**: log a thread/135, NO fixees inline
- **Self-review**: lee tu propio diff antes de commit. Verifica: no token plaintext, no Casa Chamán roomId, audit_log doesn't block response
- **Time budget**: 4-6h. Si excedes 1.5x (9h), stop + report
- **Coordination con Alex**: Phase E requires Alex action (secret + DNS). CC pushes PR, espera.
- **Do NOT add other endpoints inline**. Each future endpoint (bookings, messages, reviews, properties) is separate spec thread.

---

## 12 · Future phases (NOT in this DoIt)

Per thread/132 + memory #11 noting Beds24 Reviews already shipped:

| Phase | Endpoint | Reuse |
|---|---|---|
| Phase 2 | `/proxy/beds24/bookings` | Pattern from Phase 1, schema different |
| Phase 2 | `/proxy/beds24/messages` | Pattern from Phase 1, requires bookingId param |
| Phase 3 | `/proxy/beds24/reviews` | Reuses existing reviews-sync.ts logic (D1 read or live fetch?) |
| Phase 3 | `/proxy/beds24/properties` | Static-ish, cache 24h |
| Phase 4 | Multi-token + audit per-client | Token table in D1, per-token rate limits |
| Phase 4 | OpenAPI schema endpoint | `GET /proxy/beds24/openapi.json` |
| Phase 4 | Dashboard `/admin/proxy-usage` | Read audit_log |

Each future phase is **separate thread + brain deep**.

---

## 13 · Comando para arrancar

```
Pre-flight:
1. git pull origin main en rdm-discussion (verifica thread/134 existe)
2. git pull origin main en rdm-bot
3. ls apps/worker-bot/src/beds24-auth.ts (must exist)
4. wrangler d1 execute rincon --remote --command "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log';" (must return row)

Lee:
- threads/134-wc-cc-beds24-proxy-readonly-doit.md (este)
- apps/worker-bot/src/beds24-auth.ts (auth pattern reuse)
- apps/worker-bot/src/welcome-kb.ts (Beds24 calendar usage example)

Ejecuta thread/134 phases A-G sequential.

Time budget: 4-6h. Excedo 1.5x (9h) = stop + Telegram.
Coordinación: Phase E requires Alex (secret + DNS). PR + wait.
Output: thread/135 con report + project knowledge snippet.
```

---

WC out.

🚀 Esta proxy desbloquea self-serve queries Beds24 desde WC chat + CC autonomous + future Claude apps. Phase 1 calendar es el primero — pattern reusable para 4-5 endpoints más en próximos sprints.
