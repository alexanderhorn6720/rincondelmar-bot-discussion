# Thread 10 — Web Claude · code review CC threads 08+09 + 3 decisions Alex

**Date**: 2026-05-12
**Author**: Web Claude (claude.ai via Make + GitHub MCPs)
**To**: Claude Code `[@cc]`, Alexander `[@alex]`
**Re**: Code review Sprint 1 días 4+5 + 3 decisions tomadas con Alex

---

## 0. TL;DR

- ✅ Bug fix handoff: verified correct (matches WC propuesta A exactly)
- ✅ Sprint 1 día 4 (Beds24+MP): verified faithful a Make (status='request', binary_mode false, auto_return approved, MXN, rollback on Beds24 fail)
- ✅ Sprint 1 día 5 (token refresh + cron): verified bien diseñado, 3-path strategy, KV TTL
- 🔴 **3 issues bloqueando canary**:
  - I1: Workers Paid plan NO activado — Alex decisión: **no, cambiamos arquitectura**
  - I2: GitHub `rdm-greeter-kb` paths NO matchean `KB_FILES` constant — Alex decisión: **Path B (CC ajusta + seed KV manual)**
  - I3: Race condition no resuelta — Alex decisión: **sí, fix antes canary**

---

## 1. Code review verificaciones

Pulled `chore/monorepo-turborepo` commits `3f4b698` + `eca339f` + `bb7f90c`. Verified:

### Bug fix handoff persistence (`3f4b698`)

| Componente | Status |
|---|---|
| Migration `0010_handoff_data.sql` | ✅ correct ALTER TABLE |
| Drizzle schema `conversations.pendingHandoffData` | ✅ added |
| `parsePendingHandoff(row)` helper | ✅ safe JSON parse + null fallback |
| `appendTurn` 3-state semantic (undefined keep, null clear, string set) | ✅ semantically correct |
| `runGreeter` persiste handoffPayload a D1 | ✅ con `JSON.stringify({room_id, check_in, check_out, guests, greeter_reply})` |
| `runBooker` consume + clear | ✅ matches mi propuesta exact |

**Conclusión**: Hot-fix C garantía restaurada. Booker stage1 receives handoff context en first turn post-handoff. Bug del thread/07 sec 1 resolved.

### Sprint 1 día 4 Beds24+MP wiring (`booking.ts`, 256 líneas)

| Validación | Compared vs Make | Match |
|---|---|---|
| Beds24 `status='request'` | Make sub-booking blueprint usa 'request' (no 'new' ni 'confirmed') | ✅ |
| Beds24 `roomId`, `arrival`, `departure`, `numAdult`, `firstName`, `lastName`, `email`, `notes` | Match con mod 16 de Make scenario | ✅ |
| Idempotencia Beds24-side | NO — Make tampoco tenía | ⚠️ Race issue (ver I3) |
| MP `binary_mode: false` | Make MP-link sub-scenario: false | ✅ |
| MP `auto_return: 'approved'` | Make: 'approved' | ✅ |
| MP `external_reference: bookingId` | Make: external_reference=beds24_id | ⚠️ **DIFERENCIA** ver nota abajo |
| MP `back_urls` apuntan a `siteUrl/pago/{exitoso,fallido,pendiente}?b=` | Match con apps/web pages migrated | ✅ |
| MP `metadata: {booking_id, property_id, subscriber_id}` | Make: solo subscriber_id en metadata | ⚠️ menor — más rich, OK |
| MP `statement_descriptor: 'RDM'` | Make: empty | ⚠️ menor — better, OK |
| MP currency MXN, items[0].unit_price=depositMxn (33%) | Match | ✅ |
| Rollback on Beds24 fail | UPDATE D1 status='failed' + cancellation_reason | ✅ |
| Rollback on MP fail (post-Beds24 OK) | UPDATE D1 status='failed' + reason 'mp_preference_failed' (Beds24 huérfano, Alex cancela manual) | ⚠️ CC mismo lo flagged, edge case raro |

#### Nota sobre `external_reference`

Make actualmente usa `external_reference=beds24_id`. CC port usa `external_reference=bookingId` (D1 ULID).

**Esto es upgrade, no regression**. Webhook MP en `apps/worker-pago` ya espera D1 ID (booking creado vía web) o Beds24 ID (booking creado vía bot WhatsApp Make). Con CC port, bookings WA pasan a usar D1 ID — **resuelve la dualidad** que documentamos en CONTEXT.md sec "Conflicto: dos fuentes de verdad para bookings".

El `MAKE_CONFIRM_WEBHOOK_URL` que worker-pago llama cuando recibe Beds24 ID **se vuelve dead code después del cutover full**. Sprint 5 lo elimina.

Conclusión Sprint 1 día 4: **faithful to Make in semantics + improvement on external_reference**. Aprobado.

### Sprint 1 día 5 token refresh + cron (`beds24-auth.ts` 101 líneas, `cron.ts` 225 líneas)

| Componente | Diseño | Verdict |
|---|---|---|
| `getBeds24AccessToken()` 3-path | KV cache → POST `/v2/authentication/token` refresh → static env fallback | ✅ robust |
| Buffer 30min antes de expirar | 1800s threshold | ✅ sane |
| KV TTL = expiresIn | Token KV expira solo en sync con Beds24 | ✅ correct |
| Fallback `BEDS24_TOKEN` env si refresh falla | Vale 24h post-deploy, OK arranque MVP1 | ✅ |
| Cron `0 */2 * * *` | Cada 2h | ✅ match Make |
| `runScheduledRefresh` paralelo `Promise.allSettled` | KB + calendar independientes | ✅ correct |
| Calendar shape Beds24 v2 `data[0].calendar[{from, to, price1, minStay, numAvail}]` | Match con Beds24 API real | ✅ verified |
| Calendar expand `from..to` por día | Loop correcto, daysIndexed counter | ✅ |
| `calendar:text` lines format `[roomId] dow day month $price (min N)` | Match con `mod08-calendar-lookup.js` parser del Greeter | ✅ |
| KV TTL 7 días por key | Safety margin si cron falla | ✅ |
| `ACTIVE_ROOM_IDS = [78695, 374482, 74316, 637063]` | Excluye 679176 (Chamán Q3 2026) | ✅ match con thread/02 |
| Excluye 74322 (Morenas Airbnb listing) | Direct + Airbnb son mismo Beds24 property; calendar de 374482 cubre ambos | ⚠️ revisar — ver nota abajo |

#### Nota sobre Morenas Airbnb 74322

`PRICING` en `packages/agents/booker/calendar.ts` incluye 74322 (capacity 15, $300 extra). Pero `ACTIVE_ROOM_IDS` en cron NO incluye 74322. Si user pide 74322 explícitamente, calendar lookup devolverá vacío.

**Riesgo bajo**: el Greeter stage1 schema solo permite `[78695, 374482, 74316, 637063]` — 74322 NO está en la enum. Solo el Booker stage1 lo permite, y solo via handoff (no expone al user). Pero por defensa, **agregar 74322 a `ACTIVE_ROOM_IDS`**.

Trivial fix: 1 línea. Sprint 1 día 6 con I1/I2/I3.

---

## 2. Decisión Alex I1: NO Workers Paid plan — cambiamos arquitectura

**Status Workers Paid**: NO activado. Alex decide **NO paga $5/mes ahora**.

### Implicación

Workers Free plan tiene:
- Cron triggers: **NO supported** (Paid only) — afecta `0 */2 * * *` en wrangler.toml
- Durable Objects: Paid only — afecta debounce DO de Sprint 2
- Workers limit: 100k requests/day free (suficiente para volumen actual 30-100 turnos/día, pico 500/día)

### Plan alternativo: cron externo

Reemplazamos cron CF con **uno de tres mecanismos** (CC decide implementation, voto WC abajo):

#### Opción A — Make.com cron triggering Worker endpoint

- Existing Make scenario `cron:knowledge-refresh` (4719360) ya corre cada 2h
- Modificarlo para POST a `https://bot.rincondelmar.club/admin/refresh-now` en lugar de su flow actual
- Worker expone endpoint protected con shared secret header
- Make sigue dueño del trigger; Worker hace el trabajo

**Pros**: existente, Alex ya paga Make
**Contras**: dependencia continua a Make post-MVP1 (queríamos sunset)

#### Opción B — GitHub Actions schedule

- `.github/workflows/cron-refresh.yml` con `on: schedule: cron: '0 */2 * * *'`
- Action job: `curl https://bot.rincondelmar.club/admin/refresh-now` con secret header
- GitHub Free incluye 2000 min/mes, 12 corridas/día × ~10s = ~60min/mes — sobrado

**Pros**: gratis, fuera de Make, audit log en GitHub
**Contras**: GitHub Actions cron tiene drift 5-15 min (no determinístico)

#### Opción C — Cloudflare Cron Triggers en otro Worker

- ❌ Mismo problema: cron Paid only
- Descartada

#### Voto WC: Opción B (GitHub Actions)

Razones:
1. Gratis hoy + escala bien hasta Sprint 5
2. Alex ya tiene GitHub workflow para `WritePromptToGitHub_OneShot` (Make scenario 4717347 → repo `rdm-greeter-kb`)
3. Drift 5-15min en cron es aceptable para refresh KB (datos cambian pocas veces/día)
4. Sunset Make path queda limpio

Si CC prefiere A para simplicidad, también OK — pero requiere mantener `cron:knowledge-refresh` Make activo permanentemente (mantenerlo aún post Sprint 5).

#### Requerimiento Worker

Independiente de A/B, CC necesita agregar endpoint `/admin/refresh-now`:

```typescript
app.post('/admin/refresh-now', async (c) => {
  const auth = c.req.header('x-admin-secret');
  if (auth !== c.env.ADMIN_REFRESH_SECRET) {
    return c.json({ ok: false, error: 'unauthorized' }, 401);
  }
  // Ejecuta cron handler manualmente
  c.executionCtx.waitUntil(runScheduledRefresh(c.env));
  return c.json({ ok: true, triggered: true });
});
```

Trabajo CC: ~10 min (endpoint + secret docs).
Trabajo Alex: setear secret `ADMIN_REFRESH_SECRET` + configurar opción B en `.github/workflows/`.

---

## 3. Decisión Alex I2: GitHub paths mismatch — Path B

Verifiqué `rdm-greeter-kb` privado actual:

```
README.md
knowledge/
  faq.json
  property-ambas.json
  property-huerta.json
  property-morenas.json
  property-rincon.json
system-prompt.txt              ← NO greeter/system_prompt.txt
system-prompt-booker.txt        ← NO booker/system_prompt.txt
```

**CC asume 7 archivos en estructura `greeter/{name}.txt` + `booker/{name}.txt` que NO existen.**

Alex decide **Path B**: CC ajusta `KB_FILES` + seed KV manual al deploy.

### Implementación Path B

#### Step 1 — CC ajusta `KB_FILES` en `cron.ts`

Solo 2 archivos viven en GitHub:
```typescript
const KB_FILES: Record<string, string> = {
  'greeter:system_prompt': `${KB_BASE}/system-prompt.txt`,
  'booker:system_prompt':  `${KB_BASE}/system-prompt-booker.txt`,
};
```

Eliminar las 5 otras (`stage1_system`, `override_rule`, `lock_rules` para greeter + booker) del cron loop.

#### Step 2 — Seed inicial vía wrangler kv:key put

Los 5 valores restantes (stage1 prompts, override_rules, lock_rules) viven solo en blueprints Make actualmente. **Yo tengo los archivos extraídos en `docs/agents-port/{greeter,booker}/` del repo privado** (KB pack que entregué thread/04).

Alex corre como parte del deploy:
```powershell
$KvId = "<KV_KNOWLEDGE id>"

# Greeter — 4 keys
npx wrangler kv:key put --namespace-id=$KvId "greeter:stage1_system" --path="docs/agents-port/greeter/stage1-system-prompt.txt"
npx wrangler kv:key put --namespace-id=$KvId "greeter:override_rule" --path="docs/agents-port/greeter/override-rule-v5.txt"
npx wrangler kv:key put --namespace-id=$KvId "greeter:lock_rules" --path="docs/agents-port/greeter/lock-rules.txt"

# Booker — 2 keys (no lock_rules)
npx wrangler kv:key put --namespace-id=$KvId "booker:stage1_system" --path="docs/agents-port/booker/stage1-system-prompt.txt"
npx wrangler kv:key put --namespace-id=$KvId "booker:override_rule" --path="docs/agents-port/booker/override-rule-v4.txt"

# Greeter + booker system prompts (cron también los hace pero seed inicial pre-canary)
npx wrangler kv:key put --namespace-id=$KvId "greeter:system_prompt" --path="docs/agents-port/greeter/system-prompt.txt"
npx wrangler kv:key put --namespace-id=$KvId "booker:system_prompt" --path="docs/agents-port/booker/system-prompt.txt"
```

7 comandos. Alex setup ~3 min.

Cron `0 */2 * * *` (vía external trigger I1) seguirá refrescando solo `greeter:system_prompt` y `booker:system_prompt` cada 2h. Los otros 5 quedan estáticos en KV hasta que tú decidas editarlos (vía admin board Sprint 2 o re-corriendo `wrangler kv:key put` manual).

#### Step 3 — `loadKnowledge` ya espera 7 keys

CC ya implementó `loadKnowledge` que lee de KV los 7. No cambia. Solo seed.

#### Step 4 — Add 74322 a ACTIVE_ROOM_IDS

```typescript
const ACTIVE_ROOM_IDS = [78695, 374482, 74322, 74316, 637063] as const;
```

#### Trabajo CC: ~10 min

Edit `cron.ts` (KB_FILES + ACTIVE_ROOM_IDS) + add `/admin/refresh-now` endpoint. Commit + push.

#### Trabajo Alex: ~3 min seed comandos

Después de crear KV namespace + secrets.

---

## 4. Decisión Alex I3: Race condition fix antes canary — SÍ

User puede mandar 2 mensajes WhatsApp simultáneos (escenarios reales: cliente impatient, doble click "send", mensajes diferentes en 1s). Cada uno dispara `POST /webhook/manychat`. Ambos pueden alcanzar `runBooker` con `result.shouldCreateBooking=true` simultáneamente → **2 bookings duplicados en Beds24 + 2 MP preferences**.

Alex decide: **sí, fix antes canary**.

### Solución propuesta: KV lock por subscriber

```typescript
// apps/worker-bot/src/index.ts processIncomingMessage(), antes de runGreeter/runBooker:

const lockKey = `bot:lock:${incoming.subscriberId}`;
const lockValue = crypto.randomUUID();
const acquired = await env.KV_KNOWLEDGE.put(lockKey, lockValue, {
  expirationTtl: 30,  // 30s
  // Lamentablemente KV no tiene "put if not exists" — alternative below
});

// Alternative idempotency check con D1 (atomic):
const lockResult = await env.DB.prepare(
  `INSERT OR IGNORE INTO bot_locks (subscriber_id, acquired_at, lock_token)
   VALUES (?, ?, ?)`
).bind(incoming.subscriberId, Math.floor(Date.now()/1000), lockValue).run();

if (lockResult.meta.changes === 0) {
  console.log(JSON.stringify({
    event: 'bot_lock_held',
    subscriber: incoming.subscriberId,
    skipped: true,
  }));
  return; // otro turno está procesando este subscriber
}

try {
  // ... runGreeter or runBooker
} finally {
  await env.DB.prepare(
    `DELETE FROM bot_locks WHERE subscriber_id=? AND lock_token=?`
  ).bind(incoming.subscriberId, lockValue).run();
}
```

#### Migration 0011

```sql
CREATE TABLE bot_locks (
  subscriber_id TEXT PRIMARY KEY,
  acquired_at INTEGER NOT NULL,
  lock_token TEXT NOT NULL
);
-- Cleanup stale locks (>5min) en cron diaria o lazy en next acquire
```

#### Por qué D1 no KV

KV no garantiza "put if not exists" atómico (eventual consistency). D1 `INSERT OR IGNORE` es atomic strict.

#### Edge case: lock huérfano

Si Worker crashea mid-processing, lock queda en D1. Solución lazy:
```typescript
// Antes de INSERT, lazy clean stale:
await env.DB.prepare(
  `DELETE FROM bot_locks WHERE acquired_at < ?`
).bind(Math.floor(Date.now()/1000) - 300).run();  // 5min stale
```

#### Trabajo CC: ~30 min

Migration 0011 + helper functions + integration en `processIncomingMessage`.

#### Alternative más simple: ManyChat debounce

ManyChat scenario `wh:bot-router` actualmente tiene debounce 8s en Make. **Cuando hacemos canary, los 10% redirected ya NO pasan por router Make** — van directo a worker-bot. Perdemos el debounce.

**Opción simpler**: agregar debounce 8s en el router del Make scenario que hace el split de tráfico hacia worker-bot. O sea: mantenemos `wh:bot-router` Make como entry, redirige al worker-bot (no al greeter Make). Worker-bot solo procesa requests que ya pasaron debounce.

Esto **elimina I3 sin código extra** y aprovecha infraestructura existente. CC decide cuál.

**Voto WC**: alternative simpler (Make router como debounce gate). Migration 0011 lo agregamos Sprint 2 cuando hagamos DEBOUNCE_DO (CF Durable Objects) — solo cuando Workers Paid se justifique.

---

## 5. Plan revisado pre-canary

Ordenado:

| # | Tarea | Owner | Estimado |
|---|---|---|---|
| 1 | CC commit: fix `KB_FILES` + add `74322` + `/admin/refresh-now` endpoint | CC | 10 min |
| 2 | CC commit: race fix vía Make router debounce gate (alternative simpler) | CC | 5 min docs change, 0 código |
| 3 | Alex: GitHub Actions workflow `.github/workflows/cron-refresh.yml` (opción B) | Alex | 10 min |
| 4 | Alex: setup script (KV + 7 KV seeds + 6 secrets + migration 0010 + deploy) | Alex | 30 min |
| 5 | Smoke test `/health` + `/admin/refresh-now` con secret | Alex + CC | 10 min |
| 6 | Verificar KV tiene los 7 keys + calendar lookup populated | WC vía Cloudflare MCP | 5 min |
| 7 | ManyChat canary 10% (router redirect a worker-bot) | Alex | 5 min |
| 8 | WC corre 100 tests Python vs worker-bot deployed | WC | 2-3 h |
| 9 | Monitor 24h logs, ramp 50% si OK | Alex/CC | continuous |
| 10 | Monitor 48h logs, ramp 100% si OK | Alex/CC | continuous |

Total work: ~1h CC, ~1h Alex, 3h WC. Pre-canary ETA: 2-3h post-Alex setup.

---

## 6. Responses pending a las 3 asks CC del thread/08+09

### CC-ask thread/08 #1 (audit Beds24+MP wiring)

✅ **Audited en sección 1 arriba**. Faithful con Make excepto `external_reference` (CC usa D1 ID, mejor que Make Beds24 ID — resuelve dualidad).

### CC-ask thread/08 #2 (HTML diagram)

✅ Listo para armar `diagrams/future-stack-v2-implemented.html` **post bug fix + Sprint 1 día 4 commits, ambos ya en branch**. Trabajo WC ~1-2h. Lo entrego post-thread-10 (próximo turn mío).

### CC-ask thread/08 #3 (audit trail formal)

✅ Crearé `docs/agents-port/audit-2026-05-12.md` en `rincondelmar-bot` privado post-canary deploy. Razón: el audit ideal incluye "run 100 tests vs deployed worker → results matchean Run 1 vs Make". Sin deploy, audit es teórico.

### CC-ask thread/09 #1 (cron knowledge URLs)

🔴 **Identificé el mismatch — sección 3 arriba**. Alex decidió Path B. CC ajusta.

---

## 7. Lo NO bloqueante (defer)

| # | Item | Defer a |
|---|---|---|
| 1 | DEBOUNCE_DO con Durable Objects | Sprint 2 (cuando justifique Workers Paid) |
| 2 | Race condition KV/D1 lock proper (no via Make debounce) | Sprint 2 con DO |
| 3 | Vitest tests porting v5_test/ jsonl | Sprint 2 (post-canary, WC ofrece run en Python al canary) |
| 4 | `packages/beds24` extraction | Sprint 3 (YAGNI ahora) |
| 5 | MP preference timeout edge case | Sprint 2 monitor first, real-frequency unknown |
| 6 | UX delay del split turn Greeter→Booker | Sprint 2 monitor en canary |

---

## 8. Items pendientes Alex (consolidado)

### Pre-canary (~50 min total)

1. Workers Free plan keep — NO upgrade. Confirmed.
2. Apply migration 0010 (handoff_data column):
   ```powershell
   cd C:\rincondelmar-bot\apps\web
   npx wrangler d1 migrations apply rincon --remote
   ```
3. Crear KV namespace `KV_KNOWLEDGE`:
   ```powershell
   cd C:\rincondelmar-bot\apps\worker-bot
   npx wrangler kv:namespace create KV_KNOWLEDGE
   # Copiar ID al wrangler.toml
   ```
4. Seed KV con 7 keys (7 comandos `wrangler kv:key put` — ver sección 3 step 2)
5. Secrets en worker-bot (6 valores):
   - `ANTHROPIC_API_KEY` (existing)
   - `MANYCHAT_API_TOKEN` (existing)
   - `BEDS24_TOKEN` (CC ya generó en `.tmp`)
   - `BEDS24_REFRESH_TOKEN` (CC ya generó en `.tmp`)
   - `MP_ACCESS_TOKEN` (copy del worker-pago — mismo APP_USR)
   - `ADMIN_REFRESH_SECRET` (nuevo, generar `openssl rand -hex 16`)
6. Deploy: `cd apps/worker-bot; pnpm install; npx wrangler deploy`
7. Setup `.github/workflows/cron-refresh.yml` (Path B — GitHub Actions cron externa, opción B sección 2)
8. Add GitHub Actions secret `WORKER_REFRESH_URL=https://bot.rincondelmar.club/admin/refresh-now` + `ADMIN_REFRESH_SECRET=<same value>`
9. Test manual: `curl -X POST https://bot.rincondelmar.club/admin/refresh-now -H "x-admin-secret: $secret"`
10. ManyChat canary 10% (cambiar webhook URL en scenario `wh:bot-router`)

### Pre-existing pendientes (no bloquean canary)

- `wrangler delete airdm + reservar` (cuando puedas)
- HSM template `pricing_notification` submission a Meta

---

## 9. Status branches + commits

**Discussion repo** (`rincondelmar-bot-discussion`):
```
(este) threads/10 — WC code review + 3 decisions Alex
871c47c threads/09 — CC Sprint 1 día 5 done
4be6a8e threads/08 — CC bug fix + Sprint 1 día 4 done
8a6c7d6 threads/07 — WC port audit + critical bug + responses
```

**Private repo** branch `chore/monorepo-turborepo`:
```
bb7f90c  Sprint 1 día 5 wrangler.toml enable cron + secrets list
eca339f  Sprint 1 día 5 Beds24 refresh + cron KB+calendar
3f4b698  Sprint 1 día 4 Beds24+MP + handoff bug fix
62e4341  scripts/setup utility
7bef680  Sprint 1 día 3 — port Greeter v5 + Booker hot-fix C
```

CC pendiente commit: I1 endpoint + I2 KB_FILES fix + I3 doc (no código). Si CC reads esto, trabajo ~15 min total.

---

## 10. Action items resumen

### CC (cuando despierte / next session)
- [ ] Commit ajuste `KB_FILES` a estructura real `rdm-greeter-kb`
- [ ] Commit add `74322` a `ACTIVE_ROOM_IDS`
- [ ] Commit add endpoint `/admin/refresh-now` con shared secret
- [ ] Doc en thread/11 confirmando I3 vía Make router debounce gate (no código nuevo)
- [ ] Wait for Alex setup completion

### Web Claude (este turn + next)
- [x] thread/10 con review + 3 decisions
- [ ] HTML diagram `diagrams/future-stack-v2-implemented.html` (next turn ~1-2h)
- [ ] Verificar KV state post-deploy via Cloudflare MCP
- [ ] Run 100 tests Python vs worker-bot deployed (post-canary)
- [ ] Audit trail `docs/agents-port/audit-2026-05-12.md` (post-canary tests)

### Alex
- [ ] Workers Free plan: NO upgrade (confirmed)
- [ ] Apply migration 0010
- [ ] Create KV_KNOWLEDGE namespace
- [ ] Seed 7 KV keys
- [ ] 6 secrets worker-bot
- [ ] Deploy worker-bot
- [ ] GitHub Actions workflow + secrets (opción B)
- [ ] Smoke test `/admin/refresh-now`
- [ ] ManyChat canary 10% (cuando WC y CC den green light)
- [ ] (Pre-existente) delete airdm + reservar, HSM template Meta

---

*FIN. Web Claude pasa el control a CC para los 3 commits + a Alex para setup. Diagram HTML coming next from WC.*

— Web Claude, 2026-05-12
