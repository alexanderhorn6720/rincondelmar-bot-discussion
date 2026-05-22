# 169 · CC-Bot · Telegram "pago recibido" notification — bucket spec

**Author**: CC-Bot (DoIt session 2026-05-22)
**Type**: bucket spec proposal (awaiting Alex Q&A before execution)
**Related**: [thread/167](167-cc-bot-mp-webhook-beds24-capture-followup.md) · [thread/168](168-cc-bot-mp-webhook-beds24-capture-pr158.md) · [PR #158](https://github.com/alexanderhorn6720/rdm-bot/pull/158)

---

## TL;DR

After PR #158 lands, MP-paid bookings get captured in Beds24 silently. Ops still has no immediate visibility unless they refresh `/admin/bookings/<id>`. Need a Telegram ping fired from `worker-pago` webhook's `approved` path so Alex (and optionally Karina) see incoming payments in real time with a one-tap link to the booking detail.

~80 LOC + 4-5 tests. Single PR. Fits in one CC sitting. **Out of scope until 3 inputs from Alex below**.

---

## Decisions from Alex (2026-05-22)

| # | Q | Answer |
|---|---|---|
| Q1 | Bot identity | ✅ **Reuse existing `TG_BOT_TOKEN`** (currently in worker-bot, sync to worker-pago via `scripts/sync-secret.sh`) |
| Q2 | Destination chat_id | ✅ **"Al bot"** — direct message to Alex's chat with the bot. Concrete chat_id pending; CC will: code with `TG_CHAT_ID_PAGOS` env var, ship without setting it (graceful no-op), Alex provides chat_id later via `wrangler secret put` |
| Q3 | Message format | ✅ Use as proposed (icon + booking line + dates + amount/method + admin link) |
| Q4 | Refund pings | Not answered → defaulting to **yes**, single warning line on refunded/charged_back |

---

## Scope

| Item | Path | Notes |
|---|---|---|
| 1. New module `telegram-notify.ts` | `apps/worker-pago/src/telegram-notify.ts` | Pure function `notifyPagoRecibido(env, {bookingId, amount, currency, method, guestName, arrival, departure})`. POSTs to Telegram Bot API `sendMessage`. Fire-and-forget via `c.executionCtx.waitUntil()` — never blocks webhook response. |
| 2. Booking enrichment | `apps/worker-pago/src/booking-lookup.ts` | `loadBookingForNotify(env, beds24BookingId)` → `{guest_name, arrival, departure}` from `SELECT g.name, bb.arrival, bb.departure FROM beds24_bookings bb LEFT JOIN guests g ON g.id = bb.guest_id WHERE bb.beds24_booking_id = ?`. Returns null gracefully if booking not in D1 (notification still sends with `(unknown guest)` rather than fail). |
| 3. Wire into webhook-mp `approved` branch | `apps/worker-pago/src/webhook-mp.ts` | Right after the successful `pushMpPayment` + `markBedsResult` calls. Do NOT fire on failed Beds24 push (would alarm ops on what they can't act on yet — cron retry will handle silent). |
| 4. Wire refund (if Q4=yes) | Same | After successful negative push. Different prefix `⚠️ Reembolso`. |
| 5. Env types | `apps/worker-pago/src/types.ts` | Add `TG_BOT_TOKEN?: string` + `TG_CHAT_ID_PAGOS?: string`. Both optional → graceful no-op if missing. |
| 6. Secret provisioning | `bash scripts/sync-secret.sh TG_BOT_TOKEN worker-pago` (if reusing) | Add row to `docs/secrets-inventory.md`. |
| 7. Tests | `apps/worker-pago/tests/telegram-notify.test.ts` + extend `webhook-mp.test.ts` | Module tests: token missing → no-op (no fetch), happy path POSTs to Telegram API with right body, network exception swallowed. Integration tests: approved fires, failed push does NOT fire, refund fires (if Q4=yes). |

### Out of scope (deferred)

- ❌ Per-guest preference (Karina silenced for whales? Alex silenced for refunds?) — single chat_id for v1
- ❌ Markdown formatting / inline keyboard buttons — plain text + URL is enough
- ❌ Localization (always Spanish in v1)
- ❌ Retries on Telegram API failure — fire-and-forget; if Telegram is down, ops will see it in the next batch via `/admin/bookings` refresh anyway
- ❌ Threading multiple payments per booking (e.g. anticipo + saldo) into the same chat thread — each payment is a separate message in v1
- ❌ Quiet hours (no nightly pings) — ops can mute the chat in TG if they want

---

## Code skeleton (illustrative)

```typescript
// telegram-notify.ts
const TG_API = 'https://api.telegram.org';

export async function notifyPagoRecibido(env: TgEnv, p: {
  bookingId: number;
  amount: number;
  currency: string;
  method?: string;
  guestName?: string | null;
  arrival?: string | null;
  departure?: string | null;
  isRefund?: boolean;
}): Promise<{ ok: boolean }> {
  if (!env.TG_BOT_TOKEN || !env.TG_CHAT_ID_PAGOS) return { ok: false };
  const icon = p.isRefund ? '⚠️ Reembolso' : '💰 Pago recibido';
  const sign = p.isRefund ? '-' : '';
  const lines = [
    icon,
    `Booking #${p.bookingId}${p.guestName ? ` · ${p.guestName}` : ''}`,
    p.arrival && p.departure ? `${p.arrival} → ${p.departure}` : null,
    `${sign}$${p.amount.toLocaleString('es-MX')} ${p.currency}${p.method ? ` · MP ${p.method}` : ''}`,
    `👉 https://rincondelmar.club/admin/bookings/${p.bookingId}`,
  ].filter(Boolean).join('\n');

  try {
    const res = await fetch(`${TG_API}/bot${env.TG_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        chat_id: env.TG_CHAT_ID_PAGOS,
        text: lines,
        disable_web_page_preview: true,
      }),
    });
    return { ok: res.ok };
  } catch (err) {
    console.error('[tg-notify] failed', err);
    return { ok: false };
  }
}
```

```typescript
// webhook-mp.ts approved branch (around line ~210)
if (push.ok) {
  const booking = await loadBookingForNotify(env, beds24BookingId).catch(() => null);
  c.executionCtx.waitUntil(notifyPagoRecibido(env, {
    bookingId: beds24BookingId,
    amount,
    currency: payment.currency_id ?? 'MXN',
    method: payment.payment_method_id,
    guestName: booking?.guest_name,
    arrival: booking?.arrival,
    departure: booking?.departure,
  }));
}
```

---

## Estimates

| Metric | Estimate |
|---|---|
| LOC | ~80 src + ~60 tests = 140 |
| Commits | 3 |
| Tests | 6 |
| LLM cost | <$2 |
| Wall time | 1-2h |
| Risk | **Low** — fire-and-forget, graceful no-op without secrets, no schema changes. Worst case: silent no-op if env vars missing. |

---

## Anti-patterns avoided

- ✅ No new database tables — reads existing `beds24_bookings` + `guests`
- ✅ Workstream = CC-Bot territory (`apps/worker-pago/` only)
- ✅ No PII in logs (we log paymentId + bookingId, not guest name or email)
- ✅ No blocking on Telegram API — fire-and-forget via `waitUntil`
- ✅ Graceful degrade when secrets missing — production safety

---

**Status**: Waiting on Alex Q1/Q2/Q3 (+ optional Q4). On answer, I open `feat/telegram-pago-notify` and execute in a single 1-2h sitting.
