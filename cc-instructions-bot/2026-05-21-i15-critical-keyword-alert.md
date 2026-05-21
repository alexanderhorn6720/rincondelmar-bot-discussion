# I15 + I22 · Critical-keyword alert + "Respondí" inline button · CC DoIt spec (paired post-synthesis)

**Status**: 🟡 PAIRED · awaiting Alex Day 3 approval + H.3.8 keyword list refine
**Workstream**: CC-Bot (`apps/worker-bot` + D1 + `apps/web/src/pages/api/admin/`)
**Effort estimate**: 5h CC combined (2h I15 + 3h I22)
**Source**: §F idea I15+I22 + WC-Platform §C "loop closure" override + synthesis §D.2 resolution
**Blocking dependency**: Question H.3.8 (Alex must confirm critical keyword list)
**Updated**: 2026-05-21 ~08:10 UTC post-synthesis (merged con I22 per WC-Platform recommendation)

---

## §0 · CHANGELOG vs I15 v1 standalone

| Change | Razón |
|---|---|
| MERGE I15 (alert fire) + I22 (Respondí button) en single spec | Synthesis §D.2: paired = loop closure arquitectural. WC-Platform §C override standalone. |
| ADD §4.2 Telegram inline button + callback handler | I22 scope |
| ADD §4.3 callback handler API endpoint | I22 scope |
| ADD §4.4 D1 column `human_responded_at` migration | I22 storage |
| UPDATE effort estimate: 2h → 5h paired | I22 adds ~3h CC |
| ADD §7 risk: callback handler auth bypass | I22 security |

---

## §1 · Context

### Problem original (I15)

D1 evidence: inbox tiene 4 messages con `has_keywords_critical=1` unread × 9-day oldest. El `critical_keyword` alert type existe en schema pero firing logic a Telegram NO implementado (o broken silently). Karina no ve estos en tiempo real. SLA risk crece daily.

### Loop closure (I22 added)

Synthesis §D.2 razón: alert sin closure mechanism = backlog Telegram crece sin freno. Sin button "Respondí", Karina recibe alerts pero alert system NO sabe que respondió → cron sigue re-firing y D1 row sigue marked alerted forever.

**I22 cierra el loop**: Karina recibe alert → tap "Respondí ✅" inline button → callback marks `human_responded_at = unixepoch()` → cron skip future re-fires + `/admin/health` muestra response tracking.

### Current state (post audit + paired)

- `bot_messages_inbox` o `conversations` rows taguean `has_keywords_critical=1` cuando body matches keyword list (logic en worker-bot existing)
- Telegram bot `@RinconDelMarNotifs` (id `8667752636`) existe + Karina (id `8656647143`) + Alex (id `8711110474`) confirmados `/start`
- thread/152 PR #136 (`feat/karina-tg-distribution`) added Karina TG infrastructure
- `/admin/health` page renders `bot_alerts` recent 10 read-only

### Desired behavior (paired)

1. **I15 fire**: when NEW row `has_keywords_critical=1` AND `age > N min` (default 30) AND NOT alerted yet → fire Telegram **CON inline button** "Respondí ✅" + " 🔇 Snooze 4h"
2. **I22 close**: Karina/Alex taps button → callback handler updates D1 (`human_responded_at` o `snoozed_until`) → cron skip future re-fires
3. Track all loops via `bot_alerts` columns: `alerted_at`, `human_responded_at`, `responder_tg_id`, `snoozed_until`

---

## §2 · Explicit scope

### YES (paired)

**I15 base** (~2h):
- New cron `cron-critical-keyword-alerts` running every 5 minutes
- Query D1 para rows con `has_keywords_critical=1` AND `alerted_at IS NULL` AND `created_at < unixepoch() - 30*60`
- Fire Telegram message a Karina + Alex con inline buttons
- Idempotent: writes `alerted_at = unixepoch()` después de fire successful
- Heartbeat: write to `cron_heartbeat:critical-keyword-alerts` KV key
- Telegram message format: guest phone (last 4), property, preview (100 chars), link `/admin/conv?phone={partial}`
- Hardcoded keyword list en `packages/shared/src/critical-keywords.ts` (NEW)
- Test mode env var `CRITICAL_KEYWORD_ALERT_DRY_RUN`

**I22 paired** (~3h additional):
- Telegram inline keyboard con 2 buttons: "Respondí ✅" + "🔇 Snooze 4h"
- Callback handler endpoint `POST /api/telegram/callback` (or worker-bot webhook handler)
- D1 migration: add `human_responded_at INTEGER NULL`, `responder_tg_id TEXT NULL`, `snoozed_until INTEGER NULL` a `bot_alerts`
- Cron query filter: skip rows where `human_responded_at IS NOT NULL` OR `snoozed_until > unixepoch()`
- Edit Telegram message post-callback: replace inline buttons con plain text "✅ Karina respondió hace Xmin"
- `/admin/health` page muestra response tracking: alerts fired vs responded vs pending

### NO (paired)

- DO NOT change keyword detection logic (already exists)
- DO NOT add per-recipient acknowledgment (Alex tap = both close — first-respond wins)
- DO NOT add escalation pager (no response in 4h) — Phase 2
- DO NOT add severity split (emergencia vs infraestructura) — Phase 2
- DO NOT touch other Telegram bot handlers (Karina TG distribution PR #136 separate)

---

## §3 · Closed decisions

- **Grace period**: 30 minutes pre-alert
- **Frequency**: every 5min cron tick
- **Recipients**: BOTH Karina + Alex (redundancy)
- **First-respond wins**: primer tap cierra alert para ambos
- **Snooze duration**: 4 horas (matches manual outreach window)
- **Callback security**: verify `callback_query.from.id` ∈ allowed list [KARINA_TG_ID, ALEX_TG_ID] before processing
- **Message edit on response**: yes, post-tap remove buttons + show responder + time
- **Critical keywords**: hardcoded list `packages/shared/src/critical-keywords.ts` (edit via PR)
- **Link format**: `https://rincondelmar.club/admin/conv?phone={last4}`

### BLOCKING question (H.3.8)

**¿Qué keywords cuentan como "critical"?**

WC-Impl propuesta initial (20 items, ESPAÑOL lowercase normalized):
```
emergencias personales:
  emergencia, urgente, ambulancia, policia, bomberos,
  robo, asalto, accidente, lesion, sangre, hospital

infraestructura critica:
  fuego, incendio, inundacion,
  no funciona el aire, no hay agua, no hay luz

booking-impact:
  cancelar, reembolso, demanda
```

Alex puede aprobar as-is, agregar/quitar, o replace.

---

## §4 · Implementation

### §4.1 · `packages/shared/src/critical-keywords.ts` (NEW, common)

```typescript
/**
 * Critical keywords trigger Telegram alerts to Karina + Alex.
 * Edit via PR — Alex curates.
 */
export const CRITICAL_KEYWORDS: ReadonlyArray<string> = [
  // EMERGENCIAS PERSONALES
  'emergencia', 'urgente', 'ambulancia', 'policia', 'bomberos',
  'robo', 'asalto', 'accidente', 'lesion', 'sangre', 'hospital',

  // INFRAESTRUCTURA CRITICA
  'fuego', 'incendio', 'inundacion',
  'no funciona el aire', 'no hay agua', 'no hay luz',

  // BOOKING-IMPACT
  'cancelar', 'reembolso', 'demanda',
];

export function normalizeForMatch(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

export function matchCriticalKeywords(text: string): string[] {
  const normalized = normalizeForMatch(text);
  return CRITICAL_KEYWORDS.filter(kw => normalized.includes(normalizeForMatch(kw)));
}
```

### §4.2 · Migration · bot_alerts columns (I22 prereq)

`apps/worker-bot/migrations/0040_bot_alerts_response_tracking.sql`:

```sql
ALTER TABLE bot_alerts ADD COLUMN human_responded_at INTEGER NULL;
ALTER TABLE bot_alerts ADD COLUMN responder_tg_id TEXT NULL;
ALTER TABLE bot_alerts ADD COLUMN snoozed_until INTEGER NULL;
ALTER TABLE bot_alerts ADD COLUMN telegram_message_id TEXT NULL; -- for editing post-response

CREATE INDEX idx_bot_alerts_response_pending
  ON bot_alerts(human_responded_at, alerted_at, snoozed_until)
  WHERE human_responded_at IS NULL;
```

### §4.3 · Cron handler with inline buttons (I15+I22 combined)

`apps/worker-bot/src/handlers/cron-critical-keyword-alerts.ts`:

```typescript
import { writeHeartbeat } from '../lib/cron-heartbeat';
import { sendTelegramMessage } from '../lib/telegram';

const KARINA_TG_ID = '8656647143';
const ALEX_TG_ID = '8711110474';
const GRACE_PERIOD_SECONDS = 30 * 60;

const ROOM_NAMES: Record<number, string> = {
  78695: 'Rincón del Mar',
  74322: 'Las Morenas',
  374482: 'Las Morenas',
  74316: 'Combinada',
  637063: 'Huerta Cocotera',
};

export async function handleCriticalKeywordAlerts(env: Env): Promise<void> {
  await writeHeartbeat(env.KV_KNOWLEDGE, 'critical-keyword-alerts');

  if (!env.DB) {
    console.error('[critical-keyword-alerts] No DB binding');
    return;
  }

  const dryRun = env.CRITICAL_KEYWORD_ALERT_DRY_RUN === 'true';
  const cutoff = Math.floor(Date.now() / 1000) - GRACE_PERIOD_SECONDS;
  const now = Math.floor(Date.now() / 1000);

  // Query unalerted rows (I15) OR snooze-expired rows (I22)
  const { results } = await env.DB.prepare(
    `SELECT id, booking_id, room_id, channel, body_preview as preview,
            guest_phone, created_at
       FROM bot_alerts
      WHERE has_keywords_critical = 1
        AND human_responded_at IS NULL
        AND (alerted_at IS NULL OR snoozed_until < ?)
        AND created_at < ?
      ORDER BY created_at ASC
      LIMIT 20`
  ).bind(now, cutoff).all<{
    id: number;
    booking_id: string | null;
    room_id: number | null;
    channel: string | null;
    preview: string;
    guest_phone: string | null;
    created_at: number;
  }>();

  if (!results || results.length === 0) return;

  for (const row of results) {
    const phoneLast4 = row.guest_phone?.slice(-4) ?? '????';
    const propertyName = row.room_id ? (ROOM_NAMES[row.room_id] ?? `room ${row.room_id}`) : '—';
    const preview = (row.preview ?? '').slice(0, 100);
    const ageMinutes = Math.floor((now - row.created_at) / 60);

    const message = [
      `🚨 Mensaje crítico (${ageMinutes}min)`,
      ``,
      `Propiedad: ${propertyName}`,
      `Canal: ${row.channel ?? 'desconocido'}`,
      `Teléfono: ****${phoneLast4}`,
      ``,
      `"${preview}${preview.length >= 100 ? '...' : ''}"`,
      ``,
      `→ https://rincondelmar.club/admin/conv?phone=${phoneLast4}`,
    ].join('\n');

    // I22 paired: inline keyboard
    const inlineKeyboard = {
      inline_keyboard: [[
        { text: '✅ Respondí', callback_data: `respondi:${row.id}` },
        { text: '🔇 Snooze 4h', callback_data: `snooze:${row.id}` },
      ]],
    };

    if (dryRun) {
      console.log(`[critical-keyword-alerts] DRY RUN message:\n${message}\nKeyboard: ${JSON.stringify(inlineKeyboard)}`);
    } else {
      try {
        // Send to Karina + Alex con buttons
        const responses = await Promise.all([
          sendTelegramMessage(env, KARINA_TG_ID, message, { reply_markup: inlineKeyboard }),
          sendTelegramMessage(env, ALEX_TG_ID, message, { reply_markup: inlineKeyboard }),
        ]);

        // Persist telegram_message_id de Karina's msg (for edit later on callback)
        const karinaMsgId = responses[0]?.message_id?.toString() ?? null;

        await env.DB.prepare(
          `UPDATE bot_alerts
              SET alerted_at = unixepoch(),
                  telegram_message_id = ?
            WHERE id = ?`
        ).bind(karinaMsgId, row.id).run();
      } catch (err) {
        console.error(`[critical-keyword-alerts] Failed to alert row ${row.id}:`, err);
        // DO NOT mark as alerted — will retry next cron tick
      }
    }
  }
}
```

### §4.4 · Callback handler (I22 NEW)

`apps/worker-bot/src/handlers/telegram-callback.ts`:

```typescript
const KARINA_TG_ID = '8656647143';
const ALEX_TG_ID = '8711110474';
const ALLOWED_RESPONDERS = new Set([KARINA_TG_ID, ALEX_TG_ID]);

export async function handleTelegramCallback(env: Env, update: TelegramUpdate): Promise<Response> {
  const callback = update.callback_query;
  if (!callback) return new Response('No callback', { status: 400 });

  // Security: verify responder ∈ allowed list
  const responderId = callback.from.id.toString();
  if (!ALLOWED_RESPONDERS.has(responderId)) {
    console.warn(`[telegram-callback] Unauthorized responder: ${responderId}`);
    return new Response('Unauthorized', { status: 403 });
  }

  const data = callback.data ?? '';
  const [action, alertIdStr] = data.split(':');
  const alertId = parseInt(alertIdStr, 10);

  if (!alertId || (action !== 'respondi' && action !== 'snooze')) {
    return new Response('Invalid callback', { status: 400 });
  }

  if (action === 'respondi') {
    await env.DB.prepare(
      `UPDATE bot_alerts
          SET human_responded_at = unixepoch(),
              responder_tg_id = ?
        WHERE id = ? AND human_responded_at IS NULL`
    ).bind(responderId, alertId).run();

    // Edit message: remove buttons, add status
    const responderName = responderId === KARINA_TG_ID ? 'Karina' : 'Alex';
    const editedText = `${callback.message?.text ?? ''}\n\n✅ ${responderName} respondió`;
    await editTelegramMessage(env, callback.message?.chat?.id, callback.message?.message_id, editedText);
  } else if (action === 'snooze') {
    const snoozeUntil = Math.floor(Date.now() / 1000) + (4 * 60 * 60); // 4h
    await env.DB.prepare(
      `UPDATE bot_alerts
          SET snoozed_until = ?,
              responder_tg_id = ?
        WHERE id = ? AND human_responded_at IS NULL`
    ).bind(snoozeUntil, responderId, alertId).run();

    const responderName = responderId === KARINA_TG_ID ? 'Karina' : 'Alex';
    const editedText = `${callback.message?.text ?? ''}\n\n🔇 ${responderName} snoozed por 4h`;
    await editTelegramMessage(env, callback.message?.chat?.id, callback.message?.message_id, editedText);
  }

  // Acknowledge the callback (removes loading indicator)
  await answerCallbackQuery(env, callback.id);

  return new Response('OK', { status: 200 });
}
```

### §4.5 · Route wiring

`apps/worker-bot/src/index.ts`:

```typescript
// Cron registration
case 'critical-keyword-alerts':
  await handleCriticalKeywordAlerts(env);
  break;

// Webhook routing
// Telegram bot already receives /webhook → handle 'callback_query' update type:
if (update.callback_query) {
  return handleTelegramCallback(env, update);
}
```

### §4.6 · `wrangler.toml` addition

```toml
[triggers]
crons = [
  # ... existing crons ...
  "*/5 * * * *",  # critical-keyword-alerts
]
```

**WARNING**: Free plan allows max 5 crons. Verify current count first.

### §4.7 · `/admin/health` extension

Add to `lib/admin-health.ts` cron map: `critical-keyword-alerts`.

Add new section to `health.astro` showing alert response tracking:

```sql
SELECT
  COUNT(*) FILTER (WHERE alerted_at IS NOT NULL) AS alerts_fired,
  COUNT(*) FILTER (WHERE human_responded_at IS NOT NULL) AS alerts_responded,
  COUNT(*) FILTER (WHERE snoozed_until > unixepoch()) AS alerts_snoozed,
  COUNT(*) FILTER (WHERE has_keywords_critical=1 AND alerted_at IS NULL) AS alerts_pending,
  AVG(human_responded_at - alerted_at) AS avg_response_seconds
FROM bot_alerts
WHERE created_at > unixepoch() - (7 * 24 * 60 * 60);
```

---

## §5 · Tests

### Unit tests (`packages/shared`)

`critical-keywords.test.ts`:
- matches exact keyword
- matches case-insensitive
- matches accent-insensitive
- matches multi-word phrase
- no false positive on contained words
- multiple matches returned

### Integration tests (`apps/worker-bot`)

`cron-critical-keyword-alerts.test.ts`:
- seed bot_alerts row con `has_keywords_critical=1`, `alerted_at=NULL`, `created_at = now - 60min`
- Run handler en dry-run mode → assert log + dry-run buttons format
- Run handler real → assert sendTelegramMessage called 2x + DB updated
- Seed second row con `created_at = now - 5min` (dentro grace) → skip
- Seed third row con `human_responded_at` SET → skip

`telegram-callback.test.ts`:
- Unauthorized responder → 403
- Valid responder + action='respondi' → DB updated + message edited
- Valid responder + action='snooze' → DB updated con snoozed_until = now + 4h
- Invalid action → 400

### Smoke test (manual, post-deploy)

1. Send WhatsApp message a bot con "emergencia" content
2. Wait 30+ minutes
3. Confirm Telegram alert arrives a Karina + Alex con 2 inline buttons
4. Karina taps "Respondí ✅" → confirm message edits con "✅ Karina respondió"
5. Confirm en `/admin/health`: alerts_responded counter incrementa
6. Re-run cron manually → confirm NO duplicate alert (skip por `human_responded_at IS NOT NULL`)
7. Trigger new critical alert → Alex taps "🔇 Snooze 4h" → confirm message edits
8. Re-run cron < 4h después → confirm skip
9. Re-run cron > 4h después → confirm re-fires (snooze expired)
10. Mobile Telegram client: buttons rendered correctly + tappable

---

## §6 · Definition of done

- [ ] Migration `0040_bot_alerts_response_tracking.sql` applied prod + verified
- [ ] `critical-keywords.ts` shipped con curated list (Alex-approved)
- [ ] `cron-critical-keyword-alerts.ts` handler con inline buttons implemented
- [ ] `telegram-callback.ts` handler implementado con auth check
- [ ] `wrangler.toml` cron trigger added (verify cap on Free plan)
- [ ] `health.astro` muestra response tracking section
- [ ] All unit + integration tests pass
- [ ] Smoke test 10 steps pass on staging/prod
- [ ] Dry-run mode confirmed via env var toggle
- [ ] PR opened con: link to this spec + manual smoke test screenshots + ADR-004 reference

---

## §7 · Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Workers FREE plan cap (5 crons) | high | Audit existing crons FIRST. If at cap, consolidate (e.g., merge into existing `cron-bot-alerts` handler). |
| `bot_alerts` table doesn't have all expected columns | medium | Run migration 0040 FIRST. Verify schema con `pragma table_info(bot_alerts)`. |
| Karina+Alex spam if many critical messages | medium | 30min grace + idempotency via `alerted_at`. Snooze button gives Karina escape valve. |
| Callback handler auth bypass | medium | Hardcoded `ALLOWED_RESPONDERS` set + 403 response. Verify telegram_user_id from update payload, NOT from callback_data. |
| Keyword list too narrow → misses real emergencies | medium | Alex curates v1; iterate based on missed cases via Karina feedback (I2 ships post-Wave 2). |
| Keyword list too broad → false positives spam | medium | Same. Snooze button mitigates. |
| `sendTelegramMessage` lib lacks `reply_markup` support | medium | Check PR #136 lib. If not present → extend with inline_keyboard param FIRST (~30min addition). |
| Telegram webhook routes both bot commands + callbacks | low | Branch update payload type: `update.message` vs `update.callback_query`. Existing handlers for `update.message` untouched. |
| Race condition: 2 callbacks tap "Respondí" simultaneous | low | SQL `WHERE human_responded_at IS NULL` guard ensures first-write-wins. Second callback no-op. |
| Casa Chamán (679176) accidentally surfaces | low | `ROOM_NAMES` map omits 679176 — fall-through "room 679176" acceptable. Same exclusion como `/admin/pre-stay`. |

---

## §8 · Sequencing

1. **PRE-PICKUP**: Alex resolves H.3.8 keyword list (~15min Alex)
2. CC: branch `feat/i15-i22-critical-keyword-alerts-paired` (~5min)
3. CC: verify `bot_alerts` schema + cron cap + telegram lib (~15min)
4. CC: migration 0040 + apply local (~15min)
5. CC: `critical-keywords.ts` + unit tests (~20min)
6. CC: cron handler con inline buttons (~45min)
7. CC: callback handler + auth (~45min)
8. CC: integration tests both handlers (~45min)
9. CC: route wiring + wrangler config (~20min)
10. CC: health.astro response tracking section (~20min)
11. CC: dry-run + lint + tsc (~15min)
12. CC: open PR linking ADR-004 + synthesis §D.2 (~10min)
13. Alex: review + apply migration prod + merge + verify Telegram (~30min)
14. Alex: smoke test 10 steps async (~45min real-time)

Total CC: ~5h. Total Alex: ~1.5h.

---

## §9 · Out of scope (deferred Phase 2)

- Per-recipient acknowledgment (Karina vs Alex tracks)
- Escalation pager (no response in 4h + no snooze → escalate to Alex by call)
- Severity split (emergencia vs infraestructura vs booking-impact con different SLA)
- Per-keyword on/off toggle en admin UI
- Custom snooze durations
- "Reassign to Alex/Karina" button para hand-off

---

## §10 · Coordination con Wave 3

I15+I22 ship juntos = Wave 3 complete. Dependencies:
- Pre-req: I0 shipped (Wave 0) — NO técnica, sólo evita confusión durante prod testing
- Pre-req: Alex keyword list resolved (H.3.8) — BLOCKER

Post-ship:
- Wave 4 I1 AskClaude puede usar `bot_alerts` table for `historical incidents` queries (G6 tool whitelist allows read)
- I2 feedback channel post-Wave 2 puede agregar "alert no era crítico" como type='note-to-alex'

---

**Spec sealed paired** por WC-Implementation 2026-05-21 ~08:15 UTC post-synthesis. Pending Alex Day 3 approval + H.3.8 resolution → CC pickup. Loop closure architecture per WC-Platform §C override.
