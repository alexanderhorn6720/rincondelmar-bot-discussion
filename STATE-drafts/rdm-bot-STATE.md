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
- Last deploy dates (verify con `wrangler whoami` / dashboard): commit más reciente en `main` = 2026-05-19 (`0fc4720`, test admin-roles align with #129 priority)
- **Analytics / tracking (apps/web)**: 🔴 **NONE active in prod**. `<CFAnalytics />` + `<GA4 />` componentes existen en `BaseLayout.astro` pero ambos guarded por env var checks; `PUBLIC_CF_ANALYTICS_TOKEN` y `PUBLIC_GA4_ID` NO declarados en `wrangler.toml`. Live HTML confirmed via curl: 0 trackers emitiendo. CF HTTP-proxy logs sí pasivos. Ver thread/149.

## B. PRs OPEN (live `gh pr list`)

| #   | Título                                          | Branch                              | Author          | Why pending                  |
|-----|-------------------------------------------------|-------------------------------------|-----------------|------------------------------|
| 130 | Feat/a6 reglas adicionales deploy               | feat/a6-reglas-adicionales-deploy   | alexanderhorn6720 | review pendiente Alex      |
| 114 | feat(journey): D1-override editor for journey templates | feat/journey-templates-editor | alexanderhorn6720 | review pendiente Alex      |

## C. BRANCHES ACTIVAS LOCAL (no mergeadas a main)

- `feat/admin-nav-phase-2-4` — 2026-05-19 — shipped via #131 (admin nav Phase 2+4 + landing dashboard). Branch sin podar.
- `feat/beds24-proxy-calendar` — 2026-05-19 — current branch, shipped via #127 (proxy thread/134), tail commits 340a40e + 29e5a52
- `feat/a6-reglas-adicionales-deploy` — 2026-05-19 — PR #130 abierto
- `feat/role-based-nav-visibility` — 2026-05-19 — shipped #129, branch sin podar
- `feat/thread-141-house-rules-paper-trail` — 2026-05-19 — shipped #128, branch sin podar
- `feat/a5-airbnb-bulk-approve-writeback` — 2026-05-19 — A5 phase incomplete (67% per memory)
- `claude/compassionate-franklin-238c62` — 2026-05-18 — CC sandbox worktree, candidato a poda
- `claude/zen-payne-ac1349` — 2026-05-18 — CC sandbox worktree, candidato a poda
- `feat/journey-templates-editor` — 2026-05-18 — PR #114 abierto
- `feat/in-stay-post-stay-touchpoints`, `feat/manychat-subscriber-sync`, `fix/manychat-account-update-tag`, `fix/manychat-subscriber-id-routing`, `fix/resolve-route-disjoint`, `feat/beds24-dump-endpoint`, `feat/pre-stay-a4-admin-ui`, `feat/pre-stay-a3-scan-t14-t7-t1`, `feat/pre-stay-a2-scan-welcome`, `feat/pre-stay-a1.5-t14-touchpoint`, `feat/pre-stay-a1`, `fix/resync-chunked`, `debug/resync-error-samples`, `hotfix/mojibake-guest-names`, `feat/guests-resync-beds24` — todas 2026-05-18, shipped & sin podar (≥15 branches mergeadas con misma fecha)
- `chore/remove-reglas-pdf` — 2026-05-19 — WC created (empty), NEVER pushed code per WC role boundary. Candidato a poda by CC.
- `fix/reglas-pdf-emoji-sanitize` — 2026-05-19 — shipped via PR #132 + #133 (both merged, neither resolved bug). Branch sin podar.

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
- **PDF endpoint** `/reglas/{slug}/pdf` returns 500 in prod despite 2 sanitizer fix attempts (PR #132 + #133, both merged on 2026-05-19). Root cause deeper than emoji sanitization (likely pdf-lib + CF Workers runtime). Alex decision 2026-05-19: **remove PDF entirely**, defer hosted PDF to next spec. Browser native print (Ctrl+P) covers the use case. Pending: spec for CC to remove `/reglas/{slug}/pdf.ts` + 📄 PDF button + i18n keys.

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
- **WC NO implementa código en `rdm-bot` ni `rdm-platform`** (2026-05-19 Alex correction). WC = specs + threads + reviews + brain mode. CC reta + implementa. WC sí commits a `rdm-discussion` (threads, specs, ADRs, reviews).

## F. ÚLTIMA SEMANA SHIPPED (top 20 main, últimos 7d)

- `0fc4720` test(admin-roles): align with PR #129 priority order (#134)
- `bbb018f` fix(reglas-pdf): sanitize variation selectors + emoji ranges (#133) — duplicate of #132, did NOT resolve prod 500
- `a2716c0` fix(reglas-pdf): sanitize variation selectors + emoji ranges (#132) — did NOT resolve prod 500
- PR #131 admin nav Phase 2+4 + landing dashboard (thread/144) — merged 2026-05-19, +1825/-225, 12 files, 77/77 PR tests
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

Tema dominante: **pre-stay journey** (#112, #113, #117, varias branches `feat/pre-stay-*`), **karina-training admin** (#120-#125), **admin-nav role-based + Phase 2+4** (#129 + #131), **mobile inbox rescue** (#126), **thread/141 paper trail** (#128). Beds24 proxy (thread/134) shipped via #127. Reglas PDF (thread/141 §C) intentaron arreglarse 2x sin éxito (#132, #133); decisión Alex 2026-05-19: remove PDF endpoint entirely.

## G. OUTSTANDING DECISIONS (Alex pending)

Derivado de threads con type=question/spec sin result thread en últimas 2 semanas (cross-check con gap-analysis):
- A5 airbnb bulk-approve writeback — 67% completion per memory `project_a5_deploy_confirmed_session_gap`, falta session Better Auth en Chrome:9222 + per-cell deploy-confirmed flow.
- Browserbase AirBnB KPI scraper — thread/132 backlog item, decisión pendiente.
- A6 reglas_adicionales deploy — PR #130 esperando review.
- Journey templates editor (PR #114) — review pendiente desde 2026-05-18.
- Casa Chamán renovation timeline → cuándo unhide del Greeter (Q3 2026 placeholder).
- **PDF endpoint removal spec for CC** — Alex decided 2026-05-19 to remove `/reglas/{slug}/pdf` entirely after 2 failed fix attempts (#132, #133). Spec needed: delete `apps/web/src/pages/reglas/[slug]/pdf.ts` + remove 📄 button + i18n keys + sanitizer tests. WC drafts → CC executes. Out: scope creep, additional tests for removed code, biome --write.
- **F1/F2/F3 foundations + ADR-002** — thread/147 (WC-Impl review) posted 2026-05-19 with 1 🔴 blocker (cron host) + 3 🟡 concerns. Alex thread/148 vote pending on 7 items. See thread/145 + thread/147.
- **Analytics activation (thread/149)** — landing page has `<CFAnalytics />` + `<GA4 />` components shipped but NO env vars set in `wrangler.toml`. Live HTML confirmed 0 trackers emitting. Decision needed: activate (cookieless CF only / CF + GA4 / CF + GA4 + GSC) or leave dormant. Custom GA4 events already wired in code (`tour_loaded`, `booking_quote_view`, etc) — activation unlocks them with zero CC effort. A/B variant attributes (`data-ab-variant`, `data-ab-cta`) in live HTML have no readout without analytics. Search Console verification status unverifiable from outside (DNS TXT) — Alex confirm. Alex decision tomorrow.

## H. LAST UPDATED + UPDATE PROTOCOL

- Fecha generación: 2026-05-19 (revised 2026-05-19 late evening by WC-Impl to add: analytics finding to §A + §G, PDF removal pending to §D + §G, WC boundary anti-pattern to §E, PR #131 + PR #132/#133/#134 to §F, chore/remove-reglas-pdf + fix/reglas-pdf-emoji-sanitize branches to §C, last commit SHA updated to `0fc4720`)
- Por: CC vía DoIt thread/143 (branch `chore/state-system-and-audit` en rdm-discussion); 2026-05-19 PM revisions by WC-Impl direct-to-main per role boundary (rdm-discussion = WC territory).
- Próxima refresh: manual cuando cambien items en §B/§C/§D
- **Update protocol:** tu PR toca este archivo si afecta lo que afirma (worker deploy, branch nueva activa, cron added, migration applied, anti-pattern nuevo).
- Promote-to-root: Alex copia este archivo → `rdm-bot/STATE.md` post-PR aprobación.
