---
thread: 218
author: CC-Bot
date: 2026-05-27
topic: doit-217-pr2-pr3-megarun-report
mode: report
status: done
---

# thread/218 — CC-Bot DoIt report: thread/217 §PR2 + §PR3

## Resumen

DoIt thread/217 §PR2 + PR3 completado. Dos PRs abiertos. Greeter v7.1 DOD ya estaba
verificado en PR1 (PR #191, mergeado antes de esta sesión). Esta sesión cubrió:

- **Pre-work** (sesión anterior): fix `run-eval-local.ts` + 5 ciclos eval hasta 98.5% global
- **PR2**: Página `/comparar-casas` — PR #192
- **PR3**: Página `/disponibilidad` — PR #193

---

## PR2 — feat/comparar-casas-page — PR #192

**Branch:** `feat/comparar-casas-page`

### Archivos

| Archivo | Tipo | Descripción |
|---|---|---|
| `apps/web/src/components/ComparisonTable.tsx` | NEW | React island: 4 villas × 20 criterios, toggle "solo diferencias", valores coloreados |
| `apps/web/src/components/ComparisonTable.css` | NEW | Sticky header, scroll mobile, section/row styles |
| `apps/web/src/pages/comparar-casas.astro` | NEW | SSG con breadcrumbs, JSON-LD, WhatsAppCTA |
| `packages/agents/greeter/intent-catalog.ts` | MOD | comparar-casas URL: `/#casas` → `/comparar-casas` (ES + EN) |
| `apps/web/src/components/layout/Footer.astro` | MOD | "Comparar casas" / "Compare homes" en sección Info |
| `apps/web/src/pages/[propertyId].astro` | MOD | Sección "Compara las 4 casas" antes del WhatsApp final |

### DOD PR2

- [x] Página `/comparar-casas` creada con prerender=true
- [x] 4 villas × 20 criterios en 4 secciones (Capacidad, Espacios, Servicios, Reglas)
- [x] Toggle "solo diferencias" (oculta filas con valores idénticos)
- [x] Sticky header con `top: var(--header-height, 72px)`
- [x] Scroll horizontal mobile
- [x] CTA "Ver disponibilidad de las 4 →" → `/disponibilidad`
- [x] Footer links actualizados
- [x] Villa pages cross-link agregado
- [x] intent-catalog actualizado

---

## PR3 — feat/disponibilidad-page — PR #193

**Branch:** `feat/disponibilidad-page`

### Archivos

| Archivo | Tipo | Descripción |
|---|---|---|
| `apps/web/src/components/AvailabilityPage.tsx` | NEW | React island principal: tabs villa, 4 fetches paralelos, precio card, CTA WhatsApp |
| `apps/web/src/components/AvailabilityCalendar.tsx` | NEW | MonthCalendar: grilla 7×N, días bloqueados, range selection Airbnb-style |
| `apps/web/src/components/AvailabilityTable.tsx` | NEW | Tabla rangos disponibles: filtros villa/mes/noches, sort, "Elegir" → calendar |
| `apps/web/src/components/AvailabilityPage.css` | NEW | |
| `apps/web/src/components/AvailabilityCalendar.css` | NEW | |
| `apps/web/src/components/AvailabilityTable.css` | NEW | |
| `apps/web/src/pages/disponibilidad.astro` | NEW | SSG con breadcrumbs, JSON-LD, WhatsAppCTA |
| `packages/agents/greeter/intent-catalog.ts` | MOD | Fallback disponibilidad/cotizar/precios → `/disponibilidad` (ES + EN); comparar-casas → `/comparar-casas` |
| `apps/web/src/components/layout/Footer.astro` | MOD | Comparar casas + Disponibilidad en sección Info |
| `apps/web/src/pages/[propertyId].astro` | MOD | "Ver disponibilidad" CTA antes del WhatsApp final |
| `apps/worker-bot/tests/intent-resolver.test.ts` | MOD | 6 tests actualizados para nuevos fallback URLs |
| `apps/worker-bot/tests/__snapshots__/intent-catalog-sync.test.ts.snap` | MOD | Snapshot actualizado |

### Data source investigación

No existe cache D1 de Beds24. La disponibilidad se sirve desde **R2** via el endpoint
`/api/availability?roomId=` ya existente (Make scenario `Knowledge_Refresh_v2`, cada 12h).
Dev fallback a `availability.sample.json`. No se necesitó infra nueva.

### DOD PR3

- [x] Página `/disponibilidad` creada con prerender=true
- [x] Calendario funciona (datos en tiempo real desde API existente)
- [x] Tabla con filtros (villa, mes, noches mínimas, sort)
- [x] Selección rango Airbnb-style
- [x] Intent catalog actualizado (disponibilidad/cotizar/precios fallback)
- [x] Cross-links en footer + villa pages
- [x] Tests 1164 passing (intent-resolver + intent-catalog-sync)

---

## Orden de merge recomendado

1. **PR2 (#192) primero**: `feat/comparar-casas-page`
2. **PR3 (#193) después**: `feat/disponibilidad-page`

PR3 ya incluye los cambios de comparar-casas en `intent-catalog.ts` para no depender
del orden. Si se mergea en orden inverso, habrá un conflicto menor en `[propertyId].astro`
(fácil de resolver).

---

## Notas técnicas

- PR3 no modifica `[propertyId].astro` con la sección "Comparar" de PR2 (eso está en PR2).
  PR3 agrega solo la sección "Ver disponibilidad". Cuando se mergeen ambos, el archivo
  tendrá ambas secciones.
- `AvailabilityPage.tsx` no usa `react-day-picker` ni deps externas — calendar 100% custom
  para evitar bundle overhead.
- Los rangos disponibles se calculan client-side a partir de `blocked_dates` (horizon 180d).
- Precios mostrados son promedio de `daily_prices` sobre el rango — nota "estimado".

---

## Decisiones pendientes para Alex

Ninguna. Todo dentro de scope del spec.

## Próximo paso

- Alex merge PR2 + PR3
- CF Pages auto-deploy en push a main
- Smoke test: `curl -I https://rincondelmar.club/comparar-casas` y `/disponibilidad` → 200
- Verificar eval no regresión post-deploy (opcional, pero spec lo pide en PR3 DOD)
