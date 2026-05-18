# 117 — WC: handoff doc reconciliation — do NOT trust `rdm-bot-handoff-ops.md`

**Date**: 2026-05-18
**Author**: WC
**To**: CC-Bot, CC-Data, any future agent
**Re**: Alex shared a `rdm-bot-handoff-ops.md` doc with a new WC session. The doc is ~7-10 days stale and has one inverted fact that would actively break production if acted on. Documenting discrepancies so no agent uses it as a source of truth.
**Mode**: docs-reconciliation (no code action required)
**Status**: 🔴 Doc-level red flag — one inverted policy + stale pipeline. Sources of truth listed below.

---

## TL;DR

A handoff doc titled `rdm-bot-handoff-ops.md` was generated some days ago to brief a new agent. It's outdated and contains one **inverted policy fix** (pet policy direction reversed) that would corrupt content drafts if applied verbatim. Sprint C+E+D+P2 and thread/115 supersede the doc's P1 list entirely. Treat the doc as **deprecated** — fall back to repo-internal canonical sources.

CC-Bot: if you have this doc in any context, drop it. Use `rdm-discussion/CONTEXT.md` + `ROADMAP.md` + recent threads.

---

## §1 — The one fact that would break prod if acted on

| Doc claim | Reality (thread/59) |
|---|---|
| "Pet policy fix: content-drafts retroactively need correction from `/noche` → `/estancia` (was a transcription error)" | **`$300 MXN/mascota/noche, máximo 2`**. Alex's confirmed decision is **per night**, not per stay. Doc has the fix direction inverted. |

**Impact if obeyed**: content drafts ES+EN would silently halve the pet fee on multi-night stays (avg ~4-5 nights). Greeter system prompt + AirBnB listings + PetsPolicy component would all drift to the wrong policy.

**Action**: ignore the `/noche → /estancia` instruction. Real fix direction is `/estancia → /noche` if anything still says `/estancia` (thread/59 already aligned content drafts + PetsPolicy + AirBnB listings on `/noche`).

---

## §2 — Stale property table

Doc says 4 villas + Casa Chamán internal. Reality is **5 active roomIds** (Morenas has two listings — same property, different channels):

| Slug | Beds24 roomId | Base cap | Extra |
|---|---|---|---|
| `rincon-del-mar` | 78695 | 15 | $300/pax/noche |
| `las-morenas` (direct) | 374482 | 15 | $300/pax/noche |
| `las-morenas-airbnb` | 74322 | 15 | $300/pax/noche |
| `huerta-cocotera` | 637063 | 4 | $200/pax/noche |
| `combinada` | 74316 | 30 | $300/pax/noche (linked: blocks 78695 + 374482) |

Casa Chamán (679176, base 15) still correctly marked "not in guest prompt until renovation" — doc got this right. Q3 2026.

Source: `CONTEXT.md` §Negocio.

---

## §3 — P1 pipeline reality check

Doc lists 5 P1 blockers. Status now:

| Doc # | Doc task | Real status |
|---|---|---|
| 1 | Beds24 booking webhook (Phase C) deploy | ✅ Shipped. PR #84 backfill, threads 25/26/28, normalize fixes in 8ba7e09. Webhook is live in `apps/worker-bot/src/beds24-webhook.ts` + migration `0011_beds24_events.sql`. |
| 2 | Manual deploy of Worker `rincon-bot` | ✅ Routine now. Alex deploys regularly post-PR-merge. Not a blocker. |
| 3 | PR #32 BookingCard URL params | ✅ Ancient. Current PRs at #89. |
| 4 | R2 import of content drafts | ✅ Shipped at thread/46. KB live. |
| 5 | Beds24 Reviews API ingestion | ✅ Shipped. Migration `0012_reviews.sql` + `reviews-sync.ts` + `POST /admin/sync-reviews` cron + `<ReviewsCarousel>` component (thread/32). |

Doc's entire P1 list is closed. Active sprint = C+E+D+P2 (threads/110+111) + thread/115 guests resync + thread/113 hotfix.

---

## §4 — Other corrections

| Doc claim | Reality |
|---|---|
| "AirBnB OAuth not needed" framing for Reviews API | Correct, but framed as future work. It's done. |
| "MercadoPago re-integration is future scope, do not touch" | Stale framing. `apps/worker-pago` is live with HMAC + idempotency KV + 5 crons. Not a future task. |
| "Make.com scenarios being phased out — do not touch" | Still correct, kept as-is. |
| "PAT exposed in chat history and is pending rotation" | Alex confirmed not urgent (2026-05-18 chat). |
| §6 conventions table | All still valid. |
| §3.1/§3.2 Cloudflare resources table | Mostly valid but underspecified vs CONTEXT.md. Prefer CONTEXT.md. |

---

## §5 — Canonical sources (use these instead)

| Need | File |
|---|---|
| Property table, stack, integrations, KPIs | `rdm-discussion/CONTEXT.md` |
| Phasing + timeline | `rdm-discussion/ROADMAP.md` |
| Active sprint, blockers, decisions | `rdm-discussion/threads/` (latest = thread/115; resume from highest unresolved number) |
| CC operational rules | `rdm-discussion/CLAUDE.md` |
| Workstream territories | `rdm-discussion/CLAUDE.md` §"Workstream conventions" |
| Spec doc template | `rdm-discussion/CLAUDE.md` §"Spec doc template" |
| Open decisions during PR1 era | `rdm-bot/OPEN_QUESTIONS.md` (historical, mostly closed) |

---

## §6 — Action items

| For | Action |
|---|---|
| CC-Bot | If `rdm-bot-handoff-ops.md` is in your context, drop it. Continue C+E+D+P2 sprint per threads/110+111 and follow up with thread/115 + thread/113 per existing plans. |
| CC-Data | Same. Doc doesn't conflict with your active work but don't cite it. |
| WC (future sessions) | Don't regenerate handoff docs as standalone .md files. Onboarding lives in `CONTEXT.md` + `ROADMAP.md` + `CLAUDE.md`. |
| Alex | When briefing a new chat, point at the repo, not at a snapshot doc. Snapshots go stale within ~1 week given current ship cadence. |

---

## §7 — Why this happened (brief)

The handoff doc was generated assuming a "new collaborator takes over" scenario. The cadence of CC-Bot + WC + CC-Data ships is fast enough that any markdown snapshot decays within days. The doc is also organized around "ops execution" framing, which doesn't match how the repo actually splits work (CC-Bot autonomous + WC strategy + Alex deploys). No one's fault — just architectural mismatch between "single new contractor" framing and "multi-agent rolling collaboration" reality.

Fix going forward: rely on `CONTEXT.md` (state) + `ROADMAP.md` (plan) + `threads/` (current motion) + `CLAUDE.md` (rules). All four are repo-internal and update in-place.

---

**No code or PR action required. Pure docs hygiene.**

— WC, 2026-05-18
