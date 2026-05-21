# Thread 158 · WC → CC · `/ir/*` system overhaul (brain deep)

**From:** WC
**To:** CC-Bot (new session)
**Date:** 2026-05-21
**Type:** brain deep → DoIt spec
**Output thread:** thread/159 (CC report)
**Estimated effort:** 12-16h CC across 6 atomic PRs

---

## 1 · Context (why this exists)

### Origen del problema

Alex reportó 2026-05-21 que los links que el bot Greeter v5/v6 manda a guests no funcionan. Audit empírico de 5 mensajes prod (todos `v=v5`, frescos hace ~30min):

| Bot promesa al guest | URL emitido | Destino real | Fail mode |
|---|---|---|---|
| "Te muestro disponibilidad en vivo para 5 personas del 29 mayo al 3 jun" | `/ir/disponibilidad?check_in=2025-05-29&...&guests=5` (sin prop) | `rincondelmar.club/` (home) | Fallback descarta dates+guests; año 2025 alucinado |
| "Te muestro las diferencias entre las 4 villas" | `/ir/comparar-casas?...` | `rincondelmar.club/` (home `#casas`) | Promete comparativa, target es lista |
| "Cotización en vivo para 15 personas Rincón del Mar" | `/ir/precios?prop=rincon-del-mar&guests=15` | `/rincon-del-mar` (sin guests pre-pobl.) | `precios` intent no tiene `accepts_guests` |
| "Toda la info Huerta Cocotera" | `/ir/huerta-cocotera?conv=...` | `/contacto` ⚠️ | LLM emitió property slug como intent |

Adicionalmente, los URLs son visualmente feos para huéspedes: `bot.rincondelmar.club/ir/disponibilidad?conv=20667327&v=v5&lang=es&check_in=2025-05-29&...&guests=5` no transmite la calidez de anfitrión que el bot intenta proyectar.

### Audit del código (qué se shipped vs qué se planeó)

Cronología original (thread/21, /50, /52, /53, /65, /66, /80, /82):

| Componente | Estado | Issue |
|---|---|---|
| `apps/worker-bot/src/intent-resolver.ts` (CATALOG_ES/EN, 27 intents) | LIVE | Falta intent `propiedad`; fallback descarta query params (Bug B.1); `precios` sin `accepts_guests` (Bug C); `comparar-casas` → `/#casas` (Bug D by design) |
| `packages/agents/greeter/tools-v5.ts` (`VALID_INTENT_SLUGS` enum 26 strings) | LIVE | Hardcoded duplicate de keys de CATALOG_ES — drift inevitable |
| `packages/agents/greeter/process-tool-use.ts` (`processRouteUserToUrl`) | LIVE | **No defensive guard runtime**: pasa `args.intent_slug` raw al `wrapClickTracking` y al `resolveIntent`. Si LLM viola enum, slug llega literal al URL path |
| `apps/worker-bot/src/click-tracking.ts` (handler `/ir/:slug`) | LIVE | Hace re-resolve server-side; mismo bug de fallback descartando params; **no valida slug explícitamente** antes de resolver |
| `apps/worker-bot/src/greeter-v5-deps.ts` (`wrapClickTracking`) | LIVE | URL formato `bot.rincondelmar.club/ir/{intent}?...` con query string largo y feo |
| `packages/agents/greeter/system-prompt-v5.ts` + `system-prompt-v6.ts` | LIVE | **No inyectan `today=YYYY-MM-DD`** en dynamic context → LLM aluc. años pasados (Bug B.2). §INTENT_CATALOG markdown está hardcoded (drift con TS) |
| `bot_link_clicks` D1 table | LIVE | No guarda `check_in/check_out/guests`, `used_fallback`, `fallback_reason` → blast radius de bugs no medible |
| v5 vs v6 canary status | unclear | Memory dice v6 100%. Prod muestra `v=v5` fresco. Auditoría separada. |

### Causa raíz consolidada

Cuatro problemas estructurales, no 4 bugs aislados:

1. **Drift de 3 fuentes** (system-prompt §INTENT_CATALOG markdown + tools-v5 enum + intent-resolver catalog) sin sync test → cada PR introduce divergencia silenciosa
2. **Falta intent `propiedad`** → LLM no tiene slug para "info general de villa X" → alucina property slug como intent
3. **Fallback path estructuralmente descarta query params** → cualquier intent que requiera property pierde dates+guests si user no especificó villa
4. **No `today=` inyectado** → LLM no tiene anchor temporal para parsear "29 de mayo" → defaultea a año memorizado (2025)

Sumado al UX: query strings largos con `conv/v/lang/check_in/check_out/guests` no proyectan tono de anfitrión.

---

## 2 · Explicit scope

### ✅ YES — en scope

1. **Unificar las 4 fuentes** del catálogo en `packages/agents/greeter/intent-catalog.ts` (single source of truth para CATALOG_ES, CATALOG_EN, VALID_INTENT_SLUGS, VALID_PROPERTY_SLUGS, VALID_CITY_SLUGS, INTENT_HUMAN_NAMES)
2. **Resolver gaps**: `precios` y `disponibilidad` aceptan `check_in/check_out/guests`; fallback propaga dates+guests
3. **Intent `propiedad`** dedicado con `url_template: '/{property}/'`, `accepts_dates`, `accepts_guests`
4. **Defensive guard runtime** en `processRouteUserToUrl`: si `args.intent_slug ∈ VALID_PROPERTY_SLUGS`, remap a `intent='propiedad' + property=slug` + log para observability
5. **today= injection** en `buildSystemPromptBlocks(V5|V6)` dynamic context + validator post-tool-call que rechaza dates pasados (con margen 24h tz buffer)
6. **Bug D opening_line tweak**: §INTENT_CATALOG v5+v6 redact entry `comparar-casas` para no prometer tabla comparativa
7. **Short link service**:
   - Tabla D1 `bot_short_links` con TTL 10d + 50d buffer
   - Formato URL Patrón B: `intent-nombre-contexto-xxx` (ej. `rincondelmar.club/ir/precio-erika-mayo29-x7q`)
   - Hash 3-char random sufix para uniqueness
   - Subdomain: `rincondelmar.club/ir/*` para guests; `bot.rincondelmar.club` se mantiene para internal tools (beds24 proxy)
8. **`bot_link_clicks` schema upgrade**: agregar columnas `check_in/check_out/guests/used_fallback/fallback_reason/remapped_from` para forensic analytics
9. **CI snapshot test** que valida sync entre `CATALOG_ES.keys()`, `CATALOG_EN.keys()`, `VALID_INTENT_SLUGS` y la sección §INTENT_CATALOG renderizada en system-prompt v5+v6
10. **Tests** unit + integration cubriendo los 4 bugs + intent propiedad + defensive guard + today validator + short link generation/resolution/expiry

### ❌ NO — out of scope (queue separado)

- Página `/comparar` real (HTML view con tabla comparativa de 4 villas)
- Reescribir el sistema canary v5/v6 (brain quick separado tras este spec)
- Migrar `bot_link_clicks` legacy data al short link service (legacy queda como histórico)
- Backfill de bot_link_clicks expired entries (cleanup automático en cron)
- Casa Chamán en intent catalog (memory anti-pattern: hidden hasta Q3 2026)
- Tour-360 expansion a Huerta/Combinada (intent existe pero `only_for_properties` restringe)
- Reescribir 4 propiedades' anchor sections en property pages
- Cambios al admin UI (`/admin/bot-metrics`, `/admin/conv`)
- Sunset del legacy `/ir/{slug}?prop=X&conv=Y&...` URL format (mantener como fallback compat 90d)

### 🟡 LATER — fuera del spec pero documentar

- v6 canary mismatch audit (brain quick post-spec): auditar `canary.ts` + `bot_config.greeter_prompt_version` para confirmar v6 100% o si hay regresión
- Página `/comparar` real con tabla
- Migración de `bot_link_clicks` legacy histórica a una vista agregada
- Telemetry dashboard para ver tasa de fallback por intent (en `/admin/bot-metrics`)

---

## 3 · Closed decisions (Alex 2026-05-21)

| # | Decisión | Valor |
|---|---|---|
| 1 | Catálogo sync mechanism | CI snapshot test (no codegen build-time) |
| 2 | Bug A defensive guard timing | Dentro del spec (no hotfix paralelo) |
| 3 | Bug C precios + guests fix | Schema (add `accepts_guests` to intent), no prompt rule |
| 4 | Bug D scope | Domar `opening_line`; página `/comparar` queue separado |
| 5 | Bug B.1 fallback | Propagar `check_in/check_out/guests` al fallback URL |
| 6 | Bug B.2 año 2025 fix | `today=YYYY-MM-DD` inyectado + validator post-tool-call |
| 7 | Intent `propiedad` | Sí — dedicado con `url_template: '/{property}/'` |
| 8 | v5 vs v6 scope | Ambos (resolver y catalog son compartidos) |
| 9 | Thread numbering | CC pre-flight: `ls threads/15[8-9]-*.md`; usar primer libre ≥158 |
| 10 | Fix tactical o estructural | Ambos (A-D + reco #1 sync) en un solo spec |
| 11 | Canary v5/v6 mismatch | brain quick separado tras este spec (no bloquea) |
| 12 | Formato URL | Patrón B: `intent-nombre-contexto-xxx` (~18-32 chars) |
| 13 | Privacy nombre | Visible siempre (vía slug del subscriber first_name) |
| 14 | TTL short link | 10 días desde `created_at` |
| 15 | Expired behavior | 302 → `/{prop}/` si tabla tiene `property`, sino `/` |
| 16 | Domain switch | `rincondelmar.club/ir/*` para guests; `bot.rincondelmar.club` permanente internal (beds24 proxy) |
| 17 | Cleanup policy | 10d TTL + 50d buffer en tabla; cron mensual `DELETE WHERE created_at < unix_now - 60d` |
| 18 | Hash sufix | 3 chars random `[a-z2-9]` (31³ = 29K combos) como tiebreaker para colisiones |
| 19 | Nombre fallback | `subscriber_name` vacío/phone/emoji → `huesped` |
| 20 | Idempotency | Sin reuse de hash. Cada generación = nuevo row |

---

## 4 · Implementation

Spec técnico completo (código, schemas, helpers, handlers) está en el archivo descargado por Alex. Resumen ejecutivo de archivos tocados:

- **NEW** `packages/agents/greeter/intent-catalog.ts` — single source of truth
- **NEW** `apps/worker-bot/src/short-link-generator.ts` — slugifyName, contextSlug, randomSuffix, createShortLink
- **MODIFY** `apps/worker-bot/src/intent-resolver.ts` — importa desde intent-catalog, fallback enriquecido vía helper `appendQueryParams`
- **MODIFY** `packages/agents/greeter/tools-v5.ts` — importa desde intent-catalog
- **MODIFY** `packages/agents/greeter/system-prompt-v5.ts` + `system-prompt-v6.ts` — interpola `{{INTENT_CATALOG_MARKDOWN}}` placeholder + today= injection
- **MODIFY** `packages/agents/greeter/process-tool-use.ts` — defensive guard remap + date validator + async wrapClickTracking
- **MODIFY** `apps/worker-bot/src/click-tracking.ts` — rewrite handler para `/ir/:id` con TTL logic
- **MODIFY** `apps/worker-bot/src/greeter-v5-deps.ts` — wrapClickTracking async, llama createShortLink
- **MODIFY** `apps/worker-bot/src/index.ts` — route wiring nuevo handler + legacy compat 90d
- **MODIFY** `apps/worker-bot/src/cron.ts` — cleanup mensual
- **NEW** Migration `0034_bot_short_links.sql` — tabla nueva
- **NEW** Migration `0035_bot_link_clicks_enrichment.sql` — 6 nuevas columnas
- **MODIFY** `apps/worker-bot/wrangler.toml` — cron trigger mensual

Ver detalle code blocks en spec local (Alex tiene file `thread-158-draft.md`).

### Cambios clave en `intent-catalog.ts`

```ts
export interface IntentDef {
  url_template: string;
  requires_property?: boolean;
  only_for_properties?: readonly string[];
  accepts_dates?: boolean;
  accepts_guests?: boolean;
  accepts_city?: boolean;
  accepts_category?: boolean;
  fallback: string;
  human_name: string;      // NEW — para Patrón B URL (precio, cotizacion, info, etc)
  description: string;     // NEW — para system-prompt rendering runtime
  catalog_section: 'hot' | 'site-wide' | 'catch-all';
}

// Nuevo intent `propiedad`:
propiedad: {
  url_template: '/{property}/',
  requires_property: true,
  accepts_dates: true,
  accepts_guests: true,
  fallback: '/#casas',
  human_name: 'info',
  description: '"Info general de villa X" / "Cuéntame de Huerta" — overview de la propiedad',
  catalog_section: 'hot',
}

// `precios` ahora acepta dates + guests:
precios: { ..., accepts_dates: true, accepts_guests: true }

// `disponibilidad` ahora acepta guests:
disponibilidad: { ..., accepts_guests: true }
```

### Short link generator core

```ts
const URL_SAFE_CHARS = 'abcdefghjkmnpqrstuvwxyz23456789';  // 31 chars, no confusos
const MAX_NAME_LEN = 12;
const SUFFIX_LEN = 3;
const MAX_RETRIES = 5;

function slugifyName(name?: string): string {
  if (!name) return 'huesped';
  const cleaned = name
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
    .slice(0, MAX_NAME_LEN);
  if (!cleaned || /^\d+$/.test(cleaned)) return 'huesped';
  return cleaned;
}

function contextSlug(params): string {
  if (params.check_in) {
    const months = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
    const [, m, d] = params.check_in.split('-');
    return `${months[parseInt(m,10)-1]}${parseInt(d,10)}`;  // mayo29
  }
  if (params.guests) return `${params.guests}pax`;
  return params.today.replace(/-/g, '');  // 20260521
}

// Result: rincondelmar.club/ir/precio-erika-mayo29-x7q
```

### Defensive guard

```ts
// In processRouteUserToUrl, BEFORE resolveIntent:
if ((VALID_PROPERTY_SLUGS as readonly string[]).includes(args.intent_slug)) {
  remapped_from = args.intent_slug;
  property = args.intent_slug as PropertySlug;
  intent = 'propiedad';
  console.warn(JSON.stringify({ event: 'intent_remap_property_as_intent', ... }));
}
```

### today= injection

```ts
// In buildSystemPromptBlocksV5/V6:
const today = new Date().toISOString().slice(0, 10);
// ... dynamic context block (NO cached):
`- Today's date (use as anchor for any date parsing): ${today}\n` +
```

### Date validator

```ts
function validateDates(args, today): { valid: boolean; reason?: string } {
  // Reject check_in or check_out < today - 24h (timezone grace)
  // If invalid → strip dates from args, don't propagate to URL
}
```

### Migration 0034

```sql
CREATE TABLE bot_short_links (
  id TEXT PRIMARY KEY,
  target_url TEXT NOT NULL,
  property TEXT,
  intent_slug TEXT NOT NULL,
  conv_hash TEXT,
  bot_version TEXT,
  subscriber_name_slug TEXT,
  remapped_from TEXT,
  used_fallback INTEGER NOT NULL DEFAULT 0,
  fallback_reason TEXT,
  click_count INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  first_click_at INTEGER,
  last_click_at INTEGER
);
CREATE INDEX idx_short_links_created ON bot_short_links(created_at);
CREATE INDEX idx_short_links_conv ON bot_short_links(conv_hash, created_at);
```

### Migration 0035

```sql
ALTER TABLE bot_link_clicks ADD COLUMN check_in TEXT;
ALTER TABLE bot_link_clicks ADD COLUMN check_out TEXT;
ALTER TABLE bot_link_clicks ADD COLUMN guests INTEGER;
ALTER TABLE bot_link_clicks ADD COLUMN used_fallback INTEGER NOT NULL DEFAULT 0;
ALTER TABLE bot_link_clicks ADD COLUMN fallback_reason TEXT;
ALTER TABLE bot_link_clicks ADD COLUMN remapped_from TEXT;
```

### Handler `/ir/:id` con TTL

```ts
const TTL_SECONDS = 10 * 86400;

export async function handleShortLinkClick(c, env): Promise<Response> {
  const id = c.req.param('id');
  const row = await env.DB.prepare(
    'SELECT target_url, property, created_at FROM bot_short_links WHERE id = ?'
  ).bind(id).first();

  if (!row) return c.redirect('https://rincondelmar.club/', 302);

  const expired = (Math.floor(Date.now()/1000) - row.created_at) > TTL_SECONDS;
  if (expired) {
    const target = row.property
      ? `https://rincondelmar.club/${row.property}/`
      : 'https://rincondelmar.club/';
    return c.redirect(target, 302);
  }

  // Fresh — increment click count async, redirect to target
  c.executionCtx.waitUntil(/* UPDATE click_count */);
  return c.redirect(row.target_url, 302);
}
```

### Cron cleanup mensual

```ts
// Trigger: "0 3 1 * *" (1st of month, 3am UTC)
async function cleanupExpiredShortLinks(env): Promise<void> {
  const cutoffEpoch = Math.floor(Date.now()/1000) - (60 * 86400);  // 10d TTL + 50d buffer
  await env.DB.prepare('DELETE FROM bot_short_links WHERE created_at < ?').bind(cutoffEpoch).run();
}
```

---

## 5 · Tests

### 5.1 · Unit tests

| File | Coverage |
|---|---|
| `intent-resolver.test.ts` | Each intent: happy path + fallback. `propiedad` intent. Fallback con dates/guests propagación. `precios` con guests. `comparar-casas` → `/#casas`. |
| `process-tool-use.test.ts` | Defensive guard: `intent_slug='huerta-cocotera'` → remap. Date validator: past dates stripped. Today helper mockeable. |
| `short-link-generator.test.ts` | `slugifyName`: accents, phone, emoji, empty. `contextSlug`: check_in → mes+día. `createShortLink`: insert success + UNIQUE retry. |
| `intent-catalog.test.ts` | `renderIntentCatalogMarkdown` produce markdown table válido. |
| `intent-catalog-sync.test.ts` | CI snapshot — 4 sources sincronizadas. |

### 5.2 · Integration tests

| File | Coverage |
|---|---|
| `click-tracking-shortlink.test.ts` | Full flow: createShortLink → GET /ir/:id fresh → 302 to target. Expired → 302 to fallback. Click count increments. Not found → 302 to home. |
| `runGreeter-v5-integration.test.ts` | Update tests para reflejar new URL format. Tool emit `intent='huerta-cocotera'` → remap → URL `/ir/info-huesped-...`. |
| `cron-cleanup.test.ts` | DELETE older than 60d. |

### 5.3 · Smoke tests (post-deploy, Alex/CC manual)

Los 4 escenarios reportados originalmente deben pasar:

| Scenario | Expected URL | Expected target |
|---|---|---|
| Erika: 5 personas 29 mayo - 3 junio | `rincondelmar.club/ir/disponible-erika-mayo29-xxx` | Home `/#casas?check_in=2026-05-29&check_out=2026-06-03&guests=5` |
| Erika: comparar 4 villas | `rincondelmar.club/ir/comparar-erika-20260521-xxx` | `/#casas` (bot ya no promete tabla) |
| Erika: cotización 15 personas RdM | `rincondelmar.club/ir/precio-erika-15pax-xxx` | `/rincon-del-mar/?guests=15` |
| Erika: info Huerta | `rincondelmar.club/ir/info-erika-20260521-xxx` | `/huerta-cocotera/` (vía `propiedad` intent post defensive guard) |

---

## 6 · Definition of done

- [ ] `intent-catalog.ts` creado con CATALOG_ES, CATALOG_EN, VALID_INTENT_SLUGS, VALID_PROPERTY_SLUGS, VALID_CITY_SLUGS + 28 intents incluyendo `propiedad`
- [ ] `intent-resolver.ts`, `tools-v5.ts`, `system-prompt-v5.ts`, `system-prompt-v6.ts` importan desde intent-catalog (no duplicate)
- [ ] `precios` y `disponibilidad` aceptan check_in/check_out/guests
- [ ] Fallback URL recibe check_in/check_out/guests cuando aplica
- [ ] Defensive guard remap funciona: `intent='huerta-cocotera'` → `intent='propiedad', property='huerta-cocotera'`
- [ ] `today=YYYY-MM-DD` inyectado en dynamic context v5 + v6
- [ ] Date validator post-tool-call strip dates < today
- [ ] §INTENT_CATALOG entry `comparar-casas` cambia description a "Ver lista de villas" (no "tabla comparativa")
- [ ] Tabla `bot_short_links` creada vía migration 0034
- [ ] `bot_link_clicks` upgraded con 6 nuevas columnas vía migration 0035
- [ ] `createShortLink()` genera Patrón B URLs correctamente
- [ ] Handler `/ir/:id` lookup + expiry logic + 302 funcionando
- [ ] Legacy `/ir/{slug}?...` URLs siguen funcionando 90d (compat)
- [ ] Cron mensual cleanup configurado en wrangler.toml
- [ ] CI snapshot test pasa (sync de 4 sources)
- [ ] Unit tests pasan: 5 suites
- [ ] Integration tests pasan: 3 suites
- [ ] Smoke tests post-deploy: 4 escenarios de Erika pasan
- [ ] thread/159 posted con report
- [ ] No Casa Chamán en cualquier output (anti-pattern memory check)

---

## 7 · Risks + mitigations

| # | Riesgo | Mitigation |
|---|---|---|
| R1 | `wrapClickTracking` async breaking change rompe callers | Update `process-tool-use.ts` con await. Tests existentes capturan regressions. |
| R2 | D1 down al GENERAR short link → bot turn falla | Fallback a legacy format URL si `createShortLink` throws. Legacy handler sigue 90d. |
| R3 | D1 down al CLICK del short link | Cloudflare D1 high availability. 503 + retry. |
| R4 | Migration 0034/0035 fails en prod | CC verifica + rollback plan: `DROP TABLE` + revert ALTER. |
| R5 | `today=` rompe ephemeral cache | `today=` va en bloque NO cacheado (dynamic context). |
| R6 | Defensive guard remap pierde `opening_line` context | LLM ya menciona property en opening textualmente. Remap solo cambia URL. |
| R7 | `/#casas?check_in=X&guests=Y` no es leído por booking card global | CC pre-flight verifica `BookingCardGlobal.tsx`. Si no → issue + skip. NO fix inline. |
| R8 | Hash collision real | 5 retries con nuevos sufijos = 31³⁵ combos. Si falla → fallback legacy. |
| R9 | Nombre con caracteres raros explota slugify | Tests cubren: accents, emoji, phone, empty. `huesped` fallback. |
| R10 | Cron cleanup nunca corre (silent fail) | Telegram alert si cron falla > 2 ejecuciones. Add to `/admin/health`. |
| R11 | v6 canary mismatch con `v=v5` frescos | OUT OF SCOPE. Brain quick separado audita post-spec. |
| R12 | Casa Chamán slip en intent catalog | `VALID_PROPERTY_SLUGS` excluye casa-chaman. Test explicit. |

---

## 8 · Atomic PRs (6 partes)

| PR | Scope | Effort CC |
|---|---|---|
| **A1** | `intent-catalog.ts` + refactor de 4 sources + CI snapshot test | 3-4h |
| **A2** | Intent `propiedad` + defensive guard runtime + tests | 2h |
| **A3** | Resolver fallback enriquecido + `precios/disponibilidad` accept guests + tests | 1.5h |
| **A4** | `today=` injection + date validator + tests | 1.5h |
| **A5** | Short link service: migration 0034 + generator + handler `/ir/:id` rewrite + `wrapClickTracking` async + tests | 4h |
| **A6** | Migration 0035 + cron cleanup + comparar-casas opening_line tweak + smoke verify | 1h |

**Order dependency**: A1 → A2/A3/A4 paralelizables → A5 (depends on A1) → A6 (depends on A5).

**Each PR**: branch `feat/ir-overhaul-aX-{slug}`. Squash merge. PR description tight, mobile-first.

---

## 9 · Pre-flight checklist (CC mandatory)

Antes de empezar A1, CC ejecuta:

1. `git pull origin main` en rdm-bot + rdm-discussion
2. `ls threads/15[8-9]-*.md` → confirmar 158 es libre, sino usar próximo libre
3. `pnpm wrangler d1 execute rincon --remote --command "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('bot_link_clicks','bot_short_links');"` → confirmar `bot_link_clicks` existe, `bot_short_links` NO existe
4. `pnpm wrangler d1 migrations list rincon` → confirmar next migration number es 0034 (sino usar real next)
5. Verify Beds24 proxy en `bot.rincondelmar.club` sigue activo (no romper internal tools)
6. `grep -n "subscriber_name" packages/agents/greeter/process-tool-use.ts` → confirmar ya está en context
7. `grep -rn "BookingCardGlobal\|check_in.*useEffect\|searchParams.get" apps/web/src/components/` → confirma booking card global lee URL params al mount. Si NO → abrir issue + skip propagación al fallback `/#casas` (out of scope).

Si CUALQUIER pre-flight falla → halt + Telegram Alex.

---

## 10 · Coordination Alex

| Trigger | Acción Alex |
|---|---|
| A5 PR open | Review + verifica wrangler routes `rincondelmar.club/ir/*` → worker |
| A5 merged | Ejecuta migration 0034 vía `wrangler d1 migrations apply rincon` |
| A6 merged | Ejecuta migration 0035 |
| Smoke tests | Manda 4 mensajes de prueba al bot via WhatsApp, verifica URLs |
| Telegram halt | Lee context, decide next step |

**Budget total**: 12-16h CC. Excediendo 1.5× (24h) = stop + report.
**Comunicación**: solo milestones (PR open per A1-A6, smoke complete, thread/159 posted). NO mid-PR commits.

---

## 11 · Out-of-spec follow-ups (queue separado)

- **Brain quick canary audit**: ¿por qué `v=v5` frescos si memory dice v6 100%? Audit `canary.ts` + `bot_config.greeter_prompt_version` + force-flags.
- **Página `/comparar` real**: HTML view con tabla comparativa (chef incluido, capacidad, tour 360, precio rango). 4-6h frontend.
- **Telemetry dashboard**: `/admin/bot-metrics` agregar tab "Short Links" con CTR per intent, fallback rate, expiry rate.
- **Backfill `bot_link_clicks` legacy** con enriched columns (vía cron). Opcional.

---

*WC, 2026-05-21*
