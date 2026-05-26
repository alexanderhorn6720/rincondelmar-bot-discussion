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
| Vectorize index `rdm-conversations-v2` — 16,969 vectors live, bge-m3 1024d cosine (Data Mining v2 closure 2026-05-18) | LIVE (no bot consumption yet — wire futuro PR) |
| Pre-stay foundation A1 + A1.5 — migrations 0035 + 0036, 32 templates (4 props × 2 langs × 4 touchpoints incl T-14), pre-stay.ts skeleton, 33 invariants tests (PRs #102 + #103) | LIVE — Alex approved tone shift round 2 (warmer host persona) |
| Pre-stay A2 — scanForWelcome implementation, bypassed welcome-auto-send.ts, admin scan endpoint (PR #104) | LIVE behind `MESSENGER_OUTBOUND_ENABLED` flag (default OFF) |
| Pre-stay A3 — scanForT14 + scanForT7 + scanForT1 + cron heartbeats + 4 GH Actions workflows (welcome 30min, T-14/T-7/T-1 daily) (PR #105) | LIVE behind same flag |

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
| thread/115 guests.name resync from Beds24 (PR #98 + mojibake fix #99 + debug stats #100 + chunked invocations #101) | 2-3h CC | ✅ Shipped — migration 0034 applied |
| **Pre-stay A1 + A1.5** (PRs #102 + #103) — migrations 0035 + 0036, 32 templates, skeleton, 33 tests, Alex approved tone | 8-12h CC + iteration | ✅ Shipped 2026-05-18 |
| **Pre-stay A2** (PR #104) — scanForWelcome + bypass welcome-auto-send + admin scan endpoint + 426 lines tests | 8-12h CC | ✅ Shipped 2026-05-18 |
| **Pre-stay A3** (PR #105) — scanForT14 + T7 + T1 + cron heartbeats + 4 GH workflows + scan-touchpoints tests | 8-12h CC | ✅ Shipped 2026-05-18 |
| **Pre-stay A4** — sendPreStay manual fire + runCatchUp `[now, now+14]` + admin endpoints + drawer 4-buttons + `/admin/pre-stay` page + catch-up UI | 10-14h CC | 🟡 In-flight (started 2026-05-18 night) |
| **Pre-stay A5** — Bulk approve 7 unapproved AirBnB content drafts + Chrome MCP write-back to 8 live listings (Alex approved bulk-flip 2026-05-18 night) | 6-10h CC | 🟡 Queued post-A4 |

Total CC autónomo pipeline pendiente: **~16-24h** (A4 in-flight + A5 queued).

Pending de Alex (post-A4 canary):
- Pre-stay A4 review when CC ships
- Chrome MCP auth verify pre-A5 (1-time setup if needed)
- Catch-up trigger post-A4 (Karina supervising)
- Spot-check A5 deployed listings vs R2 drafts

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
| Latest D1 migration | 0036 (pre_arrival_t14_sent_at, PR #103). Next pre-stay-related = 0037 if needed |

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
| ~~P2.20~~ | ~~**Vectorize tail unblock**~~ ✅ **Cerrado 2026-05-18 evening** — Index `rdm-conversations-v2` live con **16,969 vectors** (dimensions=1024, metric=cosine, model=`@cf/baai/bge-m3`). Coverage 99.99%. Gap de 2 vectors (nuevas conversaciones post 2026-05-16 17:49Z) marcado acceptable per Alex "95% ok". Data Mining v2 sprint formalmente cerrado. Wire al Greeter v6+ pendiente como future PR (no urgente, bot funciona sin él). | — | — |
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

**Status 2026-05-18 evening**: ✅ **A1 + A1.5 shipped** (PRs #102 + #103). Migrations 0035 + 0036 live. 32 templates approved by Alex (warmer host tone, round 2). A2-A4 queued for CC-Bot.

**Scope evolution**: spec original = welcome + T-7 + T-1 (3 touchpoints). Alex review mid-A1 surfaced ops reality requiring **T-14 (2 weeks pre-arrival)** for: Las Morenas chef opt-in deadline, RdM/Combinada chef Celene WhatsApp handoff, all-but-Huerta guest count confirmation. Final scope = **4 touchpoints, 32 templates**.

**Effort revisado**: A1 = 8-12h shipped, A1.5 = ~2-3h iteration shipped. Remaining A2-A4 = ~26-38h CC.

| Component | Stack | Status |
|---|---|---|
| Schema (5 cols + index) | Migrations 0035 + 0036 | ✅ Applied to prod D1 |
| 32 templates (4 props × 2 langs × 4 touchpoints) | Hardcoded TS module, host persona tone | ✅ Shipped + Alex approved |
| pre-stay.ts skeleton + Touchpoint type | TypeScript types `welcome \| t14 \| t7 \| t1` | ✅ Shipped |
| Tests (33 invariants) | Casa Chamán never appears, chef phones only in T-14, etc. | ✅ Shipped 663/663 pass |
| `scanForWelcome` + sender wire | Replace/wrap welcome-auto-send (design decision pending CC) | 🟡 PR A2 queued |
| `scanForT14` + `scanForT7` + `scanForT1` | Worker cron + GHA workflows | 🟡 PR A3 queued |
| Channel routing | Re-use `resolveRoute()` from messenger-send.ts | ✅ Infra ready |
| Idempotency | 5 columns en beds24_bookings (migrations 0035 + 0036) | ✅ Shipped |
| Catch-up endpoint (4 touchpoints) | Rate-limited admin endpoint | 🟡 PR A4 spec'd |
| Admin override drawer | Per-row buttons in /admin/bookings | 🟡 PR A4 spec'd |
| Feature flag gate | `MESSENGER_OUTBOUND_ENABLED` (re-use Part E) | ✅ Validated 2026-05-18 |
| Audit | `messenger_outbound` table (re-use Part E) | ✅ Live |

**Per-property facts locked** (CC memory + tests):

| Property | Cap | Chef | Chef phone (T-14 only) | Encargada arrival |
|---|---|---|---|---|
| RdM (78695) | 30 | Celene INCLUDED | +52 744 771 3839 | Karina |
| Morenas (74322 + 374482) | 30 | Karina OPCIONAL | +52 744 144 1575 | Karina |
| Combinada (74316) | **60** (2× 30) | Celene INCLUDED | +52 744 771 3839 | Karina |
| Huerta (637063) | 12 | NO chef | — | Karina |

Casa Chamán (679176) NEVER appears — invariant test-locked.

**Universe**: 19 bookings activos próximas 4 semanas (verificado D1 prod 2026-05-18). Tractable.

**Out of scope v1** (deferred): T-3 chef menu request (subsumed in T-14 handoff), T-0 day-of, in-stay touchpoints (Client Bot Phase A separate), reply handling (/admin/inbox handles), email channel (Alex: no), LLM personalization (v2), Casa Chamán (Q3).

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
| 3 | **P3-H FAQs curation 50-80** | Obj 1 (medio plazo) | Manual Alex+Karina ~4-6h; alimenta Greeter KB v2; bot responde más, Alex menos |
| 4 | **P3-A B.7 `/admin/leads` UI** (promovido a P2 conceptual) | Obj 2 | Sin esto, 13k+ rows seedados están ciegos. Karina expansion post-pre-stay |
| 5 | **P2.10 + P2.11 dedupe** (3 promo bookings + Alex 2 records) | Datapoint quality | Post-thread/115 follow-up. 2h Alex+CC manual |
| 6 | **P2.7 Rotar PAT + ADMIN_REFRESH_SECRET** | Security hygiene | 15min; "no urge" per Alex pero hacer cuando convenga |
| 7 | **P2.18 weekend_price RdM + cache expiry** | Revenue protect | 1h; Beds24 pricing inconsistencies |
| 8 | **P3-F V7 lifecycle decisión + spec** | Pre-req escalabilidad | Necesario antes de scaling bot a in-stay/post-stay |
| 9 | **P3-G Beds24 Reviews API runtime wire** | Bot KB enrichment | Reviews enrichment para bot KB + site display (ingestion ya LIVE) |
| 10 | **Vectorize wire to Greeter v7+** — consume `rdm-conversations-v2` index (16,969 vectors live) en similarity retrieval | Bot KB enrichment | Future PR; bot funciona sin él, unlocks 11 años WA history retrieval |
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
| 2026-05-18 night | WC (Vectorize closure) | CC-Data confirmó index `rdm-conversations-v2` live con 16,969 vectors / 99.99% coverage. Tail cerrado, gap de 2 vectors acceptable. §4 LIVE add Vectorize index. P2.20 marked done. §7 sequencing renumerado (Vectorize row removed) + agregada "Vectorize wire to Greeter v7+" como future-PR item. Spec pre-stay Appendix A actualizado. |
| 2026-05-18 night #2 | WC (Pre-stay A1+A1.5 shipped) | CC-Bot shipped PRs #102 (A1 baseline) + #103 (A1.5 iteration after Alex review). Migrations 0035 + 0036 applied. Scope grew 3 → 4 touchpoints (added T-14 chef handoff + extra-guests confirmation). 32 templates total, warmer host tone "anfitrión 9 años". Per-property facts locked: Combinada cap 60 (was 30 wrong in spec), Karina = universal encargada all properties, chef phones only in T-14. §4 LIVE updated, latest migration → 0036, §6.2 Pre-stay full component table rewritten. A2-A4 remaining ~26-38h. |
| 2026-05-18 night #3 | WC (A2+A3 shipped, A5 new) | CC-Bot shipped PR #104 (A2 scanForWelcome bypassing welcome-auto-send) + #105 (A3 scanForT14+T7+T1 + crons). Two scope deviations from spec — both right per WC review thread/121. A4 in-flight. New A5 task added: bulk approve 7 unapproved AirBnB content drafts + Chrome MCP write-back to 8 live listings (Alex approved bulk-flip ciego 2026-05-18 night). Pipeline pendiente ~16-24h (A4 + A5). |

**Próximo paso sugerido**: ahora que pipeline CC actual está en queue (thread/115 + Pre-stay A1-A4), foco es **Pre-stay execution + Karina onboarding en paralelo**. Vectorize tail puede correr en background cuando Alex tenga 5 min para token creation.

---

— WC, last edit 2026-05-18 evening
