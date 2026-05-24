---
thread: 199
author: wc
topic: inbox-bugs-1-3-4-5-display-css-readiness
status: ready-for-execution
mode: DoIt
created: 2026-05-24
updated: 2026-05-24
related_threads: [196, 197, 198]
related_prs: [167, 169]
estimated_effort: 50-65min CC (1 session, frontend-only)
pipeline: single-CC
out_of_scope_for_now:
  - bug-2-conversation-lookup (separate thread/200)
  - bug-6-readiness-in-stay-backend (separate thread/201)
---

# Thread 199 — Inbox bugs 1 + 3 + 4 + 5: display + CSS + readiness compact

## §0. TL;DR

Post-deploy thread/198 reveló 5 bugs visuales. Este PR resuelve 4 (frontend-only):

**Bug 1 — Filas incompletas:** rows muestran solo `name + relative_time + channel + readiness + property`. Faltan `pax`, `days_to_checkin`, badge `🐶 has_pet`. Backend YA devuelve, solo el componente no los renderiza.

**Bug 3 — Falta link a /admin/bookings/[id]:** ConversationView en estado error no permite saltar a booking detail page existente. Parsear `beds24_booking_id` del row.id prefix `b_xxx` y mostrar link.

**Bug 4 — CSS: rows del inbox sin background blanco:** `.inbox-row` no tiene `background-color` propio → se mezcla con page background crema. Falta `background: var(--color-card)`.

**Bug 5 — ReadinessScore satura el layout horizontal:** `.readiness-pills` desktop muestra 6 pills (Pax/Mascotas/Menú/ETA/Reglas/Pago) — overcrowding. Solución: mostrar solo missing pills + compact counter "✓N" para done. Reduce ruido, focus on actionable info.

**Bug 2 (conversation lookup polimórfico) = thread/200 separado**.

**Bug 6 (computeReadiness backend: in-stay rows muestran ETA/Reglas faltando) = thread/201 separado**. Nota crítica: `pago` SÍ debe seguir visible en in-stay rows porque guests suelen pagar el balance DURANTE su estancia — Karina necesita ver claramente quién pagó completo y quién no.

---

## §1. Context (why)

### 1.1 Verificación post-deploy thread/198

Inbox en `https://rincondelmar.club/admin/inbox` muestra:
- ✅ Counter 79, 5 sections lifecycle, filter dropdowns funcionales, data real backend
- ❌ Filas solo dicen `Claudia Becerra | 7s | Airbnb 2/6 Huerta Cocotera` (sin pax/fechas/pet)
- ❌ Filas SIN background blanco, se mezclan con page crema (visualmente confuso)
- ❌ ReadinessScore expandido (6 pills + ✓/◯) en desktop = overcrowding visual
- ❌ Click row → modal "not_found" sin link a booking detail
- ❌ Rows in-stay marcan ETA/Reglas como ◯ aunque ya llegaron (defer thread/201 backend fix)

### 1.2 Backend SÍ devuelve los campos para bug 1

Confirmed `apps/worker-bot/src/inbox/aggregate.ts`:
```ts
rows.push({
  pax: br.num_adults,           // ← devuelto
  has_pet: br.num_pets > 0,     // ← devuelto
  days_to_checkin: daysToCheckin, // ← devuelto
});
```

Tipo `InboxRow` en `apps/web/src/lib/inbox-client.ts` los declara. Solo `InboxRow.tsx` no los renderiza.

### 1.3 Bug 4 root cause — CSS

En `apps/web/src/styles/inbox.css` la regla `.inbox-row` define grid, gap, padding, border-top, cursor, transition — pero NO `background-color`. Hereda transparent → page background crema visible through.

`.inbox-section-header` SÍ tiene `background: var(--color-bg-alt)` — contraste. Las rows quedan sin contraste.

### 1.4 Bug 5 root cause — ReadinessScore expansión visual

`ReadinessScore.tsx` renderiza 3 versiones (desktop pills, tablet num, mobile bar) con media queries que ocultan/muestran. En desktop ≥1024 muestra `.readiness-pills` con LOS 6 criterios + ✓/◯ + label, generando overcrowding horizontal.

Decisión Alex: mostrar **solo missing** + counter compact "✓N" al final. Foco en lo que falta hacer.

### 1.5 Booking detail page existe

Verificado: `apps/web/src/pages/admin/bookings/[id].astro` deployed (PR #155 area). URL: `/admin/bookings/{beds24_booking_id}`.

### 1.6 row.id contiene beds24_booking_id

Aggregate genera `id: \`b_${beds24_booking_id}\``. Parsing trivial sin cambio de contract.

---

## §2. Explicit scope

### 2.1 IN scope

| Archivo | Cambio | LoC aprox |
|---|---|---|
| `apps/web/src/components/inbox/InboxRow.tsx` | Render `pax`, `has_pet` badge, `days_to_checkin` chip (bug 1) | +15 |
| `apps/web/src/components/inbox/ReadinessScore.tsx` | Filter `.readiness-pills` para mostrar solo missing + compact done counter (bug 5) | +10 |
| `apps/web/src/components/conversation/ConversationView.tsx` | En error UI parsear convId `b_` prefix, mostrar link a `/admin/bookings/{id}` (bug 3) | +15 |
| `apps/web/src/lib/inbox-client.ts` | Add 2 helpers: `extractBookingIdFromRowId`, `formatDaysToCheckin` | +15 |
| `apps/web/src/styles/inbox.css` | `.inbox-row { background: var(--color-card); }` + 3 stay-info classes nuevas (bug 4 + bug 1) | +15 |
| `apps/web/tests/inbox/InboxRow.test.ts` | Tests para nuevos display fields | +25 |
| `apps/web/tests/inbox/ReadinessScore.test.ts` | Tests para filter missing + counter | +20 |
| `apps/web/tests/inbox/inbox-client.test.ts` | Tests para 2 helpers nuevos | +30 |

### 2.2 OUT of scope (NO tocar)

- ❌ **Bug 2 (conversation lookup polimórfico)** — separado thread/200
- ❌ **Bug 6 (in-stay rows ETA/Reglas faltando)** — separado thread/201 (backend computeReadiness fix). `pago` SÍ permanece visible siempre (intencional, pagan durante estancia)
- ❌ `MOCK_RESPONSE` removal en InboxApp.tsx — G2 followup
- ❌ Backend changes a `aggregate.ts`, `conversation.ts`, `inbox.ts`, `readiness.ts`
- ❌ Database migrations
- ❌ CSS rework amplio fuera de las 4 reglas nuevas/modificadas
- ❌ Casa Chamán mentions
- ❌ Click row UX change (handleRowClick queda como está, thread/200 lo refactoriza)
- ❌ Deep-link button en cada InboxRow (Alex pidió link solo en modal, no en row)

---

## §3. Closed decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Bug 3 link va en error UI de ConversationView, NO en cada InboxRow | Pedido Alex: "modal = not_found / missing link to /booking?id=X" |
| D2 | Parsear `b_xxx` prefix con helper pure, NO agregar `beds24_booking_id` field al contract | Backend untouched = bug 2 independiente |
| D3 | Formato días: "T-3d" / "hoy" / "mañana" / "ayer salió" / "día N estadía" | Mobile-friendly, ES Karina-friendly inline |
| D4 | Render pax como `👥 N` con `🐶` sufijo cuando applicable | Iconos universales sin labels |
| D5 | days_to_checkin chip va en bloque stay-info junto a pax | Mismo grupo lógico, agrupado |
| D6 | Lead rows (pax=null) NO renderizan stay-info block | Leads no tienen booking data |
| D7 | helper `extractBookingIdFromRowId` retorna `null` si formato no es `b_<positive_number>` | Defensive, no throw |
| D8 | Bug 4: `.inbox-row { background: var(--color-card); }` | Usar variable existente (no hardcode #fff). Mismo bg que `.inbox-stats` y `.inbox-filters` por consistencia |
| D9 | Bug 5: Mostrar solo pills missing (◯) en desktop. Done count en compact pill al final | Reduce ruido, focus en actionable. Tooltip preserva info completa |
| D10 | Bug 5: tablet y mobile views NO cambian (ya compact con number) | Solo desktop tenía el overcrowding |
| D11 | Bug 5: `pago` siempre visible — confirmed Alex 2026-05-24 | Pagos durante estancia common, Karina necesita visibility |
| D12 | NO modificar handleRowClick en InboxApp.tsx | Bug 2 hará ese refactor |
| D13 | computeReadiness backend (bug 6) explícitamente DEFER a thread/201 | Backend change separado |

---

## §4. Implementation

### 4.1 Helpers en `inbox-client.ts`

Agregar al final del archivo:

```ts
/** Extract beds24_booking_id from row.id prefix "b_". Pure, testable. */
export function extractBookingIdFromRowId(id: string): number | null {
  if (!id.startsWith('b_')) return null;
  const n = Number(id.slice(2));
  return Number.isFinite(n) && n > 0 ? n : null;
}

/** Format days to check-in for inbox row display. Pure, testable. */
export function formatDaysToCheckin(days: number): string {
  if (days === 0) return 'hoy';
  if (days === 1) return 'mañana';
  if (days > 0) return `T-${days}d`;
  if (days === -1) return 'ayer salió';
  return `día ${-days} estadía`;
}
```

### 4.2 InboxRow.tsx — Display fields (Bug 1)

Modificar `apps/web/src/components/inbox/InboxRow.tsx`:

**Import:**
```diff
 import type { InboxRow as Row } from '@/lib/inbox-client';
-import { fmtRelative } from '@/lib/inbox-client';
+import { fmtRelative, formatDaysToCheckin } from '@/lib/inbox-client';
 import ReadinessScore from './ReadinessScore';
```

**Agregar bloque stay-info DESPUÉS del `inbox-row-name` div y ANTES del `inbox-row-time`:**

```tsx
{/* Stay info: pax + pet + days_to_checkin — only for bookings (pax !== null) */}
{(row.pax !== null || row.days_to_checkin !== null) && (
  <div className="inbox-row-stay-info">
    {row.pax !== null && (
      <span className="inbox-row-pax">
        👥 {row.pax}
        {row.has_pet && <span aria-label="con mascota"> 🐶</span>}
      </span>
    )}
    {row.days_to_checkin !== null && (
      <span className="inbox-row-days">
        {formatDaysToCheckin(row.days_to_checkin)}
      </span>
    )}
  </div>
)}
```

### 4.3 ReadinessScore.tsx — Show only missing + compact counter (Bug 5)

Modificar `apps/web/src/components/inbox/ReadinessScore.tsx`. Reemplazar el bloque `.readiness-pills`:

```diff
-      {/* Desktop ≥1024: inline pills */}
-      <div className="readiness-pills">
-        {pills.map((p) => (
-          <span key={p.label} className={`readiness-pill ${p.done ? 'done' : 'missing'}`}>
-            {p.done ? '✓' : '○'} {p.label}
-          </span>
-        ))}
-      </div>
+      {/* Desktop ≥1024: only missing pills + compact done counter */}
+      <div className="readiness-pills">
+        {pills.filter((p) => !p.done).map((p) => (
+          <span key={p.label} className="readiness-pill missing">
+            ○ {p.label}
+          </span>
+        ))}
+        {pills.some((p) => p.done) && (
+          <span
+            className="readiness-pill done compact"
+            title={tooltip}
+            aria-label={`${pills.filter((p) => p.done).length} de 6 completados`}
+          >
+            ✓{pills.filter((p) => p.done).length}
+          </span>
+        )}
+      </div>
```

El tooltip ya existe en el componente (`const tooltip = ...`). Solo reutilizamos.

### 4.4 ConversationView.tsx — Booking deep-link en error UI (Bug 3)

Modificar `apps/web/src/components/conversation/ConversationView.tsx` líneas ~135-145:

```diff
-  if (error || !data) {
-    return (
-      <div className={`conv-page${embedded ? ' conv-page-embedded' : ''}`}>
-        <div className="conv-main">
-          <div style={{ padding: 'var(--sp-4)', color: 'var(--color-error)' }}>
-            {error ?? 'Sin datos'}
-          </div>
-        </div>
-      </div>
-    );
-  }
+  if (error || !data) {
+    const bookingId = extractBookingIdFromRowId(convId);
+    return (
+      <div className={`conv-page${embedded ? ' conv-page-embedded' : ''}`}>
+        <div className="conv-main">
+          <div style={{ padding: 'var(--sp-4)', textAlign: 'center' }}>
+            <p style={{ color: 'var(--color-error)', marginBottom: 'var(--sp-3)' }}>
+              {error === 'not_found'
+                ? 'No encontramos conversación de WhatsApp para esta reserva.'
+                : (error ?? 'Sin datos')}
+            </p>
+            <div style={{ display: 'flex', gap: 'var(--sp-2)', justifyContent: 'center' }}>
+              {bookingId !== null && (
+                <a
+                  href={`/admin/bookings/${bookingId}`}
+                  className="conv-action-btn"
+                  style={{ display: 'inline-block', textDecoration: 'none' }}
+                >
+                  Ver detalle de la reserva →
+                </a>
+              )}
+              {onBack && (
+                <button
+                  type="button"
+                  className="conv-action-btn"
+                  onClick={onBack}
+                >
+                  ← Volver al inbox
+                </button>
+              )}
+            </div>
+          </div>
+        </div>
+      </div>
+    );
+  }
```

**Y agregar al import (línea ~18 aprox):**
```diff
-import { fmtDate } from '@/lib/inbox-client';
+import { extractBookingIdFromRowId, fmtDate } from '@/lib/inbox-client';
```

### 4.5 CSS — Background rows + stay-info + compact readiness (Bug 4 + supporting Bug 1 + Bug 5)

En `apps/web/src/styles/inbox.css`:

**Modificar regla `.inbox-row` existente (línea ~165 aprox):**

```diff
 .inbox-row {
+  background: var(--color-card);
   display: grid;
   grid-template-columns: 1fr auto;
   grid-template-rows: auto auto;
   gap: var(--sp-1) var(--sp-3);
   padding: var(--sp-3) var(--sp-4);
   border-top: 1px solid var(--color-border);
   cursor: pointer;
   transition: background var(--motion-fast);
   position: relative;
   text-decoration: none;
   color: inherit;
 }
```

**Agregar al final del archivo (bug 1 stay-info + bug 5 compact done):**

```css
/* thread/199 — stay info inline (pax + pet + days_to_checkin) */
.inbox-row-stay-info {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--color-text-muted);
  flex-wrap: wrap;
  grid-column: 1;
  grid-row: 1 / span 1;
}

.inbox-row-pax,
.inbox-row-days {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}

.inbox-row-days {
  font-weight: 500;
  color: var(--color-primary);
}

/* thread/199 — compact done counter (e.g. ✓2) */
.readiness-pill.compact {
  padding: 2px 5px;
  cursor: help;
}
```

(Nota: si el grid-template-rows actual de `.inbox-row` colisiona con el stay-info en row 1, el CC puede ajustar — leer el grid existente primero y poner stay-info en su propia row si más clean.)

### 4.6 CSS verification — variables a usar

Antes de modificar, CC debe **verificar que estas variables existan**:
- `--color-card` (background row)
- `--color-text-muted` (stay-info muted)
- `--color-primary` (days emphasis)
- `--sp-2`, `--sp-3`, `--fs-sm`

Si alguna no existe, grep en `apps/web/src/styles/**/*.css` para encontrar la canónica. Si verdaderamente no existen, fallback hardcoded sensible (e.g. `background: #fff` para card).

---

## §5. Tests

### 5.1 inbox-client.test.ts — Helpers nuevos

```ts
import { extractBookingIdFromRowId, formatDaysToCheckin } from '@/lib/inbox-client';

describe('extractBookingIdFromRowId', () => {
  it('parses valid b_<number> format', () => {
    expect(extractBookingIdFromRowId('b_86656366')).toBe(86656366);
    expect(extractBookingIdFromRowId('b_12345')).toBe(12345);
  });
  it('returns null for non-booking IDs', () => {
    expect(extractBookingIdFromRowId('conv_5214424441234')).toBeNull();
    expect(extractBookingIdFromRowId('5214424441234')).toBeNull();
    expect(extractBookingIdFromRowId('')).toBeNull();
  });
  it('returns null for invalid b_ formats', () => {
    expect(extractBookingIdFromRowId('b_abc')).toBeNull();
    expect(extractBookingIdFromRowId('b_-5')).toBeNull();
    expect(extractBookingIdFromRowId('b_0')).toBeNull();
  });
});

describe('formatDaysToCheckin', () => {
  it('formats future dates', () => {
    expect(formatDaysToCheckin(0)).toBe('hoy');
    expect(formatDaysToCheckin(1)).toBe('mañana');
    expect(formatDaysToCheckin(3)).toBe('T-3d');
    expect(formatDaysToCheckin(15)).toBe('T-15d');
  });
  it('formats past dates (in-stay or post-stay)', () => {
    expect(formatDaysToCheckin(-1)).toBe('ayer salió');
    expect(formatDaysToCheckin(-2)).toBe('día 2 estadía');
    expect(formatDaysToCheckin(-5)).toBe('día 5 estadía');
  });
});
```

### 5.2 InboxRow.test.ts — Display fields

Adapt al style existing del test file. Verificar:
- Row con `pax=4, has_pet=false, days_to_checkin=3` → contiene "👥 4" y "T-3d" en rendered output, NO contiene 🐶
- Row con `pax=6, has_pet=true` → contiene 🐶
- Row con `pax=null, days_to_checkin=null` → NO contiene `.inbox-row-stay-info` block

### 5.3 ReadinessScore.test.ts — Filter + counter

Verificar via test:
- Score `{ score: 2, pax_confirmed: true, pet_decided: true, ...rest false }` → desktop pills muestra 4 pills missing + 1 compact "✓2"
- Score `{ score: 6, all true }` → 0 pills missing, 1 compact "✓6"
- Score `{ score: 0, all false }` → 6 pills missing, NO compact counter (no done items)

El existing test `pillStates` se mantiene (pure function untouched).

---

## §6. Definition of Done

- [ ] Branch `fix/inbox-display-css-readiness-compact` creada
- [ ] 5 archivos modificados:
  - `apps/web/src/lib/inbox-client.ts` (+15 LoC helpers)
  - `apps/web/src/components/inbox/InboxRow.tsx` (+15 LoC stay-info)
  - `apps/web/src/components/inbox/ReadinessScore.tsx` (+10 LoC filter logic)
  - `apps/web/src/components/conversation/ConversationView.tsx` (+15 LoC error fallback)
  - `apps/web/src/styles/inbox.css` (+15 LoC: background row + 3 new classes)
- [ ] 3 archivos tests:
  - `apps/web/tests/inbox/inbox-client.test.ts` (+30 LoC)
  - `apps/web/tests/inbox/InboxRow.test.ts` (+25 LoC)
  - `apps/web/tests/inbox/ReadinessScore.test.ts` (+20 LoC)
- [ ] `pnpm --filter web typecheck` PASS 0 errors nuevos
- [ ] `pnpm --filter web test` los tests nuevos pasan
- [ ] `git diff main --stat` muestra ~8 archivos, ~150 LoC total
- [ ] PR creada con título: `fix(inbox): display fields + CSS bg + readiness compact + booking deep-link (thread/199)`
- [ ] PR description menciona Bugs 1 + 3 + 4 + 5 con referencia thread/199 y nota que bugs 2 + 6 son threads separados
- [ ] Reporte al final con:
  - 5 cambios aplicados (resumen 1 línea cada uno)
  - Tests pass count
  - PR URL
  - Recordatorio que NO requiere worker-bot redeploy (frontend-only)

---

## §7. Risks + Mitigations

| Risk | Mitigation |
|---|---|
| CSS variables (`--color-card`, etc) no existen | Verificar antes en otros archivos *.css. Si no existen, hardcode reasonable values (#fff, #666) con comment "TODO: variable" |
| Helper `formatDaysToCheckin` colisiona con función existente | `grep -rn "formatDays" apps/web/src/` antes de definir |
| Grid layout `.inbox-row` se rompe al agregar stay-info como nuevo grid item | CC debe revisar grid template existente y adaptar. Si necesario, ajustar `grid-template-rows: auto auto auto` (3 rows en vez de 2) |
| ReadinessScore counter compact "✓2" se ve raro junto a 4 pills missing | Visual ajuste post-deploy si necesario. Si Alex lo ve mal, simple tweak CSS |
| Tests rotos por cambios | NO bloquea — los pre-existentes (15 web errors) seguirán fallando. Solo tests nuevos deben pasar |
| ConversationView error fallback rompe layout drawer en desktop | Visual check post-deploy. NO bloqueador |

---

## §8. Out-of-scope findings → issues

Si CC encuentra algo durante ejecución NO listado en §2.1:
- Abrir GitHub issue con prefix `[thread/199 OOS]`
- NO fixear inline
- Reportar en thread response

Ejemplos previsibles:
- TypeScript errors pre-existentes en otros archivos → IGNORE
- Tests rotos en otros componentes → IGNORE
- Wave 1.5 followups (deploy-worker-bot.yml, MOCK_RESPONSE, etc) → DEFER
- Bug 2 conversation lookup → thread/200
- Bug 6 backend readiness in-stay → thread/201

---

## §9. Kickoff command (Alex pegará a CC)

```
DoIt thread/199: inbox display + CSS + readiness compact + booking link, 1 PR frontend-only.

Lee spec completa:
c:/dev/rdm/dev/discussion/threads/199-wc-cc-inbox-display-and-booking-link.md

(Si no la tienes local, pull discussion repo:
cd c:/dev/rdm/dev/discussion && git pull origin main && cd c:/dev/rdm/dev/bot)

Sigue §4 implementation exacto. Self-review §6 DoD antes de commit.

Working directory: c:/dev/rdm/dev/bot

Pre-flight:
1. cd c:/dev/rdm/dev/bot
2. git status — debe estar clean en main
3. git pull origin main
4. git log --oneline -1 — confirma estás en último commit (incluye PR #169 merge)

Execution:
1. git checkout -b fix/inbox-display-css-readiness-compact
2. Edit apps/web/src/lib/inbox-client.ts según §4.1 (2 helpers: extractBookingIdFromRowId + formatDaysToCheckin)
3. Edit apps/web/src/components/inbox/InboxRow.tsx según §4.2 (bloque stay-info)
4. Edit apps/web/src/components/inbox/ReadinessScore.tsx según §4.3 (filter missing + compact done counter)
5. Edit apps/web/src/components/conversation/ConversationView.tsx según §4.4 (error fallback con booking link)
6. Edit apps/web/src/styles/inbox.css según §4.5 (background row + 3 new classes)
7. Verify CSS variables existen (§4.6) — grep antes de usar
8. Add tests inbox-client.test.ts según §5.1
9. Add tests InboxRow.test.ts según §5.2
10. Add tests ReadinessScore.test.ts según §5.3
11. pnpm --filter web typecheck — must PASS 0 errors nuevos
12. pnpm --filter web test — tests nuevos pasan
13. git diff main --stat — verifica ~8 archivos
14. git add (solo los archivos esperados)
15. git commit -m "fix(inbox): display fields + CSS bg + readiness compact + booking deep-link (thread/199)"
16. git push -u origin fix/inbox-display-css-readiness-compact
17. gh pr create con title "fix(inbox): display fields + CSS bg + readiness compact + booking deep-link (thread/199)" y body con referencia thread/199, los 4 bugs resueltos (1+3+4+5), nota que bugs 2 y 6 son threads separados y que NO requiere worker-bot redeploy.

Scope ESTRICTO: frontend-only.
- apps/web/src/lib/inbox-client.ts
- apps/web/src/components/inbox/InboxRow.tsx
- apps/web/src/components/inbox/ReadinessScore.tsx
- apps/web/src/components/conversation/ConversationView.tsx
- apps/web/src/styles/inbox.css
- apps/web/tests/inbox/inbox-client.test.ts
- apps/web/tests/inbox/InboxRow.test.ts
- apps/web/tests/inbox/ReadinessScore.test.ts

NO ejecutes:
- pnpm test completo (rompen pre-existentes)
- npx wrangler deploy (no worker-bot changes)
- Backend changes (aggregate.ts, conversation.ts, inbox.ts, readiness.ts)
- Force-push, branch delete

Si encuentras algo fuera de scope → issue GitHub con prefix [thread/199 OOS].

Bloqueado >30 min en sub-tarea = STOP y reporta.

Reportar al final con:
- 5 cambios aplicados (resumen 1 línea cada uno)
- Typecheck PASS
- Tests pass count
- PR URL
- Confirmar que NO requiere worker-bot deploy

GO.
```

---

## §10. References

- thread/196: Inbox redesign megaspec
- thread/197: AirBnB flows backlog
- thread/198: Hotfix cross-origin (PR #169 merged)
- thread/200: Bug 2 conversation lookup polimórfico (a redactar)
- thread/201: Bug 6 backend computeReadiness in-stay (a redactar)
- PR #167: FE inbox scaffold (merged)
- PR #169: Hotfix CORS + roomIds (merged)
- BookingDetailView page: `apps/web/src/pages/admin/bookings/[id].astro`
- Memorias #25, #26, #27 (inbox shipped + Wave 1.5 followups)
