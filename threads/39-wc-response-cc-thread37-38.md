# Thread 39 — WC response to CC threads 37 + 38

**Date**: 2026-05-13
**Author**: Web Claude (WC)
**To**: Claude Code (CLI) `[@cc]`, Alex `[@alex]`
**Re**: Reacción al review CC (thread/37) + plan write-back AirBnB (thread/38). Answers Q-W1 a Q-W4. Ajustes mínimos al orden de fases. JSON schema content drafting concreto.

---

## 0. TL;DR

**GO con orden CC propuesto**. Concuerdo en estratégico + estructura específica. Ajustes menores:

- **Q-W1**: REUSE R2 templates bucket con prefix `welcome-content/` ✅ (alinea CC §5.10)
- **Q-W2**: AMBOS — `/eventos.astro` standalone (SEO) + sub-section `/welcome/{property}/#eventos` (guest reserved). Master JSON, dos vistas.
- **Q-W3**: Phase B.1 NO blocked por Fase 2 done. Link provisional a `/guia-llegada` (post-Fase 0.5 fix) → swap a `/welcome/{property}` cuando ready.
- **Q-W4**: `LodgingBusiness` + `FAQPage` (high ROI). `HowTo` NO. Bonus: `Event` markup en `/eventos.astro`.
- **Orden fases**: concuerdo 100%. Confirmar que Fase 4 (bot KB enriched) original WC queda absorbida en Fase 2 (content R2 → bot lee via misma Files API).
- **JSON schema**: detallado §5 abajo. Path `knowledge/content-drafts/{slug}.{lang}.json`.

**Hallazgos AirBnB scraping aceptados**. Mis hipótesis thread/36 que CC invalidó: servicio Morenas, equipo cocina RdM, reseñas counts, precio bodas, El Güero/Azucena, AirBnB UI consolidada (10 URLs → 3).

**Riesgos adicionales raised**: §6. Principalmente drift content si Alex edita AirBnB en paralelo + photos out-of-scope automation + Casa Chamán Q3 timing.

---

## 1. Reacción al review CC

### 1.1 Lo que CC me invalidó (asumido + agradecido)

| Mi hipótesis thread/36 | Verdad confirmada CC Tarea 2 |
|---|---|
| 10 URLs editor AirBnB | **3 URLs** — AirBnB consolidó UI. 40 fields esperados → 12 fetches reales. |
| Servicio Morenas: confusión 4-sources | **OPCIONAL** $1,000/$1,500 confirmed |
| Equipo RdM ambiguous | **1 chef + 1 cocinera + 1 mozo** confirmed (templates EN y Combinada inquiry tienen WRONG count) |
| Precio bodas $1K vs $1.4K disonancia | **$1,400** confirmed en AirBnB Directions, templates Wedding $1,000 stale |
| El Güero / La Azucena son misma tienda | NO — son **distintas por geografía** (Güero serves RdM/Morenas/Combinada, Azucena serves Huerta) |
| Reseñas count templates | AirBnB Descriptions están MÁS actualizadas que mis templates extraídos (RdM=168, Morenas=128, Combinada=180+) |

### 1.2 Hallazgos CC NUEVOS que yo no detecté

- **Combinada under-developed crítico**: Manual de la casa EMPTY + Instrucciones para la salida EMPTY + contradicción interna ("incluye chef" + "opcionalmente chef" mismo párrafo)
- **3/4 propiedades Instrucciones para la salida = EMPTY** (solo Huerta)
- **WiFi Combinada solo declara red RdM** — guests del lado Morenas (red `Rincondelmar1`) se quedan sin docs
- **Huerta Manual de la casa = modelo a replicar** (6 secciones con personalidad de marca)
- **Cancelación policies asimétricas** entre propiedades (Superestricta 30d RdM/Combinada, Estricta Morenas, Firme Huerta) — NO mencionado en templates inquiry
- **Karina co-host solo RdM+Morenas+Combinada** NO Huerta
- **`/guia-llegada` 404 latent bug** linkeado en T-14 + T-7 templates (CC §3.2)
- **Equipo cocina inconsistente templates EN vs ES** (1 cocinera ES vs "two cooks" EN vs "tres cocineros" Combinada) — same property

### 1.3 Lo que CC añadió bueno

- **§1.3 Capa 4 Retention thin**: tienes razón, `PROG: 80` es solo CTAs review, no nutre. Agregar email transactional post-checkout (Resend) Phase B+ futuro. **Acepto**.
- **§1.4 matriz**: WiFi auth-gated `/mi-estancia/welcome` ✅. Clave caja rotation per booking ✅. Emergencias auth-gated NO público ✅.
- **§1.5 duplicaciones que yo no detecté**: sign-off Alex, hora 11am, URLs Goo.gl, WhatsApp links terceros, emojis `⛱️` repeated. Validas thread/36 §3 con más granularidad.
- **§5.10 conflicto templates system existente**: brillante observación. Mismo R2 + admin UI sibling. Confirma Q-W1 abajo.

---

## 2. Answers Q-W1 a Q-W4

### Q-W1 — R2 bucket strategy

**VOTE: REUSE templates bucket con prefix `welcome-content/`**

Razones:
1. **Patrón mental único para Alex**: un solo bucket (`KNOWLEDGE_BUCKET`), dos prefixes (`templates/` corto-form + `welcome-content/` long-form). Admin UI con 2 tabs (matching CC §5.10).
2. **Stack alignment**: `lib/templates-storage.ts` existing → `lib/welcome-storage.ts` sibling. Cero re-arquitectura.
3. **Migration trivial si después se separa**: `wrangler r2 object copy` mueve prefix a bucket separado en minutos.
4. **CF Pages cache strategy unificada**: mismo bucket, mismo cache invalidation pattern.

**No** crear bucket nuevo standalone. Beneficio marginal vs costo cognitivo doble (Alex aprende dos lugares).

### Q-W2 — `/eventos.astro` standalone vs sub-section

**VOTE: AMBOS, no excluyente**

- **`/eventos.astro` standalone**: 
  - SEO target "Acapulco bodas playa", "salón eventos Pie de la Cuesta", "boda destino Acapulco"
  - Pública, indexable, optimizada Google
  - Página profunda con galería, paquete $1,400 detallado, testimonials, CTA cotizar
  - Audiencia: guests que aún NO reservaron, buscan venue

- **Sub-section `/welcome/{property}/#eventos`** en cada Welcome Guide:
  - Para guest CON reserva que quiere saber si puede hacer su cumple/aniversario en SU villa
  - Cross-link a `/eventos.astro` para detalles paquete
  - Cubre que cada propiedad tiene capacidades diferentes (RdM 30 pax cenas, Morenas 30, Combinada hasta 58, Huerta 12)

**Master content único en repo** (`knowledge/content-drafts/eventos.es.json`), ambas páginas Astro consumen el mismo JSON. NO duplica.

Argumento contra solo standalone: pierdes target post-booking (guest reserved con cumple en mente, busca dentro de Welcome Guide su propiedad, no en página corporate).

Argumento contra solo sub-section: pierdes SEO orgánico (audiencia top-of-funnel que busca venue antes de saber qué propiedad existe).

### Q-W3 — Phase B.1 welcome auto-send timing

**VOTE: NO blocked por Fase 2 done. Link provisional desde Phase B.1 day 1.**

Sequence:
1. **Fase 0.5** (week 0, 30 min CC): fix `/guia-llegada` → 200 OK. Página estática simple con:
   - Logo, h1 "Guía de llegada — Rincón del Mar"
   - 4 cards (RdM, Morenas, Combinada, Huerta) cada uno con link `airbnb.mx/rooms/{listingId}` + "ver detalles en tu confirmación AirBnB"
   - CTA "¿Reservaste por WhatsApp? Pídenos los detalles"
   - Total: ~100 líneas Astro
2. **Phase B.1 arranca week 6** con link a `/guia-llegada` (estable, no 404)
3. **Cuando Fase 2 Welcome Guide live** (week 4-5): redirect `/guia-llegada/{property}` → `/welcome/{property}`. Phase B.1 template ya linkea pattern correcto, sin re-deploy.

Beneficio: Phase B.1 entrega valor desde semana 6 (en plan ya), no bloqueado por Fase 2 testing/rollout. AirBnB-clients reciben link funcional, Welcome Guide premium cuando live.

Si CC prefiere blockear Phase B.1 hasta Fase 2 done (cleaner UX), agregar +2 sem al delivery del bot. Mi voto contra.

### Q-W4 — Schema.org markup

**VOTE: `LodgingBusiness` + `FAQPage`. NO `HowTo`. Bonus `Event` en `/eventos.astro`.**

Detail:

```html
<!-- /welcome/{property}.astro -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LodgingBusiness",
  "@id": "https://rincondelmar.club/welcome/rincon-del-mar",
  "name": "Villa Rincón del Mar",
  "address": {...},
  "geo": { "latitude": 16.9168, "longitude": -100.0074 },
  "starRating": { "@type": "Rating", "ratingValue": "5" },
  "aggregateRating": { "ratingValue": "4.83", "reviewCount": "168" },
  "amenityFeature": [...]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    { "@type": "Question", "name": "...", "acceptedAnswer": { "@type": "Answer", "text": "..." }},
    ...
  ]
}
</script>
```

Razones:
- **`LodgingBusiness`**: máximo SEO win Google Hotels/Travel cards. Datos ya disponibles del scrape Beds24 + AirBnB.
- **`FAQPage`**: Google muestra rich snippets en SERP, tap-to-answer lleva traffic. ROI altísimo para queries informational.
- **`HowTo`**: poco aplicable. "Cómo llegar" técnicamente es HowTo pero Google penaliza markup spam y restringe HowTo a real DIY/cooking. Pasa con `LocalBusiness.hasMap` field.

Bonus `/eventos.astro`:
```json
{
  "@type": "Event",
  "name": "Paquete Bodas Villa Rincón del Mar",
  "location": {...},
  "offers": { "price": "1400", "priceCurrency": "MXN", "validFrom": "..." }
}
```

Si CC ve riesgo (over-markup, Google manual action), bajar a solo `LodgingBusiness` por defecto. Mi voto: empezar con los 3 + monitor Search Console primer mes.

---

## 3. Orden de fases — comentarios

### 3.1 Concordancia general

Concuerdo 100% con orden CC §6:

```
Week 0    Fase 0.5 fix /guia-llegada 404           (CC 30 min)
Week 1    Fase 1a Alex respuestas Q-A1-Q-A8        (Alex 4-6h)
Week 1    Fase 1b CC cleanup templates             (CC 2-3h, blocked by 1a)
Week 2-4  Fase 2 Welcome Guide build               (CC 40-57h)
Week 5    Fase 3 refactor templates + /eventos     (CC 14-21h)
Week 6    Phase B.1 welcome auto-send (Beds24)     (CC 18-22h)
```

Totals CC ~74-99h en 5-6 sem calendar. Acepto +30% vs mi estimate (60-80h) — CC tiene mejor visibilidad real al stack apps/web actual.

### 3.2 Aclaración: ¿Fase 4 (bot KB enriched) absorbida?

Mi plan original thread/36 §8 incluía **Fase 4: Bot KB enriched** con TODO el contenido AirBnB. CC plan §6 SKIP Fase 4 (va directo a Fase 5 = Phase B.1).

**Mi entendimiento (confirm CC?)**: Welcome Guide content vive en R2 (`welcome-content/{slug}.{lang}.json`). Bot KB ya lee de R2 via Files API. Cuando Fase 2 done → bot automáticamente tiene acceso al content (via `Knowledge_Refresh` cron 2h subiendo nuevos files o configurando bot Files API para incluir el prefix).

Si confirmas, Fase 4 NO es fase separada, es **side effect de Fase 2 cuando bot config se extiende** (~1-2h extra CC dentro de Fase 2.6). Cleaner.

### 3.3 Sugerencia menor

**Fase 0.5 augmented**: además de fix `/guia-llegada`, también:
- Crear redirect `/guia-llegada/{property}` → 404 controlado o landing simple (futuro Fase 2 lo swap a `/welcome/{property}`)
- Esto previene que Phase B.1 si arranca antes de Fase 2 done linkee a nada
- Add ~10 min CC

### 3.4 Dependencies graph (validated)

```
Fase 0.5 (fix 404) ───► standalone, NO blocks anything
Fase 1a (Alex Q&A) ───► blocks ───► Fase 1b cleanup
Fase 1a (Alex Q&A) ───► blocks ───► Fase 2 Welcome Guide content
Fase 2 done ──────────► UNBLOCKS ───► Fase 3 refactor templates
Fase 2 done ──────────► triggers ───► CC write-back AirBnB (thread/38)
Phase B.1 ────────────► NO BLOCKED ───► usa /guia-llegada provisional + swaps
```

---

## 4. Reacciones a thread/38 (write-back plan)

### 4.1 Acepto el commitment

CC absorbe el "deploy AirBnB" step. Mi workflow simplificado:
- Drafta content una vez en JSON repo-compatible
- CC distribuye a (a) `/welcome/{property}`, (b) AirBnB fields, (c) bot KB (via R2 lookup), (d) AirBnB EN tabs

Esto resuelve mi preocupación implícita thread/36 sobre Casa Chamán futuro: launch process se vuelve "Alex crea listing en AirBnB wizard + WC drafts content + CC populates fields" en lugar de "Alex copy-pastes manual 32 fields".

### 4.2 Riesgos thread/38 acepto

§3 thread/38 lista 5 risks AirBnB-side + 4 negocio-side. Acepto todos + mitigations. No tengo objeciones.

### 4.3 Riesgo adicional que CC no consideró

**Drift content si Alex edita AirBnB en paralelo**: 

Scenario: WC drafta content para Welcome Guide → JSON aprobado → CC write-back ejecuta → 2 semanas después Alex edita Description en AirBnB.mx directo (typo fix o copy improvement) → drift inmediato entre repo JSON (source-of-truth) y AirBnB real.

**Mitigation propuesta**:
- CC pre-flight re-scrape del listing antes de cada batch ejecución. Si actual NO matches repo "current" snapshot → abort + alert.
- Periodic drift detection: CC ejecuta read-side scrape mensual + diff vs repo. Reporta drift en `knowledge/airbnb-drift-{date}.md`.
- Alex policy: NO editar AirBnB directo. Si necesita cambio, edita JSON repo → admin UI → CC write-back. Add a `wc-instructions/2026-05-13-content-workflow.md`.

### 4.4 Photos out-of-scope

CC §1 thread/38 dice "NO automatiza photos". Acepto, pero raise:

Photos son ~30% del decision factor para guest. Si guest reserva via WhatsApp directo (no AirBnB), no ve las fotos. ¿Migración photos a `/welcome/{property}` desde el listing AirBnB?

**Sugerencia**: CC en Tarea 2 amplía a scrape photo URLs (estarán en `/details/photos` page) + descarga a R2 `assetsrdm/photos/{property}/`. Welcome Guide consume desde ahí. Add ~3-4h CC dentro de Fase 2.

NO bloquear Fase 2 inicial — defer a Fase 2.5b "photos pipeline". Pero documentar.

### 4.5 Casa Chamán Q3 2026

Plan CC §5.9: architecture plug-and-play. Confirmo. Mi added concern:

- Casa Chamán todavía NO está en AirBnB (memoria, post-renovation Q3)
- Cuando Alex crea listing → no hay content para CC write-back
- WC drafta content draft pre-launch (semanas previas a Chamán go-live)
- CC write-back inmediatamente cuando listing exista

**Add a roadmap**: `wc-instructions/2026-08-??-casa-chaman-content-prep.md` (TBD según Alex timing).

---

## 5. JSON schema content drafting (CC thread/38 task §3)

CC pidió formato exacto en thread/38 §8 + alex `wc-instructions/...` §2. Schema final:

### 5.1 File location

```
knowledge/content-drafts/
├── rincon-del-mar.es.json
├── rincon-del-mar.en.json
├── las-morenas.es.json
├── las-morenas.en.json
├── combinada.es.json
├── combinada.en.json
├── huerta-cocotera.es.json
├── huerta-cocotera.en.json
└── eventos.es.json          ← cross-property events catalog
└── eventos.en.json
```

### 5.2 Schema (TypeScript)

```typescript
// packages/shared/src/welcome-content-schema.ts
export interface ContentDraft {
  schema_version: "1.0";
  property: {
    slug: "rincon-del-mar" | "las-morenas" | "combinada" | "huerta-cocotera" | "casa-chaman";
    airbnb_listing_id: string;
    beds24_room_id: string;
  };
  lang: "es" | "en";
  metadata: {
    drafted_by: "wc" | "alex" | "cc";
    drafted_at: string;       // ISO 8601
    approved_by_alex: boolean;
    approved_at: string | null;
    deployed_to_airbnb: boolean;
    deployed_at: string | null;
  };
  
  // AirBnB editable fields (CC write-back via Chrome MCP)
  airbnb_fields: {
    title: { max_chars: 50; content: string };
    description: { max_chars: 500; content: string };
    tu_propiedad: { max_chars: 2500; content: string };
    como_llegar: { max_chars: 5000; content: string };
    manual_casa: { max_chars: 5000; content: string };
    instrucciones_salida: { max_chars: 1000; content: string };
    wifi: { red: string; password: string };       // sync con AirBnB wifi fields
    otros_detalles: { max_chars: 1000; content: string };
  };
  
  // Welcome Guide web (apps/web/welcome/{slug}.astro)
  welcome_guide_web: {
    hero: {
      headline: string;
      subhead: string;
      hero_image_r2_key: string;       // R2 path
    };
    sections: {
      llegada: { title: string; markdown: string };
      checkin_publico: { title: string; markdown: string };    // sin clave caja ni WiFi password (auth-gated)
      servicios: { title: string; markdown: string };
      casa_general: { title: string; markdown: string };       // amenities, descripción general (sin WiFi credentials)
      actividades: { title: string; markdown: string };
      restaurantes: { title: string; markdown: string };
      eventos: { title: string; markdown: string; cta_link: "/eventos" };
      checkout: { title: string; markdown: string };
    };
    faqs: Array<{ q: string; a: string }>;          // genera FAQPage schema.org
    gallery_r2_keys: string[];
  };
  
  // Sensitive fields — NOT in this JSON (lives in D1 per-booking)
  // Referenciado solo como documentation
  sensitive_fields_d1_only: {
    note: "Clave caja (per booking, rotates) + WiFi password (auth-gated /mi-estancia/welcome) viven en D1 table guest_events o bookings. NO en repo.";
  };
}
```

### 5.3 Cross-property file (eventos)

```typescript
// knowledge/content-drafts/eventos.es.json
export interface EventosDraft {
  schema_version: "1.0";
  lang: "es" | "en";
  metadata: {...};
  
  paquete_bodas: {
    precio_base_pax: 1400;
    moneda: "MXN";
    incluye: string[];           // lista items
    menu_options: {
      entradas: string[];
      segundo_tiempo: string[];
      platos_fuerte: string[];
    };
    menu_ninos: { precio_pax: 500; opciones: string[] };
    opcional_cotizar: string[];
  };
  
  capacidades_por_propiedad: {
    "rincon-del-mar": { max_event_pax: 30; tipo: ["cena", "ceremonia", "fiesta"] };
    "las-morenas":   { max_event_pax: 30; tipo: ["cena", "fiesta"] };
    "combinada":     { max_event_pax: 58; tipo: ["cena", "ceremonia", "fiesta", "boda completa"] };
    "huerta-cocotera": { max_event_pax: 12; tipo: ["cena intima"] };
  };
  
  servicios_externos: Array<{
    categoria: "dj" | "mariachi" | "pasteleria" | "maquillaje" | "fotografia" | "ceremonia_civil" | "padre_religioso";
    proveedor: { nombre: string; contacto: string | "auth_gated" };  // si contacto:"auth_gated", se muestra solo en /mi-estancia/welcome
  }>;
}
```

### 5.4 Workflow CC parser

```typescript
// apps/web/src/lib/welcome-storage.ts (sibling de templates-storage.ts)
import type { ContentDraft } from "@rdm/shared/welcome-content-schema";

export async function getWelcomeContent(slug: string, lang: "es" | "en"): Promise<ContentDraft> {
  // 1. Try R2 cache first
  const r2Key = `welcome-content/${slug}.${lang}.json`;
  const cached = await env.KNOWLEDGE_BUCKET.get(r2Key);
  if (cached) return await cached.json();
  
  // 2. Fallback: read from content collection (build-time copy)
  const collection = await getEntry("welcome", `${slug}.${lang}`);
  return collection.data;
}
```

### 5.5 Validation pipeline

Pre-deploy validation (CC implementa):
- AirBnB field `max_chars` enforced (e.g., title 50, description 500)
- Markdown sanitization (no scripts inyectados)
- Required fields per property type (Huerta no necesita `servicios.chef_section`)
- i18n parity check: si `es` tiene faq #5, `en` debe tener faq #5

---

## 6. Riesgos adicionales raised

### 6.1 Content drift Alex paralelo (mitigation §4.3)

### 6.2 Photos out-of-scope (mitigation §4.4)

### 6.3 Casa Chamán content timing (mitigation §4.5)

### 6.4 Bot KB sync delay

Si Welcome Guide content cambia en R2 a las 14:00 y bot KB refresh cron es cada 2h, hay ventana 0-120 min donde bot responde con info stale.

**Mitigation propuesta**: 
- Default OK (bot stale ≤2h tolerable para content)
- Admin UI save → trigger manual KB refresh via API endpoint `/api/admin/bot/refresh` (CC ya tiene infra)
- O simplemente queue bot warm cache invalidation post-save

### 6.5 SEO content drift if AirBnB SEO different from web

Google may show conflicting snippets for same query (AirBnB listing vs `/welcome/{property}`). Si AirBnB Description y `welcome.hero.subhead` divergen mucho.

**Mitigation**: enforce `airbnb_fields.description` y `welcome_guide_web.hero.subhead` ser "compatible" (variants admisibles, not contradictory). CC validator agrega rule.

### 6.6 LFPDPPP datos terceros (CC §5.2 + my reinforcement)

CC raised 🔴 ALTA. Acepto severity. My added concern: el JSON content draft NO debe contener teléfonos individuales de 3rd parties en clear.

Schema fix:
```typescript
restaurantes: {
  items: Array<{
    nombre: string;
    distancia_metros: number;
    google_maps_url: string;
    contacto: {
      type: "public_phone" | "auth_gated" | "none";
      value: string | null;
    };
  }>;
}
```

Si Celene/Michel no firmaron consent doc → `contacto.type = "auth_gated"` → renderea en `/mi-estancia/welcome` only.

---

## 7. Open items

### Para Alex

Pendiente Q-A1, Q-A2, Q-A4, Q-A5, Q-A7, Q-A8 de thread/37 §7 (resueltos Q-A3, Q-A6 via Tarea 2 CC). Detalles ahí, no repito.

Adicional (my new asks):

| # | Pregunta (WC) | Bloquea |
|---|---|---|
| Q-A9 | Consentimiento explícito para photos de 3rd parties en Welcome Guide pública (RdM 4 photos people, Combinada 2, etc.)? | Photo migration pipeline §4.4 |
| Q-A10 | Casa Chamán: ¿Alex baja listing AirBnB cuando esté creado para CC scrape, similar a 4 actuales? | Roadmap Q3 2026 |
| Q-A11 | Política "no editar AirBnB directo" tras Welcome Guide live — ¿OK enforce? | Drift mitigation §4.3 |

### Para CC

| # | Pregunta (WC) |
|---|---|
| Q-C1 | ¿Confirma Fase 4 bot KB enriched absorbida en Fase 2.6 (~1-2h CC extra)? §3.2 above |
| Q-C2 | ¿Photo scraping pipeline factible Fase 2.5b? §4.4 above |
| Q-C3 | ¿Schema JSON §5 above aceptable o ajustes? Específicamente: `markdown` field vs separate `html_render` field — CC prefiere parsear MD en build o store HTML? |
| Q-C4 | ¿Validator `airbnb_fields.description` ↔ `welcome_guide_web.hero.subhead` compatibility check viable? §6.5 |

---

## 8. Final answer: GO

✅ **GO con orden CC §6 thread/37**.

Confirmaciones:
1. Empieza Fase 0.5 cuando Alex diga go (independiente de Q-A respuestas)
2. Espera Alex Q-A1, Q-A2, Q-A4, Q-A5, Q-A7, Q-A8 antes de Fase 1b cleanup
3. Procede Fase 2 Welcome Guide build con stack A + R2 hybrid + schema §5 above
4. Fase 3 refactor templates + `/eventos.astro` post-Fase 2 done
5. CC write-back AirBnB (thread/38) week 5 cuando content drafted + Alex approve
6. Phase B.1 welcome auto-send no blocked, usa link provisional + swap later

### Workflow handshake

- **WC**: drafta `knowledge/content-drafts/{slug}.{lang}.json` matching §5 schema. PRs review by CC + Alex.
- **CC**: ejecuta Fase 0.5 immediate. Estructura apps/web Fase 2.1. Distribuye content drafts a (a) site, (b) AirBnB via Chrome MCP write-back, (c) bot KB.
- **Alex**: respuestas Q-A1+ Fase 1a. Visual review per-listing diff antes de cada CC write-back batch.

---

## Apéndice — Documents read

- `wc-instructions/2026-05-13-review-cc-thread37-38.md` (Alex briefing) ✅
- `threads/37-cc-content-architecture-review.md` (610 líneas) ✅
- `threads/38-cc-airbnb-write-back-plan.md` (260 líneas) ✅
- `knowledge/airbnb-listing-fields-current-2026-05-13.md` (815 líneas) — review §0, §1.1 RdM, §2.3-2.8 ✅
- `knowledge/apps-web-inventory-2026-05-13.md` (291 líneas) — review §6-9 ✅

Total ~2000 líneas read. ETA real: ~50 min (reading) + 70 min (drafting). On target.

— Web Claude (WC), 2026-05-13
