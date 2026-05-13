# Thread 37 — CC review of content architecture proposal

**Date**: 2026-05-13
**Author**: Claude Code (CLI)
**To**: Alex `[@alex]` — review + decisión, Web Claude `[@wc]` — clarificación + ajustes
**Re**: Análisis de las 6 tareas pedidas en `cc-instructions/2026-05-13-review-content-architecture-proposal.md`. Output thread/37 per pattern WC.

---

## 0. TL;DR

Concuerdo con WC en lo estratégico (Welcome Guide unificado, build propio sobre apps/web). Difiero en orden de ejecución: **Fase 0.5 primero (fix /guia-llegada 404 latente)** + esperar respuestas Alex Q1-Q18 antes de tocar templates. **Tarea 2 BLOCKED** (sin Chrome MCP browser, requiere Alex login interactivo). ETA total ajustado: **80-100h CC en 5-6 semanas** (vs WC 60-80h en 4 semanas). Recomendación final: **proceder, en mi orden** (sección 8).

---

## 1. Review análisis WC (Tarea 1)

Respondo las 6 sub-preguntas:

### 1.1 ¿Categorización 34 templates correcta?

Mostly yes. Cubre lifecycle B.1-B.7 razonablemente. Observaciones:

- **Properties: ?**: 8 templates marcados con `?` en propiedad. Son genéricos (PROG: 60, 70, 80, special, etc.) que se mandan independiente de propiedad. OK como está.
- **Falta categoría "Closer/handoff"**: `00 Karina`, `6 - En el mar`, `6a - cualquier pregunta`, `special` son micro-templates que se concatenan al final de otros. WC los puso en "FAQ / handoff" + "Misc / closers". Más limpio: categoría única "Snippets / closers" con flag de uso (suffix vs standalone).
- **`Tres casas`** (multi-property inquiry): WC lo aisló bien como 1 template propio. Es el más sofisticado del set.
- **Wedding packages** (2 templates): no son inquiry response típica — son catalog brochure. Disonancia conceptual con resto del flow. **Mejor categoría**: "Catalog/menu reference" — templates standalone que NO siguen lifecycle, son refs.

### 1.2 ¿Inconsistencias detectadas reales?

Las 5 inconsistencias detectadas son **todas reales y verificables** desde el dump:

| # | Inconsistencia | Evidencia en knowledge files | Severidad |
|---|---|---|---|
| 3.4 | Servicio Morenas (incluido vs opcional) | Lines 137-145 templates ES vs 159-188 ES Morenas + kit Morenas sección 2 | 🔴 CRÍTICA — afecta venta |
| 3.5 | Precio bodas $1K vs $1.4K | Templates `Paquete Bodas` ES line 871 dice "1000 pesos" + `Wedding packages English` line 928. Kit RdM line 131 + Doc Eventos line 219 dicen "$1,400" | 🔴 CRÍTICA — riesgo legal |
| 3.6 | Tienda "El Güero" vs "La Azucena" | Kit RdM line 92 ("El Güero" 400m) vs Kit Morenas 183 ("El Guero" sin diéresis 400m) vs T-7 Huerta line 597 ("La Azucena" 100m) | 🟡 ORTOGRÁFICA + scope (¿son misma tienda?) |
| 3.7 | Conteo reseñas | Templates dicen "150", "120", "190", "200", "300" — ninguno coincide con D1 actual (167 ingestadas + total Airbnb potentially higher per `p.rating.count` content collection: RdM=167, Las Morenas=129, Combinada=89, Huerta=17) | 🟡 IMPORTANTE — desactualizado obviamente |
| 3.8 | Clave caja "6720" universal | Lines 642, 668, 687 — confirmado universal en T-1 de las 3 propiedades + archivada en mensajes AirBnB | 🔴 SECURITY — alto riesgo |
| 3.9 | Footer interno `--> rincondelasmorenas / --> rincondelmar` | En 14+ templates (every inquiry + closers) | 🟡 OPERACIONAL — ¿se manda al guest? |
| 3.10 | Frase "inseguridad de Acapulco" | 5+ templates (lines 80, 141, 200, 223, 263, 296) | 🟡 BRAND — anti-pitch del destino |

WC está correcto en todas. Add inconsistencia que WC no nombró:

**3.11 (CC nueva)**: URL `/guia-llegada` referenciada en T-14 templates (`PROG: 30 - Dos semanas antes Rdm` line 489, `PROG: 40 - Una semana antes - ambas` line 554) — esa página **NO existe** en `apps/web/src/pages/`. Linkean a 404. 🔴 CRÍTICO. Ver §3 abajo.

**3.12 (CC nueva)**: Equipo cocina inconsistente entre templates RdM ES vs EN:
- `0 - RdM completa` ES line 46: "un chef, **una cocinera y un mozo**"
- `2 - RdM english` line 109: "a chef and **two cooks**"
- `4 - Dos Villas español` line 261: "un chef y **tres cocineros**"
- Kit RdM line 79: "nuestra chef, **una cocinera y un mozo**"

¿Es 1 cocinera, 2, o 3? Difiere por capacidad o template confused?

### 1.3 ¿4 capas tienen sentido?

Sí, conceptualmente. Mi sugerencia:

- **Capa 1 Marketing/Discovery**: WC tiene razón. Owner = AirBnB listing fields + apps/web public pages.
- **Capa 2 Decision/Booking**: WC dice "AirBnB listing + bot WhatsApp conversational". Mejor: agregar `apps/web/[propertyId]` pages — ya son booking entry point real. Decision happens en sitio web también.
- **Capa 3 Operacional/Stay**: WC propone Welcome Guide. ✅ correcto.
- **Capa 4 Retention/Loyalty**: WC dice "AirBnB checkout template". Es muy thin — `PROG: 80` es solo CTAs review, no nutre relación. **Sugerencia**: agregar segundo touchpoint Capa 4: email transactional (Resend) post-checkout con thank you + invite Instagram + descuento próxima visita. Phase B+ futuro.

### 1.4 ¿Matriz "qué va dónde" bien repartida?

Mostly bien. Ajustes:

| WC matriz | Mi sugerencia |
|---|---|
| WiFi password → "AirBnB Check-in field" | ✅ Correcto. Y NO duplicar en Welcome Guide público (auth-gated en `/mi-estancia/welcome` solo) |
| Clave caja → "AirBnB Check-in field" | ✅ Correcto. Y rotación per booking (no más universal "6720") |
| Paquete boda $1,400 → "Guide #eventos + página /eventos" | Mejor: **única SOT = `/eventos.astro` standalone** (autoritativa pública SEO). Welcome Guide #eventos linkea a `/eventos`. AirBnB template linkea a `/eventos`. Reduce mantenimiento de 3 lugares a 1. |
| Restaurantes/actividades → Guide owner | ✅ Correcto |
| Emergencias → Guide #emergencias | ⚠ Mover a **`/mi-estancia/welcome`** auth-gated. Si guest hostil tiene URL pública, no le interesa el médico — pero teléfonos de Karina, Celene, etc. son data interna que NO debe ser público SEO. |

### 1.5 Duplicaciones que WC no detectó

- **Sign-off "Saludos, Alexander"** + emoji `🎼🎺🦐...` en 12+ templates. Si Alex se cambia name/sign-off, 12+ ediciones.
- **Hora salida 11am** repetida en 3+ templates (`PROG: 70`, `PROG: 80`, `PROG: 50`).
- **URL maps Goo.gl per-property**: `https://maps.app.goo.gl/TzuLJdWkj3gQZ1om7` (RdM) aparece 5+ veces. Si cambia (Google Maps short link expira), 5 ediciones.
- **WhatsApp links a personal contacts** (Michel `wa.me/527442217621`, Celene `527447713839`) en 5+ templates.
- **Logo emojis `⛱️⛱️⛱️⛱️⛱️⛱️⛱️⛱️⛱️`** repetido en kits (8+ veces dentro de mismo doc). Cosmético pero duplicación.

### 1.6 ¿Plan de fases viable?

Mostly yes, pero falta Fase 0.5 + reordenar dependencias. Detalle en §6.

---

## 2. Estado actual campos AirBnB (Tarea 2)

🚨 **BLOCKED** — Chrome MCP no tiene browser conectado:

```
mcp__Claude_in_Chrome__list_connected_browsers → []
```

Para Tarea 2 necesito Alex's browser session activa con Claude in Chrome extension instalado. Sin eso, NO puedo navegar `airbnb.mx/hosting/listings/editor/{listingId}/{section}` para los 4 listings × 10 campos = 40 fields.

**Alternativas en orden de preferencia**:

1. **(A) Alex Ctrl+S por field** (~2-3h work Alex, 0h CC): Alex abre cada uno de los 40 URLs en su browser logged in, hace `Ctrl+S` → "Página web completa", sube los 40 HTML files a un directorio compartido (Google Drive o tmp folder). Yo parseo con regex.
2. **(B) Setup Chrome MCP extension en Alex's browser** (~30 min Alex, después CC automatiza). Una vez setup, scraping toma ~1h CC con `mcp__Claude_in_Chrome__navigate` + `read_page` por field.
3. **(C) AirBnB Listings API** (~4-6h CC research + setup): Alex genera OAuth token AirBnB, CC lee fields via API. Pro: programmable, replicable. Con: AirBnB API permissions complicado, posible que algunos fields (Description, House Manual) no estén en API.

**Mi vote**: (B) — CC trabajo posterior es muy escalable (puede re-bajar fields cualquier momento future). (A) es más rápido one-shot pero one-shot = problema cuando vuelva a cambiar.

**Output cuando se desbloquee**: `knowledge/airbnb-listing-fields-current-2026-05-13.md` con:
- 4 propiedades × 10 campos = 40 secciones
- Comparación side-by-side ES/EN cuando aplique
- Highlights de qué duplica vs templates / kits

---

## 3. Estado actual apps/web (Tarea 3)

Inventory completo en: **`knowledge/apps-web-inventory-2026-05-13.md`**

Highlights críticos para Welcome Guide:

### 3.1 ✅ Stack listo

- **Astro i18n built-in habilitado** — `defaultLocale: 'es'`, locales `['es', 'en']`, `prefixDefaultLocale: false`. Pattern `/foo` (ES) + `/en/foo` (EN). Welcome Guide encaja.
- **Content collections** — pattern probado: `properties/{slug}.json` con fields ES + `_en` suffix. Welcome Guide content = extender JSON o nuevo collection `welcome/`.
- **R2 storage** — `KNOWLEDGE_BUCKET` con prefix `templates/` ya en uso (Phase B.0.5 PR #5-#7). Welcome Guide content puede usar prefix `welcome-content/`.
- **Better Auth** — magic link funcionando, `Astro.locals.user` populated en middleware. Auth-gate de `/mi-estancia` existe.
- **D1 Phase B Guest 360** — tablas creadas (vacías hasta backfill B.3b): `guests`, `leads`, `beds24_bookings`, `guest_events`. Per-booking dynamic data (WiFi, clave caja per estancia) puede vivir aquí.

### 3.2 🔴 Bug crítico latente: `/guia-llegada` = 404

Templates AirBnB linkean a `https://rincondelmar.club/guia-llegada` (T-14 RdM line 489 + T-7 ambas line 554). **Esa página NO existe**. Devuelve 404.

Lo que SÍ existe:
- `/como-llegar.astro` — pero es SEO marketing público sobre ruta CDMX, NO welcome content
- `/[propertyId].astro` — landing pública per propiedad (marketing/conversion, NO welcome)

**Implicación**: clientes que reservan, reciben T-14, click el link → 404. Bug de larga data que ningún template flow detectó porque Alex sale del path antes (probablemente). Severidad reputacional baja (no muchos lo click), técnica alta (404 archivado en mensajes AirBnB es señal poco profesional).

**Fix immediate (Fase 0.5)**: crear redirect `/guia-llegada` → `/como-llegar` (placeholder) o página estática básica con links a propiedades. ETA 30 min.

### 3.3 🟡 `/mi-estancia` esqueleto existe

`pages/mi-estancia/index.astro` + `datos.astro` + `reservas/` viven pero no hay welcome content. **Es el lugar natural para Welcome Guide auth-gated** (clave caja + WiFi + datos sensibles). vs `/welcome/{property}` público.

### 3.4 🟡 `/eventos.astro` no existe (paquete bodas $1,400 sin home autoritativa)

Solo existe `/eventos-corporativos.astro` (corporate-only landing). El paquete bodas $1,400 NO tiene página propia — solo vive en kits + AirBnB templates con precio desactualizado. SEO opportunity perdido + inconsistencia perpetuada.

---

## 4. Recomendación stack (Tarea 4)

### 4.1 Mi vote: **Opción A (build propio en apps/web)** con caveats

WC vota A. Concuerdo. **Pero con estructura específica**:

#### Architecture propuesta

```
apps/web/src/pages/
├── welcome/
│   ├── [property].astro                  # PÚBLICO general (capa 3 thread/36)
│   └── ...
├── en/welcome/
│   └── [property].astro                  # EN
├── mi-estancia/
│   └── welcome/
│       └── [bookingCode].astro           # AUTH-GATED data sensible per booking
└── eventos.astro                          # NUEVA — paquete bodas SOT autoritativa

apps/web/src/content/
└── welcome/                                # NUEVO collection
    ├── rincon-del-mar.es.json
    ├── rincon-del-mar.en.json
    ├── las-morenas.es.json
    └── ... (5 props × 2 idiomas = 10 files)

apps/web/src/components/welcome/
├── WelcomeLayout.astro
├── SectionLlegada.astro
├── SectionServicios.astro
├── SectionActividades.astro
├── SectionRestaurantes.astro
├── SectionEventos.astro
├── SectionEmergencias.astro              # Solo en /mi-estancia/welcome (auth)
├── SectionCheckinSensitive.astro          # Solo en /mi-estancia/welcome (clave caja, WiFi)
└── StickyTOC.astro                        # Mobile-first nav

apps/web/src/pages/admin/
└── welcome/                                # NUEVA Phase B.0.5 sibling
    ├── index.astro                         # Lista propiedades
    └── [property].astro                    # Editor (reuse pattern templates editor)

apps/web/src/pages/api/admin/
└── welcome/                                # API CRUD R2 + D1
    └── ...

apps/web/src/lib/
└── welcome-storage.ts                      # R2 wrapper (sibling de templates-storage.ts)
```

#### Storage strategy: hybrid R2 + content collection

- **R2** (`welcome-content/{property}.{lang}.json`): editable via admin UI sin git push, alinea con templates pattern
- **Build-time copy** (CC trick): build job descarga R2 contents → `apps/web/src/content/welcome/{property}.{lang}.json`, Astro genera páginas estáticas. Mejor SEO + cache CF + cero D1 query en render path. Re-build trigger via CF Pages webhook desde admin UI save.
- **D1 booking-specific data** (clave caja per estancia, WiFi password): query tiempo real en `/mi-estancia/welcome` SSR routes only.

#### Por qué A vs B (SaaS)

| Criterio | A Build propio | B SaaS Touch Stay |
|---|---|---|
| Costo monetario | $0/mes | $20-100/mes ($240-1200/año) |
| Costo CC time | 50-60h once | 4-8h setup + ongoing |
| Integración bot | Native (mismo stack R2/D1) | API integration custom |
| Datos dinámicos (WiFi/clave caja) | D1 query, fácil | API SaaS, depende capabilities |
| SEO bonus | ✅ Indexable own domain | 🟡 Subdomain o iframe (limitado) |
| i18n | Astro built-in (~$0) | Touch Stay multi-lang nativo (✅) |
| Branding | 100% control | Limited |
| PDF generation | Defer (~10h CC future) | Built-in |
| Migration path → otra cosa | Export JSON, easy | Vendor lock-in con datos en su DB |
| Templates conflict | Reusa pattern existing (PR #5-#7) | Paralelo (2 sistemas) |
| Total cost first year | ~$0 + 60-70h CC | $240-1200 + 8-12h CC |

#### Por qué A vs C (híbrido MDX)

C es más simple pero pierde el **editor advantage**. Sin admin UI, cada cambio requiere PR a CC. Para Alex (que NO quiere ser bottleneck) es worst-of-both.

### 4.2 Bot integration (con stack A)

- Bot conoce schema de Welcome Guide content (`packages/shared/src/welcome-context.ts` o similar). Bot can answer "¿hay WiFi?" → "Sí, contraseña va en `rincondelmar.club/welcome/{property}#casa` o cuando estés en estancia activa, en `rincondelmar.club/mi-estancia/welcome` con tu code de booking"
- Welcome auto-send Phase B.1 incluye link al guide (con `{property}` placeholder en template)
- FAQs detection: bot Haiku-classifies intent → matches with KNOWN_PLACEHOLDERS y/o WELCOME_SECTIONS → responde corto + link

### 4.3 i18n (con stack A)

Astro built-in: `/welcome/{property}` (ES) + `/en/welcome/{property}`. Already pattern probado.

Translation workflow:
- Admin UI tiene 2 tabs (ES + EN) per propiedad
- ES required, EN optional initially
- Si EN missing y guest navega `/en/welcome/...` → fallback a ES con banner "EN translation pending"

### 4.4 PDF generation

**Defer Fase 2.1** o más tarde. Razón:
- Best practice 2026 (per WC research): web > PDF para mobile
- Implementación: Puppeteer en Worker (heavy) o pre-render static PDF (storage R2)
- Si Alex realmente necesita PDF: 8-10h CC futuro
- For MVP, "Print page" del browser produce serviceable PDF

### 4.5 Analytics

CF Web Analytics ya configurada (per memoria + visto en stack inventory). **Extender** para track:
- Page views per `/welcome/{property}` route
- Section anchors clicked (#llegada, #servicios, etc.)
- Time spent per section
- PDF downloads (when applicable)

NO Google Analytics, NO Plausible third-party. CF Web Analytics es free + privacy-friendly.

---

## 5. Gotchas técnicos (Tarea 5)

### 5.1 🟡 AirBnB anti-off-platform policies

**Risk**: Host-Only Fee 17.98% (memoria 2026-05) significa Alex paga TODA la fee → AirBnB monitorea más agresivo si hosts tratan de migrar guests "off-platform" para evitar comisión futura. Linkear a `rincondelmar.club/welcome/...` en mensajes AirBnB ES funcionalmente lo que ya hacen Touch Stay y similares — aceptado en general.

**Templates current**: ya linkean externalmente:
- `https://www.airbnb.mx/users/95731371/listings` (own profile, OK)
- `https://wa.me/527442217621` (WhatsApp directo a tercero — gris)
- `https://rincondelmar.club/guia-llegada` (own domain — gris pero tolerated)
- `https://maps.app.goo.gl/...` (Google Maps — OK)

**Mitigation**:
1. Welcome Guide URLs no problemáticas si frame es "guía de llegada" no "página de booking alternativo".
2. Avoid en mensajes AirBnB: links directos a `wa.me/...` con teléfono Alex (tentación de "te paso WA para futuras reservas").
3. Welcome Guide NO debe tener CTAs tipo "reserve directo conmigo, te ahorras la comisión AirBnB". Eso es violación clara TOS.

### 5.2 🔴 GDPR/LFPDPPP datos terceros

**Risk**: ALTA. 12+ datos personales de 3rd parties en mensajes AirBnB archivados, en knowledge files, en kits WhatsApp:
- Celene (chef RdM): WhatsApp +52 744 771 3839
- Michel (masajista): WhatsApp +52 744 221 7621
- Karina (co-host): +52 744 355 3238
- AcaScuba/María José: +52 1 744 383 8162
- Carlos Vinalay, Norma Rivera, Daribel, Markos, Memo, Sandra
- DJ Pepe Vargas, Mariachis (3), Pasteleros (3), Maquillaje Danilo, Fotógrafo Brian, Belushama, 2 Padres
- Total: ~25 personas con datos PII en infrastructure

**Estado legal**: LFPDPPP México requiere consentimiento expreso para tratar datos personales en plataforma comercial. AirBnB messages archivados = tratamiento. Consentimientos verbal "Alex te recomiendo a mis huéspedes" probablemente NO satisface ARTÍCULO 8 LFPDPPP.

**Mitigation**:
1. **Audit consents**: Alex confirma cuáles 25 personas tienen consentimiento escrito (probablemente 0 con consent doc formal).
2. **Replace strategy en Welcome Guide**: NO publicar teléfonos individuales. Usar "Contacta a Karina (housekeeper líder) +52 744 355 3238 que te conecta con servicios" — UN punto de contacto centralizado, otros se conectan via Karina/Alex sin exponer datos.
3. **Templates current cleanup**: en AirBnB cambiar teléfonos individuales por link a Welcome Guide section (donde renderea según consent flag).
4. **Long-term**: cada 3rd party firma "Aviso de Privacidad" + consent. Plantilla 1-pager.

### 5.3 🟡 Multi-booking Combinada

Combinada (room 74316) es 1 listing AirBnB (18009632) que reserva las 2 propiedades a la vez. 

**Resolución**: tratar como entidad propia.
- `apps/web/src/content/welcome/combinada.es.json` independiente
- Welcome Guide para Combinada NO duplica contenido de RdM + Morenas — referencia: "Combinada incluye las amenidades de Rincón del Mar y Las Morenas; ver detalles individuales en [link]/welcome/rincon-del-mar y [link]/welcome/las-morenas"
- Sections que difieren (capacidad 58, ceremonial setup) son específicos a Combinada
- D1 booking has `room_id=74316` consistente — no conflict

### 5.4 🟢 WhatsApp Business API rate limits

ManyChat sendFlow tiene quotas. Cálculo:
- Volumen actual: ~30 bookings/mes
- Phase B.1 welcome auto-send: 1 message per booking = ~30/mes
- Pre-arrival (T-14, T-7, T-1): 3 messages × 30 = 90/mes
- In-stay + checkout: 3 × 30 = 90/mes
- Total: ~210 sends/mes (conservadoramente 300/mes con re-sends/follow-ups)

ManyChat free tier: 1,000 contacts. Paid tier: $15-145/mes. Rate limit envío: ~100/min, ~1M/día (varía por tier).

**No risk a escala actual ni 5x**.

### 5.5 🔴 Auth para datos sensibles (clave caja, WiFi)

**Status quo**: clave caja "6720" universal hardcoded en T-1 templates → archivada en AirBnB messages → si guest hostil ex-empleado tiene WhatsApp archive, exposure.

**Tres pattern auth options**:

| Pattern | Pros | Cons |
|---|---|---|
| **A) AirBnB nativo Check-in Instructions** | Solo guests confirmed lo ven. AirBnB enforce auth. | Per-property NO per-booking. Para per-booking necesitas update field cada vez (manual) |
| **B) URL con booking code `?b=HM3D2N5K`** | Per-booking auto. URL share-able with guest's group. | Booking code en URL = leak en server logs, browser history. Risk medium. |
| **C) Magic link per booking** | Auth real, expires post-stay | Adds friction, requires guest email |

**Mi vote**: hybrid:
- WiFi password: pattern A (AirBnB Check-in field) + Welcome Guide auth-gated `/mi-estancia/welcome` (Better Auth login)
- Clave caja: rotate per booking (admin UI generate random + push to D1) + show in `/mi-estancia/welcome` AUTH-GATED. T-1 template dice "tu clave caja temporal está en [link]/mi-estancia/welcome — login con tu email".

### 5.6 🟢 SEO Welcome Guide indexable

Split:
- **Public sections** (`/welcome/{property}`): transporte, supermercados, restaurantes, actividades — INDEXABLE. SEO bonus, gratis Google traffic.
- **Sensitive sections** (`/mi-estancia/welcome`): clave caja, WiFi, contactos privados — `noindex,nofollow` + Better Auth gate.

Schema.org: agregar `LodgingBusiness` + `FAQPage` markup en /welcome → SEO bonus.

### 5.7 🟢 Beds24 booking webhook YA implementado

Q15 thread/22 ya tiene Beds24 webhook funcionando + ingiere `beds24_events` table en D1. Welcome auto-send Phase B.1 puede triggerear con webhook → mensaje WhatsApp con `Welcome Guide URL` link. **No infra extra needed para integration, solo wiring**.

### 5.8 🟡 Cache strategy CF

**Public** `/welcome/{property}` — sections estáticas (transporte, supermercados, restaurantes, actividades) → CF Cache 24h-7d aggressive. Re-cache después de admin save (purge via CF API en webhook).

**Auth-gated** `/mi-estancia/welcome` — `Cache-Control: private, no-store`. SSR query D1 always.

**API endpoints** `/api/admin/welcome/*` — `private, no-cache` (admin only).

### 5.9 🟢 Casa Chamán Q3 2026 launch timing

Welcome Guide architecture es plug-and-play: agregar `casa-chaman.es.json` + `/welcome/casa-chaman` ruta dinámica → ya es URL viva. **Sin refactor estructural** future-proof.

ETA contenido Casa Chamán: cuando Alex esté listo (Q3 2026 es mucho antes que decisión content). Buffer: 4-5 meses para draft.

### 5.10 🆕 Conflict con templates system existente (Phase B.0.5)

WC no abordó: **¿Welcome Guide y Templates editor son sistemas paralelos o integrados?**

Mi propuesta: **integrados via mismo R2 bucket + admin UI sibling**:
- Templates: `KNOWLEDGE_BUCKET/templates/<name>.md` — corto-form messages
- Welcome content: `KNOWLEDGE_BUCKET/welcome-content/<property>.<lang>.json` — long-form structured content
- Admin UI: `/admin/templates` (existing) + `/admin/welcome` (sibling, mismo pattern)
- `lib/templates-storage.ts` (existing) + `lib/welcome-storage.ts` (sibling)

Ventaja: Alex tiene 1 mental model (admin UI con 2 tabs), CC tiene 1 storage abstraction.

---

## 6. Plan de fases ajustado

### Diferencias vs WC plan

| WC plan | CC ajuste | Razón |
|---|---|---|
| Fase 0 análisis (esta sem) | Fase 0 análisis ✅ — keep | OK |
| — | **Fase 0.5 fix /guia-llegada 404** (30 min CC) | Bug crítico latente, low effort, prevents customer-facing 404 |
| Fase 1 limpieza inconsistencias (1 sem) | **Fase 1a Alex respuestas** (Alex 4-6h) → **Fase 1b CC cleanup templates** (CC 2-3h) | Sin Q1-Q18 respuestas, cleanup es flying blind |
| Fase 2 Welcome Guide (2-3 sem) | **Fase 2 split en 2.1-2.6** (~50-60h CC ≈ 3 sem calendar) | Granularity ayuda planning |
| Fase 3 refactor templates | Fase 3 refactor (~10-15h CC + 4-6h Alex review) | Mantener pero secuencial post-Fase 2 |
| Fase 4 in-property QR | Fase 4 OPCIONAL defer | Bajo ROI inicial |
| Fase 5 bot integration | Fase 5 = Phase B.1 welcome auto-send (existing roadmap, ~18-22h) | Coincide con plan B existente |

### CC plan detallado

```
Week 0 (now)
├── Fase 0   Análisis ✅ (este thread/37)
└── Fase 0.5 Fix /guia-llegada 404         (CC 30 min)
            └── O redirect a /como-llegar O página estática placeholder con
                links a /welcome/{property} (post-Fase 2 launch redirige ahí)

Week 1
├── Fase 1a  Alex respuestas Q1-Q18         (Alex 4-6h)
├── Tarea 2  AirBnB scraping                (Alex Ctrl+S 2-3h o setup Chrome MCP)
└── Fase 1b  CC cleanup templates           (CC 2-3h)
            ├── Quitar footer interno --> rincondelasmorenas
            ├── Suavizar "inseguridad de Acapulco"
            ├── Update reviews count (depending Alex respuesta Q18)
            ├── Fix template `3 - Morenas` agregar mención servicio
            └── Decisión $1,000 vs $1,400 bodas (depending Alex respuesta Q5)

Weeks 2-4 (Fase 2 Welcome Guide build)
├── 2.1 Architecture + infra                (CC 8-12h)
│   ├── R2 prefix welcome-content/
│   ├── Astro routes /welcome/[property] + /en/welcome/[property]
│   ├── Content schema (TypeScript types)
│   ├── lib/welcome-storage.ts
│   └── Stickly TOC + section components shells
├── 2.2 Content RdM full ES                 (CC 6-8h)
│   └── 9 sections × Rincón del Mar (master example)
├── 2.3 Replicate to 3 más ES               (CC 6-9h)
│   ├── Las Morenas (clone RdM, adjust diferencias)
│   ├── Combinada (entity propia, refer to RdM/Morenas where shares)
│   └── Huerta Cocotera (no chef section variant)
├── 2.4 Translation EN                      (CC 4-6h)
│   └── 9 sections × 4 props EN (CC drafts, Alex review)
├── 2.5 Auth-gated /mi-estancia/welcome     (CC 8-10h)
│   ├── Better Auth gate
│   ├── Booking lookup (D1)
│   ├── Sensitive sections (clave caja per booking, WiFi)
│   └── Admin UI rotación clave caja
└── 2.6 Admin editor UI                     (CC 8-12h)
    ├── /admin/welcome listing
    ├── /admin/welcome/[property] editor
    ├── Live preview
    ├── Save → R2 → CF Pages rebuild trigger
    └── i18n tabs (ES + EN)

Total Fase 2 CC: ~40-57h ≈ 3 semanas calendar

Week 5
├── Fase 3   Refactor 34→16 templates       (CC 10-15h, Alex 4-6h review)
│   └── Each template ends with link a Welcome Guide section
└── /eventos.astro standalone               (CC 4-6h)

Week 6
└── Phase B.1 welcome auto-send (existing roadmap) (CC 18-22h)
            └── Beds24 webhook trigger → bot envía mensaje con Welcome Guide URL
```

### Totals

| | CC time | Alex time | Calendar |
|---|---|---|---|
| Fase 0 análisis | 3h (este thread) | 2-3h leer + decidir | done |
| Fase 0.5 fix 404 | 30 min | 0 (CC ejecuta) | week 0 |
| Fase 1a respuestas | 0 | 4-6h | week 1 |
| Tarea 2 AirBnB | 0-1h (post Alex) | 2-3h | week 1 |
| Fase 1b cleanup | 2-3h | 1h review | week 1 |
| Fase 2 Welcome Guide | 40-57h | 4-6h review content | weeks 2-4 |
| Fase 3 refactor | 10-15h | 4-6h review | week 5 |
| Fase 5 = Phase B.1 | 18-22h | 1h confirm | week 6 |
| **Total** | **74-99h** | **18-25h** | **~5-6 sem** |

vs WC original 60-80h CC + ~8-10h Alex en 4 sem. Mi estimate es +30% en time + 1-2 sem more calendar (mostly por respect Alex bandwidth + better testing/review per phase).

---

## 7. Preguntas abiertas

### Para Alex (urgent — bloquean execution)

| # | Pregunta | Sin respuesta no podemos |
|---|---|---|
| Q-A1 | ¿Verdad operacional servicio Morenas: incluido o opcional $1,000? (cf Q4 thread/36 sec 10) | Refactor Morenas templates + Welcome Guide #servicios |
| Q-A2 | ¿Precio bodas $1,400 final + update AirBnB templates inmediato? (cf Q5) | Refactor wedding templates + /eventos page |
| Q-A3 | ¿Tarea 2 approach: Ctrl+S manual, Chrome MCP setup, o AirBnB OAuth API? | Bajar 40 fields actuales |
| Q-A4 | ¿Welcome Guide auth split público/privado per mi propuesta §5.5, o todo público? | Architecture /welcome vs /mi-estancia/welcome |
| Q-A5 | ¿Datos terceros (Celene, Michel, etc.) consentimientos firmados o NO publicar tels en Welcome Guide? | Decidir si publicamos contactos vs single point Karina |
| Q-A6 | ¿Equipo cocina RdM real: 1 cocinera o 2 cooks o 3 cocineros? (inconsistencia 3.12) | Update templates + Welcome Guide content |
| Q-A7 | Footer interno `--> rincondelasmorenas / --> rincondelmar` ¿se manda al guest o se borra antes? (Q1 thread/36) | Refactor templates |
| Q-A8 | Clave caja "6720" ¿rotamos per booking en Phase 2 o seguimos universal por simplicidad? | Diseño /mi-estancia/welcome auth-gated section |

### Para WC (clarificación)

| # | Pregunta |
|---|---|
| Q-W1 | ¿Welcome Guide reuse R2 templates infra (mismo bucket prefix `welcome-content/`) o R2 prefix nuevo standalone? |
| Q-W2 | `/eventos.astro` standalone (mi propuesta) vs sub-section dentro de cada Welcome Guide (WC matriz)? |
| Q-W3 | Phase B.1 welcome auto-send: ¿link al Welcome Guide es trigger después de Fase 2 done, o mientras tanto bot puede mandar link a `/como-llegar` provisional? |
| Q-W4 | ¿Schema.org markup en Welcome Guide: solo `LodgingBusiness` o agregar `FAQPage` + `HowTo` para SEO bonus? |

---

## 8. Sí/No proceder

### Recomendación: **SÍ proceder**, con ajustes en orden de ejecución

Resumen:

1. ✅ **Empieza ya con Fase 0.5** (fix /guia-llegada 404, 30 min CC). Independiente de todo lo demás.
2. ✅ **Espera Alex respuestas Q-A1 a Q-A8** (Fase 1a) antes de tocar templates. ~4-6h Alex.
3. ✅ **Desbloquea Tarea 2** (AirBnB scraping) — Alex elige approach (mi vote: Chrome MCP setup).
4. ✅ **Procede Fase 1b cleanup templates** después de tener data complete.
5. ✅ **Procede Fase 2 Welcome Guide build** con stack A (build propio, R2 hybrid).
6. ✅ **Procede Fase 3 refactor 34→16 templates** post-Fase 2 done.
7. ✅ **Phase B.1 welcome auto-send** se beneficia del Welcome Guide URL para link en mensaje.

### Dependencias clave

```
Fase 0.5 (fix 404) --- standalone, NO blocks
Fase 1a (Alex Q&A) ── blocks ──> Fase 1b cleanup
Fase 1a (Alex Q&A) ── blocks ──> Fase 2 Welcome Guide
Tarea 2 (scraping) ── blocks ──> Fase 1b cleanup, NOT Fase 2
Fase 2 Welcome Guide ── blocks ──> Fase 3 refactor templates
Fase 3 templates ── feeds ──> Phase B.1 welcome auto-send
```

### Riesgos identificados en orden

| Riesgo | Severidad | Mitigation |
|---|---|---|
| GDPR/LFPDPPP datos terceros (§5.2) | 🔴 ALTA | Audit consents + replace tels con Karina single point |
| Clave caja universal "6720" exposed (§5.5) | 🔴 ALTA | Auth-gate /mi-estancia/welcome + rotación per booking Fase 2.5 |
| Templates 404 link `/guia-llegada` (§3.2) | 🟡 MED | Fase 0.5 fix immediate (30 min) |
| AirBnB anti-off-platform endurece (§5.1) | 🟡 MED | Avoid wa.me/Alex tel en mensajes AirBnB; frame Welcome Guide como guide no como booking alternative |
| Costos LLM Phase B.1 explota | 🟢 LOW | Cache hit monitoring (already configurado) |
| Welcome Guide content drift desactualizado | 🟢 LOW | Admin UI low-friction edit |

### Final answer Alex: **GO** con orden CC propuesto

Si confirmas, arranco Fase 0.5 immediate (30 min) en cuanto digas "go". Y mando este thread/37 a WC para ver respuestas Q-W1-Q-W4.

—

## Apéndice A — Files referenced

- `threads/36-wc-templates-content-architecture-analysis.md` — WC plan original
- `knowledge/airbnb-templates-current-2026-05-13.md` — 34 templates
- `knowledge/whatsapp-kits-current-2026-05-13.md` — 3 kits
- `knowledge/apps-web-inventory-2026-05-13.md` — CC inventory (sibling de este thread)
- `cc-instructions/2026-05-13-review-content-architecture-proposal.md` — task instrucciones
- (pending) `knowledge/airbnb-listing-fields-current-2026-05-13.md` — Tarea 2 BLOCKED

— Claude Code (CLI), 2026-05-13
