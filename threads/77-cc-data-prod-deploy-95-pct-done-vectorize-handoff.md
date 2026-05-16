# Thread 77 — CC-Data: production deploy 95% done, Vectorize handed off

**Date**: 2026-05-16 ~00:30
**Author**: Claude Code (CC-Data session, closing out)
**To**: WC `[@wc]` + Alex `[@alex]` + next session picking up Vectorize
**Re**: Stage C executed live, D1 seeded, R2 uploaded — Vectorize remains
**Status**: 🟡 95% complete. One leg remaining (Vectorize), instructions in cc-instructions-data/2026-05-16-vectorize-handoff.md

---

## TL;DR

CC-Data sprint went from pipeline-ready (thread/76) to mostly-deployed in production tonight. Alex ran the wrangler commands with the API key from `.api-keys`; CC-Data wrote the scripts + iterated on bugs.

| Deploy step | Status | Notes |
|---|---|---|
| Stage C live (Sonnet) | ✅ done | $1.25, 5.6 min, 18 patterns |
| D1 `guests` seed | ✅ done | **7,423 rows** in production |
| D1 `leads` seed | ✅ done | **5,874 rows** in production |
| D1 `guest_events` seed | ✅ done | **51,414 rows** in production |
| R2 uploads | ✅ done | 4 markdown files in `rdm-knowledge/` |
| Vectorize index | ❌ pending | handed off — see §3 below |

Total LLM cost so far: **$1.25** (vs spec's $15-25 budget). Vectorize will add ~$0.19 paid-tier or stay in free tier if split across 2 days.

---

## 1. Stage C execution results

Ran `stage_c_operator_playbook.py --execute` with Anthropic API key from `C:/rdm-wa-api/.api-keys`:

| Prompt | Input tokens | Output | Cost | Time |
|---|---:|---:|---:|---:|
| price_quoted_vs_outcome | 98,875 | 4,000 | $0.357 | 85s |
| price_accepted_vs_outcome | 132,563 | 4,000 | $0.458 | 85s |
| group_specified_vs_outcome | 46,821 | 4,000 | $0.200 | 81s |
| initial_inquiry_vs_outcome | 57,930 | 4,000 | $0.234 | 85s |
| **TOTAL** | **336,189** | **16,000** | **$1.249** | **5.6 min** |

`data/artifacts/operator_playbook.md` is 52 KB with **18 patterns** across 4 funnel-stage cohorts. Hit `max_tokens=4000` on all 4 calls — Sonnet likely had more patterns to share. Future re-run with `max_tokens=8000` (~$0.50 more) could capture them, but the current set is already actionable.

Sample pattern:

> **Patrón 1 — Cifra Total Única Entregada Proactivamente**
>
> Frecuencia observada: 28 de 50 en converted | 4 de 50 en not_converted (7× lift)
>
> Mecanismo: "Cuando el operador entrega un número total cerrado para las fechas y grupo específicos del cliente, elimina la fricción cognitiva... La cotización personalizada funciona como señal de compromiso del vendedor con esa oferta concreta, acelerando la decisión."

CC-Bot's PR A6.1 (Greeter v5 prompt upgrade) consumes this directly.

---

## 2. D1 seed — what fought back, what we landed on

The D1 apply was harder than expected. Three PRs of fixes before it stuck:

| PR | Theory | Why it didn't fully solve |
|---|---|---|
| #57 INSERT OR IGNORE syntax | D1 should silently skip on UNIQUE violation | D1's wrangler `--remote` execute surfaced the constraint error anyway, where standalone SQLite would have swallowed it |
| #58 Python-level dedupe of email_lower / phone_e164 | Eliminate the duplicates within the seed file | Still hit cross-run conflicts because ghost rows from earlier partial-failed applies had different (non-deterministic) ULIDs but matching emails/phones |
| #59 deterministic IDs (SHA-256 → Crockford base32) | `same phone → same guest_id` forever, INSERT OR IGNORE actually works | ✅ this stuck after Alex ran `DELETE FROM` on the 3 tables to clear ghost rows |

Final state in production D1:

```
guests breakdown:
  prospect  6,777
  customer    610
  repeat       30
  vip           6
  -------------
  TOTAL     7,423

leads breakdown:
  lost_no_response  5,651
  won                 223
  -------------
  TOTAL             5,874

guest_events breakdown:
  lead_engaged   29,624
  lead_created   16,753
  lead_quoted     4,575
  lead_won          462
  -------------
  TOTAL          51,414
```

`beds24_bookings` seed: skipped per Q-72-1 (no Beds24-native IDs in source CSV; live webhook PR A2 populates instead).

The lead "won" count (223) is lower than the 473 converted conversations from Stage A because **leads are 1-per-phone** (not 1-per-conversation): a phone with multiple converted conversations gets one lead with best outcome rank. 223 phones had at least one converted conversation. The 462 `lead_won` events correctly reflect the per-conversation outcome (one event per booking_confirmed funnel stage).

---

## 3. Vectorize handoff

**Why it's not done**: CC-Data fell into a wrangler v3.91 vs v4 syntax loop (5 consecutive small errors: `--remote` on R2 put, `r2 object list` not in v3.91, etc.). Alex's productivity hit a wall on the round-trip. Handing off so a fresh session can take it without the accumulated noise.

**Instructions**: full self-contained doc at
`cc-instructions-data/2026-05-16-vectorize-handoff.md`

It covers:
- Pre-flight (verify D1 + R2 state)
- CF API token creation (needs Workers AI Edit + Vectorize Edit scopes)
- `wrangler vectorize create` (one-shot)
- `python stage_vectorize.py --execute` (the 2-3h embedding loop)
- Smoke test query via REST API
- Where to report back when done

**Estimated effort for next session**: ~5 min hands-on, ~2-3h wall (mostly waiting), ~$0.19 cost (or free if spread over 2 days).

---

## 4. PRs landed during the deploy session

| PR | Title | Purpose |
|---|---|---|
| #57 | switch D1 seed to INSERT OR IGNORE | first fix (insufficient alone) |
| #58 | Python-level dedupe of email_lower + phone_e164 | second fix (didn't address cross-run) |
| #59 | deterministic guest/lead/event IDs | the one that worked |
| #60 | drop `--remote` flag from `r2 object put` | wrangler v3.91 syntax fix |

All squash-merged to `main`.

---

## 5. Lessons for future sprints involving wrangler

CC-Data ran into a productivity wall around the wrangler v3.91 vs v4 syntax differences. Things to remember:

- `wrangler d1 execute` — DOES take `--remote`
- `wrangler r2 object put` — does NOT take `--remote` (v3.91); defaults to remote unless `--local`
- `wrangler r2 object list` — does NOT exist in v3.91 (added in v4)
- `wrangler vectorize create / get` — DO exist in v3.91
- When in doubt: `pnpm --filter worker-bot exec wrangler <cmd> --help`

Also: D1's `wrangler d1 execute --remote --file=foo.sql` claims "if execution fails, DB returns to original state" but in practice partial-batch failures leave ghost rows. Use deterministic IDs + INSERT OR IGNORE for idempotent retries, OR be ready to run `DELETE FROM <table>` between attempts.

---

## 6. Final state of the deliverables

| Deliverable | Location | Status |
|---|---|---|
| Pipeline code | `scripts/data-mining/` | committed to main (PRs #48-#60) |
| Operator playbook | `data/artifacts/operator_playbook.md` | committed + on R2 |
| Stats reports | `scripts/data-mining/reports/*.md` | committed |
| Temporal charts | `data/artifacts/temporal_charts/*.png` | committed (4 PNGs, 163 KB) |
| D1 `guests` | production `rincon` D1 | **7,423 rows** |
| D1 `leads` | production `rincon` D1 | **5,874 rows** |
| D1 `guest_events` | production `rincon` D1 | **51,414 rows** |
| R2 `operator_playbook.md` | `rdm-knowledge/` bucket | ✅ uploaded |
| R2 `temporal_insights_v2.md` | `rdm-knowledge/` bucket | ✅ uploaded |
| R2 `funnel_v2.md` | `rdm-knowledge/` bucket | ✅ uploaded |
| R2 `knowledge_reconstruction_v2.md` | `rdm-knowledge/` bucket | ✅ uploaded |
| Vectorize `rdm-conversations-v2` | (CF Vectorize) | ❌ pending — handed off |

---

**FIN thread/77**. CC-Data signing off. Next session picks up Vectorize per the handoff doc.

— Claude Code (CC-Data), 2026-05-16
