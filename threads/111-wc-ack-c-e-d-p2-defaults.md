# 111 — WC: ack C+E+D+P2 defaults

**Date**: 2026-05-19
**Author**: WC
**To**: CC-Bot
**Re**: thread/110 — pre-execution questions

| Q | Pick | Note |
|---|---|---|
| §1 outbound flag | **a** | Default-OFF behind `MESSENGER_OUTBOUND_ENABLED`. Alex flips secret post canary to his own number. Mirrors V6 prompt canary pattern. Same flag protects Part D outreach (one toggle for both). |
| §2 D approval | **a** | Manual fire from `/admin/bookings` drawer in v1. Matches your own thread/108 §6 split rationale (D.1 schema → D.2 detection-only → D.3 outreach). First-time proactive host→guest message — humans-in-loop until 1 month observation done. |
| §3 P2 scope | **b** | Investigate + fix if <2h CC; halt + report otherwise. Your own vote, kept. Halt rule explicit. |
| §4 migrations | **confirm** | No race — you're sole active committer on rdm-bot main. Order C→E→D→P2 is fine. E=0032, D=0033. P2 unlikely needs migration (likely worker handler / cron config issue). |

---

## Additional context for the sprint

**Part D shape per pick (a) on §2** — adopt the structure I originally drafted in the now-overwritten thread/110:

| Sub-piece | Status | Notes |
|---|---|---|
| Schema `extra_guests_captures` table | migration 0033 | Status field: `pending_review` / `message_sent` / `captured` / `confirmed_16` / `no_response` / `inquiry_cancelled` / `manual_review` |
| Detection cron | daily 05:00 UTC | Writes `pending_review` rows only. NO outbound. Webhook hook optional. |
| Drawer UI: "Send outreach" button per pending row | NEW per pick (a) | Hits `POST /admin/extra-guests/{booking_id}/fire-outreach` — same flag gate as §1 |
| Inbound response parser | client-bot-polling hook | Reuses existing inbound polling, parses + posts Beds24 invoice on `captured` |
| Auto-send v2 | DEFERRED | After 1 month of manual fires with zero misfires, add `auto_send_after_24h` flag |

**Tasks NOT in this sprint** (out of scope confirmation):
- thread/109 wave G+H+I+J (phone wa.me, airbnb-content 500, proxReservas, guia-llegada rich) — queued AFTER this batch
- Real logo SVG swap — Alex drops files, no code
- rdm-platform touches
- /guia-llegada hotfix you mentioned running in background is OK — doesn't conflict with C+E+D+P2 scope

**Sandbox booking for outbound testing**:
- Use Alex's own future test booking or create a test entry in Beds24
- Token: same `BEDS24_TOKEN` env that polling uses
- Confirm with Alex which beds24_booking_id he wants used as canary before flipping flag

**Time-box reminder**:
- §1 + §2 conservative defaults reduce blast radius — accept slight delay vs spec timing
- §3 P2 has explicit 2h halt rule — don't blow sprint on rabbit hole
- §4 OK — start migrations

**Reporting**: thread/112 for sprint complete, single PR with 4 atomic commits (C / E / D / P2).

---

**Decisions blessed. Sprint go. Alex canary required before flag flip.**

— WC, 2026-05-19
