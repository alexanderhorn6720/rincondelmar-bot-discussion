---
thread: 235
author: wc
topic: doit-crons-nativos-cf
status: spec-ready
mode: DoIt
workstream: CC-Bot
supersedes_ops_dependency: .github/workflows/cron-*.yml
created: 2026-05-30
---

# DoIt — Migración de crons GH Actions → CF nativo (worker-bot)

MODE: DoIt
TERRITORIO: CC-Bot (apps/worker-bot únicamente)

---

## §1. Contexto

### Problema
Los ~22 crons operacionales del bot viven en `.github/workflows/cron-*.yml`. Cada uno
pega a un endpoint `/admin/*` del worker con header `x-admin-secret` =
`ADMIN_REFRESH_SECRET`. El 2026-05-29 se descubrió que **todos** llevaban tiempo
fallando con 401: el secret en GitHub Actions driftó respecto al del worker.
Causa raíz: dos fuentes de verdad para el mismo secret, y `sync-secret.sh` solo
propaga a workers, nunca a GitHub. Toda la capa scheduled estuvo caída en silencio;
solo el path inline del webhook (`/webhook/beds24-booking` → `waitUntil`) mantuvo
el real-time vivo.

### Decisión estratégica (Alex, 2026-05-30)
Mover TODA la operación diaria a crons nativos de Cloudflare. GitHub queda solo para
PRs, threads, deploys. El cron nativo corre dentro del worker vía `scheduled()`:
sin caller externo, sin header, **sin 401 posible**. Elimina la clase de bug.

### Habilitadores verificados (2026-05-30)
- CF Workers Paid: **250 cron triggers/cuenta** (el "3 por worker" era límite de 2020,
  obsoleto). worker-pago usa 5, eval usa 1 → ~244 libres.
- CPU por cron trigger: 30s (<1h interval). Los scans son I/O-bound (no cuenta CPU). OK.
- La lógica ya está factorizada en funciones; los endpoints `/admin/*` son wrappers
  finos. El `scheduled()` llama las MISMAS funciones. Migración = mover el trigger,
  no la lógica.

---

## §2. Scope explícito

### YES
- Reescribir `scheduled()` en `apps/worker-bot/src/index.ts` como dispatch table
  por `event.cron`, llamando funciones existentes vía `ctx.waitUntil`.
- Añadir `[triggers] crons = [...]` en `apps/worker-bot/wrangler.toml` con los
  3 schedules nuevos (eval `0 10 * * *` ya existe, se mantiene).
- Reusar el contador `inquiry_cron_tick` en `bot_config` para gate de refresh
  (cada 8º pulse ≈ 2h) y bot-alerts (cada 4º pulse ≈ 1h).
- **Deshabilitar** los `cron-*.yml`: quitar el bloque `schedule:`, conservar
  `workflow_dispatch:` (trigger manual de respaldo). NO borrar los archivos.
- Tests del dispatcher (unit, mock de `event.cron`).
- Self-review del diff antes de commit.

### NO
- NO borrar los `cron-*.yml` (eso es PR aparte tras 1 semana en verde).
- NO tocar los endpoints `/admin/*` — se quedan para trigger manual + backfill.
- NO tocar otros workers (worker-pago, worker-tours, worker-feedback).
- NO tocar apps/web ni Pages.
- NO migrar secrets (Workstream B, spec aparte).
- NO `ALTER TABLE`. El contador `inquiry_cron_tick` ya existe; si hiciera falta
  otra key en `bot_config`, es INSERT/UPSERT de fila, no ALTER.
- NO cambiar la lógica de ninguna función de negocio. Solo el punto de invocación.

---

## §3. Decisiones cerradas (no re-litigar)

| # | Decisión | Valor |
|---|---|---|
| D1 | Schedules nuevos | 3 (+ eval sin tocar) |
| D2 | Pulse frequency | **15 min** (`*/15 * * * *`) — conserva alert keyword crítico |
| D3 | Refresh | **tick-gated** dentro del pulse, cada 8º tick (~2h). Respeta TTL 2h del KV de prompts |
| D4 | bot-alerts | tick-gated dentro del pulse, cada 4º tick (~1h) |
| D5 | GH workflows | deshabilitar (quitar `schedule:`, mantener `workflow_dispatch:`). Borrado = PR posterior |
| D6 | Endpoints /admin/* | se mantienen intactos |

### Set definitivo de schedules

| Cron expr | Frecuencia | Tareas (en orden, try/catch individual) |
|---|---|---|
| `*/15 * * * *` | pulse | 1. runBeds24Normalize (batchLimit 100)<br>2. processReadyInquiries (cronTick) — incl. backup sweep cada 3º interno<br>3. pollClientBotMessages<br>4. runWelcomeAutoSend<br>5. checkAndSendReminders (handoff)<br>6. **gate ÷8**: runScheduledRefresh<br>7. **gate ÷4**: runBotAlerts |
| `0 15 * * *` | daily 09:00 Acapulco | runInquiriesAutoClose · runConversationsAutoClose · syncReviews · scanForCaptures · cost-staleness (extraer lógica del endpoint) · syncDirectSubscribers · scanForWelcome/T14/T7/T1/Arrived/PreCheckout/PostStay · buildDailyDigest |
| `0 8 1 * *` | monthly | cleanupShortLinks |
| `0 10 * * *` | daily 04:00 Acapulco | eval (SIN CAMBIOS — ya nativo) |

Nota tick: `inquiry_cron_tick` ya se incrementa hoy en el endpoint normalize (wrap a 1000).
En nativo, el `scheduled()` del pulse lee+incrementa el mismo contador y lo pasa a
`processReadyInquiries`. Gates: `tick % 8 === 0` → refresh; `tick % 4 === 0` → bot-alerts.

---

## §4. Implementación

### 4.1 `apps/worker-bot/wrangler.toml`
Cambiar el bloque `[triggers]`:
```toml
[triggers]
crons = [
  "*/15 * * * *",  # pulse: normalize + inquiries + poll + welcome-queue + handoff + (÷8 refresh, ÷4 alerts)
  "0 15 * * *",    # daily 09:00 MX: housekeeping + pre-stay + digest
  "0 8 1 * *",     # monthly: cleanup short links
  "0 10 * * *",    # eval (existente)
]
```

### 4.2 `apps/worker-bot/src/index.ts` — `scheduled()`
Reescribir el handler como dispatch por `event.cron`. Estructura:
- Helper `tickAndGet(env): Promise<number>` — lee+UPSERT `inquiry_cron_tick` en
  `bot_config` (mover la lógica que hoy vive inline en `/admin/normalize-beds24-events`
  a una función reusable; el endpoint también la llama, sin duplicar).
- Cada tarea envuelta en try/catch propio + `console.log` con `event: 'cron_task'`,
  `task`, `cron`, `ok`/`error`. Una tarea que falla NO aborta las demás.
- Mantener el branch eval `0 10 * * *` tal cual (gated por `eval_framework_enabled`).
- Todo el trabajo bajo `ctx.waitUntil`.

Contrato del dispatcher (pseudocódigo):
```
scheduled(event, env, ctx):
  switch event.cron:
    case '0 10 * * *':   # eval — sin cambios
    case '*/15 * * * *': # pulse
      tick = await tickAndGet(env)
      run(normalize); run(processReadyInquiries, tick); run(poll);
      run(welcomeAutoSend); run(handoffReminders);
      if tick % 8 == 0: run(refresh)
      if tick % 4 == 0: run(botAlerts)
    case '0 15 * * *':   # daily
      run(inquiriesAutoClose); run(conversationsAutoClose); run(reviews);
      run(extraGuestsScan); run(costStaleness); run(manychatSync);
      run(preStay welcome..postStay ×7); run(dailyDigest)
    case '0 8 1 * *':    # monthly
      run(cleanupShortLinks)
```

### 4.3 cost-staleness
La lógica vive inline en el handler `/admin/cost-staleness` (isCostDataStale + TG).
Extraer a función `runCostStalenessCheck(env, hours=36)` reusable por endpoint y
dispatcher. NO cambiar comportamiento.

### 4.4 GH workflows (deshabilitar)
En cada `cron-*.yml` que hoy tiene `schedule:`, comentar/eliminar SOLO el bloque
`schedule:` y dejar `workflow_dispatch:`. Lista a tocar (verificar en filesystem):
beds24-normalize, refresh, reviews-sync, welcome-auto-send, daily-digest,
handoff-reminders, client-bot-poll, conversations-auto-close, inquiries-auto-close,
extra-guests-scan, manychat-subscriber-sync, pre-stay-{welcome,t1,t7,t14,arrived,
pre-checkout,post-stay}, cleanup-short-links, cost-staleness, bot-alerts.
NO tocar: ci.yml, deploy.yml, post-deploy-smoke.yml, scripts-tests.yml,
self-review-checklist.yml, fetch-reviews.yml (verificar si es operacional o no).

---

## §5. Tests

- Unit del dispatcher: mockear `event.cron` para cada una de las 4 expresiones,
  verificar que se invocan las tareas esperadas (spies sobre las funciones).
- Test del gate: tick % 8 y tick % 4 disparan refresh/alerts en el tick correcto
  y NO en los demás.
- Test que una tarea que throwea NO impide las siguientes (try/catch aislado).
- `pnpm --filter worker-bot test` verde.
- `pnpm --filter worker-bot exec tsc --noEmit` (o el typecheck del repo) limpio.

---

## §6. Definition of Done (checkeable)

- [ ] `wrangler.toml` tiene las 4 cron expressions.
- [ ] `scheduled()` despacha por `event.cron` con las tareas del §3.
- [ ] `tickAndGet` extraído y usado por endpoint + dispatcher (sin duplicar lógica).
- [ ] `runCostStalenessCheck` extraído.
- [ ] Tests del dispatcher verdes + typecheck limpio.
- [ ] Todos los `cron-*.yml` operacionales con `schedule:` removido, `workflow_dispatch:` intacto.
- [ ] Self-review del diff hecho.
- [ ] PR creado (branch `feat/crons-nativos-cf`), descripción mobile-first:
      qué cambió + qué verificar + que requiere `wrangler deploy` manual post-merge.

### Post-merge (Alex, fuera del DoIt — va en la PR description)
- [ ] `cd apps/worker-bot && npx wrangler deploy` (worker-bot NO tiene auto-deploy).
- [ ] Verificar en CF dashboard que los 4 cron triggers aparecen.
- [ ] Smoke: esperar 1 pulse (15 min), confirmar SMOKE row → `approval_pending`
      + heartbeats frescos en `/admin/health`.
- [ ] Confirmar daily (`0 15 * * *`) corre al día siguiente.
- [ ] Tras 1 semana en verde → PR para borrar los `cron-*.yml`.

---

## §7. Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Doble ejecución durante transición (GH cron aún activo + nativo) | Deshabilitar `schedule:` en GH en el MISMO PR. Las tareas son idempotentes igual (normalize ON CONFLICT, welcome IS NULL claim) |
| Una tarea pesada agota CPU del cron (30s) | Cada tarea bajo try/catch + waitUntil; batchLimits ya acotados. Si el pulse se acerca al límite, mover la tarea más pesada a su propio schedule (no esperado a volumen real 5-30/día) |
| Slots de cuenta | ~6 actuales + 3 nuevos = ~9, muy bajo 250. Sin riesgo |
| Refresh fuera de ventana TTL 2h del KV | Gate ÷8 del pulse 15min = 2h exacto. Si se cambia el pulse, recalcular el gate |
| Efecto rebaño al revivir crons muertos | Casi todo approval-mode/OFF (welcome encola, pre-stay gated por MESSENGER_OUTBOUND_ENABLED off, inquiry canary 0%). Solo auto-close ×2 muta estado: cerrará un lote acumulado, aceptable |
| `event.cron` no matchea por formato (espacios) | CF normaliza; el test del dispatcher cubre el string exacto de wrangler.toml |

### Costo
LLM: ~$0 (tarea de infra, sin inferencia salvo lo que las tareas ya hacían).
No requiere declaración de budget (<$10).

---

## §8. Notas de coordinación

- Band-aid opcional pre-DoIt: resincronizar `ADMIN_REFRESH_SECRET` (5 min) restaura
  ops vía GH durante la ventana de migración. Irrelevante si el deploy nativo
  completa hoy. Decisión de Alex.
- Workstream B (hub central de secrets vía CF Secrets Store): spec aparte. Esta
  migración REDUCE la urgencia de B al eliminar el consumidor más frágil del secret.
- Followup: tras verificar nativo 1 semana, borrar `cron-*.yml` + actualizar el
  comentario en wrangler.toml que aún razona en el mundo "5-cron cap / GH Actions".
