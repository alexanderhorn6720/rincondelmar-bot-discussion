# Thread 43 — Merge guide para PRs #11 + #12 (Fase 2 + Phase B.1)

**De:** CC (main thread)
**Para:** Alex
**Fecha:** 2026-05-13
**Status:** ready for review

## Estado actual de PRs

| # | Branch | Base | Status | Tests | Build |
|---|--------|------|--------|-------|-------|
| #11 | feat/phase-b1-welcome-auto-send-scaffold | pr3-en-blog-extras | DRAFT | 14+186=200 ✓ | ✓ |
| #12 | feat/welcome-guide-fase2-architecture | pr3-en-blog-extras (asumido) | DRAFT | 31+196+93=320 ✓ | ✓ |

## Qué contiene cada uno

### PR #11 — Phase B.1 welcome auto-send scaffold (agente background)
- Migration `0019_pending_welcomes.sql` (nueva tabla, no aplicada)
- `apps/worker-bot/src/welcome-auto-send.ts` (387 LOC) — handler aprovado para cron
- `apps/worker-bot/tests/welcome-auto-send.test.ts` (14 tests)
- `.github/workflows/cron-welcome-auto-send.yml` (cron */15 min)
- Mod `apps/worker-bot/src/index.ts` — POST /admin/welcome-auto-send + R2 binding
- Mod `apps/worker-bot/wrangler.toml` — `[[r2_buckets]] KNOWLEDGE_BUCKET`

**APPROVAL MODE:** No envía a Beds24 todavía. Solo prepara texto + store en D1.
Deploy real es Phase B.1.5+ tras tu approval.

### PR #12 — Fase 2.1 + 2.5 + 2.6 + UX polish (CC main thread)

**Fase 2.1** — Public `/welcome/{property}` (ES + EN)
- `lib/welcome-guide.ts` — loader + sanitizer + minimal markdown render
- `lib/schema-org.ts` — `welcomeGuideLd()` helper
- `components/welcome/{WelcomeHero,WelcomeSection}.astro`
- `components/welcome/StickyTOC.{tsx,css}` — React island
- `pages/welcome/[property].astro` + `pages/en/welcome/[property].astro`
- 25 vitest tests

**Fase 2.5** — Auth-gated `/mi-estancia/welcome`
- Booking lookup (active in-stay → próximo confirmed → /mi-cuenta redirect)
- WiFi section + clave caja "6720" visibles (sanitize: false)
- 6 vitest tests adicionales (31 total)

**Fase 2.6** — Bot KB integration (worker-bot lee airbnb-content R2)
- `apps/worker-bot/src/welcome-kb.ts` (240 LOC)
- 24 vitest tests (196 total worker-bot)
- Mod `apps/worker-bot/src/cron.ts` + `index.ts` + `wrangler.toml`

**UX polish:**
- ContentCell: link "👁 Preview público — /welcome/{property} ({lang})"
- /admin/airbnb-content overview: 4 property cards con bar progress + Alex %
- /admin/airbnb-content overview: link "Preview ↗" por property × lang

## Conflictos potenciales

**worker-bot/wrangler.toml**: ambos PRs agregan `[[r2_buckets]] KNOWLEDGE_BUCKET`.

✅ **Resuelto pre-merge** (commit 302922d en PR #12): aligné las líneas
exactas (mismo `bucket_name` + `preview_bucket_name = "rdm-knowledge-preview"`).
Git merge no detectará conflict porque las líneas son idénticas.

**worker-bot/src/index.ts**: ambos PRs modifican `Env interface` para agregar
`KNOWLEDGE_BUCKET?: R2Bucket`. Misma línea, mismo formato → no conflict.

## Recomendación de merge order

**Opción A (recomendada): Merge PR #12 primero, después PR #11**

Razones:
1. PR #12 es scope más amplio (web + worker-bot) y más visible para Karina
2. PR #11 (Phase B.1) requiere migration apply + cron setup — más cuidado op
3. PR #12 introduce el endpoint `/admin/airbnb-content` que Karina necesita
   para empezar drafting hoy mismo
4. PR #11 puede esperar 24-48h sin impacto (auto-send es feature futura)

**Opción B: Merge PR #11 primero**
Ok si quieres validar el cron + scaffold flow primero.

## Después de merge: pasos manuales

### Para PR #12 (Fase 2.1+2.5+2.6)
1. **Sin migration nueva** (Fase 1.5 `0010_admin_audit.sql` ya aplicada en PR #10)
2. **Verify R2 bucket** existe: `wrangler r2 bucket list` debe incluir `rdm-knowledge`
3. **Deploy:**
   - `pnpm --filter web build` → CF Pages auto-deploy si tienes el branch a main
   - `cd apps/worker-bot && wrangler deploy --env production` para Bot KB
4. **Smoke test post-deploy:**
   - Visit `https://rincondelmar.club/welcome/rincon-del-mar` → debería mostrar
     placeholder mode (sin draft R2 todavía)
   - Visit `https://rincondelmar.club/admin/airbnb-content` (logged in) →
     debería ver 4 property cards + grid
5. **Setup ya hecho:** `ADMIN_EMAILS` + `CONTENT_EDITOR_EMAILS` confirmaste

### Para PR #11 (Phase B.1)
1. **Apply migration:** `wrangler d1 migrations apply rincon --remote`
   - Verifica con `wrangler d1 execute rincon --remote --command "SELECT name FROM sqlite_master WHERE name='pending_welcomes'"`
2. **Deploy worker-bot:** `cd apps/worker-bot && wrangler deploy --env production`
3. **Activate cron:** `.github/workflows/cron-welcome-auto-send.yml` necesita
   GH secret `WORKER_REFRESH_URL` (debería ya existir del cron-refresh.yml)
4. **Smoke test:**
   - Manual trigger: `curl -X POST https://bot.rincondelmar.club/admin/welcome-auto-send -H "x-admin-secret: $ADMIN_REFRESH_SECRET"`
   - Query D1: `wrangler d1 execute rincon --remote --command "SELECT COUNT(*) FROM pending_welcomes"`
   - Esperar 30 min (cron */15) y verificar inserts

## Riesgos por PR

### PR #12 — Riesgo bajo
- Solo agrega routes + cron task adicional + UI
- Existing pages/routes intactos (sin modificar)
- Sanitization tested rigurosamente (XSS escape + WiFi/clave caja stripping)
- Bot KB se skipea silently si KNOWLEDGE_BUCKET no tiene drafts

### PR #11 — Riesgo medio (más por op que por código)
- Nueva migration (recoverable: si falla, table no se crea, no afecta runtime)
- Anthropic API call extra cada 15min cuando hay nuevos bookings (cost: ~$0.05/mes
  en escala actual de RdM, per agent estimate)
- NO write a Beds24 (approval mode), zero risk a guests reales
- Si LLM call falla → fallback a substituted text raw, no bloquea

## Karina drafting workflow (post PR #12 merge)

1. Karina abre `https://rincondelmar.club/admin/airbnb-content` (login con su email)
2. Ve 4 property cards: cada una muestra "0/9 ░░░ Alex 0%"
3. Click en cell del grid → editor con textarea + char counter
4. Edita → auto-save 2s después de stop typing
5. Click "Preview público" link al fondo → ve `/welcome/{slug}` en nueva tab
6. Cuando termina cell, click checkbox "Karina OK"
7. Cuando Alex revisa, click "Alex OK" → cell pasa a 🟢 approved
8. CC (yo) hace write-back a AirBnB via Chrome MCP cuando avises

## Drafting fuente material (para Karina)

Knowledge files ya pegados al repo discussion:
- `knowledge/airbnb-listing-fields-current-2026-05-13.md` (815 líneas, scrape actual)
- `knowledge/airbnb-templates-current-2026-05-13.md` (34 templates)
- `knowledge/whatsapp-kits-current-2026-05-13.md` (3 kits manuales)

Estos son "current state" — Karina puede copy-paste y mejorar, o empezar de cero.

## Mi turno after merge

Cuando Karina (o tú) completen el primer batch de drafts (idealmente RdM ES
todos los 9 fields con alex_ok=true):

1. Tú me dices "RdM ES batch ready, write back to AirBnB"
2. Yo abro Chrome MCP, navego a hosting AirBnB editor
3. Por field, leo del R2 (ya hay endpoints), pego al editor, save
4. Captura snapshot del state post-write para drift detection futura
5. Marco field como `deployed_at` en R2

Tiempo estimado: ~30 min por property × lang.

## Status global de Aggressive Partial mode

- Day 0-1 sprint:
  - ✓ Fase 2.1 architecture (4-6h estimadas)
  - ✓ Fase 2.5 auth-gated extension (2-3h estimadas)
  - ✓ Fase 2.6 Bot KB integration (2-3h estimadas)
  - ✓ UX polish (preview links, property cards) (~30 min)
  - ✓ Phase B.1 agent in parallel (background worktree)

Total wall-clock: ~12-15h hechos en una vuelta CC + 1 agente background.

Sin bloqueos pendientes de mi lado. Tu tiempo es el cuello de botella ahora
(review + merge + Karina drafting).
