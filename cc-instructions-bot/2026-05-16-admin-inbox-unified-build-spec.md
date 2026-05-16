# Build spec — `/admin/inbox` unified inbox

**Date**: 2026-05-16
**Author**: WC (with Alex)
**Owner**: CC-Bot
**Mode**: DoIt
**Priority**: P1 — after V6 cutover + after admin/bookings (sequence)
**Estimated effort**: 12-16h CC

---

## TL;DR

Build `/admin/inbox` as a unified operational view consolidating three signal sources:

1. **Bot conversations** (`conversations` table) — active WhatsApp sessions, paused, etc.
2. **Beds24 inbox** (`bot_messages_inbox`) — guest messages from Airbnb/Booking/Direct synced via Beds24
3. **Handoffs/Escalations** (`human_handoff_log`) — open escalations waiting for human response

Read-only MVP with filters and jump-to-action links (no reply integration in v1). Color-coded by state. Click → opens existing `/admin/conv` for actions.

---

## Why this exists

Alex + Karina currently track guest interactions across:
- WhatsApp (via ManyChat dashboard)
- Beds24 messages (via Beds24 panel)
- Telegram notifications (escalation alerts)
- D1 directly via `/admin/conv` (one subscriber at a time)

No consolidated "what needs my attention NOW" view. The inbox solves that.

---

## Route + access

- Route: `/admin/inbox`
- Auth: `isAdmin(env, user?.email) || isAdminReadonly(env, user?.email)`
- Readonly: same view, no destructive actions (consistent with `/admin/conv` PR A7.7.4)
- Add to `/admin/index.astro` cards
- **Priority order in /admin/index**: place above `bot-metrics`, below `airbnb-content`

---

## Visual design

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ /admin/inbox · 5 items need attention                                          │
│                                                                                │
│ Filters: [All▼] [Bot conversations] [Beds24 msgs] [Escalations]              │
│          Status: [▼ All] Channel: [▼ All] Time: [Last 24h ▼] Search: [_____]│
│                                                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🔴 ESCALATED · 1h 24m waiting                                                  │
│ Luis Pérez · +52 55 1234 5678 · WhatsApp                                       │
│ Last: "no me sirve el link, quiero hablar con alguien"                         │
│ Property: Huerta Cocotera · Intent: complaint                                  │
│ Actions: [Open conv] [Mark responded] [Resolve]                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🟡 BOT PAUSED · 1h 12m remaining                                               │
│ María García · +52 55 9876 5432 · WhatsApp                                     │
│ Last: "déjame consultar con mi familia"                                        │
│ Property: Las Morenas · Turn: 7 · Paused by: Karina                           │
│ Actions: [Open conv] [Unpause now] [Extend pause]                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🟠 STALLED · No reply for 3h 45m                                               │
│ Juan López · +52 81 5555 1234 · WhatsApp                                       │
│ Last (bot): "Te paso el link a tarifas: rincondelmar.club/#tarifas"            │
│ Property: Rincón del Mar · Turn: 4 · Intent: precios                          │
│ Actions: [Open conv] [Mark resolved]                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🟢 BEDS24 UNREAD · 28m old                                                     │
│ Booking 4827193 · Roberto Hernández (Airbnb)                                   │
│ Last (guest): "qué incluye el servicio de chef?"                               │
│ Property: Rincón del Mar · Arrival: 2026-06-12                                 │
│ Actions: [Open Beds24] [View booking detail]                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ ⚠ CRITICAL KEYWORD · Beds24 · 2h old                                           │
│ Booking 4825002 · Ana Soto (Direct)                                           │
│ Last (guest): "tengo un problema con la alberca, hay que cancelar"            │
│ Property: Las Morenas · In stay · Day 2 of 4                                  │
│ Actions: [Open Beds24] [Trigger escalation]                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ ✅ RESOLVED · Today 14:30                                                       │
│ Ana Vega · +52 55 7777 8888 · WhatsApp                                         │
│ Outcome: Booking confirmed CLA-XX9P3                                           │
│ [Show 12 more resolved today ▼]                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### States

| State | Color | Source table | Trigger condition |
|---|---|---|---|
| 🔴 **Escalated** | red #DC2626 | `human_handoff_log` | `human_responded_at IS NULL` |
| 🟡 **Bot paused** | yellow #FBBF24 | `conversations` | `bot_paused_until > now()` |
| 🟠 **Stalled** | orange #F97316 | `conversations` | Bot conversation, `last_active < now-2h` AND `turn_count >= 2` AND no handoff |
| 🟢 **Active bot** | green #10B981 | `conversations` | `last_active > now-30min` AND `bot_paused_until IS NULL` |
| 🟢 **Beds24 unread** | green #10B981 | `bot_messages_inbox` | `read_flag=0 AND source='guest'` AND no recent host reply |
| ⚠ **Critical keyword** | red bg w/ ⚠ | `bot_messages_inbox` | `has_keywords_critical=1` AND `read_flag=0` |
| ✅ **Resolved** | gray #9CA3AF | various | Conversation ended, booking confirmed, or human_responded_at set |

### Priority ordering (default sort)

Top to bottom, descending urgency:

1. ⚠ Critical keywords (Beds24) — unread + has_keywords_critical=1
2. 🔴 Escalated — oldest first (longest waiting)
3. 🟡 Bot paused — sorted by `bot_paused_until` ascending (soonest expiring first)
4. 🟠 Stalled — oldest stalled first
5. 🟢 Active bot — last_active descending (most recent first)
6. 🟢 Beds24 unread — message_time descending
7. ✅ Resolved — collapsed by default (click to expand)

User can override sort via column header click (last_active, time_waiting, etc.).

---

## Filters

- **Type**: All / Bot conversations / Beds24 msgs / Escalations
- **Status**: All / Escalated / Paused / Stalled / Active / Unread / Critical / Resolved
- **Channel**: All / WhatsApp / Airbnb / Booking.com / Direct / Web
- **Time**: Last 24h / Last 7d / Last 30d / All time
- **Search**: substring match on `subscriber_id`, `guest.name`, `phone_e164`, `message_text`

URL params:
- `?type=bot|beds24|escalations|all`
- `?status=escalated|paused|stalled|active|unread|critical|resolved`
- `?channel=whatsapp|airbnb|booking|direct|web|all`
- `?time=24h|7d|30d|all`
- `?q=search_term`

Filters compose. Default load: type=all, status=all, time=24h.

---

## Top-of-page summary

```
5 need attention now:
  · 1 critical keyword (⚠)
  · 1 escalated 1h+
  · 1 stalled 3h+
  · 2 Beds24 unread

12 active bot conversations
+ 18 resolved today
```

This is the "scan in 3 seconds" header. Counts driven by current filters (24h default).

---

## Hover/click behaviors

### Click on item row
- **Bot conversation** → jumps to `/admin/conv?sub={subscriber_id}` (existing page, handles pause/unpause/reset)
- **Beds24 message** → opens Beds24 in new tab: `https://www.beds24.com/control3.php?action=editbooking&bookid={booking_id}`
- **Escalation** → jumps to `/admin/conv?sub={subscriber_id}` + shows handoff context

### Action buttons per row (visible on hover, hidden on row click)

| Action | When applicable | Behavior |
|---|---|---|
| **Open conv** | Bot conversations, escalations | Navigate to `/admin/conv?sub=...` |
| **Mark responded** | Escalations | POST `/api/admin/handoff/{id}/respond` → sets `human_responded_at=now()` |
| **Resolve** | Stalled, active bot | POST `/api/admin/conv/{sub}/resolve` (NEW endpoint, see below) |
| **Unpause now** | Bot paused | POST `/api/admin/conv/{sub}/unpause` (existing endpoint, /admin/conv has it) |
| **Extend pause** | Bot paused | Modal: select 30m/1h/2h/4h → POST `/api/admin/conv/{sub}/pause?duration=Xh` |
| **Open Beds24** | Beds24 messages | Open Beds24 panel in new tab |
| **Trigger escalation** | Beds24 messages w/ critical keyword | POST `/api/admin/handoff/trigger` (NEW endpoint) — creates handoff_log row + sends Telegram |

**Readonly users**: only "Open conv" and "Open Beds24" visible. Destructive actions hidden.

---

## Data queries

### Query 1 — bot conversations

```sql
SELECT
  c.subscriber_id,
  c.last_active,
  c.turn_count,
  c.last_intent,
  c.bot_paused_until,
  c.active_agent,
  c.last_room_id,
  c.updated_at,
  -- Get last message text from history (parsed)
  c.history
FROM conversations c
WHERE c.last_active > strftime('%s', 'now', '-1 day')   -- last 24h filter (parameterized)
ORDER BY c.last_active DESC;
```

Parsing `c.history` (concatenated USER/ASSISTANT turns): TypeScript extracts last turn for preview.

### Query 2 — Beds24 unread messages

```sql
SELECT
  bmi.message_id,
  bmi.booking_id,
  bmi.room_id,
  bmi.channel,
  bmi.source,
  bmi.message_text,
  bmi.message_time,
  bmi.has_keywords_critical,
  bmi.read_flag,
  bb.id AS our_booking_id,
  bb.arrival,
  bb.departure,
  bb.status AS booking_status,
  g.name AS guest_name
FROM bot_messages_inbox bmi
LEFT JOIN beds24_bookings bb ON bb.beds24_booking_id = bmi.booking_id
LEFT JOIN guests g ON g.id = bb.guest_id
WHERE bmi.read_flag = 0
  AND bmi.source = 'guest'
  AND bmi.message_time > strftime('%s', 'now', '-7 days')
ORDER BY bmi.has_keywords_critical DESC, bmi.message_time DESC;
```

### Query 3 — open escalations

```sql
SELECT
  hhl.id,
  hhl.subscriber_id,
  hhl.notified_at,
  hhl.intent,
  hhl.property,
  hhl.reminder_1h_sent_at,
  hhl.reminder_8h_sent_at,
  c.last_active,
  c.history,
  c.last_intent AS conv_intent
FROM human_handoff_log hhl
LEFT JOIN conversations c ON c.subscriber_id = hhl.subscriber_id
WHERE hhl.human_responded_at IS NULL
  AND hhl.notified_at > datetime('now', '-7 days')
ORDER BY hhl.notified_at ASC;
```

### Derived state logic (TypeScript, server-side)

```typescript
type InboxItemState = 'escalated' | 'paused' | 'stalled' | 'active_bot' | 'beds24_unread' | 'critical' | 'resolved';

function deriveState(item: any): InboxItemState {
  // 1. Critical keywords win
  if (item.has_keywords_critical && item.read_flag === 0) return 'critical';
  
  // 2. Has open escalation
  if (item.handoff_pending) return 'escalated';
  
  // 3. Bot paused
  if (item.bot_paused_until && new Date(item.bot_paused_until) > new Date()) return 'paused';
  
  // 4. Stalled (bot turn pending for >2h)
  const ageMin = (Date.now() / 1000 - item.last_active) / 60;
  if (item.turn_count >= 2 && ageMin > 120 && !item.bot_paused_until) return 'stalled';
  
  // 5. Active bot (recent)
  if (ageMin < 30) return 'active_bot';
  
  // 6. Beds24 unread
  if (item.read_flag === 0 && item.source === 'guest') return 'beds24_unread';
  
  return 'resolved';
}
```

---

## New worker endpoints (CC adds)

### `POST /api/admin/handoff/{id}/respond`

Marks handoff as responded.

```typescript
// In worker
async function markHandoffResponded(env: Env, handoffId: number): Promise<Response> {
  const now = new Date().toISOString();
  await env.DB.prepare(
    `UPDATE human_handoff_log
     SET human_responded_at = ?,
         response_latency_seconds = (strftime('%s', ?) - strftime('%s', notified_at))
     WHERE id = ? AND human_responded_at IS NULL`
  ).bind(now, now, handoffId).run();
  return new Response(JSON.stringify({ ok: true }), { status: 200 });
}
```

### `POST /api/admin/conv/{sub}/resolve`

Marks conversation as resolved manually.

```typescript
// Simple version: append a system note to conversation history
async function resolveConversation(env: Env, sub: string): Promise<Response> {
  await env.DB.prepare(
    `UPDATE conversations
     SET history = history || '\n[ADMIN: resolved manually at ' || datetime('now') || ']',
         updated_at = strftime('%s', 'now')
     WHERE subscriber_id = ?`
  ).bind(sub).run();
  return new Response(JSON.stringify({ ok: true }), { status: 200 });
}
```

### `POST /api/admin/handoff/trigger`

Manually trigger escalation from a Beds24 message (when critical keyword detected but no handoff exists).

```typescript
async function triggerEscalation(env: Env, body: { booking_id: number; reason: string }): Promise<Response> {
  // Insert into human_handoff_log
  // Trigger notifyHumanHandoff() to send Telegram
  // Return new handoff id
}
```

All endpoints: admin-only (existing `x-admin-secret` proxy pattern from `/admin/conv`).

---

## Tech stack

- **Astro page**: `apps/web/src/pages/admin/inbox.astro`
- **React island** for interactive list (filters, sort, action buttons) — same pattern as `/admin/conv`
- **Server-side rendering**: `export const prerender = false`
- **D1 queries** via `Astro.locals.runtime.env.DB`
- **Worker endpoints** in `apps/worker-bot/src/admin/`
- **Tailwind** for styling
- Reuse `AdminLayout`

---

## Acceptance criteria

- [ ] Route `/admin/inbox` exists, admin/readonly auth
- [ ] 3 source types unified in single list (bot conv, Beds24, escalations)
- [ ] 7 states render with correct colors and labels
- [ ] Priority ordering correct (critical → escalated → paused → stalled → active → unread → resolved)
- [ ] Filters work: type, status, channel, time, search
- [ ] URL params reflect filters and reload preserves state
- [ ] Top-of-page summary counts accurate
- [ ] Hover shows action buttons
- [ ] Click on row navigates to appropriate destination
- [ ] "Mark responded" sets `human_responded_at` in D1
- [ ] "Resolve" updates conversation
- [ ] "Trigger escalation" creates handoff + sends Telegram
- [ ] "Unpause now" and "Extend pause" work (reuse existing endpoints)
- [ ] Readonly users see no destructive actions
- [ ] Performance: page loads <2s with up to 50 active items
- [ ] Critical keyword items render with red bg + ⚠ icon
- [ ] Resolved section collapsible (default collapsed)
- [ ] Page added to `/admin/index.astro` cards above bot-metrics

---

## Out of scope (DO NOT do)

- ❌ Reply integration (sending WhatsApp messages from inbox) — Phase 2
- ❌ Reply integration from inbox to Beds24 — Phase 2 (Beds24 has POST API but not used yet)
- ❌ Real-time updates / SSE / polling — page refresh button is fine in MVP
- ❌ Bulk actions (select multiple, resolve all) — Phase 2
- ❌ Notifications (browser push, email) — Phase 2
- ❌ Mobile-first design — tablet+ only
- ❌ Customizable views / saved filters
- ❌ Assigning items to specific operators (Karina vs Alex)
- ❌ SLA timers / alerting on items waiting too long

---

## Definition of Done

- [ ] PR opened against main, branch `feat/admin-inbox-unified`
- [ ] All acceptance criteria pass manual QA
- [ ] Self-review of diff
- [ ] 3 new worker endpoints implemented + tested
- [ ] Sample data renders correctly: at least 1 of each state visible
- [ ] Test escalate flow end-to-end: trigger escalation → handoff row created → Telegram sent
- [ ] Test mark-responded flow: open escalation → mark responded → status changes to resolved
- [ ] Readonly user view tested (no destructive buttons visible)
- [ ] Page added to `/admin/index.astro`
- [ ] Thread `XX-cc-bot-admin-inbox-built.md` published with screenshots

---

## Future Phase 2 (separate PR, NOT this MVP)

After v1 ships and Alex/Karina use for 2-3 weeks:

- Reply integration: send WhatsApp via Cloud API directly (replaces "Open Beds24" for Beds24 messages)
- Bulk actions
- SLA timers (red border if waiting >1h, etc.)
- Notifications (browser, email)
- Operator assignment
- Saved filter views

Open separate spec when v1 has 2+ weeks of real usage.

---

## Anti-patterns

- ❌ Don't poll Beds24 API from the page — use D1 cache (synced every 5 min)
- ❌ Don't denormalize state into a `last_state` column — derive on read
- ❌ Don't write to `human_handoff_log` from Astro page — go through worker endpoint
- ❌ Don't try to make this realtime — refresh button is fine
- ❌ Don't add reply UI "just stubbed" — keep MVP scope tight

---

## If stuck >30 min

- State derivation logic getting tangled → write 10 unit tests on `deriveState()` first, then build UI
- Filter combinations breaking → simplify to 1 filter at a time, compose later
- Beds24 message text rendering wrong (truncation, encoding) → use a `<pre>` element with max-height + scroll

---

## Sequence relative to other PRs

```
V6 prompt deploy (in flight) ──────► 100% cutover ──────►
                                                          │
                                       Pet fee fix       │
                                       faqs.json ────────┤
                                                          │
                                       /admin/bookings ───┤
                                       Gantt (PR A8.X)    │
                                                          │
                                       /admin/inbox ──────┘
                                       (this PR, A8.Y)
```

Inbox waits for bookings Gantt to ship first because:
- Bookings is faster to build (fewer states, simpler UI)
- Inbox builds on patterns established by bookings (same Astro+React island setup)
- Sequencing reduces parallel CC work

---

**End of spec. CC-Bot starts after bookings Gantt PR lands.**
