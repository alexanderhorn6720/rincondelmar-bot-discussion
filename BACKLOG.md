# RdM Bot · Backlog Completo

**Fecha original**: 2026-05-18 morning (brain mode)
**Última revisión**: 2026-05-18 evening — cleanup post-Sprint C+E+D+P2 canary + PRs #88-97 shipped + Pre-stay MVP spec ready
**Próxima revisión sugerida**: cada 14 días o post-sprint mayor (lo que ocurra primero)
**Autor**: WC
**Alcance**: Bot conversacional + admin tools + features estratégicos
**Propósito**: Inventario único, exhaustivo, no perderlo en hand-offs futuros

**Relación con otros docs canónicos del repo**:
- `CONTEXT.md` → estado verificado del sistema (propiedades, stack, IDs). Source of truth técnico.
- `ROADMAP.md` → fases macro (Fase 0/1/2/3/4) con timeline mensual.
- `VISION.md` → norte estratégico de largo plazo.
- `BACKLOG.md` (este doc) → inventario operacional P2/P3 con effort estimates + sequencing.

Este doc NO reemplaza a los demás. Es complemento táctico para no perder items específicos entre sesiones. Si hay contradicción con `CONTEXT.md`, gana `CONTEXT.md`.

**Excluidos por scope**: Foundations + Charter, personal items, M1-M5 conceptual modules, ideas I11-I14 operations. Esos viven en `rdm-platform/` y `VISION.md`.

---

## 1 · Resumen ejecutivo

Hand-off documentation perdió items específicos de los buckets P2 y P3. Este doc consolida **TODO** el backlog descubierto a lo largo de threads 89-115 y memorias acumuladas, organizado por:

- **Estado actual** del sistema (qué está LIVE, qué está en pipeline CC)
- **P2 — Operational fixes** (sprints cortos, 1-8h cada uno)
- **P3 — Strategic features** (multi-day, requieren brain mode + spec)
- **Voto WC sequencing** post-pipeline-actual

Estimado total backlog: **~150-200h CC** + brain mode WC para specs.

---

## 2 · Objetivo

Construir el **journey huésped completo automatizado** end-to-end para Rincón del Mar (4 propiedades + Casa Chamán Q3), donde Alex interviene **por elección**, nunca por necesidad.

El bot conversacional fue la primera capa. Las siguientes capas son:

1. **Operational hardening** — fixes que están afectando users hoy
2. **Guest intelligence** — saber quién es el huésped antes de saludarlo (Guest 360)
3. **Proactive lifecycle** — bot escribe primero en pre-stay/in-stay/post-stay
4. **Revenue optimization** — upsells, drip campaigns, lost-booking recovery
5. **Analytics layer** — unit economics, forecasting, cancellation analysis
6. **Brand growth** — UGC pipeline, Casa Chamán launch coordinado

Métrica norte: **% de touch-points huésped manejados sin Alex/Karina activos** (hoy ~40-50%, target 90%+ pre-checkout, 70%+ in-stay).

---

## 3 · Espíritu

### Principios no-negociables

| Principio | Implicación práctica |
|---|---|
| **Beds24 source of truth** | Sync mode `Prices & Availability` ONLY. NUNCA `Everything` |
| **AirBnB source of truth para listings** | Bot no genera content de listings; sólo Karina edita |
| **No LLM en decisiones de dinero** | Pricing, descuentos, deducciones = deterministic logic. LLM solo para prose summary |
| **Bot nunca obliga, siempre habilita** | Alex interviene por elección, no por urgencia |
| **Encapsulación por módulo** | Bot pre-stay separado de in-stay, separado de post-stay. No "do-it-all bot" |
| **Multi-canal mismo prompt MVP** | WhatsApp + FB + IG + TikTok, single prompt; templates HSM fase final |
| **Debounce 8s sin excepciones** | Excepto `/start` y `/stop`. Sin typing indicator |
| **Mobile-first siempre** | Xiaomi 15 es el primary device de operación |

### Working modes (WC ↔ CC ↔ Alex)

| Mode | Output | Cuándo |
|---|---|---|
| brain | Análisis + opciones | Default, decisiones complejas |
| brain quick | Recommendation 5min | Decisión rápida |
| brain deep | Spec doc completa | 1h+ análisis pre-implementation |
| DoIt | Spec ejecutable autónomo | CC implementa sin permisos a cada paso |
| verify | Comandos guiados Alex | Validación pegada a sistema real |

Flujo típico: `brain → spec → DoIt → verify`.

### Anti-patrones generales

- ❌ Reintervenir CC en scope mid-flight (issue separada, no fix aquí)
- ❌ Bypass DoIt template v3 conventions
- ❌ Auto-merge PRs a main sin Y/N
- ❌ Force-push, delete branches, drop databases (DENIED en autonomy config)
- ❌ Promote a producción sin smoke test
- ❌ Casa Chamán visible en Greeter prompt antes de Q3 renovation

---

## 4 · Estado actual del sistema

### LIVE (no tocar sin razón fuerte)

| Componente | Status |
|---|---|
| Greeter V6 | 100% canary, telemetría verde |
| Booker | LIVE |
| Multi-canal AirBnB Connect API | Post-cutover 2026-05-12 |
| Beds24 integration | `/v2/inventory/rooms/calendar` source of truth |
| Beds24 booking webhook (Phase C) | LIVE — migration 0011 + backfill PR #84 |
| Beds24 messages outbound (Part E) | LIVE PR #90 + body shape fix PR #94 — **canary validated 2026-05-18, Beds24 msg ID 148091343** |
| `messenger_outbound` audit table (migration 0032) | LIVE |
| `MESSENGER_OUTBOUND_ENABLED` flag | LIVE, flipped back OFF post-canary (default OFF, manual flip per release) |
| `extra_guests_captures` (migration 0033) + cron daily scan | LIVE PR #90 (detection-only v1, manual fire via drawer) |
| ManyChat WhatsApp | LIVE |
| Anti-loop guards | LIVE |
| Telegram alerts | LIVE |
| `/admin/conv` | LIVE |
| `/admin/bookings` | LIVE PR #82 + guest name + 360d window PR #93 |
| `/admin/inbox` | LIVE PR #85 + ReplyPanel via Part E |
| `/admin/extra-guests` | LIVE PR #93 (Karina row-per-row send-outreach) |
| `/admin/airbnb-content` | LIVE (Karina onboarding 95% — magic-link verify pending) |
| `/admin/health` | LIVE |
| `/proxReservas` | LIVE post hotfix PR #91 (guest name source from guests table) |
| ChannelBadge SVG logos for OTA | LIVE PR #92 |
| Spanish UX sweep across /admin pages + layout nav | LIVE PR #96 |
| Greeter v5 pet policy `/noche → /estancia` + orphan prompt file delete | LIVE PR #97 (from thread/118 §4+§5) |
| Beds24 backfill 62 pre-webhook bookings | LIVE |
| Greeter V6 small items wave #1 (F+C+A+B) PR #87 | LIVE |
| Greeter V6 small items wave #2 (G+H+I+J) PR #88 | LIVE |
| Greeter V6 small items hotfix /guia-llegada redirect PR #89 | LIVE |
| Data Mining v2 D1 seed (Phase B tables) | LIVE — **7,423 guests + 5,874 leads + 51,414 guest_events** |
| Reviews ingestion (migration 0012 + `reviews-sync.ts` + ReviewsCarousel) | LIVE |
| `pre_arrival_sent_at` cron on `bookings` direct table | LIVE (worker-pago, but only direct 5-row scope, NOT beds24_bookings) |
| thread/115 guests.name resync from Beds24 + mojibake auto-fix + debug stats (PRs #98-100, migration 0034) | LIVE |

### Pipeline CC (shipped + queued)

| Item | Effort | Status |
|---|---|---|
| thread/113 hotfix `/proxReservas` guest name (PR #91) | — | ✅ Shipped |
| thread/109 wave-2 G+H+I+J (PR #88) + redirect hotfix (PR #89) | — | ✅ Shipped |
| C+E+D+P2 sprint (PR #90 + body-shape PR #94) | 15-19h CC | ✅ Shipped + canary validated |
| Admin guest name + 360d window (PR #93) | — | ✅ Shipped |
| ChannelBadge OTA UI (PR #92) | — | ✅ Shipped |
| Spanish UX admin sweep (PR #96) | — | ✅ Shipped |
| v5 pet policy + orphan delete from thread/118 (PR #97) | — | ✅ Shipped |
| thread/115 guests.name resync from Beds24 (PR #98 + mojibake fix #99 + debug stats #100) | 2-3h CC | ✅ Shipped — migration 0034 applied |
| **Pre-stay MVP A1-A4** (spec `cc-instructions-bot/2026-05-18-pre-stay-notifications-mvp.md`, migration 0035) | 35-50h CC across 4 atomic PRs | 🟡 Queued — spec deep ready 2026-05-18 |

Total CC autónomo pipeline pendiente: **~35-50h** (Pre-stay A1-A4).

Pending de Alex (post-sprint canary):
- Pre-stay A1-A4 reviews when CC ships
- Catch-up trigger post-A4 (Karina supervising, 6 candidates ready in window)

### Datos clave del stack

| Recurso | Detalle |
|---|---|
| D1 database `rincon` | `d81622d7-32e2-40a3-9609-80813c0e8a96` |
| R2 buckets | `assetsrdm`, `rdm-knowledge` |
| KV | `KV_KNOWLEDGE` |
| WhatsApp business | `+52 55 7061 8798` |
| Beds24 propertyId | `31862` |
| Rooms | 78695 RdM · 374482 Morenas · 74316 Combinada · 637063 Huerta · 679176 Casa Chamán (hidden Q3) |
| Repos GitHub | `rdm-platform`, `rdm-bot`, `rdm-discussion` bajo `alexanderhorn6720` |
| Path local Windows | `C:\Users\Alexa\rdm\dev\{platform,bot,discussion}\` |
| Latest D1 migration | 0034 (guests_name_locked, thread/115 PR #98). Next pre-stay = 0035 |

---

## 5 · P2 — Operational fixes

Sprints cortos, 1-8h cada uno. Pueden tomarse uno a la vez sin spec brain mode.

**Items cerrados en revisión 2026-05-18 evening** (removidos de la tabla activa):
- ~~P2.1 Welcome auto-send "bug"~~ → No era bug. Pipeline detection funciona; outbound wire era deferred. **Resolución**: incorporado a Pre-stay MVP spec §Y1 (PR A2 drena 10 rows pending_welcomes). Ver `cc-instructions-bot/2026-05-18-pre-stay-notifications-mvp.md`
- ~~P2.2 Cron threshold per-cadence~~ → Shipped PR #90 Part C
- ~~P2.3 Conversation rule tuning `lead_cold_7d` → 5d~~ → Shipped en small items wave (PR #87/88)
- ~~P2.4 Pet fee uniformización AirBnB listings~~ → Implementación en código + web LIVE; Alex 2026-05-18 cerró el tema
- ~~P2.5 Gantt range default 180d → 365d~~ → Shipped PR #93
- ~~P2.9 Strip " (AirBnB)" suffix retroactivo~~ → Cubierto en thread/115 spec edge 4 (queued)
- ~~P2.12 Beds24 webhook Phase C~~ → Shipped PR #84 + Phase C webhook live
- ~~P2.13 Worker `rincon-bot` manual deploy~~ → Routine post-PR (no es task discreto)
- ~~P2.14 PR #32 review~~ → Ancient (cursor en PR #97)
- ~~P2.15 Greeter v5 PR A1.5 sub-components~~ → Replaced en v6 prompt (canary 100%)
- ~~P2.17 Pet policy /noche → /estancia content-drafts~~ → Shipped PR #97 from thread/118
- ~~P2.19 Data Mining v2 Day 1 start~~ → Done (threads 72-77). Seed: 7,423 guests + 5,874 leads + 51,414 guest_events en prod D1

**Items activos (post-cleanup)**:

| # | Item | Effort | Trigger / contexto |
|---|---|---|---|
| P2.6 | **Real logos swap** en `apps/web/public/logos/` | 5min tú + 30min CC | Pendiente desde Day 1 |
| P2.7 | **Rotar PAT expuesto** (thread/56) + `ADMIN_REFRESH_SECRET` | 15min | Alex 2026-05-18: "no urge" — security hygiene cuando convenga |
| P2.8 | **Old paths cleanup** `C:\rincondelmar-*\` | 10min tú | Post-rename to `rdm-*` |
| P2.10 | **Re-link 3 promo bookings** 86496769/86497786/86685323 → recipients reales | 1h investigación + manual | Separate dedupe post-thread/115 |
| P2.11 | **Re-dedupe Alex 2 guest records** (g_01KRSZ + g_XRP4Y5, phones distintos) | 1h | Separate dedupe post-thread/115 |
| P2.16 | **Karina onboarding final** — magic-link verify + walkthrough `/admin/{inbox,bookings,airbnb-content,extra-guests}` | 30-45min Alex + Karina | Unblocks objetivo handoff |
| P2.18 | **weekend_price RdM erróneo** + cache expiry post-Jun 2027 → Default fallback | 1h | Beds24 pricing backlog |
| P2.20 | **Vectorize tail unblock** — completar Data Mining v2 (17k embeddings → index `rdm-conversations-v2`) | 5min Alex scoped CF token + 2-3h CC-Data background, ~$0.19 | Handoff doc: `cc-instructions-data/2026-05-16-vectorize-handoff.md`. Bot NO consume aún (greeter v6 no wired); unlock futuro |
| P2.21 | **Operator playbook v6 → bot KB integration verify** | 1h WC | Confirmar que Greeter v6 consume `data/artifacts/operator_playbook-v6-trimmed.md` correctamente |
| P2.22 | **AirBnB published listings verify pet policy** | 30min Karina manual | Web + greeter ya correctos (`$300/estancia, máx 2`); pendiente verificar listings publicados en airbnb.com no digan `/noche` |

**Total P2 estimado restante**: ~6-8h CC + ~3-4h Alex/Karina manual + ~3h CC-Data.

---

## 6 · P3 — Strategic features

Requieren brain mode + spec doc antes de DoIt.

### 6.1 · P3-A · Guest 360

**Objetivo**: Saber quién es el huésped antes de saludarlo. Cross-property history, repeat detection, VIP segmentation, lifetime value.

**Scope total**: ~80h CC, ~2 meses calendario.
**Status memoria 2026-05-18 evening**: D1 Phase B tables built **y poblados via Data Mining v2** — `guests` (7,423), `leads` (5,874), `guest_events` (51,414), `beds24_bookings` (poblado via webhook + backfill). Architecture approved. **Lo que falta es la lens UI** (B.7) para que humanos consuman los datos.

| Phase | Scope | Status |
|---|---|---|
| B.1 | Guest profile unified view across channels | ✅ Data Mining v2 seedeó |
| B.2 | Repeat guest detection via phone match | ✅ guests dedup vía phone_e164 PK |
| B.3 | VIP tier segmentation — Bronce (1 stay), Plata (2-3), Oro (4+) per I8 | ⚪ Schema soporta, sin compute aún |
| B.4 | Cross-property guest history | ✅ guest_events timeline poblado |
| B.5 | Lifetime value calculation per guest | ⚪ Schema soporta, sin compute aún |
| B.6 | Guest events timeline (bookings + messages + reviews) | ✅ events table 51k rows |
| **B.7** | **`/admin/leads` UI unificado** — bloqueador real ahora | 🟡 No iniciado. Sin esto, 13k+ rows seedados están ciegos |
| B.8 | Booking.com integration (deferred from initial scope) | ⚪ Out of immediate scope |

**Drivers downstream**: alimenta I1 pre-stay (en spec), I3 in-stay, I8 VIP, I9 drip, M4 staff scheduling.

**WC recomendación**: promover **B.7 a P2** — es lo que desbloquea Guest 360 entero. Resto es procesamiento sobre data que ya existe.

---

### 6.2 · P3-B · Pre-stay notifications (I1 Pre-arrival concierge)

**Objetivo**: Bot proactivo escribe welcome + T-7 + T-1 antes check-in con canales multi-source (Beds24 messages OTA + ManyChat direct).

**Status 2026-05-18 evening**: ✅ **Brain deep spec ready** at `cc-instructions-bot/2026-05-18-pre-stay-notifications-mvp.md`. Awaiting CC-Bot capacity.

**Effort revisado**: ~35-50h CC across 4 atomic PRs (A1-A4). Effort original 12-16h estaba subestimado para scope MVP completo.

| Component | Stack | Status |
|---|---|---|
| Wire welcome cron → `sendMessageRouted` (Part E) | Migration 0035 + drains 10 pending_welcomes rows | 🟡 PR A2 spec'd |
| Cron pre-arrival T-7d + T-1d (drop T-3d v1) | Worker cron + GitHub Actions | 🟡 PR A3 spec'd |
| Template render per property × lang × touchpoint (24 templates) | Hardcoded TS module v1, source = wc-seed-drafts content | 🟡 PR A1 spec'd |
| Channel routing | Re-use `resolveRoute()` from messenger-send.ts | ✅ Infra ready |
| Idempotency | 4 new columns en beds24_bookings (migration 0035) | 🟡 PR A1 spec'd |
| Catch-up one-shot for próximas 4 sem objetivo | Rate-limited admin endpoint, Karina supervisa | 🟡 PR A4 spec'd |
| Admin override drawer en /admin/bookings | Per-row buttons: Send Welcome / T-7 / T-1 / Skip | 🟡 PR A4 spec'd |
| Feature flag gate | `MESSENGER_OUTBOUND_ENABLED` (re-use Part E, no nuevo) | ✅ Validated 2026-05-18 |
| Audit | `messenger_outbound` table (re-use Part E) | ✅ Live |

**Universe**: 19 bookings activos en próximas 4 semanas (T-1: 1, T-2-7: 5, T-8-14: 4, T-15-28: 8 + uno mañana). Tractable. Single canary batch safe.

**Out of scope v1** (deferred): T-3 chef menu, T-0 day-of, in-stay touchpoints (Client Bot Phase A), reply handling (/admin/inbox handles), email channel (Alex: no), LLM personalization (v2), Casa Chamán (Q3).

**Drives**: objetivos Alex 2026-05-18 — ↓ workload personal + handoff Karina + huéspedes próximas 4 sem cubiertos al 100%.

**Anti-patrón**: nunca enviar pre-stay si el huésped escribió en últimas 48h (sería ruido). Spec captura en R10.

---

### 6.3 · P3-C · Ideas catalogadas (subset)

19 ideas totales en `rdm-platform/ideas/`. Aquí el subset relevante para hand-off (sin I11-I14 operations):

#### Guest experience (4)

| ID | Idea | Foundation requerida |
|---|---|---|
| I1 | Pre-arrival concierge AI personalizado | Cubierto en P3-B arriba |
| I2 | Digital check-in/out con QR — direcciones + Waze + código cerradura rota + house manual | R2 manuals + D1 `access_codes` |
| I3 | In-stay WhatsApp assistant — lane separado del Greeter pre-booking | V7 multi-bot personality routing |
| I4 | Welcome packet generator multilingüe — render PDF + send link, EN/ES/FR | Welcome-auto-send v2 (ya en `welcome-auto-send.ts`) |
| I5 | Post-stay review request automation — T+24h, plantilla suave, ≤3★ → Telegram | `reviews-sync.ts` ya tiene audit |

#### Revenue & marketing (5)

| ID | Idea | Detalle |
|---|---|---|
| I6 | Upsell engine post-booking | Catálogo: chef Morenas $1k-1.5k/d, transport, tours, masajes, fogata, decoración, DJ, fotos, paseo caballo. Tablas `addons_catalog`, `booking_addons` |
| I7 | Lost-booking recovery | User llena fechas+huéspedes sin pagar en 2h → bot WhatsApp con incentivo suave. Anti-spam: solo si dio teléfono explícito |
| I8 | Repeat guest VIP segmentation | Tiers Bronce/Plata/Oro (driver para P3-A) — discount auto, upgrade prob, welcome amenity, named greeting |
| I9 | Drip campaign post-cotización | Día+1/+3/+7/+14 anchor a cotización original. Cohort conversion tracking |
| I10 | Dynamic packaging | "Bodas grupo 40" / "Retiro corporativo" / "Año nuevo 4N+gala" — precio bundled vs à la carte savings visible |

#### Analytics & intelligence (3)

| ID | Idea | Detalle |
|---|---|---|
| I15 | Unit economics dashboard per booking | `revenue gross - commission canal - fees pago - costo chef/staff - grocery - consumibles - mantenimiento prorrateado - utilities prorrateado = net margin`. Revela cuál booking type es rentable real |
| I16 | Cancellation root cause analysis | Timing antes arrival + razón (guest input + AI inference) + refund amount + channel. Drive policy `deposit_non_refundable_threshold`. Campo `cancellation_reason` ya existe en `bookings` |
| I17 | Weather + event impact forecasting | Cross-ref `beds24_bookings.arrival` con pronóstico clima 14d + calendario eventos Acapulco (Tianguis, Foro, congresos, vacaciones SEP, mareas, alertas huracán jun-nov). Proactive reschedule preventivo |

#### Brand & growth (2)

| ID | Idea | Detalle |
|---|---|---|
| I18 | Guest UGC pipeline | T+7d post-stay opt-in "¿compartir foto/video con crédito?" → R2 upload + consent firma digital + Airtable queue Karina curar + post auto IG/TikTok con tag. Reduce ~90% tiempo Karina haciendo content |
| I19 | Casa Chamán launch playbook | Coordinador Q3 2026 — checklist T-90d (fotos, tour 360°, EN/ES, pricing, AirBnB listing, landing waitlist) · T-60d (drip históricos, IG/TikTok teaser) · T-30d (soft-launch VIP) · T-0d (público + Greeter prompt incluye 679176) · T+30d (review iteración) |

---

### 6.4 · P3-F · Bot lifecycle V7

**Objetivo**: Separar Greeter pre-booking de Concierge in-stay de Relationship post-stay.

| Lifecycle | Bot personality | Trigger |
|---|---|---|
| `booked` (pre-arrival) | Greeter actual | New conversation, lead nurturing |
| `in_stay` | Concierge bot (I3) | `beds24_bookings.lifecycle=in_stay` — operación casa, "¿cómo enciendo calentador?", "más toallas" |
| `past_stay` | Relationship bot | Post-checkout T+24h — review request, retention, drip |

**Decisión pendiente**:

| Voto | Aproach |
|---|---|
| WC-Implementation | 3 distinct prompts (`greeter-prebooking-v7`, `concierge-instay-v1`, `relationship-poststay-v1`) selected by router |
| WC-Platform thread/91 | 1 prompt con condicionales lifecycle internas |

**Tradeoff**: 3 prompts = separate concerns + caching + testing + debug; penalty = 3x management overhead. 1 prompt = single source of truth; penalty = condicionales explotan rápido.

**Acción**: Alex pick + WC spec deep mode antes implementation.

---

### 6.5 · P3-G · Beds24 Reviews API integration (Beta)

**Objetivo**: Ingestar reviews de huéspedes directamente desde Beds24 Reviews API Beta para display en sitio + bot KB enrichment, sin necesitar AirBnB OAuth.

| Component | Status |
|---|---|
| Reviews ingestion P1 | Spec pending |
| Display on `rincondelmar.club` | Spec pending |
| Bot KB enrichment con reviews | Spec pending |
| Client Bot Phase A | DEMOTED to P2 después de Reviews API discovery |

**Por qué importante**: ~360+ reviews históricas en AirBnB (rating 4.85) + Booking.com. Desbloqueadas en KB del bot suben significativamente la calidad de respuestas sobre "¿cómo es la propiedad?" "¿qué dicen huéspedes?".

---

### 6.6 · P3-H · 174 FAQs curation → 50-80 finales

**Objetivo**: Curar FAQ extraction (PR #81) a entries usable en Vectorize embeddings para Greeter KB retrieval.

| Status | Detail |
|---|---|
| Extracted | 174 candidates DELIVERED PR #81 |
| Pending | Curation Alex/Karina, finalize 50-80 |
| Phase next | Vectorize embeddings rebuild + Greeter KB retrieval |

**Effort**: 4-6h Alex + Karina manual review. CC handles Vectorize rebuild post-curación (~1h).

---

## 7 · Voto WC · sequencing post-pipeline-actual

**Revisado 2026-05-18 evening** alineado con objetivos Alex (chat de sesión):
1. ↓ workload personal WhatsApp + Airbnb
2. Handoff operativo a Karina
3. Próximas 4 semanas todos los huéspedes reciben pre-arrival info

Después que CC termine pipeline actual (thread/115 + Pre-stay A1-A4):

| Orden | Block | Driver objetivo | Razón |
|---|---|---|---|
| 1 | **Pre-stay MVP A1-A4** (`cc-instructions-bot/2026-05-18-pre-stay-notifications-mvp.md`, migration 0035) | Obj 1 + 3 | Cubre objetivo 4-semanas; reusa Part E infra validada; spec ready |
| 2 | **P2.16 Karina onboarding final** — magic-link + walkthrough completo /admin/{inbox,bookings,extra-guests,airbnb-content} + drawer pre-stay post A4 | Obj 2 | 30-45min Alex+Karina; desbloquea handoff diario |
| 3 | **P2.20 Vectorize tail unblock** (CC-Data scope, paralelo) | Indirect (calidad bot) | 5min Alex + 2-3h CC-Data background; cierra Data Mining v2 |
| 4 | **P3-H FAQs curation 50-80** | Obj 1 (medio plazo) | Manual Alex+Karina ~4-6h; alimenta Greeter KB v2; bot responde más, Alex menos |
| 5 | **P3-A B.7 `/admin/leads` UI** (promovido a P2 conceptual) | Obj 2 | Sin esto, 13k+ rows seedados están ciegos. Karina expansion post-pre-stay |
| 6 | **P2.10 + P2.11 dedupe** (3 promo bookings + Alex 2 records) | Datapoint quality | Post-thread/115 follow-up. 2h Alex+CC manual |
| 7 | **P2.7 Rotar PAT + ADMIN_REFRESH_SECRET** | Security hygiene | 15min; "no urge" per Alex pero hacer cuando convenga |
| 8 | **P2.18 weekend_price RdM + cache expiry** | Revenue protect | 1h; Beds24 pricing inconsistencies |
| 9 | **P3-F V7 lifecycle decisión + spec** | Pre-req escalabilidad | Necesario antes de scaling bot a in-stay/post-stay |
| 10 | **P3-G Beds24 Reviews API** | Bot KB enrichment | Reviews enrichment para bot KB + site display |
| 11 | **P3-C ideas restantes** en orden valor/effort | Long-term value | I6 Upsell → I9 Drip → I7 Lost-booking → I8 VIP completion → I5 Review automation → I2 QR check-in → I10 Dynamic packaging → I15 Unit economics → I16 Cancellation → I17 Weather → I18 UGC → I19 Casa Chamán launch |

---

## 8 · Lecciones clave acumuladas

### Técnicas

- **Beds24 sync mode permanente**: `Prices & Availability` ONLY (NUNCA `Everything`)
- **AirBnB phone field**: en `phone`, no `mobile`. UI cap guest input = 16
- **Pet policy**: $300 MXN/mascota/**estancia** (NO per night), max 2
- **Channel mapping**: `apps/worker-bot/src/beds24-normalize.ts:91` referer→channel
- **Webhook activation**: ~mayo 2026. Pre-may bookings necesitan backfill via API (resuelto thread/103)
- **Beds24 messages**: `POST /v2/bookings/messages` FIRST OUTBOUND
- **Beds24 invoice items**: `POST /v2/bookings` con `invoiceItems` array FIRST WRITE
- **ManyChat send**: `api.manychat.com/fb/sending/sendContent` tag `ACCOUNT_UPDATE` fuera 24h
- **MESSENGER_OUTBOUND_ENABLED**: default-OFF, Alex canary mode

### Coordinación

- **DoIt template v3**: pre-flight auto-verifiable commands · placeholders `<USER_HOME>`/`<OWNER>`/`<EMAIL>` · absolute paths · additive-first then mutating · defaults explicit
- **CC autonomy 3-tier** `.claude/settings.json`: allow (tests, lint, build, read) · ask (deploy, push, merge, kv put, d1 migrations apply) · deny (force push, rm-rf, db delete)
- **Conservative defaults sprint**: opt-in flags, manual canary, halt-on-failure, smoke verify
- **CC spec gap protocol**: halt + report 4 options (A/B/C/D pattern), no auto-pick

### Diseño

- **Encapsulación per lifecycle**: bot pre-booking ≠ in-stay ≠ post-stay (V7 spec pendiente)
- **No LLM en money path**: deterministic for prices/discounts; LLM solo para prose summary
- **Visualizaciones admin**: refresh-based MVP, polling acceptable, real-time = Phase 2

---

## 9 · Métricas norte (cuando todo el backlog viva)

| Métrica | Hoy estimado | Target post-backlog |
|---|---|---|
| % touch-points pre-checkout sin Alex/Karina | ~40-50% | 90%+ |
| % touch-points in-stay sin Alex/Karina | ~5% | 70%+ |
| % bookings con upsell adicional | ~3-5% | 25-35% |
| Cotización → booking conversion rate | TBD baseline | +15-20 pts |
| Lost-booking recovery rate | 0% | 10-15% |
| Repeat guest rate | TBD baseline | +20-30% |
| Review request response rate | TBD baseline | 40%+ |
| Cancellation rate proactive intervention | 0% | Caso huracán: 80%+ catch |

---

## 10 · Cierre

Este doc es **fuente única de verdad** para el backlog completo. Si en una sesión futura no aparece un item aquí, lo perdimos.

**Cadence de revisión**: cada 14 días o post-sprint mayor (lo que ocurra primero). Si un item se completa, marcar tachado + commit; si se descubre nuevo, agregar al P2 o P3 correspondiente con effort + driver.

**Changelog**:

| Fecha | Editor | Cambios |
|---|---|---|
| 2026-05-18 morning | WC | Doc inicial creado |
| 2026-05-18 evening | WC (DoIt cleanup #1) | Sprint C+E+D+P2 canary validado movió 12 items a LIVE; removidos 11 P2 ya cerrados; agregados P2.20-P2.22; Guest 360 actualizado con row counts reales (13k+ seedados); Pre-stay effort revisado 12-16h → 35-50h con link a spec deep; sequencing §7 realineado a objetivos Alex (workload + Karina + 4 sem) |
| 2026-05-18 late evening | WC (DoIt cleanup #2 — CC feedback) | thread/115 shipped (PRs #98-100), migration 0034 ya aplicada en prod; spec pre-stay re-numerado migration 0034 → 0035; §4 actualizado con guests resync LIVE + mojibake fix + debug stats; §7 sequencing thread/115 removido (done), P2.10+P2.11 dedupe agregado como follow-up |

**Próximo paso sugerido**: ahora que pipeline CC actual está en queue (thread/115 + Pre-stay A1-A4), foco es **Pre-stay execution + Karina onboarding en paralelo**. Vectorize tail puede correr en background cuando Alex tenga 5 min para token creation.

---

— WC, last edit 2026-05-18 evening
