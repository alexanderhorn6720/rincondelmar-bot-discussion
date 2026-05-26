---
id: 213
author: wc
topic: m1-pricing-v0.5-port-make-to-cf
status: draft
mode: brain_deep
priority: P2
target_repo: rdm-bot
target_branch: feat/m1-pricing-v05-cf-port
model: sonnet-4-6
effort_estimate_h: 8-12
created_at: 2026-05-26
based_on: Make scenario "cron:pricing-daily" (scenarioId 4718358) blueprint
supersedes: modules/pricing/README.md (rdm-platform) conceptual sketch
---

# thread/213 — M1 Pricing v0.5: Port Make Scenario to Cloudflare

## §0 · TL;DR para Alex (mobile-friendly)

| Item | Resumen |
|---|---|
| **Genealogía** | Port del Make scenario `cron:pricing-daily` (4718358) al worker-pago cron CF. ~95% reuso lógica probada |
| **Diferencias vs Make actual** | Floor Morenas $3500→$4000 (tu mental), channel asymmetry minStay, premium SEP completo, audit en D1 rincon (no Make datastore), JSON config en /admin |
| **Workflow preservado** | Email diario → APPROVE/REJECT botones → webhook applies a Beds24. Identical UX al actual |
| **Anti-pattern caveat** | El LLM (Sonnet) decide precios. Anti-pattern WC-Plat dice "NO LLM en money". **Mitigation**: hard validator post-LLM (multiples 250, floor/ceiling, max ±20% change, etc) — ya existe en Make, port |
| **Effort CC** | 8-12h en 1 mega-run, Sonnet 4.6 |
| **Branch** | `feat/m1-pricing-v05-cf-port` |
| **Activation** | Default OFF (`pricing_auto_run=false` en bot_config). Alex activa cuando smoke OK |
| **Rollback** | Instant via `UPDATE bot_config SET pricing_auto_run='false'` |

---

## §1 · CONTEXT

### 1.1 Estado actual del pricing operacional

- Make scenario `cron:pricing-daily` (4718358) PAUSED desde ~2026-05-06
- Beds24 prices y minStay **estáticos hace 3 semanas**
- 81 bookings nuevos en 60 días — demanda activa pero pricing no se adapta
- Tu workflow histórico: scenario corre 06:00 UTC daily → email con cambios → tú clickeas APPROVE → webhook applies a Beds24

### 1.2 Por qué portar a Cloudflare

- Migración a CF es prioritaria (ADR-001). Pricing en Make es deuda técnica
- Worker-pago YA tiene crons activos (`nodejs_compat_v2`, Workers Paid plan)
- Beds24 auth + token refresh ya hookeable en worker-pago
- D1 `rincon` ya tiene `audit_log`, `bot_config`, `pricing_proposals` no existe pero schema trivial
- Email via Resend (`email.rincondelmar.club`) ya configurado
- Eliminamos dependencia Make subscription para pricing (Make sigue activo para otros scenarios por ahora)

### 1.3 Qué tan bueno es el Make scenario actual (audit)

**Veredicto: muy bueno**. Audit completo de blueprint (`Make:scenarios_get` 4718358):

**Lo excelente (preservar):**

| Aspecto | Detalle |
|---|---|
| Hard rules en system prompt | 10 rules explícitas (multiples de 250, floor/ceiling, no premium, no past dates, Saturday minStay=4) |
| MinStay logic matrix | Property × season × horizon table en prompt |
| Anti-orphan rules diferenciado | gap_length 1N→noCheckIn, 2-3N→base, 4N+→bump primer día |
| Discount curve | 5 breakpoints (-5%/-10%/-15%/-20%/-25%) por horizon `<45/30/14/7/3d` |
| Combinada nunca discount | Hard-coded en prompt + validator |
| Premium seasons hard exclude | Christmas/HolyWeek/Sept15 hard skip |
| **Hard validator post-LLM** | Math sanity, floor/ceiling check, no past dates, no booked days, max ±20% change, auto-correct prices a múltiplo 250 |
| Two-step approval | email APPROVE/REJECT links → webhook → solo entonces Beds24 PATCH. 24h expiry, token único per proposal |
| Audit trail | `pricing_proposals` datastore con `status=pending`, `expires_at`, `deltas_json` |
| Email detallado | Executive summary + 6 sub-secciones reasoning + tabla cambios + tabla financial monthly |

**Los gaps a mejorar en v0.5:**

| Gap | Severidad | Fix v0.5 |
|---|---|---|
| Floor Morenas $3500 (Alex mental floor es $4000) | Media | Update constant a 4000 |
| Premium seasons incompleta (falta verano SEP, semana santa larga) | Media | Extender list, derivar SEP calendar |
| No channel asymmetry (AirBnB minStay = direct) | Baja | Añadir +1 minStay para AirBnB room_id 74322 |
| Ceiling Combinada $60k pero histórico max $20k | Baja | Reducir a $30k (más realista) |
| 40% error rate histórico (10/25 runs) | Alta operacional | Diagnosticar antes de port: probable Beds24 token expired (`cron:beds24-token-refresh` también paused) |

### 1.4 Validación contra histórico (CSV bookings 2019-2027)

Verificado contra `Bookings_historicos.csv` (1501 rows, 942 confirmados):

| Validation | Resultado | Implicación spec |
|---|---|---|
| Premium season Dec 23-Jan 2 | ADR $24-33k/N vs $11k baseline RdM. 2-3x premium 4 años | **Confirmar**: hard skip discount en este window |
| Premium season HolyWeek (Apr) | ADR avg $8.4k Apr — moderado, NO premium fuerte | **Considerar**: solo Easter weekend, no toda Sem Santa |
| Premium summer (Jul-Aug) | ADR Jul $9.2k, Aug $8.9k vs baseline $7-8k. Premium ligero | **Considerar**: minStay +1 en Jul-Aug, no skip discount |
| Floor RdM histórico | Min $3k (cancelados raros), p10 $5k, median $9.3k | Floor $5k correcto |
| Floor Morenas histórico | Min $4k cancelados, p10 $4.5k, median $5.9k | **Floor $4k justified** (no $3.5k) |
| Ceiling Combinada histórico | Max $20k, median $17.7k | Ceiling $30k generous, $60k inflated |
| Channel mix | AirBnB 64%, Pagina 31%, Direct 25% | Channel asymmetry valuable (premiar direct) |

### 1.5 Hallazgos críticos del Make blueprint

1. **El LLM SÍ decide precios** — anti-pattern WC-Plat. Pero el validator post-LLM atrapa el 95% de halucinaciones (multiples 250, floor/ceiling, max ±20%). En la práctica funciona.
2. **No hay kill-switch reversible**. Si scenario corre con bug, no hay flag interno. Solo "deactivate scenario" en Make UI.
3. **APPROVE/REJECT tokens expiran en 24h** — bueno (no se aplica accidentalmente cambio de hace 5 días).
4. **Email es HTML standalone** — no requiere infra extra, solo Resend.
5. **El system prompt es 95% transferible** — no requiere rewrite, solo update floors/seasons.

---

## §2 · SCOPE — YES/NO explícito

### YES — Sí se hace en este mega-run

- ✅ Crear `apps/worker-pago/src/pricing-engine.ts` con port de la logic Make
- ✅ Crear `apps/worker-pago/src/pricing-validator.ts` con port del validator Make
- ✅ Crear `apps/worker-pago/src/pricing-email.ts` con port del email HTML builder
- ✅ Crear `apps/worker-pago/src/pricing-config.ts` con constants (floors, ceilings, premium seasons)
- ✅ Migration D1 `pricing_proposals` table en `rincon` database
- ✅ Cron entry en worker-pago `wrangler.toml` (06:00 UTC daily)
- ✅ Endpoints `/api/pricing/approve/:token` y `/api/pricing/reject/:token` en worker-pago
- ✅ Bug fix: Beds24 token refresh — verify token NOT expired antes de cron run
- ✅ Update floor Morenas $3500→$4000
- ✅ Premium seasons extendidas (Dec 22-Jan 5, HolyWeek window, Sept 15-16, Jul 15-Aug 15)
- ✅ Channel asymmetry: AirBnB room 74322 minStay = direct 374482 minStay + 1
- ✅ Bot_config keys: `pricing_auto_run`, `pricing_dry_run`, `pricing_disabled_rooms`
- ✅ Admin endpoint `/api/admin/pricing/config` GET+POST (JSON editor de config)
- ✅ Admin page `/admin/pricing` mostrando últimas 30 proposals + status + JSON config editor
- ✅ Telegram alert si run falla (reusar `TG_BOT_TOKEN` existente)
- ✅ Tests anti-regression (golden cases del Make actual)
- ✅ Smoke test endpoint: `/api/admin/pricing/dry-run` (corre con `dry_run=true`, NO escribe Beds24)

### NO — Fuera de scope

- ❌ Eliminar Make scenario `cron:pricing-daily` — queda como fallback paused
- ❌ Demand signal driver (Phase 2, post-F1 events bus)
- ❌ Booking.com pricing (out of scope v0.5)
- ❌ Tour 360° pricing
- ❌ Casa Chamán pricing (Q3 2026, NO surfacar)
- ❌ Multi-bot owner pricing (single RdM owner)
- ❌ Refactor del Make scenario (lo dejamos paused funcional)
- ❌ Migration de Make datastore `pricing_proposals` (history Make no se migra)
- ❌ AUTO-APPLY threshold (<5% changes auto-apply). **POSTPONE para v0.6** — preservamos workflow APPROVE manual
- ❌ Premium events ad-hoc (Tianguis Turístico, conciertos Foro Acapulco) — manual override Alex via /admin
- ❌ ALTER TABLE en cualquier tabla existente
- ❌ Auto-merge a main

---

## §3 · DECISIONES CERRADAS (Alex votos)

| # | Decisión | Voto Alex |
|---|---|---|
| 1 | Port to Cloudflare worker-pago (no nuevo worker dedicado) | GO |
| 2 | Workflow preservado: email APPROVE/REJECT → webhook → Beds24 | GO |
| 3 | Default OFF inicial: `pricing_auto_run=false`, Alex enable manual | GO |
| 4 | Floor Morenas $4000 (no $3500 Make actual) | GO |
| 5 | Ceiling = floor + Math.max(historic max × 1.3, current_price × 1.3) — derive from CSV | GO |
| 6 | Base minStay floor universal = 2 noches (NUNCA 1N por costo limpieza) | GO |
| 7 | Premium seasons: SEP vacaciones oficiales 2026-2027 + Christmas + HolyWeek weekend | GO |
| 8 | Discount curve igual a Make (step function -5%/-10%/-15%/-20%/-25%) | GO |
| 9 | Channel asymmetry: AirBnB room_id 74322 minStay = direct +1 | GO |
| 10 | JSON config en `/admin/pricing` textarea (Alex edita JSON directo) | GO |
| 11 | Audit en D1 `pricing_proposals` table (no Make datastore) | GO |
| 12 | Telegram alerts reuse `TG_BOT_TOKEN` + `TG_CHAT_ID_PAGOS` | GO |
| 13 | Modelo: Sonnet 4.5 (mismo que Make actual) | GO |
| 14 | Token approval expira 24h | GO |
| 15 | Hard validator: copy 100% del Make existente | GO |

---

## §4 · IMPLEMENTACIÓN

### 4.1 Sub-deliverables (11 items, ordenados de simple a complejo)

| # | Componente | Files | Effort |
|---|---|---|---|
| P1 | `pricing-config.ts` — floors, ceilings, premium seasons, channel asymmetry, room metadata | `apps/worker-pago/src/pricing-config.ts` | 30 min |
| P2 | Migration D1 `pricing_proposals` table | `apps/web/migrations/0049_pricing_proposals.sql` | 30 min |
| P3 | `pricing-validator.ts` — port del ExecuteCode `id:8` del Make | `apps/worker-pago/src/pricing-validator.ts` | 1.5h |
| P4 | `pricing-engine.ts` — port del ExecuteCode `id:6` + system prompt + Anthropic call | `apps/worker-pago/src/pricing-engine.ts` | 2h |
| P5 | `pricing-email.ts` — port del HTML builder con buttons APPROVE/REJECT | `apps/worker-pago/src/pricing-email.ts` | 1h |
| P6 | Cron handler `cron:pricing-daily` en worker-pago | `apps/worker-pago/src/pricing-cron.ts` + `wrangler.toml` | 1h |
| P7 | Endpoints `/api/pricing/approve/:token` + `/reject/:token` | `apps/worker-pago/src/pricing-webhooks.ts` | 1h |
| P8 | Admin endpoint `/api/admin/pricing/config` (GET/POST JSON config) | `apps/worker-pago/src/admin-pricing.ts` | 30 min |
| P9 | Admin page `/admin/pricing` (proposals list + JSON config editor) | `apps/web/src/pages/admin/pricing.astro` + React component | 1.5h |
| P10 | Tests anti-regression (golden cases) | `apps/worker-pago/tests/pricing-*.test.ts` | 1h |
| P11 | Smoke endpoint `/api/admin/pricing/dry-run` | en P6/P7 files | 30 min |
| **TOTAL** | | | **~11h** |

### 4.2 D1 Schema (P2)

```sql
-- migration 0049_pricing_proposals.sql
CREATE TABLE pricing_proposals (
  token TEXT PRIMARY KEY,                  -- e.g. "2026-05-26-a3b7c1d2"
  created_at TEXT NOT NULL,                -- ISO timestamp UTC
  expires_at TEXT NOT NULL,                -- ISO +24h
  status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | expired | applied | failed
  
  -- Inputs snapshot (for audit + reproducibility)
  bookings_count INTEGER,
  rooms_count INTEGER,
  
  -- LLM response
  total_proposed INTEGER,                  -- changes proposed by LLM
  valid_count INTEGER,                     -- passed validator
  invalid_count INTEGER,                   -- rejected by validator
  warnings_count INTEGER,
  auto_corrected_count INTEGER,
  
  -- Deltas
  deltas_json TEXT NOT NULL,               -- {changes:[...], beds24_payload:[...]}
  summary TEXT,
  email_subject TEXT,
  email_html TEXT,                         -- copy for audit (compressed in real)
  
  -- Applied
  approved_at TEXT,
  applied_at TEXT,
  beds24_response_status INTEGER,
  beds24_response_body TEXT,
  apply_error TEXT,
  
  -- Run metadata
  run_dry BOOLEAN DEFAULT 0,
  run_error TEXT,                          -- if scenario crashed mid-run
  llm_tokens_input INTEGER,
  llm_tokens_output INTEGER,
  llm_cost_usd REAL                        -- estimate
);

CREATE INDEX idx_pricing_proposals_created ON pricing_proposals(created_at DESC);
CREATE INDEX idx_pricing_proposals_status ON pricing_proposals(status, created_at DESC);
CREATE INDEX idx_pricing_proposals_token ON pricing_proposals(token);
```

### 4.3 Config constants (P1) — Single source of truth

```typescript
// apps/worker-pago/src/pricing-config.ts

export const ROOM_METADATA = {
  78695:  { name: 'Rincon del Mar',          slug: 'rdm',      capacity: 30, base_price_extra: 300, channel: 'multi' },
  374482: { name: 'Las Morenas (direct)',    slug: 'morenas',  capacity: 30, base_price_extra: 300, channel: 'direct' },
  74322:  { name: 'Las Morenas (Airbnb)',    slug: 'morenas',  capacity: 30, base_price_extra: 300, channel: 'airbnb' },
  74316:  { name: 'Combinada (RdM+Morenas)', slug: 'combinada', capacity: 60, base_price_extra: 300, channel: 'multi' },
  637063: { name: 'Huerta Cocotera',         slug: 'huerta',   capacity: 12, base_price_extra: 200, channel: 'multi' },
} as const;

export const ROOM_LIMITS = {
  78695:  { floor: 5000,  ceiling: 40000 },
  374482: { floor: 4000,  ceiling: 25000 },  // UPDATED $3500 → $4000 (Alex mental floor)
  74322:  { floor: 4000,  ceiling: 25000 },  // same as direct
  74316:  { floor: 11000, ceiling: 30000 },  // UPDATED $60k → $30k (historic max ~$20k × 1.3)
  637063: { floor: 1500,  ceiling: 6000 },
} as const;

// Min stays — base por property (FLOOR UNIVERSAL = 2)
export const BASE_MIN_STAY = {
  78695:  2,  // RdM
  374482: 2,  // Morenas direct
  74322:  2,  // Morenas AirBnB
  74316:  3,  // Combinada (bigger group)
  637063: 2,  // Huerta
} as const;

// Saturday rule HARD
export const SATURDAY_MIN_STAY = 4;

// Channel asymmetry: AirBnB room_id 74322 minStay = direct room_id 374482 minStay + DELTA
export const AIRBNB_MINSTAY_DELTA = 1;

// Discount curve (step function, port del Make)
export const DISCOUNT_CURVE = [
  { max_days: 3,  pct: -25 },
  { max_days: 7,  pct: -20 },
  { max_days: 14, pct: -15 },
  { max_days: 30, pct: -10 },
  { max_days: 45, pct: -5  },
] as const;

// Premium seasons (NO discount, NO touch automated)
// Format: month-day ranges. Year-agnostic.
export const PREMIUM_SEASONS_FIXED = [
  // Christmas + New Year
  { name: 'Christmas', from: '12-22', to: '01-05', minStay: 4 },
  
  // Independencia
  { name: 'Sept15-16', from: '09-13', to: '09-17', minStay: 3 },
  
  // Día de muertos (small premium)
  { name: 'Muertos', from: '10-31', to: '11-03', minStay: 3 },
] as const;

// Premium seasons SEP-derived (require yearly update)
// Format: ISO dates exact. Need to update annually.
export const PREMIUM_SEASONS_DATED = [
  // Holy Week 2026 (Jueves Santo Apr 2 - Domingo Resurrección Apr 5)
  { name: 'HolyWeek-2026', from: '2026-03-30', to: '2026-04-12', minStay: 3 },
  
  // Summer vacation SEP 2026 (Jul 15 - Aug 23)
  { name: 'Summer-2026', from: '2026-07-15', to: '2026-08-23', minStay: 3 },
  
  // Winter vacation SEP 2026-2027 (Dec 21 - Jan 8)
  { name: 'Winter-2026-27', from: '2026-12-21', to: '2027-01-08', minStay: 4 },
  
  // Holy Week 2027 (estimated Mar 29 - Apr 11 — verify yearly)
  { name: 'HolyWeek-2027-est', from: '2027-03-29', to: '2027-04-11', minStay: 3 },
] as const;

// Max % change per run (hard guardrail)
export const MAX_CHANGE_PCT = 20;

// Round prices to multiples of
export const PRICE_ROUNDING = 250;

// Token expiry
export const PROPOSAL_EXPIRY_HOURS = 24;
```

### 4.4 System prompt (P4) — Port + updates

System prompt = **95% del Make scenario actual**, con cambios:
- Floor Morenas $3500 → $4000
- Premium seasons table actualizado con SEP vacaciones completas
- Sección nueva "CHANNEL ASYMMETRY": AirBnB 74322 minStay = direct 374482 minStay + 1
- Hard rule: minStay siempre >= 2 (universal floor)

```typescript
// Excerpt of system prompt v0.5 — diferencias vs Make
const SYSTEM_PROMPT_V05 = `You are the pricing agent for Rincon del Mar (4 vacation rental properties in Acapulco, Mexico).

PRIMARY OBJECTIVE: Maximize occupancy by avoiding orphan nights via dynamic minStay AND last-minute discounts.

PROPERTIES:
- 78695  Rincon del Mar (RdM)          cap 30, high baseline
- 374482 Las Morenas (direct booking)  cap 30, mid baseline
- 74322  Las Morenas (Airbnb listing)  cap 30, minStay = direct + 1 (channel asymmetry)
- 74316  Combinada (RdM+Morenas)       cap 60, linked: blocks 78695+374482. NO discounts.
- 637063 Huerta Cocotera               cap 12, opened Dec 2025

HARD RULES:
1. minStay only {2, 3, 4} — NEVER 1 (cleaning cost floor)
2. Override only null or "noCheckIn" (NEVER "blackout")
3. Prices MUST be multiples of 250
4. Max +/-20% price change vs current per run
5. NEVER touch dates with bookings (numAvail=0)
6. NEVER touch premium seasons
7. Floor by roomId: 78695=5000, 374482=4000, 74322=4000, 74316=11000, 637063=1500
8. Ceiling by roomId: 78695=40000, 374482=25000, 74322=25000, 74316=30000, 637063=6000
9. Saturday always minStay=4
10. Channel asymmetry: 74322 (AirBnB) minStay = 374482 (direct) minStay + 1

PREMIUM SEASONS (NO discount, NO touch automated):
- Christmas + NewYear: Dec 22 to Jan 5 (always minStay=4)
- HolyWeek 2026: Mar 30 - Apr 12 (minStay=3)
- Summer SEP 2026: Jul 15 - Aug 23 (minStay=3)
- Winter SEP 2026-27: Dec 21 - Jan 8 (minStay=4)
- Sept 15-16 Independencia: Sep 13-17 (minStay=3)
- Muertos: Oct 31 - Nov 3 (minStay=3)

MIN-STAY LOGIC BY HORIZON x PROPERTY x SEASON:
[same matrix as Make actual]

ANTI-ORPHAN LOGIC (1-4m and <1m only):
[same as Make actual]

LAST-MINUTE DISCOUNTS:
[same as Make actual]

OUTPUT JSON: [same schema as Make actual]
`;
```

### 4.5 Validator (P3) — Port 1:1 del Make

El validator del Make ya es muy bueno. Port 100%:

```typescript
// apps/worker-pago/src/pricing-validator.ts
import { ROOM_LIMITS, PRICE_ROUNDING, MAX_CHANGE_PCT } from './pricing-config';

export interface ValidationResult {
  valid: PriceChange[];
  invalid: { change: PriceChange; errors: string[] }[];
  auto_corrected: { roomId: number; date: string; from: number; to: number }[];
  beds24_payload: Beds24CalendarUpdate[];
}

export function validatePriceChanges(
  parsed: LLMResponse,
  calendar_data: Beds24Calendar,
  today: string
): ValidationResult {
  // Port exacto del ExecuteCode id:8 del Make
  // Mantiene:
  // - Multiples 250 check + auto-correct
  // - Floor/ceiling check
  // - No past dates
  // - No booked days (numAvail=0)
  // - No blackout days
  // - Max ±20% change check
  // - "no-op" detection (change does not modify anything)
  // ...
}
```

### 4.6 Cron + worker-pago wrangler.toml (P6)

```toml
# apps/worker-pago/wrangler.toml — añadir:

[triggers]
crons = [
  # ... existing crons ...
  "0 12 * * *"  # 06:00 MX (UTC-6) = 12:00 UTC. Daily pricing run.
]
```

### 4.7 Approve/Reject webhooks (P7)

```typescript
// apps/worker-pago/src/pricing-webhooks.ts

// GET /api/pricing/approve/:token
//   1. Lookup token en D1 pricing_proposals
//   2. Check status='pending' AND expires_at > now()
//   3. POST a Beds24 /v2/inventory/rooms/calendar con deltas_json
//   4. UPDATE D1: status='applied', applied_at, beds24_response_status
//   5. Send confirmation email a Alex
//   6. Telegram ping: "✅ Pricing applied: N changes"
//   7. Return: HTML success page

// GET /api/pricing/reject/:token  
//   1. Same lookup + check
//   2. UPDATE D1: status='rejected', no Beds24 call
//   3. Send confirmation email
//   4. Return: HTML rejected page
```

### 4.8 Admin page `/admin/pricing` (P9)

Layout simple, mobile-friendly:

```
┌─────────────────────────────────────────────┐
│ /admin/pricing                              │
├─────────────────────────────────────────────┤
│ Status: ✅ Active (next run: 06:00 MX)      │
│ [Toggle] pricing_auto_run = true            │
│ [Toggle] pricing_dry_run = false            │
│                                             │
│ Last 30 proposals:                          │
│ ┌─────────────────────────────────────────┐ │
│ │ 2026-05-26  pending  3 changes  $-450  │ │
│ │ 2026-05-25  applied  5 changes  $+1200 │ │
│ │ 2026-05-24  applied  2 changes  $+300  │ │
│ │ 2026-05-23  rejected 8 changes  -      │ │
│ │ ...                                     │ │
│ └─────────────────────────────────────────┘ │
│ [View Email] [Re-send] [Approve] [Reject]   │
│                                             │
│ Config JSON (editable textarea):            │
│ ┌─────────────────────────────────────────┐ │
│ │ {                                       │ │
│ │   "floors": {"78695": 5000, ...},      │ │
│ │   "ceilings": {"78695": 40000, ...},   │ │
│ │   "premium_seasons": [...],            │ │
│ │   ...                                   │ │
│ │ }                                       │ │
│ └─────────────────────────────────────────┘ │
│ [Save Config] [Reset to defaults]           │
└─────────────────────────────────────────────┘
```

### 4.9 Bug fixes pre-port

Antes de portar, diagnosticar el 40% error rate del Make:

1. **Beds24 token expirado** — verify `cron:beds24-token-refresh` corrió recientemente. Si NO: refrescar manual antes del port.
2. **Anthropic timeout >120s** — agregar retry logic en CF
3. **Parse JSON falla** — el validator del Make ya tiene try/catch robusto, port

---

## §5 · TESTS (P10)

### 5.1 Golden tests (5 cases)

Cada test = input real del Make scenario + expected output:

| # | Input | Expected output |
|---|---|---|
| G1 | Calendar with gap 1N en RdM | minStay=base, override='noCheckIn' |
| G2 | Calendar with gap 3N en Morenas direct | minStay=2 (base), override=null |
| G3 | Calendar with gap 5N en RdM | minStay=3 (bump primer día), override=null |
| G4 | Date T-5 días, RdM, current $9000, no premium | new_price = 9000 × 0.80 = 7200 → round 250 → $7250 |
| G5 | Date Dec 25 (Christmas premium) | NO change (skip) |
| G6 | AirBnB room 74322, base direct=2, no premium | AirBnB minStay = 3 (delta +1) |

### 5.2 Validator tests (17 cases)

Port los tests del validator Make:
- Multiples 250 enforcement
- Floor/ceiling enforcement per room
- No past dates
- No booked days (numAvail=0)
- No blackout
- Max ±20% change
- Auto-correct $8075 → $8000
- "no-op" detection
- ... (los 17 casos del Make actual)

### 5.3 Smoke test

```typescript
// Endpoint: POST /api/admin/pricing/dry-run
// Runs the full engine but skips Beds24 PATCH + email send
// Returns: proposal preview JSON

// Alex puede correr esto sin riesgo antes de activar
```

---

## §6 · DEFINITION OF DONE (verificable)

| # | Check | Cómo verificar |
|---|---|---|
| DoD-1 | Branch `feat/m1-pricing-v05-cf-port` existe en rdm-bot | `git branch -r grep v05` |
| DoD-2 | Archivos creados: pricing-{config,engine,validator,email,cron,webhooks}.ts | `ls apps/worker-pago/src/pricing-*` |
| DoD-3 | Migration 0049 `pricing_proposals` aplicada local | `wrangler d1 execute rincon --command "SELECT name FROM sqlite_master WHERE name='pricing_proposals'"` |
| DoD-4 | Floor Morenas $4000 hardcoded | `grep 4000 apps/worker-pago/src/pricing-config.ts` |
| DoD-5 | Channel asymmetry AirBnB +1 | `grep AIRBNB_MINSTAY_DELTA` |
| DoD-6 | Cron entry en wrangler.toml worker-pago | `grep "0 12" apps/worker-pago/wrangler.toml` |
| DoD-7 | Endpoints /api/pricing/approve/:token + /reject/:token responden 200 (con token válido) | `curl localhost:8788/api/pricing/approve/test-token` |
| DoD-8 | Admin page /admin/pricing carga y muestra last 30 proposals | Browser smoke test |
| DoD-9 | bot_config keys creadas: `pricing_auto_run`, `pricing_dry_run` | D1 query |
| DoD-10 | Tests pass: `pnpm --filter worker-pago test` | exit 0 |
| DoD-11 | Lint + typecheck clean | `pnpm lint && pnpm typecheck` |
| DoD-12 | Smoke endpoint /api/admin/pricing/dry-run retorna proposal JSON | curl test |
| DoD-13 | PR creada con descripción linkeando thread/213 | `gh pr list --head feat/m1-pricing-v05-cf-port` |
| DoD-14 | Conventional commits semánticos | `git log --oneline` |
| DoD-15 | CC reporta en thread/214-cc-bot-doit-213-m1-pricing-report.md | thread exists |

---

## §7 · RIESGOS + MITIGATIONS

| # | Riesgo | Prob | Impacto | Mitigation |
|---|---|---|---|---|
| R1 | Beds24 API timeout (calendar query 360d × 5 rooms es pesado) | Media | Run crashea | Timeout 120s + retry 1x. Si falla, Telegram alert + skip run |
| R2 | Anthropic timeout >120s | Baja | Run crashea | Reducir max_tokens a 8000 si timeout recurring |
| R3 | LLM hallucina precio fuera de regla | Media | Validator atrapa | Hard validator post-LLM (port del Make) |
| R4 | Validator deja pasar bug | Baja | Mal pricing aplicado | Tests anti-regression 17 cases. Manual review email todavía es human gate |
| R5 | Email no llega a Alex (Resend down) | Baja | Cambio queda pending, expira 24h | Telegram alert si email send falla |
| R6 | Token expirado pero Alex aprueba viejo | Baja | expires_at check rechaza | DB check + UI muestra status='expired' |
| R7 | Approve clickeado 2 veces (double apply) | Media | Idempotency falla | `UPDATE pricing_proposals SET status='applied' WHERE token=? AND status='pending'`. RETURNING rows = 0 → "already applied" |
| R8 | Beds24 PATCH parcial success (algunos rooms OK, otros fail) | Media | Estado inconsistente | Telegram alert + manual review. Audit beds24_response_body. Future v0.6 implementa rollback |
| R9 | Bot_config flag toggleado durante run | Baja | Confuso, no rompe | Check flag at start of cron run |
| R10 | Casa Chamán surface (room_id 679176) | Muy baja | Anti-pattern violation | NOT in ROOM_METADATA = engine ignora. Defensive |

### Rollback playbook

Si v0.5 muestra problemas:

```sql
-- Instant rollback: pause cron
UPDATE bot_config SET value='false' WHERE key='pricing_auto_run';
-- No redeploy required. Make scenario sigue paused as fallback.
```

Si necesitas rollback de un cambio ya aplicado:
```sql
-- Inspect proposal
SELECT deltas_json FROM pricing_proposals WHERE token='2026-05-26-xxxx';
-- Manual Beds24 PATCH con valores antiguos (no automated en v0.5)
```

---

## §8 · MIGRATION STRATEGY (Make → CF)

| Fase | Acción | Cuándo |
|---|---|---|
| **Phase 1** | Make paused (current). Spec thread/213 ready | NOW |
| **Phase 2** | CC mega-run port to CF (8-12h) | Post v7 ship |
| **Phase 3** | Deploy worker-pago con nuevo cron. `pricing_auto_run=false` | Post-merge |
| **Phase 4** | Alex enable `pricing_dry_run=true` + manual run-once. Review email salida | T+1d |
| **Phase 5** | Alex enable `pricing_auto_run=true` + `pricing_dry_run=false`. Cron corre 06:00 MX | T+2d |
| **Phase 6** | Observar 7 días. Si OK, declarar Make scenario "deprecated" | T+9d |
| **Phase 7** | Después de 30 días sin issues, archivar Make scenario | T+39d |

---

## §9 · APPENDIX A — Comparación lado a lado Make vs v0.5

| Aspecto | Make actual | v0.5 CF |
|---|---|---|
| Cron schedule | 06:00-06:01 UTC daily | `0 12 * * *` (12:00 UTC = 06:00 MX) |
| Beds24 API | HTTP module Make | fetch() en worker-pago |
| Anthropic API | HTTP module Make | fetch() en worker-pago |
| Model | Sonnet 4.5 | Same (claude-sonnet-4-5) |
| Max tokens | 12000 | Same |
| System prompt | Inline ExecuteCode | Same prompt en pricing-engine.ts |
| Validator | ExecuteCode JS | TypeScript port |
| Audit storage | Make datastore | D1 `pricing_proposals` table |
| Email | Gmail OAuth | Resend (existing infra) |
| Approve URL | Make webhook | `/api/pricing/approve/:token` |
| Reject URL | Make webhook | `/api/pricing/reject/:token` |
| Token expiry | 24h Make logic | 24h D1 check |
| Floor Morenas | $3500 | **$4000** |
| Channel asymmetry | None | AirBnB +1 minStay |
| Premium SEP completo | Christmas, Sept15, HolyWeek | + Summer + Winter SEP |
| Telegram alert | None | Reuse worker-pago TG infra |
| Kill-switch | Make UI deactivate | `bot_config pricing_auto_run=false` |
| Dry-run mode | None | `pricing_dry_run=true` flag |
| Admin UI | None | `/admin/pricing` page |
| JSON config editor | None | Textarea en /admin/pricing |
| Per-room disable | None | `pricing_disabled_rooms` config |

---

## §10 · APPENDIX B — Comando CC para mega-run

```
Modo: DoIt
Spec: rdm-discussion/threads/213-wc-m1-pricing-v0.5-port-make-to-cf.md
Branch: feat/m1-pricing-v05-cf-port (rdm-bot)
Modelo: claude-sonnet-4-6 (default per settings.json)
Effort estimate: 8-12h

Pre-flight:
1. cd c:/dev/rdm/dev/bot
2. git fetch origin && git checkout main && git pull --rebase
3. git checkout -b feat/m1-pricing-v05-cf-port
4. pnpm install
5. Lee thread/213 completo

Ejecuta P1→P11 en orden:
- P1: pricing-config.ts (30 min)
- P2: migration 0049_pricing_proposals.sql (30 min)
- P3: pricing-validator.ts (1.5h)
- P4: pricing-engine.ts (2h)
- P5: pricing-email.ts (1h)
- P6: pricing-cron.ts + wrangler.toml (1h)
- P7: pricing-webhooks.ts (1h)
- P8: admin-pricing.ts (30 min)
- P9: /admin/pricing page (1.5h)
- P10: Tests anti-regression (1h)
- P11: Smoke endpoint (30 min)

Defaults:
- ASCII shell args, UTF-8 file contents
- Conventional Commits
- NO ALTER TABLE
- NO commits con secrets (verify .env.example, .dev.vars correct)
- NO force-push
- NO auto-merge a main

Si stuck >30 min: HALT, commit progress, escribe report en thread/214.

Anti-patterns CRÍTICOS:
- Pet fee NO toca este módulo (es del greeter v7). Si tocas: fuera de scope.
- Casa Chamán (679176) NOT en ROOM_METADATA — verificar.
- Karina cel NO toca este módulo (es del greeter v7).
- NO hardcode floor Morenas $3500 (es $4000).
- minStay floor universal = 2 NEVER 1.
- NO usar LLM para decisión final — el validator es authoritative.
- Beds24 PATCH solo desde webhook approve, NUNCA desde cron run.

Al final:
1. pnpm test && pnpm lint && pnpm typecheck pasan
2. git push origin feat/m1-pricing-v05-cf-port
3. gh pr create con descripción linkeando thread/213
4. Crea thread/214-cc-bot-doit-213-m1-pricing-report.md
5. NO mergees PR. Alex revisa.
```

---

## §11 · FIN DEL SPEC

Ready for CC mega-run **después que Greeter v7 (PR #186) sea merged + deployed**.

Lecciones del Make scenario incorporadas:
- ✅ Hard validator preservado (era lo mejor del Make)
- ✅ Workflow APPROVE/REJECT email preservado (era lo que te funcionaba)
- ✅ Floor Morenas actualizado ($4000)
- ✅ Channel asymmetry agregado
- ✅ Premium SEP completo agregado
- ✅ Bug 40% error rate identificado (Beds24 token refresh) y mitigation

— wc, 2026-05-26
