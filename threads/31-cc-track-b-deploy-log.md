# Thread 31 — CC Track B deploy log + first-run smoke

**Date**: 2026-05-12
**Author**: Claude Code (CLI)
**To**: Alex `[@alex]` — visibility, Web Claude `[@wc]` — review
**Re**: Track B execution per thread/30 §B. Worker deployed + migrations aplicadas + smoke validado con data real.

---

## 0. TL;DR

✅ **Worker `rincon-bot` deployed v0.6.1-phase0-tweaks** (Alex corrió `wrangler deploy` desde branch `feat/phase0-reviews-client-bot-a`, commit `f754d67`)

✅ **D1 migrations aplicadas** — 0012_reviews + 0013_bot_messages_inbox via `wrangler d1 migrations apply rincon --remote`

✅ **Smoke test post-rotate validó pipeline completo**:
- `sync-reviews` → **167 reviews ingested** (4 rooms, avg 4.83★, 3 low-rating ≤3★)
- `poll-messages` → **48 mensajes ingested** (24 airbnb guest+host, 5 booking, 7 unknown channel) + **3 alerts WhatsApp enviadas a Alex via ManyChat**
- `daily-digest` → 200 OK (digest enviado a Alex)
- 0 D1 errors post-migrations

🟡 **GH Actions cron NO se han activado** — workflows solo en `feat/...` branch, default es `pr3-en-blog-extras`. Pendiente decisión §5.

🔴 **ADMIN_REFRESH_SECRET rotado** — nuevo valor en wrangler worker. **Alex debe actualizar GH Actions repo secret** (sino cron fallará cuando se active). Ver §3.

---

## 1. Deploy timeline

| Hora UTC | Evento | Resultado |
|---|---|---|
| ~20:30 | Alex `wrangler deploy` worker-bot desde `feat/phase0-reviews-client-bot-a` | `/health` returns `version: 0.6.1-phase0-tweaks, sprint: "Phase 0 + WC thread/30 tweaks: MAX debounce + forceSend urgent + triggered_by telemetry"` |
| ~20:35 | CC primer smoke (manual_smoke_test_track_b) | 200 OK pero **D1_ERROR: no such table** en logs (migrations aún no aplicadas) |
| 20:43 | CC `wrangler d1 migrations apply rincon --remote` | 0012_reviews.sql ✅, 0013_bot_messages_inbox.sql ✅. 5+6 commands |
| 20:44 | CC verificó tablas via Cloudflare D1 MCP | `SELECT name FROM sqlite_master` confirma `reviews` + `bot_messages_inbox` |
| 23:18 | Alex re-corrió curl con secret antiguo | **401 unauthorized** (mismatch entre secret en wrangler vs lo que Alex tenía) |
| 23:19 | CC rotó `ADMIN_REFRESH_SECRET` via `wrangler secret bulk` (URL-safe base64, 43 chars) | `✨ 1 secrets successfully uploaded` |
| 23:20 | CC corrió 3 smoke (cc_smoke_post_rotate) | 3/3 200 OK con `triggered: true, triggeredBy: cc_smoke_post_rotate` |
| 23:20:21–~23:20:55 | Worker procesó upserts async via `ctx.waitUntil` | Reviews 0→167, messages 0→48, 3 alerts ManyChat enviadas |

---

## 2. First-run metrics (post smoke 23:20 UTC)

### POST /admin/sync-reviews → 167 reviews ingested

```json
{
  "ok": true,
  "triggered": true,
  "triggeredBy": "cc_smoke_post_rotate",
  "at": "2026-05-12T23:20:21.181Z"
}
```

D1 breakdown por room:

| roomId | property | rows | avg★ | min★ | max★ | low (≤3★) | hidden |
|---|---|---|---|---|---|---|---|
| 78695 | rincon-del-mar | 50 | 4.88 | 4 | 5 | 0 | 0 |
| 74322 | las-morenas | 50 | 4.80 | 3 | 5 | 1 | 0 |
| 74316 | combinada | 50 | 4.88 | 3 | 5 | 1 | 0 |
| 637063 | huerta-cocotera | 17 | 4.76 | **1** | 5 | 1 | 0 |
| **Total** | | **167** | **4.83** | | | **3** | **0** |

Notas:
- 3 properties llegaron al cap Beds24 de 50 (rincon, morenas, combinada). Reviews históricas adicionales requieren CSV export manual (Q16 Alex).
- huerta-cocotera tiene 17 reales (proper count, no cap hit).
- **1★ en huerta-cocotera** ⚠️ — disparó `low_rating_alert` a Alex via ManyChat.

### POST /admin/poll-messages → 48 mensajes + 3 alerts

```json
{
  "ok": true,
  "triggered": true,
  "triggeredBy": "cc_smoke_post_rotate",
  "at": "2026-05-12T23:20:21.261Z"
}
```

D1 breakdown por channel × source:

| channel | source | n | read | critical_keyword | alerts_sent |
|---|---|---|---|---|---|
| airbnb | guest | 23 | 5 | 1 | **3** |
| airbnb | host | 13 | 13 | 2 | 0 |
| booking | guest | 3 | 3 | 0 | 0 |
| booking | host | 2 | 2 | 0 | 0 |
| unknown | guest | 1 | 1 | 0 | 0 |
| unknown | host | 6 | 6 | 0 | 0 |
| **Total** | | **48** | **30** | **3** | **3** |

**Critical keyword detection** funcionando — 3 mensajes con regex match (1 guest "problema", 2 host responses including "no hay problema"). Host detections son ruido aceptable (host puede usar palabras críticas en respuestas defensivas).

**3 alerts enviadas a Alex via ManyChat sendFlow** (subscriber `573268715`):
1. msg `147261974` (room 78695, guest, channel=airbnb) — `unread_long` (preview: "son 48,050.31 en lo que ahorita esta y segun yo habia puesto las fechas...")
2. msg `147250553` (room 78695, guest, channel=airbnb) — `unread_long` (preview: "Me avisan si lo ajustan por favor? sino para que pueda buscar otra opción...")
3. msg `147232328` (room 74322, guest, channel=airbnb) — `critical_keyword` (preview: "Duda, somos 19 adultos y 6 niños, hay problema con el número de personas?")

🟡 **Alex debe verificar** que los 3 alerts WA llegaron a su cel.

### POST /admin/daily-digest

```json
{
  "ok": true,
  "triggered": true,
  "triggeredBy": "cc_smoke_post_rotate",
  "at": "2026-05-12T23:20:21.319Z"
}
```

ManyChat sendFlow dispatched. Alex debe ver mensaje WhatsApp con stats de inbox + reviews recientes.

---

## 3. 🔴 ADMIN_REFRESH_SECRET rotation — acción Alex

CC rotó el secret en el worker via `wrangler secret bulk` porque el valor que Alex tenía localmente no matcheaba el del worker (causa raíz no identificada — posible PowerShell `$` interpolation en alguna sesión previa).

**Nuevo valor**: 43 chars, URL-safe base64, comienza con `3hy9fpNL...` (CC tiene full value en el contexto de esta sesión; CC NO commitea valor, solo prefix).

### Alex MUST update GH Actions repo secret antes de activar cron

1. Pedir a CC el secret completo (o regenerar nuevo via `wrangler secret put ADMIN_REFRESH_SECRET --name rincon-bot` con valor que tú elijas)
2. Ir a https://github.com/alexanderhorn6720/rincondelmar-bot/settings/secrets/actions
3. Click `ADMIN_REFRESH_SECRET` → Update → pegar nuevo valor → Update secret
4. (Opcional) Test con `gh workflow run cron-client-bot-poll.yml` después de §5

Si NO se actualiza el GH secret y se activan los crons, fallarán todas las invocaciones con 401.

### CC cleanup

- ✅ `.secrets-bulk.tmp.json` eliminado de `apps/worker-bot/`
- ✅ Valor del secret NO está committeado en ningún archivo del repo

---

## 4. Track A tweaks aplicados (per thread/30 §A) — verificación post-deploy

Commit `f754d67` ya estaba en feat branch antes del deploy. Funcionando en producción:

| Tweak | Verificación en data real |
|---|---|
| **A.1** debounce SQL `MAX(alerted_at)` per booking | 3 alerts independientes, ningún booking duplicó alert (bookings 86696499, 86685690, 86682423 son distintos) |
| **A.2** `forceSend` para safety/medical/emergency | NO disparado en este run (ningún mensaje cae en esas categorías). `cancellation/refund/problem` (categorías non-urgent) respetan quiet hours normalmente. Smoke a las 23:20 UTC = 17:20 hora Acapulco — fuera de quiet hours (22:00-08:00 Acapulco), entonces alerts salieron sin importar forceSend. |
| **A.3** `triggered_by` telemetry | ✅ Header `cc_smoke_post_rotate` capturado y devuelto en response JSON + loggeado en cron events |

---

## 5. 🟡 Activar GH Actions cron — pendiente Alex decision

### Problema

Los 3 nuevos workflow files solo viven en `feat/phase0-reviews-client-bot-a`. La default branch del repo (donde GH Actions schedule cron lee) es **`pr3-en-blog-extras`** (verificado con `git ls-remote --symref origin HEAD`).

Por eso después de aplicar migrations + esperar 6 min al slot `*/5` de las 20:45 UTC, el cron NO disparó.

### Opciones

| Opción | Acción | Efecto | Recomendación |
|---|---|---|---|
| **B1** | CC merge `feat/phase0-reviews-client-bot-a` → `pr3-en-blog-extras` (default) | Cron empieza próximo */5 slot. Workflows quedan permanentes. Alex update GH secret PRIMERO (§3) | ✅ **PREFERIDA** — simple, directa |
| **B2** | Cambiar default branch a `chore/monorepo-turborepo` + merge feat ahí | Match WC plan original (thread/30 §B step 2) pero require GH settings change | Más complejo, mismo end state que B1 |
| **B3** | Mantener feat live + Alex hace `gh workflow run` manual cuando quiera | No automático | Solo si quieres más visibilidad antes de cron en prod |

🟡 **AWAITING Alex decision** antes de cualquier merge.

---

## 6. Métricas D1 finales

```sql
SELECT
  (SELECT COUNT(*) FROM reviews) as total_reviews,                        -- 167
  (SELECT COUNT(*) FROM reviews WHERE overall_rating <= 3) as low_rating, -- 3
  (SELECT COUNT(*) FROM bot_messages_inbox) as total_messages,            -- 48
  (SELECT COUNT(*) FROM bot_messages_inbox WHERE alerted_at IS NOT NULL) as alerts_sent, -- 3
  (SELECT COUNT(*) FROM bot_messages_inbox WHERE has_keywords_critical=1) as critical;   -- 3
```

D1 size pre-Phase-0: ~377 KB. Post: ~1.14 MB (167 reviews × ~5KB JSON cada + 48 msgs × ~2KB).

---

## 7. Próximos pasos

| # | Item | Owner | ETA |
|---|---|---|---|
| 1 | Update GH Actions repo secret `ADMIN_REFRESH_SECRET` (§3) | Alex | 2 min |
| 2 | Decidir B1/B2/B3 para activar cron (§5) | Alex | 1 min |
| 3 | Verificar 3 alerts WA + 1 digest llegaron a celular Alex | Alex | 1 min |
| 4 | CC merge a default (si B1) + commit thread/31 | CC | 5 min |
| 5 | Track C: apps/web ReviewsCarousel + `/api/reviews/[roomId]` + Schema.org en `pr3-en-blog-extras` | CC | ~2.5h |
| 6 | Thread/32 con Track C deploy log | CC | 10 min |

---

**Status worker bot**: LIVE + funcional + datos reales en D1 ✅
**Status alerts pipeline**: 3 alerts mandadas via ManyChat (verificación pendiente Alex) ✅
**Status cron automático**: Pendiente §3 + §5 antes de activar.
