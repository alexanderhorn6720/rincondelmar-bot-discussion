# Thread 141 · WC handoff CC · House rules paper trail Phase 1 (welcome + T-7)

**From:** WC
**To:** CC-Bot
**Date:** 2026-05-19
**Type:** DoIt autonomous
**Order:** After thread/139 A6 deploy. Independent of all in-flight work.
**Estimated:** 3-5h CC autonomous
**Output thread:** thread/142
**Depends on:** thread/139 deployed (reglas_adicionales live in AirBnB + R2 source of truth)

---

## 1 · Context

Alex needs paper trail proving guests received house rules BEFORE arrival, for legal/AirCover defense in disputes. Decision (Alex 2026-05-19 chat with WC):

- **Phase 1 (this thread)**: Touch 1 (welcome) + Touch 2 (T-7) only
- Phase 2 (acknowledgment portal): deferred to post-Phase 1 validation
- Phase 3 (smart risk-tier routing): backlog
- **Audience**: Airbnb-first wording. Direct booking variant = backlog (find/replace ~9 strings)
- **Format**: text message Airbnb + link to public rules page + PDF attachment optional
- **Source of truth**: R2 reglas_adicionales (from thread/139 deploy)
- **NOT**: hidden in folleto, separate set for direct guests, signed legal contract

Infrastructure already exists:
- `apps/worker-bot/src/pre-stay-templates.ts` has 7 touchpoints × 4 props × 2 langs
- `apps/worker-bot/src/pre-stay.ts` orchestrates send via Beds24 messages API
- `apps/worker-bot/src/welcome-auto-send.ts` for confirmation-time send
- `/admin/pre-stay` for monitoring

This thread **adds** house rules mention + link + optional PDF attachment to:
- `welcome` template (sent on booking confirmation)
- `t7` template (sent 7 days before arrival)

---

## 2 · Pre-flight (mandatory, ~5 min)

```bash
# Sync repos
cd <rdm-discussion> && git pull origin main
cd <rdm-bot>        && git pull origin main

# Verify spec
ls <rdm-discussion>/threads/141-wc-cc-house-rules-paper-trail-phase1.md

# Verify thread/139 A6 deployed (reglas live in R2 + AirBnB)
curl -s https://rincondelmar.club/api/admin/airbnb-content/rincon-del-mar/es/reglas_adicionales | jq '.field.deployed_at'
# Expected: ISO timestamp post-2026-05-19

# Verify pre-stay templates infra
ls apps/worker-bot/src/pre-stay-templates.ts
grep -c "T_WELCOME_\|T_T7_" apps/worker-bot/src/pre-stay-templates.ts
# Expected: 8+ welcome templates + 8 T-7 templates = 16+ matches

# Verify public rules page does NOT exist yet (we build it)
ls apps/web/src/pages/reglas/ 2>/dev/null && echo "EXISTS" || echo "NEEDS BUILD"
```

If any pre-flight fails → halt + Telegram Alex.

---

## 3 · Scope

### ✅ YES — en scope

1. Build public page `apps/web/src/pages/reglas/[slug].astro` (4 properties)
   - Renders `reglas_adicionales` from R2 source of truth
   - Mobile-friendly responsive
   - Per-property URL: `rincondelmar.club/reglas/rincon-del-mar`, `/reglas/las-morenas`, etc.
   - Defaults ES, accepts `?lang=en` query
   - Header with property photo + title
   - Footer same canonical "— Alexander 🌅 · rincondelmar · club"
   - Print-friendly CSS (since some guests will save/print)
   - No login required (public)

2. Generate PDF version per property/lang (optional attachment)
   - Use existing `apps/skills/pdf` or wkhtmltopdf or puppeteer-print
   - Path: R2 bucket `rdm-knowledge/reglas-pdf/{prop}-{lang}.pdf`
   - Regenerates on each content deploy (hook into `deploy-confirmed`)
   - File ~200-400 KB max

3. Update `welcome` templates (4 props × 2 langs = 8)
   - Add rules section after warm intro, before tactical info
   - Reference `rincondelmar.club/reglas/{slug}?bookingId={id}` link
   - Tone: hospitable but firm — "Aceptarlas es parte de tu reserva"
   - Lang-aware (ES + EN versions)

4. Update `t7` templates (4 props × 2 langs = 8)
   - Stronger reminder language
   - Same link
   - Add explicit checklist: "Confirma que tu grupo recibió las reglas"
   - Optional PDF attachment via Beds24 messages API

5. Add `bookingId` parameter to template input (for trackable link)
   - Track which bookings clicked the rules link
   - D1 table `rules_link_clicks` for audit trail

6. Tests: vitest for template rendering with new sections

### ❌ NO — out of scope (separate threads)

- Phase 2: Acknowledgment portal `/g/[token]/checkin` with explicit consent
- Phase 3: Risk-tier routing (auto-detect high-risk bookings)
- Direct booking variant of rules (find/replace 9 Airbnb mentions)
- Physical signature at check-in
- Pre-stay flow for non-Airbnb channels (direct, Booking.com)
- Image/infografía version
- Custom PDF design with photos (Phase 1 = basic PDF only, fancy design later)
- Touchpoint changes to t14, t1, arrived, pre_checkout, post_stay (only welcome + t7)

---

## 4 · Closed decisions (Alex 2026-05-19)

| Decision | Value |
|---|---|
| Phase 1 scope | Touch 1 (welcome) + Touch 2 (t7) only |
| Audience Phase 1 | Airbnb guests primary, direct backlog |
| PDF format | Basic (text + structure), no fancy design |
| Hide in folleto? | NO. Reglas visible y prominentes. |
| Separate set for direct? | NO. One set with backlog for direct find/replace. |
| Acknowledgment portal? | Phase 2, deferred |
| Physical signature? | NO Phase 1, backlog only for high-risk |
| Source of truth | R2 `reglas_adicionales` (post-thread/139) |
| Public page URL | `rincondelmar.club/reglas/[slug]` |
| Tracking | D1 `rules_link_clicks` per booking |

---

## 5 · Implementation

### Phase A · Public rules page (1-1.5h)

`apps/web/src/pages/reglas/[slug].astro`:

```astro
---
import Layout from '@/layouts/Layout.astro';
import { getContentDraft, getDeployedField } from '@/lib/airbnb-content-storage';

const { slug } = Astro.params;
const lang = Astro.url.searchParams.get('lang') === 'en' ? 'en' : 'es';
const bookingId = Astro.url.searchParams.get('bookingId') ?? null;

if (!['rincon-del-mar', 'las-morenas', 'combinada', 'huerta-cocotera'].includes(slug)) {
  return Astro.redirect('/404');
}

// Pull from R2 deployed snapshot (latest version)
const rules = await getDeployedField(Astro.locals.runtime.env, slug, lang, 'reglas_adicionales');

// Track click if bookingId present
if (bookingId) {
  await Astro.locals.runtime.env.DB.prepare(`
    INSERT INTO rules_link_clicks (booking_id, property_slug, lang, clicked_at, user_agent, ip)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(
    bookingId,
    slug,
    lang,
    Math.floor(Date.now() / 1000),
    Astro.request.headers.get('user-agent') ?? null,
    Astro.request.headers.get('cf-connecting-ip') ?? null,
  ).run().catch(err => console.error('click track failed', err));
}

const propertyDisplayNames = {
  'rincon-del-mar': 'Villa Rincón del Mar',
  'las-morenas': 'Villa Las Morenas',
  'combinada': 'Villas Combinadas (RdM + Morenas)',
  'huerta-cocotera': 'Huerta Cocotera',
};
---

<Layout title={`Reglas · ${propertyDisplayNames[slug]}`}>
  <main class="reglas-page">
    <header class="reglas-header">
      <h1>{propertyDisplayNames[slug]}</h1>
      <p class="reglas-subtitle">Reglas de la Casa</p>
      <a href={`/reglas/${slug}/pdf?lang=${lang}`} class="reglas-pdf-link">
        📄 Descargar PDF
      </a>
      <div class="reglas-lang-switcher">
        <a href={`?lang=es`} class={lang === 'es' ? 'active' : ''}>Español</a>
        <a href={`?lang=en`} class={lang === 'en' ? 'active' : ''}>English</a>
      </div>
    </header>

    <article class="reglas-content">
      <!-- Render rules markdown / plaintext with section emoji headers preserved -->
      <pre class="reglas-text">{rules.content}</pre>
    </article>

    <footer class="reglas-footer">
      <p>Última actualización: {new Date(rules.deployed_at).toLocaleDateString()}</p>
    </footer>
  </main>
</Layout>

<style>
  .reglas-page {
    max-width: 720px;
    margin: 0 auto;
    padding: 24px 16px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
  }
  .reglas-header h1 { margin: 0 0 4px; }
  .reglas-subtitle { color: #666; margin: 0 0 16px; }
  .reglas-pdf-link {
    display: inline-block;
    padding: 8px 16px;
    background: #f0f0f0;
    border-radius: 8px;
    text-decoration: none;
    color: #000;
    margin-bottom: 12px;
  }
  .reglas-lang-switcher a {
    margin-right: 12px;
    text-decoration: none;
    color: #666;
  }
  .reglas-lang-switcher a.active { font-weight: 600; color: #000; }
  .reglas-text {
    white-space: pre-wrap;
    font-family: inherit;
    font-size: 14px;
    background: transparent;
    padding: 0;
  }
  @media print {
    .reglas-pdf-link, .reglas-lang-switcher { display: none; }
  }
</style>
```

### Phase B · D1 migration (15 min)

`migrations/00XX_rules_link_clicks.sql`:

```sql
CREATE TABLE IF NOT EXISTS rules_link_clicks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id TEXT,
  property_slug TEXT NOT NULL,
  lang TEXT NOT NULL,
  clicked_at INTEGER NOT NULL,
  user_agent TEXT,
  ip TEXT
);

CREATE INDEX idx_clicks_by_booking ON rules_link_clicks(booking_id);
CREATE INDEX idx_clicks_recent ON rules_link_clicks(clicked_at DESC);
```

Apply via:
```bash
pnpm wrangler d1 migrations apply rincon --remote
```

### Phase C · PDF generation (1h)

Use `apps/skills/pdf` if available, OR implement simple via Workers:

Option 1 — On-demand at request time:
- Route `/reglas/[slug]/pdf` renders Astro page → puppeteer-cloudflare → PDF blob
- Cache 24h via Cache API

Option 2 — Pre-generated on deploy:
- Hook in `deploy-confirmed.ts` for reglas_adicionales field
- Generate PDF after successful deploy, save to R2 `rdm-knowledge/reglas-pdf/{slug}-{lang}.pdf`
- Public link: `https://rincondelmar.club/reglas-pdf/{slug}-{lang}.pdf`

**Mi voto: Option 2** (pre-gen + R2 cache). Cheaper at request time.

Skill reference: read `/mnt/skills/public/pdf/SKILL.md` for current best practice in this repo.

### Phase D · Update welcome templates (45 min)

Edit `apps/worker-bot/src/pre-stay-templates.ts`. Add **rules paragraph** between intro and tactical info in all 8 welcome templates:

```typescript
// RdM welcome ES (existing intro preserved)
const T_WELCOME_RDM_ES = `¡Hola {guestFirstName}! 🌅

¡Qué emoción recibirlos en Villa Rincón del Mar!
Llegada el {arrivalFmt} desde las 3 PM, salida el {departureFmt} hasta las 11 AM — ya estamos preparándoles unas vacaciones inolvidables.

📋 Antes de tu llegada, te pido leer nuestras reglas de la casa:
   👉 rincondelmar.club/reglas/rincon-del-mar?bookingId={bookingId}

Son cortas y las aplicamos — mejor las conoces antes de llegar para evitar sorpresas. Por favor compártelas con tu grupo.

Soy Alexander, dueño de RdM (9 años recibiendo huéspedes en Acapulco). Karina, nuestra encargada, los recibe en persona el día de llegada y está disponible durante toda su estancia.

[... rest of existing template ...]`;
```

Same pattern × 8 templates (4 props × ES/EN). EN version:

```typescript
const T_WELCOME_RDM_EN = `Hi {guestFirstName}! 🌅

We're thrilled to host you at Villa Rincón del Mar!
Arrival {arrivalFmt} from 3 PM, departure {departureFmt} by 11 AM — we're already preparing unforgettable vacations for you.

📋 Before arrival, please read our house rules:
   👉 rincondelmar.club/reglas/rincon-del-mar?lang=en&bookingId={bookingId}

They're short and we enforce them — best to know them in advance to avoid surprises. Please share with your group.

[... rest of existing template ...]`;
```

Update `TemplateInput` interface to include `booking_id: string`:

```typescript
export interface TemplateInput {
  // ... existing fields
  booking_id: string;  // ADDED — for trackable rules link
}
```

Update `renderTemplate()` to substitute `{bookingId}` placeholder.

### Phase E · Update t7 templates (45 min)

Same pattern, stronger language. Example RdM ES:

```typescript
const T_T7_RDM_ES = `¡Hola {guestFirstName}! 

Faltan 7 días para su llegada a Rincón del Mar. ¡Ya casi!

📋 Recordatorio importante: reglas de la casa
   👉 rincondelmar.club/reglas/rincon-del-mar?bookingId={bookingId}

Si aún no las has leído con tu grupo, por favor hazlo ahora. Las reglas cubren:
✅ Capacidad y huéspedes adicionales
✅ Mascotas (si traes, avísanos)
✅ Daños y AirCover
✅ Mar abierto (¡atento al oleaje!)
✅ Horarios estrictos de entrada/salida
✅ Cero tolerancia con personal

[... existing T-7 tactical content ...]`;
```

### Phase F · Wire PDF attachment in Beds24 send (optional, 30 min)

If Beds24 messages API supports attachments (verify in pre-flight):

In `pre-stay.ts` send logic, for `t7` touchpoint:

```typescript
if (touchpoint === 't7' && env.PDF_ATTACHMENT_ENABLED === 'true') {
  const pdfUrl = `https://rincondelmar.club/reglas-pdf/${slug}-${lang}.pdf`;
  // Per Beds24 v2 API docs, attachment param if supported
  attachments = [{ url: pdfUrl, name: `Reglas-${slug}.pdf` }];
}
```

Feature flag `PDF_ATTACHMENT_ENABLED` default OFF until verified working.

If Beds24 doesn't support attachments → skip Phase F. Link in text is sufficient.

### Phase G · Tests (30 min)

`apps/worker-bot/tests/pre-stay-rules-mention.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { renderTemplate } from '../src/pre-stay-templates';

describe('Pre-stay templates with rules mention', () => {
  it('welcome includes rules link with bookingId', () => {
    const out = renderTemplate({
      property_slug: 'rincon-del-mar',
      touchpoint: 'welcome',
      lang: 'es',
      guest_first_name: 'Alex',
      arrival: '2026-12-20',
      departure: '2026-12-25',
      num_adults: 4,
      num_children: 0,
      channel: 'airbnb',
      booking_id: 'HMK52J9XZM',
    });
    expect(out).toContain('reglas/rincon-del-mar');
    expect(out).toContain('bookingId=HMK52J9XZM');
    expect(out).toContain('Reglas de la casa'.toLowerCase()).toBeTruthy();
  });

  it('t7 includes checklist + rules link', () => {
    const out = renderTemplate({
      // ... same but touchpoint: 't7'
    });
    expect(out).toContain('reglas/rincon-del-mar');
    expect(out).toContain('Capacidad'); // checklist item
  });

  it('EN versions use lang=en query', () => {
    const out = renderTemplate({
      // ... same but lang: 'en'
    });
    expect(out).toContain('lang=en');
    expect(out).toContain('house rules'.toLowerCase());
  });

  // ... × 4 properties × 2 langs × 2 touchpoints = 16 cases minimum
});
```

`apps/web/tests/reglas-page.test.ts`:

```typescript
// Render public page for each slug
// Verify content includes property name + rules text
// Verify lang switcher works
// Verify click is tracked when bookingId param present
```

---

## 6 · Definition of done

- [ ] Public page `/reglas/[slug]` live for 4 properties × 2 langs
- [ ] D1 migration `rules_link_clicks` applied to prod
- [ ] PDF version generated per property/lang in R2 (or on-demand)
- [ ] 8 welcome templates updated with rules paragraph + trackable link
- [ ] 8 t7 templates updated with stronger reminder + checklist
- [ ] `TemplateInput.booking_id` added
- [ ] 16+ tests passing
- [ ] Beds24 attachment feature: implemented if API supports, skipped if not
- [ ] PR opened with all changes
- [ ] thread/142 posted with:
  - Phase A-G results
  - Sample rendered template per property × lang
  - Public page screenshot
  - PDF sample download link
  - Any out-of-scope findings (don't fix inline)

---

## 7 · Risks + mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | thread/139 reglas not yet deployed | Check pre-flight; halt if not |
| R2 | Beds24 messages API doesn't support attachments | Skip Phase F; document in thread/142 |
| R3 | PDF generation slow / expensive | Pre-generate on deploy (Option 2) instead of on-demand |
| R4 | Public `/reglas/[slug]` accessible to crawlers — Google index | OK (transparent + good SEO). If concerns, add `noindex` meta |
| R5 | Rules content > what fits in one message | Use link, never embed full text. Tests verify message length |
| R6 | Welcome templates currently used in production — risk break | Tests + canary preview env first if available |
| R7 | bookingId might leak via URL share to non-guest | OK (rules are public anyway). Don't include guest PII in URL |
| R8 | Click tracking can identify guest | Anonymize after 30 days (cron deletes ip+user_agent after window) |
| R9 | EN translations don't sync if RdM rules update | Source of truth = R2, page reads live, always fresh |
| R10 | Karina edits rules mid-stay — guest sees changed text | Page shows `deployed_at` timestamp, guest can know when read |

---

## 8 · Communication milestones

| Trigger | Message |
|---|---|
| Pre-flight done | "thread/141 starting. ETA 3-5h." |
| Phase A done | "Public /reglas/[slug] page live in dev. 4 props × 2 langs render correctly." |
| Phase D + E done | "8 welcome + 8 t7 templates updated. Tests passing." |
| Phase F skipped | "Beds24 API does not support attachments → skipped Phase F. Link in text only." |
| PR ready | "PR #N ready for Alex review. Sample renders in PR description." |
| Halt | "thread/141 halted at Phase X. Reason: Y." |

---

## 9 · Smoke test post-merge

After Alex merges + deploys:

1. Public page:
   - `curl https://rincondelmar.club/reglas/rincon-del-mar` → 200, contains "REGLAS DE LA CASA"
   - `curl https://rincondelmar.club/reglas/rincon-del-mar?lang=en` → 200, contains "HOUSE RULES"
   - `curl https://rincondelmar.club/reglas/rincon-del-mar?bookingId=test123` → 200, click logged in D1

2. PDF (if Phase C Option 2):
   - `curl -I https://rincondelmar.club/reglas-pdf/rincon-del-mar-es.pdf` → 200, content-type PDF

3. Templates (use existing `/admin/pre-stay` preview):
   - Pick a real upcoming reservation
   - Click "Preview welcome" → see rules link in output
   - Click "Preview t7" → see rules link + checklist

4. End-to-end: Wait for next real booking → check Beds24 sent message includes link → click link from guest's perspective (incognito) → verify tracked in D1 `rules_link_clicks`

---

## 10 · Backlog explicit (post-Phase 1)

| Item | Effort |
|---|---|
| Phase 2 · Acknowledgment portal `/g/[token]/checkin` | 10-15h |
| Direct booking variant (find/replace 9 Airbnb mentions) | 2-3h |
| Phase 3 · Risk-tier routing (high-risk bookings get extra touchpoints) | 8-12h |
| PDF design upgrade (photos, branding) | 4-6h |
| Multi-channel pre-stay (Booking.com, direct via WhatsApp) | varies |

---

WC out. CC: ejecuta Phase 1 limpio, output thread/142.
