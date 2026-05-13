# INSTRUCCIÓN PARA CC — Review Guest 360 architecture + Phase B.1-B.8 plan

**From**: Alex (vía WC)
**To**: CC
**Status**: Read + comment + propose. **NO implementación** todavía.
**Output**: Commit `threads/34-cc-review-guest360-phaseb.md`
**Decision after**: Alex review tus comentarios + ajustamos plan antes de arrancar Phase B.1 post-observación

---

## Contexto

Esta tarde Alex y WC discutieron el flujo post-Phase 0 deployment. Resultado:
- Bot 100% automático (Opción 1 confirmada)
- Alex interviene cuando quiere, nunca requerido
- Single dashboard unificado para todo el guest lifecycle (leads + bookings + post-stay)
- Plan completo Guest 360 + Phase B.1-B.8 documentado

**Necesitamos tu review** antes de comprometernos a 2 meses de implementación. Tu opinión técnica importa: tú conoces el código actual mejor que nadie y vas a ser quien implemente.

---

## Threads a leer (en orden, 30-45 min total)

| # | Archivo | De qué trata |
|---|---|---|
| 1 | `threads/27-alex-decisions-cc-implementation-greenlight.md` | Decisiones Q1-Q17 originales |
| 2 | `threads/30-alex-approvals-cc-execution-plan.md` | Tracks A+B+C autorizados (ya implementaste) |
| 3 | `threads/31-cc-track-b-deploy-log.md` | Tu propio deploy log (revisa que esté correcto) |
| 4 | `threads/32-cc-track-c-reviews-carousel.md` | Tu propio carousel work (verifica) |
| 5 | **`threads/33-guest360-architecture-phase-b-plan.md`** | 🔴 **EL PLAN PRINCIPAL** — lee con cuidado |

---

## Lo que Alex confirmó esta tarde (Q18-Q34)

| Q | Decisión | Status |
|---|---|---|
| Q18 | Deploy worker after §3 tweaks | ✅ DONE (tu thread/31) |
| Q19 | Phase B Welcome auto-send concept | ✅ APPROVED |
| Q20 | ReviewsCarousel post-deploy | ✅ APPROVED |
| Q21 | apps/admin/leads AVANZAR a Sprint 2 | ✅ |
| Q22 | WhatsApp cubre hot alerts (no PWA push aún) | ✅ |
| Q23 | Backfill AirBnB inquiries últimos 30d | ✅ |
| Q24 | Booking.com defer (casi nula reservación) | ✅ |
| Q25 | Backend tablas separadas, UI unificada | ✅ |
| Q26 | Lifecycle stages + cancelled + no_show | ✅ |
| Q27 | guest_events desde día 1 | ✅ |
| Q28-Q34 | Open questions menores | 🟡 WC voto pero Alex no votó aún |

---

## Tu misión — 6 áreas de review

### 1. 🔴 D1 Schema (thread/33 §2) — el más crítico

Lee las 4 migrations propuestas: `0014_guests_master`, `0015_leads`, `0016_bookings`, `0017_guest_events`.

**Pregúntate:**
- ¿Los tipos están bien? (TEXT vs INTEGER vs JSON columns)
- ¿Los indexes cubren los queries reales del dashboard?
- ¿Falta algún campo crítico que vas a necesitar después?
- ¿`guest_events.payload_json` es la forma correcta para flexibilidad o prefieres event-specific columns?
- ¿`bookings.lead_id FOREIGN KEY` con NULL allow está bien para direct bookings?
- ¿La separación `guests.status_master` (computed) vs `leads.status` (specific) tiene sentido?
- ¿Los `idempotency_key` en events evitan double-logging realmente?
- ¿Performance OK con D1? D1 tiene límites (~10GB max database, ~50ms p99 reads). Estimar volumen.

**Si propones cambios al schema, comparte SQL diffs específicos.**

### 2. 🟡 Phase B.1 → B.8 sequencing (thread/33 §3)

Lee el plan de 8 sub-phases. ETAs totales ~80h CC work.

**Pregúntate:**
- ¿El orden tiene sentido? ¿Hay dependencies que faltan?
- ¿ETAs son realistas? (tú conoces tu velocidad mejor)
- ¿Algún phase tiene scope creep o se puede partir?
- ¿Phase B.4 (Dashboard UI, 24h) realista? Astro + React + D1 queries + Better Auth + mobile-first
- ¿Phase B.3 (Backfill scripts) tiene riesgos no obvios? (e.g. dedupe phone normalization)
- ¿Falta alguna Phase importante? (e.g. damage/cancellation handling, dispute mgmt)

### 3. 🟡 Migration strategy (thread/33 §5)

Migration desde estado actual:
- Make datastore `conversations` legacy → coexiste
- Beds24 `/bookings` → backfill 365d back + 365d forward
- D1 `bot_messages_inbox` → link a bookings via booking_id
- D1 `reviews` → link a bookings via room_id + reservation_code

**Pregúntate:**
- ¿Hay riesgo de data loss durante backfill?
- ¿Dedupe across channels (phone/email/manychat) es robusto?
- ¿Make datastore `conversations` debe migrarse a D1 ahora o defer Sprint 3?
- ¿Bot greeter sigue leyendo del datastore Make sin cambios? ¿Hay race conditions?

### 4. 🟡 Dashboard UI design (thread/33 §3 Phase B.4)

Inbox + Guest 360 detail + Pending welcomes approval.

**Pregúntate:**
- ¿`apps/admin` como nuevo Astro app, o submontaje de `apps/web`?
- ¿Better Auth gate suficiente o necesitas role-based (admin vs viewer)?
- ¿Polling 30s para real-time es OK o WebSocket vale la pena?
- ¿Mobile UX patterns (bottom sheets, swipe, infinite scroll) específicos a recomendar?
- ¿Component library (shadcn? raw Tailwind?)?
- ¿Performance: 1500+ bookings históricos, ¿paginación server-side o client?

### 5. 🟡 Cost & risk estimates (thread/33 §6)

WC listó risks pero quiero tu estimación realista:
- Costo Anthropic API mensual cuando Phase B.1+B.2 estén live (welcome + inquiry auto-respond + follow-ups)
- Costo Cloudflare (D1 storage, Worker invocations, R2)
- Costo Beds24 API (rate limits — tenemos ~432K/día, polling usa ~0.07%)
- Risk: ¿qué se rompe primero a escala? (e.g. 100 inquiries/día)

### 6. 🟢 Ideas adicionales — propuestas tuyas

Vectores que WC no exploró:
- **Smart features**: lead scoring ML simple? Sentiment analysis en mensajes? Auto-tag extraction?
- **Performance**: caching estratégico, CF Cache API, edge-rendered queries
- **DX (developer experience)**: testing infra (Playwright E2E?), staging env, feature flags
- **Operacional**: monitoring/observability (logs estructurados ya hay), error tracking (Sentry?)
- **Migration safety**: feature flags por phase, rollback procedures
- **AI/LLM optimization**: prompt caching strategy, fallback models (Haiku → Sonnet on complex)
- **Integration gaps**: ¿qué pasa con Booking.com inquiries entrantes mientras está "deferred"?

---

## Output format

Commit `threads/34-cc-review-guest360-phaseb.md` con esta estructura:

```markdown
# Thread 34 — CC review of Guest 360 + Phase B.1-B.8 plan

## 0. TL;DR
[Tu opinión general en 3-5 líneas]

## 1. D1 Schema review
### 1.1 0014_guests_master
[OK / changes proposed con SQL diff]
### 1.2 0015_leads
### 1.3 0016_bookings
### 1.4 0017_guest_events

## 2. Phase B sequencing review
[¿Orden OK? ¿ETAs realistas?]

## 3. Migration strategy review
[Risks, dedupe robustness]

## 4. Dashboard UI design review
[Architecture choice + recommendations]

## 5. Cost & risk estimates
[Numbers concretos]

## 6. Additional proposals
[Ideas tuyas]

## 7. Open questions for Alex
[Si surge algo no decidido]

## 8. Estimated revised ETA
[Si cambia algo del plan]
```

---

## Reglas

- ✅ **Lee thread/33 completo** — es el plan
- ✅ **Cuestiona supuestos WC** — soy generalista, tú conoces el código
- ✅ **Data > opinión** — si propones cambios, justifica con ejemplos concretos
- ✅ **Sé honesto con ETAs** — si crees que algo es 40h en vez de 24h, dilo
- ✅ **Propón mejoras** — no solo critique, también ideas
- ✅ **Identifica blind spots** — qué se le escapó a WC

- 🔴 **NO implementar nada** todavía — solo review
- 🔴 **NO empezar Phase B.1** — esperamos Phase A observation week + Alex approval post-review tuya
- 🔴 **NO tocar production** — bot está delicado post-credit-reload

---

## Phase A observation status

Bot está corriendo (post-credit-reload + 4 replays exitosos):
- Phase 0 + Client Bot A worker DEPLOYED hoy (commit `f754d67`)
- D1 ingesta funcionando (167 reviews + 48 messages)
- GH Actions crons PENDING (Alex needs to rotate secret + decide branch)

Mientras Alex está observando Phase A en la semana, tu output thread/34 nos ayuda a ajustar plan ANTES de comprometernos a 80h de implementación.

---

## Timeline esperado

| When | Owner | Action |
|---|---|---|
| Now → +24h | CC | Lee + escribe thread/34 (~2-3h work) |
| +24h → +48h | Alex + WC | Review thread/34, decidimos ajustes |
| +1 week | Alex | Approves final Phase B.1 plan post-Phase A observation |
| +1 week | CC | Arranca Phase B.1 con plan refinado |

---

## Limitaciones que ya conoces (no las repitas, asume estos están)

- AirBnB API NO permite Special Offer programático (manual desde panel)
- Beds24 hard-delete NO dispara webhook (polling delta required)
- Reviews API cap 50 sin pagination (estrategia híbrida bulk CSV + cron delta)
- ManyChat SendFlow puede fallar si subscriber bloqueó bot
- Quiet hours 22:00-08:00 Acapulco UTC-6 sin DST (urgent keywords bypass)
- ADMIN_REFRESH_SECRET rotado hoy worker-side, pending GH Actions

---

## Si surge algo bloqueante mid-review

Si encuentras un blocker técnico mientras revisas (e.g. "D1 no soporta X feature que requerimos"), commit thread/34 parcial con flag 🚧 y avísale a Alex via WhatsApp directo o WC en chat next session.

---

*ETA total para CC: 2-3 horas (read + analyze + write). No hay rush — Phase A observation va paralelo. Output thread/34 cuando termines, Alex revisa cuando vuelva a su laptop.*

— Web Claude, 2026-05-12, vía Alex
