# Thread 85 — WC: build spec /admin/inbox unified inbox

**Date**: 2026-05-16
**Author**: WC (with Alex)
**To**: CC-Bot
**Re**: New admin page — unified inbox (3 signal sources)
**Priority**: P1 (after V6 cutover + after /admin/bookings ships)
**Status**: 🟢 Spec ready

---

## TL;DR

Build `/admin/inbox` consolidating three signal sources:

1. **Bot conversations** (`conversations` table) — paused, stalled, active WhatsApp sessions
2. **Beds24 inbox** (`bot_messages_inbox`) — guest messages Airbnb/Booking/Direct
3. **Escalations** (`human_handoff_log`) — open escalations awaiting human response

Read-only MVP. Click row → jumps to existing `/admin/conv` for actions. No reply integration yet.

Spec: `cc-instructions-bot/2026-05-16-admin-inbox-unified-build-spec.md`

---

## Why now

Karina + Alex currently track guest interactions across 3 separate panels:
- ManyChat (WhatsApp sessions)
- Beds24 admin (Airbnb/Booking msgs)
- Telegram (escalation alerts)

No consolidated "what needs attention NOW" view. D1 already has all the data — just needs UI.

---

## What's included

- 7 states color-coded: 🔴 Escalated · 🟡 Paused · 🟠 Stalled · 🟢 Active bot · 🟢 Beds24 unread · ⚠ Critical keyword · ✅ Resolved
- Priority sort (critical → escalated → paused → stalled → active → unread → resolved)
- Filters: type, status, channel, time, search
- Hover actions: open conv, mark responded, resolve, unpause, extend pause, open Beds24, trigger escalation
- Top-of-page summary ("5 need attention now")
- 3 new worker endpoints (mark handoff responded, resolve conv, trigger escalation)
- Readonly user support

---

## What's OUT of scope

- ❌ Reply integration (WhatsApp send-from-inbox) — Phase 2
- ❌ Real-time updates — page refresh fine in MVP
- ❌ Bulk actions
- ❌ Notifications
- ❌ Mobile design (tablet+ only)
- ❌ Customizable views / SLA timers

Phase 2 spec written after 2+ weeks of real usage.

---

## Sequence

Don't start until:
1. ✅ V6 cutover at 100% (no overlapping risky changes)
2. ✅ `/admin/bookings` Gantt PR shipped (establishes patterns this PR reuses)

Then this PR begins.

---

## Effort estimate

~12-16h CC. Single PR.

---

## Coordinación

Spec self-contained. CC-Bot proceeds in sequence. Alex available for state ordering tweaks after v1 renders.

---

**WC standing by.**
— WC, 2026-05-16
