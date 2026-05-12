# Thread 21 — Greeter v5: Site-as-Knowledge-Base + bot deflection a reserva online

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]` — **CHALLENGE & EXTEND**, Alex `[@alex]` — decide before implementation
**Re**: Estrategia para que el bot deje de tipear texto largo y empiece a routear al sitio. Incluye nuevas ideas de Alex: deflection a reserva online, bot on-site, calendario con dropdown.

---

## 0. Status

Alex confirmó:
- ✅ Idea calendario unificado le gusta + quiere también vista per-property con dropdown
- ✅ FAQ: extender en site agrupado, reducir scope bot a top-20 most asked
- ✅ Enfatizar reserva online (más fácil que vía bot, menos tokens)
- ✅ Idea nueva: bot on-site (chatbox en landing page que dirige a secciones)
- 🟡 CC challenge: revisar ideas, retar implementación, proponer más

Este thread es para **CC review + reto**, NO para implementación. Alex decide antes de cualquier código.

---

## 1. Inventario actual del sitio (verificado 2026-05-12)

### URLs existentes
```
/                                    Inicio
/rincon-del-mar/                     Ficha completa villa
/las-morenas/
/huerta-cocotera/
/combinada/
/casa-chaman/                        "Próximamente" (NO usar en bot todavía)

/bodas/
/eventos-corporativos/
/reuniones-familiares/
/pie-de-la-cuesta/                   Zona / Barrio Mágico

/tour-virtual/                       Hub (verificar contenido)
/tour-virtual/rincon-del-mar         360°
/tour-virtual/las-morenas
/tour-virtual/huerta-cocotera
/tour-virtual/combinada

/faq/                                ✅ Categorizado: General | Mascotas | Pago | Cómo llegar | Eventos | Chef
/blog/
/como-llegar/
/contacto/
/privacidad/

/desde/cdmx/                         SEO landing por origen
/desde/edomex/
/desde/puebla/
/desde/cuernavaca/

/en/...                              Versiones EN
```

### Anchors verificados en `/faq/`
✅ `#cat-general` `#cat-mascotas` `#cat-pago` `#cat-llegada` `#cat-eventos` `#cat-chef`

Cada FAQ pregunta tiene markdown `**¿pregunta?**` pero **NO IDs por pregunta individual** (no se puede linkear a una pregunta específica, solo a categoría).

### Anchors en fichas de casas (e.g. `/rincon-del-mar/`)
🟡 NO se identificaron anchors `#galeria`, `#amenidades`, etc. en el HTML. 

**Task para CC**: verificar si existen en el Astro template (`apps/web/src/pages/rincon-del-mar.astro` o similar). Si no, agregarlos.

### Reserva online — existe?
🟡 La página `/rincon-del-mar/` no muestra widget de booking obvio. Solo dice "Cargando disponibilidad…" como placeholder.

**Task para CC**: verificar estado de:
- Página dedicada `/reservar/` o `/reservar/<casa>/`
- Widget de booking inline en fichas
- Integración con MercadoPago + Beds24 booking API

Si no existe → **CRÍTICO construir antes de Greeter v5**, sino el deflection "puedes reservar en línea fácil" miente.

---

## 2. Propuesta consolidada (5 features)

### 2.1 🔴 Greeter v5 prompt — "Site-First Routing"

**Filosofía**: bot tipea menos, linkea más. Single source of truth = el sitio.

**Cambios al prompt**:

Sección nueva `# REGLAS DE LINKS — site-first`:
- Detectar intent (info casa, fotos, tour, calendar, FAQ, evento, llegada, reserva, etc.)
- Responder con 1-2 frases highlight + link específico
- NO escribir párrafos describiendo lo que está en la página linkeada
- Adjuntar UTM tags para tracking

Sección reducida `# FAQ` (de 60+ a top-20):
- Mantener inline: precio anticipo, métodos pago, mascotas (línea base), check-in/out, capacidad
- TODO lo demás → link a `/faq/#cat-X`

Sección nueva `# DEFLECTION A RESERVA ONLINE`:
- Cuando intent es booking confirmation, en vez de capturar datos vía bot, enviar:
  > "Puedes reservar en línea, es muy fácil: confirmas fechas, eliges casa y pagas con tarjeta (a meses sin intereses), transferencia SPEI o tu cuenta MercadoPago. Tarda 2 minutos:
  > 
  > https://rincondelmar.club/reservar/<casa>/?fechas=<X-Y>"
- Bot sigue activo para: dudas previas, casos complejos (grupos >30, eventos, fechas conflictivas)
- Booker scenario activa SOLO si cliente prefiere humano o tiene caso atípico

**Tokens estimate**: greeter v4 ~600 tokens output promedio → v5 ~150 tokens. **75% reducción**.

### 2.2 🔴 Página `/disponibilidad/` con 2 vistas

Reto de Alex: necesita 2 vistas, no solo la cross-property.

**Vista A — Multi-property (default)**:
```
┌─────────────────────────────────────────────────────────┐
│   Disponibilidad · Las 4 casas                          │
│   [Mes: Mayo 2026 ▼]                                    │
├─────────────────────────────────────────────────────────┤
│ Día  RdM   Morenas  Huerta  Combinada                  │
│ 12   🟢    🟢       🟢      🔴 (RdM ocupa)             │
│ 13   🟢    🟢       🟢      🔴                          │
│ 14   🔴    🟢       🟢      🔴                          │
│ ...                                                      │
├─────────────────────────────────────────────────────────┤
│ Click día → modal con detalle + CTA "Reservar"          │
└─────────────────────────────────────────────────────────┘
```

**Vista B — Single property con dropdown**:
```
┌─────────────────────────────────────────────────────────┐
│   Disponibilidad de: [Rincón del Mar ▼]                 │
│                       Las Morenas                        │
│                       Huerta Cocotera                    │
│                       Combinada                          │
├─────────────────────────────────────────────────────────┤
│   Calendario clásico mensual                            │
│   L  M  M  J  V  S  D                                   │
│   .  .  .  .  🟢 🟢 🟢                                  │
│   🟢 🟢 🟢 🔴 🔴 🔴 🔴                                  │
│   ...                                                    │
│   Min stay shown per día (e.g. "min 4 noches" en sáb)   │
└─────────────────────────────────────────────────────────┘
```

**Implementación técnica**:
- Worker apps/web nueva route `/disponibilidad/`
- Query param `?casa=rincon-del-mar` activa vista B
- Default sin param → vista A
- Fetch R2 `availability.json` (existe, generado por Knowledge_Refresh cron 2h)
- Render SSR Astro + React island para interactividad
- Mobile-first

**Bot integration**:
- "¿Qué fines tienes libre?" → `https://rincondelmar.club/disponibilidad/`
- "¿Disponible 10-12 mayo?" → consulta Beds24 + responde + linkea `https://rincondelmar.club/disponibilidad/?casa=rincon-del-mar` para verificar visualmente

### 2.3 🔴 FAQ expandido en site + reducción en bot

Estado actual:
- Site FAQ: ~30 preguntas en 6 categorías ✅
- Bot KB: estimado 60+ FAQs en system prompt

**Propuesta**:

**Site FAQ extension** (target ~60-80 preguntas categorizadas):
- Mantener 6 categorías actuales
- Agregar IDs por pregunta individual: `id="faq-cancelacion-30dias"` para linkear directo
- Buscador en página (Algolia/Pagefind o simple JS filter)
- Schema.org `FAQPage` markup para Google rich snippet

**Bot KB reduction** (target top-20 most asked):
Análisis de conversaciones pasadas (Make datastore 85639 conversations_v2) para identificar top-20 por frecuencia.

Top-20 que probablemente son (basado en intuición + screenshots históricos):
1. Mascotas — sí, todas pet-friendly
2. Check-in/out — 3PM / 11AM (rigid post-Connect)
3. Capacidad por casa — 30/30/12/60
4. Anticipo — 33% no reembolsable
5. Métodos pago — MP, transferencia, OXXO
6. Chef incluido — RdM, Morenas, Combinada (NO Huerta)
7. Llegada aeropuerto — 45 min taxi
8. Llegada CDMX — 4-5 hrs autopista
9. WiFi — sí, 99+ Mbps
10. A/C — sí en todas las recámaras
11. Alberca — sí, todas
12. Pie de playa — sí, todas (excepto Huerta es palapa privada en playa)
13. Eventos — RdM/Morenas hasta 80, Combinada hasta 150, Huerta 30
14. Niños — sí
15. Estacionamiento — sí
16. Factura CFDI — sí
17. Idioma staff — español + inglés básico
18. Cancelación general — 33% no reembolsable
19. Política mascotas — sin cargo, traer cama
20. Casa para grupos chicos vs grandes — recommendation

Cualquier otra → bot dice: *"Para eso tenemos info detallada en https://rincondelmar.club/faq/#cat-pago — ¿algo más en lo que te ayudo?"*

**Tokens estimate**: bot KB reduction ~40% del system prompt.

### 2.4 🆕 Bot on-site — chatbox en landing page

**Concepto**: chatbox embebido en `rincondelmar.club` donde usuario hace pregunta y bot lo dirige a sección del sitio o casa específica.

**Diferencia clave vs WhatsApp bot**:

| Característica | WhatsApp Bot | Bot On-Site |
|---|---|---|
| Goal | Generar lead → handoff a humano para reservar | Self-service: ayudar al user a encontrar info, llevar a reservar |
| Output principal | Texto conversacional | Texto BREVE + link clickeable + render scroll to section |
| State | Persistente por subscriber_id | Session-only (sin sign-up) |
| Tools | Beds24 calendar lookup, handoff, knowledge | Site navigation, scroll-to-section, deep-links a calendar/reserva |
| Latency target | 3-5s OK | <2s (web UX expectations) |
| Modelo | Haiku 4.5 (greeter actual) | Haiku 4.5 — same, even más simple system prompt |

**Diseño UI**:
```
┌────────────────────────────────────────────┐
│  Página actual (rincondelmar.club/)        │
│                                            │
│  ...                                       │
│                                            │
│                          ┌──────────────┐  │
│                          │ 💬 Pregunta? │  │  ← floating button
│                          └──────────────┘  │
└────────────────────────────────────────────┘

Click → expande:
┌────────────────────────────────────────────┐
│  ✕                                         │
│  Hola, soy el asistente. ¿Qué buscas?     │
│                                            │
│  [Disponibilidad fines de mayo]            │  ← quick replies
│  [Ver fotos Rincón del Mar]                │
│  [Cuánto cuesta evento boda]               │
│  [Cuál casa para 20 personas]              │
│                                            │
│  ┌──────────────────────────────────┐      │
│  │ Escribe tu pregunta...            │      │
│  └──────────────────────────────────┘      │
└────────────────────────────────────────────┘
```

**Interaction flow**:
```
User: "Cuánto cuesta para 20 personas un fin de semana"
Bot: "Para 20 personas, Rincón del Mar o Las Morenas funcionan perfecto.
      Te llevo al calendario y precios:"
      [Botón: Ver disponibilidad RdM]   ← deeplink a /rincon-del-mar/#calendario
      [Botón: Ver disponibilidad Morenas]
      [Botón: Comparar las 2 casas]    ← scroll a sección comparativa

User clicks botón → 
  - Si link interno: scroll suave a sección, highlight 2 seg
  - Si link external: nueva pestaña con UTM tracking
```

**Implementación técnica**:
- Worker apps/web nueva endpoint `/api/onsite-bot` (POST text → respuesta + acciones)
- React island en layout global con state local
- Storage: sessionStorage (no requiere auth)
- Misma Anthropic API integration que el bot WhatsApp (Files API + caching)
- DIFERENTE system prompt — más corto, output JSON `{message, links: [{label, url, action}]}`
- Latencia: cache hit ~600ms p50

**Coste estimate**: ~$0.001 per conversation (3-5 turns Haiku con cache). Para 1000 sesiones/mes ≈ $1/mes.

**Valor agregado**:
- Reduce tráfico al bot WhatsApp para preguntas que SE pueden self-service
- Aumenta conversion rate del sitio (chatbox UX = engagement)
- Datos de qué buscan los usuarios = roadmap insights para contenido
- Pre-cualifica lead antes de handoff a WhatsApp (cliente ya vió fotos, calendar, etc.)

### 2.5 🔴 Reserva online → flow completo

**Status verificación pendiente**: ¿existe `/reservar/`?

**Si NO existe** (probable) → **build BEFORE Greeter v5 deflection**:

**Flow propuesto**:
```
1. Cliente entra a /reservar/<casa>/?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD
2. Formulario:
   - Confirma fechas (pre-filled)
   - Selecciona huéspedes (adultos, niños, mascotas)
   - Datos contacto (nombre, email, WhatsApp)
   - Opcional: comentarios especiales
3. Cliente ve breakdown:
   - X noches × $Y = $Z subtotal
   - + Cleaning fee
   - + Extra person fees (si aplica)
   - + Pet fee (si aplica)
   - = Total
   - "Pagas 33% ahora: $W"
4. Pago MercadoPago Checkout:
   - Tarjeta crédito (a meses sin intereses ✅)
   - Tarjeta débito
   - Transferencia SPEI
   - OXXO
   - Cuenta MercadoPago
5. Confirmación:
   - Crea booking en Beds24 (estatus "request" hasta segundo pago)
   - Email confirmación (template pre-arrival)
   - Calendar event ICS
   - WhatsApp opcional con detalle
```

**Componentes técnicos**:
- Cloudflare Worker `apps/reservar/` nuevo (o extend `rincon-pago` existente)
- React form con state machine (XState o similar)
- API `POST /api/reservar/quote` → consulta Beds24 calendar + pricing
- API `POST /api/reservar/confirm` → crea MP preference + Beds24 booking
- Webhook MP listener (ya existe en Make `4709161` y workers/rincon-pago) — extend/replace

**ETA realista**: 2-3 sprints (~3-4 semanas) si se hace bien con tests.

🟡 **Decisión crítica**: ¿esto entra en MVP1 scope o se queda en backlog?
- **Pro**: completa el "deflection a reserva online" del prompt
- **Contra**: scope creep enorme. MVP1 era para terminar Sprint 1 bot WhatsApp.

**Mi voto**: **MVP simple de reservar primero** — solo flow happy-path, sin mascotas/extras complejos, solo RdM y Huerta primero (las más simples). Iterar después.

---

## 3. Propuestas ADICIONALES — extensiones del concepto

### 3.1 🆕 Smart Quote Generator

URL: `/cotizar/?fechas=X-Y&grupo=N&mascotas=M`

Una sola página que toma input mínimo y devuelve:
- Las 4 casas con precios para esas fechas/grupo
- Highlights de cada casa relevantes (capacidad, chef, mascotas)
- CTA "Reservar esta" directo

Bot deflection: "Tengo una herramienta que te muestra los 4 precios en 30 segundos: https://rincondelmar.club/cotizar/?fechas=2026-06-15_2026-06-17&grupo=20"

Reduce conversaciones repetitivas "cuánto cuesta para X".

### 3.2 🆕 Comparador de casas

URL: `/comparar/` o `/comparar/rincon-del-mar-vs-las-morenas/`

Tabla side-by-side:
- Capacidad, recámaras, baños
- Servicios incluidos
- Pricing range
- Para qué tipo de grupo
- Fotos representativas

Bot deflection: "Te ayudo a decidir entre RdM y Morenas: https://rincondelmar.club/comparar/rincon-del-mar-vs-las-morenas/"

### 3.3 🆕 Pages "Para qué" mejoradas

`/bodas/`, `/eventos-corporativos/`, `/reuniones-familiares/` — existen pero probable que son thin content.

**Propuesta**: enriquecer con:
- Casos reales (anonimizados)
- Pricing template por tamaño de grupo
- FAQ específico (e.g. en `/bodas/`: música hasta cuándo, permisos, vendors recomendados)
- Galería filtrada del use case
- CTA fuerte "Cotizar tu boda" → smart quote pre-filled

### 3.4 🆕 Video assets

- Hero videos en home + cada ficha (5-15 seg, drone shots)
- Video walkthrough de cada casa (5 min, narrado)
- Testimonios en video de huéspedes (3 ejemplos)

Bot deflection: "Te paso un video walkthrough de 3 minutos de RdM: https://rincondelmar.club/rincon-del-mar/#video"

🟡 Requiere production work (no es solo código). Backlog mediano-largo.

### 3.5 🆕 Reviews aggregator en sitio

Actualmente bot dice "169 reseñas 4.84★ en Airbnb" como texto plano.

**Propuesta**: scraper + cache de top reviews + display en sitio con filtros (por casa, por tipo de viaje, idioma).

Sitio actual nota: *"En PR3 vamos a destacar los más recientes en esta misma página"* — ya en roadmap.

Acelerar esto, integrar con bot:
- Bot deflection: "Mira lo que dicen otros huéspedes: https://rincondelmar.club/rincon-del-mar/#reseñas"

### 3.6 🆕 Calendario embebible (widget)

Para futuro: ofrecer a Alex un widget JS que pueda embedber en otros sitios (e.g. partner properties, blog posts).

Long-term. Backlog.

### 3.7 🆕 Email pre-arrival automation

7 días antes de check-in, email con:
- Cómo llegar (link a `/como-llegar/`)
- Checklist qué llevar
- Tour virtual (link)
- Restaurantes en la zona
- Lista de servicios opcionales (masajes, paseos lancha) con precios

Esto NO es bot ni site — es email automation. Pero conecta: el bot puede deflectar "qué llevar" → "Te llega un email 7 días antes con toda la info de llegada, ¿algo específico que necesitas saber ya?"

---

## 4. Roadmap propuesto (prioridad y dependencias)

### Fase A — pre-requisites (1 sprint)
- A1. Verificar `/reservar/` existe o no — CC
- A2. Si NO existe → decisión Alex: build ahora o backlog
- A3. Verificar anchors `#galeria`, `#amenidades`, etc. en fichas — CC
- A4. Si NO existen → agregar al Astro template — CC

### Fase B — quick wins (1-2 sprints, sin tocar bot)
- B1. Página `/disponibilidad/` con 2 vistas — CC, ~6h
- B2. Anchors faltantes en fichas — CC, ~2h
- B3. Site FAQ expansion (60-80 preguntas + IDs por pregunta) — Alex content + CC code, ~8h
- B4. UTM helper en bot — CC, ~1h

### Fase C — Greeter v5 (1 sprint)
- C1. Análisis top-20 FAQs reales — WC + CC, ~2h
- C2. Greeter v5 prompt con site-first routing — WC, ~3h
- C3. Deflection deshabilitable hasta que `/reservar/` existe — WC, conditional
- C4. A/B test con 10% canary — CC + Alex monitor, 1 semana

### Fase D — Bot on-site (1-2 sprints)
- D1. UI/UX design — Alex review, ~3h
- D2. Worker `/api/onsite-bot` — CC, ~6h
- D3. React island chatbox — CC, ~4h
- D4. System prompt + Files API integration — WC + CC, ~3h
- D5. Deploy + canary — CC, ~2h

### Fase E — Reserva online (2-3 sprints, si entra en scope)
- E1. Design flow — Alex review, ~4h
- E2. Quote API — CC, ~6h
- E3. Form UI — CC, ~8h
- E4. MP Checkout integration — CC, ~6h
- E5. Beds24 booking creation — CC, ~4h
- E6. Email confirmations — CC, ~3h
- E7. Tests + canary — CC, ~8h

### Fase F — Extensions (backlog, low priority)
- Smart quote generator
- Comparador
- Video assets
- Reviews aggregator
- Email pre-arrival

---

## 5. Reto explícito para CC

@cc — **review and challenge** before any implementation. Specifically:

### 5.1 Cuestiona mis supuestos

- ¿Es realista 75% reducción tokens con site-first routing, o estoy optimista?
- ¿Bot on-site va a competir con WhatsApp o complementar? Validar con data
- ¿`/disponibilidad/` con SSR Astro vs fetch from edge — qué es más rápido?
- ¿FAQ reduction bot 60→20 va a generar más handoffs por preguntas no respondidas?

### 5.2 Verifica estado actual del sitio

- ¿`/reservar/` existe? ¿Estado de la integración MP + Beds24 booking?
- ¿`/tour-virtual/` hub está poblado o vacío?
- ¿Anchors en fichas existen en el Astro source code?
- ¿Hay analytics existentes (CF Web Analytics, Plausible) para ver qué páginas visita el usuario actual?

### 5.3 Propón mejoras

- ¿Alguna idea adicional al concepto site-first?
- ¿Hay optimizaciones técnicas (e.g. service workers, prefetch) para mejorar el flow?
- ¿Análisis de competencia: cómo lo hacen Plum Guide, AvantStay, Onefinestay?
- ¿Sugerencias de tracking para medir éxito de Greeter v5 vs v4?

### 5.4 Identifica riesgos

- ¿Qué falla si el sitio se cae y el bot solo linkea?
- ¿Versionado del sitio vs bot prompt — cómo evitar drift?
- ¿Backup plan si Greeter v5 reduce conversions vs v4?

### 5.5 Cuestiona alcance MVP

- ¿Reserva online MVP realmente es 1 sprint o son 3?
- ¿Bot on-site es prioritario o lo dejamos para Sprint 3?
- ¿Vale la pena hacer Greeter v5 si `/reservar/` no está listo (no podemos hacer deflection completo)?

### 5.6 Output esperado de CC

Commit `threads/22-cc-greeter-v5-challenge.md` con:
1. Verificación estado actual del sitio (sección 5.2)
2. Challenge a supuestos WC (sección 5.1)
3. Propuestas adicionales (sección 5.3)
4. Riesgos identificados (sección 5.4)
5. Scope recommendation MVP (sección 5.5)
6. Estimaciones revisadas de ETA por feature

Alex decide después de leer thread/22.

---

## 6. Preguntas para Alex (post CC review)

❓ **Q1**: Scope MVP — qué entra primero:
  - A: Solo Greeter v5 + `/disponibilidad/` (más conservador, 1 sprint)
  - B: A + FAQ expansion (2 sprints)
  - C: B + reserva online MVP (3-4 sprints)
  - D: C + bot on-site (4-5 sprints, ambicioso)

❓ **Q2**: ¿Construir `/reservar/` ahora o mantener handoff humano para closing?

❓ **Q3**: ¿Bot on-site vale la inversión o usuarios mobile prefieren WhatsApp directo?

❓ **Q4**: ¿Top-20 FAQs los defino yo (basado en conversaciones pasadas en datastore 85639) o tú me das tu lista?

---

## 7. Memoria / context preservation

Este thread + cualquier follow-up de CC en thread/22 + decisiones de Alex deben quedar en repo discusión para que Sprint 3+ tenga contexto completo.

Crear en repo: `docs/site-as-knowledge-base-strategy.md` con resumen final post-decisions.

---

*FIN thread/21. CC review pending. Alex decide post CC.*

— Web Claude, 2026-05-12
