# 115 — WC: DoIt — `guests.name` resync from Beds24 (source of truth)

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: Alex policy decision — Beds24 booking firstName/lastName overwrites guests.name (history + new)
**Mode**: DoIt
**Status**: 🟢 Ready (after thread/113 hotfix lands; independent of C+E+D+P2 sprint)
**Estimated effort**: ~2-3h CC single PR

---

## TL;DR

Alex policy: Beds24 = source of truth for guest names. WhatsApp/Google Contacts initial sources were lower quality (placeholders like `"AirBnB +5215543549066"`, `"AirBnB - Promo: 625"`, `"🧿"`). Going forward AND for history, overwrite `guests.name` from Beds24 booking data.

4 edge case rules locked in:

| # | Rule | Default |
|---|---|---|
| 1 | Multi-booking conflicts | Most recent confirmed wins (`status IN ('booked','confirmed','request') ORDER BY created_at DESC`) |
| 2 | Beds24 firstName+lastName empty | Skip update, preserve previous (idempotent for future resync) |
| 3 | Booking status | Skip `inquiry` (unreliable AirBnB placeholder phase) |
| 4 | Cosmetic " (AirBnB)" suffix | Strip via regex `/\s*\(AirBnB\)\s*$/i` |

Plus 1 lock mechanism for Alex's own 2 guest records (name="Alexander Horn", never overwrite).

---

## §0 — Pre-flight

```powershell
1. Set-Location "$env:USERPROFILE\rdm\dev\bot"
2. git status --short  → clean
3. git fetch origin && git checkout main && git pull origin main
4. Verify thread/113 hotfix merged (PR for /proxReservas guest name source)
5. wrangler whoami → authenticated
6. ls migrations/ | tail -1  → confirms latest (0031 if before C+E+D+P2,
   0033 if after D's migration shipped). New migration is NEXT_AVAILABLE.
```

**Note on migration numbering**: this sprint is independent of C+E+D+P2.

- If lands BEFORE C+E+D+P2 sprint → migration 0032
- If lands AFTER → migration 0034 (assumes E=0032, D=0033)
- CC picks number based on observed `ls migrations/` state at start

---

## §1 — Branch + scope

```
git checkout -b feat/guests-resync-beds24
```

4 atomic commits per part (§2-§5 below).

---

## §2 — Migration: `name_locked` column + Alex lock

`migrations/00XX_guests_name_locked.sql` (NN per pre-flight):

```sql
-- Allow locking specific guest records from auto-name-resync.
-- Used for: Alex's own records, promo code holders, special guests.
-- Per Alex policy decision 2026-05-19 (thread/115).

ALTER TABLE guests ADD COLUMN name_locked INTEGER NOT NULL DEFAULT 0;

-- Lock Alex's 2 guest records + normalize to canonical "Alexander Horn"
-- (was "Alexander Horn ." with trailing period and "AirBnB - Promo: 625")
UPDATE guests 
  SET name = 'Alexander Horn', name_locked = 1, updated_at = unixepoch()
  WHERE id = 'g_01KRSZJVEH2H2M6G2WX6QGHGSQ';  -- +5215661027255, alex@rincondelmar.club

UPDATE guests 
  SET name = 'Alexander Horn', name_locked = 1, updated_at = unixepoch()
  WHERE id = 'g_XRP4Y5CZGJAREDCWRW0DBJS9K8';  -- +525570618798 (promo bookings linked here, dedupe later)

CREATE INDEX idx_guests_name_locked ON guests(name_locked) WHERE name_locked = 1;
```

**Verify post-apply**:
```sql
SELECT id, name, phone_e164, name_locked FROM guests WHERE name_locked = 1;
-- Expect 2 rows, both "Alexander Horn"
```

### Commit
```
fix(guests): add name_locked column + lock Alex's 2 guest records

Per thread/115: Beds24 = source of truth for guest names, EXCEPT
when name_locked=1. Alex's 2 records (g_01KRSZJVEH... CDMX phone +
g_XRP4Y5CZ... old promo phone) are locked to "Alexander Horn".

Promo bookings 86496769, 86497786, 86685323 stay linked to
g_XRP4Y5CZ... — separate dedupe work needed later if they should
be re-linked to actual promo recipients.

Refs: thread/115 §2
```

---

## §3 — Resync script (one-time + manual trigger)

`apps/worker-bot/src/scripts/resync-guest-names.ts`:

```typescript
/**
 * One-time resync of guests.name from Beds24 booking firstName/lastName.
 * 
 * Per thread/115 — Beds24 is source of truth for guest names.
 * 
 * Rules:
 *   - Pick MOST RECENT booking per guest (status IN booked/confirmed/request)
 *   - GET /v2/bookings?id={id} for that booking
 *   - Build name = trim(firstName + ' ' + lastName).replace(' (AirBnB)' suffix)
 *   - Skip if empty (Beds24 cap / AirBnB obscured)
 *   - Skip if name_locked = 1
 *   - Skip if same as current (no-op)
 *   - UPDATE guests SET name = new_name, updated_at = unixepoch()
 * 
 * Idempotent — safe to rerun. Subsequent runs only touch rows where Beds24
 * changed firstName/lastName since last sync.
 */

import { getBeds24AccessToken } from '../beds24-auth';

interface ResyncStats {
  total_guests_scanned: number;
  no_eligible_booking: number;
  api_fetched: number;
  api_errors: number;
  locked_skipped: number;
  empty_name_skipped: number;
  noop_same_name: number;
  updated: number;
  duration_ms: number;
  samples_updated: Array<{ guest_id: string; old: string; new: string }>;
}

const AIRBNB_SUFFIX = /\s*\(AirBnB\)\s*$/i;
const SAMPLE_CAP = 20;

export async function resyncGuestNames(env: Env, dryRun: boolean): Promise<ResyncStats> {
  const start = Date.now();
  const stats: ResyncStats = {
    total_guests_scanned: 0,
    no_eligible_booking: 0,
    api_fetched: 0,
    api_errors: 0,
    locked_skipped: 0,
    empty_name_skipped: 0,
    noop_same_name: 0,
    updated: 0,
    duration_ms: 0,
    samples_updated: [],
  };

  // Step 1: Get most-recent eligible booking per guest_id
  const eligibleBookings = await env.DB.prepare(`
    SELECT 
      bb.guest_id,
      bb.beds24_booking_id,
      bb.status,
      bb.created_at,
      g.name AS current_name,
      g.name_locked
    FROM beds24_bookings bb
    JOIN guests g ON g.id = bb.guest_id
    WHERE bb.status IN ('booked', 'confirmed', 'request')
    ORDER BY bb.guest_id, bb.created_at DESC
  `).all<{
    guest_id: string;
    beds24_booking_id: number;
    status: string;
    created_at: number;
    current_name: string | null;
    name_locked: number;
  }>();

  // Dedupe — take first (most recent) per guest_id
  const mostRecentPerGuest = new Map<string, typeof eligibleBookings.results[0]>();
  for (const row of eligibleBookings.results ?? []) {
    if (!mostRecentPerGuest.has(row.guest_id)) {
      mostRecentPerGuest.set(row.guest_id, row);
    }
  }

  stats.total_guests_scanned = mostRecentPerGuest.size;

  // Step 2: For each guest's most recent booking, fetch Beds24 + update
  let token: string;
  try {
    token = await getBeds24AccessToken(env);
  } catch (err) {
    console.error('[resync-guest-names] failed to get Beds24 token', err);
    throw err;
  }

  for (const [guestId, booking] of mostRecentPerGuest) {
    // Rule: skip locked
    if (booking.name_locked === 1) {
      stats.locked_skipped++;
      continue;
    }

    // Fetch Beds24 booking
    let firstName = '';
    let lastName = '';
    try {
      const res = await fetch(
        `https://api.beds24.com/v2/bookings?id=${booking.beds24_booking_id}`,
        { headers: { token, accept: 'application/json' } },
      );
      if (!res.ok) {
        stats.api_errors++;
        console.warn(`[resync-guest-names] Beds24 ${res.status} for booking ${booking.beds24_booking_id}`);
        continue;
      }
      const json = await res.json() as { data?: Array<{ firstName?: string; lastName?: string }> };
      firstName = (json.data?.[0]?.firstName ?? '').trim();
      lastName = (json.data?.[0]?.lastName ?? '').trim();
      stats.api_fetched++;
    } catch (err) {
      stats.api_errors++;
      console.error(`[resync-guest-names] fetch error for ${booking.beds24_booking_id}:`, err);
      continue;
    }

    // Build clean name
    const cleanName = `${firstName} ${lastName}`.trim().replace(AIRBNB_SUFFIX, '').trim();

    // Rule: skip empty
    if (!cleanName) {
      stats.empty_name_skipped++;
      continue;
    }

    // No-op same
    if (cleanName === (booking.current_name ?? '').trim()) {
      stats.noop_same_name++;
      continue;
    }

    // Update
    if (!dryRun) {
      await env.DB.prepare(`
        UPDATE guests SET name = ?, updated_at = unixepoch() WHERE id = ?
      `).bind(cleanName, guestId).run();
    }
    stats.updated++;

    if (stats.samples_updated.length < SAMPLE_CAP) {
      stats.samples_updated.push({
        guest_id: guestId,
        old: booking.current_name ?? '(null)',
        new: cleanName,
      });
    }
  }

  stats.duration_ms = Date.now() - start;
  return stats;
}
```

### Admin endpoint

In `apps/worker-bot/src/index.ts`:

```typescript
app.post('/admin/guests-resync-names', async (c) => {
  const auth = c.req.header('x-admin-secret');
  if (auth !== c.env.ADMIN_REFRESH_SECRET) {
    return c.json({ ok: false, error: 'unauthorized' }, 401);
  }
  
  const dryRun = c.req.query('dry_run') !== 'false';  // safe default: TRUE
  
  try {
    const stats = await resyncGuestNames(c.env, dryRun);
    return c.json({ ok: true, dry_run: dryRun, stats });
  } catch (err) {
    return c.json({ ok: false, error: String(err).slice(0, 500) }, 500);
  }
});
```

### Tests

`apps/worker-bot/tests/resync-guest-names.test.ts`:

- Guest with most recent booked → Beds24 API returns "John Doe" → guests.name updated, sample logged
- Guest with name_locked=1 → skipped, counter incremented
- Guest with Beds24 empty firstName+lastName → empty_name_skipped++
- Guest with current name == Beds24 name → noop_same_name++
- Beds24 returns 404 / error → api_errors++ but loop continues
- Guest with " (AirBnB)" suffix in Beds24 → cleaned (stripped) before save
- Multi-booking same guest: only most recent processed (others ignored)
- dryRun=true → no UPDATEs executed, stats correct
- dryRun=false → UPDATEs executed
- Guest with only inquiry-status bookings → no_eligible_booking++ (filtered out)

### Commit
```
feat(guests): resync names from Beds24 (source of truth)

One-time script + manual trigger endpoint to overwrite guests.name
with Beds24 firstName/lastName for the most recent booked/confirmed
booking per guest.

Rules:
- Skip name_locked=1 records (Alex's 2 records pre-locked)
- Skip if Beds24 firstName+lastName both empty (AirBnB cap)
- Strip ' (AirBnB)' suffix cosmetic
- Skip status='inquiry' (unreliable)
- Idempotent (no-op when same name)

Endpoint: POST /admin/guests-resync-names?dry_run=true (default safe)
Switch to ?dry_run=false to execute updates.

Tests: 10 paths covering edge cases.

Refs: thread/115 §3
```

---

## §4 — Webhook handler: update guests.name on every event

In `apps/worker-bot/src/beds24-webhook.ts`, after normalize + insert event:

```typescript
import { updateGuestNameFromBooking } from './guests-name-update';

// After existing webhook flow:
try {
  await updateGuestNameFromBooking(env, normalizedBooking);
} catch (err) {
  console.error('[webhook] guest name update failed', err);
  // Don't fail the webhook — log only
}
```

New file `apps/worker-bot/src/guests-name-update.ts`:

```typescript
/**
 * Update guests.name when a Beds24 booking event arrives.
 * 
 * Per thread/115 — Beds24 = source of truth. Webhook is the live path
 * for keeping names fresh. Resync script handles history.
 * 
 * Same rules as resync:
 *   - Skip name_locked=1
 *   - Skip if firstName+lastName both empty
 *   - Strip ' (AirBnB)' suffix
 *   - Skip status='inquiry'
 *   - Idempotent (no-op when same)
 */

const AIRBNB_SUFFIX = /\s*\(AirBnB\)\s*$/i;

interface NormalizedBooking {
  beds24_booking_id: number;
  guest_id: string;
  status: string;
  firstName?: string;
  lastName?: string;
}

export async function updateGuestNameFromBooking(
  env: Env, 
  booking: NormalizedBooking,
): Promise<{ updated: boolean; reason: string }> {
  // Rule: skip inquiry status
  if (!['booked', 'confirmed', 'request'].includes(booking.status)) {
    return { updated: false, reason: 'status_not_eligible' };
  }

  const firstName = (booking.firstName ?? '').trim();
  const lastName = (booking.lastName ?? '').trim();

  // Rule: skip empty
  const cleanName = `${firstName} ${lastName}`.trim().replace(AIRBNB_SUFFIX, '').trim();
  if (!cleanName) {
    return { updated: false, reason: 'empty_name' };
  }

  // Get current guest name + lock status
  const guest = await env.DB.prepare(`
    SELECT name, name_locked FROM guests WHERE id = ?
  `).bind(booking.guest_id).first<{ name: string | null; name_locked: number }>();

  if (!guest) {
    return { updated: false, reason: 'guest_not_found' };
  }

  // Rule: skip locked
  if (guest.name_locked === 1) {
    return { updated: false, reason: 'name_locked' };
  }

  // No-op same
  if (cleanName === (guest.name ?? '').trim()) {
    return { updated: false, reason: 'noop_same_name' };
  }

  // Update
  await env.DB.prepare(`
    UPDATE guests SET name = ?, updated_at = unixepoch() WHERE id = ?
  `).bind(cleanName, booking.guest_id).run();

  return { updated: true, reason: 'updated' };
}
```

### Tests

`apps/worker-bot/tests/guests-name-update.test.ts`:

- Inquiry status → skipped (reason: status_not_eligible)
- Empty firstName + lastName → skipped (reason: empty_name)
- Locked guest → skipped (reason: name_locked)
- Same name → skipped (reason: noop_same_name)
- Different name → updated, returns reason: updated
- " (AirBnB)" suffix → stripped before compare/save
- guest_id not found → skipped (reason: guest_not_found)

### Commit
```
feat(beds24-webhook): live update guests.name on every event

Webhook handler now calls updateGuestNameFromBooking() after
event normalize. Same rules as resync script (skip locked, skip
empty, skip inquiry, strip ' (AirBnB)', idempotent).

Errors logged but don't fail webhook response.

Refs: thread/115 §4
```

---

## §5 — Backfill code update: respect resync rule

In `apps/worker-bot/src/beds24-backfill.ts` (where it links bookings to existing guests):

```typescript
// EXISTING: dedupe match by phone, link booking to existing guest
// CHANGE: also UPDATE guests.name with current booking's name
//   (subject to lock + empty rules from §4)

import { updateGuestNameFromBooking } from './guests-name-update';

// Inside the per-booking backfill loop, AFTER guest_id resolution:
await updateGuestNameFromBooking(env, {
  beds24_booking_id: booking.id,
  guest_id: resolvedGuestId,
  status: booking.status,
  firstName: booking.firstName,
  lastName: booking.lastName,
});
```

### Tests

Extend `apps/worker-bot/tests/beds24-backfill.test.ts` (if exists):
- Backfilling booking with existing guest + different name → updates guests.name
- Backfilling with locked guest → preserves locked name
- Backfilling with empty firstName → no UPDATE

### Commit
```
feat(beds24-backfill): apply guests.name resync rule during backfill

Future backfill runs now call updateGuestNameFromBooking() per
booking. Aligns backfill with webhook + manual resync behavior:
single rule, single helper, three call sites.

Refs: thread/115 §5
```

---

## §6 — Push + PR + apply + deploy

```bash
git push origin feat/guests-resync-beds24

gh pr create \
  --title "feat(guests): name resync from Beds24 source of truth" \
  --body "Per thread/115 — Alex policy: Beds24 firstName+lastName overwrites guests.name.

4 atomic commits:
- §2 migration NN: add name_locked column + lock Alex's 2 records
- §3 resync script + endpoint POST /admin/guests-resync-names
- §4 webhook live update on every Beds24 event
- §5 backfill code respects resync rule

Rules: skip name_locked=1, skip empty, skip inquiries, strip ' (AirBnB)'.

Refs: thread/115"

gh pr merge <N> --squash --delete-branch

# Apply migration (ask tier)
wrangler d1 migrations apply rincon --remote

# Deploy worker (ask tier)
wrangler deploy
```

---

## §7 — Smoke tests after deploy

```bash
# Verify lock applied
wrangler d1 execute rincon --remote --command "SELECT id, name, name_locked FROM guests WHERE name_locked = 1"
# Expected: 2 rows, both 'Alexander Horn'

# DRY RUN first
curl -X POST \
  -H "Authorization: Bearer $ADMIN_REFRESH_SECRET" \
  "https://rincondelmar.club/admin/guests-resync-names?dry_run=true"
# Expected: {ok: true, dry_run: true, stats: {scanned: N, updated: M, ...}}
# Review samples_updated array — confirm names look right

# If samples look correct, ACTUAL RUN
curl -X POST \
  -H "Authorization: Bearer $ADMIN_REFRESH_SECRET" \
  "https://rincondelmar.club/admin/guests-resync-names?dry_run=false"
# Expected: same counts, this time UPDATEs applied

# Verify specific bookings post-resync
wrangler d1 execute rincon --remote --command "
  SELECT bb.beds24_booking_id, g.name 
  FROM beds24_bookings bb 
  LEFT JOIN guests g ON g.id = bb.guest_id 
  WHERE bb.beds24_booking_id IN (85820359, 86655644, 86496769)
"
# Expected:
#   85820359 → "Erika ..." (was "AirBnB +5215543549066")
#   86655644 → "AirBnB +52..." or similar (Beds24 empty → preserved old)
#   86496769 → "Alexander Horn" (LOCKED — not changed)
```

---

## §8 — Anti-patterns (NO HACER)

- ❌ Bypass `name_locked` for any reason
- ❌ Update inquiry-status bookings (Edge 3)
- ❌ Overwrite with empty Beds24 names (Edge 2)
- ❌ Re-link promo bookings 86496769/86497786/86685323 to new guests (separate dedupe task)
- ❌ Touch `guests.phone_e164` (separate field, separate task)
- ❌ Backfill past 365+ days (only recent active bookings)
- ❌ Auto-trigger resync on cron (manual trigger only for v1)

---

## §9 — Out of scope

- ❌ Re-dedupe Alex's 2 guest records (they have different phones — separate concern)
- ❌ Re-link promo bookings to actual recipients (post-resync work)
- ❌ Strip " (AirBnB)" from past names in `guests.name` directly (only on new updates via resync flow)
- ❌ Touch /admin/conv display
- ❌ Touch /admin/inbox display
- ❌ Beds24 invoice items / messages (Part D scope)
- ❌ rdm-platform repo touches

---

## §10 — External state

- Alex's 2 guest_ids confirmed via D1 MCP:
  - `g_01KRSZJVEH2H2M6G2WX6QGHGSQ` — +5215661027255 — email alex@rincondelmar.club
  - `g_XRP4Y5CZGJAREDCWRW0DBJS9K8` — +525570618798 — old 2021 record, 3 promo bookings linked
- Beds24 API v2: `GET /v2/bookings?id=N` returns `{ data: [{ firstName, lastName, ... }] }`
- AirBnB cap: ~1 booking observed (86655644) with empty firstName+lastName — preserved per Edge 2
- Backfill 62 bookings (thread/103) all have guest_id linked to existing or new guests
- ~62 + ~30 webhook arrival = ~92 guests with eligible bookings (rough estimate)

---

## §11 — Si te atoras

- Beds24 API rate limit hit: throttle to 5 req/s, retry with backoff
- `name_locked` UPDATE fails: rollback migration, investigate
- Resync stats show 50%+ api_errors: STOP, investigate token / endpoint
- Some guests have no bookings (lead-only): no_eligible_booking++ counter expected
- Beds24 API returns weird data shape: log + skip, don't crash
- Multi-language names (accents): UTF-8 safe (D1 + Beds24 both UTF-8) — should just work
- Anything unexpected: STOP, report

---

## §12 — Reporting

In thread/116-cc-bot-guests-resync-shipped.md:

- Migration NN applied confirmation
- Resync endpoint deployed
- Dry-run stats (Alex sees first, blesses real run)
- Actual run stats post-bless
- Sample of 10-20 updates (old → new name pairs)
- Specific verifications:
  - 85820359 → resolves to real name (Erika ...)
  - 86655644 → preserved (empty Beds24)
  - 86496769/86497786/86685323 → all "Alexander Horn" (locked)
- Any blockers or partial implementations

---

**WC standing by. CC executes single PR, 4 atomic commits.**

— WC, 2026-05-19
