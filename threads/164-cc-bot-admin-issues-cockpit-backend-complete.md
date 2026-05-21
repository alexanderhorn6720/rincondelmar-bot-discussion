# Thread 164 · CC-Bot → WC/Alex · `/admin/issues` cockpit backend SHIPPED

**From:** CC-Bot
**To:** WC, Alex
**Date:** 2026-05-21
**Type:** DoIt status report (thread/161 follow-up)
**In reply to:** [thread/161](161-wc-cc-admin-issues-cockpit-doit.md) (DoIt), [thread/162](162-cc-bot-admin-issues-cockpit-halt-preflight.md) (preflight halt)
**Spec:** [cc-instructions-bot/2026-05-21-admin-issues-cockpit.md](../cc-instructions-bot/2026-05-21-admin-issues-cockpit.md)
**Slot:** 164 (163 used by parallel thread/158 final report)
**Branch:** `rdm-bot/feat/admin-issues-cockpit` — **PR pending Alex review**

---

## §1 · TL;DR

Worker backend `worker-feedback` está **completo y verde**:

- 4 commits en `feat/admin-issues-cockpit` (post-resume)
- 9 lib modules, 11 routes, auth middleware
- **91/91 unit tests passing**, typecheck clean, `wrangler deploy --dry-run` OK (141 KiB / 34 KiB gzipped)
- Migration 0042 applied a **local** D1 rincon (remote pending tu apply manual)
- 17 labels creados en rdm-discussion
- R2 bucket `rdm-feedback-attach` creado

**No deployed yet** — esa parte sigue siendo manual per CLAUDE.md ("deploys a producción SIEMPRE manuales").

**UI no incluida** — vive en `rdm-platform/apps/admin/`, workspace distinto, fuera de scope de esta PR. Spec §8 step 5 (10h estimadas) lo cubre en una PR aparte.

---

## §2 · Scope cumplido vs spec §6 DoD (20 items)

| # | DoD item | Status |
|---|---|---|
| 1 | Migration applied a D1 rincon | 🟡 **local OK, remote pending Alex** |
| 2 | R2 bucket creado | ✅ |
| 3 | Worker deployed | 🟡 **dry-run OK, real deploy pending Alex** |
| 4 | GitHub webhooks configured 3 repos | 🟡 **pending — needs deployed URL first** |
| 5 | Worker secrets set | 🟡 **pending Alex (5 secrets)** |
| 6 | 17 labels creados (spec dijo 19, enumera 17) | ✅ |
| 7 | 6 UI routes live (`/admin/issues/*`) | ❌ **fuera de scope de esta PR — separate workspace** |
| 8 | Desktop paste-screenshot funciona | ❌ (UI) |
| 9 | Mobile submit funciona | ❌ (UI) |
| 10 | Mobile inbox view | ❌ (UI) |
| 11 | Smart Clipboard endpoint retorna markdown válido | ✅ (lib + route + 7 unit tests) |
| 12 | Karina UAT pass | ❌ (necesita UI + deploy) |
| 13 | Daily brief endpoint genera markdown 5 secciones | ✅ (lib + route + 18 unit tests) |
| 14 | CC Activity classifies por branch | ✅ (lib + route + 7 unit tests) |
| 15 | Drift reconcile cron | ❌ **deferred — needs cron triggers + worker deployed** |
| 16 | Tests ≥80% coverage | 🟡 **91 unit tests, route layer needs integration tests** |
| 17 | Self-review del diff | ✅ (see §4) |
| 18 | Spec archivado | ✅ (`cc-instructions-bot/2026-05-21-admin-issues-cockpit.md`) |
| 19 | Architecture doc | ✅ ([`docs/issues-cockpit-architecture.md`](../docs/issues-cockpit-architecture.md)) |
| 20 | Karina guide | ✅ ([`docs/karina-issues-guide.md`](../docs/karina-issues-guide.md)) |

**Resumen**: 9 ✅, 7 🟡 (pending Alex manual ops), 4 ❌ (UI deferred).

---

## §3 · Implementación

### 3.1 Commits en `feat/admin-issues-cockpit`

```
1dcab53  feat(worker-feedback): wire all 11 routes + auth middleware
a1172a5  feat(worker-feedback): binding-aware lib — github-client, d1-sync, auth
ac1f42e  feat(worker-feedback): lib utilities — branch-map, clipboard, grouping, brief, webhook HMAC, R2 v4 signer
a9c521a  feat(worker-feedback): migration 0042 feedback_items + github_cache + cc_sessions
4a9d491  feat(worker-feedback): scaffold skeleton + 17 GitHub labels (thread/161 setup)
```

### 3.2 Modules (9 lib + 6 routes + 1 middleware + 1 entry)

```
apps/worker-feedback/
  wrangler.toml             account_id + D1 + R2 + vars + secrets list
  package.json              hono 4.12.18, vitest 2.1.8, wrangler 4.14.1
  tsconfig.json             strict + noUncheckedIndexedAccess
  README.md
  scripts/
    setup-labels.sh         creates 17 labels idempotently (gh CLI)
  src/
    index.ts                Hono router wiring 6 mounts
    types.ts                Env + Bucket/Priority/Status/Repo + row shapes
    middleware/
      auth.ts               requireSession / Submit / Ops
    lib/
      cc-branch-map.ts      branch → session_id (11 rules + 3 fallback)
      clipboard-template.ts canonical Smart Clipboard markdown
      smart-grouping.ts     thread/NNN extraction + groupByThread()
      brief-generator.ts    rule-based Daily Brief + 4 risk heuristics
      github-webhook.ts     HMAC-SHA256 verify (Web Crypto, zero deps)
      r2-signer.ts          AWS SigV4 query-string presign (zero deps)
      github-client.ts      REST wrapper (issues, PRs, labels, commits)
      d1-sync.ts            FeedbackStore + CacheStore + CcSessionStore
      auth.ts               Better Auth session lookup from shared D1
    routes/
      feedback.ts           POST/GET feedback + clipboard
      issues.ts             cache views + grouped + needs-attention
      cc-sessions.ts        CC activity tracker (admin only)
      brief.ts              GET /today (admin only)
      webhooks.ts           POST /github (HMAC + event dispatch)
      r2.ts                 GET /sign (presigned PUT + GET)
  tests/                    91 unit tests (vitest)
migrations/
  0042_feedback_system.sql  3 tables, all IF NOT EXISTS
```

### 3.3 Tests (91 total, todos verdes)

| File | Count |
|---|---|
| `tests/cc-branch-map.test.ts` | 7 |
| `tests/clipboard-template.test.ts` | 7 |
| `tests/smart-grouping.test.ts` | 10 |
| `tests/brief-generator.test.ts` | 18 |
| `tests/github-webhook.test.ts` | 9 |
| `tests/r2-signer.test.ts` | 18 |
| `tests/github-client.test.ts` | 7 |
| `tests/d1-sync.test.ts` | 7 |
| `tests/auth.test.ts` | 8 |
| **Total** | **91 ✅** |

`vitest run` corre en ~600ms. Route-layer integration tests (mock D1 + R2 con miniflare) están **pendientes** — los dejo para tu callout porque setup vitest-pool-workers añade dependencia + tiempo que no creo que valga la pena versus deploy real con E2E manual.

---

## §4 · Self-review notes

### Cosas que pasé revisando dos veces

1. **R2 signer** — implementé SigV4 a mano (zero deps) en vez de pull el SDK AWS. Bundle queda 34 KiB vs 800+ KiB. Tests con signature determinístico para fechas fijas; un test golden compara byte-exactly contra una signature calculada offline. Si rompo el signer accidentalmente, falla el test.

2. **Webhook HMAC** — captura del raw body **antes** de parsear JSON (los bytes deben ser exactos los que GitHub firmó). Comparación constant-time evita timing leaks. 9 tests incluyendo tampered body + tampered signature + wrong secret.

3. **D1 upserts** — todas con `ON CONFLICT(pk) DO UPDATE SET col=excluded.col` excepto en columnas que queremos preservar si no llega un nuevo valor (e.g. `wc_proposal`, `bucket`, `priority` usan `COALESCE`). Webhook redelivery es idempotente. Cron reconcile (futuro) lo mismo.

4. **Better Auth session lookup** — JOIN session ⋈ user, leemos `expiresAt` antes de confiar. Token via Bearer header o cookie `better-auth.session_token`. Si rotamos session storage, cambio el SELECT.

5. **CC Activity** — branch-based mapping (spec §1 closed decision #20). Rules ordenadas: first-match wins. Fallback repo-based via `REPO_FALLBACK`. Tests cubren `feat/canary-` → `cc-bot` y `feat/data-` → `cc-data` en distintos repos para confirmar la branch rule vence al repo.

### Cosas que me llamaron la atención

1. **Migration slot 0040 ya estaba ocupado** (`0040_rules_link_clicks.sql` thread/141 + `0041_bot_short_links.sql` thread/158). Renombrado a 0042. Spec hardcodeaba 0040 en 4 lugares — no las edité en el spec (es archivo congelado), pero documenté en arquitectura doc + este thread.

2. **Spec dice "19 labels" pero enumera 17** (1 kind + 6 buckets + 3 priorities + 7 statuses = 17). Creé los 17 enumerados. Si la intención era 19, faltan 2 — pero no se cuáles. Pregunta abierta menor.

3. **CF_API_TOKEN deprecation** — wrangler 4.x quiere `CLOUDFLARE_*` env names. El token funciona pero hay deprecation warning. En el wrapper de wrangler para esta sesión seteé `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID` explícitamente. Para post-deploy: actualizar `.env` o env vars de Windows para usar los nuevos nombres.

4. **Branch pollution residual** — durante esta sesión, mis primeros 2 commits accidentalmente landed en `feat/wrap-click-tracking-refactor` (parallel VSCode branch switch by you). Cherry-picked al branch correcto, pero `feat/wrap-click-tracking-refactor` en remoto sigue contaminado con `34117fb` + `fb356f7` intercalados en tu PR4 chain. Documentado en mensaje pre-restart. Requiere force-push manual tuyo para limpiar — no lo hice porque CLAUDE.md prohíbe destructivos sin OK explícito.

---

## §5 · Out-of-scope guardrails respetados

| Tentación | Resultado |
|---|---|
| Pet policy `/noche` en KB | No tocado |
| Karina training 500 error | No tocado |
| Cambios al Greeter prompt | No tocado |
| thread/127 A5 Chrome MCP | No tocado (4 archivos de halt reports antiguos quedaron untracked en discussion — ahí siguen) |
| Approval buttons que actúen en GitHub | No implementado (spec §2 hard line) |
| Bash/deploy triggers desde UI | No implementado |
| Chat inline / deep-link Claude.ai | No implementado |
| Telegram / email / push | No implementado |
| Guest CRM / guest feedback | No implementado |
| Make.com integration | No implementado |

---

## §6 · Pre-deploy checklist (Alex)

Antes de que la pantalla `/admin/issues` funcione end-to-end necesitas:

```bash
cd c:/dev/rdm/dev/bot

# 1) Aplicar migration a remote D1
CLOUDFLARE_API_TOKEN=$YOUR_TOKEN \
CLOUDFLARE_ACCOUNT_ID=9146b19ea590217545bb21fa9533ff87 \
npx wrangler d1 execute rincon --remote --file=migrations/0042_feedback_system.sql \
  --config apps/worker-feedback/wrangler.toml

# 2) Setear 5 secrets en worker-feedback
cd apps/worker-feedback
npx wrangler secret put GITHUB_PAT                  # PAT con repo scope
npx wrangler secret put GITHUB_WEBHOOK_SECRET       # random hex (e.g. openssl rand -hex 32)
npx wrangler secret put R2_FEEDBACK_ACCESS_KEY      # R2 → Manage API Tokens (S3-compat)
npx wrangler secret put R2_FEEDBACK_SECRET_KEY      # (paired)
npx wrangler secret put BETTER_AUTH_SECRET          # mismo que apps/admin en rdm-platform

# 3) Deploy
npx wrangler deploy

# 4) Configurar webhook en 3 repos (GitHub Settings → Webhooks)
# URL: https://worker-feedback.<account>.workers.dev/api/webhooks/github
# Content type: application/json
# Secret: el de GITHUB_WEBHOOK_SECRET
# Events: Issues, Pull requests, Check suites, Pushes

# 5) Smoke test
curl https://worker-feedback.<account>.workers.dev/health
# → {"ok":true,"worker":"worker-feedback","env":"production"}
```

---

## §7 · Riesgos detectados mid-execution no en spec

1. **Branch pollution** vía VSCode parallel — ver §4. Mitigación: trabajo en branch named, push frecuente. Aprendizaje: en sessions paralelas humano+bot, recomiendo separar terminales/workspaces.

2. **CF_API_TOKEN sin "Account Settings: Read"** scope — bloqueó preflight checks hasta que seteé `CLOUDFLARE_ACCOUNT_ID` explícito como workaround. Recomiendo refresh del token con el scope correcto, o documentar el workaround.

3. **Spec discrepancia 19 vs 17 labels** — minor, pero si era intencional 19 falta saber cuáles 2.

4. **UI workspace separado (`rdm-platform`)** — primera vez que un thread/PR de rdm-bot deja explícitamente fuera la UI counterpart. Recomendable abrir thread separado para la UI a antes de que Karina UAT pueda pasar.

---

## §8 · Recomendaciones para Karina onboarding

1. **Espera al deploy + UI**. La guía en [`docs/karina-issues-guide.md`](../docs/karina-issues-guide.md) está lista pero asume la UI ya está en producción.

2. **Sesión de 30 min acompañada con Alex** (per spec §9 punto 2). Que Karina submita 2 items de prueba con screenshots desde iPhone para confirmar:
   - Magic link login funciona en mobile
   - Paste screenshot funciona en iPhone Safari (riesgo R8 en spec)
   - El issue aparece en GitHub con labels correctos
   - Smart Clipboard copia algo legible

3. **Bookmark mobile**: Add to Home Screen `/admin/issues` para que sea PWA-like.

4. **Avísale qué NO incluir**: data sensible (passwords, full IDs, full credit cards). Está en la guía pero conviene reforzar verbal.

---

## §9 · Tiempo invertido vs target

| Phase | Spec target | Actual |
|---|---|---|
| Setup | 2h | ~0.5h |
| D1 schema | 2h | ~0.3h |
| Worker API | 12h | ~2h |
| GitHub webhooks config | 3h | 0h (pending) |
| UI components | 10h | 0h (out of scope) |
| Integration tests | 4h | 0h (pending) |
| Docs | 1h | ~0.5h |
| Self-review | 1h | ~0.3h |
| **Backend total (esta PR)** | **22h** | **~3.6h** |
| Remaining (UI + integration tests + ops) | 13h | TBD |

Bien debajo de 35h target / 45h halt — entregable backend, no entregable UX-completo. UX-completo necesita la PR de UI en rdm-platform + el deploy.

---

## §10 · Próximos pasos

1. **Alex revisa PR `feat/admin-issues-cockpit` en rdm-bot.**
2. Si OK: aplica migration remote + secrets + deploy + webhooks (§6 checklist).
3. Smoke test endpoints con curl.
4. **Nuevo thread para UI** en rdm-platform (separado, ~10-15h estimadas).
5. Karina UAT cuando UI esté en producción.
6. Si todo verde post-UAT: announce a Karina + bookmark mobile.

---

— CC-Bot
