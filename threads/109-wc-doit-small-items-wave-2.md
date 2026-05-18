# 109 — WC: DoIt — small items wave #2 (4 issues)

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: 4 issues nuevos from Alex feedback wave
**Mode**: DoIt
**Status**: 🟢 Ready AFTER thread/108 (thread/107 small items wave #1) completes
**Estimated effort**: ~10-13h CC

---

## TL;DR — Table of Contents

4 parts bundled. Single PR after thread/108 merged.

| Part | Item | Effort | Section |
|---|---|---|---|
| **G** | Phone display fix + wa.me clickable | 1-2h | §1 |
| **H** | Fix `/admin/airbnb-content` 500 error | 1-2h | §2 |
| **I** | `/proxReservas` modern clone (staff temporal tool) | 3-4h | §3 |
| **J** | `/guia-llegada` rich content (replace placeholder) | 4-5h | §4 |

Total: ~10-13h CC. Single PR `feat/small-items-wave-2`. 4 atomic commits.

---

## §0 — Common pre-flight

```powershell
1. Set-Location "$env:USERPROFILE\rdm\dev\bot"
2. git status --short  → clean
3. git fetch origin
4. git checkout main && git pull origin main
5. gh auth status → logged in
6. wrangler whoami → authenticated
7. Verify thread/108 (small items wave #1) merged successfully:
   gh pr list --repo alexanderhorn6720/rdm-bot --state merged --limit 5
   Should include "feat(wave): small items bundle"
8. ls migrations/ | tail -1  → should show 0033 (last from thread/107)
   New migrations start at 0034
```

============================================================
DELIVERABLES — high level
============================================================

PASO 1 — Branch
```
git checkout -b feat/small-items-wave-2
```

PASO 2 — Execute parts G → H → I → J in order (Quick wins first)
PASO 3 — 4 atomic commits min
PASO 4 — Push + PR + squash merge
PASO 5 — Deploy worker (ask tier) + Apply migrations (if any)
PASO 6 — Smoke tests
PASO 7 — Report thread/110

---

## §1 — Part G: Phone field display + wa.me clickable (1-2h)

### Problem statement (Alex feedback)

> "AirBnB bookings phone number is not showing up in beds24, at least not in mobile or cell phone field"

### Diagnosis (WC verified via D1 MCP)

**NOT a bug**. Beds24 maps phone differently per channel:

| Channel | Field used | Example |
|---|---|---|
| AirBnB | `phone` | `525577588604` (Luis), `525514510393` (Moy) |
| Direct (AlexanderHorn) | `mobile` | `5570618798` (Alex own) |
| Booking.com | TBD (verify during impl) | — |

The Beds24 panel "Móvil" field shows `mobile` value. For AirBnB bookings, phone lives in `phone` field, NOT `mobile`.

### Fix scope

1. **Update `/admin/bookings` drawer** to display phone as `phone OR mobile OR '(sin teléfono)'`
2. **Update list view** if phone column exists
3. **Make phone clickable** → opens `https://wa.me/<normalized_phone>`
4. **Phone normalization helper** for wa.me URL construction

### Phone normalization logic

Different formats observed:

| Raw format | Normalized for wa.me |
|---|---|
| `525577588604` (12 dígitos, MX completo) | `525577588604` (passthrough) |
| `5215514935302` (13 dígitos, MX viejo móvil con `1`) | `5215514935302` (passthrough, both formats work) |
| `5570618798` (10 dígitos, sin código país) | `525570618798` (prepend `52`) |
| `+52 55 7061 8798` (con espacios) | `525570618798` (strip non-digits, normalize) |

```typescript
// File: apps/web/src/lib/phone-normalize.ts

/**
 * Normalize Mexican phone number for wa.me deep-link.
 * 
 * Returns normalized digits-only string (no +, no spaces).
 * Returns null if phone is empty or invalid.
 */
export function normalizePhoneForWhatsApp(rawPhone: string | null | undefined): string | null {
  if (!rawPhone || rawPhone.trim() === '') return null;
  
  // Strip all non-digits
  let digits = rawPhone.replace(/\D/g, '');
  
  // Empty after strip
  if (digits.length === 0) return null;
  
  // 10 digits = MX without country code → prepend 52
  if (digits.length === 10) {
    digits = '52' + digits;
  }
  
  // 11 digits starting with 1 = MX viejo mobile (1XXX) → keep as is (assume already has country?)
  // Conservative: if 11 digits and starts with 1, treat as malformed, prepend 52 + drop leading 1
  if (digits.length === 11 && digits.startsWith('1')) {
    digits = '52' + digits.slice(1);
  }
  
  // 12 digits starting with 52 = MX full → passthrough
  // 13 digits starting with 521 = MX old mobile format → passthrough (wa.me accepts both)
  // Other lengths (e.g. US 11 digits 1XXXXXXXXXX) → passthrough, trust user
  
  // Sanity: must be 10-15 digits
  if (digits.length < 10 || digits.length > 15) return null;
  
  return digits;
}

/**
 * Get wa.me URL for phone, or null if phone invalid.
 */
export function whatsappLink(phone: string | null | undefined): string | null {
  const normalized = normalizePhoneForWhatsApp(phone);
  return normalized ? `https://wa.me/${normalized}` : null;
}

/**
 * Get display-formatted phone (with + and country code).
 */
export function formatPhoneDisplay(phone: string | null | undefined): string {
  const normalized = normalizePhoneForWhatsApp(phone);
  if (!normalized) return '(sin teléfono)';
  return `+${normalized}`;
}
```

### Drawer rendering

In booking drawer (wherever phone displays):

```tsx
import { whatsappLink, formatPhoneDisplay } from '@/lib/phone-normalize';

const rawPhone = booking.phone || booking.mobile || null;
const waUrl = whatsappLink(rawPhone);
const displayPhone = formatPhoneDisplay(rawPhone);

<div className="phone-row">
  <strong>Phone:</strong>
  {waUrl ? (
    <a href={waUrl} target="_blank" rel="noopener noreferrer" className="phone-link">
      {displayPhone} 💬
    </a>
  ) : (
    <span className="phone-empty">{displayPhone}</span>
  )}
</div>
```

### CSS

```css
.phone-link {
  color: #25D366; /* WhatsApp green */
  text-decoration: none;
  font-family: monospace;
}
.phone-link:hover {
  text-decoration: underline;
}
.phone-empty {
  color: #999;
  font-style: italic;
}
```

### Tests

`apps/web/tests/phone-normalize.test.ts`:

- `525577588604` → `525577588604`
- `5215514935302` → `5215514935302`
- `5570618798` → `525570618798`
- `+52 55 7061 8798` → `525570618798`
- `` (empty) → null
- `abc` (no digits) → null
- `123` (too short) → null
- AirBnB obscured "+1 (555) ***-XXXX" with mask → null gracefully

### Acceptance criteria Part G

- `phone-normalize.ts` helper created with tests
- Drawer shows phone (fallback to mobile if phone empty)
- Phone clickable → opens wa.me in new tab
- AirBnB bookings show real number (not empty)
- Empty phone shows "(sin teléfono)" gracefully

**Commit**:
```
feat(admin/bookings): phone fallback + wa.me clickable links

- Drawer uses booking.phone || booking.mobile (AirBnB stores in phone)
- Phone normalization helper (10d MX → prepend 52, etc)
- Clickable phone opens wa.me in new tab
- Helper: apps/web/src/lib/phone-normalize.ts (with tests)

Resolves Alex feedback: AirBnB phone was hidden in panel Móvil view.
Refs: thread/109 §1
```

---

## §2 — Part H: Fix `/admin/airbnb-content` 500 error (1-2h)

### Problem statement (Alex feedback)

> "https://rincondelmar.club/admin/airbnb-content still showing 500 when logged in"

### Investigation scope

CC must debug LIVE. Possible causes:

1. **R2 binding `KNOWLEDGE_BUCKET` issue post deploy**
   - Verify binding in `apps/web/wrangler.toml`
   - Check `getAllDrafts(env.KNOWLEDGE_BUCKET)` doesn't throw
   - Check R2 access permissions

2. **Schema breaking change**
   - Check `@rdm/shared/airbnb-content-schema` recent changes
   - Verify `AIRBNB_FIELD_NAMES`, `AIRBNB_FIELDS`, etc still exist
   - Check imports in `apps/web/src/pages/admin/airbnb-content/index.astro`

3. **Auth issue**
   - Verify `isContentEditor(env, user?.email)` works with Alex's email
   - Check Better Auth session cookie

4. **Server-side render error**
   - Check Worker tail logs during request
   - Look for unhandled errors in async load

### Debug steps

```bash
# Step 1: Run worker tail to see real-time errors
wrangler tail --format pretty &

# Step 2: Trigger /admin/airbnb-content request from browser
# (Alex logs in, navigates to URL)

# Step 3: Capture error stack trace

# Step 4: Identify root cause from logs

# Step 5: Apply fix per root cause type
```

### Fix scope (depends on root cause)

Once identified:
- **R2 issue**: ensure binding configured + graceful degrade if bucket empty
- **Schema issue**: align imports with current schema package
- **Auth issue**: verify email comparison logic + handle edge cases
- **Render error**: try/catch + error boundary + user-friendly error page

### Acceptance criteria Part H

- Root cause documented in commit message
- `/admin/airbnb-content` returns 200 for content_editor + admin roles
- Graceful error display if R2 bucket has issues (not bare 500)
- Tests added for error handling path
- Karina + Alex can access page

**Commit**:
```
fix(admin/airbnb-content): resolve 500 error logged in

Root cause: [TBD from investigation — e.g. R2 binding missing,
schema import broken, etc.]

Fix:
- [specific fix actions]
- Added error boundary for graceful degradation
- Tests cover error handling path

Refs: thread/109 §2
```

---

## §3 — Part I: `/proxReservas` modern clone (3-4h)

### Problem statement (Alex feedback)

> "Need something like this, with EXACTLY same path and password — my staff uses it currently, can't wait until staff PWA ready, temp solution: https://rincondelmar.club/proxReservas.php?pass=vivamexico (including huerta)"

### Scope (per Alex confirmation)

| Requirement | Decision |
|---|---|
| Properties | All 4 (RdM + Morenas + Combinada + Huerta) |
| Filter periods | 2 semanas / 2 meses / 4 meses |
| Design | **Moderno** (not legacy HTML/CSS) |
| Filters/search | YES (free-text search guest name + property filter chips) |
| Time range | Solo futuras (no pasadas) |
| URL | EXACT same path: `/proxReservas.php?pass=vivamexico` (preserve muscle memory) |
| Pass | `vivamexico` hardcoded en env var (rotable después) |
| Refresh | Manual reload (no realtime) |
| Mobile | Mobile-first (staff usa phone) |

### Route handler

Astro page at `apps/web/src/pages/proxReservas.php.astro`:

```astro
---
/**
 * /proxReservas.php?pass=vivamexico — Staff próximas reservas (temp).
 * 
 * Per thread/109 §3 (Alex feedback 2026-05-19).
 * URL preserves muscle memory from legacy PHP page.
 * Replaces legacy PHP. Temp until apps/staff PWA ready (~months).
 * 
 * Auth: simple pass via URL param. NO Better Auth (staff doesn't have accounts).
 * Pass stored in env STAFF_PROX_RESERVAS_PASS (default 'vivamexico').
 * 
 * Data: D1 beds24_bookings filtered status='booked' AND arrival >= today.
 * Filter UI: period chips (2w/2m/4m) + search input.
 */
import BaseLayout from '@/layouts/BaseLayout.astro';
import StaffReservasList from '@/components/staff/StaffReservasList.tsx';

export const prerender = false;

const env = Astro.locals.runtime?.env as Env | undefined;
const url = Astro.url;
const providedPass = url.searchParams.get('pass') ?? '';
const expectedPass = env?.STAFF_PROX_RESERVAS_PASS ?? 'vivamexico';

if (providedPass !== expectedPass) {
  return new Response('Forbidden', { status: 403 });
}

// Load upcoming bookings
let bookings: BookingRow[] = [];
let error: string | null = null;

try {
  const result = await env?.DB.prepare(`
    SELECT 
      bb.beds24_booking_id,
      bb.room_id,
      bb.arrival,
      bb.departure,
      bb.num_nights,
      bb.num_adults,
      bb.num_children,
      bb.num_pets,
      bb.total_guests,
      bb.channel,
      bb.status,
      bb.total_amount_mxn,
      -- Pull guest name + phone from beds24_events latest
      (SELECT json_extract(payload_json,'$.booking.firstName') 
       FROM beds24_events e 
       WHERE CAST(json_extract(e.payload_json,'$.booking.id') AS INTEGER) = bb.beds24_booking_id
       ORDER BY received_at DESC LIMIT 1) as first_name,
      (SELECT json_extract(payload_json,'$.booking.lastName') 
       FROM beds24_events e 
       WHERE CAST(json_extract(e.payload_json,'$.booking.id') AS INTEGER) = bb.beds24_booking_id
       ORDER BY received_at DESC LIMIT 1) as last_name,
      (SELECT COALESCE(json_extract(payload_json,'$.booking.phone'),
                        json_extract(payload_json,'$.booking.mobile'))
       FROM beds24_events e 
       WHERE CAST(json_extract(e.payload_json,'$.booking.id') AS INTEGER) = bb.beds24_booking_id
       ORDER BY received_at DESC LIMIT 1) as phone,
      (SELECT json_extract(payload_json,'$.booking.guestComments') 
       FROM beds24_events e 
       WHERE CAST(json_extract(e.payload_json,'$.booking.id') AS INTEGER) = bb.beds24_booking_id
       ORDER BY received_at DESC LIMIT 1) as guest_comments
    FROM beds24_bookings bb
    WHERE bb.status = 'booked'
      AND bb.arrival >= date('now')
    ORDER BY bb.arrival ASC
    LIMIT 200
  `).all<BookingRow>();
  
  bookings = result?.results ?? [];
} catch (err) {
  error = String(err);
  console.error('[proxReservas] load error', err);
}

// Property names mapping
const PROPERTY_NAMES: Record<number, string> = {
  78695: 'Rincón del Mar',
  374482: 'Las Morenas',
  74316: 'Combinada',
  637063: 'Huerta Cocotera',
};
---

<BaseLayout
  title="Próximas reservas"
  description="Staff tool"
  noindex={true}
>
  <main class="staff-prox-reservas">
    <header>
      <h1>Próximas reservas</h1>
      <p class="meta">
        {bookings.length} reservas próximas · Actualizado: {new Date().toLocaleString('es-MX', { timeZone: 'America/Mexico_City' })}
      </p>
    </header>

    {error && <div class="error-banner">Error cargando datos: {error}</div>}

    <StaffReservasList 
      bookings={bookings} 
      propertyNames={PROPERTY_NAMES} 
      client:load 
    />
  </main>
</BaseLayout>

<style>
  .staff-prox-reservas {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px;
  }
  
  header h1 {
    margin: 0 0 4px;
    font-size: 24px;
  }
  
  .meta {
    font-size: 13px;
    color: #666;
    margin: 0 0 16px;
  }
  
  .error-banner {
    background: #fee;
    border: 1px solid #fcc;
    padding: 12px;
    border-radius: 8px;
    color: #c00;
    margin-bottom: 16px;
  }
</style>
```

### React component for list + filters

```tsx
// apps/web/src/components/staff/StaffReservasList.tsx

import { useState, useMemo } from 'react';
import { whatsappLink, formatPhoneDisplay } from '@/lib/phone-normalize';

interface BookingRow {
  beds24_booking_id: number;
  room_id: number;
  arrival: string;
  departure: string;
  num_nights: number;
  num_adults: number;
  num_children: number;
  num_pets: number;
  channel: string;
  total_amount_mxn: number;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  guest_comments: string | null;
}

type PeriodFilter = '2w' | '2m' | '4m' | 'all';

interface StaffReservasListProps {
  bookings: BookingRow[];
  propertyNames: Record<number, string>;
}

export default function StaffReservasList({ bookings, propertyNames }: StaffReservasListProps) {
  const [period, setPeriod] = useState<PeriodFilter>('2m');
  const [propertyFilter, setPropertyFilter] = useState<number | 'all'>('all');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let result = bookings;
    
    // Period filter
    if (period !== 'all') {
      const days = period === '2w' ? 14 : period === '2m' ? 60 : 120;
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() + days);
      result = result.filter(b => new Date(b.arrival) <= cutoff);
    }
    
    // Property filter
    if (propertyFilter !== 'all') {
      result = result.filter(b => b.room_id === propertyFilter);
    }
    
    // Search filter
    if (search.trim()) {
      const q = search.toLowerCase().trim();
      result = result.filter(b => {
        const fullName = `${b.first_name ?? ''} ${b.last_name ?? ''}`.toLowerCase();
        return fullName.includes(q) || (b.phone ?? '').includes(q);
      });
    }
    
    return result;
  }, [bookings, period, propertyFilter, search]);

  return (
    <div className="staff-list">
      {/* Filters */}
      <div className="filters">
        <div className="filter-chips" role="group" aria-label="Período">
          {(['2w', '2m', '4m', 'all'] as PeriodFilter[]).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`chip ${period === p ? 'active' : ''}`}
            >
              {p === '2w' && '2 semanas'}
              {p === '2m' && '2 meses'}
              {p === '4m' && '4 meses'}
              {p === 'all' && 'Todas'}
            </button>
          ))}
        </div>
        
        <div className="filter-chips" role="group" aria-label="Propiedad">
          <button
            onClick={() => setPropertyFilter('all')}
            className={`chip ${propertyFilter === 'all' ? 'active' : ''}`}
          >
            Todas
          </button>
          {Object.entries(propertyNames).map(([id, name]) => (
            <button
              key={id}
              onClick={() => setPropertyFilter(Number(id))}
              className={`chip ${propertyFilter === Number(id) ? 'active' : ''}`}
            >
              {name}
            </button>
          ))}
        </div>
        
        <input
          type="search"
          placeholder="🔍 Buscar nombre o teléfono..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="results-count">
        {filtered.length} de {bookings.length} reservas
      </div>

      {/* Bookings cards */}
      <div className="bookings-grid">
        {filtered.length === 0 ? (
          <div className="empty">Sin reservas con los filtros aplicados.</div>
        ) : (
          filtered.map(b => (
            <article key={b.beds24_booking_id} className="booking-card">
              <header className="card-header">
                <span className="property-name">{propertyNames[b.room_id] ?? `Room ${b.room_id}`}</span>
                <span className={`channel-badge channel-${b.channel}`}>
                  {b.channel === 'airbnb' ? '🅰 Airbnb' :
                   b.channel === 'booking_com' ? 'Ⓑ Booking' :
                   b.channel === 'direct' ? '💬 Direct' : b.channel}
                </span>
              </header>
              
              <div className="card-body">
                <h3 className="guest-name">
                  {b.first_name ?? '(sin nombre)'} {b.last_name ?? ''}
                </h3>
                
                <div className="dates">
                  <span className="date-arrival">{formatDate(b.arrival)}</span>
                  <span className="date-sep">→</span>
                  <span className="date-departure">{formatDate(b.departure)}</span>
                  <span className="nights">({b.num_nights}N)</span>
                </div>
                
                <div className="guests-row">
                  👥 {b.num_adults} adultos
                  {b.num_children > 0 && <span> · {b.num_children} niños</span>}
                  {b.num_pets > 0 && <span> · 🐾 {b.num_pets}</span>}
                </div>
                
                {b.phone && (
                  <div className="phone-row">
                    📞 {whatsappLink(b.phone) ? (
                      <a href={whatsappLink(b.phone)!} target="_blank" rel="noopener">
                        {formatPhoneDisplay(b.phone)}
                      </a>
                    ) : (
                      <span>{b.phone}</span>
                    )}
                  </div>
                )}
                
                {b.guest_comments && (
                  <div className="comments">
                    💬 {b.guest_comments}
                  </div>
                )}
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: '2-digit',
  });
}
```

### CSS (mobile-first)

```css
.staff-list { padding: 0; }

.filters {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  position: sticky;
  top: 0;
  background: white;
  padding: 12px 0;
  z-index: 10;
}

.filter-chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: thin;
}

.chip {
  padding: 6px 14px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.chip.active {
  background: #00A19A;
  color: white;
  border-color: #00A19A;
}

.search-input {
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  width: 100%;
}

.results-count {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}

.bookings-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

@media (min-width: 768px) {
  .bookings-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .bookings-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.booking-card {
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 14px;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
}

.property-name {
  font-weight: 600;
  color: #333;
}

.channel-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
}
.channel-badge.channel-airbnb { background: #ffe0e0; color: #FF5A5F; }
.channel-badge.channel-booking_com { background: #e0e8ff; color: #003580; }
.channel-badge.channel-direct { background: #d9fdd3; color: #1f7a1f; }

.guest-name {
  font-size: 16px;
  margin: 0 0 8px;
  font-weight: 600;
}

.dates {
  font-size: 14px;
  margin-bottom: 8px;
}
.nights { color: #888; margin-left: 8px; font-size: 12px; }
.date-sep { margin: 0 6px; color: #aaa; }

.guests-row, .phone-row {
  font-size: 13px;
  margin-bottom: 6px;
}

.phone-row a {
  color: #25D366;
  text-decoration: none;
  font-family: monospace;
}

.comments {
  margin-top: 10px;
  padding: 8px 10px;
  background: #fffde7;
  border-radius: 6px;
  font-size: 12px;
  border-left: 3px solid #fbc02d;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}
```

### Wrangler config

Add to `apps/web/wrangler.toml`:

```toml
[vars]
STAFF_PROX_RESERVAS_PASS = "vivamexico"  # production override via secret
```

Then in production:
```bash
wrangler secret put STAFF_PROX_RESERVAS_PASS --env production
# enter: vivamexico
```

### Tests

`apps/web/tests/staff-prox-reservas.test.ts`:
- Wrong pass → 403
- Right pass → 200 with bookings
- No future bookings → 200 with empty state
- Filter logic isolated (mock data → filtered correctly)

### Acceptance criteria Part I

- Route `/proxReservas.php?pass=vivamexico` returns 200
- Wrong pass returns 403
- Lists ONLY future bookings (status='booked' AND arrival >= today)
- All 4 properties included
- 3 period filters (2w / 2m / 4m) + "Todas"
- Property chips + free-text search
- Phone clickable (uses Part G helper)
- Mobile-friendly cards (responsive grid)
- Guest comments displayed when present
- Karina/staff can use on phone

**Commit**:
```
feat(staff/prox-reservas): modern clone of legacy PHP staff tool

Replaces /proxReservas.php (legacy) with modern Astro+React page.
URL preserved EXACTLY (muscle memory staff).
Pass-protected via STAFF_PROX_RESERVAS_PASS env (default 'vivamexico').

Features:
- Future bookings only (status=booked, arrival>=today)
- All 4 properties (RdM, Morenas, Combinada, Huerta)
- Filters: period (2w/2m/4m), property chips, free-text search
- Phone clickable via wa.me (reuses Part G helper)
- Mobile-first responsive grid
- Guest comments displayed inline

Temp solution until apps/staff PWA ready.
Refs: thread/109 §3
```

---

## §4 — Part J: `/guia-llegada` rich content (4-5h)

### Problem statement (Alex feedback)

> "/como-llegar/ or /guia-llegada needs to be much nicer, this link is out already to many guests through Airbnb and whatsapp, they actively use it. Needs something much more detailed like what I had before, here legacy sister site morenas: rincondelasmorenas.club/guia-llegada"

### Scope

Replace current placeholder (180 lines) with rich content matching legacy quality + adapted to RdM properties (4 properties vs 1).

### Reference legacy content sections

Per `rincondelasmorenas.club/guia-llegada`:

1. **Llegada** (horarios, dirección, distance CDMX, taxis aeropuerto)
2. **Renta de camionetas y maxivan** (links proveedores)
3. **Compras de víveres y bebidas** (servicio opcional + supermercados con maps)
4. **Ideas para su menu** (calculadora costo + ejemplos platillos)
5. **Servicios incluidos y adicionales** (qué incluye precio, qué cobra extra)
6. **Qué hay en la casa y qué traer** (inventory + recomendaciones)
7. **Tours y actividades** (yates, laguna, taxco)
8. **Reglas de la casa y seguridad** (rules + security info)

### Adaptations for RdM (4 properties)

| Section | Adaptation |
|---|---|
| Llegada | Same (all 4 properties same area Pie de la Cuesta) |
| Renta camionetas | Same |
| Compras | Same supermarkets, mention service per property (chef RdM/Combinada included) |
| Menu | RdM/Combinada chef incluido vs Morenas opcional vs Huerta cabin-style |
| Servicios | Tabla diferenciada per property |
| Qué hay en la casa | Generic + tabla per property differences |
| Tours | Same |
| Reglas | Same + WiFi 99 Mbps RdM mention + Huerta animals (3 chivos, 3 borregos) |

### Implementation approach

Build as Astro components for reusability + maintenance:

```
apps/web/src/pages/guia-llegada.astro                 ← main page
apps/web/src/pages/como-llegar.astro                  ← redirect or alias
apps/web/src/components/guia-llegada/
  ├── HorarioLlegada.astro       (3PM check-in, 11AM check-out)
  ├── DireccionMapa.astro        (address + Google Maps + Waze)
  ├── TransportePicker.astro     (taxis, camionetas, autobus options)
  ├── ComprasViveres.astro       (servicio + supermarkets list)
  ├── CalculadoraViveres.tsx     (React, interactive cost estimate)
  ├── MenuIdeas.astro             (platillos populares, precio mercado)
  ├── ServiciosTabla.astro       (4 properties × incluido/extra)
  ├── QueTraer.astro             (inventario + recomendaciones)
  ├── ToursActividades.astro     (yates, laguna, taxco con maps)
  └── ReglasSeguridad.astro      (rules + security)
```

### Page structure (`/guia-llegada.astro`)

```astro
---
import BaseLayout from '@/layouts/BaseLayout.astro';
import HorarioLlegada from '@/components/guia-llegada/HorarioLlegada.astro';
import DireccionMapa from '@/components/guia-llegada/DireccionMapa.astro';
import TransportePicker from '@/components/guia-llegada/TransportePicker.astro';
import ComprasViveres from '@/components/guia-llegada/ComprasViveres.astro';
import CalculadoraViveres from '@/components/guia-llegada/CalculadoraViveres.tsx';
import MenuIdeas from '@/components/guia-llegada/MenuIdeas.astro';
import ServiciosTabla from '@/components/guia-llegada/ServiciosTabla.astro';
import QueTraer from '@/components/guia-llegada/QueTraer.astro';
import ToursActividades from '@/components/guia-llegada/ToursActividades.astro';
import ReglasSeguridad from '@/components/guia-llegada/ReglasSeguridad.astro';
import { webpageLd } from '@/lib/schema-org';

const SITE = import.meta.env.SITE_URL ?? 'https://rincondelmar.club';
---

<BaseLayout
  title="Guía de llegada — Rincón del Mar"
  description="Todo lo que necesitas saber para tu estancia en Pie de la Cuesta, Acapulco. Horarios, llegada, compras, menu, reglas."
  jsonLd={webpageLd({
    url: `${SITE}/guia-llegada`,
    title: 'Guía de llegada — Rincón del Mar',
    description: 'Guía completa para huéspedes.',
  })}
>
  <main class="guia-llegada">
    <header class="hero">
      <h1>Listos para la playa?</h1>
      <p class="subtitle">Todo lo que necesitas saber para tu estancia en Pie de la Cuesta, Acapulco.</p>
    </header>

    <nav class="toc" aria-label="Índice">
      <h2>Índice rápido</h2>
      <ol>
        <li><a href="#llegada">Llegada y dirección</a></li>
        <li><a href="#transporte">Transporte</a></li>
        <li><a href="#compras">Compras de víveres</a></li>
        <li><a href="#menu">Menu e ideas</a></li>
        <li><a href="#servicios">Servicios incluidos</a></li>
        <li><a href="#traer">Qué hay en la casa</a></li>
        <li><a href="#actividades">Tours y actividades</a></li>
        <li><a href="#reglas">Reglas y seguridad</a></li>
      </ol>
    </nav>

    <section id="llegada">
      <HorarioLlegada />
      <DireccionMapa />
    </section>
    
    <section id="transporte"><TransportePicker /></section>
    
    <section id="compras">
      <ComprasViveres />
      <CalculadoraViveres client:idle />
    </section>
    
    <section id="menu"><MenuIdeas /></section>
    
    <section id="servicios"><ServiciosTabla /></section>
    
    <section id="traer"><QueTraer /></section>
    
    <section id="actividades"><ToursActividades /></section>
    
    <section id="reglas"><ReglasSeguridad /></section>

    <footer class="cta-footer">
      <h2>¿Listos para reservar o tienes dudas?</h2>
      <a href="https://wa.me/525570618798" class="cta-whatsapp">
        💬 Escríbenos por WhatsApp
      </a>
    </footer>
  </main>
</BaseLayout>

<style>
  .guia-llegada {
    max-width: 800px;
    margin: 0 auto;
    padding: 24px 16px;
    line-height: 1.6;
  }
  
  .hero { margin-bottom: 32px; }
  .hero h1 { font-size: 32px; margin: 0 0 8px; }
  .subtitle { color: #666; font-size: 16px; margin: 0; }
  
  .toc {
    background: #f5f5f0;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 32px;
  }
  .toc h2 { font-size: 14px; text-transform: uppercase; margin: 0 0 8px; color: #666; }
  .toc ol { margin: 0; padding-left: 20px; }
  .toc li { margin-bottom: 4px; }
  .toc a { color: #00A19A; text-decoration: none; font-size: 14px; }
  .toc a:hover { text-decoration: underline; }
  
  section {
    margin-bottom: 48px;
    scroll-margin-top: 80px;
  }
  
  .cta-footer {
    text-align: center;
    margin-top: 48px;
    padding: 32px 20px;
    background: #f5f5f0;
    border-radius: 12px;
  }
  
  .cta-whatsapp {
    display: inline-block;
    padding: 12px 28px;
    background: #25D366;
    color: white;
    border-radius: 24px;
    text-decoration: none;
    font-weight: 600;
    margin-top: 12px;
  }
</style>
```

### Content data source (per Alex feedback)

- **Base text**: legacy `rincondelasmorenas.club/guia-llegada` adapted
- **Differences**: explicit per property where relevant (chef incluido, capacity, etc.)
- **Pricing references**: keep from legacy but update if expired
- **Photos**: use existing R2 assets from `rdm-knowledge` or fallback to legacy URLs initially

### Component example — `ServiciosTabla.astro`

```astro
---
const properties = [
  {
    name: 'Rincón del Mar',
    cap: 30,
    chef: 'Incluido',
    cocinera: 'Incluida',
    mozo: 'Incluido',
    notes: 'Servicio completo de 8AM a 6PM',
  },
  {
    name: 'Las Morenas',
    cap: 28,
    chef: 'Opcional ($1,000-1,500/día)',
    cocinera: 'Incluida',
    mozo: 'Incluido',
    notes: 'Cocinera + mozo incluidos',
  },
  {
    name: 'Combinada (RdM + Morenas)',
    cap: 58,
    chef: 'Incluido',
    cocinera: 'Incluida',
    mozo: 'Incluido',
    notes: 'Para grupos grandes',
  },
  {
    name: 'Huerta Cocotera',
    cap: 12,
    chef: '—',
    cocinera: 'Opcional',
    mozo: 'Opcional',
    notes: 'Cabaña self-service, alberca infinity 3×2m, asador argentino',
  },
];
---

<h2>Servicios por propiedad</h2>

<p>Cada propiedad tiene un servicio diferente según el grupo y la experiencia que buscas:</p>

<div class="servicios-grid">
  {properties.map(p => (
    <article class="property-card">
      <header>
        <h3>{p.name}</h3>
        <span class="cap">Hasta {p.cap} personas</span>
      </header>
      <ul>
        <li><strong>Chef:</strong> {p.chef}</li>
        <li><strong>Cocinera:</strong> {p.cocinera}</li>
        <li><strong>Mozo:</strong> {p.mozo}</li>
      </ul>
      <p class="notes">{p.notes}</p>
    </article>
  ))}
</div>

<h3>Servicios adicionales</h3>
<ul>
  <li>Compra de insumos antes de su llegada</li>
  <li>Masajes ($450 por sesión)</li>
  <li>Fogatas (~$250)</li>
  <li>Cocos ($20)</li>
  <li>Cena o evento en la playa</li>
  <li>Horario especial personal antes de 8AM o después de 6PM</li>
</ul>

<style>
  .servicios-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    margin: 20px 0;
  }
  
  @media (min-width: 600px) {
    .servicios-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  .property-card {
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 16px;
  }
  
  .property-card header h3 { margin: 0 0 4px; font-size: 16px; }
  .cap { color: #666; font-size: 13px; }
  .property-card ul { padding-left: 18px; margin: 12px 0; }
  .property-card ul li { font-size: 14px; margin-bottom: 4px; }
  .notes { font-size: 13px; color: #555; margin: 8px 0 0; font-style: italic; }
</style>
```

### Other components — abbreviated

CC implements remaining components following same pattern:
- `HorarioLlegada.astro`: 3PM check-in, 11AM check-out, restaurantes para esperar
- `DireccionMapa.astro`: Address + Google Maps embed/link + Waze
- `TransportePicker.astro`: taxis aeropuerto, autobús opciones, camionetas links
- `ComprasViveres.astro`: servicio opcional + supermarkets con maps
- `CalculadoraViveres.tsx`: React component cost estimate (3 plans × N personas × N noches)
- `MenuIdeas.astro`: platillos populares grid + lista
- `QueTraer.astro`: inventory + cosas que llevar
- `ToursActividades.astro`: yates, laguna, taxco
- `ReglasSeguridad.astro`: house rules + security info

### Tests

`apps/web/tests/guia-llegada.test.ts`:
- All 8 section anchors present
- TOC links match section IDs
- WhatsApp CTA link valid
- Calculadora components render

### Acceptance criteria Part J

- /guia-llegada returns 200
- 8 sections rendered (matching legacy structure)
- 4 properties differences clearly shown (services table)
- Calculadora víveres interactive
- Mobile-friendly throughout
- Internal TOC navigation works
- WhatsApp CTA footer
- SEO meta tags set

**Commit**:
```
feat(guia-llegada): rich content replacing placeholder

Replaces 180-line placeholder with 8 sections adapted from legacy
rincondelasmorenas.club/guia-llegada (already known UX, used by guests).

Adaptations for RdM (4 properties):
- Services table per property (chef incluido vs opcional)
- Same supermarket/transport recommendations
- Calculadora víveres interactive (3 plans)
- Mobile-first responsive design

Componentized for future maintenance:
- 9 .astro components + 1 .tsx interactive component

Links already shared via AirBnB + WhatsApp templates → guests now get
real content instead of placeholder.

Refs: thread/109 §4
```

---

## §5 — Push + PR + Merge

```bash
git push origin feat/small-items-wave-2

gh pr create \
  --title "feat(wave-2): 4 small items — G+H+I+J" \
  --body "Per thread/109.

4 atomic commits:
- G: Phone fallback + wa.me clickable links
- H: /admin/airbnb-content 500 fix
- I: /proxReservas modern clone (staff temp tool)
- J: /guia-llegada rich content (replace placeholder)

Total ~10-13h CC.

Refs: thread/109"

gh pr merge <N> --squash --delete-branch
```

## §6 — Deploy + smoke tests

```bash
# Apply migrations (if Part H needed any)
wrangler d1 migrations apply rincon --remote

# Deploy worker
wrangler deploy

# Smoke tests:

# Part G — Phone field
curl -I https://rincondelmar.club/admin/bookings  # 302 (auth)
# Browser: verify drawer shows phone clickable

# Part H — airbnb-content
curl -I https://rincondelmar.club/admin/airbnb-content  # 200/302
# Browser: Alex tests as logged in

# Part I — proxReservas
curl -I "https://rincondelmar.club/proxReservas.php?pass=vivamexico"  # 200
curl -I "https://rincondelmar.club/proxReservas.php?pass=wrong"       # 403

# Part J — guia-llegada
curl -I https://rincondelmar.club/guia-llegada  # 200
# Browser: verify all 8 sections render
```

============================================================
DEFAULTS
============================================================

- Commit format: Conventional Commits, atomic per part (4 commits min)
- Encoding: UTF-8 file contents
- Branch: feat/small-items-wave-2
- Squash merge with --delete-branch
- Phone normalization library reusable (used by G + I)
- Wrangler secret for staff pass (production via secret put, dev via vars)
- Mobile-first design throughout
- Reuse existing patterns from PR #82 / thread/108

============================================================
OUT OF SCOPE (NO HACER)
============================================================

- ❌ Reply/messaging in /proxReservas (read-only tool, future PWA scope)
- ❌ Edit bookings in /proxReservas
- ❌ Track view metrics for guests on /guia-llegada
- ❌ Multi-language /guia-llegada (ES only MVP)
- ❌ Replace legacy PHP /proxReservas.php at rincondelasmorenas.club (separate site)
- ❌ Touch /admin/conv (separate concerns)
- ❌ Touch /admin/inbox (thread/108)
- ❌ Auth for /proxReservas (pass via URL OK for staff temp tool)
- ❌ Photo gallery in /guia-llegada (text + minimal images MVP)
- ❌ Touch rdm-platform repo

============================================================
EXTERNAL STATE (informational)
============================================================

- Legacy `rincondelasmorenas.club/guia-llegada` STILL LIVE (different site, don't touch)
- Karina has `content_editor` role for /admin/airbnb-content (fix preserves access)
- /proxReservas.php pass `vivamexico` shared in WhatsApp staff group (don't expose in logs)
- AirBnB obscured phones may appear as masked "+1-555-XXX-XXXX" — handle gracefully
- Some bookings have empty firstName (AirBnB cap) — display "(sin nombre)" fallback
- D1 latest migration after thread/108: 0033 (next 0034)

============================================================
SI TE ATORAS
============================================================

- /admin/airbnb-content 500 root cause unclear after wrangler tail: STOP, report log output for Alex/WC review
- Phone normalization edge case (e.g. AirBnB masked number): document + fallback gracefully, do NOT crash
- /proxReservas pass param URL encoding issue: use URLSearchParams + decodeURIComponent
- Legacy /guia-llegada content has expired pricing references: keep structure, update prices via Alex Q in commit body
- Astro component import errors: check file extensions (.astro vs .tsx) match content
- Calculadora víveres interactive — start with simple component, iterate
- pnpm test breaking unrelated: investigate, may need fixture update
- Anything unexpected: STOP, report

============================================================
REPORTAR AL FINAL (thread/110-cc-bot-small-items-wave-2-complete.md)
============================================================

Por cada part G-J:
1. Files changed (path + line count)
2. Commit SHA
3. Tests added
4. Acceptance criteria check (pass/fail)

Overall:
5. PR # + merge SHA + URL
6. Worker deploy result
7. Smoke test results per endpoint
8. Browser verification by Alex pending list
9. Any partial implementations
10. Status for next priority

---

**WC standing by. CC executes AFTER thread/108 ack. Single sprint, single PR, 4 atomic commits.**

— WC, 2026-05-19
