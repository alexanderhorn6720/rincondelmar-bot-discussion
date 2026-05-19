# rdm-bot · STATE (draft)

> Source of truth ligero para "qué hay vivo ahora" en `rdm-bot`.
> Generado por CC vía DoIt thread/143 (2026-05-19). Para promote-to-root, ver §H.

---

## A. STACK

- `apps/`: `web` (Astro + Cloudflare Pages), `worker-bot` (Greeter/Booker LLM), `worker-pago` (MercadoPago), `worker-tours` (read-only tours API)
- `packages/`: `agents`, `auth`, `channels`, `conversation-state`, `db`, `email-templates`, `llm-client`, `mp`, `shared`
- Workers desplegados (nombre prod):
  - `rincondelmar-bot` → `web` → rincondelmar.club
  - `rincon-bot` → `worker-bot` → bot.rincondelmar.club + beds24.rincondelmar.club (thread/134)
  - `rincon-pago` → `worker-pago` → pago.rincondelmar.club (cron triggers ACTIVOS)
  - `rincon-tours` → `worker-tours` → tours.rincondelmar.club
- D1: `rincon` (id `d81622d7-32e2-40a3-9609-80813c0e8a96`, compartido por los 3 workers + web)
- R2 buckets: `rdm-knowledge` (templates + KB, preview `rdm-knowledge-preview`), `assetsrdm` (imágenes)
- KV: `KV_KNOWLEDGE` (`033ee15acf3744c096e83342d2e81dd4`) prompts cacheados 2h
- Last deploy dates (verify con `wrangler whoami` / dashboard): commit más reciente en `main` = 2026-05-19 (7625c55)

## B. PRs OPEN (live `gh pr list`)

| #   | Título                                          | Branch                              | Author          | Why pending                  |
|-----|-------------------------------------------------|-------------------------------------|-----------------|------------------------------|
| 130 | Feat/a6 reglas adicionales deploy               | feat/a6-reglas-adicionales-deploy   | alexanderhorn6720 | review pendiente Alex      |
| 114 | feat(journey): D1-override editor for journey templates | feat/journey-templates-editor | alexanderhorn6720 | review pendiente Alex      |

## C. BRANCHES ACTIVAS LOCAL (no mergeadas a main)

- `feat/admin-nav-phase-2-4` — 2026-05-19 — admin nav siguiente fase, probable continuación post-#129
- `feat/beds24-proxy-calendar` — 2026-05-19 — current branch, shipped via #127 (proxy thread/134), tail commits 340a40e + 29e5a52
- `feat/a6-reglas-adicionales-deploy` — 2026-05-19 — PR #130 abierto
- `feat/role-based-nav-visibility` — 2026-05-19 — shipped #129, branch sin podar
- `feat/thread-141-house-rules-paper-trail` — 2026-05-19 — shipped #128, branch sin podar
- `feat/a5-airbnb-bulk-approve-writeback` — 2026-05-19 — A5 phase incomplete (67% per memory)
- `claude/compassionate-franklin-238c62` — 2026-05-18 — CC sandbox worktree, candidato a poda
- `claude/zen-payne-ac1349` — 2026-05-18 — CC sandbox worktree, candidato a poda
- `feat/journey-templates-editor` — 2026-05-18 — PR #114 abierto
- `feat/in-stay-post-stay-touchpoints`, `feat/manychat-subscriber-sync`, `fix/manychat-account-update-tag`, `fix/manychat-subscriber-id-routing`, `fix/resolve-route-disjoint`, `feat/beds24-dump-endpoint`, `feat/pre-stay-a4-admin-ui`, `feat/pre-stay-a3-scan-t14-t7-t1`, `feat/pre-stay-a2-scan-welcome`, `feat/pre-stay-a1.5-t14-touchpoint`, `feat/pre-stay-a1`, `fix/resync-chunked`, `debug/resync-error-samples`, `hotfix/mojibake-guest-names`, `feat/guests-resync-beds24` — todas 2026-05-18, shipped & sin podar (≥15 branches mergeadas con misma fecha)

## D. POST-MERGE PENDING

- D1 migrations totales: 39 archivos (`0001` → `0039_audit_log.sql`). Aplicación a prod NO verificada en este snapshot — verificar con `wrangler d1 migrations list rincon --remote`. Las recientes (`0035_pre_stay_columns` → `0039_audit_log`) corresponden a PRs mergeados últimos 7d, asumir aplicadas pero CONFIRMAR.
- Workers con cambios local sin deploy: ninguno detectado (todas las branches activas son post-merge sin pendientes nuevos), excepto las dos PRs open (#114, #130) que esperan deploy post-merge.
- Cron jobs activos (`apps/worker-pago/wrangler.toml`):
  - `*/30 * * * *` — expire holds
  - `0 15 * * *` — pre-arrival reminder 09:00 MX
  - `0 17 * * *` — review request 11:00 MX
  - `0 */6 * * *` — auth cleanup
  - `0 21 * * *` — auto check-in / complete 15:00 MX
- worker-bot, worker-tours, web: SIN crons activos (Workers Free plan, GH Actions externa llama `/admin/refresh-now` cada 2h).

## E. ANTI-PATTERNS ENFORCED

- Casa Chamán NO en Greeter system prompt hasta Q3 2026 renovation; OK mencionar interno como "in renovation".
- Pet fee: **$300 MXN/ESTANCIA**, max 2 por reserva. NUNCA "/noche".
- Beds24 sync: `Prices&Availability` only. NUNCA `Everything`.
- Beds24 horizon: 365 días. No más.
- No deploys prod viernes >5pm (CLAUDE.md).
- Commits con secrets plaintext → blocked por hook + `wrangler secret put`.
- No hardcodear paths Windows; usar placeholders + `Test-Path`.
- `ALTER TABLE` durante multi-agent execution → blocked.
- "Tests pass" sin self-review del diff → not done.
- Beds24 v2 write endpoints: array body raw, NO `{data:[]}` (memory: reference_beds24_v2_array_body).
- Beds24 outbound chat echoes como `booking_modified` webhook ~3s después; upsert debe preservar journey/automation columns (memory: reference_beds24_outbound_echo_webhook).
- Pre-stay = 4 touchpoints (welcome + T-14 + T-7 + T-1), NO 3 (memory: project_pre_stay_4_touchpoints).
- Morenas chef = strictly opt-in T-14 deadline (memory: feedback_morenas_chef_opt_in).
- Prod ops manual: `wrangler deploy` / `d1 execute --remote` / `secret put` NUNCA ejecutar autónomo (memory: feedback_prod_deploy_always_manual).

## F. ÚLTIMA SEMANA SHIPPED (top 15 main, últimos 7d)

- `7625c55` feat: thread 141 house rules paper trail (#128)
- `391af4d` feat(admin-nav): role-based visibility + 7 roles + M1-M5 placeholders (#129)
- `c2d752f` fix(mcp): use --browser-url explicit for chrome-devtools-mcp attach
- `1f26187` chore(claude): permissions config for autonomous execution (3-tier)
- `150e78e` chore(mcp): add chrome-devtools-mcp config for A5 write-back
- `d84ed64` feat(inbox): mobile WhatsApp-style UX — thread/131 Part E rescue (#126)
- `15644e9` feat(airbnb-content): bulk-approve endpoint A5 §1 (#116)
- `03f063a` feat(beds24-webhook): inline normalize + welcome via waitUntil (#123)
- `92ece0e` chore(biome): ignore vendor CSS + utility scripts (#118)
- `aa0f3ab` fix(karina-training): escape literal {placeholders} as HTML entities (#125)
- `ea69adb` fix(karina-training): self-close void elements (#124)
- `ba857ee` / `24766a3` fix(admin): allow karina@ into karina-training (#121/#120)
- `30dc515` revert(cf-pages): remove root wrangler.toml — caused prod auth 500 (#119)
- `20f46fa` fix(beds24-normalize): preserve journey columns on upsert (#117)
- `494addc` feat(pre-stay): in-stay + post-stay touchpoints (#113)
- `2772d9d` feat(manychat): auto-create subscribers for direct-booking guests (#112)
- `2f94331` fix(messenger): sendManychatContent via setCustomField+sendFlow (#111)

Tema dominante: **pre-stay journey** (#112, #113, #117, varias branches `feat/pre-stay-*`), **karina-training admin** (#120-#125), **admin-nav role-based** (#129), **mobile inbox rescue** (#126), **thread/141 paper trail** (#128). Beds24 proxy (thread/134) shipped via #127.

## G. OUTSTANDING DECISIONS (Alex pending)

Derivado de threads con type=question/spec sin result thread en últimas 2 semanas (cross-check con gap-analysis):
- A5 airbnb bulk-approve writeback — 67% completion per memory `project_a5_deploy_confirmed_session_gap`, falta session Better Auth en Chrome:9222 + per-cell deploy-confirmed flow.
- Browserbase AirBnB KPI scraper — thread/132 backlog item, decisión pendiente.
- A6 reglas_adicionales deploy — PR #130 esperando review.
- Journey templates editor (PR #114) — review pendiente desde 2026-05-18.
- Casa Chamán renovation timeline → cuándo unhide del Greeter (Q3 2026 placeholder).

## H. LAST UPDATED + UPDATE PROTOCOL

- Fecha generación: 2026-05-19
- Por: CC vía DoIt thread/143 (branch `chore/state-system-and-audit` en rdm-discussion)
- Próxima refresh: manual cuando cambien items en §B/§C/§D
- **Update protocol:** tu PR toca este archivo si afecta lo que afirma (worker deploy, branch nueva activa, cron added, migration applied, anti-pattern nuevo).
- Promote-to-root: Alex copia este archivo → `rdm-bot/STATE.md` post-PR aprobación.
