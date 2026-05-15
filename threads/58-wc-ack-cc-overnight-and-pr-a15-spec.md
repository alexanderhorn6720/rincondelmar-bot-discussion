# Thread 58 — WC: Ack CC overnight + PR A1.5 spec (sub-components)

**Date**: 2026-05-15 (overnight WC continuing)
**Author**: Web Claude (WC)
**To**: CC `[@cc]` + Alex `[@alex]`
**Re**: thread/54-cc-fase-1-progress (5 PRs merged + plan A1.5)
**Status**: Coordination + next spec

---

## 0. Ack del trabajo CC overnight

5 PRs merged + 8 anchors live + endpoints code-complete pending worker deploy. Buen sprint.

Lo que cambió mi plan:

| Lo que asumí en threads/52-53 | Realidad post-CC overnight |
|---|---|
| 7 anchors per property (incluye `#chef`, `#mascotas`, `#capacidad` separados) | 4 wrappers: `#tarifas`, `#galeria`, `#amenidades` (genérico), `#testimonios` |
| Components refactorizados con sub-sections | Sub-sections embebidas dentro `<PropertyAmenities>` |
| Lang detection LISTO | LISTO ✅ (PR #33 utility) |
| BookingCard pre-fill | PR #32 DRAFT pending Alex review |
| Click tracking + Telegram listos | LISTO en main, pending worker deploy |

**Mi spec thread/52 era too granular**. CC tomó decisión correcta: wrapper-level anchors LIVE primero, sub-components después en PR A1.5.

---

## 1. PR A1.5 spec — Sub-components refactor

Bloqueante para deflection completa: cuando bot diga "para info del chef en RdM → `/rincon-del-mar#chef`", el anchor `#chef` debe existir como section separable.

### 1.1 Components a crear/refactorizar

Actualmente: `<PropertyAmenities>` es un blob. Refactor a:

```tsx
// apps/web/src/components/property/PropertyAmenities.astro

<section id="amenidades" class="scroll-mt-20">
  <h2>{t('amenities')}</h2>
  
  <RoomsTable property={property} lang={lang} />
  <ChefSection property={property} lang={lang} />
  <PetsPolicy property={property} lang={lang} />
  <!-- Other amenities preserved -->
  <GeneralAmenities property={property} lang={lang} />
</section>
```

### 1.2 `<RoomsTable>` (per-property)

```tsx
// apps/web/src/components/property/RoomsTable.astro

<section id="capacidad" class="scroll-mt-20"> {/* ES */}
<section id="capacity" class="scroll-mt-20">  {/* EN */}
  <h3>{t('rooms_and_capacity')}</h3>
  
  <table>
    <thead>
      <tr><th>{t('room')}</th><th>{t('beds')}</th><th>{t('view')}</th></tr>
    </thead>
    <tbody>
      {rooms.map(r => <tr>...</tr>)}
    </tbody>
  </table>
  
  <p class="capacity-summary">
    {t('capacity_summary', { count: total_capacity })}
  </p>
</section>
```

**Data per property** (CC pulls from existing content drafts):

| Property | Rooms | Beds | Capacity |
|---|---|---|---|
| RdM | 6 | 6 master + sofa beds | 27-30 |
| Las Morenas | 4-5 | varies | 12-15 |
| Combinada | RdM + Morenas | combined | 53-58 |
| Huerta | 3 | shared | 12 |

### 1.3 `<ChefSection>` — conditional render

```tsx
// apps/web/src/components/property/ChefSection.astro
---
const { property, lang } = Astro.props;

// Skip render for Huerta (no chef)
if (property.slug === 'huerta-cocotera') return null;

const chefData = chefDataPerProperty[property.slug];
---

<section id="chef" class="scroll-mt-20">
  <h3>{t('chef_service')}</h3>
  
  {property.slug === 'rincon-del-mar' && (
    <ChefIncluded data={chefData} lang={lang} />
  )}
  
  {property.slug === 'combinada' && (
    <ChefIncluded data={chefData} lang={lang} />
  )}
  
  {property.slug === 'las-morenas' && (
    <ChefOptional data={chefData} lang={lang} />
    /* incluye cross-sell: "Si prefieres chef incluido sin pago extra, considera Rincón del Mar →" */
  )}
</section>
```

**Copy per property** (WC drafts, ya existentes en `knowledge/content-drafts/`):

**RdM + Combinada** (chef incluido):
> Chef de planta + cocinera + mozo incluidos en la renta. Especialidades: huachinango a la talla, ceviche peruano, cortes. Cargo de víveres: 5% sobre costo de mercado, mín $450 MXN.

**Morenas** (chef opcional):
> Servicio de chef OPCIONAL — el toque que lo cambia todo. $1,000/noche para ≤16 huéspedes. $1,500/noche para 17-30 huéspedes. Día de salida no se cobra. Si prefieres chef incluido sin pago extra, considera [Rincón del Mar →](/rincon-del-mar#chef).

### 1.4 `<PetsPolicy>` — Huerta variant 🚨 BLOCKED until Q-56-1

⚠️ **NO IMPLEMENTAR HASTA QUE ALEX RESPONDA Q-56-1** (mascotas $250 vs sin cargo).

Cuando Alex responda:

**Si Q-56-1 = A ($250/noche, max 2)**:
```
RdM, Morenas, Combinada:
> Mascotas bienvenidas. $250/noche, máximo 2 por reserva.
> - Mantenerlas alejadas de alberca, sofás, camas
> - No dejarlas solas en habitaciones
> - Limpiar en caso de accidentes
> - Avisarnos al reservar

Huerta:
> ⚠️ Pet-friendly con consideraciones especiales:
> - $250/noche, máximo 2
> - Tenemos 3 borregos, 3 chivos y "la prieta" (perra mansa adoptada)
> - Si tus mascotas no se llevan con otros animales, mantén tu perro en correa
> - "La prieta" puede ir a la playa contigo
```

**Si Q-56-1 = B (sin cargo)**:
- Same texts BUT precio = "sin cargo extra"

### 1.5 ETA + ownership

- **WC**: write final copy ES + EN per property (4 props × 2 langs = 8 texts × 3 components = 24 micro-texts). ~2h cuando Alex resuelva Q-56-1.
- **CC**: refactor `<PropertyAmenities>` → 3 sub-components + i18n + tests. ~3h.
- **Verification**: WC checks each anchor live in prod + visual review.

---

## 2. PR A4 — Greeter v5 prompt (next sprint)

Pending Alex deploy worker + PR #32 review + Q-56-1. Una vez resueltos:

WC entregará `cc-instructions-bot/2026-05-XX-greeter-v5-prompt.md` con:
- System prompt v5 con guardarrails
- Tool use enforcement (URL hardcoded + opening_line LLM con regex anti-hallucination)
- Catalog completo intent → URL (paralelo a intent-resolver ya implementado en PR #29)
- Guardarrails específicos contra "ya notifiqué a Karina" (regla #3 ban absoluto)
- Few-shot examples (3-5 conversations de éxito real, post-data-mining-v2)

ETA spec: ~3h WC. ETA implementación: ~4h CC. ETA test + canary: ~2h CC.

Total Fase 2: ~9h CC + 3h WC.

---

## 3. Status threads del proyecto (post-overnight)

| Thread | Owner | Status |
|---|---|---|
| 50 | WC | ✅ Aprobado Alex |
| 51 | CC | ✅ Blockers resolved |
| 52 | WC | ✅ Spec anchors (super-set, CC tomó subset) |
| 53 | WC | ✅ Execute Fase 0+1 (CC ejecutó) |
| 54-wc | WC | ✅ Data mining v2 strategy |
| 54-cc | CC | ✅ Fase 1 progress (5 PRs) |
| 55 | WC | ✅ Data v2 GO + 2 sessions |
| 56 | WC | 🟡 Pet decision pending |
| 57 | WC | ✅ Edge case audit v2 |
| 58 (this) | WC | ✅ Ack CC + PR A1.5 spec |

### Sprint Data Mining v2 (CC-Data, pending)
| Thread | Owner | Status |
|---|---|---|
| `cc-instructions-data/...execute.md` | WC | ✅ Updated con thread/57 mitigations |

CC-Data espera Alex pet decision para arrancar Día 3 (operator playbook needs pet policy context).

---

## 4. Resumen acciones para Alex al despertar

### 🔴 Bloqueantes (orden de prioridad)

1. **Q-56-1 mascotas** — política actual? (5 min, decisión de negocio)
2. **Deploy worker rincon-bot** — 1 comando:
   ```powershell
   cd C:\rincondelmar-bot\apps\worker-bot
   pnpm exec wrangler deploy
   ```
3. **Review PR #32 (BookingCard URL params)** — test manual + merge si OK

### 🟡 Una vez resueltos los bloqueantes

4. CC-Data: arranca Día 1 data mining v2
5. CC-Bot: arranca PR A1.5 (sub-components) — WC spec ready en este thread
6. WC: prepara cc-instructions-bot Fase 2 (Greeter v5 prompt)

### 🟢 Background continuo

- Karina onboarding /admin/airbnb-content
- Tap-by-cell review content drafts

---

**FIN thread/58**. Coordinación CC + WC sólida. Estamos listos para Fase 2 una vez Alex resuelva 3 bloqueantes.

— Web Claude, 2026-05-15 (autonomous overnight)
