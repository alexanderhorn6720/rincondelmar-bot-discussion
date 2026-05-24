---
thread: 207
author: wc
topic: inbox-action-buttons-dates-counts-drawer-autoscroll
status: ready-for-execution
mode: DoIt
created: 2026-05-24
related_threads: [196, 202, 204, 205, 206]
estimated_effort: 2-3h CC (1 session)
pipeline: PR-C of mega-run (after PR-A thread/205 + PR-B thread/206 merged+deployed+smoke)
requires_worker_bot_deploy: YES (manual, has minor contract additions)
requires_web_redeploy: YES (auto CF Pages — mostly frontend)
severity: MEDIUM (UX polish + missing thread/202 gaps + drawer width Alex pidió en sesión)
---

# Thread 207 — PR-C: Quick action buttons + dates + counts + auto-scroll + drawer width

> **PR-C of 3 (mega-run, final)**. Pre-req: PR-A (thread/205) + PR-B (thread/206) merged + deployed + smoke OK.

## §0. TL;DR

Cierra gaps thread/202 §4 (acciones row-level) + thread/204 §6.2/§6.3 (fechas + count format) + screenshot Alex 2026-05-24 (drawer width) + thread/204 §5.5 (auto-scroll).

| Fix | Tipo |
|---|---|
| Quick action buttons row-level desktop (AirBnB, Beds24, /booking, /conversation) | Feature nueva |
| Fechas check-in/check-out display row | Backend contract + frontend render |
| Total message count badge ("5 nuevos / 24 total") | Backend contract + frontend |
| Auto-scroll to bottom en ConversationView mount | UX polish |
| **Drawer width desktop fix** (Alex screenshot — timeline cramped ~280px → debería ser ~600px) | CSS |

~3 archivos backend + ~5 archivos frontend modificados. ~200-300 LoC.

## §1. Context

### 1.1 Screenshot Alex sesión 2026-05-24

Drawer desktop conv-drawer cubre ~55% viewport. Timeline column dentro queda muy estrecha (~280px). Bot message text "preparándoles unas vacaciones tranquilas, conectadas con la naturaleza" se rompe en líneas de 3-4 palabras. Compose textarea espacio aceptable pero subóptimo.

Causa probable: CSS `conv-drawer` width fija o vh constraint que no responde a viewport real disponible.

### 1.2 Gaps thread/202 §4 (Alex pidió, NO en spec original)

| Botón row-level | URL | Estado |
|---|---|---|
| AirBnB host inbox | `https://www.airbnb.mx/hosting/reservations/details/{airbnb_code}` | ❌ NO implementado |
| Beds24 booking | `https://beds24.com/control3.php?action=showBooking&bookid={beds24_booking_id}` | ❌ NO |
| /admin/bookings/[id] | `/admin/bookings/{beds24_booking_id}` | ❌ NO (existe la page, falta link from row) |
| /admin/conversation/[id] | `/admin/conversation/{row.id}` | ✅ ya es el default onClick |

### 1.3 Gap fechas + counts

Row hoy muestra: `T-3d`. Falta fechas raw "21 may - 23 may" (más legible). Row hoy muestra `unread_count` "5 nuevos". Falta `total_message_count` "5 nuevos / 24 total" para contexto.

### 1.4 UX auto-scroll

ConversationView abre mostrando primer mensaje arriba. Karina necesita scroll manual al final cada vez. Industry standard: auto-scroll bottom on mount.

## §2. Explicit scope

### 2.1 IN scope

| Archivo | Cambio |
|---|---|
| `apps/worker-bot/src/inbox/aggregate.ts` | Agregar al SELECT: `bb.airbnb_confirmation_code` (verificar nombre column real). Agregar campos al InboxRow contract |
| `apps/worker-bot/src/inbox/aggregate.ts` | Computar `total_message_count` = WA history USER+ASSISTANT count + bot_messages_inbox COUNT |
| `apps/web/src/lib/inbox-client.ts` | Type `InboxRow` add: `check_in: string \| null`, `check_out: string \| null`, `total_message_count: number`, `airbnb_confirmation_code: string \| null` |
| `apps/web/src/components/inbox/InboxRow.tsx` | Render: fechas formato "21 may - 23 may", count "N nuevos / M total", 4 botones row-level desktop only (hover-revealed o always-visible) |
| `apps/web/src/components/conversation/ConversationView.tsx` | useRef + useEffect scroll-to-bottom on data load |
| `apps/web/src/styles/conversation.css` | Fix `.conv-drawer` width desktop (target ~85vw para que timeline >= 500px) |
| `apps/web/src/styles/inbox.css` | Estilos botones row-level + fechas + count |
| Tests | Extender row tests + ConversationView scroll test |

Esperado: ~7-8 archivos modificados, ~200-300 LoC.

### 2.2 OUT of scope

- ❌ Internal notes, tags, translation → Wave 2
- ❌ Bulk actions → Wave 2
- ❌ Send + schedule → Wave 2
- ❌ Cross-channel guest profile → Wave 2
- ❌ Real timestamps per message (sidecar column needed) → Wave 1.5 separate
- ❌ Search conversation → Wave 2
- ❌ Multi-user typing presence → never

## §3. Closed decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Botones row-level visible always-visible (NO hover-revealed) | Karina mobile-friendly. Hover no funciona touch. Visual clutter aceptable Wave 1 |
| D2 | Botones row-level desktop only (`>= 1024px`). Mobile: omitir, tap row abre conversation full-page | Mobile space limited. Single-tap flow > multi-button |
| D3 | Fechas formato "21 may - 23 may" en pre-stay + in-stay + post-stay sections (todas Reservas) | Lead rows no tienen fechas. Format `toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })` |
| D4 | Count format: "5 nuevos / 24 total" cuando unread > 0. Solo "24 mensajes" cuando 0 unread | Si 0 unread, "0 nuevos / 24 total" noise. Simplificar |
| D5 | total_message_count = WA history user+bot lines count + bot_messages_inbox count (all sources, all directions) | Karina quiere ver volumen total intercambio |
| D6 | airbnb_confirmation_code source: SELECT desde beds24_bookings columna real (verificar) o derivar de booking_id si no existe | CC verifica schema actual primero |
| D7 | Botón AirBnB solo aparece si channel === 'airbnb' AND airbnb_confirmation_code exists | Direct bookings no tienen AirBnB inbox |
| D8 | Botón Beds24 siempre visible (todos bookings tienen beds24_booking_id) | Universal |
| D9 | Drawer width fix: cambiar `width: Xvw` o `max-width` para que timeline column >= 500px | CC inspecciona CSS actual y ajusta empirically. Target: bot message bubble ~70-90% del timeline width |
| D10 | Auto-scroll usa `scrollIntoView({ behavior: 'smooth', block: 'end' })` en ref final | Smooth animation Karina note. Alternativa instant si performance issue |
| D11 | Scroll trigger en useEffect `[data?.conversation.messages.length]` — dispara cuando msgs cargan o se agregan | Idempotente, no scroll on every re-render |
| D12 | Botones row-level: stopPropagation onClick para no triggear row open | Estándar React patrón |

## §4. Implementation

### 4.1 Backend — aggregate.ts contract additions

`apps/worker-bot/src/inbox/aggregate.ts`:

```diff
 export interface InboxRow {
   // ... existing fields
+  check_in: string | null;          // thread/207: "2026-05-21"
+  check_out: string | null;         // "2026-05-23"
+  airbnb_confirmation_code: string | null;  // thread/207: from beds24_bookings
+  total_message_count: number;      // thread/207: total intercambio
 }
```

Tab Reservas SELECT — agregar airbnb_confirmation_code (verificar nombre column en beds24_bookings):

```diff
 SELECT
   bb.beds24_booking_id, bb.room_id, bb.arrival, bb.departure,
   bb.num_adults, bb.num_pets, bb.total_amount_mxn, bb.deposit_paid,
   bb.balance_due_mxn, bb.channel, bb.status, bb.guest_id,
+  bb.airbnb_confirmation_code,  -- verify exact column name (could be `external_id`, `channel_booking_id`, etc)
   bc.mascotas_confirmed, bc.mascotas_count, bc.menu_status,
   bc.compras_confirmed, bc.morenas_svc_confirmed, bc.rules_accepted,
   ...
```

CC primero verifica schema actual:
```bash
npx wrangler d1 execute rincon --remote --command="SELECT name FROM pragma_table_info('beds24_bookings')"
```

Si no existe `airbnb_confirmation_code`, derivar URL desde `beds24_booking_id` para AirBnB también — AirBnB host inbox acepta beds24 ID? **NO**. AirBnB inbox usa confirmation_code AirBnB. CC investiga schema y procede:

Opciones si column not exists:
- A) Migration 0036 add column + backfill via Beds24 API (defer thread/208)
- B) Skip botón AirBnB Wave 1, dejar solo Beds24 + /booking + /conversation (3 botones)
- C) Buscar otra column candidato (`external_booking_id`, `referer_booking_id`)

**Voto WC**: **C primero, B fallback**. CC verifica schema antes.

Computar `total_message_count` en el loop de Tab Reservas:

```ts
// In aggregate.ts loop
let totalMsgCount = 0;
if (convRow) {
  totalMsgCount += convRow.history.split('\n').filter(l =>
    l.startsWith('USER:') || l.startsWith('ASSISTANT:')
  ).length;
}
if (br.beds24_booking_id) {
  const totalOta = await env.DB.prepare(
    `SELECT COUNT(*) as n FROM bot_messages_inbox WHERE booking_id = ?`
  ).bind(br.beds24_booking_id).first<{ n: number }>().catch(() => null);
  totalMsgCount += totalOta?.n ?? 0;
}

// rows.push({
//   ...
//   check_in: br.arrival,
//   check_out: br.departure,
//   airbnb_confirmation_code: br.airbnb_confirmation_code,
//   total_message_count: totalMsgCount,
// });
```

Mirror Tab Leads: `check_in: null, check_out: null, airbnb_confirmation_code: null, total_message_count: WA history count`.

**Performance note**: 1 query extra per row (75 rows × 1 = 75 queries ~75ms). Cuando suma fix Bug #2 = 150 + 75 = 225 queries total ~225ms aggregate. Aceptable Wave 1. Optimización lateral subquery Wave 2.

### 4.2 Frontend — InboxRow.tsx render

`apps/web/src/components/inbox/InboxRow.tsx`:

```diff
 import { fmtRelative, formatDaysToCheckin, fmtDate } from '@/lib/inbox-client';
+
+/** Exported for tests — format check-in/out range for row display. */
+export function formatDateRange(checkIn: string | null, checkOut: string | null): string | null {
+  if (!checkIn || !checkOut) return null;
+  const ci = new Date(checkIn);
+  const co = new Date(checkOut);
+  const sameMonth = ci.getMonth() === co.getMonth();
+  const ciFmt = ci.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
+  const coFmt = sameMonth
+    ? co.toLocaleDateString('es-MX', { day: 'numeric' })
+    : co.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
+  return `${ciFmt} – ${coFmt}`;
+}
+
+/** Exported for tests — format count "N nuevos / M total" or "M mensajes". */
+export function formatMessageCount(unread: number, total: number): string {
+  if (unread > 0) return `${unread} nuevos / ${total} total`;
+  return total > 0 ? `${total} mensajes` : '';
+}
+
+function urlAirBnB(code: string): string {
+  return `https://www.airbnb.mx/hosting/reservations/details/${code}`;
+}
+function urlBeds24(bookingId: string): string {
+  return `https://beds24.com/control3.php?action=showBooking&bookid=${bookingId}`;
+}
+function urlBookingDetail(bookingId: string): string {
+  return `/admin/bookings/${bookingId}`;
+}

 // ... interface Props { row, onClick }

 export default function InboxRow({ row, onClick }: Props) {
   const isTestNumber = row.is_test_number;
+  const beds24Id = row.id.startsWith('b_') ? row.id.slice(2) : null;
+  const dateRange = formatDateRange(row.check_in, row.check_out);
+  const countLabel = formatMessageCount(row.unread_count, row.total_message_count);

   return (
     <div className="inbox-row" ...>
       <div className="inbox-row-name">
         {row.guest_name}
         {/* ... existing badges ... */}
         {shouldShowStayInfo(row.pax, row.days_to_checkin) && (
           <div className="inbox-row-stay-info">
             {row.pax !== null && (...)}
             {row.days_to_checkin !== null && (
               <span className="inbox-row-days">
                 {formatDaysToCheckin(row.days_to_checkin)}
               </span>
             )}
+            {dateRange && (
+              <span className="inbox-row-dates" title={`${row.check_in} a ${row.check_out}`}>
+                📅 {dateRange}
+              </span>
+            )}
           </div>
         )}
       </div>

       <div className="inbox-row-time">{fmtRelative(row.last_msg_at)}</div>

       <div className="inbox-row-preview" title={row.preview}>
         {row.preview}
+        {countLabel && (
+          <span className="inbox-row-count">{countLabel}</span>
+        )}
       </div>

       <div className="inbox-row-meta">
         {/* ... existing channels, lang, readiness ... */}

+        {/* thread/207: row-level quick action buttons (desktop only via CSS) */}
+        <div className="inbox-row-actions" onClick={(e) => e.stopPropagation()}>
+          {row.airbnb_confirmation_code && row.channels.includes('airbnb') && (
+            <a
+              href={urlAirBnB(row.airbnb_confirmation_code)}
+              target="_blank"
+              rel="noopener noreferrer"
+              className="inbox-action-icon"
+              title="Abrir en AirBnB host inbox"
+              aria-label="AirBnB"
+            >
+              ✈️
+            </a>
+          )}
+          {beds24Id && (
+            <a
+              href={urlBeds24(beds24Id)}
+              target="_blank"
+              rel="noopener noreferrer"
+              className="inbox-action-icon"
+              title="Abrir en Beds24"
+              aria-label="Beds24"
+            >
+              🛏
+            </a>
+          )}
+          {beds24Id && (
+            <a
+              href={urlBookingDetail(beds24Id)}
+              className="inbox-action-icon"
+              title="Detalle de la reserva"
+              aria-label="Booking detail"
+            >
+              📋
+            </a>
+          )}
+        </div>
       </div>
     </div>
   );
 }
```

### 4.3 ConversationView auto-scroll bottom

`apps/web/src/components/conversation/ConversationView.tsx`:

```diff
 import { useEffect, useMemo, useRef, useState } from 'react';

 // ...

 export default function ConversationView({ convId, onBack, embedded = false }: Props) {
   // ... existing state
+  const messagesEndRef = useRef<HTMLDivElement | null>(null);

   // ... existing useEffects

+  // thread/207: auto-scroll to bottom on initial load and when new messages arrive
+  useEffect(() => {
+    if (data?.conversation.messages.length) {
+      // Small delay to ensure DOM has rendered
+      const timer = setTimeout(() => {
+        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
+      }, 100);
+      return () => clearTimeout(timer);
+    }
+    return undefined;
+  }, [data?.conversation.messages.length]);

   // ... rest of component

   <div className="conv-timeline" aria-label="Mensajes">
     {dayGroups.map((group) => (
       <div key={group.dateLabel}>
         {group.messages.map((msg, i) => (
           <MessageBubble ... />
         ))}
       </div>
     ))}
     {conversation.messages.length === 0 && (
       <div className="inbox-empty">Sin mensajes. Puedes iniciar la conversación abajo.</div>
     )}
+    {/* thread/207: scroll anchor */}
+    <div ref={messagesEndRef} aria-hidden="true" />
   </div>
```

### 4.4 Drawer width CSS fix

`apps/web/src/styles/conversation.css` (o donde esté el CSS de `.conv-drawer`):

CC primero ve el archivo actual:
```bash
cat apps/web/src/styles/conversation.css | grep -A 10 'conv-drawer'
```

Probable fix:

```diff
 .conv-drawer {
-  width: 50vw;
-  max-width: 800px;
+  /* thread/207: drawer wider para timeline cómodo en desktop */
+  width: 85vw;
+  max-width: 1100px;
   position: fixed;
   right: 0;
   top: 0;
   height: 100vh;
   /* ... */
 }

 @media (max-width: 1023px) {
   .conv-drawer {
-    width: 100%;
+    width: 100vw;
     max-width: none;
   }
 }
```

(Valores exactos dependen de CSS actual. Target: dentro del drawer, `.conv-timeline` column tiene `min-width: 500px` y messages bubble max-width permite ~70-80% timeline width.)

Si el problema NO es width del drawer sino layout interno (grid columns):

```diff
 .conv-page-embedded {
-  grid-template-columns: 1fr 280px;  /* timeline + sidebar */
+  grid-template-columns: minmax(500px, 1fr) 280px;
 }
```

CC inspecciona y ajusta empíricamente. Target verificable: bot bubble text al menos 8-10 palabras por línea (vs 3-4 actuales screenshot Alex).

### 4.5 inbox.css estilos botones row + fechas + count

```css
/* thread/207 — row-level action buttons */
.inbox-row-actions {
  display: none; /* mobile: hidden */
  gap: var(--sp-1);
  margin-left: auto;
}

@media (min-width: 1024px) {
  .inbox-row-actions {
    display: inline-flex;
  }
}

.inbox-action-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  text-decoration: none;
  font-size: 14px;
  color: var(--color-text);
  background: transparent;
  transition: background 100ms;
}

.inbox-action-icon:hover {
  background: var(--color-bg-hover);
}

/* thread/207 — fechas + count */
.inbox-row-dates {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-left: var(--sp-2);
}

.inbox-row-count {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-left: var(--sp-2);
  font-style: italic;
}
```

## §5. Tests

### 5.1 InboxRow new fields render

```tsx
describe('InboxRow — new fields (thread/207)', () => {
  it('renders date range "21 may – 23 may"', () => {
    const row = { ...mockRow, check_in: '2026-05-21', check_out: '2026-05-23' };
    render(<InboxRow row={row} onClick={jest.fn()} />);
    expect(screen.getByText(/21 may.*23 may/i)).toBeInTheDocument();
  });

  it('formats count "5 nuevos / 24 total" when unread > 0', () => {
    const row = { ...mockRow, unread_count: 5, total_message_count: 24 };
    render(<InboxRow row={row} onClick={jest.fn()} />);
    expect(screen.getByText(/5 nuevos \/ 24 total/i)).toBeInTheDocument();
  });

  it('formats count "24 mensajes" when 0 unread', () => {
    const row = { ...mockRow, unread_count: 0, total_message_count: 24 };
    render(<InboxRow row={row} onClick={jest.fn()} />);
    expect(screen.getByText(/24 mensajes/i)).toBeInTheDocument();
  });

  it('renders AirBnB action link only when code present + airbnb channel', () => { ... });
  it('renders Beds24 action link when beds24Id available', () => { ... });
  it('stopPropagation on action button click does not trigger onClick', () => { ... });
});
```

### 5.2 ConversationView auto-scroll

```tsx
describe('ConversationView — auto-scroll (thread/207)', () => {
  it('scrolls to bottom when messages load', async () => {
    const scrollSpy = jest.spyOn(HTMLElement.prototype, 'scrollIntoView');
    render(<ConversationView convId="b_123" />);
    await waitFor(() => {
      expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'end' });
    });
  });
});
```

### 5.3 aggregate.ts new fields populated

```ts
describe('aggregateInbox — new InboxRow fields (thread/207)', () => {
  it('populates check_in, check_out, total_message_count, airbnb_confirmation_code', async () => {
    const env = mockEnv({
      bookings: [{
        beds24_booking_id: 86656062,
        arrival: '2026-05-21', departure: '2026-05-23',
        airbnb_confirmation_code: 'HMABCD1234',
        ...
      }],
      botMessagesInbox: Array(15).fill({ booking_id: 86656062, /* ... */ }),
    });
    const result = await aggregateInbox(env, 'reservas', {});
    const row = result.sections.flatMap(s => s.rows).find(r => r.id === 'b_86656062');
    expect(row?.check_in).toBe('2026-05-21');
    expect(row?.check_out).toBe('2026-05-23');
    expect(row?.airbnb_confirmation_code).toBe('HMABCD1234');
    expect(row?.total_message_count).toBe(15);
  });
});
```

## §6. Definition of Done

- [ ] aggregate.ts SELECT + populate 4 new fields
- [ ] inbox-client.ts type extends
- [ ] InboxRow renders dates + count + 3-4 action buttons (desktop only)
- [ ] ConversationView auto-scroll on data load
- [ ] CSS drawer width fix verified by inspect: timeline bot bubble ~70% width
- [ ] inbox.css + conversation.css updated
- [ ] Tests pasan
- [ ] PR título: `feat(inbox): action buttons + dates + counts + auto-scroll + drawer (thread/207)`
- [ ] Reporte CC

## §7. Risks + Mitigations

| Risk | Mitigation |
|---|---|
| airbnb_confirmation_code column NO existe | CC verifica schema antes. Si missing: skip botón AirBnB Wave 1, log issue para thread/208 |
| Drawer width fix rompe mobile layout | CSS media queries @media (max-width: 1023px) preserva mobile fullscreen |
| Botones row-level desktop clutter visual con muchas badges | Si Karina complain: hover-revealed Wave 2 |
| Auto-scroll smooth animation lag con 100+ msgs | setTimeout 100ms + smooth fallback to instant if performance issue |
| total_message_count query +75 D1 calls aggregate | Aceptable Wave 1 (~75ms). Optimización JOIN lateral Wave 2 |
| beds24_booking_id "b_" prefix parse fragile | Test edge cases. Si row.id NO empieza con "b_" (lead), beds24Id = null, botones beds24/booking no aparecen — correcto |

## §8. Out-of-scope findings → issues

- airbnb_confirmation_code column missing → `[thread/207 OOS]` issue thread/208 backfill via Beds24 API
- Real per-message timestamps → `[thread/207 OOS]` Wave 1.5 separate
- Bulk actions, internal notes, etc → Wave 2

## §9. Kickoff command (Alex paste to CC)

```
DoIt thread/207 PR-C (FINAL mega-run): action buttons + dates + counts + auto-scroll + drawer width.

⚠️ PRE-REQUISITES:
  1. PR-A (thread/205) MERGED + DEPLOYED + SMOKE OK
  2. PR-B (thread/206) MERGED + DEPLOYED + SMOKE OK
  3. Migration 0035 applied remote

Verificar https://rincondelmar.club/admin/inbox antes empezar:
  - LLM suggestion visible (PR-A)
  - Preview Tab Reservas no vacío (PR-A)
  - Sidebar paid correcto (PR-A)
  - Status badges (PR-B)
  - Readiness 6/6 alcanzable (PR-B)

Lee spec completa:
c:/dev/rdm/dev/discussion/threads/207-wc-inbox-action-buttons-dates-counts-drawer.md

Working directory: c:/dev/rdm/dev/bot

Pre-flight:
1. cd c:/dev/rdm/dev/bot && git checkout main && git pull origin main
2. git status clean
3. git log --oneline -3 — confirma PR-A + PR-B en main

Execution:
1. git checkout -b feat/inbox-pr-c-actions-dates-counts-drawer
2. Verify schema beds24_bookings — airbnb_confirmation_code o equivalente:
   npx wrangler d1 execute rincon --remote --command="SELECT name FROM pragma_table_info('beds24_bookings')"
3. Si column missing: log [thread/207 OOS] issue + skip AirBnB button
4. Editar aggregate.ts §4.1 (contract + SELECT + populate)
5. Editar inbox-client.ts type extends
6. Editar InboxRow.tsx §4.2 (formatDateRange + formatMessageCount + buttons + render)
7. Editar ConversationView.tsx §4.3 (auto-scroll)
8. Inspect conv-drawer CSS actual + ajustar §4.4 (target timeline bubble ~70% width)
9. Update inbox.css + conversation.css
10. Tests §5
11. typecheck + tests
12. Commit + push + PR
13. Reporte final con files + LoC + PR URL + nota wrangler deploy

Scope ESTRICTO §2.1. OOS → issue prefix [thread/207 OOS].

Bloqueado >30 min = STOP + reporta.

GO.
```

## §10. Post-merge smoke test (Alex)

Post merge + `cd apps/worker-bot && npx wrangler deploy`:

1. **Action buttons aparecen desktop**: open Tab Reservas → cada row con booking muestra 2-3 íconos al final (✈️ AirBnB si aplica, 🛏 Beds24, 📋 detalle)
2. **Click ✈️ AirBnB**: nueva pestaña con AirBnB host reservations detail
3. **Click 🛏 Beds24**: nueva pestaña Beds24 panel
4. **Click 📋 detalle**: navega a `/admin/bookings/[id]`
5. **Fechas visibles**: rows muestran "📅 21 may – 23 may"
6. **Count mensajes**: rows muestran "5 nuevos / 24 total" o "24 mensajes" según unread
7. **Drawer width**: click cualquier row → drawer abre con timeline más ancho, bot messages ~70% width readable
8. **Auto-scroll**: al abrir conversation, scroll automático al último mensaje (no quedarse arriba)

✅ Smoke completa → **mega-run COMPLETO**. 3 PRs deployed. Karina inbox listo para uso diario.

## §11. References

- thread/202 §4 (Alex gaps thread/202)
- thread/204 audit §6.1, §6.2, §6.3, §5.5
- Alex screenshot 2026-05-24 (drawer width problem)
- Memorias #25

---

## §12. Post-mega-run actions (post PR-C deploy)

1. **Sentar 30min con Karina poblar quick_replies** — sugerido lista thread/204 §10 Action 1 (15 templates iniciales)
2. **Comunicar a Karina**: ahora readiness puede llegar 6/6, status badges visibles, action buttons disponibles desktop
3. **Track metrics 1 semana**: response latency improvement, LLM suggestion usage rate (audit_log queries)
4. **Decidir Wave 2 priorities** per thread/204 §10 ranking
