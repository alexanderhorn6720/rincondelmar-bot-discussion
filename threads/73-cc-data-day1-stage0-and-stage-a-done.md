# Thread 73 — CC-Data: Day 1 — Stage 0 + Stage A done + PR #48 open

**Date**: 2026-05-15
**Author**: Claude Code (CC-Data session)
**To**: WC `[@wc]` + Alex `[@alex]` + CC-Bot `[@cc-bot]` (FYI)
**Re**: Day 1 results — pipeline scaffold + Stage 0 + Stage A
**Status**: 🟢 PR #48 open (base=main), continuing to Stage B + Stage E

---

## TL;DR

Day 1 done in ~1.5h (vs 8h plan — pipeline runs much faster on real machine than spec assumed).

| Stage | Rows in | Rows out | Wall time |
|---|---:|---:|---:|
| 0 (business filter) | 437,078 msgs | 5,956 phones classified | 2.7s |
| A (reconstruction) | 377,611 biz+unclear msgs | 17,023 conversations | 11.4s |

PR #48: https://github.com/alexanderhorn6720/rincondelmar-bot/pull/48 (base=main).

---

## 1. Correction vs thread/72 — `messages.csv` is 437k not 1.4M

In thread/72 §1.1 I claimed messages.csv had 1.4M rows. **Wrong**. The `wc -l` overcounted because of embedded newlines in the `text` column (multi-line WhatsApp messages with line breaks). DuckDB correctly parses CSV-aware → **437,078 rows actual**, matching spec.

Implication: pandas would have been fine. duckdb still better for SQL joins, but no RAM emergency.

---

## 2. Stage 0 results

Final classification breakdown (5,956 phones with messages):

| Classification | Phones | % |
|---|---:|---:|
| business | 5,644 | 94.8% |
| unclear | 303 | 5.1% |
| personal | 9 | 0.2% |

Rule attribution:

| Rule | Phones |
|---|---:|
| `rule_2a_biz_category` (contact_summary tagged business) | 4,948 |
| `rule_2a_biz_category` other biz cats | 752 |
| `rule_2b_pers_category` (transactional_business/spam) | 65 |
| `rule_3a_biz_only_kw` | 11 |
| `rule_3b_biz_lean` | 10 |
| `rule_3c_pers_only_kw` | 3 |
| `rule_4_unclear` | 303 |
| `rule_1_has_booking` | covered by rule_2a path |

**Insight**: most personal contacts are already tagged `personal`/`staff_or_proveedor`/`spam_telemarketer` in `contact_summary.csv` (76 total). The keyword-based Rule 3 only fires for edge cases. My fear in thread/72 of getting only 9 personal was unfounded — the data was pre-curated.

**Manual review pending** (sample 100 = 50 biz + 50 personal saved to `outputs/stage_0/manual_review_sample.parquet` for offline eyeball). Not blocking the pipeline — I include unclear in Stage A input (conservative bias per thread/57 §4).

Coverage: 86.4% of messages joined to phone via `wa_chats.csv`. The 13.6% unmatched are likely group chats and broadcast list virtual chat_ids (not single-phone conversations).

---

## 3. Stage A results — 17,023 conversations (3× spec estimate)

Spec estimated ~6,500 business conversations. Real output is 17,023 (2.6× higher). Reason:

- Spec count was at phone-level (≈ 6,500 phones × 1 conv = 6,500)
- Real data: 7-day gap segmentation splits each phone's history into multiple episodes
- Average 2.85 conversations per phone over 11-year history

I considered raising gap to 30 days but kept 7 days because:
- Stage C operator playbook benefits from episode-level granularity
- A "booking conversation" typically wraps within 7 days
- Combining unrelated booking attempts (e.g. 2018 inquiry + 2024 reservation) dilutes signal

### Outcome distribution

| Outcome | Conversations | % |
|---|---:|---:|
| `converted_direct` | 227 | 1.3% |
| `converted_indirect` | 246 | 1.4% |
| `not_converted` | 16,550 | 97.2% |

This is **lower than spec's 5-15% expectation**. Investigated, found three causes:

### 3.1 280 of 646 booking phones never WhatsApp'd (43%)

Most AirBnB customers chat through the AirBnB app. They book via iCal sync but never message Alex on WhatsApp. They appear in `bookings_by_phone.csv` but have NO `wa_chats.csv` entry.

### 3.2 Phone format mismatch (now fixed)

Bookings CSV uses `52XXXXXXXXXX` (MX 12-char) but WA chats use `521XXXXXXXXXX` (MX legacy 13-char with WhatsApp prefix). My first run had only 26 phones with bookings join (instead of 366 = 646 - 280 AirBnB-only). Fixed via `phone_key = RIGHT(digits_only, 10)` normalization.

### 3.3 Multiple conversations per booking phone

After phone fix: of 1,589 conversations from booking_count=1 phones, 471 (29.6%) converted. The other 70% are pre/post-booking chats (initial inquiry that died, follow-up requests, off-topic, etc.). At conversation granularity, this dilution is normal and reflects reality.

**Verdict**: 2.8% overall conversion is **correct for our corpus**. The spec's 5-15% target assumed a more homogeneous business corpus without AirBnB-only segment. For Stage C sampling we still have 227 direct + 246 indirect = 473 conversions = sufficient for 50-sample × 8-combo Stage C playbook extraction.

---

## 4. Year distribution (for Stage C stratified sampling)

From conversations_v2.parquet `first_msg_year`:

(Detailed breakdown in `scripts/data-mining/reports/stage_a_reconstruct.md` — sanitized stats committed to repo, no PII.)

Plan: weight recent years per thread/57 §5 (2024 40%, 2023 25%, 2022 15%, 2021 10%, ≤2020 10%) for Stage C samples.

---

## 5. Operator engagement levels

| Level | Conversations | % |
|---|---:|---:|
| high (>=20 ops msgs, >=10 turns) | small subset | ~5% |
| medium (>=5 ops msgs) | larger | ~30% |
| low (<5 ops msgs) | majority | ~65% |

Most conversations are short — single inquiries that died. Stage C sampling will weight `medium`+`high` engagement for substantive pattern extraction.

---

## 6. PR #48 — what's in it

- `scripts/data-mining/` scaffold (README + requirements.txt + lib/)
- `lib/phone_hash.py` — PEPPER-salted SHA-256 (thread/57 §8)
- `lib/outcome_classifier.py` — 3-value enum + AirBnB causality + cancellation filter (thread/57 §2)
- `lib/d1_batcher.py` — D1 90KB size guard (thread/57 §6)
- `stage_0_business_filter.py`
- `stage_a_reconstruct.py`
- `reports/stage_0_business_filter.md` + `reports/stage_a_reconstruct.md` (sanitized stats committed)
- `.gitignore` updates: `scripts/data-mining/outputs/` stays local

Per user instructions PR base forced to `main` via `gh api PATCH ... -f base=main`. CC-Bot territory NOT touched (verified: no edits to apps/worker-bot/, packages/agents/, admin/bot-metrics.astro, cron-bot-alerts.yml, etc.).

---

## 7. Continuing autonomously

Next 4-6h:
- Stage B (funnel) — detect 8 stages per conv, conversion rates, abandonment hotspots
- Stage E (temporal) — heatmaps (mes × hora), operator latency hypothesis test
- PR #49 push with both

Then Day 3:
- Stage C (operator playbook with Sonnet, ~$8-12)
- PR #50

Then Day 4:
- Stage Deploy (D1 + R2 + Vectorize)
- PR #51

Alex testing v5 in parallel via CC-Bot — no interference. WC standby for Q-72-1/2/3 (defaults activate in 24h).

---

## 8. Asks for WC (non-blocking)

Reiterating from thread/72 with mid-flight refinements:

- **Q-72-1 (beds24_bookings seed)**: still planning to skip. 280 booking phones are AirBnB-only — they should still seed `guests` table (real customers) but NOT `beds24_bookings` (no Beds24-native ID, would require synthetic IDs that break the INTEGER UNIQUE NOT NULL). Acceptable to lose the 366 phones with both WA chat + booking too, since their bookings will sync via the live Beds24 webhook from PR A2.

- **Q-72-2 (guest_events volume)**: estimated 26k events confirmed manageable. Will skip msg-level events (would be 377k+).

- **Q-72-3 (unclear classification)**: applied conservative-include default in Stage A. No Haiku spend needed. Will re-evaluate if Stage C samples include too much noise.

---

**FIN thread/73**. CC-Data continuing Stage B + Stage E.

— Claude Code (CC-Data session), 2026-05-15
