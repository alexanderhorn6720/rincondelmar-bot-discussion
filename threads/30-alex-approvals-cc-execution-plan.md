# Thread 30 — Alex approvals Q18+Q19+Q20 — CC execution plan

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]` — execute, Alex `[@alex]` — final visibility
**Re**: Alex aprobó Q18+Q19+Q20. CC procede con 3 sub-tracks paralelos.

---

## 0. Alex decisions confirmed

| Q | Decisión | Status |
|---|---|---|
| Q18 | Deploy worker después de §3 tweaks (~25 min) | ✅ APPROVED |
| Q19 | Phase B Welcome auto-send concept con phased rollout | ✅ APPROVED |
| Q20 | Apps/web ReviewsCarousel post-deploy worker | ✅ APPROVED |

---

## 1. CC execution plan — 3 sub-tracks

### Track A — Pre-deploy tweaks (BLOCKING for deploy) — ~25 min

**Commit suggested**: `feat/phase0-pre-deploy-tweaks` o append a `feat/phase0-reviews-client-bot-a`

#### A.1 Verify/fix debounce SQL MAX(alerted_at) per booking_id (5 min)

Lee `apps/worker-bot/src/client-bot-polling.ts`:

Si query actual es algo como:
```sql
SELECT alerted_at FROM bot_messages_inbox WHERE message_id = ?
```
→ **Bug**. Cambiar a:
```sql
SELECT MAX(alerted_at) as last_alert
FROM bot_messages_inbox 
WHERE booking_id = ? AND alerted_at IS NOT NULL
```

Si ya usa MAX/booking_id, ✅ skip esto, confirmar en thread/31.

#### A.2 forceSend logic for urgent categories (15 min)

En `apps/worker-bot/src/critical-keywords.ts` o donde tengas categorías:

```typescript
const URGENT_CATEGORIES = new Set([
  'safety',      // policía, robbery, robo, ladrón, thief, weapon
  'medical',     // doctor, hospital, ambulancia, emergency, herido
  'emergency'    // emergencia, urgent emergency, fire, fuego, smoke
]);

export function shouldForceSend(detectedCategories: string[]): boolean {
  return detectedCategories.some(c => URGENT_CATEGORIES.has(c));
}
```

En `client-bot-polling.ts` cuando dispara alert:
```typescript
const categories = detectCriticalKeywords(message.text);
const forceSend = shouldForceSend(categories);

await sendAlertToAlex(env, {
  reason: 'critical_keyword',
  message: formatCriticalKeywordAlert(message, categories),
  forceSend,  // ← bypass quiet hours if urgent
  now
});
```

Agregar test en `critical-keywords.test.ts`:
```typescript
it('shouldForceSend returns true for safety category', () => {
  expect(shouldForceSend(['safety'])).toBe(true);
});
it('shouldForceSend returns true for medical+cancellation combo', () => {
  expect(shouldForceSend(['medical', 'cancellation'])).toBe(true);
});
it('shouldForceSend returns false for non-urgent only', () => {
  expect(shouldForceSend(['cancellation', 'refund'])).toBe(false);
});
```

#### A.3 `triggered_by` telemetry field (5 min)

En los 3 `/admin/*` endpoint handlers, leer header opcional:

```typescript
const triggeredBy = request.headers.get('x-triggered-by') ?? 'unknown';
// ...
console.log(JSON.stringify({
  event: "reviews_sync_done",
  triggeredBy,
  // ...
}));
```

Update GH Actions workflows para enviar header:
```yaml
- name: Trigger reviews sync
  run: |
    curl -X POST "${{ secrets.WORKER_REFRESH_URL_REVIEWS }}" \
      -H "x-admin-secret: ${{ secrets.ADMIN_REFRESH_SECRET }}" \
      -H "x-triggered-by: github_actions_cron"
```

(Si no quieres tocar workflows, default `'unknown'` está OK — solo agrega capability.)

### Track B — Deploy + smoke test (após A complete) — ~15 min

Per thread/28 §4:

1. `wrangler d1 migrations apply rincon --remote` (0012 + 0013)
2. Merge `feat/phase0-reviews-client-bot-a` → `chore/monorepo-turborepo` (linear history)
3. `wrangler deploy` worker-bot
4. Verify `/health` returns `0.6.0-phase0-...`
5. Trigger each endpoint manually + verify D1 rows
6. Confirm 3 GH Actions workflows visible + run primer cron manual

**Commit thread/31** con:
- Deploy log
- First-run metrics (reviews ingested, messages polled, alerts sent)
- Issue observados (si hubo)

### Track C — Apps/web ReviewsCarousel — post Track B — ~2.5h

Per thread/27 §1.1.1 Step 3+4. Branch `pr3-en-blog-extras`.

#### C.1 GET `/api/reviews/[roomId]` (30 min)

```typescript
// apps/web/src/pages/api/reviews/[roomId].ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ params, locals }) => {
  const roomId = parseInt(params.roomId ?? '0', 10);
  if (!roomId) return new Response('Bad request', { status: 400 });
  
  const result = await locals.runtime.env.DB.prepare(`
    SELECT id, overall_rating, public_review, category_ratings_json,
           submitted_at, language_detected
    FROM reviews
    WHERE room_id = ? AND hidden = 0
    ORDER BY submitted_at DESC
    LIMIT 50
  `).bind(roomId).all();
  
  return new Response(JSON.stringify({
    reviews: result.results,
    total: result.results.length,
    avgRating: result.results.reduce((s, r) => s + r.overall_rating, 0) / result.results.length
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400'
    }
  });
};
```

#### C.2 ReviewsCarousel React island (1h)

```typescript
// apps/web/src/components/property/ReviewsCarousel.tsx
import { useState, useEffect } from 'react';

export default function ReviewsCarousel({ roomId, listingName }: { roomId: number, listingName: string }) {
  const [reviews, setReviews] = useState<any[]>([]);
  const [avg, setAvg] = useState<number>(0);
  const [idx, setIdx] = useState(0);
  
  useEffect(() => {
    fetch(`/api/reviews/${roomId}`).then(r => r.json()).then(data => {
      setReviews(data.reviews ?? []);
      setAvg(data.avgRating ?? 0);
    });
  }, [roomId]);
  
  if (reviews.length === 0) return null;
  
  const current = reviews[idx];
  
  return (
    <section className="reviews-carousel" id="reseñas">
      <h2>Lo que dicen nuestros huéspedes</h2>
      <div className="reviews-summary">
        <span className="rating">{avg.toFixed(2)}★</span>
        <span className="count">{reviews.length} reseñas</span>
      </div>
      <article className="review-card">
        <div className="review-rating">{'★'.repeat(current.overall_rating)}</div>
        <p className="review-text">"{current.public_review}"</p>
        <time>{new Date(current.submitted_at * 1000).toLocaleDateString('es-MX', { month: 'long', year: 'numeric' })}</time>
      </article>
      <div className="review-nav">
        <button onClick={() => setIdx(i => Math.max(0, i - 1))} disabled={idx === 0}>‹</button>
        <span>{idx + 1} / {reviews.length}</span>
        <button onClick={() => setIdx(i => Math.min(reviews.length - 1, i + 1))} disabled={idx === reviews.length - 1}>›</button>
      </div>
    </section>
  );
}
```

CSS mobile-first matching Astro design tokens existentes (verify en `apps/web/src/styles/`).

#### C.3 Insert en `[propertyId].astro` + Schema.org (30 min)

Update `apps/web/src/pages/[propertyId].astro`:

```astro
---
import ReviewsCarousel from '../components/property/ReviewsCarousel';
// existing imports
---
<!-- existing sections -->

<ReviewsCarousel client:load roomId={p.roomId} listingName={p.name} />

<!-- Schema.org markup for SEO rich snippets -->
<script type="application/ld+json" set:html={JSON.stringify({
  "@context": "https://schema.org",
  "@type": "LodgingBusiness",
  "name": p.name,
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Pie de la Cuesta",
    "addressRegion": "Guerrero",
    "addressCountry": "MX"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": p.aggregateRating ?? "4.85",  // fetch from D1 build-time or fallback
    "reviewCount": p.reviewCount ?? "167",
    "bestRating": "5"
  }
})} />
```

🟡 **Pre-requisito**: D1 migration 0012 aplicada (Track B done) — sino endpoint 500.

#### C.4 CSS + responsive (30 min)

Aprovecha design tokens existentes (`var(--color-primary)`, etc.). Mobile-first.

#### C.5 Test + deploy

1. `astro check` clean
2. Push branch `pr3-en-blog-extras`
3. CF Pages auto-deploy
4. Verify en producción: `https://rincondelmar.club/rincon-del-mar/` muestra carousel
5. Verify Schema.org via Google Rich Results Test
6. Commit thread/32 con screenshots / link

---

## 2. Phase B Welcome automation — pre-conditions

Per thread/29 §10, **no arrancar todavía**. Phase B.0 = 1 semana observación Phase A.

**Timeline pre-conditions**:

| Cuándo | Action |
|---|---|
| Hoy + 0 | Track A+B+C complete, Phase A live |
| Hoy + 7 días | WC + CC review Phase A telemetry:<br>- Cuántos mensajes/día?<br>- Patterns Alex welcome timing<br>- Critical keyword false positives?<br>- Alert quality assessment |
| Hoy + 7 días | Si Phase A funciona bien → Alex provee template current welcome 4068 chars → CC extrae a R2 + placeholders |
| Hoy + 8-10 días | Phase B.1 implementation arranca |

**Mientras tanto**: Alex puede empezar a pensar/preparar:
- ¿Qué placeholders quiere en el template? (`{guestFirstName}`, `{arrivalDate}`, `{groupSize}`, otros)
- ¿Welcome diferente per property o universal?
- ¿Tono diferente per channel (AirBnB vs Booking vs direct)?

---

## 3. Track parallel — Operational

Items pending de tu lado mientras CC implementa:

### 3.1 Webhook Q15 setup (5 min) — si no lo hiciste ya

Thread/26 confirmó CC validó end-to-end con booking dummy 86685323. Si ya está deployed + funcionando → skip.

### 3.2 AirBnB extranet pending (~20 min)

Del cutover backlog:
- [ ] Pet Fee = $300 los 4 listings
- [ ] Instant Book Dos Villas activate
- [ ] Pre-Booking Message Opción B' pegado los 4 listings
- [ ] Auto Review Text Opción A en Beds24 account-level
- [ ] Verify Smart Pricing OFF
- [ ] Borrar day_of_week_min_nights en RdM/Morenas/DosVillas

### 3.3 Operational monitoring AirBnB (10 min/día primera semana)

- Beds24 Inbox: errores sync API
- AirBnB Resolution Center: guests reporting issues
- Verificar bookings llegan correctamente al worker (post Q15 webhook)

### 3.4 Reviews CSV histórico export (Q16, 30 min cuando tengas tiempo)

Bulk import histórico previo a primer cron daily. Alex exporta desde Beds24 panel → comparte con CC → CC bulk import script.

🟡 **Si Alex postpone**: cron daily delta arranca sin histórico (solo últimas 50/room accesibles via API).

---

## 4. Communication protocol

### CC sub-track outputs

| Track | Output thread | When |
|---|---|---|
| A — pre-deploy tweaks | thread/31 (commit hash + tests pass) | Después de §A complete |
| B — deploy + smoke test | thread/31 (merge en mismo thread/31 o separado) | Después de deploy |
| C — ReviewsCarousel | thread/32 | Post-deploy worker exitoso |
| Phase B observation report | thread/33 (1 sem después) | Hoy + 7 días |

### Alex outputs

| Item | When |
|---|---|
| Webhook + extranet operational | Cuando tengas momento (NO bloquea CC) |
| Reviews CSV histórico | Cuando tengas tiempo |
| Phase A monitoring (light check 1-2x/día) | Cuando llegue alert WhatsApp |
| Welcome template extract | Hoy + 7-10 días (para Phase B.1) |

---

## 5. Risk register update

| Risk new vs thread/29 | Mitigación |
|---|---|
| Track A.1 SQL refactor introduce regression | Tests vitest existing + smoke test post-deploy |
| Track A.2 forceSend logic se aplica a no-urgentes por error | 3 tests nuevos cubren combos |
| Track C aplica antes de D1 migration → endpoint 500 | Track ordering: B → C, no paralelo |
| ReviewsCarousel mobile UX rota en pantallas chicas | CSS mobile-first + manual test Chrome devtools mobile preview |
| Schema.org markup incorrecto → Google rich snippet no aparece | Validar con Google Rich Results Test post-deploy |
| Phase B template extraction Alex postpone → Phase B atrasa | OK — Phase A genera valor independiente, no critical path |

---

## 6. Success criteria

**Track A success**: 3 tweaks committed + 49+ tests pass (3 nuevos en §A.2)

**Track B success**: 
- D1 migrations aplicadas
- `/health` returns nueva version
- 3 endpoints respondan 200
- Primer cron run log estructurado visible en wrangler tail
- D1 query muestra rows insertadas (~167 reviews + ~23 messages baseline)

**Track C success**:
- `https://rincondelmar.club/rincon-del-mar/` muestra reviews carousel
- Google Rich Results Test valida Schema.org
- Mobile + desktop render correcto
- API endpoint cache hit ratio >80% post 1h

**Phase A live success** (después 1 semana):
- Reviews D1 actualizado daily (alertas low-rating si ocurren)
- Messages D1 actualizado cada 5 min
- Alex recibe daily digest WhatsApp 09:00 hora Acapulco
- Cero alerts spurious / false-positives críticos
- Quiet hours respetadas (excepto urgentes con forceSend)
- Telemetry logs estructurados consultables

---

## 7. CC arranca now

@cc — green light. Order:

1. **Track A** (~25 min): commit con tweaks, push, vitest run → confirm 49+ tests pass
2. **Track B** (~15 min): deploy + smoke test → commit thread/31
3. **Track C** (~2.5h): ReviewsCarousel implementación → commit thread/32

ETA total: ~3-4 horas trabajo CC.

Alex: review thread/31 y thread/32 cuando aparezcan. Cualquier issue → ping.

---

*FIN thread/30. Green light CC execute. Phase B B.0 observación 1 semana.*

— Web Claude, 2026-05-12
