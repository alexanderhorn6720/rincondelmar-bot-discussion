# 103 — WC: DoIt — Beds24 API backfill (pre-webhook bookings)

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: Bookings created before webhook activation missing from D1
**Mode**: DoIt
**Status**: 🟢 Ready after thread/101 completes
**Estimated effort**: 3-4h CC

---

## TL;DR

Alex tested `/admin/bookings` and noticed direct bookings missing. Investigation (WC via D1 MCP): booking 79421553 (Jovany Granados, check-in 25 may 2026, 15 adultos) exists in Beds24 panel but NOT in our `beds24_bookings` table.

**Root cause**: webhook activation date ~mayo 2026 (Q15 thread 2026-05-12). Any booking created BEFORE webhook activation never reached `beds24_events`. Backfill via `GET /v2/bookings` is the fix.

This task does that backfill — idempotent, safe to rerun.

---

## §1 — Problem evidence

### What WC found via D1 MCP

```sql
-- beds24_events earliest arrival date
SELECT MIN(arrival) FROM beds24_events;
-- → 2026-05-07

-- referer breakdown
SELECT referer, status, COUNT(*) FROM beds24_events GROUP BY referer, status;
-- Airbnb / inquiry    → 66
-- Airbnb / confirmed  → 56
-- API / cancelled     → 7
-- AlexanderHorn / confirmed → 2  (BUT both are SAME booking id 86685323, arrival 2027-07-22)

-- Search for Jovany booking 79421553
SELECT * FROM beds24_bookings WHERE beds24_booking_id = 79421553;  -- empty
SELECT * FROM beds24_events WHERE beds24_booking_id = 79421553;    -- empty
```

### Beds24 panel evidence (Alex screenshot)

- Booking ID: 79421553
- Habitación: Rincón Mar (78695)
- Check In: 25 mayo 2026
- Salida: 28 mayo 2026
- Adultos: 15
- Estado: Confirmado
- Agente o Agencia: AlexanderHorn
- Fecha de Reserva: **mié 10 dic 2025 14:25** ← created BEFORE webhook active

### Conclusion

Webhook only fires on NEW bookings post-activation. Beds24 didn't replay history. Pre-webhook bookings need active pull from API.

---

## §2 — Channel definition (clarify confusion)

Per `apps/worker-bot/src/beds24-normalize.ts` line 91, `normalizeChannel()`:

```typescript
function normalizeChannel(channel, referer) {
  const candidates = [channel, referer].filter(Boolean);
  for (const c of candidates) {
    const lower = c.toLowerCase();
    if (lower.includes('airbnb')) return 'airbnb';
    if (lower.includes('booking')) return 'booking_com';
    if (lower.includes('whatsapp')) return 'whatsapp_direct';
    if (lower.includes('web') || lower.includes('rincondelmar.club')) return 'web';
    if (lower.includes('direct')) return 'direct';
  }
  return 'direct';  // default
}
```

**Allowed channels** (per migration 0016 CHECK constraint):
- `airbnb`
- `booking_com`
- `direct` ← bookings created from panel by Alex/Karina (referer="AlexanderHorn")
- `web` ← bookings via rincondelmar.club booking engine
- `whatsapp_direct` ← bookings created via WhatsApp flow

Backfill must use this same mapping for consistency.

---

## §3 — TASK

```
TASK: Backfill beds24_bookings via Beds24 API GET /v2/bookings
MODE: DoIt
Branch: feat/beds24-backfill-prewebhook

CONTEXT:
- Pre-webhook bookings missing from beds24_bookings
- Beds24 API has full history
- Pattern exists in apps/worker-bot/src/client-bot-polling.ts:85
- Auth via getBeds24AccessToken from beds24-auth.ts
- Normalize via normalizeBeds24Event from beds24-normalize.ts (refactor for idempotency)

============================================================
PRE-FLIGHT (auto-execute, halt only on actual failure)
============================================================

1. cd "$env:USERPROFILE\rdm\dev\bot"
2. git status --short  → clean (or stashed)
3. git fetch origin
4. git checkout main && git pull origin main
5. gh auth status  → logged in
6. Verify Beds24 auth works:
   - Check KV `beds24:access_token` exists OR env var BEDS24_TOKEN configured
   - Test small call: GET /v2/bookings?propertyId=31862&modifiedSince=2025-01-01&page=1
   - Expect 200 OK, JSON response with `data` array

============================================================
DELIVERABLES
============================================================

PASO 1 — Create branch
   git checkout -b feat/beds24-backfill-prewebhook

PASO 2 — Build backfill function

Create `apps/worker-bot/src/beds24-backfill.ts`:

```typescript
/**
 * One-shot backfill of beds24_bookings via Beds24 API.
 * 
 * Calls GET /v2/bookings with full date range, paginates, processes each booking
 * through normalize logic, inserts into beds24_bookings if not already present.
 * 
 * Idempotent: safe to rerun. Skips bookings already in DB.
 * 
 * Trigger: POST /admin/beds24-backfill (admin-only endpoint)
 * 
 * Usage:
 *   curl -X POST -H "Authorization: Bearer $ADMIN_REFRESH_SECRET" \
 *        https://rincondelmar.club/admin/beds24-backfill
 */

import { getBeds24AccessToken } from './beds24-auth';
// Refactor: extract reusable normalize logic from beds24-normalize.ts
// such that we can pass a full Beds24 booking object (not webhook event)
// and get back the normalized row ready for INSERT.

interface BackfillResult {
  total_fetched: number;
  total_inserted: number;
  total_skipped_existing: number;
  total_errors: number;
  errors: Array<{ booking_id: number; error: string }>;
  duration_ms: number;
}

export async function runBackfill(env: Env): Promise<BackfillResult> {
  const start = Date.now();
  const token = await getBeds24AccessToken(env);
  
  const result: BackfillResult = {
    total_fetched: 0,
    total_inserted: 0,
    total_skipped_existing: 0,
    total_errors: 0,
    errors: [],
    duration_ms: 0,
  };
  
  // Use modifiedSince far in past to capture everything
  // Beds24 paginates — handle pagination loop
  let page = 1;
  const pageSize = 100;
  
  while (true) {
    const url = `https://api.beds24.com/v2/bookings?propertyId=31862&modifiedSince=2020-01-01&includeInvoiceItems=true&page=${page}`;
    
    const res = await fetch(url, {
      headers: { token, accept: 'application/json' },
    });
    
    if (!res.ok) {
      const text = await res.text();
      console.error(`[backfill] page ${page} fetch failed: ${res.status} ${text}`);
      throw new Error(`Beds24 API error: ${res.status}`);
    }
    
    const json = await res.json() as {
      data?: Array<Record<string, unknown>>;
      pages?: number;
    };
    
    const bookings = json.data ?? [];
    if (bookings.length === 0) break;
    
    result.total_fetched += bookings.length;
    
    for (const booking of bookings) {
      const beds24BookingId = booking.id as number;
      
      try {
        // Check if already in DB
        const existing = await env.DB.prepare(
          'SELECT id FROM beds24_bookings WHERE beds24_booking_id = ?'
        ).bind(beds24BookingId).first();
        
        if (existing) {
          result.total_skipped_existing++;
          continue;
        }
        
        // Normalize via shared logic (refactored from beds24-normalize.ts)
        const normalized = normalizeBookingForInsert(booking);
        
        // INSERT
        await env.DB.prepare(`
          INSERT INTO beds24_bookings (
            beds24_booking_id, guest_id, room_id, property_id,
            channel, channel_reservation_code,
            arrival, departure, num_nights,
            num_adults, num_children, num_pets, total_guests,
            total_amount_mxn, deposit_amount_mxn, deposit_paid, balance_due_mxn, payout_amount_mxn,
            status, beds24_status, special_offers_count,
            created_at, updated_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          normalized.beds24BookingId,
          normalized.guestId,
          normalized.roomId,
          normalized.propertyId,
          normalized.channel,
          normalized.channelReservationCode,
          normalized.arrival,
          normalized.departure,
          normalized.numNights,
          normalized.numAdults,
          normalized.numChildren,
          normalized.numPets,
          normalized.totalGuests,
          normalized.totalAmountMxn,
          normalized.depositAmountMxn,
          normalized.depositPaid ? 1 : 0,
          normalized.balanceDueMxn,
          normalized.payoutAmountMxn,
          normalized.status,
          normalized.beds24Status,
          normalized.specialOffersCount,
          new Date().toISOString(),
          new Date().toISOString(),
        ).run();
        
        result.total_inserted++;
      } catch (err) {
        result.total_errors++;
        result.errors.push({
          booking_id: beds24BookingId,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
    
    // Check pagination
    const totalPages = json.pages ?? 1;
    if (page >= totalPages) break;
    page++;
    
    // Rate limit: small delay between pages
    await new Promise(r => setTimeout(r, 200));
  }
  
  result.duration_ms = Date.now() - start;
  return result;
}
```

PASO 3 — Refactor normalize for reusability

In `beds24-normalize.ts`, extract the parsing logic from `normalizeBeds24Event` into a standalone `normalizeBookingForInsert(booking)` function that takes a Beds24 booking object directly (without the webhook event wrapper).

This is the key refactor:
- Existing: `normalizeBeds24Event(event)` expects `{ payload_json: { booking: {...} } }`
- New: `normalizeBookingForInsert(booking)` expects the booking object directly
- Existing function should call new function internally to avoid duplication

PASO 4 — Add admin endpoint

In `apps/worker-bot/src/index.ts` (or wherever admin routes live):

```typescript
// POST /admin/beds24-backfill — requires ADMIN_REFRESH_SECRET
if (url.pathname === '/admin/beds24-backfill' && request.method === 'POST') {
  const auth = request.headers.get('authorization');
  if (auth !== `Bearer ${env.ADMIN_REFRESH_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }
  
  try {
    const result = await runBackfill(env);
    return Response.json(result);
  } catch (err) {
    return Response.json({
      error: err instanceof Error ? err.message : String(err),
    }, { status: 500 });
  }
}
```

PASO 5 — Tests

Create `apps/worker-bot/tests/beds24-backfill.test.ts`:

- Mock Beds24 API response
- Test pagination loop
- Test idempotency (rerun = 0 inserts, all skipped_existing)
- Test channel mapping for direct booking (referer="AlexanderHorn")
- Test error handling (one bad booking doesn't kill the run)

Reuse fixtures from `beds24-normalize.test.ts`.

PASO 6 — Verification chain

   pnpm typecheck   → 0 errors
   pnpm lint        → no new errors
   pnpm test        → all green (existing 788 + new backfill tests)
   pnpm build       → clean

PASO 7 — Commits (atomic)

   git commit -m "refactor(beds24-normalize): extract normalizeBookingForInsert helper
   
   Split parsing logic from event wrapper for reuse. Existing
   normalizeBeds24Event now calls normalizeBookingForInsert internally.
   
   Prep for backfill in next commit."
   
   git commit -m "feat(beds24): backfill endpoint for pre-webhook bookings
   
   New: apps/worker-bot/src/beds24-backfill.ts
   New: POST /admin/beds24-backfill admin endpoint
   New: tests covering pagination + idempotency + channel mapping
   
   Solves missing pre-webhook bookings (e.g. Jovany 79421553 created
   2025-12-10, before webhook activation 2026-05).
   
   Idempotent: safe to rerun. Refs: thread/103."

PASO 8 — Push + PR + merge

   git push origin feat/beds24-backfill-prewebhook
   gh pr create --title "feat(beds24): backfill endpoint for pre-webhook bookings" \
                --body "..."
   gh pr merge <N> --squash --delete-branch

PASO 9 — Deploy
CF Pages auto-deploys (web). Worker needs explicit deploy:
   wrangler deploy
(this is the `ask` tier — Y/N prompt expected)

PASO 10 — Run backfill (one-shot)

   curl -X POST -H "Authorization: Bearer $env:ADMIN_REFRESH_SECRET" \
        https://rincondelmar.club/admin/beds24-backfill
   
   Or use wrangler tail to monitor.

Expected response:
```json
{
  "total_fetched": <some number, expect 100-500>,
  "total_inserted": <some number, expect 30-100 new bookings>,
  "total_skipped_existing": <16 + others = current count>,
  "total_errors": 0,
  "errors": [],
  "duration_ms": <2000-10000>
}
```

PASO 11 — Verify backfill worked

   Query D1:
   SELECT beds24_booking_id, channel, status, arrival
   FROM beds24_bookings WHERE beds24_booking_id = 79421553;
   
Expected: 1 row, channel='direct', arrival='2026-05-25', status='booked'.

If empty: investigate (booking might have been filtered, or pagination missed it).

Also:
   SELECT channel, status, COUNT(*) FROM beds24_bookings GROUP BY channel, status;

Expected dramatic increase in direct + booking_com bookings.

PASO 12 — Browser smoke test

Open https://rincondelmar.club/admin/bookings:
- Header should show new breakdown (more direct bookings)
- Gantt should now show Jovany booking 25-28 may RdM
- Channel breakdown shows realistic numbers

============================================================
DEFAULTS
============================================================

- Commit format: Conventional Commits (refactor + feat)
- Encoding: UTF-8 file contents
- 2 atomic commits (refactor + feature)
- Squash merge with --delete-branch
- Branch: feat/beds24-backfill-prewebhook
- Deploy worker via wrangler deploy (NOT auto, requires Y/N)
- Run backfill via curl with admin secret

============================================================
OUT OF SCOPE (NO HACER)
============================================================

- ❌ Don't make backfill auto-run on cron (this is one-shot, manual trigger)
- ❌ Don't modify webhook handler (that path works fine for new bookings)
- ❌ Don't change channel enum values (use existing 'direct', 'web', etc.)
- ❌ Don't touch beds24_events table (backfill writes to beds24_bookings directly)
- ❌ Don't bulk-modify existing rows (only INSERT new, skip existing)
- ❌ Don't touch /admin/inbox build
- ❌ Don't touch welcome bug
- ❌ Don't touch rdm-platform repo
- ❌ Don't force push, don't delete branches with unmerged work

============================================================
EXTERNAL STATE (informational only)
============================================================

- Beds24 API rate limit: be respectful, 200ms between pages
- Webhook continues to work for new bookings (no conflict with backfill)
- Pagination: Beds24 returns `pages` count in response
- Auth: getBeds24AccessToken auto-refreshes if expired

Memorias relevantes:
- propertyId 31862 (RDM)
- KV `KV_KNOWLEDGE` for token cache
- ADMIN_REFRESH_SECRET configured in secrets

============================================================
CRITERIO DE ÉXITO
============================================================

- runBackfill function exists, idempotent
- POST /admin/beds24-backfill endpoint live
- pnpm test: green (existing + new backfill tests)
- 2 atomic commits, PR merged, branch deleted
- Worker deployed
- Backfill run successful (response.total_inserted > 0)
- Jovany booking 79421553 NOW visible in beds24_bookings query
- /admin/bookings UI shows expanded direct/web bookings
- No errors in run (or errors list is < 5% of total_fetched)

============================================================
SI TE ATORAS
============================================================

- Beds24 API auth fails: check env BEDS24_TOKEN or KV cache, may need manual refresh
- Beds24 API rate limit hit: increase delay between pages, retry
- Normalize function fails on certain bookings: capture in errors[], continue loop
- Booking 79421553 NOT in API response: check pagination didn't miss it, increase page size
- Schema mismatch on INSERT: review beds24_bookings columns, may need migration
- Anything unexpected: STOP, report

============================================================
REPORTAR AL FINAL (thread/104-cc-bot-beds24-backfill-complete.md)
============================================================

1. Pre-flight 6/6 pass
2. Files created/modified (paths + line counts)
3. Refactor confirmed (normalizeBeds24Event still works for webhook path)
4. Test results (typecheck/lint/test/build)
5. Commits SHA + PR # + merge SHA
6. Worker deploy result
7. Backfill execution result (full JSON response from POST /admin/beds24-backfill)
8. D1 query verifying booking 79421553 now present
9. D1 query showing new channel breakdown (before vs after)
10. Browser smoke test of /admin/bookings (confirm new bookings visible)
11. Any blockers or edge cases discovered
```

---

## §4 — What Alex does after thread/104

1. Open `/admin/bookings`
2. Verify Jovany booking 25-28 may RdM appears
3. Verify direct + web bookings increased significantly
4. Confirm Gantt now shows realistic occupancy
5. Decide next priority (P2 welcome bug | P3 inbox | other)

---

## §5 — Why this approach

### Why one-shot manual trigger vs cron?

- Backfill is historical, not ongoing. Cron creates duplicates risk.
- One-shot is auditable: explicit run, explicit response, explicit verification.
- Idempotent design = safe to rerun if needed.

### Why refactor normalize first?

- Reuse logic that already battle-tested (PR #80)
- Avoid double maintenance (webhook path + backfill path)
- Single source of truth for "how to parse Beds24 booking object"

### Why include channels beyond direct?

- We don't know what else is missing (pre-webhook Booking.com, web, etc.)
- Backfill catches everything in one go
- Channel mapping already handles all enum values correctly

### Why include invoiceItems in API call?

- Pricing data lives there
- Without it, total_amount_mxn would be wrong
- Existing normalize logic depends on invoiceItems being present

---

## §6 — Tradeoffs accepted

- **Cost**: ~3-4h CC vs immediate UI fix only
- **Risk**: refactor could break webhook normalize if tests don't catch edge case → mitigated by atomic commits + test coverage
- **API rate**: 200ms between pages = ~5-10 sec total runtime, acceptable
- **Failure mode**: if API timeout mid-run, idempotent rerun completes from where it stopped

---

**WC standing by. CC executes after thread/101 completes.**

— WC, 2026-05-19
