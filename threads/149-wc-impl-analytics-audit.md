# Thread 149 · WC-Implementation · Analytics tracking audit · 0 trackers active in prod

**From**: WC-Implementation
**To**: Alex
**Date**: 2026-05-19 (late evening)
**Re**: Alex question "checa landing page a ver si usamos cloudflare Analytics or GSC, a quien le enviamos datos?"
**Type**: finding · informational · low urgency
**Status**: Open · needs Alex decision tomorrow on activation

---

## TL;DR

The landing page (and all `apps/web` pages) include `<CFAnalytics />` and `<GA4 />` components in `BaseLayout.astro`, but **neither emits in production**. Both are guarded by env var checks and the env vars are NOT declared in `apps/web/wrangler.toml`.

**Today, the site sends data to:**
- ✅ Cloudflare HTTP-proxy logs (passive server-side, not queryable from WC)
- ❌ Cloudflare Web Analytics → NO (token missing)
- ❌ Google Analytics 4 → NO (gaId missing)
- ❌ Search Console → unverifiable from HTML, possibly via DNS TXT, Alex confirm
- ❌ Anything else → NO

This is a **dormant capability**: code is shipped, activation is one env var + deploy away.

---

## Evidence

Read via `get_file_contents` (no code modified):

### `apps/web/src/layouts/BaseLayout.astro` (verified · main · SHA `2809f2c`)

```astro
import CFAnalytics from '@/components/ui/CFAnalytics.astro';
import GA4 from '@/components/ui/GA4.astro';
...
<SEO {...seo} lang={lang} />
<CFAnalytics />
<GA4 />
```

### `apps/web/src/components/ui/CFAnalytics.astro` (verified)

```astro
const token = import.meta.env.PUBLIC_CF_ANALYTICS_TOKEN ?? '';
{token && (
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" ... />
)}
```

Empty token → no `<script>` emitted.

### `apps/web/src/components/ui/GA4.astro` (verified)

```astro
const gaId = (import.meta.env.PUBLIC_GA4_ID as string | undefined) ?? '';
const enabled = gaId && !import.meta.env.DEV;
{enabled && ( /* gtag scripts */ )}
```

Empty gaId → no `<script>` emitted.

The GA4 component has a historical comment worth noting:

> "Create a new GA4 property at https://analytics.google.com (recomendado: dedicated al sitio nuevo, **no reusar G-KXE1Q1G6M3 del tour viejo** para data clean)"

So there was an old GA4 property `G-KXE1Q1G6M3` (the virtual tour site), but the recommendation was NOT to reuse it. New GA4 property was never created.

### `apps/web/wrangler.toml` `[vars]` section (verified · main · SHA `9e7f59c`)

Variables declared:
- `SITE_URL`, `PUBLIC_WHATSAPP_NUMBER`, `ADMIN_EMAILS`, `CONTENT_EDITOR_EMAILS`, `CHEF_EMAILS`, `STAFF_EMAILS`, `TECNICO_EMAILS`, `COMPRAS_EMAILS`, `PUBLIC_CF_IMAGES_HASH`, `STAFF_PROX_RESERVAS_PASS`

Variables NOT declared:
- ❌ `PUBLIC_CF_ANALYTICS_TOKEN`
- ❌ `PUBLIC_GA4_ID`

CF Pages dashboard env vars: NOT verifiable from WC, but components rely on `import.meta.env.PUBLIC_*` which Astro reads from **build-time** env (`wrangler.toml [vars]` is the source for CF Pages). So if not in wrangler.toml, very unlikely to be set elsewhere.

### Live HTML verification

```
curl -s https://rincondelmar.club/ | grep -iE "cloudflareinsights|googletagmanager|gtag|data-cf-beacon"
→ 0 matches
```

Response headers confirm CF proxy active (`server: cloudflare`, `cf-ray`, `nel`), so HTTP-level logs exist passively on CF side. Not queryable from this MCP setup.

### `<head>` content summary (live HTML)

Present:
- Standard meta (charset, viewport, theme-color)
- SEO meta tags (canonical, hreflang, og:*, twitter:*)
- Two `<script type="application/ld+json">` blocks (Organization + WebSite structured data, **good for SEO** — Google reads these even without GSC)
- Cloudflare Rocket Loader (auto-injected by CF, unrelated to analytics)
- Service Worker registration

NOT present:
- CF Beacon
- GA4 gtag
- GTM container
- Meta Pixel
- TikTok Pixel
- Any tracker

---

## What this means

### Pros of current state

- **Zero cookie load** = zero cookie consent banner needed (philosophy alignment with `vision/01-philosophy.md` §minimalism)
- **GDPR/LGPD compliance is trivial** (no PII collected client-side)
- **Page load is faster** (no third-party JS)
- **No vendor data exfiltration** to Google/Facebook

### Cons of current state

- **Zero visibility on traffic patterns**: which pages get traffic, which referrers send users, which devices/countries, bounce rate, time-on-page, scroll depth
- **Zero conversion funnel data**: how many `Cotizar` clicks → contact form submits → bookings
- **Zero A/B test signal**: the landing has `data-ab-variant="a"` and `data-ab-cta` attributes in HTML (verified live), suggesting A/B testing infrastructure was set up, but no analytics to read the variant performance from
- **Zero attribution**: paid spend (if any) has no measurable ROI
- **Zero SEO insight from CTR / impressions** without Search Console
- **Zero crawler-error visibility** (Google indexed pages, 404 reports)

### What IS visible passively

CF Dashboard → Analytics & Logs → HTTP Traffic shows (server-side, no JS needed):
- Total requests / unique visitors estimate
- Top countries
- HTTP status codes distribution
- Cache hit ratio
- Bandwidth

This is **enough for "is the site getting traffic"** but **not for SEO** or **conversion analysis**.

---

## Reactivation options

### Option 1 · Cloudflare Web Analytics only (minimal, cookieless)

**Effort**: 10 min Alex + 5 min CC + deploy
- Alex: CF Dashboard → Analytics & Logs → Web Analytics → Add a site → copy token
- CC: add `PUBLIC_CF_ANALYTICS_TOKEN = "abc123..."` to `apps/web/wrangler.toml [vars]`, deploy

**Gets**: page views, top URLs, referrers, countries, Core Web Vitals, devices

**Compliance**: cookieless, no banner needed

**Trade-off**: less detail than GA4 (no events, no funnels), but enough for SEO triage

### Option 2 · CF Web Analytics + GA4

**Effort**: Option 1 + 15 min Alex (create new GA4 property) + 5 min CC + deploy

**Gets**: everything from Option 1 + custom events (already wired in code: `tour_loaded`, `tour_scene_change`, `tour_to_whatsapp`, `linktree_click`, `booking_quote_view`, `booking_pay_clicked`), conversion funnels, demographic data, lifetime user tracking

**Compliance**: GA4 sets cookies (`_ga`, `_ga_*`). If EU traffic is non-trivial (TBD), needs consent banner. The GA4 component file explicitly notes this trade-off:

> "Cookie consent: por ahora SIN banner (consistencia con CF Analytics que tampoco lo tiene). Si entra tráfico EU significativo, agregar Cookiebot o similar como sprint separado."

### Option 3 · Add Google Search Console (independent of 1 & 2)

**Effort**: 20 min Alex (DNS TXT verification + property setup)

**Gets**: query terms users type into Google to find the site, CTR per query, average position, indexed pages, crawl errors, sitemap submission

**Compliance**: none (server-side, no JS)

**Critical for SEO**: this is the primary tool. CF Analytics + GA4 measure traffic that arrives. GSC tells you **why and from what query**. For SEO work specifically, GSC is non-negotiable.

### Option 4 · Bing Webmaster Tools

Smaller traffic share (~3% in MX), but free and 10 min setup. Optional.

---

## Existing A/B testing infrastructure (bonus finding)

The live landing has these DOM attributes (verified via curl):

```html
<section class="hero" data-ab-variant="a" ...>
  <a class="btn" href="/contacto" data-ab-cta data-ab-variant="b" data-cta="quote">
  <a class="btn btn-secondary" href="#casas" data-ab-cta data-ab-variant="b" data-cta="see-homes">
```

Without analytics, the variant signal is invisible. Activating CF Web Analytics or GA4 would immediately unlock reading these data attributes against page outcomes. Worth noting in the activation spec.

---

## Custom GA4 events already wired

Per `GA4.astro` component comment, these events emit when GA4 ID is set:

| Event | Where |
|---|---|
| `tour_loaded` | PannellumTour component |
| `tour_scene_change` | PannellumTour |
| `tour_to_whatsapp` | PannellumTour |
| `linktree_click` | LinktreePage |
| `booking_quote_view` | BookingCard |
| `booking_pay_clicked` | BookingCard (currently disabled) |

So Option 2 unlocks rich product-level signal with zero additional CC work — just set the env var.

---

## My recommendation

**Tomorrow morning, take the 30 min to do all three** (Option 1 + Option 2 + Option 3 in parallel by Alex):

1. CF Web Analytics token → CF dashboard (10 min)
2. New GA4 property `G-XXXXXXXXXX` → Google Analytics (15 min)
3. Search Console verification → DNS TXT record (20 min, Alex)

Then CC ships one PR adding both env vars to `wrangler.toml` and deploys.

Cookie consent banner: defer until first EU-traffic data point shows it's worth the work. Currently zero EU customers per business reality (MX-CDMX/Edomex/Puebla market). If GA4 shows >5% EU traffic, sprint a banner.

**Decision needed from Alex tomorrow** (no urgency tonight): pick Option 1/2/3/all + I write the spec for CC to execute.

---

## Cross-references

- thread/147 §E item 5-7 (Alex pending confirmations on F2 observability) — this audit is adjacent: F2 monitors WORKER metrics, CF Web Analytics + GA4 + GSC monitor USER metrics. Both serve "is the system healthy" but different layers.
- `STATE.md` §G — to add as new outstanding decision item

---

## Boundary respected

- ✅ Written in `rdm-discussion` (WC-Impl primary writer territory)
- ✅ NO writes to `rdm-bot` code
- ✅ NO writes to `rdm-platform`
- ✅ Evidence-based: 3 files read from `rdm-bot/main`, 1 live HTML curl

---

**Signed**: WC-Implementation, brain mode, 2026-05-19 late evening
