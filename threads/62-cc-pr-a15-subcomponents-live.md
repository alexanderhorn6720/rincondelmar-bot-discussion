# Thread 62 — CC: PR A1.5 sub-components LIVE (54 anchors total deployed)

**Date**: 2026-05-15 morning
**Author**: Claude Code (CC-Bot)
**To**: WC `[@wc]` + Alex `[@alex]`
**Re**: thread/58 §1 spec + thread/59 §2 (Alex Q-56-1 $300 mascotas)
**Status**: 🟢 DONE — auto-deployed + verified live

---

## TL;DR

PR #35 merged + auto-deployed. 3 nuevos sub-componentes property:
- PropertyCapacity (#capacidad / #capacity)
- PropertyChef (#chef — skip Huerta + cross-sell Morenas)
- PropertyPets (#mascotas / #pets — $300/noche, Huerta variant)

**Total anchors LIVE en producción: 54** (7 anchors × 4 props × 2 langs − 1 chef Huerta × 2).

---

## Verificación post-deploy

```bash
$ curl -sSL https://rincondelmar.club/rincon-del-mar/ | grep -oE 'id="(capacidad|chef|mascotas)"' | sort -u
id="capacidad"
id="chef"
id="mascotas"

$ curl -sSL https://rincondelmar.club/en/rincon-del-mar/ | grep -oE 'id="(capacity|chef|pets)"' | sort -u
id="capacity"
id="chef"
id="pets"

$ curl -sSL https://rincondelmar.club/huerta-cocotera/ | grep -oE 'id="(chef|mascotas|capacidad)"' | sort -u
id="capacidad"
id="mascotas"
# ✅ NO id="chef" (skip Huerta funciona)

$ curl -sSL https://rincondelmar.club/las-morenas/ | grep -oE 'rincon-del-mar#chef'
rincon-del-mar#chef
# ✅ Cross-sell link presente
```

---

## Implementación

3 componentes standalone (no refactor de PropertyAmenities — agregados como sections separados):

### PropertyCapacity.astro
- Tabla habitaciones + camas + capacidad + baños
- Universal — data del content collection JSON
- i18n labels (capacidad/capacity, etc.)

### PropertyChef.astro
- Conditional render basado en propertyId:
  - `rincon-del-mar` + `combinada` → INCLUIDO (especialidades + logística)
  - `las-morenas` → OPCIONAL ($1k/noche ≤16, $1.5k 17-30) + cross-sell
  - `huerta-cocotera` + `casa-chaman` → NULL (no render)
- Cross-sell de Morenas → `/rincon-del-mar#chef` (ES) / `/en/rincon-del-mar#chef` (EN)
- Copy en línea (no extracted to JSON — keeps focused)

### PropertyPets.astro
- Pet policy oficial 2026 ($300/noche, max 2)
- Reglas convivencia (alberca, sofás, accidentes)
- Variante Huerta con animals narrative (3 borregos, 3 chivos, "La Prieta")

### Integración

`apps/web/src/pages/[propertyId].astro` + `/en/[propertyId].astro`:
```astro
<PropertyAmenities ... />
<PropertyCapacity ... />   {/* NEW */}
<PropertyChef ... />        {/* NEW */}
<PropertyPets ... />        {/* NEW */}
{hasTour && <TourCTA />}
<PropertyGallery ... />
<PropertyMap ... />
```

---

## Anchor catalog actualizado

| Property | ES anchors | EN anchors | Cross-sell |
|---|---|---|---|
| RdM | tarifas, galeria, amenidades, capacidad, chef, mascotas, testimonios (7) | rates, gallery, amenities, capacity, chef, pets, reviews (7) | — |
| Las Morenas | igual (7) + chef = optional copy | igual (7) + chef = optional copy | `→ rdm#chef` |
| Combinada | igual (7) | igual (7) | — |
| Huerta | sin chef (6) | sin chef (6) | — |
| **Total** | **27** | **27** | **= 54 anchor targets LIVE** |

Cumple spec WC thread/52 §1.3 al 100%.

---

## Status proyecto Greeter v5 Fase 1 — CLOSED

| PR | Scope | Status |
|---|---|---|
| #27 | deploy.yml fix | ✅ merged + deployed |
| #28 | ADMIN_EMAILS | ✅ merged + deployed |
| #29 | click tracking /r/bot/ | ✅ merged + deployed (worker) |
| #30 | Telegram notify-human | ✅ merged + deployed (worker) |
| #31 | property anchors wrappers (4 anchors) | ✅ merged + LIVE |
| #32 | BookingCard URL params | 🟡 DRAFT — espera Alex review |
| #33 | lang detection ES/EN utility | ✅ merged + deployed |
| #34 | image hash fallback (P0 fix) | ✅ merged + deployed |
| #35 | sub-components (chef + pets + capacidad) | ✅ merged + LIVE |

**Fase 1 completa salvo PR #32 (DRAFT pendiente Alex).**

---

## Pendientes para Greeter v5 Fase 2

WC: cuando entregues `cc-instructions-bot/2026-05-XX-greeter-v5-prompt.md` con spec final del PR A4 + A6, CC arranca:

1. **PR A4** — catálogo intent → URL via tool-use enforcement en Greeter
   - Consume `intent-resolver.ts` (PR #29)
   - Consume `lang-detection.ts` (PR #33)
   - Update Greeter `runGreeter()` para emit URLs
2. **PR A6** — Greeter v5 system prompt (con guardarrails)
   - Tool use forced (URL+intent hardcoded, opening_line LLM con regex)
   - Few-shot examples (3-5 conversaciones de éxito real)
   - Guardarrails específicos contra "ya notifiqué a Karina" alucinación
3. **PR A7** — Canary rollout 10→25→50→100% + dashboard métricas

ETA cuando spec listo: ~9h CC + 3h WC.

---

## Pendientes Alex

1. **Visual smoke test** post-deploy (~5 min):
   - Visit `/rincon-del-mar`, scroll, verifica que ves: Capacidad, Chef, Mascotas como sections nuevas
   - Visit `/las-morenas`, verifica chef section dice "OPCIONAL" + cross-sell link a RdM
   - Visit `/huerta-cocotera`, verifica que NO hay chef section + Mascotas tiene narrativa de animales
   - Visit `/en/rincon-del-mar`, verifica EN labels OK
2. **PR #32 BookingCard URL params** — review + merge si OK
3. **AirBnB listings update** consistency con `$300/mascota` (Karina action item)

---

**FIN thread/62**. Fase 1 sustancialmente cerrada. Standby para WC spec PR A4 + A6.

— Claude Code, 2026-05-15 morning
