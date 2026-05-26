---
id: 211
author: wc
topic: greeter-v7-megarun-spec
status: ready_for_cc
mode: DoIt
priority: P1
target_repo: rdm-bot
target_branch: feat/greeter-v7-warm-vip-aware
model: sonnet-4-6
effort_estimate_h: 7-9
created_at: 2026-05-26
supersedes: thread/82 (v6 spec)
---

# thread/211 — Greeter v7: Warm + VIP-Aware + Bucket Detection

## §0 · TL;DR para Alex (mobile-friendly)

| Item | Resumen |
|---|---|
| **Problema** | Greeter v6 es seco, deflecta 95% con link, escalations 22% (>80% waste a leads), 24% saludos idénticos plantilla, NO detecta clientes activos |
| **Solución** | Greeter v7: bucket detection D1 (VIP_in_stay / VIP_pre_stay / VIP_repeat / lead), tonal palette 3 niveles derivada de voz real Alex, escalation SOLO a VIPs (cel Karina +52 744 144 1575), mix sano de respuestas (35% inline / 25% inline+link / 13% opciones / 22% link puro / <5% escalate) |
| **Effort CC** | 7-9h en mega-run autónomo, Sonnet 4.6 |
| **Branch** | `feat/greeter-v7-warm-vip-aware` |
| **Canary inicial** | 0% — Alex sube manualmente después de smoke test |
| **Rollback** | Instant via `UPDATE bot_config SET greeter_prompt_version_force='v6'` |
| **Bugs colaterales arreglados** | Número viejo `+525570618798` en fallback → cel Karina. `buildSystemPromptBlocksV6` unused bug. Validator falso positivo `pet_fee_per_noche` |

---

## §1 · CONTEXT (audit completo del v6)

### 1.1 Estado actual v6 verificado en D1 (848 turns)

| Métrica | Valor v6 | Diagnóstico |
|---|---|---|
| Turns | 848 (100% canary) | OK |
| route_user_to_url (link) | 480 (56%) | DEMASIADO ALTO |
| escalate_to_human | 199 (23%) | DEMASIADO ALTO |
| anti_loop forzados | 168 (de 199) | 85% de escalations = bot dió loop, no escalación legítima |
| clarification | 138 (16%) | Pregunta texto libre, sin opciones acotadas → causa loops |
| Cache hit ratio | 95.6% | OK económico |
| Avg cost/turn | $0.0023 | OK económico |
| Saludos plantilla 4 villas IDÉNTICA | 24% | ANTI-PATTERN |
| Cierres con `→ link` | 95% | ANTI-PATTERN |
| Acuse del nombre del user | 4% (accidental) | NO INTENCIONAL |
| Acuse emocional (gratitud/bendición/frustración) | 0% | CRITICAL GAP |
| VIPs detectados con trato diferencial | 0/6 esperados | BUG: contexto guest NO llega al LLM |

### 1.2 Hallazgos arquitectónicos críticos

**Bug 1 — `buildSystemPromptBlocksV6` está muerto.** Retorna 2 bloques (static + dynamic con Today/lang/turn_count), pero `handler-v5.ts` solo recibe `systemPromptV5: string` (single string) y pasa 1 bloque. Implicación: las variables `{TODAY}`, `{LANG}`, `{TURN_COUNT}` que el prompt v6 referencia **nunca llegan al LLM**. El bot está adivinando contexto.

**Bug 2 — Fallback con número viejo.** `buildFallbackResult` (process-tool-use.ts) usa `https://wa.me/525570618798`. Ese NO es Karina. Cuando notifyHuman falla, user es enviado a número incorrecto.

**Bug 3 — Escalate reply hardcoded plano.** `buildEscalateReply` retorna texto fijo "Le paso esto a Karina o Alex — te van a escribir en un rato." Cero variación según urgencia, cero acuse del sentimiento del user.

**Bug 4 — Solo 1/7450 guests tiene `manychat_subscriber_id`.** Lookup primario debe ser `phone_e164` con normalización subscriber→phone, NO subscriber_id directo.

**Bug 5 — AirBnB tiene `deposit_paid=0` SIEMPRE.** AirBnB cobra al guest, no pasa por nuestra MP. Criterio bucket VIP_pre_stay debe ser `status='booked'`, NO `deposit_paid > 0`.

**Bug 6 — Validator falso positivo.** Regex `pet_fee_per_noche` matchea cuando bot dice CORRECTO "$300 por estancia, NO por noche". 1 falso positivo en 144 flags (0.7%) pero estilo a corregir.

### 1.3 Por qué el bot es seco (causa raíz)

El system prompt v6 dice **literalmente**:
> *"Tu trabajo es redirigir al usuario al sitio web. NO respondes con datos concretos. PROHIBIDO: CERO emojis en cierre, Hard cap 150 palabras"*
> *Target: `route_user_to_url` 80% de los casos*

El prompt fue diseñado defensivo contra overselling. En el proceso eliminó: reconocimiento emocional, variación de plantillas, llamar al user por nombre, cierres conversacionales sin URL, emojis cálidos. **Cero acuse del sentimiento del user — 0/40 muestras.**

### 1.4 Voz real de Alex (extraída de 40 host messages reales, últimos 30 días)

Patrones auténticos detectados en `bot_messages_inbox` (source='host', channel='airbnb'):

**Saludos personales con nombre:**
- *"Muy buenos días Yoselin !!🤗"*
- *"Hola [Name], buenas tardes,"*
- *"Hi [Name]! 🌅"*

**Reconocimiento de calor humano:**
- *"Todo un gusto tenerla de vuelta con su linda familia - bienvenidos!"*
- *"Que bueno saber que ya tienen todo listo, estamos encantados de recibirlos 🤗"*
- *"Welcome! 🌴🐟🌞"*

**Decir NO con calidez (NO seco):**
- *"Buenas noches Liliana, lo siento, es temporada alta y tendremos huéspedes antes y después de ustedes, les pido respetar el horario..."*
- *"Lo siento, año nuevo ya todo reservado"*

**Anfitrión sensorial:**
- *"brisa garantizada 🌊"* / *"estamos en la costa pacífico"* / *"🌴🐟🌞"*

**Humor ligero cuando aplica:**
- *"Ojalá y nuestros amigos de la CFE lo arreglen rápido"* (a cliente sin luz)
- *"...come one.. 😁"* (a cliente EN dudando de chef)

**Cierres invitacionales (sin link siempre):**
- *"¡Te esperamos!"* → *"— Alexander 🌅"*
- *"Cualquier otra cosa siempre estoy a sus ordenes!"*

**Emojis signature**: 🤗 🌴 🌅 🌊 🐟 🌞 😁 ❤️ 🆘 📍 🗺️ 🌤️

---

## §2 · SCOPE — YES/NO explícito

### YES — Sí se hace en este mega-run

- ✅ Crear `system-prompt-v7.ts` con tonal palette 3 niveles
- ✅ Crear `handler-v7.ts` que recibe blocks array (NO string)
- ✅ Crear `bucket-detector.ts` con D1 query VIP_in_stay/VIP_pre_stay/VIP_repeat/lead
- ✅ Crear `karina-config.ts` con cel hardcoded + off-hours window
- ✅ Extender `PromptContextV6` → `PromptContextV7` con bucket+guest fields
- ✅ Implementar 3-tier cache (static / per-conv / per-turn)
- ✅ 5 plantillas saludo alternables determinísticas (djb2 hash)
- ✅ Few-shot examples derivados de voz real Alex (40 host messages)
- ✅ Lead exit gracioso (NO escalate, mostrar WA Karina link)
- ✅ Off-hours auto-reply 22:00-08:00 hora MX
- ✅ Distress de lead → auto-reply 911 (NO Karina)
- ✅ Bug fix: `buildFallbackResult` cel viejo → Karina
- ✅ Bug fix: Validator `pet_fee_per_noche` exclude negaciones
- ✅ Canary `canary_percent_v7` + `greeter_prompt_version_force` con valor `'v7'`
- ✅ Tests anti-regression (worst cases reales como golden tests)
- ✅ Defaults: Conventional Commits, ASCII shell args UTF-8 file contents, branch protection NO

### NO — Fuera de scope (anotar como issue si encuentras)

- ❌ Cambiar `tools-v5.ts` (los 4 tools quedan igual: route_user_to_url, request_clarification, handoff_to_booker, escalate_to_human)
- ❌ Cambiar `run-greeter-v5.ts` orchestrator (anti-loop, dispatch wiring sigue igual)
- ❌ Tocar Booker (out of scope, otro thread)
- ❌ Migration D1 nueva (todo usa schemas existentes)
- ❌ ALTER TABLE en guests o beds24_bookings
- ❌ Tocar Beds24 sync (sólo lectura D1 de bookings)
- ❌ Tocar MercadoPago webhook
- ❌ Cambiar `apps/worker-bot/src/canary.ts` core logic (solo añadir v7 flags)
- ❌ Borrar v6 (queda como fallback funcional)
- ❌ VIP_imminent_booker bucket (descartado en discusión Alex)
- ❌ Casa Chamán bucket o mention (Q3 2026, NO surfacar)
- ❌ Tocar `apps/web` admin (otro thread)
- ❌ Modificar bot_metrics, audit_log schemas

---

## §3 · DECISIONES CERRADAS (Alex votos documentados)

| # | Decisión | Voto Alex |
|---|---|---|
| 1 | Política buckets: 4 buckets (VIP_in_stay / VIP_pre_stay / VIP_repeat / lead) | GO |
| 2 | Escalation SOLO a VIPs, leads = exit gracioso con WA link Karina | GO |
| 3 | Hard escalate (bot pausado) para VIP_in_stay + VIP_pre_stay; soft alert (bot sigue) para VIP_repeat | GO |
| 4 | Karina cel: `+52 744 144 1575` hardcoded en `karina-config.ts` | GO |
| 5 | Karina WA link: `https://wa.me/527441441575` | GO |
| 6 | Off-hours auto-reply 22:00-08:00 hora MX (UTC-6) | GO |
| 7 | Distress lead → auto-reply 911 (NO Karina, NO Alex) | GO |
| 8 | VIP_imminent_booker (gap 30 min booker→MP) | DESCARTADO |
| 9 | MP-Beds24 bridge para Edge 4 | DESCARTADO (latency real 14s, no 10 min) |
| 10 | Mix sano respuestas: 30-40% inline / 25-30% inline+link / 10-15% opciones / 15-25% link puro / <5% escalate | GO |
| 11 | Tonal palette 3 niveles: Cálido-bienvenido, Anfitrionero-funcional, Cálido-personal | GO |
| 12 | 5 plantillas saludo alternables (djb2(subscriber_id) % 5) | GO |
| 13 | Canary inicial v7 = 0%, Alex sube manualmente | GO |
| 14 | Modelo: claude-haiku-4-5 (igual que v6) | GO |
| 15 | Cache: 3-tier con 2 breakpoints, beta header `extended-cache-ttl-2025-04-11` para 1h TTL | GO |
| 16 | Bucket criterion: `status='booked'` NO `deposit_paid > 0` (AirBnB siempre tiene deposit_paid=0) | GO (post-corrección) |
| 17 | Phone lookup primary, subscriber_id secondary (solo 1/7450 guests tiene subscriber_id) | GO |

---

## §4 · IMPLEMENTACIÓN

### 4.1 Sub-deliverables (11 items)

| # | Componente | Files | Effort |
|---|---|---|---|
| D1 | `system-prompt-v7.ts` con tonal palette + 5 plantillas + bucket coaching + few-shots de voz Alex | `packages/agents/greeter/system-prompt-v7.ts` | 2h |
| D2 | `handler-v7.ts` con blocks array (fix bug v6) | `packages/agents/greeter/handler-v7.ts` | 1h |
| D3 | `bucket-detector.ts` con 2 queries D1 + phone normalize | `apps/worker-bot/src/bucket-detector.ts` | 1h |
| D4 | `karina-config.ts` constants + off-hours helper | `apps/worker-bot/src/karina-config.ts` | 30 min |
| D5 | `PromptContextV7` extension + `buildSystemPromptBlocksV7` con 3-tier cache | en D1 file | 45 min |
| D6 | Run wiring: `run-greeter-v5.ts` añade rama v7 (similar a v6 swap) | `apps/worker-bot/src/run-greeter-v5.ts` (small patch) | 30 min |
| D7 | Bug fix: `buildFallbackResult` + `buildEscalateReply` usan Karina cel | `packages/agents/greeter/process-tool-use.ts` | 30 min |
| D8 | Lead exit gracioso (en system prompt v7 + dispatcher para escalate→lead path) | en D1 + process-tool-use | 30 min |
| D9 | `v7-validator.ts` con regex anti falso positivo pet_fee | `apps/worker-bot/src/v7-validator.ts` | 1h |
| D10 | Canary toggle: `canary_percent_v7` + `greeter_prompt_version_force` con `'v7'` valor | `apps/worker-bot/src/canary.ts` (small patch) + bot_config seed | 30 min |
| D11 | Tests anti-regression: 17 golden tests con worst cases reales D1 | `packages/agents/tests/greeter-v7-system-prompt.test.ts` | 1h |
| **TOTAL** | | | **~8h** |

### 4.2 Constants críticas (D4 — karina-config.ts)

```typescript
// apps/worker-bot/src/karina-config.ts
/**
 * Karina (co-host RdM) contact details.
 * SOURCE OF TRUTH: thread/211 §3 decision #4-5.
 * NEVER hardcode this phone number elsewhere; import from here.
 */
export const KARINA_PHONE_E164 = '+52 744 144 1575';
export const KARINA_PHONE_E164_NO_SPACES = '+527441441575';
export const KARINA_WA_LINK = 'https://wa.me/527441441575';

/**
 * Off-hours window (hora MX = UTC-6, no DST).
 * Outside this window the bot adds an auto-reply note for VIPs about response timing.
 * Lead off-hours: no special handling (lead exit gracioso siempre).
 */
export const OFF_HOURS_START_MX = 22; // 22:00 MX
export const OFF_HOURS_END_MX = 8;    // 08:00 MX

/**
 * Returns true if the given timestamp falls in Karina's off-hours window (MX time).
 * Uses UTC-6 offset (no DST in México post-2022 in most regions including Guerrero).
 */
export function isOffHoursMX(date: Date = new Date()): boolean {
  const mxHour = (date.getUTCHours() - 6 + 24) % 24;
  return mxHour >= OFF_HOURS_START_MX || mxHour < OFF_HOURS_END_MX;
}
```

### 4.3 Bucket detection (D3 — bucket-detector.ts)

```typescript
// apps/worker-bot/src/bucket-detector.ts
/**
 * Greeter v7 bucket detection.
 *
 * 4 buckets:
 *   - VIP_in_stay: arrival <= today <= departure AND status='booked'
 *   - VIP_pre_stay: arrival > today AND status='booked'  (NOT deposit_paid, AirBnB siempre tiene 0)
 *   - VIP_repeat: total_bookings >= 1 AND last departure ∈ últimos 365d AND status='booked'
 *   - lead: cualquier otra cosa
 *
 * Lookup strategy (ordered):
 *   1. phone_e164 normalized from subscriber_id (~3-10% match rate)
 *   2. manychat_subscriber_id direct (<0.1% match rate, only 1/7450 guests)
 *
 * Uses 2 SEPARATE queries (NO OR combined) for index usage.
 * Both indices exist: idx_guests_phone_e164_unique + idx_guests_manychat_subscriber_id.
 */

export type Bucket = 'VIP_in_stay' | 'VIP_pre_stay' | 'VIP_repeat' | 'lead';

export interface BucketDetectionResult {
  bucket: Bucket;
  guest_id?: string;
  guest_name?: string;
  total_bookings?: number;
  active_booking?: {
    beds24_booking_id: string;
    arrival: string;
    departure: string;
    property: string; // roomId or property slug
    channel: string;
  };
  last_stay?: {
    property: string;
    departure: string; // YYYY-MM-DD
  };
}

export interface BucketDetectorEnv {
  DB: D1Database;
}

/**
 * Normalize WhatsApp subscriber_id (e.g. "5217441441575") to E.164 phone_e164 format
 * (e.g. "+527441441575") matching the format stored in guests.phone_e164.
 *
 * México mobile numbers in WhatsApp: 13 chars starting with "521" → 12-char E.164 starting with "+52".
 * México landline: 12 chars starting with "52" → 12-char E.164 starting with "+52".
 * Other countries: prepend "+".
 */
export function subscriberToPhoneE164(subscriberId: string): string {
  if (subscriberId.startsWith('521') && subscriberId.length === 13) {
    // MX mobile: drop the "1" → +52 + 10 digits
    return '+52' + subscriberId.slice(3);
  }
  if (subscriberId.startsWith('52') && subscriberId.length === 12) {
    // MX landline: keep all
    return '+' + subscriberId;
  }
  // Other countries: just prepend +
  return '+' + subscriberId;
}

/**
 * Detect bucket for incoming subscriber_id.
 * Returns bucket='lead' on any error (defensive — never block bot on D1 hiccup).
 *
 * Performance: ~1-3ms warm cache (2 indexed lookups).
 */
export async function detectBucket(
  env: BucketDetectorEnv,
  subscriberId: string,
): Promise<BucketDetectionResult> {
  if (!subscriberId) return { bucket: 'lead' };

  const phoneE164 = subscriberToPhoneE164(subscriberId);
  const today = new Date().toISOString().slice(0, 10);

  try {
    // Step 1: lookup guest by phone (primary path) or subscriber_id (fallback)
    // Two queries instead of OR — guarantees index usage.
    let guest = await env.DB.prepare(
      `SELECT id, name, total_bookings, language_preferred
       FROM guests
       WHERE phone_e164 = ? AND deleted_at IS NULL
       LIMIT 1`,
    )
      .bind(phoneE164)
      .first<{
        id: string;
        name: string | null;
        total_bookings: number;
        language_preferred: string | null;
      }>();

    if (!guest) {
      guest = await env.DB.prepare(
        `SELECT id, name, total_bookings, language_preferred
         FROM guests
         WHERE manychat_subscriber_id = ? AND deleted_at IS NULL
         LIMIT 1`,
      )
        .bind(subscriberId)
        .first();
    }

    if (!guest) return { bucket: 'lead' };

    // Step 2: lookup active booking (in_stay or pre_stay)
    const activeBooking = await env.DB.prepare(
      `SELECT beds24_booking_id, arrival, departure, channel
       FROM beds24_bookings
       WHERE guest_id = ?
         AND status = 'booked'
         AND departure >= date('now', '-1 day')
         AND arrival <= date('now', '+90 days')
       ORDER BY arrival ASC
       LIMIT 1`,
    )
      .bind(guest.id)
      .first<{
        beds24_booking_id: string;
        arrival: string;
        departure: string;
        channel: string;
      }>();

    if (activeBooking) {
      const isInStay =
        activeBooking.arrival <= today && activeBooking.departure >= today;
      const isPreStay = activeBooking.arrival > today;

      if (isInStay) {
        return {
          bucket: 'VIP_in_stay',
          guest_id: guest.id,
          guest_name: guest.name ?? undefined,
          total_bookings: guest.total_bookings,
          active_booking: {
            beds24_booking_id: activeBooking.beds24_booking_id,
            arrival: activeBooking.arrival,
            departure: activeBooking.departure,
            property: '', // TODO: enrich with roomId→slug mapping if needed
            channel: activeBooking.channel,
          },
        };
      }

      if (isPreStay) {
        return {
          bucket: 'VIP_pre_stay',
          guest_id: guest.id,
          guest_name: guest.name ?? undefined,
          total_bookings: guest.total_bookings,
          active_booking: {
            beds24_booking_id: activeBooking.beds24_booking_id,
            arrival: activeBooking.arrival,
            departure: activeBooking.departure,
            property: '',
            channel: activeBooking.channel,
          },
        };
      }
    }

    // Step 3: check VIP_repeat (past stay in last 365d)
    if (guest.total_bookings >= 1) {
      const lastStay = await env.DB.prepare(
        `SELECT departure, channel
         FROM beds24_bookings
         WHERE guest_id = ?
           AND status = 'booked'
           AND departure < date('now')
           AND departure > date('now', '-365 days')
         ORDER BY departure DESC
         LIMIT 1`,
      )
        .bind(guest.id)
        .first<{ departure: string; channel: string }>();

      if (lastStay) {
        return {
          bucket: 'VIP_repeat',
          guest_id: guest.id,
          guest_name: guest.name ?? undefined,
          total_bookings: guest.total_bookings,
          last_stay: {
            property: '',
            departure: lastStay.departure,
          },
        };
      }
    }

    return {
      bucket: 'lead',
      guest_id: guest.id,
      guest_name: guest.name ?? undefined,
      total_bookings: guest.total_bookings,
    };
  } catch (err) {
    console.error('[bucket-detector] D1 error, defensive fallback to lead', err);
    return { bucket: 'lead' };
  }
}
```

### 4.4 PromptContextV7 (D5)

```typescript
// packages/agents/greeter/system-prompt-v7.ts (header)

export type BucketV7 = 'VIP_in_stay' | 'VIP_pre_stay' | 'VIP_repeat' | 'lead';

export interface PromptContextV7 {
  // Per-turn (Tier 3 — NO cached)
  today: string;           // YYYY-MM-DD
  lang: 'es' | 'en';
  turn_count: number;
  last_intent?: string;
  subscriber_id: string;
  detected_property?: string;

  // Per-conversation (Tier 2 — cached 5min)
  bucket: BucketV7;
  guest_name?: string;
  total_bookings?: number;
  active_booking?: {
    arrival: string;
    departure: string;
    days_to_arrival: number; // negative if in_stay, positive if pre_stay
    property: string;
  };
  last_stay?: {
    departure: string;
    property: string;
  };

  // Per-turn (Tier 3)
  is_off_hours: boolean;   // if true, system prompt instructs to add Karina response-time note
  saludo_template_index: number; // djb2(subscriber_id) % 5 → which of 5 templates
}
```

### 4.5 Tonal palette (D1 — system-prompt-v7.ts)

3 niveles de calidez según contexto. El bot elige nivel basado en intent + bucket + emotional cues del user.

**Nivel 1 — Cálido-bienvenido** (primer turn, saludo)
- Greeting con nombre si VIP
- Mención de zona / sensorial
- Pregunta de seguimiento natural (NO lista de 4 villas)
- Variar entre 5 plantillas

**Nivel 2 — Anfitrionero-funcional** (preguntas info, cotización)
- Eco del dato (number, dates, property)
- Respuesta inline cuando aplica
- Link contextual al final si requiere data dinámica

**Nivel 3 — Cálido-personal** (gratitud, repeat guest, bendición, frustración, in-stay distress)
- Acuse del sentimiento PRIMERO
- Sin link (a veces)
- Emojis cálidos permitidos: ❤️ 🙏 🤗
- Sin plantillas, respuesta corta humana

### 4.6 5 Plantillas saludo (D1)

Selección determinística: `saludo_template_index = djb2(subscriber_id) % 5`

```
Plantilla 0 (variación estándar):
  "¡Hola{name_or_empty}, buenas{time_of_day}! 🌅 Bienvenido a Rincón del Mar, Pie de la Cuesta. {open_question}"

Plantilla 1 (sensorial):
  "¡{greeting_by_time}{name_or_empty}! 🌴 Frente al Pacífico, brisa garantizada 🌊. {open_question}"

Plantilla 2 (anfitrión directo):
  "¡Hola{name_or_empty}! Soy Felix, asistente del equipo de Alex y Karina. {open_question}"

Plantilla 3 (cálido familiar):
  "¡{greeting_by_time}{name_or_empty}! 🤗 Qué gusto saludarte. {open_question}"

Plantilla 4 (zona específica):
  "¡Hola{name_or_empty}! Bienvenido. Estamos en Pie de la Cuesta, costa pacífico de Acapulco. {open_question}"
```

Donde:
- `{name_or_empty}` = `" {guest_name}"` si bucket es VIP_repeat o VIP_*, vacío si lead sin name
- `{greeting_by_time}` = "Buenos días" / "Buenas tardes" / "Buenas noches" según hora MX
- `{open_question}` = pregunta abierta variable (NO lista de 4 villas). Ej: "¿Buscas algo para qué plan?" / "¿En qué fechas y cuántos vienen?" / "¿Para cuánta gente?"

**Override para VIP_repeat**: usar plantilla específica:
```
"¡{name}! Qué emoción saber de ti de nuevo 🤗. ¿Cómo van todos? {context_question}"
```

### 4.7 Bucket coaching sections (en system prompt v7)

Cada bucket tiene su sección de coaching dentro del Tier 1 (system prompt static). El LLM lee el `bucket` field del Tier 2 context y aplica la sección correspondiente.

```
BUCKET COACHING:

[VIP_in_stay]
- Tono: Cálido-personal (Nivel 3)
- Usa el nombre del guest siempre
- Si user reporta problema operacional (luz, agua, chef, late check-in): escalate inmediato
  con `escalate_to_human` reason='customer_support' urgency='high'
- Reply: "Le aviso a Karina ahora mismo, te marca al +52 744 144 1575 en minutos. ¿Estás bien mientras?"
- Si user solo saluda o pregunta amenidad: respuesta cálida + ofrece ayuda
- NUNCA mandes al sitio para info operacional in-stay

[VIP_pre_stay]
- Tono: Cálido-personal (Nivel 3)
- Usa el nombre del guest
- Si user pide cambio reserva, extra guests, mascota nueva, fechas: escalate inmediato
  con reason='booking_modification' urgency='medium'
- Reply: "Le paso a Karina ahora para coordinar esto contigo. WA: +52 744 144 1575"
- Si user pregunta amenidad, ubicación, check-in: respuesta inline directa (Nivel 2)

[VIP_repeat]
- Tono: Cálido-personal en saludo, Anfitrionero-funcional en preguntas
- Usa el nombre, menciona estancia previa si aplica
- NO escalate automáticamente (soft alert solo)
- Soft alert: añade metadata.soft_alert=true para que worker mande TG ping a Karina FYI
- Sigue respondiendo normalmente con info actualizada

[lead]
- Tono: Cálido-bienvenido en saludo, Anfitrionero-funcional resto
- NUNCA escalate. Si user pide humano: exit gracioso con WA Karina:
  "Para hablar directo con Karina, mándale WhatsApp al +52 744 144 1575.
   Mientras tanto, el sitio tiene toda la info que necesitas → [link contextual]"
- Si distress emocional REAL (suicidio, emergencia médica, peligro):
  auto-reply emergencia 911, NO Karina, NO Alex.
  Reply: "Esto suena a una emergencia. Llama al 911 (México) — son los que pueden ayudarte ahora."
- Si en loop (2+ reformulaciones distintas): exit gracioso con WA Karina (NO escalate)
```

### 4.8 Mix de modos esperado v7

| Modo | Cuándo | Target % | Anti-pattern v6 actual |
|---|---|---|---|
| Modo 1 — Respuesta inline directa | Pregunta puntual con respuesta en prompt (pet policy, chef incluido) | 30-40% | <5% |
| Modo 2 — Respuesta inline + link profundidad | Pregunta + sitio tiene más detalle | 25-30% | <10% |
| Modo 3 — Respuesta con opciones acotadas | "Para 15 personas qué me recomiendas" → 3 opciones concretas | 10-15% | <2% |
| Modo 4 — Link contextual | Disponibilidad en vivo, cotización con dates+pax | 15-25% | ~50% (sobre-deflect) |
| Modo 5 — Escalation | Solo 4 cases × bucket VIP | <5% | 22% (>80% waste) |
| Clarification | Cuando datos incompletos | <10% | 16% (loops) |

### 4.9 Acuse emocional (regla nueva §3F del prompt)

```
RECONOCIMIENTO EMOCIONAL OBLIGATORIO antes de responder cuando user expresa:

- Gratitud / bendición:
  Detect: "gracias", "bendiciones", "Bendito sea Dios", "que Dios los", "feliz", "alegría"
  Respuesta: ACUSE PRIMERO, sin link, máximo 2 líneas, emoji cálido permitido
  Ejemplo: "¡Gracias por las bendiciones! Iris, la bebé y yo lo apreciamos un montón 🙏. Aquí estamos cuando nos necesites."

- Frustración / queja:
  Detect: "no me contesta", "esperé", "muy caro", "lejos", "decepcionado", "molesto"
  Respuesta: ACUSE PRIMERO ("una disculpa", "entiendo"), luego ofrece solución
  Ejemplo: "Una disculpa por la espera. Para que veas todo en orden, te paso disponibilidad y precios en vivo → [link]"

- Distress emocional:
  Detect: emergencia, peligro, crisis, suicidio, "no puedo más", "ayúdame", "urgente"
  → Si VIP: hard escalate Karina con urgency='high'
  → Si lead: auto-reply 911

- Cortesía / follow-up cortés:
  Detect: turn_count > 1 AND user msg corto "gracias", "ok", "espero igual", "buen día"
  Respuesta: SIN plantilla saludo, sin link, máximo 1-2 líneas
  Ejemplo: "Por aquí todo bien, gracias por preguntar. ¿En qué te ayudo?"
```

### 4.10 Cache architecture 3-tier

```typescript
// buildSystemPromptBlocksV7 returns:
[
  // Tier 1 — STATIC (cached 1h via beta header extended-cache-ttl-2025-04-11)
  {
    type: 'text',
    text: GREETER_SYSTEM_PROMPT_V7, // ~12K tokens (prompt + intent_catalog + coaching + few-shots)
    cache_control: { type: 'ephemeral', ttl: '1h' },
  },
  
  // Tier 2 — PER-CONVERSATION (cached 5min ephemeral)
  // CAVEAT: Haiku 4.5 min cache = 2048 tokens. Bloque siempre debe pad hasta >=2048
  // o no cachea. Solución: añadir BUCKET_COACHING_FULL (~3K tokens, content por bucket)
  {
    type: 'text',
    text: buildBucketContextBlock(ctx), // ~2500-3500 tokens (incluye full bucket coaching)
    cache_control: { type: 'ephemeral' },
  },
  
  // Tier 3 — PER-TURN (NO cached)
  {
    type: 'text',
    text: buildTurnContextBlock(ctx), // ~150-300 tokens (Today, turn_count, etc)
    // NO cache_control
  },
]
```

**Cost projection con cache 95%+ hit rate**:
- Cold conv (T1 read, T2 write, T3 fresh): ~$0.007/turn
- Warm conv (T1+T2 read, T3 fresh): ~$0.003/turn
- Average 5-turn conv: ~$0.004/turn

Target $0.005/turn promedio — cumple.

### 4.11 Lead exit gracioso (D8)

Cuando bucket='lead' AND user pide humano explícito OR está en loop 2+ reformulaciones:

```typescript
// En process-tool-use.ts, cuando bucket='lead' y reason='user_request':
// NO llamar a notifyHumanHandoff. NO pausar bot. Solo responder con exit gracioso.

const LEAD_EXIT_REPLIES = {
  es: `Para hablar directo con Karina, mándale WhatsApp al ${KARINA_PHONE_E164}: ${KARINA_WA_LINK}\n\nMientras tanto, el sitio tiene toda la info — disponibilidad en vivo, precios, fotos, FAQ.`,
  en: `To talk directly with Karina, send her WhatsApp at ${KARINA_PHONE_E164}: ${KARINA_WA_LINK}\n\nIn the meantime, the site has everything you need — live availability, prices, photos, FAQ.`,
};
```

### 4.12 Bug fixes (D7)

**Fix 1**: `buildFallbackResult` cambia de `https://wa.me/525570618798` a `KARINA_WA_LINK`
**Fix 2**: `buildEscalateReply` ahora recibe `bucket` y `urgency` param, varía mensaje
**Fix 3**: Si bucket es 'lead', `processEscalateToHuman` redirige a `processLeadExit` (NO escalate)

### 4.13 Canary toggle (D10)

Añadir a `bot_config`:
```sql
INSERT INTO bot_config (key, value, updated_at, updated_by) VALUES
  ('canary_percent_v7', '0', datetime('now'), 'thread/211'),
  -- greeter_prompt_version_force ya existe, solo añadir support para valor 'v7' en canary.ts
ON CONFLICT(key) DO NOTHING;
```

En `canary.ts`, añadir:
```typescript
export type PromptVersion = 'v5' | 'v6' | 'v7'; // expand union

export async function getPromptVersion(...) {
  // ...existing logic...
  const force = config.get('greeter_prompt_version_force') ?? '';
  if (force === 'v7') return 'v7';
  if (force === 'v6') return 'v6';
  if (force === 'v5') return 'v5';

  // Two-stage canary: v6 base + v7 layered on top of v6
  const percentV7Str = config.get('canary_percent_v7') ?? '0';
  const percentV7 = Number.parseInt(percentV7Str, 10);
  if (!Number.isNaN(percentV7) && percentV7 > 0 && isInCanaryV5(subscriberId + 'v7', percentV7)) {
    return 'v7';
  }
  // ...fallback to v6/v5 logic...
}
```

---

## §5 · TESTS (D11)

### 5.1 Anti-regression golden tests (17 cases)

Cada test = mensaje real del v6 worst cases + expected output mode (sin pinear texto exacto, sí estructura).

| # | Input (real D1) | Bucket | Expected Mode | Expected NO contiene |
|---|---|---|---|---|
| 1 | "Bendito sea Dios, deseo lo mejor a tu nueva familia" | lead | Modo 1 con 🙏, sin link | `→ http`, plantilla 4 villas |
| 2 | "Buenos días. No sé cómo funcionan pero no hay nadie que me contacta" | lead | Modo 2 con acuse + link | Plantilla saludo, escalate |
| 3 | "aque hora salen los huéspedes todavía están aquí" | VIP_in_stay | Modo 5 escalate hard | "Le paso esto" plantilla genérica |
| 4 | "Buenas tardes, sí gracias, espero usted esté bien" (turn 2+) | lead | Modo 1 corto sin link | Plantilla 4 villas |
| 5 | "Hola Alex! Estuvimos en tu casa el año pasado" | VIP_repeat | Modo 1 con nombre + emoción | Plantilla genérica |
| 6 | "Aceptan mascotas?" | lead | Modo 1 inline | "→" link genérico |
| 7 | "Cuánto cobran extra de huéspedes?" | lead | Modo 2 con número | Solo link sin explicación |
| 8 | "Para 15 personas qué recomiendan?" | lead | Modo 3 con 3 opciones | Una sola villa genérica |
| 9 | "Está libre del 15-17 ago?" | lead | Modo 4 link disponibilidad | Respuesta de disponibilidad inventada |
| 10 | "Hola" (primer turn) | lead | Modo 1 saludo, 1 de 5 plantillas | Plantilla 4 villas literal |
| 11 | "Quiero hablar con alguien" | lead | Modo 1 exit gracioso con WA Karina | Escalate, número viejo `525570618798` |
| 12 | "Quiero hablar con alguien" | VIP_in_stay | Modo 5 escalate hard con cel Karina | número viejo, "Le paso esto" plano |
| 13 | "Necesito ayuda urgente" | VIP_in_stay | Modo 5 escalate urgency=high | número viejo |
| 14 | "no quiero más links" | lead | Modo 1 exit gracioso WA Karina | Otro link genérico |
| 15 | "$300 por mascota?" | lead | Modo 1 inline con clarif "por estancia" | "/noche", link mascotas |
| 16 | Off-hours 3am MX + "Hola" | lead | Modo 1 saludo + nota horario Karina | Escalate, ping Karina |
| 17 | Distress real "estoy en crisis ayúdenme" | lead | Auto-reply 911 | Escalate a Karina o Alex |

### 5.2 Bucket detection unit tests

| # | Input subscriber_id | Expected guest match | Expected bucket |
|---|---|---|---|
| B1 | "5215534956750" (existing guest Erik Tchalla) | matched via phone +525534956750 | VIP_in_stay (arrival 22 dep 25) |
| B2 | "521" + Yosselin's phone | matched | VIP_pre_stay (arrival 28) |
| B3 | "521XXXXXXXXXX" unknown phone | no match | lead |
| B4 | "521XXXXXXXXXX" repeat (last stay <365d) | matched | VIP_repeat |
| B5 | "" empty | no match | lead (defensive) |
| B6 | D1 error simulation | error throw caught | lead (defensive) |

### 5.3 Cache structure tests

- Verifica que `buildSystemPromptBlocksV7` retorna 3 blocks
- Verifica `cache_control` en Tier 1 + Tier 2, NO en Tier 3
- Verifica Tier 2 size >= 2048 tokens (Haiku min)
- Verifica orden: static → per-conv → per-turn

### 5.4 Validator tests

- `pet_fee_per_noche` regex con "$300 por estancia, NO por noche" → NO match (negación)
- Same regex con "$300 por noche" → match
- Same regex con "$300/noche" → match
- Same regex con "300 mxn por estancia" → NO match

---

## §6 · DEFINITION OF DONE (verificable)

| # | Check | Cómo verificar |
|---|---|---|
| DoD-1 | Branch `feat/greeter-v7-warm-vip-aware` existe en rdm-bot | `git branch -a | grep v7` |
| DoD-2 | `packages/agents/greeter/system-prompt-v7.ts` creado, exports `GREETER_SYSTEM_PROMPT_V7`, `PromptContextV7`, `buildSystemPromptBlocksV7` | `grep -l GREETER_SYSTEM_PROMPT_V7 packages/agents/greeter/` |
| DoD-3 | `packages/agents/greeter/handler-v7.ts` creado, recibe blocks array | `grep "blocks: PromptBlock\[\]" packages/agents/greeter/handler-v7.ts` |
| DoD-4 | `apps/worker-bot/src/bucket-detector.ts` creado con `detectBucket()` export | file exists + exports |
| DoD-5 | `apps/worker-bot/src/karina-config.ts` creado con `KARINA_PHONE_E164 = '+52 744 144 1575'` | grep exact string |
| DoD-6 | `apps/worker-bot/src/v7-validator.ts` creado | file exists |
| DoD-7 | `process-tool-use.ts` con bug fixes: NO más número `525570618798` en código | `grep "525570618798" packages/agents/greeter/process-tool-use.ts` retorna vacío |
| DoD-8 | `canary.ts` actualizado: type `PromptVersion = 'v5' \| 'v6' \| 'v7'`, soporta `canary_percent_v7` + force value `'v7'` | grep types + getPromptVersion logic |
| DoD-9 | `run-greeter-v5.ts` con rama promptVersion === 'v7' usando handler-v7 + bucket-detector | grep import handler-v7 |
| DoD-10 | Tests `packages/agents/tests/greeter-v7-system-prompt.test.ts` creados, 17+ golden tests | `wc -l packages/agents/tests/greeter-v7-system-prompt.test.ts` >= 200 |
| DoD-11 | `pnpm test` pasa todos los tests del repo (no regresión v5/v6) | `pnpm test` exit 0 |
| DoD-12 | `pnpm lint` pasa (Biome) | `pnpm lint` exit 0 |
| DoD-13 | `pnpm typecheck` pasa (TS5 strict) | `pnpm typecheck` exit 0 |
| DoD-14 | bot_config seed INSERT canary_percent_v7=0 ejecutado via migration o seed file | D1 query confirma row |
| DoD-15 | PR creada en rdm-bot apuntando a main, descripción incluye link a thread/211 | `gh pr list --head feat/greeter-v7-warm-vip-aware` |
| DoD-16 | Commits semánticos: `feat(greeter): add v7 system prompt with tonal palette`, `feat(bot): add bucket detector`, etc | `git log --oneline feat/greeter-v7-warm-vip-aware ^main` |
| DoD-17 | CC reporta en thread/212-cc-bot-doit-211-greeter-v7-report.md con: archivos creados, tests pass, costos LLM consumidos, blockers (si hubo) | thread/212 existe en rdm-discussion |

---

## §7 · RIESGOS + MITIGATIONS

| # | Riesgo | Probabilidad | Impacto | Mitigation |
|---|---|---|---|---|
| R1 | Haiku 4.5 cache Tier 2 < 2048 tokens → no cachea | Alta | Cost 2x | Pad Tier 2 con full bucket coaching hasta >=2048. Verificar en test |
| R2 | Beta header `extended-cache-ttl-2025-04-11` no soportado por `callAnthropic()` actual | Media | TTL 5min, cost +25% | Si llm-client no soporta, dejar default 5min (sigue cumpliendo cost target) |
| R3 | `phone_e164` lookup falla por formatos raros (sin +, con espacios) | Media | Pierde matches VIP | Test con muestra de 50 phones reales D1. Si <90% match, ampliar normalize logic |
| R4 | Validator `pet_fee_per_noche` regex nuevo introduce nuevos falsos positivos | Baja | Estilístico | Test con 144 turns v6 históricos: deben no flag-ar más que antes |
| R5 | CC implementa pero rompe v5/v6 (regresión) | Media | Producción afectada | Tests anti-regression v5 + v6 deben seguir pasando. Canary v7 = 0% inicial |
| R6 | Bot pierde el `subscriber_name` threading desde ManyChat | Baja | Sin nombre en respuestas | Verifica subscriber_name en ProcessToolUseContext sigue threaded (ya está en v5) |
| R7 | Off-hours detection con DST mexicana | Muy baja | Wrong window 1h | México NO usa DST en Guerrero/Acapulco post-2022. UTC-6 fijo |
| R8 | Karina cel cambia y queda hardcoded | Baja | Mensajes con número incorrecto | Single source of truth en `karina-config.ts`. Fácil de cambiar en 1 file |
| R9 | Bucket detection lento (>50ms) | Baja | Latency total bot >3s | Index hit benchmark. Si lento, considerar KV cache per-conversation |

### Rollback playbook

Si v7 muestra problemas en canary 10% o mayor:

```sql
-- Instant rollback to v6 (no redeploy)
UPDATE bot_config 
SET value = 'v6', updated_at = datetime('now'), updated_by = 'rollback-thread/211' 
WHERE key = 'greeter_prompt_version_force';
```

Si v7 muestra bugs en código (errors throw), `canary_percent_v7 = 0` y la rama v5/v6 toma todo el traffic automáticamente.

---

## §8 · APPENDIX A — Voz real Alex (muestra de 40 host messages)

Patterns extraídos de `bot_messages_inbox WHERE source='host' AND channel='airbnb'`, últimos 30 días:

```
[Saludo cálido directo]
- "Muy buenos días Yoselin !!🤗"
- "Hi Araceli, good afternoon,"
- "Hi Lucero! 🌅"
- "Hola Marycarmen, que gusto saber que ya tienen todo listo"

[Welcome humano]
- "Todo un gusto tenerla de vuelta con su linda familia - bienvenidos!"
- "Estamos encantados de recibirlos 🤗"
- "Welcome! 🌴🐟🌞"

[Decir NO con calidez]
- "Lo siento, es temporada alta y tendremos huéspedes antes y después de ustedes, les pido respetar el horario..."
- "Lo siento, año nuevo ya todo reservado"
- "Buenos dias, lo siento, esa casa que está viendo le queda chica"

[Problema CFE - humor ligero]
- "Ojalá y nuestros amigos de la CFE lo arreglen rápido"
- "Una disculpa por el inconveniente de todas maneras"

[Anfitrión sensorial]
- "estamos en la costa pacífico, brisa garantizada 🌊"
- "Welcome! 🌴🐟🌞"

[Cierre invitacional sin link]
- "¡Te esperamos!" → firma: "— Alexander 🌅"
- "Cualquier otra cosa siempre estoy a sus ordenes!"
- "Any further question is always welcome.."

[Humor cuando aplica]
- "But honestly, why cooking and cleaning dishes during your vacation, come one.. 😁"

[Info concreta inline sin link]
- "El asador es tipo argentino con carbon"
- "Tenemos cupo para hasta 30 en camas, en la app pueden ver la distribución"
- "El servicio de cocina/limpieza ya está incluído sin costo extra"
```

**Emojis signature Alex**: 🤗 🌴 🌅 🌊 🐟 🌞 😁 ❤️ 🆘 📍 🗺️ 🌤️ 🔐 📶

**Cierre signature**: "— Alexander 🌅"

**Estructura típica**:
```
[Greeting personal con nombre]
[línea vacía]
[Contenido: respuesta concreta o disculpa con razón breve]
[línea vacía]
[Cierre cálido invitacional o "Cualquier cosa, aquí estoy"]
```

Few-shots para el prompt v7 deben extraerse de este corpus, NO inventarse.

---

## §9 · APPENDIX B — Comando CC para mañana

```
Modo: DoIt
Spec: rdm-discussion/threads/211-wc-greeter-v7-megarun-spec.md
Branch: feat/greeter-v7-warm-vip-aware (rdm-bot)
Modelo: claude-sonnet-4-6 (per .claude/settings.json)
Effort estimate: 7-9h

Pre-flight:
1. `cd c:/dev/rdm/dev/bot` (or wherever rdm-bot lives locally)
2. `git fetch origin && git checkout main && git pull --rebase`
3. `git checkout -b feat/greeter-v7-warm-vip-aware`
4. `pnpm install` (verify deps)
5. Lee thread/211 completo desde rdm-discussion/threads/

Ejecuta 11 sub-deliverables D1-D11 en orden:
- D1: system-prompt-v7.ts (2h)
- D2: handler-v7.ts (1h)
- D3: bucket-detector.ts (1h)
- D4: karina-config.ts (30 min)
- D5: PromptContextV7 + buildSystemPromptBlocksV7 (45 min)
- D6: run-greeter-v5.ts patch (30 min)
- D7: process-tool-use.ts bug fixes (30 min)
- D8: lead exit gracioso (30 min)
- D9: v7-validator.ts (1h)
- D10: canary.ts patch + bot_config seed (30 min)
- D11: tests anti-regression (1h)

Defaults:
- ASCII shell args, UTF-8 file contents
- Conventional Commits semánticos (feat/fix/chore)
- Git attribution: inherit
- NO ALTER TABLE
- NO commits con secrets
- NO force-push, NO delete branches
- NO auto-merge a main

Si stuck >30 min en cualquier sub-deliverable: HALT, reporta en thread/212.

Al final:
1. `pnpm test && pnpm lint && pnpm typecheck` deben pasar todos
2. `git push origin feat/greeter-v7-warm-vip-aware`
3. `gh pr create` con descripción que linkea a thread/211
4. Crea thread/212-cc-bot-doit-211-greeter-v7-report.md con:
   - Archivos creados (lista)
   - Tests pass count
   - Cost LLM consumido en mega-run (ccusage)
   - Blockers encontrados (si hubo)
   - Smoke test plan sugerido para Alex

NO mergees PR. Alex revisa manualmente.

Anti-patterns CRÍTICOS (NEVER violate):
- Pet fee SIEMPRE "/estancia" NUNCA "/noche"
- Casa Chamán NO surfacar en prompts ni en few-shots
- NO LLM money decisions
- Karina cel `+52 744 144 1575` desde karina-config.ts ÚNICAMENTE (single source)
- NO hardcode número viejo `525570618798` anywhere
```

---

## §10 · FIN DEL SPEC

Ready for CC mega-run. Alex aprueba este thread leyéndolo en mobile. CC ejecuta mañana.

**Cualquier ajuste post-publicación**: thread/212+ amendments, o Alex edita inline si crítico.

— wc, 2026-05-26
