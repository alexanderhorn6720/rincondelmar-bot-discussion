# Thread 132 · WC · Browserbase eval + AirBnB KPI scraper backlog item

**From:** WC
**To:** Alex + future WC sessions
**Date:** 2026-05-19
**Type:** Backlog item · spec-pending
**Status:** Approved by Alex 2026-05-19, post-A5 execution
**Effort estimate:** 14-20h CC total across 4 phases

---

## TLDR

Alex confirmó 2026-05-19: instalar **Browserbase + Stagehand** como infrastructure permanente para browser ops, principalmente para:

1. AirBnB KPIs scraper recurrent (occupancy, views, search rank, conversion) — NO expuesto vía Beds24 API
2. Scrapes ocasionales otros sitios (general purpose)
3. CC autonomous capability cuando Chrome MCP no es viable (CF Workers, scheduled jobs)

Migración Chrome MCP a Browserbase eventual cuando trigger emerja. Chrome MCP queda para one-shot dev work.

---

## 1 · Context

### Lo que tenemos hoy

| Tool | Use cases actuales |
|---|---|
| **Beds24 v2 API** | Calendar, pricing, basic content, reviews, direct booking inquiries, messages |
| **Beds24 Reviews API** | Already shipped (reviews-sync.ts cron) |
| **`postBeds24Message`** | OTA messages outbound (works for AirBnB inbox via Beds24) |
| **Chrome MCP** | Set up for A5 thread/127 one-shot AirBnB content write-back |

### Lo que NO tenemos

| Gap | Por qué importa |
|---|---|
| AirBnB hosting analytics (occupancy %, listing views, search position, conversion rate, response rate) | NOT exposed via Beds24 v2 — UI-only |
| Booking.com extranet analytics | Similar gap |
| Other sites scraping infrastructure | One-off needs sin tool fijo |
| CC autonomous browser ops para CF Workers cron jobs | Chrome MCP no funciona desde Worker context |

### Por qué Browserbase específicamente

| Argumento | Detalle |
|---|---|
| Anti-bot evasion real | Stealth mode + residential IPs + fingerprint randomization. Chrome MCP detectable. |
| Session persistence | Auth survives hours, can pick up after interruption |
| Concurrent | Multiple parallel sessions if needed |
| MCP support | Browserbase MCP existe para CC autonomous |
| Observability | Dashboard de runs, screenshots, logs |
| Stagehand | LLM-native (CC decides element targeting semantically — resilient to UI changes) |
| Pricing | ~$50-200/mo for RdM volume |
| Cost vs alternative | Less than time debugging Chrome MCP failures |

### Por qué NO ahora (defer post-A5)

| Razón | Detalle |
|---|---|
| Pipeline activo (thread/127 + 128 + 131) | Don't change tooling mid-flight |
| Chrome MCP one-shot for A5 acceptable | A5 is rare event |
| Need validation: stealth works against AirBnB | Phase 1 trial first |
| Account/billing relationship setup overhead | Wants Alex's explicit signup |

---

## 2 · Phases · ordered

### Phase 1 · Eval (1 week wall-clock, 4-6h CC effective)

**Goal:** Validar que Browserbase + Stagehand puede scrapear AirBnB host dashboard sin trigger anti-bot detection.

| Step | Acción | Quien | Tiempo |
|---|---|---|---|
| 1 | Alex account Browserbase + free trial | Alex | 5 min |
| 2 | Setup Browserbase project + API keys | Alex | 10 min |
| 3 | Add to rdm-bot/.claude/mcp.json with Browserbase MCP server | Alex or CC | 5 min |
| 4 | CC autonomous test: navigate to https://www.airbnb.com/hosting/listings | CC | 30 min |
| 5 | If login required: persistent session config + Alex login one-time | Alex+CC | 30 min |
| 6 | Once authenticated: scrape sample KPI (occupancy %, last 30d) | CC | 1-2h |
| 7 | Verify no anti-bot trigger over 1 week (test 3-5x random times) | CC cron | passive |

**Success criteria:**
- ✅ AirBnB dashboard accessible vía Browserbase
- ✅ Session persists across runs
- ✅ No CAPTCHAs / verifications / account warnings after 5+ scrapes
- ✅ KPIs extractable (specific selectors or via Stagehand LLM)

**Halt conditions:**
- ❌ AirBnB triggers CAPTCHA → defer eval, explore alternatives
- ❌ Account warning email from AirBnB → STOP immediately, defer
- ❌ Selectors change every run → Stagehand may not work, evaluate alternatives

### Phase 2 · AirBnB KPI scraper (post-validation, 6-10h CC)

**Goal:** Recurrent automated KPI ingestion from AirBnB hosting dashboard.

**Spec brain deep pendiente** (60 min WC) — only after Phase 1 ✅.

| Component | Detalle |
|---|---|
| `apps/worker-bot/src/airbnb-kpi-scraper.ts` | Worker module |
| `migrations/00XX_airbnb_kpis.sql` | Time-series table |
| Cron weekly Sundays | Lower frequency reduces detection risk |
| `/admin/airbnb-kpis` dashboard | Visualization |
| Telegram alert if drop >X% | Optional |

**Schema D1 propuesto:**

```sql
CREATE TABLE airbnb_kpis_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scraped_at INTEGER NOT NULL,       -- Unix seconds
  listing_id TEXT NOT NULL,           -- AirBnB listing ID
  property_slug TEXT,                 -- mapping a rincon-del-mar / las-morenas / etc
  metric TEXT NOT NULL,               -- enum: occupancy_30d | views_30d | search_rank | conversion | response_rate | response_time_avg
  value REAL,                         -- numeric value
  unit TEXT,                          -- pct | count | minutes | etc
  raw_json TEXT                       -- full scrape payload for debugging
);

CREATE INDEX idx_kpis_recent ON airbnb_kpis_history(scraped_at DESC);
CREATE INDEX idx_kpis_by_listing ON airbnb_kpis_history(listing_id, metric, scraped_at DESC);
```

**KPIs target (initial):**

| KPI | Source | Useful for |
|---|---|---|
| Occupancy % (last 30/60/90 days) | Hosting dashboard | Verify vs internal calc |
| Total views | Listing analytics | Demand signal |
| Search rank position | If accessible | SEO health |
| Conversion rate (view → inquiry) | Listing analytics | Listing quality |
| Response rate | Hosting profile | Superhost retention |
| Response time avg | Hosting profile | Bot effectiveness |

### Phase 3 · Migration Chrome MCP → Browserbase (when triggered)

**Trigger conditions:**

| Signal | Action |
|---|---|
| Próxima vez necesitamos AirBnB UI write (post-A5) | Migrate from Chrome MCP for that work |
| Chrome MCP breaks for any reason | Migrate proactively |
| Want CC autonomous browser ops desde CF cron | Move to Browserbase |
| Multi-site scraping needs emerge | Standardize on Browserbase |

**Migration scope:**

| Component | Migrate? |
|---|---|
| A5 already done (thread/127) | NO — was one-shot, leave |
| Future AirBnB content edits | YES |
| Future Special Offers | OUT OF SCOPE (Alex confirmed Special Offers NOT used anymore) |
| Booker auto write to AirBnB | OUT OF SCOPE (no longer planned) |
| Other sites general purpose | YES |

### Phase 4 · CC autonomous integration

**Goal:** CC can invoke Browserbase tools naturally como cualquier MCP server.

| Component | Detalle |
|---|---|
| Add Browserbase MCP to `rdm-bot/.claude/mcp.json` | Permanent |
| Document patterns in `cc-instructions-bot/` for browser ops | Reference for future CC sessions |
| Browserbase secrets via Worker secrets | Auth tokens |
| Persistent session config | Auth survives runs |
| Cost monitoring alert | Avoid surprise bills |

---

## 3 · Decisions (closed)

| Decision | Value |
|---|---|
| Tool primary | Browserbase + Stagehand |
| Tool fallback / dev | Chrome MCP one-shot |
| Cron frequency | Weekly (lower detection risk) |
| Anti-bot tier | Browserbase residential IPs + stealth |
| Multi-site support | Yes (general infra) |
| Special Offers automation | OUT — confirmed Alex 2026-05-19 |
| Booker auto write AirBnB | OUT — not planned |
| Booking.com KPIs | DEFER — focus AirBnB first, replicate pattern later |
| Account billing | Alex personal/RdM account (Alex choice) |
| Effort budget | Phase 1+2 = 10-16h CC total |
| Stop trigger | If detection issues in Phase 1, defer indefinitely |

---

## 4 · Out of scope (this thread)

- NO Special Offers automation
- NO Bot Booker auto write to AirBnB
- NO Booking.com extranet integration (separate future thread)
- NO scraping competitors / market intelligence
- NO bypass of AirBnB ToS (we use legitimate host access only)
- NO 24/7 cron (weekly max for detection avoidance)

---

## 5 · Risks + mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | AirBnB blocks/warns account | Rate limit aggressive (weekly), residential IPs, randomized timing, halt immediately on warning |
| R2 | Browserbase cost overruns | Set budget alerts in CF/Browserbase dashboard, weekly review first month |
| R3 | UI changes break scraper | Stagehand LLM-native targeting is resilient; tests cover selectors |
| R4 | Auth session expires | Persistent context + re-auth flow via Alex one-time per N weeks |
| R5 | Browserbase service downtime | Cron retry next interval, no real-time dependency |
| R6 | KPIs inaccurate (UI differs from internal calc) | Cross-check with Beds24 data for sanity, log discrepancies |
| R7 | Alex's AirBnB account compromise risk | Use API tokens where possible, Browserbase secrets encrypted |

---

## 6 · Dependencies

| Dep | Status |
|---|---|
| A5 thread/127 complete | 🟡 In progress |
| Alex account Browserbase | ❌ Pending |
| Browserbase budget approved | ❌ Pending |
| AirBnB hosting credentials secured | ✅ Alex has |
| Chrome MCP A5 complete | 🟡 In progress thread/127 |

---

## 7 · Definition of done (entire backlog item)

- [ ] Phase 1 eval complete with success criteria met
- [ ] Phase 2 KPI scraper shipped + visible in `/admin/airbnb-kpis`
- [ ] First KPI weekly cron runs successfully
- [ ] Phase 4 CC autonomous can invoke Browserbase tools
- [ ] Documentation in `cc-instructions-bot/` updated with Browserbase patterns
- [ ] Memory updated with new infra tooling

---

## 8 · Order in queue

| Priority | Item |
|---|---|
| 1 | thread/128 (omnibus) — in progress |
| 2 | thread/127 (A5) — pending Chrome MCP setup |
| 3 | thread/131 (mobile inbox Part E rescue) |
| 4 | Bot Greeter Airbnb conv brain deep (pending Alex's 7 decisions) |
| 5 | **THIS · thread/132 Browserbase eval Phase 1** |
| 6 | Phase 2 AirBnB KPI scraper (post-eval) |
| 7 | Phase 4 CC autonomous integration |

---

## 9 · Notes

- **Memory correction**: WC's memory #11 incorrectly said "Reviews API beta = P1 ingestion". Reviews API actually shipped (reviews-sync.ts + migration 0012 + /api/reviews + ReviewsCarousel + bot KB enrichment). Updated 2026-05-19. Lesson: cross-check repos before claiming "pending".

- **BACKLOG.md cleanup needed**: P3-G section says "Reviews ingestion P1: Spec pending" and "Bot KB enrichment con reviews: Spec pending" — both INCORRECT. Update BACKLOG.md to reflect shipped status.

- **Why Special Offers OUT**: Alex confirmed 2026-05-19 that pattern no longer used. Recordatorios solo are now via Beds24 messages API (already shipped). This significantly reduces the scope of browser automation we'd need.

- **Why Chrome MCP NOT migrated retroactively for A5**: One-shot acceptable cost. Migration overhead > one-shot pain.

---

WC out.

Esta capability open future for AirBnB KPI visibility + general purpose scraping para futuras necesidades sin que cada caso reinvente la rueda.
