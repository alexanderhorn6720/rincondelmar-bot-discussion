# 167 · CC-Bot · MP webhook → Beds24 invoiceItem capture (follow-up to PR #157)

**Author**: CC-Bot (ad-hoc session 2026-05-22, post-deploy smoke for PR #157)
**Type**: follow-up bucket proposal (request for spec approval)
**Related**: [thread/166](166-cc-bot-booking-detail-quick-dirty-pr157.md) · [PR #157](https://github.com/alexanderhorn6720/rdm-bot/pull/157) · spec [`cc-instructions-bot/2026-05-22-booking-detail-quick-dirty.md`](../cc-instructions-bot/2026-05-22-booking-detail-quick-dirty.md) §2 NO list

---

## TL;DR

PR #157 shipped the **MP link generator** (`/admin/bookings/[id]` Tab 3 → "Generar link") but explicitly excluded **MP webhook → Beds24 capture** from scope. Result: when a guest pays via the generated link, **the money sits in MP and never reaches Beds24 invoiceItems**. Old Make.com confirm scenario was retired in PR #155, so there is no glue at all today.

Need a small bucket (~150-250 LOC, 1 PR, <$3 LLM) to wire `worker-pago/webhook-mp.ts` → Beds24 `POST /v2/bookings invoiceItems[type:'payment']`.

---

## Evidence (real test today 2026-05-22 ~05:30 UTC)

1. Fixed `MP_ACCESS_TOKEN` in apps/web Pages env (was a TEST credential from MP dashboard onboarding — user_id `3367645000`; replaced with prod user_id `257420805`).
2. Regenerated payment link from Tab 3 for a real booking, paid **$20 MXN** with my own card.
3. MP MCP `notifications_history` for app `7012552756080539` jumped **7 → 9** notifications (+1 payment, +1 merchant_order_wh), all HTTP 200. Webhook delivered fine.
4. **D1**: no row in `booking_captures`, no row anywhere with `mp_payment_id` or `external_reference = "b24-<id>"`. Worker-pago wrote nothing.
5. **Beds24**: no `invoiceItem type='payment'` created on the booking. Money invisible to ops.
6. Worker-pago last deployed `2026-05-09T10:49:15Z` (commit `1167fa1`), pre-PR #157. Code at [`apps/worker-pago/src/webhook-mp.ts:154`](../../bot/apps/worker-pago/src/webhook-mp.ts#L154) queries a non-existent `bookings` table → falls into `console.warn('[mp_webhook] booking no existe')` → returns 200. Even if the table existed, the `approved` branch only calls `MAKE_CONFIRM_WEBHOOK_URL`, which Alex confirmed is dead (Make scenario disabled per PR #155 wrangler.toml comment).

So `MP → MP webhook → 200 OK silent drop` is the current flow end-to-end.

---

## Proposed bucket: `worker-pago` MP webhook → Beds24 capture

### Scope

| Item | Path | Notes |
|---|---|---|
| **1. Refactor webhook to support `b24-<id>` external_ref** | `apps/worker-pago/src/webhook-mp.ts` | Detect prefix, branch to new handler. Keep legacy `bookings` path behind feature flag or just remove (table doesn't exist anyway). |
| **2. New module `beds24-payment.ts`** | `apps/worker-pago/src/beds24-payment.ts` | Pure function `pushMpPayment(env, {bookingId, paymentId, amount, paidAt, description})`. POST `/v2/bookings` with `[{id, invoiceItems:[{type:'payment', qty:1, amount, description, vatRate:0}]}]` per `CLAUDE.md` Beds24 v2 reference §invoice items. |
| **3. D1 audit table** | new migration via `bash scripts/new-migration.sh mp_payments` | Columns: `mp_payment_id PK`, `beds24_booking_id`, `amount_mxn`, `status` (approved/refunded/etc.), `paid_at`, `beds24_pushed_at`, `beds24_push_status` (ok/error), `beds24_push_error`, `raw_json`, `created_at`. Idempotency key = `mp_payment_id`. |
| **4. Idempotency** | webhook-mp.ts | Two layers: KV `mp:webhook:{request-id}` (already there, keep) + D1 `mp_payments.mp_payment_id` (new — protects against MP webhook duplicates that re-use request-id OR cron retry). |
| **5. Status handling** | webhook-mp.ts | `approved` → push positive payment + write D1. `refunded`/`charged_back` → push negative payment (or `type:'charge'` with negative amount per Beds24 v2 docs) + update D1. `rejected`/`cancelled`/`pending` → only update D1 status, no Beds24 push. |
| **6. Tests** | `apps/worker-pago/tests/webhook-mp-b24.test.ts` | Mock MP API + Beds24 API + D1. Cases: approved happy, approved dup (idempotent), refunded, rejected, b24-prefix detection, missing token, Beds24 5xx (retry once + write `beds24_push_status='error'`). |
| **7. Deploy** | `bash scripts/safe-deploy.sh worker-pago` | Plus apply migration to prod via `wrangler d1 migrations apply rincon --remote`. |
| **8. Inventory update** | `docs/secrets-inventory.md` | Add `MP_ACCESS_TOKEN` row for `apps/web` Pages (PR #157 missed it). |

### Out of scope

- ❌ Multi-currency (Beds24 booking currency = `amount` value; MP returns MXN; we trust 1:1 for now)
- ❌ Confirmation email to guest (worker-pago has `sendBookingConfirmEmail` for the legacy path; for the new b24 path, ops can send manually from Beds24 or via existing Karina templates)
- ❌ Statement_descriptor (MP quality_checklist item; nice-to-have but not blocking)
- ❌ Refund automation UI (only webhook-driven for now)
- ❌ Cleanup of legacy `bookings` path — recommend deleting after this PR ships since the table genuinely doesn't exist (separate hygiene PR if Alex wants the git diff clean)

### Code skeleton (illustrative — to be implemented)

```typescript
// webhook-mp.ts after HMAC + fetch payment
const externalRef = payment.external_reference ?? '';
if (externalRef.startsWith('b24-')) {
  const beds24BookingId = Number(externalRef.slice(4));
  if (!beds24BookingId) return c.text('bad_external_ref', 200);

  // D1 idempotency
  const existing = await env.DB.prepare(
    'SELECT mp_payment_id FROM mp_payments WHERE mp_payment_id = ?',
  ).bind(paymentId).first();
  if (existing) {
    console.log({event:'mp_webhook', sub:'dup_d1', paymentId});
    return c.text('ok', 200);
  }

  if (payment.status === 'approved') {
    const pushRes = await pushMpPayment(env, {
      bookingId: beds24BookingId,
      paymentId,
      amount: payment.transaction_amount,
      paidAt: payment.date_approved,
      description: `MP ${paymentId}`,
    });
    await env.DB.prepare(`INSERT INTO mp_payments (...) VALUES (...)`).bind(...).run();
    return c.text('ok', 200);
  }
  // refunded / rejected / etc. → INSERT/UPDATE D1 only
  ...
}
// legacy path (bookings table — currently dead, candidate for removal)
```

```typescript
// beds24-payment.ts
export async function pushMpPayment(env, {bookingId, paymentId, amount, paidAt, description}) {
  const body = [{
    id: bookingId,
    invoiceItems: [{
      type: 'payment',
      qty: 1,
      amount,                          // positive number; Beds24 treats type=payment as credit
      description: `${description} ${paidAt}`,
      vatRate: 0,
    }],
  }];
  const res = await fetch('https://api.beds24.com/v2/bookings', {
    method: 'POST',
    headers: { token: env.BEDS24_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  // Per CLAUDE.md: response is [{success:true}] with no echo of id — must GET-refetch if we want the new invoiceItem.id (we don't for v1).
  return { ok: res.ok, status: res.status, text: res.ok ? null : await res.text() };
}
```

---

## Estimates

| Metric | Estimate |
|---|---|
| LOC | ~250 (200 src + 50 tests) |
| Commits | 4-5 semantic |
| Tests | 1 file, 8-10 cases |
| LLM cost | <$3 |
| Wall time | 4-6 h continuous |
| Risk | **Low** — additive only; legacy path was already dead. Worst case Beds24 push fails → D1 has the audit row + push_status='error' for manual reconciliation. |

---

## Open questions (for Alex / WC)

1. **Q1**: Is `external_reference=b24-<id>` the long-term contract, or do we want a richer `mp_<uuid>` referencing a `mp_payments` PK created at link-generation time? Today PR #157 uses `b24-<id>` directly. Simple, works, but couples MP to Beds24 IDs.
2. **Q2**: For partial payments (saldo flow — guest pays $5,000 of $15,000), do we mark booking as `confirmed`? Today Beds24 has its own logic (`balance > 0` = pendiente). I'd defer to Beds24's own balance math and just push the payment — no `confirmed` flip from our side.
3. **Q3**: Failed Beds24 push retry: cron-driven catch-up (every 30 min, retry all `beds24_push_status='error'`) or fire-and-forget with manual recon? My take: **cron** — already have a `*/30` for hold expiry, easy to add. ~15 LOC.
4. **Q4**: Do we want a Telegram alert to Alex on `beds24_push_status='error'` after 3 retries? Existing alert path lives where? (worker-bot has TG_BOT_TOKEN per secrets inventory.) Could be a follow-up bucket if not urgent.

My recommended defaults if Alex doesn't object: Q1 keep `b24-<id>`, Q2 no confirmed flip, Q3 add cron retry (15 LOC), Q4 skip for v1, manual recon via `/admin/issues` cockpit.

---

## Decisions pending

- [ ] **Alex**: approve bucket as scoped (or push to WC for fuller spec)
- [ ] **Alex** (manual NOW, separate from this bucket): manually register the $20 MXN test payment via Tab 3 → "Pago manual" with description `MP TEST 2026-05-22` so Beds24 reflects reality. Alternative: refund in MP panel (cleaner since it was a test).
- [ ] **WC** (if upgrading to formal spec): land in `cc-instructions-bot/2026-05-XX-mp-webhook-beds24-capture.md` with the §1-§5 template (objective, scope, code locations, smoke tests, NO list).

---

## Anti-patterns avoided in this proposal

- ✅ Pet fee not mentioned (irrelevant here)
- ✅ Casa Chamán not surfaced (irrelevant here)
- ✅ Beds24 sync mode untouched (we only POST invoiceItems, not /inventory/sync)
- ✅ No plaintext secrets in this thread
- ✅ Atomic migration claim via `bash scripts/new-migration.sh` documented
- ✅ Single PR (not multi-PR fragmentation)
- ✅ Workstream = **CC-Bot** territory (`apps/worker-pago/`, `apps/worker-bot/` not touched, `apps/web/` not touched except inventory doc)

---

**Next action**: Alex acks "go" → I open `feat/mp-webhook-beds24-capture` branch + execute bucket per CLAUDE.md §"Tu loop por bucket". Report back in thread/168.
