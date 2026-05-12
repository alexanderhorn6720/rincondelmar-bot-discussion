# INSTRUCCIÓN CONSOLIDADA PARA CC — Challenge Greeter v5 + Beds24 APIs validated

**From**: Alex (vía WC)
**To**: CC
**Status**: Read 3 threads first. NO code yet. Only review + challenge + verify + propose.
**Output**: Commit `threads/22-cc-greeter-v5-challenge.md`
**Decision after**: Alex decides Q1-Q6 (scope MVP, qué entra) antes de cualquier implementación

---

## Contexto cronológico (read in order)

1. **`threads/21-greeter-v5-site-routing-bot-onsite.md`** — WC propuesta original
   - 5 features core (Greeter v5, /disponibilidad/, FAQ expansion, Bot on-site, Reserva online)
   - 7 extensiones (Smart Quote, Comparador, Pages enriched, Video, Reviews aggregator, Calendar widget, Email pre-arrival)
   - 6 áreas de challenge (sección 5)
   - Q1-Q4 para Alex

2. **`threads/23-beds24-messages-reviews-api-unlocked.md`** — Alex validó 3 endpoints Beds24
   - `GET /bookings/messages` (multi-canal AirBnB+Booking+directos)
   - `POST /bookings/messages` (enviar + mark as read)
   - `GET /channels/airbnb/reviews` (Beta)
   - Re-priorización roadmap thread/21
   - 2 features nuevos: Client Bot post-booking + Reviews ingestion
   - Q5, Q6 nuevas para Alex

3. **Este documento** — task consolidada para CC

---

## Decisiones Alex ya tomadas (NO cuestionar)

- **Q4 ✅ RESUELTO**: Para top-20 FAQs ranked, NO uses Make datastore 85639. Usa el thread previo de **WhatsApp históricos** que ya procesaste con Alex (export chats raw). Esa data es la fuente, no Make conversations.
- Q1, Q2, Q3, Q5, Q6 pendientes — Alex decide después de leer tu thread/22

---

## Tu misión (en orden)

### 1. Read 3 threads completos

Lee thread/21 + thread/23 + este documento. Entiende:
- Las 5 propuestas originales + 7 extensiones
- Los 2 features nuevos desbloqueados por Beds24 APIs
- Roadmap re-priorizado
- Las 6 áreas de challenge

### 2. Verifica estado actual del sitio

Explora `apps/web/` en monorepo o navega producción para responder:

**Páginas:**
- ¿`/reservar/` existe? ¿Widget inline en fichas o página standalone?
- ¿Estado integración MP Checkout + Beds24 booking API?
- ¿`/tour-virtual/` hub está poblado con las 4 cards o vacío?
- ¿Existe `/cotizar/` o `/comparar/`?

**Anchors:**
- Verificar en `apps/web/src/pages/rincon-del-mar.astro` (o equivalente) si existen anchors `#galeria`, `#amenidades`, `#ubicacion`, `#reseñas`, `#faq`, `#calendario`
- Mismo check en las otras 3 fichas

**FAQ:**
- ¿Preguntas individuales tienen `id="faq-X"` o solo las 6 categorías?
- ¿Hay search/filter en la página?
- ¿Schema.org `FAQPage` markup?

**Analytics:**
- ¿Cloudflare Web Analytics o Plausible activos?
- ¿Páginas más visitadas? ¿Bounce rate `/rincon-del-mar/`?

**Calendario actual:**
- ¿Fichas tienen widget o solo placeholder "Cargando disponibilidad…"?
- ¿De dónde lee la data? R2 `availability.json` / Beds24 API directo / otra?

### 3. Verifica endpoints Beds24 con calls reales

Token: datastore Make 85380 key `main` (auto-refresh activo).

**Calls a hacer y documentar samples (anonimizados)**:

```bash
# 1. List messages recientes
curl -X GET "https://api.beds24.com/v2/bookings/messages?limit=10" \
  -H "token: $TOKEN" -H "accept: application/json"

# 2. Filtrar por canal AirBnB
curl -X GET "https://api.beds24.com/v2/bookings/messages?channel=airbnb&limit=10" \
  -H "token: $TOKEN" -H "accept: application/json"

# 3. Messages de un booking específico (tomar de bookings recientes)
curl -X GET "https://api.beds24.com/v2/bookings/messages?bookingId=XXXX" \
  -H "token: $TOKEN" -H "accept: application/json"

# 4. Reviews AirBnB
curl -X GET "https://api.beds24.com/v2/channels/airbnb/reviews?propertyId=31862&limit=10" \
  -H "token: $TOKEN" -H "accept: application/json"

# 5. Reviews per listing
curl -X GET "https://api.beds24.com/v2/channels/airbnb/reviews?listingId=18780853&limit=5" \
  -H "token: $TOKEN" -H "accept: application/json"
```

**Reporta**:
- ¿Schema response real vs schema esperado en thread/23 §1?
- ¿Devuelve mensajes de TODOS los canales o solo algunos?
- ¿Reviews trae histórico completo o solo últimas N?
- ¿Rate limits documentados o detectados?
- ¿Webhook events o solo polling?
- ¿Pagination cómo funciona (cursor, offset, page)?
- Sample responses anonimizadas en thread/22 para que WC pueda diseñar concretamente

### 4. Challenge supuestos WC con data

Responde con números, no opinión:

- **75% reducción tokens** — ¿realista?
  - Cuenta tokens de 10 últimas conversaciones Greeter v4 (Make datastore o WhatsApp histórico)
  - Proyecta tokens v5 con site-first routing
  - Devuelve reducción real esperada (%)

- **Bot on-site** — ¿competirá con WhatsApp o complementará?
  - Analiza patrones tráfico WhatsApp
  - ¿Usuarios que entran al sitio probablemente cierran sitio y van a WA, o se quedan?
  - Si hay analytics CF disponibles, usar data real

- **`/disponibilidad/` SSR Astro vs fetch from edge** — qué es más performant?
  - Considerar mobile 3G/4G typical RTT
  - Considerar Knowledge_Refresh cron 2h (data staleness)

- **Top-20 FAQs ranked** — 🔴 USAR WhatsApp histórico (thread previo con Alex), NO Make datastore
  - Devuelve lista ranked por frecuencia
  - Para cada uno: ¿se puede deflectar a sitio? ¿debe quedarse en bot?

- **Client Bot Phase A read-only** — ¿realmente zero risk?
  - ¿Polling rate apropiado (5min) sin saturar Beds24 API?
  - ¿Cómo manejar alerts a Alex sin spam (e.g. fuera de horario laboral)?

- **Reviews API utilidad real**:
  - ¿Cuántas reviews tiene cada listing actualmente?
  - ¿Se puede pull histórico completo o solo recientes?
  - ¿Vale la pena display sitio si Google ya tiene rich snippet de AirBnB?

### 5. Propón mejoras (additional ideas)

Vectores a explorar:

**Performance:**
- Service workers para offline-first + prefetch del calendario
- Edge caching estratégico (HTML TTL agresivo + invalidación post Knowledge_Refresh)
- Image optimization: ¿Cloudflare Images está usando responsive variants?
- Prefetch links cuando bot envía URL → mejora perceived latency

**Bot mejoras:**
- AB testing infra para canary Greeter v5 vs v4 (10% → 50% → 100%)
- Analytics granular: intent → URL clicked → conversion
- Fallback strategy si site cae (bot detecta + responde sin link)
- Versionado: cómo evitar drift entre prompt bot y contenido sitio

**Competencia:**
- Cómo lo hacen Plum Guide, AvantStay, Onefinestay, Misterb&b, Vrbo
- ¿Qué features tienen que no tenemos?
- ¿Cómo manejan multi-property availability search?

**Multi-channel/i18n:**
- Sitio tiene `/en/` — ¿está completo?
- Bot debería detectar idioma del user (mensaje en EN → respuesta + link a `/en/...`)
- Soporte futuro: portugués (Brasil mercado emergente?)

**Reviews leverage:**
- Schema.org `Review` + `AggregateRating` markup para Google rich snippet con estrellas en search results
- Open Graph dinámico per casa con rating + último review
- ¿Reviews 5★ con citas específicas → auto-trigger content pipeline social?

**Client Bot ideas adicionales:**
- ¿Auto-send pre-arrival info 7 días antes (qué llevar, cómo llegar, link tour virtual)?
- ¿Daily digest a Alex con resumen del día (bookings nuevos, mensajes pendientes, reviews nuevos)?
- ¿Post-stay automation: gracias + request feedback + offer descuento próxima estancia?

**Mobile-first patterns:**
- Bottom sheet para chatbox sitio
- Swipe gestures en `/disponibilidad/`
- Voice input para bot on-site?

### 6. Identifica riesgos

Lista riesgos técnicos y operacionales:

- ¿Sitio cae → bot solo linkea → cliente frustrado? Fallback strategy
- Versionado bot prompt vs sitio (e.g. bot dice "X está en /Y/" pero /Y/ se renombró)
- Testear cambios prompt sin romper conversaciones live
- Si Greeter v5 reduce conversions vs v4, ¿cómo detectarlo en <24h (no 1 semana)?
- Bot on-site: tokens cost vs valor real
- Privacy: session tracking bot on-site requiere cookie banner?
- `/disponibilidad/` data 2h-old → puede mostrar disponible una fecha que ya se reservó
- Rate limiting bot on-site (abuse prevention)
- Client Bot Phase A: ¿alerts spam si guest manda 5 mensajes seguidos?
- Reviews API Beta: ¿estabilidad? ¿deprecation timeline?
- POST /bookings/messages: si bot envía mensaje incorrecto a guest AirBnB → review malo afecta reputación

### 7. Recomienda scope MVP

Dado:
- Sprint 1 bot WhatsApp en canary (no rampado 100% todavía)
- AirBnB cutover apenas terminó (operational monitoring requerido 1ª semana)
- Reserva online si no existe = scope creep grande
- Beds24 APIs validadas abren Client Bot phased rollout

**Tu voto razonado**. Opciones combinadas:

**Q1 thread/21 — Site features**:
- A: Greeter v5 + `/disponibilidad/` (1 sprint, conservador)
- B: A + FAQ expansion (2 sprints)
- C: B + reserva online MVP (3-4 sprints — agresivo)
- D: C + bot on-site (4-5 sprints — overcommit?)

**Q5 thread/23 — Client Bot scope**:
- A: Phase A read-only solo (1 sprint, zero risk)
- B: A + B + C (3-4 sprints)
- C: Full Phase D (6+ sprints)
- D: Backlog total, solo Reviews

**Q6 thread/23 — Reviews ingestion + display**:
- YES: próximo sprint ~8h
- NO: backlog

Considera: capacidad team, riesgo, ROI esperado, dependencies bloqueantes.

### 8. Quick wins Phase 0

¿Hay algo implementable **HOY MISMO** que sea low-risk + high-value?

E.g.:
- Cron simple ingesta reviews AirBnB → tabla Airtable (sin display) — ~1h
- Daily digest a Alex de mensajes AirBnB unread vía WhatsApp — ~30 min
- Bookings new alert (cuando llega reserva AirBnB) — ~30 min

Lista Phase 0 quick wins con ETAs en thread/22.

### 9. ETAs revisados

Reto las estimaciones WC en sección 4 roadmap thread/21 (Fases A→F):
- Fase A pre-requisites
- Fase B quick wins
- Fase C Greeter v5
- Fase D Bot on-site (lower priority ahora)
- Fase E Reserva online (si entra scope)

Plus las fases nuevas thread/23:
- Reviews ingestion (Phase A → D)
- Client Bot post-booking (Phase A → D)

¿Realistas? ¿Faltan tareas? ¿Dependencies bloqueantes?

---

## Output format

Commit `threads/22-cc-greeter-v5-challenge.md` con estructura:

```markdown
# Thread 22 — CC challenge to Greeter v5 + Beds24 APIs

## 0. Site current state verification
[Sección 2 resultados — páginas, anchors, FAQ IDs, analytics, calendario actual]

## 1. Beds24 endpoints verification with real calls
[Sección 3 — sample responses anonimizadas, schemas reales, rate limits, paginación]

## 2. Challenge to WC assumptions (with data)
[Sección 4 — tokens reales, top-20 FAQs ranked from WhatsApp histórico, etc.]

## 3. Additional proposals
[Sección 5 — performance, bot, competencia, i18n, reviews, client bot, mobile patterns]

## 4. Risks identified
[Sección 6]

## 5. Recommended MVP scope + votes Q1, Q5, Q6
[Sección 7 — voto razonado con tradeoffs]

## 6. Phase 0 quick wins implementables HOY
[Sección 8]

## 7. Revised ETAs (Fases A-F + Client Bot + Reviews)
[Sección 9]

## 8. Open questions for Alex
[Cosas que CC necesita decisión antes de implementar — adicional a Q1-Q6]
```

Push a discussion repo. Avisa a Alex en chat cuando esté listo.

---

## Reglas

- **NO implementar nada** hasta que Alex decida Q1, Q2, Q3, Q5, Q6 (Q4 ya resuelto)
- **Verificar antes de asumir** — leer Astro source code real, hacer API calls reales
- **Data > opinión** — analizar WhatsApp histórico, Make scenarios, Beds24 API responses
- **Realista > ambicioso** — si algo es scope creep, decirlo claro
- **Challenge respetuoso** — WC propone, CC reta. Goal: Alex tener mejor decisión

ETA total: **2-3 horas** (read 3 threads + verify site + API calls + analyze + write).

---

*Esta es la instrucción FINAL consolidada. Alex la pasa al chat de CC. NO ejecutar tareas previas separadas.*

— Web Claude, 2026-05-12
