# I0 · Welcome auto-send rebuild · CC DoIt spec

**Status**: 🔴 P0 · awaiting Alex path-forward decision · spec pre-staged
**Workstream**: CC-Bot (`apps/worker-bot` + D1 + `apps/web/src/pages/admin/pre-stay.astro`)
**Effort estimate**: 4-8h CC (depends on path chosen)
**Source**: §10 of `reports/admin-audit-2026-Q2-v2/` · thread/157 P0 alert · audit-2026-Q2 follow-up F-6
**Discovery**: D1 evidence query 2026-05-21 ~05:30 UTC during Day 1 second-pass audit

---

## §1 · Context

### Problem (urgency real-time)

Sara Ramos llega **2026-05-22**. NO tiene welcome record. 10 bookings con arrival próximas 14 días en igual estado.

`pending_welcomes` table tiene 10 rows TODOS `status='rejected'` desde `manual_batch_reject_2026-05-14`. Nuevos bookings NO están entrando a la tabla — el flow underlying NO está creando rows.

Karina ve `/admin/pre-stay` mostrando los 10 rejected, pero NO ve los 10 sin record. Operación silente.

### D1 evidence

```sql
-- Bookings próximos 14d sin welcome record:
SELECT bb.beds24_booking_id, bb.arrival, g.name, pw.status
FROM beds24_bookings bb
LEFT JOIN guests g ON g.id = bb.guest_id
LEFT JOIN pending_welcomes pw ON pw.beds24_booking_id = bb.beds24_booking_id
WHERE bb.arrival >= date('now') AND bb.arrival <= date('now','+14 days')
  AND bb.status NOT IN ('cancelled','archived')
  AND bb.room_id != 679176;
-- → 10 rows, TODOS pw.status NULL
```

### Compound issue · messenger_outbound 92% fail

Incluso si pending_welcomes rebuild → sends usan `messenger_outbound`. 1039 failed vs 88 sent cumulative. Most failures = "Subscriber does not exist" ManyChat tracking broken.

I0 NO arregla messenger_outbound (audit-2026-Q2 F-1 task separate). I0 SÍ arregla la generación + visibility.

---

## §2 · Explicit scope

### Path-forward selection (BLOCKER · Alex decides al despertar)

| Path | Effort | Risk | Description |
|---|---|---|---|
| (a) Reactivate flow con template ACTUAL | 4h CC | template imperfecto pero algo > nada | Restart pending_welcomes generation con current R2 template (last good before reject) |
| (b) Manual backfill 10 bookings | 1h CC + Alex review | tedious, no scaling | Insert 10 rows manualmente vía SQL + Karina aprueba uno a uno |
| (c) Accept gap hasta template nuevo | 0h CC | 10 bookings sin contacto + Sara mañana | Reject I0 hasta template rebuild listo (separate workstream) |

**Voto WC**: (a). Sara mañana > template perfection. Path (b) si Alex prefiere control granular.

### YES (regardless of path)

1. Investigate root cause cron broken (¿por qué pending_welcomes NO gana nuevas rows?)
2. Add visibility en `/admin/pre-stay`: "Sin record" section (bookings sin row en pending_welcomes)
3. Add Telegram alert: "X bookings arriving <72h sin welcome record"
4. Document fix en thread/158 + changelog

### Path-specific YES

**Path (a)**:
5. Restore cron generation con current R2 template
6. Run catch-up para 10 backlogged bookings con `status='approval_pending'`
7. Karina aprueba via existing UI flow

**Path (b)**:
5. INSERT 10 rows manualmente vía SQL con `status='approval_pending'`
6. Skip restore — solo manual generation per-booking via SQL

**Path (c)**:
5. SKIP. Just deploy `/admin/pre-stay` visibility + Telegram alert.

### NO (all paths)

- DO NOT touch messenger_outbound flow (separate audit-2026-Q2 F-1)
- DO NOT modify template content (separate spec — Karina training v2 spec thread/151)
- DO NOT mass-deploy welcomes sin Karina approval (preserve current `approval_pending` gating)
- DO NOT delete the 10 `rejected` rows (history preservation)

---

## §3 · Closed decisions

- **Telegram alert threshold**: 72h before arrival (lead time matches manual outreach window)
- **/admin/pre-stay "Sin record" section**: above the existing pending_welcomes table (greater attention)
- **Cron schedule for generation**: keep existing (per current bot config)
- **Approval flow**: preserve current `approval_pending` → Karina aprueba (no auto-approve)
- **R2 template version**: per path-forward choice (a uses current, b/c skips)

---

## §4 · Implementation (per path)

### §4.1 · Investigation phase (BEFORE writing fixes, ~30min)

```bash
# 1. ¿Qué cron debería generar pending_welcomes rows?
grep -ri "pending_welcomes" apps/worker-bot/src/
grep -ri "INSERT INTO pending_welcomes" apps/worker-bot/

# 2. ¿Cuándo fue último insert?
# wrangler d1 query rincon --command "SELECT MAX(created_at), datetime(MAX(created_at),'unixepoch') FROM pending_welcomes"

# 3. ¿Hay heartbeat de cron-pre-stay-* en bot worker?
# Check cron schedules in apps/worker-bot/wrangler.toml

# 4. ¿Tabla cron_heartbeats tiene entries del cron relevante?
# wrangler d1 query rincon --command "SELECT DISTINCT cron_name, MAX(heartbeat_at) FROM cron_heartbeats WHERE cron_name LIKE '%welcome%' OR cron_name LIKE '%pre-stay%' GROUP BY cron_name"
```

Output investigation: which cron + last fire time + likely root cause. Add to PR description.

### §4.2 · Common to all paths · `/admin/pre-stay` visibility (~2h)

File: `apps/web/src/pages/admin/pre-stay.astro`

Add new "Sin record" section ABOVE existing pending_welcomes table:

```typescript
// New query (server-side)
const bookingsSinRecord = await env.DB.prepare(
  `SELECT bb.beds24_booking_id, bb.room_id, bb.channel, bb.arrival, bb.departure,
          bb.num_adults, bb.num_pets,
          g.name AS guest_name, g.phone_e164 AS guest_phone
     FROM beds24_bookings bb
     LEFT JOIN guests g ON g.id = bb.guest_id
     LEFT JOIN pending_welcomes pw ON pw.beds24_booking_id = bb.beds24_booking_id
    WHERE bb.arrival >= date('now')
      AND bb.arrival <= date('now', '+60 days')
      AND bb.status NOT IN ('cancelled','archived')
      AND bb.room_id != 679176
      AND pw.beds24_booking_id IS NULL
    ORDER BY bb.arrival ASC`
).all();
```

UI:
```astro
{bookingsSinRecord.results.length > 0 && (
  <section class="sin-record-alert">
    <h2>⚠️ Bookings sin welcome record ({bookingsSinRecord.results.length})</h2>
    <p>
      Estos bookings NO tienen entry en pending_welcomes. Sin atención manual
      o reactivación del flow, no recibirán welcome automatizado.
    </p>
    <table>
      <thead><tr>
        <th>Arrival</th><th>Property</th><th>Huésped</th><th>Phone</th><th>Acciones</th>
      </tr></thead>
      <tbody>
        {bookingsSinRecord.results.map(b => (
          <tr class={daysUntil(b.arrival) <= 3 ? 'urgent' : ''}>
            <td>{b.arrival} ({daysUntil(b.arrival)}d)</td>
            <td>{PROPERTY_NAMES[b.room_id]}</td>
            <td>{b.guest_name ?? '—'}</td>
            <td>{b.guest_phone ?? '—'}</td>
            <td>
              <button data-booking={b.beds24_booking_id} class="btn-create-pw">
                Crear pending welcome
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
)}
```

Backend endpoint `POST /api/admin/pre-stay/create-pending-welcome` que toma `beds24_booking_id` + crea row con `status='approval_pending'`.

### §4.3 · Path (a) · Reactivate cron generation (~2h)

After investigation identifies broken cron:
1. Fix root cause (likely template R2 key missing, polling logic regression, or cron disabled)
2. Run one-off catch-up: insert rows para 10 backlogged bookings con current template
3. Verify cron fires next iteration (heartbeat updates)
4. Smoke test: nuevo booking webhook → row aparece en pending_welcomes en <5min

### §4.4 · Path (b) · Manual backfill SQL (~1h)

```sql
-- Para cada de las 10, ejecutar:
INSERT INTO pending_welcomes (
  id, beds24_booking_id, beds24_event_id, room_id, channel,
  guest_first_name, arrival, departure, num_nights, group_size,
  template_r2_key, template_content_snapshot,
  personalized_text, llm_model, llm_tokens_in, llm_tokens_out, llm_cache_hit,
  status, created_at, updated_at
) VALUES (
  '<uuid>', <booking_id>, NULL, <room_id>, '<channel>',
  '<first_name>', '<arrival>', '<departure>', <nights>, <group>,
  'welcomes/<template_key>.md', '<snapshot>',
  '<personalized>', 'claude-haiku-4-5', 0, 0, 0,
  'approval_pending', unixepoch(), unixepoch()
);
```

Karina aprueba 10 manualmente vía UI existente.

### §4.5 · Common to all paths · Telegram alert (~1h)

New cron (or reuse existing) que cada 6h verifica:
```sql
SELECT COUNT(*) FROM beds24_bookings bb
LEFT JOIN pending_welcomes pw ON pw.beds24_booking_id = bb.beds24_booking_id
WHERE bb.arrival >= datetime('now')
  AND bb.arrival <= datetime('now', '+72 hours')
  AND bb.status NOT IN ('cancelled','archived')
  AND bb.room_id != 679176
  AND (pw.beds24_booking_id IS NULL OR pw.status != 'sent');
```

Si count > 0: Telegram alert a Karina + Alex con lista de phone numbers + arrivals.

---

## §5 · Tests

### Unit tests

- `pending_welcomes.test.ts`: insert row valido → status='approval_pending'
- `admin/pre-stay.test.ts`: query bookingsSinRecord retorna rows con LEFT JOIN NULL

### Smoke test (manual)

1. Verify `/admin/pre-stay` muestra "Sin record" section con las 10 bookings
2. Path (a): Verify nuevo booking webhook → row aparece en pending_welcomes
3. Path (b): Verify SQL inserts → rows aparecen con `status='approval_pending'`
4. Telegram alert dispara con count > 0
5. Mobile 320px: layout no rompe

---

## §6 · Definition of done

- [ ] Investigation root cause documented en PR description
- [ ] `/admin/pre-stay` muestra "Sin record" section visible para Karina
- [ ] Path-specific: pending_welcomes rows existen para los 10 bookings
- [ ] Telegram alert fires correctly with count > 0
- [ ] Sara Ramos (arrival 2026-05-22) tiene welcome enviado manual O en pending_welcomes
- [ ] PR opened linking to thread/157 + §10 second-pass audit
- [ ] Smoke test 5 steps pass locally
- [ ] No regressions en /admin/pre-stay existing functionality

---

## §7 · Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Template R2 key missing → path (a) sends mensaje incorrect | medium | Verify template key exists ANTES de catch-up. Use template original que funcionó antes de reject batch. |
| Karina overwhelmed con 10 aprovals simultáneos | medium | Sequence backfill por arrival proximity (Sara primero, luego Claudia, etc) |
| messenger_outbound 92% fail rate → welcomes generados no llegan | high | Document separately. NOT blocked por este spec. Track en audit-2026-Q2 F-1 followup. |
| Cron generation root cause harder than expected | medium | Time-box investigation a 30min. Si no resuelve, switch to path (b) manual backfill |
| Telegram alert noisy | low | Threshold count > 3 antes de fire alert (config) |

---

## §8 · Sequencing

### Path (a) recomendado

1. CC: branch `feat/i0-welcome-autosend-rebuild` (5min)
2. CC: investigation phase ~30min, document findings
3. CC: implement `/admin/pre-stay` "Sin record" section (2h)
4. CC: investigate + fix cron + run catch-up (2h)
5. CC: Telegram alert wiring (1h)
6. CC: smoke test + tsc + lint (30min)
7. CC: open PR linking thread/157 + §10 (10min)
8. Alex: review + merge + deploy (30min)
9. Alex/Karina: verify Sara/Claudia/Erik tienen welcomes (manual o auto-generated) antes de 2026-05-22 noon

Total CC: ~6h. Total Alex: ~30-45min. Target: Sara protegida antes de mañana noon.

### Path (b) sequencing

1-3 igual
4. CC: manual SQL backfill (30min)
5. CC: telegram alert (1h)
6-8 igual

Total CC: ~4h.

---

## §9 · Out of scope (future iteration)

- Fix messenger_outbound 92% fail rate (audit-2026-Q2 F-1, separate)
- Rebuild template content (thread/151 Karina training v2 spec)
- Auto-approval flow (preserve current `approval_pending` Karina gate)
- Multi-language welcome variants
- Per-property template customization beyond current state

---

## §10 · Coordination con Day 3 ranking

Si esto se ship antes de Day 3 → Top 5 ranking refresh:
- I0 ✅ shipped
- Originales Top 5 (I21/I2/I15/I13+I14/I1) siguen pendientes
- Adjust §F.5 voto WC

Si Alex elige path (c) → I0 NO ship hasta template nuevo listo. Welcomes manuales hasta entonces. Asumir 2-3 días gap.

---

**Spec sealed** por WC-Implementation 2026-05-21 ~05:50 UTC. Pending Alex path-forward decision al despertar. Pre-staged para CC pickup inmediato post-vote.
