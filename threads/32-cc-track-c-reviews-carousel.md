# Thread 32 — CC Track C ReviewsCarousel implementation

**Date**: 2026-05-12
**Author**: Claude Code (CLI)
**To**: Alex `[@alex]` — review + merge, Web Claude `[@wc]` — visibility
**Re**: Track C completo per thread/30 §C. Branch `pr3-track-c-reviews-carousel` pushed (commit `d2f7a5d`). PR pendiente.

---

## 0. TL;DR

✅ **`/api/reviews/[roomId]` endpoint** — Astro APIRoute server-rendered en CF Pages Functions. Query D1 reviews tabla, validation roomId activos, cache headers agresivos.

✅ **`<ReviewsCarousel client:visible>` React island** — i18n es/en, keyboard nav, skeleton loading, fallback al estilo PropertyReviews.astro previo cuando D1 vacío/error.

✅ **Integration en `[propertyId].astro` + `en/[propertyId].astro`** — replace `<PropertyReviews>` con `<ReviewsCarousel>`. Solo renderea si `p.room_id` (skip casa-chaman placeholder).

✅ **11/11 vitest tests pass** — validation, normalización, malformed JSON, cache headers, 500 error.

✅ **Build clean** — 141 files, astro check sin nuevos errores. (3 errores pre-existentes en proxReservas + tour-virtual NO tocados.)

🟡 **NO deployed yet** — Alex debe abrir PR + merge para CF Pages auto-deploy. URL abajo.

🟡 **Schema.org aggregateRating** — sigue static (de `p.rating` content collection) porque page es prerendered. Display vivo via React island, pero SEO Schema usa build-time data. Update via content collection sync script queda para separate work (Q16).

---

## 1. Files added/modified (Track C scope)

| File | Type | LOC | Purpose |
|---|---|---|---|
| `apps/web/src/pages/api/reviews/[roomId].ts` | NEW | ~110 | APIRoute D1 query, validation, normalization |
| `apps/web/src/components/property/ReviewsCarousel.tsx` | NEW | ~210 | React island con loading/loaded/empty states |
| `apps/web/src/components/property/ReviewsCarousel.css` | NEW | ~145 | Mobile-first design tokens del sitio |
| `apps/web/src/pages/[propertyId].astro` | MOD | -3+11 | Replace `<PropertyReviews>` |
| `apps/web/src/pages/en/[propertyId].astro` | MOD | -3+11 | Replace `<PropertyReviews>` |
| `apps/web/tests/reviews-api.test.ts` | NEW | ~165 | 11 vitest tests |

Total: 6 files, +827 -4 LOC. Commit `d2f7a5d`.

---

## 2. API endpoint design

`GET /api/reviews/{roomId}`:

```typescript
// Validation
- roomId NOT integer → 400 invalid_roomId
- roomId NOT in {78695, 74322, 637063, 74316} → 404 unknown_roomId
- DB binding missing → 503 db_not_bound
- D1 throws → 500 db_error

// Query
SELECT id, overall_rating, public_review, category_ratings_json,
       submitted_at, language_detected, reviewer_id
FROM reviews
WHERE room_id = ? AND hidden = 0
  AND public_review IS NOT NULL AND overall_rating IS NOT NULL
ORDER BY submitted_at DESC LIMIT 50

// Response
{
  ok: true,
  roomId: 78695,
  total: 50,
  avgRating: 4.88,           // 2 decimals
  reviews: [{
    id: "...",
    rating: 5,
    text: "...",
    categories?: { cleanliness: 5, ... },
    submittedAt: 1750000000,
    language?: "es"
  }]
}

// Headers
Cache-Control: public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400
```

**Razones del cache 1h fresh + 24h SWR**:
- Reviews UPSERT por id en D1 — el payload es estable hasta nuevo cron daily
- 1h fresh = tolerable lag para reviews nuevas (cron 00:00 UTC daily anyway)
- SWR 24h = en caso de D1 outage, CDN sirve último good value mientras revalida

**Restricciones de validation activas**:
- Filter `public_review IS NOT NULL` — algunas reviews Beds24 vienen sin texto público (host-only feedback)
- Filter `hidden = 0` — host puede marcar review hidden vía Beds24 panel; respetamos
- Filter `overall_rating IS NOT NULL` — review no submitted aún

---

## 3. ReviewsCarousel React island design

**Props**:
```typescript
{
  roomId: number,                                      // required, valida en API
  propertyName: string,                                // a11y aria-label
  airbnbUrl?: string,                                  // fallback link
  lang?: 'es' | 'en' = 'es',                          // i18n labels + dates
  fallbackRating?: { average, count }                 // de p.rating, render fallback
}
```

**State machine**:
```
loading  → renders skeleton (3 lines, prefers-reduced-motion respected)
   ↓
loaded   → renders carousel (avg★ + count + card prev/next + see all link)
   ↓
empty/error → renders fallback (avg★ + count + airbnb btn) IF fallbackRating + airbnbUrl
                                                          ELSE returns null
```

**A11y features**:
- `role="group"` + `aria-roledescription="carrusel"`
- `tabIndex={0}` + arrow key nav (→/← entre reviews)
- `aria-live="polite"` en card + counter
- `aria-label` en buttons prev/next
- focus-visible ring 2px primary

**Performance**:
- `client:visible` — JS solo carga cuando section entra viewport
- 1 fetch en mount, no polling (cache HTTP del endpoint = 1h)
- `<img>` no usado (texto only) — cero layout shift

**i18n**:
- Labels hardcoded en componente (LABELS const) para es/en
- Date formatting via `Intl.DateTimeFormat` con locale es-MX / en-US
- `formatMonthYear` helper (e.g., "marzo de 2026" vs "March 2026")

---

## 4. Schema.org consideration

Page `[propertyId].astro` tiene `export const prerender = true` → static HTML build-time. JSON-LD ya incluye `aggregateRating` desde `lodgingBusinessLd(p, ...)` que lee `p.rating.average` + `p.rating.count` del content collection (`apps/web/src/content/properties/*.json`).

**Implicaciones**:
- ReviewsCarousel display refleja último cron daily (live D1 data) — bien
- Schema.org aggregateRating refleja build-time content collection — drift si Alex no actualiza propiedades JSON entre builds
- Google rich snippets seguirán mostrando aggregate antiguo hasta próximo CF Pages deploy

**Opciones para closing the gap** (NO en este PR):
- Build-time script: `pnpm sync-ratings` → query D1 (vía wrangler d1 execute) → update content collection JSONs → re-build
- Alternativamente: switch [propertyId].astro a SSR (`prerender = false`) y query D1 build-time + render-time. Menos performante, más fresh.
- Tercera opción (preferida si scope grew): un cron diario en GH Actions que actualice content collection JSONs en repo + commit + trigger CF Pages rebuild.

Defer hasta thread/33 o decisión Alex post-Track C live.

---

## 5. Test coverage

`apps/web/tests/reviews-api.test.ts` — 11 vitest tests, 12ms total:

1. ✅ 400 si roomId no es número entero (`abc`)
2. ✅ 400 si roomId vacío (`""`)
3. ✅ 400 si roomId 0 o negativo (`0`, `-5`)
4. ✅ 404 si roomId no es uno de los activos (`99999`)
5. ✅ 404 incluye `74322` en `known` (post-cutover Las Morenas)
6. ✅ 404 NO incluye `374482` (legacy archive)
7. ✅ 503 si D1 binding missing
8. ✅ 200 con array vacío cuando D1 sin reviews
9. ✅ 200 con reviews normalizadas + avg correcto (4.5 = (5+4)/2)
10. ✅ Omite reviews con malformed category JSON sin throw
11. ✅ 500 cuando D1 lanza error
12. ✅ Cache headers agresivos (1h + 24h SWR)
13. ✅ avgRating redondeado a 2 decimales (4.33 = 13/3)

(Counted as 11 it() blocks; some grouped multiple assertions.)

ReviewsCarousel.tsx NO tiene tests automatizados (React testing library no setup en este repo). Hand-tested via build + manual inspection del HTML generado. Si necesitamos, instalar `@testing-library/react` + happy-dom y agregar render tests. Defer.

---

## 6. Pre-existing errors NOT touched

`astro check` reporta 3 errores en archivos pre-existentes que Track C NO toca:

1. `src/pages/proxReservas.astro:235-236` — `'property' is possibly 'undefined'` (TS 18048)
2. `src/pages/tour-virtual/las-morenas.astro:42` — `PannellumConfig` type incompat

Estos existían antes del Track C commit. NO bloquean build (`astro build` exit 0). Out-of-scope para esta PR.

---

## 7. Pendiente

| # | Item | Owner | Bloqueante |
|---|---|---|---|
| 1 | Open PR `pr3-track-c-reviews-carousel` → `pr3-en-blog-extras` (default) | Alex | NO |
| 2 | CF Pages preview deploy (auto al PR) — verifica live URL | Alex | preview |
| 3 | Merge PR → CF Pages prod deploy automático | Alex | thread/31 §5 B1 también |
| 4 | Verify reviews aparecen en `/rincon-del-mar`, `/las-morenas`, `/huerta-cocotera`, `/combinada` | Alex | post-deploy |
| 5 | (Opcional) Sync Schema.org aggregate via content collection script | CC future | thread/33 |
| 6 | Q16: CSV import histórico (>50 reviews per room) | Alex (cuando tenga tiempo) | NO |

PR URL: https://github.com/alexanderhorn6720/rincondelmar-bot/pull/new/pr3-track-c-reviews-carousel

---

## 8. PR template suggested

**Title**: `feat(web): Track C — ReviewsCarousel + /api/reviews/[roomId] live D1`

**Body**:
```markdown
## Summary

- Replaces static PropertyReviews.astro with React island fetching live D1 reviews
- Adds /api/reviews/[roomId] APIRoute (CF Pages Function) with validation + cache
- Tested: 11/11 vitest (validation, normalization, cache headers, errors)
- Build: 141 files astro check + build clean (3 pre-existing errors NOT touched)

## Test plan

- [ ] CF Pages preview URL renders /rincon-del-mar with carousel visible
- [ ] Click prev/next nav cycles between reviews
- [ ] Keyboard arrow keys (focus on carousel) advance
- [ ] /api/reviews/78695 returns ~50 reviews JSON
- [ ] /api/reviews/99999 returns 404
- [ ] /las-morenas (en) renders English labels
- [ ] /casa-chaman (placeholder, no room_id) does NOT render carousel section

## Dependencies

Blocks on B1 merge (thread/31 §5) so Track B cron infra ships to default branch
along with this Track C UI. If merging Track C first, the worker has data already
(167 reviews D1) so UI works — just no cron updates until B1 lands.
```

---

**Status**: Code DONE + tests pass + build clean + branch pushed. Awaiting Alex PR creation + merge.
