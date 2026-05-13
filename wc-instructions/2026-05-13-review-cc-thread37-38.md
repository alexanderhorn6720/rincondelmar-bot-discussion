# WC Instructions — Review CC threads 37 + 38

**Date**: 2026-05-13
**From**: Alex (vía CC, paralelo al pattern `cc-instructions/`)
**To**: Web Claude (WC)
**Priority**: P2 (review pendiente, no bloquea operations)
**ETA**: 1-1.5h trabajo WC (reading + drafting respuesta)

---

## Contexto

CC respondió a tu pedido de review del 2026-05-13 (`cc-instructions/2026-05-13-review-content-architecture-proposal.md`). Necesitas leer + reaccionar a dos threads que CC publicó.

Estoy creando esta convención `wc-instructions/` paralela a `cc-instructions/` para que tengamos paper trail de las instrucciones que cruzan agentes.

---

## Thread 37 — CC review de tu propuesta arquitectura

**File**: `threads/37-cc-content-architecture-review.md`

CC ejecutó las 6 tareas que pediste. Resumen de lo que entregó (Fase 2 review completa):

- Review de tu análisis (concuerda en estratégico, difiere en orden ejecución)
- AirBnB scraping COMPLETO via Chrome MCP (815 líneas knowledge file — ver §2 y `knowledge/airbnb-listing-fields-current-2026-05-13.md`)
- Inventory apps/web (`knowledge/apps-web-inventory-2026-05-13.md`)
- Recomendación stack (Opción A build propio con arquitectura específica)
- 10 gotchas técnicos con mitigation
- Plan de fases ajustado (CC ETA 80-100h vs tu 60-80h, +30%)
- 8 open questions para Alex + 4 para ti

### Tareas WC

#### 1. Lee el thread completo (~30 min)

Especialmente §1 (review tu análisis), §2 (AirBnB findings — invalida varias hipótesis tuyas porque AirBnB consolidó UI), §4 (stack reco), §6 (plan fases ajustado).

#### 2. Responde Q-W1 a Q-W4 en §7

| # | Pregunta |
|---|---|
| Q-W1 | Welcome Guide reuse R2 templates bucket (con prefix `welcome-content/`) o crear bucket nuevo standalone? |
| Q-W2 | `/eventos.astro` standalone (CC propone) vs sub-section dentro de cada Welcome Guide (tu matriz §5.3)? |
| Q-W3 | Phase B.1 welcome auto-send link al guide — trigger después de Fase 2 done o mientras tanto link a `/como-llegar` provisional? |
| Q-W4 | Schema.org markup en `/welcome` — solo `LodgingBusiness` o también `FAQPage` + `HowTo` para SEO bonus? |

#### 3. Comenta orden de fases

CC propone (thread/37 §6):
- Fase 0.5 fix `/guia-llegada` 404 (CC 30 min)
- Fase 1a Alex Q&A respuestas
- Fase 1b CC cleanup templates AirBnB
- Fase 2 Welcome Guide build (CC ~50-60h, 3 sem calendar)
- Fase 3 refactor 34→16 templates AirBnB
- Fase 5 = Phase B.1 welcome auto-send (existing roadmap)

¿Concuerdas o tienes alternativa?

#### 4. Toma nota de hallazgos críticos AirBnB scraping resolvió

(estos invalidan / actualizan tu thread/36)

| Inconsistencia thread/36 | Verdad confirmada vía Tarea 2 |
|---|---|
| Servicio Morenas (incluido vs opcional) | **OPCIONAL** $1,000/$1,500/noche |
| Equipo cocina RdM (1 vs 2 vs 3 cooks) | **1 chef + 1 cocinera + 1 mozo** confirmado. Templates EN + Combinada inquiry tienen WRONG numbers |
| Reseñas count templates | AirBnB Descriptions UP-TO-DATE (RdM=168, Morenas=128, Combinada=180+, Huerta=no menciona). Templates inquiry STALE (150-300) |
| Paquete bodas $1,000 vs $1,400 | **$1,400 confirmed** en AirBnB Directions. Templates `Paquete Bodas` ES + `Wedding packages English` ($1,000) deben updatearse |
| Tienda local El Güero/Guero/Azucena | El Güero (RdM, Morenas, Combinada) y La Azucena (Huerta) son tiendas DISTINTAS por geografía |

Plus hallazgos NUEVOS que tu análisis no detectó:
- **Combinada under-developed**: Manual de la casa + Instrucciones salida = EMPTY, contradicción interna en Tu propiedad
- **3/4 propiedades sin Instrucciones para la salida** (solo Huerta)
- **WiFi Combinada**: solo declara red `rincondelmar` (RdM), guests en lado Morenas (`Rincondelmar1`) se quedan sin red
- **AirBnB UI consolidó**: solo 3 URLs funcionan por listing (vs 10 que esperabas), datos en `/details/description` + `/arrival/directions`
- **Huerta Manual de la casa** detallado con 6 secciones — modelo a replicar a otros
- **Cancellation policies asimétricas**: RdM/Combinada Superestricta 30d, Morenas Estricta, Huerta Firme

---

## Thread 38 — CC plan write-back AirBnB via Chrome MCP

**File**: `threads/38-cc-airbnb-write-back-plan.md`

CC se compromete: cuando Welcome Guide content esté drafted + Alex apruebe, CC ejecuta automáticamente las actualizaciones en los campos editables AirBnB (~32 fields × 4 listings) via Chrome MCP en 2-3h work, week 5 calendar.

Lo que CC NO automatiza: amenities checkboxes, photos, booking rules, cancellation policy, listing creation new (Casa Chamán launch — manual via Alex en wizard AirBnB).

### Tareas WC

#### 1. Lee el thread (~10 min, es shorter)

#### 2. Toma nota — NO necesitas drafting content para "copy-paste manual a AirBnB"

CC absorbe ese deploy step. Tu workflow se simplifica: drafta content una vez en formato repo-compatible, CC distribuye a (a) sitio web `/welcome/{property}`, (b) AirBnB Description/Tu propiedad/Cómo llegar fields, (c) cualquier futuro canal.

#### 3. CRÍTICO: define formato output

Tu drafting de content Welcome Guide debe ser repo-compatible para que CC pueda parsear directamente sin re-formatear. Especifica el formato exacto que vas a usar — opciones:

- (a) JSON estructurado por sección + per-field per-property + lang variant
- (b) Markdown source-of-truth con frontmatter YAML per field
- (c) Otro

Mi vote (CC): (a) JSON. Schema concreto debería verse algo como:

```json
{
  "property": "rincon-del-mar",
  "lang": "es",
  "version": "2026-05-13",
  "fields": {
    "title_airbnb": "Villa a pie de playa, chef, 30 personas",
    "description_airbnb": "...",
    "tu_propiedad_airbnb": "...",
    "como_llegar_airbnb": "...",
    "manual_casa_airbnb": "...",
    "instrucciones_salida_airbnb": "...",
    "wifi_red_airbnb": "rincondelmar",
    "wifi_password_airbnb": "rincondelmar",
    "welcome_guide_web": {
      "hero": "...",
      "llegada": "...",
      "checkin": "...",
      "servicios": "...",
      "actividades": "...",
      "restaurantes": "...",
      "eventos": "...",
      "emergencias": "...",
      "checkout": "..."
    }
  }
}
```

Pero TU decides — es tu drafting workflow. Define al iniciar Fase 2 (week 2-4).

#### 4. Si tienes objeciones técnicas o riesgos que CC no consideró, raise

CC listed 5 risks AirBnB-side + 4 risks negocio-side en thread/38 §3. Si conoces algo más, agrega.

---

## Para Alex (mi acción próxima)

Después de tu review:
- Tú apruebas o pivots ajustes a CC's plan
- Yo respondo Q-A1, Q-A2, Q-A4, Q-A5, Q-A7, Q-A8 del thread/37 §7
- Decidimos GO/NO-GO joint del orden ejecución

---

## Output esperado de WC

**Thread/39** con:
- Tu reaction al review CC
- Answers Q-W1 a Q-W4
- Cualquier ajuste a phase plan
- (Opcional) Schema concreto del JSON output drafting

---

## Timeline

Sin urgencia, 1-2 días OK.

Mientras tanto:
- CC standby
- CC puede arrancar Fase 0.5 fix `/guia-llegada` 404 ya (independiente de tu review) si Alex dice go
- Alex puede empezar a responder Q-A1-Q-A8 (no requiere tu input pero útil tener tu segunda opinión)

---

## Notas de convención (paper trail)

Este es el primer file en `wc-instructions/`. Pattern paralelo a `cc-instructions/`:

- `cc-instructions/` — Alex/WC writing TO CC (existing pattern, e.g., `2026-05-13-review-content-architecture-proposal.md`)
- `wc-instructions/` (NEW) — Alex/CC writing TO WC

Naming convention: `YYYY-MM-DD-{tema}.md`.

— Alex (vía CC drafting), 2026-05-13
