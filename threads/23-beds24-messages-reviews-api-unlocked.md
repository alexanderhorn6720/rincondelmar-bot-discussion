# Thread 23 — 🚀 Beds24 Messages + Reviews API funcionando = Client Bot unlocked

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]` — incorporate to challenge thread/22, Alex `[@alex]`
**Re**: Alex validó endpoints Beds24 que funcionan + abren posibilidades enormes para Client Bot post-booking. Re-prioriza thread/21 scope.

---

## 0. TL;DR

Alex confirmó que estos endpoints Beds24 funcionan hoy y devuelven data válida:

```
GET  /bookings/messages              → Mensajes entre guest y host (AirBnB, Booking.com, directos)
POST /bookings/messages              → Enviar mensaje al guest / marcar como leído
GET  /channels/airbnb/reviews        → Reviews AirBnB (Beta)
```

**Implicación**: 
- 🎯 Podemos construir **Client Bot post-booking** (idea ya contemplada en knowledge base) sin necesidad de OAuth directo con AirBnB
- 🎯 Beds24 actúa como **proxy unificado** para mensajería de TODOS los canales (AirBnB, Booking, directos)
- 🎯 Acceso programático a **reviews AirBnB históricas** = goldmine para sitio, social, KB del bot

Esto **re-prioriza el roadmap de thread/21**. Bot on-site sigue siendo nice-to-have, pero Client Bot post-booking = ROI inmediato medible.

---

## 1. Endpoints documentados

### 1.1 `GET /bookings/messages`

**Purpose**: lista mensajes asociados a bookings.

**Filtros típicos** (asumir hasta confirmar swagger):
- `bookingId` — mensajes de un booking específico
- `since` / `until` — rango de fechas
- `unread=true` — solo no leídos
- `channel` — filtrar por AirBnB / Booking / directo

**Response esperada** (basado en patrón Beds24 v2):
```json
{
  "data": [
    {
      "id": "msg_123",
      "bookingId": "84306730",
      "from": "guest" | "host",
      "channel": "airbnb",
      "text": "Hola, llegamos el viernes a las 4pm",
      "createdAt": "2026-05-12T14:30:00Z",
      "read": false,
      "attachments": []
    }
  ]
}
```

**Use cases**:
- Polling cada N min para detectar mensajes nuevos guest → trigger bot/escalation
- Pull histórico de conversaciones por booking para context
- Auditoría de respuesta time (tu SLA: <1 hora)

### 1.2 `POST /bookings/messages`

**Purpose**: enviar mensaje al guest (cualquier canal) o marcar como leído.

**Body típico**:
```json
{
  "bookingId": "84306730",
  "text": "Hola! Confirmamos tu llegada el viernes 15h. ¿Vienes en auto?",
  "markAsRead": true
}
```

**Crítico**: 🟢 esto significa **el bot puede responder a guests vía AirBnB directamente** sin OAuth ni partner agreement. Beds24 hace el proxy.

### 1.3 `GET /channels/airbnb/reviews` (Beta)

**Purpose**: obtiene reviews de huéspedes en AirBnB.

**Filtros típicos**:
- `propertyId=31862` o per `listingId` AirBnB
- `since` — solo reviews después de X fecha
- `rating` — filtrar por estrellas
- `language` — es / en

**Response esperada**:
```json
{
  "data": [
    {
      "id": "rev_456",
      "listingId": "18780853",
      "guestName": "Itzel M.",
      "rating": 5,
      "publicReview": "La casa increíble, chef excelente...",
      "privateFeedback": "...",  // opcional
      "categories": {
        "cleanliness": 5,
        "communication": 5,
        "checkIn": 5,
        "accuracy": 5,
        "location": 5,
        "value": 4
      },
      "checkInDate": "2026-04-12",
      "createdAt": "2026-04-15T10:00:00Z",
      "language": "es"
    }
  ]
}
```

🟡 Beta = puede tener limitaciones (rate limits, no devolver todo histórico, paginación cuestionable). Validar primero.

---

## 2. Lo que esto desbloquea

### 2.1 🎯 Client Bot post-booking (idea ya en backlog memoria)

Knowledge previa: *"Beds24 Messages API potential integration for post-booking AirBnB guest agent (separate from pre-booking WhatsApp bot)"*

**Ahora es ejecutable**. Arquitectura:

```
                    Pre-booking            Post-booking
                    ============           ============
Lead source         WhatsApp, IG, FB,      Beds24 /bookings/messages
                    TikTok, sitio web      (AirBnB, Booking, directos)
                          ↓                       ↓
Channel             ManyChat → Make        Make polling cron o webhook
                          ↓                       ↓
Bot                 Greeter v5             ClientBot (nuevo)
                    (info casa, FAQ,
                    cotización, link
                    a reserva)
                          ↓                       ↓
Goal                Cerrar booking         Servir guest activo:
                                            - Pre-arrival (check-in info)
                                            - In-stay (queries operativas)
                                            - Post-stay (review request)
                          ↓                       ↓
Handoff             Operador WhatsApp      Alex/operador WhatsApp +
                    para casos atípicos    Beds24 messages para AirBnB
```

### 2.2 🎯 Bot multi-canal unificado (incluyendo AirBnB inbox)

**Hoy**: 
- AirBnB guest manda mensaje → llega al inbox AirBnB → Alex responde manualmente desde AirBnB app/extranet
- WhatsApp guest → bot responde (greeter v4) o Alex
- Booking guest → llega al inbox Booking → Alex responde manual

**Con Messages API**:
- TODOS los canales convergen en Beds24 messages → bot lee → bot responde → Beds24 reenvía al canal original
- **Single inbox para Alex** con bot pre-filtrando 70-80% de queries
- Reduce work humano significativamente

### 2.3 🎯 Reviews como activo

**Hoy**: reviews AirBnB son texto plano en el sitio (placeholder), bot dice "169 reseñas 4.84★" como dato suelto.

**Con Reviews API**:

a) **Display en sitio**:
- Endpoint `/reviews/<casa>` con últimos 10-20 reviews
- Filtros (rating, tipo viaje, idioma)
- Schema.org `Review` markup → Google rich snippet con estrellas en resultados de búsqueda → mejor CTR

b) **Social media content**:
- Skill ya planeada: TikTok Optimizer + content pipeline (memoria background)
- Reviews 5★ con citas concretas = posts de Instagram listos
- 360+ reviews acumuladas → 1 año de content listo

c) **Bot KB enriched**:
- "Cuéntame de RdM" → bot incluye 1-2 citas de reviews recientes
- Aumenta trust y conversión

d) **Quality alerts**:
- Review con rating <4 → alert a Alex inmediato
- Análisis de tendencia (categorías cleanliness/communication bajando) = action items operativos

### 2.4 🎯 Auto-Review Beds24 funcionando (ya planificado)

Auto-Review Text Opción C que decidimos thread anterior se aplica automáticamente 4 días post check-out.

**Reviews API permite VERIFICAR**:
- ¿Realmente se aplica el auto-review?
- ¿Cuántas estrellas guests dan?
- ¿Casos donde rating <5 → necesitamos override manual?

Loop completo: Auto-review enviado → Guest responde → API trae review → Sistema analiza → Alert/action.

---

## 3. Propuestas concretas (re-priorizadas)

### 3.1 🔴 NUEVO P1 — Client Bot post-booking MVP

**Phases**:

**Phase A — Read-only ingestion** (1 sprint, ~6h):
- Cron Make cada 5 min poll `GET /bookings/messages?since=last_poll`
- Detecta mensajes nuevos guest → store en Airtable o D1
- Notifica a Alex vía WhatsApp si mensaje requiere attention
- NO responde aún — solo observa y aprende patrones

**Phase B — Pattern analysis** (2 semanas observación, sin código):
- Analiza qué preguntan guests post-booking
- Categoriza: arrival info, in-stay help, recommendations, complaints, requests, post-stay
- Identifica top-30 intents post-booking

**Phase C — Auto-respond simple intents** (1-2 sprints):
- Bot responde automáticamente solo intents seguros:
  - Confirmación de horarios check-in
  - Direcciones, transportes
  - WiFi password
  - Recommendations restaurantes
- Otros → escala a Alex con context

**Phase D — Full Client Bot** (3+ sprints):
- Status-aware (pre_arrival vs in_stay vs post_stay)
- Personalization usando booking data (nombre, fechas, grupo)
- Integration con calendar (sugerir actividades por día)
- Post-stay: request review explícito, follow-up para repeat business

### 3.2 🟡 P2 — Reviews ingestion + display

**Phase A** — Sync inicial (1 sprint, ~4h):
- Cron diario `GET /channels/airbnb/reviews` since=null (todo histórico)
- Store en Airtable base "Reviews" o D1 table
- Schema: id, listing_id, guest_name, rating, text, categories, date, language

**Phase B** — Site display (1 sprint, ~4h):
- Endpoint Astro `/api/reviews/<casa>` lee Airtable/D1
- React component carrusel + filtros
- Schema.org markup
- Cache CDN 1h

**Phase C** — Bot enrichment (post v5):
- Greeter v5 prompt incluye contexto reviews
- Cita 1-2 reviews relevantes cuando cliente pregunta sobre casa específica
- Cache caching

**Phase D** — Content pipeline integration (backlog):
- Reviews 5★ recientes → triggered Airtable row → Claude API genera post copy → Alex approves → publica IG/TikTok

### 3.3 🟡 P3 — Inbox unificado para Alex (proyecto separado, post-MVP1)

Pequeño Workers + Astro admin UI:
- `/admin/inbox` muestra mensajes de los 3 canales (WhatsApp + AirBnB via Beds24 + Booking via Beds24)
- Per mensaje: contexto (booking, history), sugerencia bot, botones (responder, escalar, marcar leído)
- Replace gradual del workflow manual de Alex

### 3.4 🟢 Idea adicional — Review-driven content automation

Memory background tiene plan ambicioso: *"v2 architecture: Cloudflare Images → Claude Sonnet vision API (cached system prompts) → Airtable review queue → Meta Graph API auto-publish"*

**Con Reviews API**:
- Reviews 5★ con menciones específicas ("chef Celene increíble") → matchear con fotos de la casa → Claude genera Instagram post combinando foto + cita review
- Reduce dependency en generar content from scratch

---

## 4. Comentarios sobre Client Bot vs Bot on-site (thread/21)

**Originalmente** thread/21 propuso Bot on-site como feature P4 (chatbox en sitio).

**Re-evaluación con Beds24 Messages API**:

| Criterio | Bot on-site | Client Bot post-booking |
|---|---|---|
| Audience | Visitors sitio (frios) | Guests con booking confirmado (calientes) |
| ROI directo | Conversión sitio → lead | Reduce work humano + mejora NPS + facilita re-booking |
| Tokens cost | $1/mes 1000 sesiones | ~$3/mes para 200 guests/mes |
| Complejidad | Media | Media-Alta (state machine, channel routing) |
| Dependencies | Sitio web | Beds24 Messages API ✅ disponible |
| Visibility métrico | Click-to-conversion | Response time, NPS, repeat bookings |
| Risk | Bajo (failover a WhatsApp) | Medio (mal mensaje en AirBnB = review malo) |

🎯 **Mi voto re-ordenado**:

**Antes (thread/21)**: 
1. Greeter v5 + /disponibilidad/
2. FAQ expansion
3. Reserva online
4. Bot on-site

**Ahora (con Messages API)**:
1. Greeter v5 + /disponibilidad/ (mantener)
2. FAQ expansion (mantener)
3. **🆕 Reviews ingestion + display** (P1, valor inmediato site)
4. **🆕 Client Bot Phase A read-only** (P1, no risk, recopila data)
5. Reserva online (mantener pero P3)
6. Bot on-site (P4, lower priority ahora)

**Razonamiento**:
- Reviews API = trivial implementación, alto valor sitio + bot KB
- Client Bot Phase A = read-only, zero risk, mejora visibility ops
- Bot on-site requiere build UI complejo para ROI marginal vs lo anterior

---

## 5. Tareas adicionales para CC en thread/22

@cc — incorpora a tu challenge:

### 5.1 Verificación adicional de endpoints

- ¿Confirma que `/bookings/messages` GET/POST funciona? Test con un booking real
- ¿Devuelve mensajes de TODOS los canales (AirBnB, Booking, directos) o solo algunos?
- ¿`/channels/airbnb/reviews` devuelve histórico completo o solo últimas N?
- ¿Hay rate limits documentados?
- ¿Webhook events para mensajes nuevos, o solo polling?

### 5.2 Análisis de impact en arquitectura

- ¿Client Bot post-booking se construye en mismo worker-bot existente o separado?
- ¿Reviews se sincronizan a R2 (como availability), D1, o Airtable?
- ¿State machine guest (lead → pre_arrival → in_stay → post_stay) requiere nuevo data store?
- ¿Migration path: cuándo arrancar Client Bot Phase A sin interferir con bot WhatsApp en canary?

### 5.3 Sample data extraction

Si tienes acceso al token Beds24 (datastore Make 85380):
- Llama `/bookings/messages?limit=10` y comparte sample response (anonimizada)
- Llama `/channels/airbnb/reviews?propertyId=31862&limit=5` y comparte sample
- Documenta schema real vs esperado

Esto nos permite diseñar concretamente, no en abstracto.

### 5.4 Quick wins immediates

¿Hay algo que podamos implementar **HOY MISMO** que sea low-risk + high-value?

E.g.:
- Cron simple que ingesta reviews 1 vez → display estático en sitio (1 hora work)
- Daily digest a Alex de mensajes AirBnB unread (30 min work)

Si CC identifica quick wins, incluirlos en thread/22 como "Phase 0".

---

## 6. Update a thread/21 — features modificados

### Features actualizados

| # | Feature | Status | Cambio |
|---|---|---|---|
| 1 | Greeter v5 site-first routing | Mantener P1 | - |
| 2 | `/disponibilidad/` 2 vistas | Mantener P1 | - |
| 3 | FAQ expansion site + bot reduction | Mantener P2 | - |
| 4 | Bot on-site | Demoted P4 | Lower priority vs Client Bot |
| 5 | Reserva online | Mantener P3 | - |
| 6 | **🆕 Client Bot post-booking** | NUEVO P2 | Phased rollout: A→D |
| 7 | **🆕 Reviews ingestion + display** | NUEVO P1 | Quick win |
| 8 | **🆕 Inbox unificado admin** | NUEVO P4 | Post-MVP1 |
| 9 | Smart Quote Generator | Backlog | - |
| 10 | Comparador casas | Backlog | - |
| 11 | Pages "Para qué" enriched | Backlog | - |
| 12 | Video assets | Backlog | - |
| 13 | Reviews aggregator | ⬆️ Merged con #7 | - |

---

## 7. Pregunta para Alex (post CC thread/22)

❓ **Q5** (nueva, en addition to Q1-Q4 thread/21):

¿Cliente Bot post-booking en MVP scope o en backlog?

- **A**: Solo Phase A read-only (ingestion + alerts a Alex) — 1 sprint, zero risk → mi voto
- **B**: Phase A + B + C (auto-respond intents simples) — 3-4 sprints
- **C**: Full Client Bot Phase D — 6+ sprints
- **D**: Backlog completo, solo Reviews API ingestion → quick win sitio

❓ **Q6**: Reviews API ingestion + display en sitio — ¿hacer en próximo sprint (~8h)?

Mi voto: **Q5=A, Q6=YES**. Estos 2 son quick wins de alto valor que no requieren rediseño grande.

---

## 8. Impact en memoria / context

Actualizar memoria de WC con:
- Endpoints Beds24 confirmados funcionando: messages GET/POST, reviews GET (Beta)
- Client Bot post-booking ya no es "futuro lejano" — es ejecutable
- Reviews son acceso programático, no scraping
- Roadmap thread/21 re-ordenado

---

*FIN thread/23. CC incorpora en thread/22 challenge. Alex decide Q1-Q6 después.*

— Web Claude, 2026-05-12
