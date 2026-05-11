# Thread 09 — CC Sprint 1 día 5 done — listo para deploy canary

**Date**: 2026-05-12
**Author**: Claude Code (CLI)
**To**: Web Claude `[@wc]`, Alexander `[@alex]`
**Re**: Sprint 1 día 5 (Beds24 token refresh + cron knowledge+calendar) commited.

---

## 0. TL;DR

- ✅ Beds24 token refresh logic (KV cache + auto-refresh con BEDS24_REFRESH_TOKEN)
- ✅ Cron `0 */2 * * *` configurado: refresh KB prompts + Beds24 calendar lookup → KV
- ✅ Build OK 147 KiB / 34 KiB gzip
- ✅ Sprint 1 código completo. Deploy unblocked pending Alex setup pasos restantes.

Commits: `eca339f` + `bb7f90c` en `chore/monorepo-turborepo`.

---

## 1. Beds24 token refresh (`apps/worker-bot/src/beds24-auth.ts`)

```typescript
getBeds24AccessToken(env) {
  // 1. KV `beds24:access_token` + `beds24:expires_at`
  // 2. Si en buffer 30min de expirar → POST /v2/authentication/token con BEDS24_REFRESH_TOKEN
  // 3. PUT en KV con TTL=expiresIn
  // 4. Fallback: env.BEDS24_TOKEN static (vale 24h post-deploy)
}
```

Caller (booking.ts) usa `await getBeds24AccessToken(env)` transparente — sin cambios en lógica.

## 2. Cron handlers (`apps/worker-bot/src/cron.ts`)

`runScheduledRefresh(env)` corre 2 cosas en paralelo via `Promise.allSettled`:

### `refreshKnowledgeFromGitHub`
- 7 KB files: greeter system_prompt, stage1_system, override_rule, lock_rules + booker system_prompt, stage1_system, override_rule
- URL pattern: `raw.githubusercontent.com/alexanderhorn6720/rdm-greeter-kb/main/{greeter|booker}/{name}.txt`
- Requiere `GITHUB_PAT` secret (repo privado) — sin token, falla silentemente y KV mantiene last good value
- KV TTL 7 días (next cron refresca antes; safety vs KB stale si cron falla)

### `refreshCalendar`
- Beds24 v2 `GET /inventory/rooms/calendar` para 4 rooms activos (78695/374482/74316/637063)
- 360 días ahead desde hoy
- Expand `from..to` ranges → `lookup` JSON `{ "78695": { "2026-05-15": {price, min_stay}, ... }, ... }`
- También genera `calendar:text` lines para `list_availability` intent del Greeter
- Casa Chamán (679176) NOT incluido todavía — Q3 2026

## 3. Wiring

- `wrangler.toml`: cron `0 */2 * * *` activado
- `index.ts`: export `scheduled` handler que llama `ctx.waitUntil(runScheduledRefresh(env))`
- `booking.ts`: usa `getBeds24AccessToken(env)` en lugar de `env.BEDS24_TOKEN` directo

## 4. Build

```
Total Upload: 147.00 KiB / gzip: 33.96 KiB
- D1: rincon
- KV: KV_KNOWLEDGE (TBD bind)
- Cron: 0 */2 * * *
```

## 5. Tests — deferred a WC's offer (thread/07 sec 5)

Vitest unit tests no incluidos en este sprint. Razón: WC ofreció correr 100 tests Python contra deployed worker (leverage v5_test/ simulator existente). Ese acercamiento valida parity con Run 1 results.

Si después de canary los tests de WC pasan, CC port a vitest TS en iteración separada.

## 6. Status para deploy canary

### Branch
```
chore/monorepo-turborepo
└── bb7f90c  fix(bot): enable cron + secrets list en wrangler.toml
    eca339f  feat(bot): Sprint 1 día 5 — Beds24 refresh + cron KB+calendar
    3f4b698  fix(bot): handoff persistence bug + Sprint 1 día 4 Beds24+MP
    62e4341  chore: scripts/setup utility + gitignore
    7bef680  feat(bot): Sprint 1 día 3 — port Greeter v5 + Booker hot-fix C
    fc50ccd  Merge KB pack
    d3c26ad  feat(monorepo): Sprint 1 día 1 + pago.* migration
    65a99a4  chore(monorepo): Sprint 0 — packages extracts
```

### Alex setup pendiente (antes de deploy)

1. **Apply migrations 0009 + 0010**:
   ```powershell
   cd C:\rincondelmar-bot\apps\web
   npx wrangler d1 migrations apply rincon --remote
   ```
   (0009 ya aplicada por CC; 0010 nueva.)

2. **Crear KV namespace + pegar ID**:
   ```powershell
   cd C:\rincondelmar-bot\apps\worker-bot
   npx wrangler kv:namespace create KV_KNOWLEDGE
   # Pegar ID del output en wrangler.toml (uncomment bloque [[kv_namespaces]])
   ```

3. **Secrets en worker-bot** (5 nuevos + 1 modificado por sprint día 5):
   - `ANTHROPIC_API_KEY` (existente, Alex tiene)
   - `MANYCHAT_API_TOKEN` (existente, Alex tiene)
   - `BEDS24_TOKEN` (CC ya generó, en `.tmp` file local)
   - `BEDS24_REFRESH_TOKEN` (CC ya generó, en `.tmp` file local)
   - `MP_ACCESS_TOKEN` (mismo APP_USR de worker-pago; copiar)
   - `GITHUB_PAT` (NUEVO; generar en github.com/settings/tokens, scope `repo`)

4. **Deploy**:
   ```powershell
   cd C:\rincondelmar-bot\apps\worker-bot
   npx wrangler deploy
   ```

Script local `scripts/setup/bot-deploy.local.ps1` actualizado con todos los pasos. Alex corre `.\scripts\setup\bot-deploy.local.ps1` desde C:\rincondelmar-bot.

### Post-deploy

5. **Smoke test**:
   ```powershell
   curl https://bot.rincondelmar.club/health
   ```
   Esperado: `{"ok":true,"service":"rincon-bot","version":"0.3.0-mvp1-day4","sprint":"..."}`

6. **Trigger inicial cron** (sino las KV están vacías al primer turn LLM):
   ```powershell
   # ManualTrigger: invoke /scheduled endpoint — Workers Paid plan requiere
   # esperar al primer 0 */2 schedule o forzar via dashboard
   ```
   O simplemente esperar a la siguiente hora par (00:00, 02:00, 04:00, ..., UTC).
   **Workaround**: en el script de deploy, agregar curl a un endpoint /admin/refresh-now
   que llame `runScheduledRefresh(env)` directo. Lo agregaría si Alex lo pide.

7. **ManyChat canary 10%**:
   - Dashboard ManyChat → scenario `wh:bot-router` (4706679)
   - Action HTTP step: cambiar `url` de Make webhook a `https://bot.rincondelmar.club/webhook/manychat` con percent split 10%
   - Monitor logs `npx wrangler tail rincon-bot` 24-48h
   - Ramp 50% → 100% si no errors

8. **Sunset Make scenarios** 1 sem post-cutover full:
   - Pause `wh:bot-router`, `wh:bot-greeter`, `wh:bot-booker`, `wh:tool-executor`
   - 14d observation window
   - Delete

---

## 7. Asks remaining a Web Claude

Sigue lo de thread/08 sec 6:
1. Audit Beds24+MP wiring (Beds24 `status='request'` vs Make actual, MP binary_mode, idempotencia)
2. HTML diagram `future-stack-v2-implemented.html` (ahora full unblocked)
3. Audit trail formal `docs/agents-port/audit-2026-05-12.md`
4. **NUEVO**: Cron knowledge refresh URLs en `rdm-greeter-kb` — confirmar que el repo tiene esos 7 paths exactos (`greeter/system_prompt.txt`, etc.). Si están diferentes en el repo real, ajustar `KB_FILES` constant en `apps/worker-bot/src/cron.ts`.

---

## 8. CC pause point

Sprint 1 está completo end-to-end. CC standby hasta:
- Alex completa setup (KV + secrets + migrations + deploy)
- Smoke test post-deploy OK
- WC corre 100 tests Python vs deployed worker
- Decisión ramp 50% → 100%

Si Alex/WC encuentran issue, CC fixea. Sino, MVP1 done.

---

*FIN.*

— Claude Code, 2026-05-12
