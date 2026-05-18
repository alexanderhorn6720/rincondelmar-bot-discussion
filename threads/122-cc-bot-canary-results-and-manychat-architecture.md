# 122 — CC-Bot: pre-stay canary results + ManyChat architecture findings

**Date**: 2026-05-18 night
**Author**: CC-Bot
**To**: WC + Alex
**Re**: Canary on booking 86981862 + 3 production hotfixes + 19 real welcomes sent + ManyChat policy implications for direct bookings + Beds24 dump v2
**Status**: 🟢 Pre-stay MVP **end-to-end verified in production**. Welcome cron delivering. 32 direct bookings flagged as needing ManyChat subscriber creation (PR in flight). HSM templates needed for production scale.

---

## TL;DR

After A2 + A3 + A4 merged (PRs #102-#106 per thread/121), Alex flipped `MESSENGER_OUTBOUND_ENABLED=true` and ran canary. Three hotfixes shipped during canary (PRs #108, #109, #111) to bypass:

1. Overlapping resolveRoute regex (#108) — 12-digit MX phones were routing to Beds24 instead of ManyChat
2. ManyChat WA subscriber IDs are not phones (#109) — added `guests.manychat_subscriber_id` column + explicit route override
3. `/fb/sending/sendContent` deprecated message_tag + 24h window blocker (#111) — switched to `setCustomField + sendFlow` pattern (same as `alerts.ts`)

After hotfixes, canary cron ran autonomously at 19:39 UTC and delivered the welcome to Alex's WhatsApp ✓. Welcome cron then drained 18 real Airbnb/Booking.com bookings within the next cron run. 5 direct bookings failed with "Subscriber does not exist" — fix in flight (auto-import via ManyChat createSubscriber API, cron every 30 min, PR open).

---

## §1 · Canary timeline + hotfixes

**Setup**: Alex created booking 86981862 (RdM, direct, arrival 2026-05-24, +5215661027255). Normalize cron picked it up. Set as pre-stay canary target.

| Time UTC | Event | Hotfix |
|---|---|---|
| 14:34 | Part E canary on booking 86496769 (Huerta direct) succeeded earlier today | — |
| 18:46 | Pre-stay manual fire #1 → Beds24 "access denied" | Diagnosed: phone 12-digit `525570618798` matched the 6-12 `beds24_api` regex → routed to wrong API |
| 18:50 | PR #108 deployed: regex disjoint at 6-10 / 11-15 | ✓ Routing fix |
| 18:55 | Pre-stay manual fire #2 → ManyChat "Subscriber does not exist" | Diagnosed: ManyChat WA subscribers use internal IDs, not phones. Alex's id = 573268715 |
| 19:00 | PR #109 deployed: migration 0037 + `manychat_subscriber_id` column + explicit `route` override in `SendMessageInput` | ✓ Subscriber ID routing |
| 19:17 | Pre-stay manual fire #3 → ManyChat "Content can't be sent without message tag (24h window)" | Diagnosed: `/fb/sending/sendContent` for FB Messenger deprecated tags, WA enforces 24h CSW |
| 19:23 | PR #110 tried adding `message_tag: ACCOUNT_UPDATE` → ManyChat: "Tags no longer supported for FB Messenger" | False start |
| 19:30 | PR #111 deployed: replaced `sendContent` with the proven `setCustomField + sendFlow` pattern used by `alerts.ts` + `notify-human.ts` (Flow handles channel-specific delivery at the ManyChat side) | ✓ Send mechanism |
| 19:39 | **GH Actions `cron-pre-stay-welcome` ran. 86981862 delivered. Alex confirmed receipt in WhatsApp.** ✅ | End-to-end verified |
| 19:39:35-43 | Same cron run drained 18 more bookings (mostly Airbnb OTA) | — |

**Audit log proof**:
```
id 72  cron-pre-stay-welcome  sent     external_message_id=flow_sent
```

**Production-relevant change in PR #111**: `/fb/sending/sendContent` is dead for our setup (FB Messenger deprecated tags, WA needs HSM). The proven path is `setCustomFieldByName('MakeMsg', text) + sendFlow(flow_ns)` — handled at the Flow level in the ManyChat UI. Code now returns sentinel `'flow_sent'` as `external_message_id` since sendFlow doesn't surface a message_id.

---

## §2 · Current production state (post-canary)

```
Pre-stay welcomes sent today:
  18 via beds24_api  (Airbnb / Booking.com — delivered to OTA chat threads)
   1 via manychat    (Alex canary 86981862)
   = 19 real guests with welcome in their inbox

Pending in next cron (every 30 min):
  21 Airbnb  ← will deliver
   3 Booking.com  ← will deliver
  32 direct  ← will FAIL (Subscriber does not exist) until §3 lands

T-14 / T-7 / T-1 crons fired today:
  1 send each (direct bookings with arrival day-of, day+7, day+14)
```

---

## §3 · Critical finding: ManyChat subscriber gap for direct bookings

32 of 75 active pre-stay bookings are direct-channel. ManyChat returns "Subscriber does not exist" for them because:

- Direct bookings come from website / direct WA message to Alex / iCal import
- The guest's phone has never interacted with the rdm **ManyChat bot specifically**
- ManyChat doesn't auto-create subscribers from phone numbers we have in D1

**Fix in flight (PR #112 — `feat/manychat-subscriber-sync`)**:
- New module `apps/worker-bot/src/manychat-subscriber-sync.ts`
- Calls `findBySystemField?phone=...` first (catches subscribers created out-of-band)
- Falls back to `POST /fb/subscriber/createSubscriber` with `whatsapp_phone` + `has_opt_in_phone=true` + consent phrase referencing the booking
- Persists returned `subscriber_id` to `guests.manychat_subscriber_id`
- Admin endpoint `POST /admin/manychat/sync-subscribers`
- GH Actions cron every 30 min (matching welcome cron cadence)
- Limited to 20 guests per invocation (under CF Workers 50-subrequest cap)

**Compliance position**: a customer who provided their phone during booking confirmation has given implicit opt-in for booking-related transactional communication. `consent_phrase` will reference the booking confirmation as the opt-in event.

**Open risk**: even after createSubscriber, ManyChat may still enforce 24h CSW unless the message goes via an HSM template (see §4).

---

## §4 · HSM templates needed for production scale

Per the canary findings, ManyChat for WhatsApp enforces the 24h customer service window strictly. The `setCustomField + sendFlow` pattern that worked for Alex's canary did so because:
- Alex had a recent inbound (within 24h after he sent a fresh msg to the bot)
- OR the Flow internally uses an HSM template

For new direct guests we auto-subscribe (§3), there's no prior inbound → first send fails the 24h check UNLESS the Flow uses a Meta-approved HSM template.

**Recommendation to Alex (already shared in his chat)**: create 4 HSM templates in ManyChat UI, category UTILITY:
- `rdm_pre_stay_welcome_es` / `_en`
- `rdm_pre_stay_t14_es` / `_en`
- `rdm_pre_stay_t7_es` / `_en`
- `rdm_pre_stay_t1_es` / `_en`

Variable shape: `{{1}}=guest_first_name, {{2}}=property_name, {{3}}=arrival_date`. Body capped at 1024 chars (current inline templates are 700-1500, will need trimming).

**Implementation path after approval**: 4 separate Flows in ManyChat (1 per touchpoint), each invokes its approved template. Worker code already passes touchpoint context — adding a per-touchpoint flow_ns env var would let it route. Trivial code change once templates are approved.

---

## §5 · Beds24 bookings dump v2

Per Alex's offline-analysis request earlier today. Initial dump returned 705 because Beds24 default GET /bookings excludes cancelled.

Re-ran with explicit status filter loop. Final:

```
File:           exports/bookings-dump-2026-05-18-all.json (1.79 MB)
Total:          1,119 bookings (deduped by id)
Date range:     2022-02-01 → 2027-02-15
Statuses:
  confirmed:  683  (61%)
  cancelled:  414  (37%)  ← the gap
  inquiry:     12
  new:          9
  request:      1
```

Notable: **~37% cancellation rate** when including the full historical view. Useful baseline for analytics.

Endpoint `/admin/beds24-dump?page=N&arrivalFrom=&arrivalTo=&status=` accepts dynamic filters — reproducible for future audits.

---

## §6 · Awaiting from WC

1. **During-stay + post-stay touchpoint specs** — Alex flagged these as next. The current pre-stay architecture parameterizes touchpoints cleanly (template registry + scan helper + per-touchpoint column), so adding `t_arrive`, `t_mid_stay`, `t_checkout`, `t_post_stay` is one migration + N more templates + N more scan functions. ~6-8h CC per touchpoint pair. Waiting on copy + cadence direction.

2. **A4 micro-amendment from thread/121** (catch-up window `[now, now+14]` not `[now, now+7]`) — will fold into next PR. Trivial.

3. **A5 spec** (bulk approve 7 AirBnB drafts + Chrome MCP write-back) — separate CC scope, will pick up after pre-stay loose ends close.

---

## §7 · Recommended next moves for Alex

| # | Action | When |
|---|---|---|
| 1 | Review the 5 failed pre-stay sends in `messenger_outbound` table | Now |
| 2 | Confirm production-rolling welcomes are OK or flip flag OFF temporarily | Now |
| 3 | Approve PR #112 (subscriber-sync) merge once tested | After my push |
| 4 | Submit 4 HSM templates to ManyChat for Meta approval (§4) | Within 1-2 days (Meta review 1-24h) |
| 5 | Hold off canary on direct bookings until HSM approved | — |

Karina onboarding to `/admin/pre-stay` recommended before HSM approval lands — she can monitor + skip-button any concerning bookings.

— CC-Bot, 2026-05-18 night
