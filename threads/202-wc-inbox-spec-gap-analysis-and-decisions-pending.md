---
thread: 202
author: wc
topic: inbox-spec-gap-analysis-and-decisions-pending
status: pending-alex-decisions
mode: brain (analysis + decision capture)
created: 2026-05-24
related_threads: [196, 197, 198, 199, 200, 201]
related_prs: [167, 169, 170]
next_action: Alex decides §6 items 1-5 → WC redacts execution specs (likely thread/203 backend, thread/204 frontend OR expansion thread/200)
---

# 202 — Inbox spec gap analysis + decisiones pendientes

> **Status:** Nota WC. NO es spec ejecutable. Documenta análisis post deploy thread/199 (PR #170 merged 2026-05-24) y decisiones pendientes Alex antes de redactar threads ejecutables.

---

## §0. TL;DR

Post-merge PR #170 (thread/199 — Bug 1+3+4+5), Alex revisó screenshot real del inbox y notó **features faltantes vs el spec original thread/196**:

1. ❌ **Preview / texto descriptivo** vacío en Tab Reservas (existe en Tab Leads)
2. ❌ **Unread count badge** "N nuevos" ausente en Tab Reservas
3. ❌ **Fechas check-in/check-out** no visibles directamente en row (solo `días estadía` calculado)
4. ❌ **Quick action buttons** (AirBnB, Beds24, /booking, /conversation) — feature pedida ahora, NO en spec original

Causa raíz de #1 + #2: **backend `aggregate.ts` no consulta `bot_messages_inbox`** (mismo problema raíz que Bug 2 thread/200). Se conoce el dataset pero la query no lo lee.

Causa de #3: `InboxRow` contract en spec §4.2.1 NO incluye `check_in`/`check_out` strings, solo `days_to_checkin` derivado.

Causa de #4: Feature nueva, NO formalizada en spec thread/196 (probablemente discutida en 5 iteraciones mockup pero no congelada).

---

## §1. Spec audit — thread/196 vs realidad shipped

### 1.1 InboxRow contract spec §4.2.1

```typescript
type InboxRow = {
  id: string
  subscriber_id: string
  guest_name: string
  display_name_was_garbage: boolean
  property: { roomId: number, name: string } | null
  pax: number | null
  has_pet: boolean
  channels: ('whatsapp' | 'airbnb' | 'booking')[]
  preview: string                   // ← último msg 100 chars
  last_msg_at: string               // ISO
  hours_since_last_response: number
  unread_count: number              // ← badge "N nuevos"
  lifecycle_stage: LifecycleStage
  days_to_checkin: number | null    // ← derivado, NO check_in/check_out raw
  readiness: ReadinessScore | null
  priority_score: number
  detected_lang: 'es' | 'en' | 'de' | null
  is_test_number: boolean
  escalation_reason: string | null
  bot_paused_until: string | null
}
```

**Faltantes vs lo que Alex ahora pide:**
- `check_in: string` (YYYY-MM-DD)
- `check_out: string` (YYYY-MM-DD)
- `total_message_count: number` (opt — para badge "N nuevos / M total")
- `airbnb_confirmation_code: string | null` (para AirBnB quick link)

### 1.2 Backend aggregate.ts — qué consulta vs qué debería

**Hoy (líneas 197-198 de aggregate.ts) para bookings:**
```ts
const lastMsgText = convRow
  ? convRow.history.split('\n').filter((l) => l.startsWith('USER:')).slice(-1)[0]?.slice(5).trim() ?? null
  : null;
```

Solo lee `conversations.history`. Si `convRow` es null (95% bookings activos no tienen WA conv linked), `lastMsgText = null` → `preview = ''`, `unread_count = 0`.

**Lo correcto:** consultar `bot_messages_inbox WHERE booking_id = ?`:
- Last message text → `preview`
- Count messages source='guest' AND read_flag=0 → `unread_count`
- MAX(message_time) → `last_msg_at`
- COUNT(*) total → `total_message_count`

### 1.3 Pipeline data verificado en D1 (queries 2026-05-24)

```
bot_messages_inbox:           476 messages, 66 unique bookings
- AirBnB bookings activos:    ~60 con messages (3-24 msgs cada uno)
- Direct bookings:            0 messages (no aplica este pipeline)
```

Mismo dataset que arregla thread/200 para conversation detail.

### 1.4 Frontend InboxRow.tsx — qué renderiza vs qué falta

**Hoy renderiza:**
- guest_name
- garbage badge (?)
- unread badge (cuando >0, hoy nunca por backend bug)
- test badge
- stay-info: `👥 N 🐶` + `T-3d`
- relative timestamp (`20s`, `2h`, etc)
- preview (cuando string non-empty, hoy vacío Tab Reservas)
- channels badges
- detected_lang badge (si != es)
- ReadinessScore component
- property name badge

**Falta:**
- Fechas check-in/check-out string format
- Quick action buttons (desktop only)
- Total count near unread (e.g. "5 nuevos / 24 total")

### 1.5 Items Alex pidió que NUNCA estuvieron en spec

| Item | Razón |
|---|---|
| Quick action buttons row-level | Mockup phase v3-v5 con Alex no formalizó esto. Probablemente Alex lo asumió implícito o se discutió pero se omitió del spec final |
| Fechas check-in/check-out display | Spec definió `days_to_checkin` como derivado. Alex pide ahora ver fechas raw también |
| "Total mensajes" count | `unread_count` está. Total no. Add minor |

---

## §2. Análisis del "texto descriptivo resumen"

Alex pregunta literalmente: *"En el draft/spec queriamos generar un texto descriptivo resumen. Donde quedó? lees spec que hiciste para inbox nueva."*

**3 interpretaciones posibles:**

### Opción A — `preview` field (último msg truncado 100 chars)

Spec §4.2.1 lo define: `preview: string  // last msg, truncated 100 chars`.

Tab Leads SÍ lo muestra hoy ("Hay algún asesor?", "precios", "Es para una boda"). Tab Reservas NO lo muestra porque backend aggregate no consulta `bot_messages_inbox` (sección 1.2).

**Probabilidad: ALTA.** Es lo más obvio en spec. Fix = arreglar backend aggregate.

### Opción B — AI-generated summary del lifecycle/contexto

Algo tipo: *"T-3, mascotas pendientes, último msg hace 2h preguntando por menú"*.

NO está en spec §4.2.1. Spec tiene LLM suggestion (§4.4.5) pero es para borrador editable de respuesta, no summary.

**Probabilidad: BAJA.** Sería feature totalmente nueva. Costo LLM tokens por row × ~80 rows = ~$0.01-0.03 por load del inbox.

### Opción C — Resumen multi-mensaje del último intercambio guest

Algo tipo: *"Guest pregunta horario check-in + si acepta perro chico. Última respuesta: ninguna."*

NO está en spec. Sería derived feature LLM-based.

**Probabilidad: MEDIA.** Más útil que A pero más caro y complejo.

---

## §3. Opciones de agrupación de specs

### Opción 1 — Expandir thread/200 + crear thread/203

| Thread | Scope | Effort CC |
|---|---|---|
| **200 expandido** | Backend conversation polimórfico + aggregate.ts también lee `bot_messages_inbox` para popular preview/unread/last_msg/total para Tab Reservas | ~100 min (era 75-90) |
| **201 unchanged** | Readiness in-stay override | ~45 min |
| **203 nuevo** | Frontend: fechas check-in/out + quick action buttons + total count badge | ~45 min |

Total: ~3.2 hrs CC, 3 PRs, 3 deploys (2 worker-bot + 1 frontend)

**Tradeoff:** thread/200 crece pero los temas son afines (todo es backend que lee bot_messages_inbox).

### Opción 2 — Todo en thread/200 mega

| Thread | Scope | Effort CC |
|---|---|---|
| **200 mega** | Backend conversation + aggregate fix + Frontend new fields + Quick links + InboxRow contract extension | ~140 min |
| **201** | Readiness | ~45 min |

Total: ~3 hrs CC, 2 PRs, 2 deploys.

**Tradeoff:** PR gigante (~500 LoC), harder review, harder rollback si falla. Pero menos overhead de coordinación.

### Opción 3 — Clean separation (3 threads independientes)

| Thread | Scope | Effort CC |
|---|---|---|
| **200 unchanged** | Backend conversation polimórfico solo (Bug 2) | ~80 min |
| **201 unchanged** | Readiness in-stay (Bug 6) | ~45 min |
| **203 nuevo** | Backend aggregate.ts read bot_messages_inbox + Frontend fechas/links/total + InboxRow contract extension | ~70 min |

Total: ~3.3 hrs CC, 3 PRs, 3 deploys (3 worker-bot + 1 frontend depending on cleanness)

**Tradeoff:** clean rollback path, easier review, 1 PR per concern. WC voto preliminar.

---

## §4. Quick action buttons — propuesta de contrato (si Alex confirma)

**4 botones por row (desktop only, >=1024px):**

| Button | URL pattern | Disponibilidad | Notas |
|---|---|---|---|
| AirBnB | `https://www.airbnb.mx/hosting/reservations/details/{confirmation_code}` | Solo si `channel === 'airbnb'` AND `airbnb_confirmation_code` exists | Requiere agregar `airbnb_confirmation_code` al row contract. Column ya existe en `beds24_bookings` (memoria — migration 0026 agregó). |
| Beds24 | `https://beds24.com/control3.php?action=showBooking&bookid={beds24_booking_id}` | Siempre disponible para bookings | Direct link Beds24 dashboard |
| /booking | `/admin/bookings/{beds24_booking_id}` | Siempre disponible para bookings | Detalle interno. Page existe (PR #155 area). |
| /conversation | `/admin/conversation/{rawId}` | Siempre disponible | Conv detail. Bug 2 lo fixea (thread/200). |

**UI:** iconos pequeños o text-button corto al final del row meta. Click `stopPropagation` para no abrir conversation accidentally.

**Mobile (<1024px):** ocultos (Alex confirmó "solamente desktop view").

---

## §5. InboxRow contract extension — propuesta de diff

Si Alex confirma scope, agregar al backend `InboxRow`:

```diff
 export interface InboxRow {
   id: string;
   subscriber_id: string;
   guest_name: string;
   display_name_was_garbage: boolean;
   property: { roomId: number; name: string } | null;
   pax: number | null;
   has_pet: boolean;
+  check_in: string | null;            // YYYY-MM-DD, null for leads
+  check_out: string | null;           // YYYY-MM-DD, null for leads
+  airbnb_confirmation_code: string | null;  // null if not AirBnB booking
   channels: ('whatsapp' | 'airbnb' | 'booking')[];
   preview: string;
   last_msg_at: string;
   hours_since_last_response: number;
   unread_count: number;
+  total_message_count: number;        // total across history + bot_messages_inbox
   lifecycle_stage: LifecycleStage;
   days_to_checkin: number | null;
   readiness: ReadinessScore | null;
   priority_score: number;
   detected_lang: 'es' | 'en' | 'de' | null;
   is_test_number: boolean;
   escalation_reason: string | null;
   bot_paused_until: string | null;
 }
```

Frontend `inbox-client.ts` también extiende. Helpers nuevos:
- `formatCheckInOut(checkIn: string, checkOut: string): string` — e.g. "28 may - 1 jun"
- `getBookingAirBnBUrl(code: string): string`
- `getBookingBeds24Url(bookingId: number): string`

---

## §6. Decisiones pendientes Alex (BLOQUEADOR para ejecución)

### Decisión 1 — Cuál opción de agrupación

- **(1)** Expandir thread/200 + crear thread/203
- **(2)** Mega thread/200 todo junto
- **(3)** Clean separation: 200 unchanged, 201 unchanged, 203 nuevo ← voto WC

### Decisión 2 — "Texto descriptivo resumen" = ?

- **(A)** `preview` del último mensaje (Opción más probable, fix automático con aggregate fix)
- **(B)** AI-generated summary lifecycle/context (feature nueva, $$ LLM)
- **(C)** Resumen multi-mensaje del último intercambio (feature nueva LLM)

### Decisión 3 — Quick action buttons — confirmar 4 propuestos

Validar URLs propuestas en §4:
- AirBnB ✅ / ❌
- Beds24 ✅ / ❌
- /admin/bookings/[id] ✅ / ❌
- /admin/conversation/[id] ✅ / ❌

¿Algún otro? ¿Algún botón más?

### Decisión 4 — Formato "total mensajes" badge

- **(A)** `5 nuevos / 24 total` (más info)
- **(B)** Solo `5 nuevos` cuando hay, sino vacío (más limpio, status quo spec)
- **(C)** `24 msgs` siempre + `5 nuevos` cuando hay (separados)

### Decisión 5 — Formato fechas check-in/check-out display

- **(A)** `28 may - 1 jun` (corto, español)
- **(B)** `mar 28 may - sáb 1 jun` (con día semana)
- **(C)** `2026-05-28 → 2026-06-01` (ISO completo)
- **(D)** Solo en hover/tooltip, no inline en row (ahorrar espacio)

---

## §7. Hard anti-patterns a respetar (recordatorio)

Independiente de la opción elegida:

- ❌ NO Casa Chamán (roomId 679176) en ningún UI / link / mention
- ❌ NO LLM money decisions (cualquier feature con $ recommendation autonomous)
- ❌ NO pet fee como `/noche` — siempre `/estancia`
- ❌ NO ALTER TABLE durante multi-CC concurrent (si se agregan columnas, hacer pre-merge ventana segura)
- ❌ NO commits con secrets
- ❌ NO production deploys viernes 5pm+
- ✅ Beds24 sync mode siempre Prices & Availability ONLY
- ✅ apps/worker-bot deploy manual post-merge (no auto en GH Actions)

---

## §8. Plan post-decisión Alex

Cuando Alex confirme §6 items 1-5:

1. WC redacta thread ejecutable(s) según opción elegida
2. CC ejecuta en orden:
   - thread/200 (Bug 2 — ya redactado, listo o expandido según opción)
   - thread/201 (Bug 6 — ya redactado, sin cambio)
   - thread/203 (gaps — a redactar post-decisión)
3. Cada PR: Alex review → merge → manual worker-bot deploy si aplica → smoke test visual
4. Update STATE.md final post all merged

---

## §9. References

- thread/196: Spec original inbox redesign (33-46h CC estimated, 5 iteraciones mockup)
- thread/198: Hotfix CORS post-deploy (PR #169 merged)
- thread/199: Display fields + CSS + readiness compact (PR #170 merged)
- thread/200: Conversation endpoint polimórfico Bug 2 (ready, awaiting CC execution)
- thread/201: Readiness in-stay override Bug 6 (ready, awaiting CC execution)
- D1 query investigation 2026-05-24: 0/75 bookings activos linked a conversations; 476 messages OTA en bot_messages_inbox; pipeline AirBnB vs WhatsApp desacoplado
- Screenshot verification 2026-05-24 ~08:00 UTC: Alex confirmó visualmente bugs 1+3+4+5 fixed in production. Bugs 2+6 + gaps §0 still visible
- Memorias #25, #26, #27: inbox redesign shipped post thread/196, Wave 1.5 followups identificados
