# Thread 84 — WC: build spec /admin/bookings Gantt view

**Date**: 2026-05-16
**Author**: WC (with Alex)
**To**: CC-Bot
**Re**: New admin page — bookings Gantt
**Priority**: P1 (after V6 cutover lands)
**Status**: 🟢 Spec ready

---

## TL;DR

Build `/admin/bookings` — horizontal Gantt-style calendar showing all bookings across 4 properties + Combinada overlay. Read-only MVP. Each booking shows surname + group size: `Pérez (16)`, `García (25)`, `Wedding Soto (40)`.

Spec: `cc-instructions-bot/2026-05-16-admin-bookings-gantt-build-spec.md`

---

## Why now

Alex currently checks bookings in Beds24 panel — slow, no consolidated view, no internal metadata. D1 already has unified `beds24_bookings` table syncing all channels (multi-canal cutover completed 2026-05-12). Just needs UI.

---

## What's included

- 4 property rows (RdM, Morenas, Combinada overlay, Huerta)
- Color-coded by channel (Airbnb orange, Booking.com blue, Direct green)
- Visual flags: ★ event, 🐶 pet, ⚠ issue, 💰 pending payment
- View zoom: Day / Week / Month (default) / Quarter
- Filters: channel, property
- Today indicator
- Header KPIs: occupancy %, revenue MXN, pending payments
- Hover tooltip + click modal with Beds24 link
- Readonly user support (consistent with /admin/conv)

---

## What's OUT of scope (deferred)

- Drag-and-drop edit (writes to Beds24 — high risk)
- Mobile design (tablet+ only)
- Real-time updates
- CSV/PDF export
- Multi-property comparison charts

---

## Effort estimate

~16-24h CC. Single PR.

---

## Dependencies

- V6 cutover should complete first (avoid stacking 2 risky changes)
- No other blockers — D1 schema + data are already production

---

## Coordinación

Spec self-contained. CC-Bot proceeds after V6 lands at 100%. Alex available for visual tweaks after v1 renders.

---

**WC standing by.**
— WC, 2026-05-16
