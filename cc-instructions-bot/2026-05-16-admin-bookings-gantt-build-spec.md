# Build spec — `/admin/bookings` Gantt view

**Date**: 2026-05-16
**Author**: WC (with Alex)
**Owner**: CC-Bot
**Mode**: DoIt
**Priority**: P1 — after V6 cutover lands
**Estimated effort**: 16-24h CC

---

## TL;DR

Build `/admin/bookings` as a horizontal Gantt-style calendar showing all bookings across 4 properties + Combinada overlay. Read-only MVP. Color-coded by channel. Each booking shows guest surname + group size (e.g. "Pérez (16)"). Filterable by view (day/week/month/quarter) and channel.

---

## Why this exists

Alex currently checks bookings via Beds24 admin panel — slow, no consolidated view across channels, no internal metadata (guest history, lead source, flags). D1 already has unified `beds24_bookings` table syncing all channels. We need a fast internal view to:

- Plan staff schedules
- Spot occupancy gaps
- Identify conflicts (Combinada vs individual villa)
- Flag issue bookings (Luis-type, complaints, pending payments)
- Visualize seasonality

---

## Route + access

- Route: `/admin/bookings`
- Access: `isAdmin(env, user?.email) || isAdminReadonly(env, user?.email)`
- Readonly users: view only, no actions (consistent with `/admin/conv` PR A7.7.4 pattern)
- Add to `/admin/index.astro` cards (mark `Live · PR A7.X`)

---

## Visual design (Gantt)

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ /admin/bookings                                                                │
│                                                                                │
│ View: [Day] [Week] [Month*] [Quarter]   Channel: [▼ All]   Today: [< May 16 >]│
│                                                                                │
│ Occupancy this month: ████████████░░░░░░ 67%  (RdM 71% · Morenas 80%...)      │
│ Revenue (MXN):       $542,800       Pending payments: $48,200 across 3 bookings│
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│              May 16  17  18  19  20  21  22  23  24  25  26  27  28  29  30  │
│              ─────────────────────────────────────────────────────────────── │
│              Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed     │
│ RdM          [══Pérez (16)══][══Hernández (8)═══]    [═══González (22)═══] │
│              🟠 airbnb       🟢 direct               🟠 airbnb               │
│                                                                                │
│ Morenas              [══García (25)══] [═══Soto WEDDING (40) ★═══]          │
│                       🔵 booking      🟢 direct                              │
│                                                                                │
│ Combinada                          [══════Soto WEDDING (58) ★═══════]        │
│                                     🟢 direct · blocks RdM+Morenas           │
│                                                                                │
│ Huerta       [══Cuauh.(6)═══][══Daniela(8)═══]              [══Eric(4)═══]  │
│              🟠 airbnb        🟠 airbnb · 🐶                  🟢 direct      │
│                                                                                │
│              ┃ TODAY                                                          │
│                                                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ Legend: 🟠 Airbnb  🔵 Booking.com  🟢 Direct  🟡 Web  ★ Event  🐶 Pet  ⚠ Issue │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Row structure

Rows ordered top→bottom:
1. **RdM** (room_id 78695)
2. **Morenas** (room_id 74322)
3. **Combinada** (room_id 74316) — virtual row, overlays RdM + Morenas
4. **Huerta** (room_id 637063)

When Combinada has an active booking: shade RdM and Morenas rows with semitransparent "blocked by Combinada" pattern in those date ranges. Tooltip explains.

### Bar content

Each booking bar shows:
- **Surname + (group_size)** — e.g. `Pérez (16)`, `García (25)`, `Wedding Soto (40)`
- If surname unknown: `[Direct booking] (N)` or `[Anonymous] (N)`
- Channel emoji underneath
- Flags (★ event, 🐶 pet, ⚠ issue) inline after group_size

Bar height = single row line (don't stack — if 2 bookings same day same villa, that's an error worth flagging).

Bar width = (departure - arrival) in date units of current view.

### Colors by channel

| Channel | Bar color | Emoji |
|---|---|---|
| `airbnb` | orange #FF5A5F | 🟠 |
| `booking_com` | blue #003580 | 🔵 |
| `direct` | green #34A853 | 🟢 |
| `web` | yellow #FBBC04 | 🟡 |
| `whatsapp_direct` | green #34A853 (treat as direct visually) | 🟢 |

### Flag indicators (icons appended to bar text)

| Flag | Trigger | Icon |
|---|---|---|
| Event | `total_guests >= 30` OR `lead.tag = 'wedding'` OR notes mention boda | ★ |
| Pet | `num_pets > 0` | 🐶 |
| Issue | `guest_events` has `complaint` event OR `reviews.rating <= 2` | ⚠ |
| Pending payment | `deposit_paid = 0` AND `arrival - today < 7 days` | 💰 |
| Multi-night | `num_nights >= 7` | (visible by bar width alone) |

---

## Views (zoom levels)

| View | Date range shown | Column width |
|---|---|---|
| **Day** | Today ± 6 days (13 days total) | Wide (each day visible with hourly grid optional) |
| **Week** | Today's week ± 2 weeks (21 days) | Medium |
| **Month** | Current month + next (~60 days) | Narrow |
| **Quarter** | 90 days | Narrowest (just monthly grid) |

Default: **Month**.

URL params:
- `?view=month|week|day|quarter`
- `?date=YYYY-MM-DD` (anchor date, defaults today)
- `?channel=airbnb|booking_com|direct|web|all` (filter)
- `?property=rdm|morenas|combinada|huerta|all` (filter)

`prev`/`next` buttons advance by view's date range.

`Today` button jumps to today's anchor.

---

## Header KPIs (above Gantt)

Two lines of summary stats for visible date range:

**Line 1 — Occupancy**:
- Total: `XX%` (booked nights / available nights across visible properties)
- Per property: `RdM XX% · Morenas XX% · Combinada XX% · Huerta XX%`

Calculation: 
```
total_available_nights = days_in_range * 4 properties
total_booked_nights = SUM(min(departure, range_end) - max(arrival, range_start)) per booking
occupancy_pct = booked / available
```

**Line 2 — Revenue**:
- `Revenue: $X,XXX MXN` (sum `total_amount_mxn` for bookings overlapping range)
- `Pending payments: $X,XXX MXN across N bookings` (sum where `deposit_paid = 0` AND arrival within range)

---

## Hover/click behaviors

### Hover on a bar
Tooltip shows:
- Guest full name (from `guests.name`)
- Booking ID (Beds24 + our internal `b_*`)
- Channel + confirmation code
- Dates + nights
- Adults + children + pets
- Total amount MXN + deposit paid status
- Status (`status` column)
- Property + room_id
- Click hint: "Click for detail"

### Click on a bar
Navigate to `/admin/bookings/:id` (detail page — **NOT in this MVP**, just stub the link for now, returns "Coming in PR X").

For MVP: click opens modal or expand inline showing same tooltip info + a link to Beds24 (`https://www.beds24.com/control3.php?action=editbooking&bookid=X`).

---

## Data queries

### Main query for bars

```sql
SELECT
  bb.id,
  bb.beds24_booking_id,
  bb.room_id,
  bb.channel,
  bb.channel_reservation_code,
  bb.arrival,
  bb.departure,
  bb.num_nights,
  bb.num_adults,
  bb.num_children,
  bb.num_pets,
  bb.total_guests,
  bb.total_amount_mxn,
  bb.deposit_amount_mxn,
  bb.deposit_paid,
  bb.status,
  bb.beds24_status,
  bb.special_offers_count,
  g.name AS guest_name,
  g.phone_e164 AS guest_phone,
  l.source AS lead_source,
  l.intent_tags AS lead_tags
FROM beds24_bookings bb
LEFT JOIN guests g ON g.id = bb.guest_id
LEFT JOIN leads l ON l.id = bb.lead_id
WHERE bb.arrival <= ?range_end
  AND bb.departure >= ?range_start
  AND bb.status NOT IN ('cancelled', 'no_show', 'archived')
ORDER BY bb.room_id, bb.arrival;
```

### Surname extraction (for bar label)

```typescript
function extractSurname(fullName: string | null): string {
  if (!fullName) return 'Anonymous';
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 1) return parts[0];
  // Take last word, capitalize first letter only
  return parts[parts.length - 1];
}

// Examples:
// "Luis Pérez Hernández" → "Hernández" (last word)
// "Maria García" → "García"
// "Wedding Soto" → "Soto"
// null → "Anonymous"
// "Booking.com Guest" → "Guest" (channel-default name)
```

**Edge case**: if name is a channel default like "Airbnb Guest" or starts with channel name → fallback to `[Channel] (N)` format. CC decides exact heuristic with sample data.

### Issue flag detection

```sql
-- Has complaint event
SELECT 1 FROM guest_events
WHERE booking_id = ? AND event_type IN ('complaint', 'issue_reported')
LIMIT 1;

-- Has bad review
SELECT 1 FROM reviews
WHERE reservation_code = ? AND rating <= 2
LIMIT 1;
```

### Occupancy calc

Server-side TypeScript, not SQL (cleaner with date arithmetic):

```typescript
function calcOccupancy(bookings: Booking[], range: { start: Date; end: Date }, properties: number[]) {
  const totalNights = daysBetween(range.start, range.end) * properties.length;
  let bookedNights = 0;
  for (const b of bookings) {
    const overlapStart = max(b.arrival, range.start);
    const overlapEnd = min(b.departure, range.end);
    if (overlapStart < overlapEnd) {
      bookedNights += daysBetween(overlapStart, overlapEnd);
    }
  }
  return bookedNights / totalNights;
}
```

---

## Tech stack

- **Astro** page (`apps/web/src/pages/admin/bookings.astro`)
- **Server-side rendering** (`export const prerender = false`)
- **React island** for the Gantt itself (handles view-switching state without full page reload)
- **D1** queries via Astro `Astro.locals.runtime.env.DB`
- **Tailwind** for styling
- Use `AdminLayout` component (same as other admin pages)

### Library choice for Gantt

Options:
- **Build from scratch** with CSS grid + absolute positioning — recommended for MVP, no dep
- `frappe-gantt` (3.3 KB, lightweight, well-maintained) — alternative
- `dhx-gantt` — too heavy, no

WC voto: **build from scratch**. 16-24h budget allows it, more flexibility, no dep risk. Use CSS grid for the date columns + absolute-positioned bars.

---

## Acceptance criteria

- [ ] Route `/admin/bookings` exists, requires admin/admin-readonly auth
- [ ] 4 property rows visible (RdM, Morenas, Combinada, Huerta)
- [ ] Combinada visually blocks RdM + Morenas when active (semitransparent overlay)
- [ ] Bookings render as bars with `Surname (N)` label
- [ ] Color per channel (orange/blue/green/yellow)
- [ ] Flag icons (★ 🐶 ⚠ 💰) render correctly
- [ ] View switcher works (Day/Week/Month/Quarter)
- [ ] Channel filter works
- [ ] Property filter works
- [ ] Today indicator visible
- [ ] Prev/Next navigation works per view
- [ ] Hover tooltip shows all metadata
- [ ] Click on bar shows modal/inline detail with Beds24 link
- [ ] Occupancy KPI line correct (manual spot-check on 3 dates)
- [ ] Revenue KPI line correct
- [ ] Pending payments KPI line correct
- [ ] Performance: page loads <2s for 90-day view with ~50 bookings
- [ ] Responsive: works on tablet (1024px+). Mobile out of scope.
- [ ] Readonly users see same data, no actions (consistent with `/admin/conv`)
- [ ] Added to `/admin/index.astro` cards

---

## Out of scope (DO NOT do)

- ❌ Drag-and-drop to edit bookings (writes to Beds24 — high risk, future PR)
- ❌ Create new bookings from UI (Beds24 stays source of truth)
- ❌ Cancel/modify bookings from UI
- ❌ Mobile-first design (tablet+ only in MVP)
- ❌ Real-time updates (polling/SSE) — page reload is fine
- ❌ Export to CSV/PDF (backlog)
- ❌ Color-coding by guest segment (backlog)
- ❌ Multi-property comparison charts (backlog)

---

## Definition of Done

- [ ] PR opened against main, branch `feat/admin-bookings-gantt`
- [ ] All acceptance criteria pass manual QA
- [ ] Self-review of diff
- [ ] At least 5 sample bookings render correctly in current production data
- [ ] Test with Luis booking (verify ⚠ flag for issue)
- [ ] Test with future wedding booking (verify ★ flag)
- [ ] Test with Combinada booking (verify overlay behavior)
- [ ] Page added to `/admin/index.astro`
- [ ] Thread `XX-cc-bot-admin-bookings-gantt.md` published with screenshots

---

## Possible visual tweaks (Alex decides after seeing v1)

These are likely to change after seeing actual data rendered:

- Row order (RdM → Morenas → Combinada → Huerta vs by occupancy desc)
- Color palette (Airbnb orange might be too aggressive; some hosts use blue)
- Bar height / spacing
- Whether Combinada gets its own row or is just an overlay-only on RdM+Morenas
- Whether to show cancelled bookings dimmed
- Tooltip vs modal vs side panel for detail

Build v1 with WC's defaults; Alex iterates.

---

## Anti-patterns

- ❌ Don't query Beds24 API directly from this page — D1 is the source
- ❌ Don't denormalize guest name into bookings table — JOIN is fine, ~50 rows
- ❌ Don't compute occupancy in SQL — do in TS, cleaner
- ❌ Don't add edit/cancel buttons "just in case" — out of scope
- ❌ Don't ship without testing Combinada overlap behavior

---

## If stuck >30 min

Bar positioning is the hard part. If CSS grid + absolute positioning fights you, fall back to:
- Each row is a flex container
- Each day column is fixed width
- Bars span via JS-calculated grid-column-start/end

If still stuck, switch to `frappe-gantt` library. Document the decision.

---

**End of spec. CC-Bot starts after V6 cutover completes.**
