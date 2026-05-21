# Thread 158 · CC · Admin Tools Audit (2026-Q2-v2) · §08 Tech Validation SHIPPED

**From**: Claude Code (rdm-bot session)
**To**: Alex, WC-Platform, WC-Implementation
**Date**: 2026-05-21 (late evening MX)
**Status**: ✅ §08 committed · independent of §07 (does not yet exist) and §09 (Day 2) per spec hard rule

---

## §A · Deliverable

- `rdm-platform/reports/admin-audit-2026-Q2-v2/08-cc-tech-validation.md` · commit `fe41254`
- Per-tool tech-health validation for **12 live admin pages + collective `coming-soon` stub** (13 cards total)
- Follows audit spec §3 structure (§A setup · §B per-tool table + detail · §C cross-cutting · §D WC-Impl prelim validation · §E verdict)
- Effort: ~3h (within target)

## §B · Method (and the gap)

Pre-flight clean:
- bot HEAD `cd4b13f` · platform HEAD `390bc5b`
- `pnpm --filter web build` → exit 0, **zero warnings** across all admin pages
- `pnpm --filter web dev` ready in 2.2s, no startup errors
- curl HTTP probe: every `/admin/*` route returns 302 → `/login?next=...` (expected — middleware-gated)

**Chrome MCP was not attached** (no Chromium running with `--remote-debugging-port=9222`; mirrors thread/130 finding). The spec asks for live mobile breakpoint testing + console error capture; without an authenticated browser session this validation substitutes static CSS / source analysis.

Validation therefore combines:
1. `pnpm build` (compile-time check across all admin pages)
2. curl HTTP status probe of every route
3. Source-level audit of each page's Astro file + its React island components
4. Static check of CSS `@media` queries vs the 320 / 720 / 1024 px audit spec targets

Live click-throughs, browser console capture, viewport-rendered screenshots, and Lighthouse timings are gaps. See §E of the audit file for the honest disclosure (5 documented gaps).

## §C · TL;DR findings

### C.1 · Net-new 🔴 (1)

- **B.9 / C.1** — `karina-training/index.astro` mobile breakpoint at **900px**, not 720px. At a 720px landscape-phone viewport (Karina's likely device class), the sticky TOC sidebar still attempts side-by-side layout, squeezing content. WC-Impl prelim rated this page 🟢 tech ("static HTML, sin queries") — accurate at the architecture level, but missed this breakpoint. ~15 min fix; suggest a 1-line PR (`max-width: 900px` → `720px`) after Alex review, ahead of broader synthesis.

### C.2 · Net-new 🟡 (5)

1. **Mobile breakpoint inconsistency** across admin (720 / 768 / 900 / 960 / 1100) — no project-wide responsive constants
2. **`PROPERTY_NAMES: Record<number, string>` duplication** in `extra-guests.astro:83-88` and `pre-stay.astro:75-81` — adds 2 more sites to my prior `audit-2026-Q2 C.8` (8 sites); total ≥10
3. **Empty-state UX delegated to React islands** in 4 pages (extra-guests, airbnb-content, pre-stay, audit-logs) instead of server-rendered → potential FOUC on slow devices
4. **TemplateEditor.tsx sole breakpoint at 960px** — 33% viewport gap from 720 where editor stays mobile-collapsed despite being on a tablet
5. **`coming-soon.astro` `featureDescriptions` decoupled from `NAV_HREFS`** — silent drift possible when a placeholder is added; renders fallback copy without warning

### C.3 · Confirmation of WC-Impl prelim findings

- `templates/index.astro:193,197` — `prompt()` + `alert()` anti-pattern: **confirmed at exact line numbers**
- `conv.astro:254` — `confirm()` reset guard: **confirmed**
- `extra-guests.astro:99` — `MESSENGER_OUTBOUND_ENABLED` env-var name visible in user-facing lede: **confirmed**
- `bot-metrics.astro` — 28,396 bytes / 773 lines (WC-Impl said 27.6 KB): **confirmed**
- `karina-training/index.astro` — 216,646 bytes / 3,538 lines (WC-Impl said 213 KB): **confirmed**
- `health.astro` — 5 parallel queries via `Promise.all`: **confirmed, excellent shape**
- `audit-logs.astro:345` — `overflow-x: auto` on table: **confirmed, best-in-class mobile-table handling**
- 14 placeholders in NAV_HREFS: **confirmed exactly**
- `pre-stay.astro:62` — Casa Chamán exclusion via `room_id != 679176`: **confirmed**

WC-Impl prelim accuracy: **12 of 13 tool cards spot-on**. Sole adjustment: B.9 karina-training degrade from 🟢 to 🟡 due to mobile-breakpoint finding.

### C.4 · Lede word-count caveats

WC-Impl content-audit overstated lede length on 2 pages — both directionally correct but numerically off:
- B.5 conv: WC-Impl 75 words → actual ~35 (page does have ~120 words of pre-action prose including `<h2>` + `.hint`, so WC-Impl's number reflects the full pre-action region, not the `.lede` element)
- B.7 pre-stay: WC-Impl ~110 words → actual ~85
- B.4 extra-guests: WC-Impl ~95 words → actual ~80

Documenting for synthesis; doesn't change WC-Impl's directional finding that the pages front-load prose.

## §D · No blockers, but a recommendation

The audit can proceed to Day 2 synthesis on this validation file. No tool is broken. No 5xx fires. No new 🔴 affects more than 1 page.

**One concrete pre-synthesis hotfix opportunity**: the karina-training 720px breakpoint. A 1-line CSS change with low risk. If Alex green-lights, CC can ship after Day-2 synthesis lands (so it doesn't churn the audit input).

## §E · Audit gaps (honest disclosure — §08 §E)

1. No live browser testing (Chrome MCP not attached)
2. No D1 evidence — could not run `wrangler d1 execute`; row counts cited in WC-Impl audit accepted as given
3. No primer-paint timing — Lighthouse not run
4. React islands surface-only (CSS + console + link patterns); behavioral audits (empty-row rendering inside `<InboxView>` etc.) not done
5. Admin proxy API endpoints (`/api/admin/conv/...` etc) explicitly out of scope per spec

A follow-up live smoke pass with authenticated browser + Chrome MCP attached + local D1 seeded would surface additional findings, especially in items 4 and 5. Flagged for §H Synthesis Questions if warranted.

## §F · Status

```
✅ Day 0  · WC-Impl       · admin-audit-2026-Q2-v2 (thread/156)
🟡 Day 1  · WC-Platform   · 07-wc-platform-review.md      (pending — not in repo as of my commit)
✅ Day 1  · CC            · 08-cc-tech-validation.md      (this thread)
🟡 Day 2  · WC-Platform   · 09-synthesis-bigbang.md
🟡 Day 3  · Alex          · vote Top X + ADR-004 candidate
```

CC standing by for synthesis-pass clarifications. Independence period over from CC's side (I can now read §07 once it lands + §09 when authored).

---

## §G · UPDATE 2026-05-21 late evening · Live validation pass added (§F addendum to §08)

After the initial commit, Alex launched Chrome with `--remote-debugging-port=9222` and logged into prod `/admin`. CC re-validated all 13 routes live at 1280/720/320 viewports against real prod D1 data. Committed as §F appendix to `08-cc-tech-validation.md` (platform `main`, commit `9e12279`).

### G.1 · Material correction — one of my net-new 🔴 was wrong

**§B.9 karina-training 900px breakpoint finding was based on misreading the CSS.** `@media (max-width: 900px) { .kt-doc-wrap { grid-template-columns: 1fr } }` DOES fire at 720px (since 720 < 900) — the TOC collapses to a top strip exactly as designed. Live screenshot at 720×900 confirms the breakpoint works. WC-Impl's original 🟢 prelim for B.9 stands; my §D adjustment of "degrade 🟢→🟡" was wrong.

**Updated tally**: net-new 🔴 across entire validation = **0** (not 1 as the original ack claimed).

### G.2 · New live-only findings (couldn't see these via static analysis)

| ID | Severity | Description |
|---|---|---|
| F.2 | 🟡 | karina-training **page-level horizontal overflow at 320px** — wide SVG diagram or `<pre>` element doesn't shrink. Real mobile UX issue. ~30 min fix. |
| F.4 | 🟢 | Every authenticated admin page emits 1-2 preload warnings for `page.BT_9kWGp.js` (`crossorigin` attribute mismatch). Upstream Astro config fix. |
| F.5 | 🟡 | `/admin/inbox` searchbox + `/admin/bookings` filters (3 fields) lack `name`/`id` — Chrome flags as a11y `[issue]`. ~10 min. |
| F.7 | 🟡 | `/admin/inbox` Beds24-only rows: clicking the booking ID navigates to `/admin` (home). Source: `InboxView.tsx:79-82` — `convPathForRow` returns `'/admin'` as fallback. Soft 404 UX trap. ~15 min to wire to `/admin/bookings?id=...`. |

### G.3 · Prod data state deltas vs WC-Impl snapshot

- `/admin/inbox`: **275 rows / 260 need attention** (was 100 unread / 4 critical in WC-Impl). State breakdown: 3 Critical / 77 Escalated / 123 Stalled / 57 Unread (Beds24) / 15 Resolved. Ops gap deepening.
- `/admin/templates`: **prod R2 bucket is EMPTY** ("No hay templates todavía"). The `prompt()` + `alert()` anti-pattern UX has never been exercised by Karina because no templates exist. Worth a synthesis discussion — is `/admin/templates` dormant?
- `/admin/bot-metrics`: Greeter v5 canary at **100%** (last config update by `alex-stage1` 4d ago); 59 clicks last 24h, top intents `casas` 32% / `disponibilidad` 19% / `cotizar` 12%. WORKER HEARTBEAT 6min ago (`cron-client-bot-poll`).
- `/admin` dashboard: 5,874 total leads, 91 bot turnos 24h, 2.6s latencia.

### G.4 · WC-Impl prelim accuracy revised

- **B.2 `/admin/inbox`** — prelim said "Phase 1 read-only"; **prod is Phase 2**: Reply button + Resolve + Escalate + Beds24 deep-link all live per InboxView.tsx:466-522 and confirmed visually. Framing update recommended in `01-tool-cards.md`.
- **B.9 `/admin/karina-training`** — keep WC-Impl's 🟢 prelim (my downgrade was based on the wrong F.1 finding).
- **B.8 `/admin/templates`** — prelim still accurate at code level, but add live note: "prod R2 bucket empty 2026-05-21; anti-pattern UX never exercised."
- The other 10 cards: prelim spot-on.

### G.5 · Updated effort tally

- Original static §08: ~3h
- Live §F addendum: ~30 min (browser-driven smoke pass + addendum write-up)
- **Cumulative**: ~3.5h actual vs 3h estimated — over by 30 min, but the live pass closed the biggest gap from the original §E disclosure.

---

**Signed**: Claude Code, rdm-bot session, branch `chore/process-improvements-thread-146`, ~3.5h cumulative effort. Chrome MCP attached for §F live pass; gap #1 of original §E ("no live browser") closed within the same audit window.

Per spec §6 hard rule: did NOT read `07-wc-platform-review.md` (does not yet exist in repo) nor `09-synthesis-bigbang.md` (does not yet exist) prior to my commit. Did read `00-foundation.md`, `01-tool-cards.md`, README, and my own prior `audit-2026-Q2/03-technical-audit-cc.md` for cross-reference.
