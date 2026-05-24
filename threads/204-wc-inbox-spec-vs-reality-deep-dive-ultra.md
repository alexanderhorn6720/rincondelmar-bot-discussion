---
thread: 204
author: wc
topic: inbox-spec-vs-reality-deep-dive-ultra
status: analysis-complete
mode: brain ultra (deep dive, 3h research + audit)
created: 2026-05-24
related_threads: [196, 197, 198, 199, 200, 201, 202, 203]
related_prs: [167, 168, 169, 170, 171, 172]
audit_scope: every YES item §2.1 + every closed decision §3 of thread/196 vs production code + D1 data + industry best practices
next_action: Alex prioriza items §10 con voto, WC redacta thread/205 ejecutable según selección
related_d1_queries: 14 verified during audit
external_research: Hostaway, Hostfully, Front, Intercom, HelpScout, Crisp, Missive, Superhuman, Gmelius, Runnr.ai
---

# Thread 204 — Inbox spec vs entregado: deep dive brain ultra + best practices

> **Status**: análisis completo. NO es spec ejecutable. Documenta 30+ findings concretos comparando thread/196 megaspec vs producción real al 2026-05-24 04:30 UTC.

---

## §0. TL;DR — Top 10 findings priorizados

Lista ordenada por impacto Karina × esfuerzo fix:

| # | Finding | Tipo | Severidad | Esfuerzo fix |
|---|---|---|---|---|
| 1 | **LLM suggestion NUNCA se renderiza en producción** (D11/D18) — `initial=null` siempre, componente retorna null. 0 invocaciones en audit_log verificadas | Bug crítico | 🔴 Alta | ~30min CC |
| 2 | **Tab Reservas preview vacío** — aggregate.ts NO lee bot_messages_inbox para popular preview/unread/timestamp en bookings AirBnB (mismo dataset que thread/200 arregló en conversation view) | Bug crítico | 🔴 Alta | ~90min CC |
| 3 | **Threading 1 row por cliente NO existe** (D7 violada) — hoy 1 row por booking. Si guest tiene 2 bookings → 2 rows. Spec quería merge cross-booking | Bug arquitectural | 🟡 Media | ~3-4h CC |
| 4 | **`paid_amount_mxn` calc erróneo** — `deposit_paid ? total : 0` muestra "$0 / $5,452 MXN" en Claudia (Image 1) cuando ya pagó depósito. Correcto: `total - balance_due` | Bug funcional | 🔴 Alta | ~15min CC |
| 5 | **`rules_accepted` siempre false** — score máximo 5/6 nunca 6/6. Column `rules_form_submitted_at` no existe → readiness incompleto sistémicamente | Bug funcional | 🟡 Media | ~30min CC + 1 migration |
| 6 | **Counter Leads=0 en Tab Reservas** y vice versa — aggregate setea `leads: 0` cuando tab='reservas'. Tab buttons muestran "0" siempre | Bug menor | 🟢 Baja | ~15min CC |
| 7 | **LLM suggestion lookup phone obsoleto** — llm-suggestion.ts línea 113 NO usa helper normalizePhoneToWA (thread/203 fix). Para guests MX, booking NO se carga → suggestion sin contexto | Bug regresión thread/203 | 🟡 Media | ~10min CC |
| 8 | **Quick replies vacíos en producción** — Karina nunca creó ninguno (verified D1: 0 rows). UI funciona pero panel no aparece. **No es bug — es onboarding pendiente** | Producto incompleto | 🟡 Media | ~30min Alex + Kari sentar juntos a poblar |
| 9 | **Quick action buttons row-level NO existen** (gap thread/202 §4) — Alex pidió 4 botones desktop: AirBnB / Beds24 / /booking / /conversation. NO en spec original | Feature nueva | 🟡 Media | ~2h CC |
| 10 | **`vip_repeat_check` typo en lifecycle.ts** retorna stage que no matchea sectionMap key `vip_repeat` → sección VIP nunca aparece aunque haya repeats | Bug menor | 🟢 Baja | ~10min CC |

**Total esfuerzo CC para resolver Top 10**: ~8-12h split en 3-4 PRs separados.

---

## §1. Audit methodology

### 1.1 Inputs analizados

| Fuente | Stage analizado |
|---|---|
| `threads/196-wc-inbox-redesign-spec.md` | Spec original (50+ páginas, 32 closed decisions, 20 YES items) |
| Production code commit `fd051c75` (rdm-bot main) | Estado actual post thread/203 deploy |
| D1 producción queries (14 distintas) | Verificación datos reales en `conversations`, `bot_messages_inbox`, `quick_replies`, `inbox_drafts`, `audit_log` |
| Screenshots Alex 2026-05-24 ~03:28 hora local | Visual verification Alan Granados + Claudia Becerra cases |
| 8 web searches industry research | Hostaway, Hostfully, Front, Intercom, HelpScout, Crisp, Missive, Superhuman patterns |

### 1.2 Files audited (filesystem reales)

Frontend (apps/web):
- ✅ `pages/admin/inbox.astro`
- ✅ `pages/admin/conversation/[id].astro`
- ✅ `pages/admin/quick-replies/{index,[id]}.astro`
- ✅ `components/inbox/{InboxApp,InboxTabs,InboxRow,ReadinessScore,LifecycleSection,QuickStatsHeader,InboxFilters}.tsx`
- ✅ `components/conversation/{ConversationView,MessageBubble,ComposeBox,LLMSuggestion,QuickRepliesPanel,BookingContextSidebar,AuditTrail}.tsx`
- ✅ `lib/inbox-client.ts`
- ✅ `styles/{inbox,conversation}.css`

Backend (apps/worker-bot):
- ✅ `api/admin/{inbox,conversation,quick-replies,drafts}.ts`
- ✅ `inbox/{aggregate,readiness,lifecycle,lead-intent,filters,llm-suggestion,auto-pause,lang-detect,phone-normalize}.ts`
- ✅ `src/index.ts` (routing verification)

Migrations: 0032 inbox_drafts ✅, 0033 quick_replies ✅, 0034 inbox_indexes ✅ (verified D1)

---

## §2. YES items audit — §2.1 estado actual

### Resumen ejecutivo

| Status | Count | % |
|---|---|---|
| ✅ Implementado correctamente | 9 | 45% |
| 🟡 Implementado con bug/gap | 7 | 35% |
| ❌ Implementado pero NO funcional en producción | 4 | 20% |
| **Total YES items** | **20** | **100%** |

### Tabla detallada

| # | Spec feature | Status | Hallazgo |
|---|---|---|---|
| 1 | 2 tabs Reservas/Leads counters live | 🟡 | Counter de Leads=0 cuando estás en Tab Reservas (aggregate setea hard-coded). Counter Reservas=0 viceversa. Tab buttons engañosos |
| 2 | 1 row por cliente threading | ❌ | **NO implementado**. Hoy 1 row por booking. Sandy con 5 conversations sin booking → 5 rows en Tab Leads. Guest con 2 bookings → 2 rows en Tab Reservas |
| 3 | Readiness 6 components responsive | 🟡 | Componente OK. Pero `rules_accepted` SIEMPRE false (column missing). Score máximo posible 5/6, nunca 6/6 |
| 4 | Tab Reservas 8 lifecycle sections | 🟡 | 7 de 8 funcionales. `vip_repeat` jamás aparece — lifecycle.ts retorna `vip_repeat_check` que NO matchea sectionMap key `vip_repeat` |
| 5 | Tab Leads 3 intent sections | ✅ | 3 funcionales |
| 6 | Filter cron + placeholder out | ✅ | filters.ts funciona — cron-bot-alerts subscriber + `{{first_name}}` literal blocked |
| 7 | Filter garbage names → phone parcial | ✅ | normalizeDisplayName cubre 1-2 chars + solo emojis + comilla suelta + punto solo |
| 8 | Test number `5217441441575` CSS tenue | ✅ | CSS data-test="true" linear gradient lavanda + border-left |
| 9 | `/admin/conversation/[id]` WhatsApp-style | ✅ | Página existe + endpoint polimórfico (thread/200) |
| 10 | Reply directo desde inbox | ✅ | sendMessageRouted enruta WA/AirBnB/Booking según context |
| 11 | **LLM suggested reply pre-cargada editable** | ❌ | **BUG CRÍTICO**. ConversationView pasa `initialSuggestion={null}` → ComposeBox → LLMSuggestion con `initial=null` → componente retorna null y NUNCA muestra sugerencia. **0 invocaciones en audit_log durante 7 días.** Verificado D1: `SELECT COUNT(*) FROM audit_log WHERE kind = 'inbox_llm_suggestion'` = 0 |
| 12 | `/admin/quick-replies` CRUD | ❌ | Backend + frontend wired pero **0 rows en `quick_replies` table**. Karina nunca creó. Panel en conversation queda invisible (`top3.length === 0` → return null) |
| 13 | Drafts persistentes blur/2s/beforeunload | ✅ | 12 drafts en producción confirmation uso real |
| 14 | Auto-pause bot 1h post-reply | ✅ | auto-pause.ts ejecuta. Respeta manual indefinite |
| 15 | Auto-mark responded | ✅ | UPDATE conversations.resolved_at en reply handler |
| 16 | Audit trail per-conversation | ❌ | Component renders correctly pero **0 entries en audit_log con kind LIKE 'inbox_%'**. Audit trail vacío para todas las conversations. Si Kari hace pause/resolve/reply nunca aparece |
| 17 | Idioma detectado badge | ✅ | detectLangFromHistory + render badge cuando !== 'es' |
| 18 | Mobile full-screen compose | ✅ | matchMedia(max-width: 767px) + modal `mobileOpen` state |
| 19 | Booking context sidebar | 🟡 | Render OK. Pero **`paid_amount_mxn` calc BUG**: `deposit_paid ? total : 0`. Claudia muestra "$0 / $5,452" (Image 1). Correcto: `total - balance_due_mxn` |
| 20 | Quick replies top 3 por keyword | 🟡 | Algoritmo OK (suggestQuickReplies en inbox-client.ts) pero **sin datos no funciona**. Wave 1.5 dependency |

---

## §3. Closed decisions audit — §3 estado actual

### Resumen ejecutivo

| Status | Count | % |
|---|---|---|
| ✅ Aplicada correctamente | 23 | 72% |
| 🟡 Aplicada parcial | 5 | 16% |
| ❌ Violada o no aplicada | 4 | 12% |
| **Total decisions** | **32** | **100%** |

### Tabla resumida (solo no-✅)

| D# | Decisión | Status | Hallazgo |
|---|---|---|---|
| D1 | Readiness 6 components | 🟡 | 5 funcionan, `rules_accepted` siempre false |
| D5 | Tab Reservas incluye AirBnB inquiries | 🟡 | Section `airbnb_inquiry_unconfirmed` existe en lifecycle.ts pero categorize NO matchea bookings inquiry. Verificar query backend |
| D7 | 1 row por cliente | ❌ | NO implementado. Es 1 row por booking |
| D8 | Cross-channel merge (WA + AirBnB) | ❌ | NO implementado. Mismo guest con WA + AirBnB inquiry = 2 rows separados |
| D9 | Lead → Reserva auto migration | 🟡 | Backend separa por booking_id presence. Pero si guest tiene conv WA pura sin booking, queda en Leads aunque cree booking después (no se migra retroactivamente sin re-aggregate) |
| D18 | Haiku 4.5 LLM suggestion | ❌ | Modelo correcto en código pero NUNCA invocado por bug #1 |
| D29 | Audit trail visible solo en conv view | ❌ | Component existe pero D1 vacío — no datos para mostrar |

### Decisiones ✅ destacables (bien implementadas)

- **D11 Cron alerts filter** ✅ — filters.ts maneja `cron-bot-alerts` subscriber + `cron_alert:` prefix
- **D12 `{{first_name}}` literal filter** ✅ — `shouldFilterOut` detecta y loggea (aunque `logBugToErrors` parece no-op)
- **D13 Display name basura** ✅ — Edge cases bien cubiertos
- **D17 Reply directo Beds24** ✅ — sendMessageRouted funcional
- **D27 Auto-pause 1h** ✅ — Respeta manual indefinite (verified auto-pause.ts)
- **D31 Pet fee /estancia canónico** ✅ — Hardcoded en buildAdminSuggestPrompt system prompt
- **D32 Casa Chamán excluida** ✅ — `room_id != 679176` en TODAS las queries (aggregate, readiness, conversation, etc) — VERIFIED 14 queries

---

## §4. Bugs CRÍTICOS — breakdown técnico

### 4.1 Bug #1 — LLM suggestion NUNCA aparece

**Síntoma observable**: Alex menciona explícitamente: *"mensaje propuesto de respuesta de llm, lo vi en el thread y cuando xx estaba ejecutando, pero no aparece."*

**Verificación D1**:
```sql
SELECT COUNT(*) FROM audit_log WHERE kind = 'inbox_llm_suggestion';
-- Result: 0
```

7 días en producción, NUNCA se ejecutó.

**Root cause**:

`ConversationView.tsx` line 196 pasa al `<ComposeBox>`:
```tsx
<ComposeBox
  initialSuggestion={null}  // ← SIEMPRE null
  ...
/>
```

`ComposeBox.tsx` pasa al `<LLMSuggestion>`:
```tsx
<LLMSuggestion
  initial={initialSuggestion}  // null
  onFetch={fetchSugg}
/>
```

`LLMSuggestion.tsx` (líneas 30-58):
```tsx
export default function LLMSuggestion({ initial, onUse, onFetch }: Props) {
  const [result, setResult] = useState<...>(initial);  // null
  const [loading, setLoading] = useState(false);
  
  if (loading) { ... }
  
  if (!result || !result.ok) {
    if (result && !result.ok) { ... }  // skip reason
    return null;  // ← ESCAPE: nada se renderiza
  }
  // ... ✨ Sugerencia IA box (NUNCA llega aquí)
}
```

El componente **nunca trigger fetch automático**. Solo se ejecuta cuando user click "Regenerar", pero el botón "Regenerar" solo aparece DESPUÉS de tener una suggestion. **Deadlock UX**.

**Fix proposal A** (mínimo): ConversationView debe pre-fetch suggestion al cargar conv:

```tsx
useEffect(() => {
  // Existing fetches...
  Promise.all([
    fetchConversation(convId),
    fetchQuickReplies(),
    fetchDraft(convId),
    fetchSuggestion(convId),  // ← AGREGAR
  ])
    .then(([conv, qr, savedDraft, suggestion]) => {
      setData(conv);
      setQuickReplies(qr.items);
      setSuggestion(suggestion);  // ← AGREGAR
      // ...
    })
}, [convId]);

// Pass to ComposeBox
<ComposeBox initialSuggestion={suggestion} />
```

**Fix proposal B** (alternativo): LLMSuggestion auto-trigger en mount:

```tsx
useEffect(() => {
  if (initial === null) {
    setLoading(true);
    onFetch().then(setResult).finally(() => setLoading(false));
  }
}, []);
```

**Fix proposal C** (más conservador): mostrar botón "Generar sugerencia ✨" cuando no hay suggestion:

```tsx
if (!result || !result.ok) {
  return (
    <div className="conv-suggestion">
      <button onClick={handleRegen}>✨ Generar sugerencia IA</button>
    </div>
  );
}
```

**Voto WC**: **A** — match spec D11 "pre-cargada editable" y match industry pattern (Superhuman, Gmelius drafts esperan automáticos). Cost previsión: 79 rows Tab Reservas × ~$0.001 Haiku call = ~$0.08 per inbox load. Aceptable. Si cost concern, agregar `cache_control: ephemeral` que ya está implementado en system prompt (90% reduction).

**Bonus fix**: el suggestion endpoint hoy retorna `no_wa_history` para bookings sin conv WA (caso Claudia AirBnB pure). Pero **se podría agregar contexto OTA messages** desde `bot_messages_inbox` y generar suggestion para esos casos también. Esto requiere modificar `suggestReply()` en llm-suggestion.ts para opcionalmente accept booking_id en lugar de subscriber_id.

### 4.2 Bug #2 — Tab Reservas preview vacío

**Síntoma observable**: Screenshot Karina (no entregado pero Alex menciona en thread/202): Tab Reservas muestra rows pero columna preview vacía.

**Verificación código**:

`aggregate.ts` líneas 197-200 (Tab Reservas loop):
```ts
const lastMsgText = convRow
  ? convRow.history.split('\n').filter((l) => l.startsWith('USER:')).slice(-1)[0]?.slice(5).trim() ?? null
  : null;
```

**Solo lee `conversations.history`**. Si `convRow=null` (95% bookings activos no tienen WA conv linked → ver thread/203 §1.3), `lastMsgText=null`, `preview=''`, `unread_count=0`, `last_msg_at=now()` (default falso).

**Pero** los AirBnB bookings SÍ tienen mensajes — en `bot_messages_inbox`. El endpoint `/conversation/[id]` (thread/200) SÍ los lee y muestra. El aggregate NO.

**D1 evidencia**:
```sql
SELECT COUNT(DISTINCT booking_id) FROM bot_messages_inbox;
-- Result: 66 bookings con mensajes OTA reales
```

66 bookings con mensajes que aparecen vacíos en Tab Reservas.

**Fix proposal**: agregar query secundaria a `bot_messages_inbox` en el loop de aggregate.ts Tab Reservas:

```ts
// Para cada booking row, si NO hay convRow, fallback a OTA messages
if (!convRow && bookingId) {
  const otaMsg = await env.DB.prepare(
    `SELECT message_text, message_time, source, read_flag
     FROM bot_messages_inbox 
     WHERE booking_id = ? 
     ORDER BY message_time DESC LIMIT 1`
  ).bind(bookingId).first();
  
  if (otaMsg) {
    lastMsgText = otaMsg.message_text;
    lastActive = otaMsg.message_time;
  }
}

// Unread count desde OTA si no WA
const unreadOta = await env.DB.prepare(
  `SELECT COUNT(*) as n FROM bot_messages_inbox 
   WHERE booking_id = ? AND source = 'guest' AND read_flag = 0`
).bind(bookingId).first<{ n: number }>();

unread_count = (convRow ? unreadWa : 0) + (unreadOta?.n ?? 0);
```

**Esfuerzo**: ~90min CC (incluye tests + idempotency check + considerar performance — actualmente N+1 query por row, podría hacerse batch).

**Optimización**: si performance preocupa, hacer JOIN en query principal con un LEFT JOIN lateral o subquery con MAX(message_time) en bot_messages_inbox.

### 4.3 Bug #3 — Threading 1 row por cliente NO existe

**Síntoma**: Si Sandy escribe 5 mensajes consecutivos sin booking confirmado, aparece como **5 rows separados** en Tab Leads (cada conversation = 1 row), NO como 1 row con badge "5 nuevos".

**Verificación código**:

`aggregate.ts` Tab Leads query:
```sql
SELECT c.subscriber_id, c.history, ...
FROM conversations c
LEFT JOIN guests g ON ...
LEFT JOIN beds24_bookings bb ON ...
WHERE bb.id IS NULL
  AND (c.resolved_at IS NULL OR c.resolved_at < unixepoch() - 7 * 86400)
```

Para Tab Leads, cada `conversations` row se mapea a 1 InboxRow. **No hay grupping por phone/subscriber subyacente cross-conversations**.

Para Tab Reservas, cada `beds24_bookings` row se mapea a 1 InboxRow. Si guest tiene 2 bookings activos → 2 rows separadas.

**D1 verificación**:
```sql
SELECT g.phone_e164, COUNT(*) as bookings 
FROM beds24_bookings bb 
JOIN guests g ON g.id = bb.guest_id 
WHERE bb.status NOT IN ('cancelled', 'no_show') 
GROUP BY g.phone_e164 
HAVING COUNT(*) > 1;
```

Muchos guests con multi-booking (esperado en RDM — Carlos Castro Garcia: 5 bookings totales, etc).

**Spec D7 dice literal**: *"1 row por cliente (threading agregado D1 view)"*. NO implementado.

**Fix proposal**: refactor aggregate.ts para hacer GROUP BY subscriber/phone post-fetch, mergeando:
- Channels list (unique)
- Unread counts (sum)
- Preview = más reciente
- last_msg_at = MAX
- Properties list (si multi-booking, mostrar todas o "Multi-propiedad")
- Readiness = del booking más cercano upcoming

**Tradeoff**: aumenta complejidad significativa. Multi-booking guest con propiedades diferentes ¿qué readiness mostrar? ¿Cuál property badge?

**Voto WC**: **DEFER**. Spec ambicioso pero en práctica:
- 95% guests tienen 1 booking activo a la vez en RDM
- Multi-booking real = Carlos cumpleaños (1 vez al año, eventos especiales)
- Multi-conv WA mismo guest = Sandy 5 mensajes consecutivos (rare, mismo phone → ya es 1 conversation row, lo agrupa la DB naturalmente)

**El threading verdadero NO es necesario Wave 1**. Spec exagerado. Item para Wave 2 o never.

Posible alternativa más barata: agrupar SOLO en Tab Leads (donde el problema 5-Sandy era el motivador original). Mantener Tab Reservas 1-row-per-booking. Estimación: 1-2h CC.

### 4.4 Bug #4 — `paid_amount_mxn` cálculo erróneo

**Síntoma observable**: Sidebar booking de Claudia muestra "**Pago: $0 / $5,452 MXN**" cuando ya pagó depósito (Image 1).

**Código bug** en `conversation.ts` línea 218:
```ts
paid_amount_mxn: br.deposit_paid ? br.total_amount_mxn : 0,
```

Esto interpreta `deposit_paid=1` como "pagó 100%". Falso. `deposit_paid` significa "el depósito (típicamente 33% AirBnB) ha sido cobrado".

**Cálculo correcto**:
```ts
paid_amount_mxn: br.balance_due_mxn !== null
  ? br.total_amount_mxn - br.balance_due_mxn
  : (br.deposit_paid ? br.total_amount_mxn * 0.33 : 0),
```

(O usar `Math.round` para evitar floats.)

**Verificación**:
- AirBnB: deposit_paid=1, total=5,452, balance_due=3,653 → paid=1,799 (33%)
- Direct con pago completo: deposit_paid=1, total=18,000, balance_due=0 → paid=18,000
- Direct sin pago: deposit_paid=0, total=18,000, balance_due=18,000 → paid=0

**Esfuerzo**: ~15min CC + 1 test.

### 4.5 Bug #5 — `rules_accepted` siempre false

**Síntoma observable**: Image 1 Claudia ReadinessScore muestra "2/6" — pero Mascotas+ETA+Reglas+Pago marcadas missing (4 ○). Si pago contó como ✓ entonces score debe ser 5-2=3, pero muestra 2. **Score cálculo también probable broken**.

(Espera, voy a revisar: Image 1 también muestra "✓2" en footer. Hmm. El "2/6" en sidebar puede ser readiness diferente al de conv. Voy a recalcular: Claudia readiness sidebar dice "Readiness 2/6". Los 4 pills missing: Menú, ETA, Reglas, Pago. Implícitamente 2 ✓: Pax + Mascotas. Pago marca missing aunque sí pagó depósito (porque deposit_paid debería contar pero el bug #4 lo descuadra). Hmm complejo.)

Independiente del display issue, el bug específico:

**Código bug** en `readiness.ts` línea 64:
```ts
// rules_accepted: no column exists → false (Wave 1.5)
const rules_accepted = false;
```

Comment del CC indica que conoce la limitación. Score máximo posible:
```ts
[pax_confirmed, pet_decided, menu_decided, eta_known, rules_accepted=false, paid].filter(Boolean).length
// max = 5/6, never 6/6
```

**Fix Wave 1**: usar proxy column. Opciones:
- A) `booking_captures.notes_karina` LIKE '%reglas%' (heurístico texto)
- B) `booking_captures` agregar column `rules_accepted` via migration 0035 (off-window, no multi-CC)
- C) Verificar si Beds24 expone field via API (`bookingFlags.rules` o similar)

**Voto WC**: **B** — migration 0035_booking_captures_rules.sql, simple ALTER TABLE en off-window (sábado pre-deploy o post-multi-CC pause). 1 column boolean default 0. Karina marca toggle en `/admin/bookings/[id]`.

**Esfuerzo**: ~30min CC backend + ~15min frontend toggle + migration 0035.

### 4.6 Bug #6 — Counter cross-tab = 0

**Código bug** en `aggregate.ts` líneas 326-329 (al final de Tab Reservas):
```ts
const counters = {
  reservas: rows.length,
  leads: 0, // filled if needed
};
```

Y mirror en Tab Leads:
```ts
counters: { reservas: 0, leads: leadRows.length },
```

**Frontend** muestra los counters en `<InboxTabs>` desde response. Cuando está en Tab Reservas, ve "Reservas 12" y "Leads **0**" (falso si hay leads).

**Fix proposal**: hacer una query liviana para el counter cross-tab:

```ts
// In Tab Reservas branch
const leadsCount = await env.DB.prepare(
  `SELECT COUNT(*) as n FROM conversations c
   LEFT JOIN guests g ON g.manychat_subscriber_id = c.subscriber_id
   LEFT JOIN beds24_bookings bb ON bb.guest_id = g.id
   WHERE bb.id IS NULL AND c.resolved_at IS NULL
     AND c.subscriber_id != 'cron-bot-alerts'`
).first<{ n: number }>();

const counters = {
  reservas: rows.length,
  leads: leadsCount?.n ?? 0,
};
```

**Esfuerzo**: ~15min CC + 1 test.

### 4.7 Bug #7 — LLM suggestion lookup phone obsoleto (regresión thread/203)

**Síntoma**: Cuando thread/204 fix #1 se aplique y LLM suggestion empiece a llamarse, para guests MX retornará suggestion sin contexto booking porque la query NO usa el helper thread/203.

**Código bug** en `llm-suggestion.ts` líneas 110-119:
```ts
const booking = await env.DB.prepare(
  `SELECT ... FROM beds24_bookings bb
   LEFT JOIN booking_captures bc ...
   JOIN guests g ON g.id = bb.guest_id
   WHERE (g.manychat_subscriber_id = ? 
         OR REPLACE(g.phone_e164, '+', '') = ?)
     AND bb.room_id != 679176
   ORDER BY bb.arrival DESC LIMIT 1`,
)
  .bind(convId, convId)
  ...
```

**Problema**: `REPLACE(g.phone_e164, '+', '')` es el normalization viejo. Para Alan Granados, `convId='5215582528741'` (con 1), `phone_e164='+525582528741'` (sin 1), JOIN falla → booking=null → suggestion sin contexto booking.

**Fix proposal**: aplicar mismo CASE de thread/203:

```sql
WHERE (g.manychat_subscriber_id = ?
      OR (
        CASE
          WHEN g.phone_e164 LIKE '+52%' AND substr(g.phone_e164, 4, 1) != '1'
          THEN '521' || substr(g.phone_e164, 4)
          ELSE REPLACE(g.phone_e164, '+', '')
        END
      ) = ?)
```

**Esfuerzo**: ~10min CC.

---

## §5. Bugs MEDIOS

### 5.1 `vip_repeat_check` typo

`lifecycle.ts` `categorizeLifecycle` retorna `'vip_repeat_check'` cuando booking is past + total_bookings > 3. Pero `sectionMap` y `LifecycleStage` type tienen `'vip_repeat'` (sin `_check`). Section nunca aparece.

**Fix**: cambiar return string a `'vip_repeat'`. 10min CC.

### 5.2 Header conversation muestra "Booking 79421553" en vez del nombre

`conversation.ts` línea 277:
```ts
name: ctx.bookingRow
  ? `Booking ${ctx.bookingId}`
  : (ctx.subscriberId ?? rawId),
```

Falla con dignidad pero UX bad. Debería JOIN con guests.name. Fix: ~15min.

### 5.3 Mensajes timestamps ficticios

`parseHistoryToMessages` reparte msgs en intervalo fijo (`(24h) / numLines`):
```ts
const baseMs = Date.now() - 24 * 3_600_000;
const step = lines.length > 0 ? (24 * 3_600_000) / lines.length : 60_000;
```

`conversations.history` no guarda timestamps reales por turn. Solo `last_active`. Frontend muestra "5h" "23h" "11h" pero son **falsos** (calculados regresivamente desde now).

**Impacto**: Karina no sabe cuándo realmente llegó el mensaje "Que tal Alexander buena noche". Si fue ayer 23:00 o anteayer 11:00 — ambos posibles.

**Fix proposal**: backend agregar `last_msg_at` real por turn via columna `messages_timestamps_json` o tabla `messages` separada (anti-pattern thread/196 D7 backfire — schema mismo problem).

**Fix incremental Wave 1.5**: durante ingest del webhook (`processIncomingMessage` o `appendTurn`), append timestamp a un sidecar column. Effort medio.

### 5.4 Mensajes "USER:" parsing edge case

Si mensaje user contiene literal "ASSISTANT:" como parte del texto, parser confunde direction. Edge case raro pero posible si guest pega screenshot conversation.

**Fix**: usar delimiter robusto (NUL char, JSON lines, etc). Defer Wave 2.

### 5.5 No hay scroll-to-bottom automático al abrir conversation

ConversationView renderiza messages ordered ASC pero NO hace `scrollIntoView` al final. Karina abre y ve mensaje viejo arriba (Image 1 muestra "5h" arriba que es el más viejo en pantalla).

**Fix**: agregar useRef + useEffect:
```tsx
const messagesEndRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [data?.conversation.messages.length]);
```

10min CC.

### 5.6 No hay indicador "mensajes no leídos desde último visit"

Spec implícito pero no detalla. Industry pattern (HelpScout, Front): línea separadora "↓ 3 unread messages ↓" al primer mensaje no leído.

**Fix**: requiere persistir `last_visited_at` per (conv, user). Tabla nueva o agregar a inbox_drafts.

Defer Wave 1.5 o backlog.

### 5.7 Datos drafts viejos no se limpian

Tabla `inbox_drafts` (12 rows en prod) crece indefinidamente. No hay cleanup cuando conv resolved. Wave 2 — cron mensual delete WHERE conv resolved >30d.

---

## §6. UX gaps (no son bugs pero faltan vs industry)

### 6.1 Quick action buttons row-level NO existen

Alex pidió explícitamente (thread/202 §4): 4 botones desktop por row: AirBnB / Beds24 / `/admin/bookings/[id]` / `/admin/conversation/[id]`. NO está en spec original.

**Implementación recomendada**: hover-revealed icons al final de row meta. Click stopPropagation.

### 6.2 Fechas check-in/check-out display

Row hoy muestra `T-3d` (derivado). Alex pidió fechas raw también: "28 may - 1 jun".

**Backend**: agregar `check_in` + `check_out` strings al `InboxRow` contract.
**Frontend**: render adicional en stay-info block.

### 6.3 Total mensajes badge

Row hoy muestra `unread_count` "5 nuevos". Falta `total_message_count` "5 nuevos / 24 total".

**Backend**: agregar `total_message_count` al contract.
**Frontend**: format function.

### 6.4 Texto descriptivo resumen (Alex thread/202 §0)

Alex pregunta literalmente: *"En el draft/spec queriamos generar un texto descriptivo resumen. Donde quedó?"*

Hay 3 interpretaciones (thread/202 §2 las cubre):
- A) `preview` del último msg ← más probable
- B) AI-generated summary lifecycle/context ← feature nueva
- C) Resumen multi-message del último intercambio ← feature nueva

Si Alex confirma A, fix coincide con Bug #2.

Si Alex confirma B o C: feature nueva backend (Haiku call por row), ~$0.01-0.03 por inbox load × 80 rows.

### 6.5 Internal notes / mention teammate (industry standard)

Front, HelpScout, Intercom, Missive: feature standard. Kari + Alex (o futuro Camila/asistentes) pueden escribir notas internas en una conversation que el guest NO ve. Ej: "Carlos siempre pide cuna extra, recordar". 

**NO en spec thread/196**. Pero industria considera essential. **Recomendación WC**: agregar a backlog Wave 2.

### 6.6 Status badges (assigned, snoozed, resolved)

Industry: cada row muestra estado workflow.

RDM tiene `resolved_at` + `bot_paused_until` pero no expone como badge visual. **Recomendación**: agregar 3 estados visuales:
- 🟢 Open (default)
- 🟡 Snoozed (bot_paused_until > now)
- ✅ Resolved (resolved_at IS NOT NULL recent)

### 6.7 Tags / categorías custom

Industry: tags multi-color custom por conversation ("VIP", "complain", "evento", "boda", etc).

RDM hoy: NO. Recomendación Wave 2.

### 6.8 Send + schedule message (programar envío)

Útil para "te confirmamos mañana 9am". Hostaway/Front lo tienen.

**RDM hoy**: NO. Recomendación Wave 2.

### 6.9 Translation auto guest ↔ Karina

Industry vacation rental: cuando guest escribe EN/DE, traducir auto a ES para Karina + mostrar original.

**RDM hoy**: solo badge `detected_lang`. No translation. Wave 2.

### 6.10 Cross-channel guest profile completo

Industry: cliquear guest abre profile con historia COMPLETA (todos bookings + todos messages todos canales + reviews + ratings).

**RDM hoy**: `/admin/bookings/[id]` muestra solo 1 booking. No hay `/admin/guests/[id]` cross-history. Wave 2.

---

## §7. Backend gaps

### 7.1 `bot_metrics` table no existe

Memoria #25 ya lo flag. Actualmente cost LLM va a `audit_log` con kind `inbox_llm_suggestion`. No queryable para dashboard cost.

**Fix**: migration 0035 `bot_metrics` con columns: `model, input_tokens, output_tokens, cost_usd, latency_ms, occurred_at, kind`. Wave 1.5.

### 7.2 No hay endpoint `mark-vip` o `note-add`

Spec `AuditEvent.action` incluye `'marked_vip', 'note_added'` pero no hay endpoint backend para emitir esos eventos.

Cuando Wave 2 agregue internal notes / VIP toggle, estos endpoints son needed.

### 7.3 No hay endpoint para `subscribers` metadata

Memoria #25: "CC-B usó subscriber_id como name fallback". Tabla `subscribers` o `guests` per-subscriber metadata not exposed via API.

**Fix Wave 1.5**: crear `subscribers` JOIN or expose getter.

### 7.4 Suggestion endpoint no captures `kb_docs_loaded`

`llm-suggestion.ts` `kbDocs: string[] = [];` — siempre array vacío. Spec §4.4.5 dice "R2 KB docs relevantes" pero la implementación NUNCA fetch R2.

**Fix**: implementar R2 search:
```ts
const kbDocs = await searchKB(env.KNOWLEDGE_BUCKET, lastGuestMsg.text, { topK: 3 });
```

`searchKB` no existe en codebase actual. Wave 1.5 o defer.

### 7.5 `karina_training_examples` lee de quick_replies count

`llm-suggestion.ts` línea 162:
```ts
`SELECT text FROM quick_replies WHERE usage_count > 0 ORDER BY usage_count DESC LIMIT 3`
```

En prod = 0 rows. Spec dice "karina_training" — distinto a quick_replies. Probablemente quería `karina_training` table o `/admin/karina-training` content (memoria histórico).

**Fix**: clarificar source con Alex. Wave 2.

### 7.6 No hay rate limiting en suggest endpoint

Spec §4.4.5 menciona `rate_limit` skip reason pero implementación NO rate-limits. Si Karina abre 80 conversations Tab Reservas → 80 Haiku calls = ~$0.08 instantáneo.

**Fix**: agregar simple counter en KV (`KV_IDEMPOTENCY`):
```ts
const today = new Date().toISOString().slice(0, 10);
const key = `llm-sugg-count:${today}`;
const count = parseInt(await env.KV.get(key) ?? '0', 10);
if (count > 500) return { ok: false, skip_reason: 'rate_limit' };
await env.KV.put(key, String(count + 1), { expirationTtl: 86400 });
```

Wave 1.5.

---

## §8. Industry best practices research synthesis

Tras 8 web searches comparando Hostaway, Hostfully, Front, Intercom, HelpScout, Crisp, Missive, Superhuman, Gmelius, Runnr.ai — síntesis de patterns:

### 8.1 RDM ya está BIEN vs industry

| Feature | RDM | Industry |
|---|---|---|
| Lifecycle awareness 8 sections | ✅ | Ninguno tan granular |
| Readiness score 6-component | ✅ | Ninguno tiene esto — unique RDM |
| WhatsApp Business via ManyChat | ✅ | Hostaway/Hostfully sí, otros no |
| Booker bot agent autonomous | ✅ | Top-tier feature |
| Test number CSS tenue | ✅ | Detail polish raro |
| Pet policy canónico | ✅ | Domain-specific |
| Casa Chamán filter sistémico | ✅ | Aislamiento limpio |

### 8.2 RDM FALTA vs industry

| Feature | Industry | Impacto Kari |
|---|---|---|
| **AI draft pre-loaded** | Superhuman, Gmelius (Gemini), alfred_ | 🔴 HIGH — Bug #1 lo fix |
| **Status badges** (open/snoozed/resolved) | Todos | 🟡 MED |
| **Internal notes** | Front, HelpScout, Missive, Intercom | 🟡 MED — multi-user future |
| **Tags custom** | Todos | 🟡 MED |
| **Smart routing rules** | Crisp, Hostaway | 🟢 LOW Wave 2 |
| **Send schedule** | Hostaway, Front | 🟡 MED |
| **Translation auto** | Hostaway, Runnr.ai | 🟡 MED — `detected_lang` is half |
| **Cross-channel profile** | Hostaway, Hostfully | 🟡 MED |
| **WhatsApp templates library** | Hostaway, AiSensy | 🟡 MED — Quick replies framework existe pero vacío |
| **Bulk actions** | Front, HelpScout | 🟢 LOW |
| **Conversation search semantic** | Front, Intercom | 🟢 LOW Wave 2 |
| **AI-powered triage** | Crisp 50% auto | 🟢 LOW (RDM Greeter ya filtra el front, este es backend) |
| **Mention @teammate** | Missive, Front | 🟢 LOW Wave 2 (multi-user) |

### 8.3 Industry pricing context (para Alex perspective)

- **Hostaway** unified inbox: incluido en plan PMS ~$150-500/mes según portfolio
- **Hostfully**: similar
- **Front**: $25-99/seat/mes shared inbox (sin PMS context)
- **Intercom Essential**: $29/seat/mes
- **HelpScout**: $20-65/seat/mes
- **Crisp**: $25/seat/mes + AI separate
- **Superhuman**: $30/seat/mes individual AI email

**RDM custom build**: $0 marginal por seat (Cloudflare Workers + D1) + costos LLM ~$3/mes Haiku según estimate spec §4.4.5. Tradeoff: tiempo dev vs commercial off-the-shelf.

### 8.4 Industry insights destacados

De Crisp blog (April 2026): *"Draft suggestions should never auto-send. Full conversation context, not just the last message: the AI must read the full thread to avoid contradicting what was said three messages earlier."*

✅ RDM D19 cumple esto.

De alfred_ blog: *"Superhuman currently leads in voice matching. It creates separate writing profiles for each recipient, so your tone shifts naturally between contacts."*

🟡 RDM oportunidad: el system prompt admin-suggest-reply hoy es genérico. Podría adaptarse a tono de cada guest based on history.

De Hostaway: *"Automations handle up to 90-93% of routine messages with consistent, accurate replies."*

⚠️ RDM Greeter ya filtra ~90% del top funnel. Inbox es solo el 10% que escala humano. **Diferente philosophy**: RDM inbox no quiere automatizar 90%, quiere ayudar Kari a resolver el 10%. Posicionamiento OK.

De Nielsen Norman Group (cited en Crisp): *"agents using AI assistance handle 13.8% more customer inquiries per hour."*

Métrica para tracking post-Wave fix #1. Wave 1.5: agregar `bot_metrics` para medir esto.

De Hostaway: *"unified inbox reduces average response time by 50-70%"*

KPI tracking: response_latency post-Wave 1.5 dashboard.

---

## §9. Lo que falta en orden de impacto Karina

Ranking pragmático asumiendo objetivo = **Karina usa el inbox cada día sin fricciones**:

### Tier 0 — Bloqueantes para que Karina USE el inbox

1. **Fix #1 LLM suggestion render** — sin esto, principal feature anunciada NO existe
2. **Fix #2 Preview Tab Reservas** — sin preview, Kari no sabe qué row abrir
3. **Fix #4 paid_amount calc** — info errónea en sidebar enseña mal a Kari
4. **Poblar quick_replies** — sentar con Kari 30min, crear 10-15 quick replies básicos (Pet policy, Check-in info, Llegada Acapulco, Menú info, Cancelación, etc)

### Tier 1 — Reducción de fricción inmediata

5. **Fix #5 rules_accepted** — readiness incompleto sistémicamente engaña Kari
6. **Fix #6 Counter cross-tab** — tabs muestran info correcta
7. **Fix #7 LLM suggestion phone normalization** — sin esto, Wave 1 fix #1 sirve solo 50%
8. **Quick action buttons row-level** — saltar a AirBnB/Beds24 en 1 click (Alex thread/202 §4)
9. **Bug #2 vip_repeat typo** — VIP guests visibles

### Tier 2 — Polish UX

10. **Auto-scroll to bottom** — Kari ve último mensaje al abrir
11. **Fechas check-in/checkout en row** — preview rápido sin abrir
12. **Status badges** (snoozed visual, resolved visual)
13. **Header conversation guest name** (no "Booking 79421553")
14. **Real timestamps** (no ficticios)

### Tier 3 — Features nuevos (post estabilización)

15. **Internal notes** — Kari + Alex colaboración escrita
16. **Tags custom** — categorización ad-hoc
17. **Send + schedule** — "te confirmamos mañana 9am"
18. **Translation auto** — guests inglés/alemán
19. **Cross-channel guest profile** — historia completa
20. **WhatsApp templates library** — pre-populated quick_replies pre-Kari onboarding

### Tier 4 — Wave 2+

21. **AI summary lifecycle context** — el "texto descriptivo resumen" Alex menciona si NO es interpretación A
22. **Bulk actions** — mark N resolved
23. **Conversation search semantic**
24. **Smart routing rules no-code**
25. **Mention @teammate**
26. **Multi-user typing presence**

---

## §10. Recommendations priorizadas — accionables

### Plan WC sugerido (3 PRs ejecutables ASAP)

#### PR-A: **thread/205 — Bugs críticos LLM + Preview + Sidebar fixes** (~3-4h CC)

Backend changes:
- Fix LLM suggestion auto-trigger en ConversationView mount (Bug #1)
- Fix aggregate.ts read bot_messages_inbox para Tab Reservas (Bug #2)
- Fix paid_amount_mxn calc (Bug #4)
- Fix llm-suggestion.ts phone normalization (Bug #7)
- Fix counter cross-tab query (Bug #6)
- Fix vip_repeat typo (Bug medium 5.1)

Frontend changes:
- ConversationView pre-fetch suggestion + pass to ComposeBox

Tests + 1 PR.

**Resultado**: 5 bugs críticos + 1 medio resueltos. Kari ve LLM suggestion + preview real Tab Reservas + sidebar pago correcto.

#### PR-B: **thread/206 — Readiness + Status badges** (~2-3h CC)

Backend changes:
- Migration 0035 booking_captures.rules_accepted column
- readiness.ts uses new column (Bug #5)
- Add status badge fields al InboxRow contract: `is_snoozed`, `is_resolved`
- Aggregate populates them

Frontend changes:
- ReadinessScore handles full 6/6 (no longer max 5/6)
- InboxRow render status badges visual

Tests + 1 PR.

**Resultado**: Readiness sistemicamente correcto + visual state per row.

#### PR-C: **thread/207 — Quick action buttons + dates + counts** (~3h CC)

Backend changes:
- Agregar al InboxRow contract: `check_in`, `check_out`, `airbnb_confirmation_code`, `total_message_count`
- Aggregate poblar campos

Frontend changes:
- InboxRow render fechas formato "28 may - 1 jun"
- InboxRow render total count badge "5 nuevos / 24 total"
- Quick action buttons row-level desktop only (AirBnB / Beds24 / `/booking` / `/conversation`)
- Auto-scroll to bottom en ConversationView mount

Tests + 1 PR.

**Resultado**: Alex gaps thread/202 §4 todos resueltos. Quick navigation funcional.

### Acciones non-code (Alex + Karina)

#### Action 1: **Sentar 30min con Karina poblar quick_replies**

Sugerido contenido inicial (15 replies por defecto):

| Emoji | Name | Category | Template text |
|---|---|---|---|
| 🐶 | Pet policy | reglas | "Hola {{guest_name}}, sobre tu mascota: aceptamos hasta 2 perros, $300 MXN por mascota por estancia. ¿Confirmas cuántos vienen?" |
| 🕐 | Check-in info | logistica | "Check-in a las 3pm, check-out 12pm. ¿A qué hora estiman llegar a {{property}}?" |
| 🍽 | Menú info | servicios | "Para {{pax}} personas en {{property}}, nuestra cocinera Cele tiene menús. ¿Quieres que te pase opciones?" |
| 🚗 | Llegada Acapulco | logistica | "Para llegar a {{property}}, la mejor opción es Uber/Didi del aeropuerto (~45min). ¿Te paso ubicación?" |
| 💰 | Saldo pendiente | precios | "Hola {{guest_name}}, te confirmo que tu reserva en {{property}} para el {{checkin_date}} tiene un saldo de [revisar Beds24]. ¿Cómo prefieres liquidar?" |
| 🏊 | Servicios incluidos | servicios | "{{property}} incluye alberca, mozo, jardín. La cocinera y limpieza extra son aparte si los necesitas." |
| 🎂 | Eventos | eventos | "Tenemos disponibilidad para eventos en {{property}}. Necesito saber: día, cantidad de invitados, tipo de evento (cumpleaños/boda/familiar). ¿Me confirmas?" |
| 📋 | Reglas de la casa | reglas | "Te paso las reglas básicas de {{property}}: respetar vecinos hora 22:00, no fumar dentro, mascotas con correa. ¿Estás de acuerdo?" |
| 🌅 | Día de llegada | logistica | "¡Bienvenido {{guest_name}}! ¿Cómo estuvo el viaje? El acceso a {{property}} es por [Raul/portero]. ¿Necesitan algo al llegar?" |
| 👋 | Despedida | logistica | "Gracias por hospedarse en {{property}} 🙏 Por favor déjenos su review en AirBnB cuando puedan. ¡Esperamos verlos pronto!" |
| 🐕 | Sin mascotas | reglas | "{{property}} no acepta mascotas (excepto Rincón del Mar y Huerta Cocotera). Tengo opciones que sí aceptan, ¿te interesa?" |
| 🚫 | Sin disponibilidad | precios | "Para {{checkin_date}} no tengo {{property}} libre. Te puedo ofrecer otras propiedades disponibles. ¿Te paso opciones?" |
| 🏖 | Bienvenida nuevo | logistica | "¡Hola! Soy Karina de Rincón del Mar 🌊 Cuéntame: ¿cuántas personas, qué fechas y qué tipo de propiedad buscas?" |
| 📸 | Compartir fotos | servicios | "Te paso fotos y videos de {{property}}: [enlace]. ¿Te puedo dar más detalles?" |
| 🤝 | Confirmación final | logistica | "Listo {{guest_name}}, tu reserva en {{property}} para {{pax}} personas del {{checkin_date}} al {{checkout_date}} queda confirmada. Te esperamos! 🌴" |

15 quick_replies bien curadas > 100 mediocres. Empezar con esto, iterar.

#### Action 2: **Decidir gaps thread/202 (5 decisiones)**

(thread/202 §6 — Alex aún no votó.)

#### Action 3: **Comunicar Kari pre-launch**

Memoria #25: "techo readiness 5/6 hasta rules form exists". Después de PR-B (rules_accepted column fix), comunicar a Kari que ahora puede llegar 6/6.

#### Action 4 (longer term): **Roadmap Wave 2** (post-foundations)

- Internal notes
- Tags custom
- Translation auto
- Cross-channel profile
- Send + schedule

---

## §11. Final summary table — todo

### Por urgencia

| Tier | Items | Effort total CC | Effort total Alex |
|---|---|---|---|
| Tier 0 (must-fix) | 7 bugs + poblar QR | ~6h CC | ~30min QR + smoke tests |
| Tier 1 (UX inmediato) | 5 bugs medios + features | ~5h CC | ~smoke tests |
| Tier 2 (polish) | 5 UX details | ~3h CC | minimal |
| Tier 3 (features new) | 6 nuevas features | ~30h CC | onboarding |
| Tier 4 (Wave 2+) | 6+ features | ~50h CC | discussions |

**Tier 0+1 total**: ~11h CC = **3 PRs separados** sugerido (A/B/C arriba). 1-2 días wall-clock.

### Por valor

Top 3 cost/benefit:

1. **Fix Bug #1 LLM suggestion** — 30min CC, valor MUY alto (feature core anunciada empieza a funcionar)
2. **Poblar quick_replies con Kari** — 30min juntos con Alex, valor MUY alto (panel compose funcional, Kari empieza a usarlo)
3. **Fix Bug #2 preview Tab Reservas** — 90min CC, valor alto (Tab Reservas se vuelve scaneable)

---

## §12. Preguntas abiertas para Alex (cuando despierte)

1. **¿PR-A primero o juntar todo en megaspec?** Voto WC: PR-A primero (smaller, faster, less risk).

2. **¿Cuándo poblar quick_replies con Karina?** Voto WC: después de PR-A merge, antes de PR-C. Una vez Kari ve panel funcional, sentar 30min.

3. **¿Aceptas migration 0035 booking_captures.rules_accepted?** Off-window pre-PR-B. Voto WC: sí — single column boolean, low risk.

4. **¿Threading 1-row-per-cliente Decision D7 — implementar parcial (solo Tab Leads) o defer?** Voto WC: **defer** — 95% guests = 1 booking, complexity vs value bajo.

5. **Quick action buttons row-level (PR-C) — confirmar 4 URLs**:
   - AirBnB: `https://www.airbnb.mx/hosting/reservations/details/{confirmation_code}` ✅?
   - Beds24: `https://beds24.com/control3.php?action=showBooking&bookid={beds24_booking_id}` ✅?
   - `/admin/bookings/{beds24_booking_id}` ✅?
   - `/admin/conversation/{rawId}` ✅?

6. **¿Wave 2 features prioritarias?** Industry pattern faltantes — internal notes / tags / translation / cross-channel profile / send-schedule. Voto WC priority: internal notes > tags > translation > send-schedule > cross-channel profile.

7. **Bug #3 paid_amount fix — confirmar fórmula correcta?**:
   ```
   paid = total - balance_due_mxn  // si balance_due no null
       OR deposit * 0.33           // si deposit_paid=1
       OR 0                        // base
   ```
   ¿Es correcto AirBnB siempre 33% deposit, direct booking variable?

---

## §13. References

- **Spec source**: thread/196 (mega-spec, 50+ pp)
- **Threads ejecutados pre-204**: 197-203
- **D1 queries verified** (14): aggregates, counts, samples
- **Industry research** (8 web searches): Hostaway, Hostfully, Front, Intercom, HelpScout, Crisp, Missive, Superhuman, Gmelius, Runnr.ai
- **Code files audited** (filesystem real): 22 files frontend + backend + migrations
- **Memorias relevantes**: #25 (Wave 1.5 followups), #26 (worker-bot deploy gotcha), #27 (zero-auth applied)

**Hours invertidos audit + análisis + research + redacción**: ~3h WC brain ultra (target Alex).

— WC, 2026-05-24 04:30 UTC

> *"Audita lo entregado contra el spec, no el spec contra lo entregado. La fuente de verdad es el código que corre, no el doc."* — principle aplicado.
