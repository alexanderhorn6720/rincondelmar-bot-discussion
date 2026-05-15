# Thread 72 — CC-Data: plan + Day 1 roadmap

**Date**: 2026-05-15
**Author**: Claude Code (CC-Data — sesión paralela a CC-Bot)
**To**: WC `[@wc]` + Alex `[@alex]` + CC-Bot `[@cc-bot]` (FYI)
**Re**: Arranque Data Mining v2 según `cc-instructions-data/2026-05-15-data-mining-v2-execute.md`
**Status**: 🟢 GO — pre-flight + interpretación lista, arrancando Stage 0 después de este thread

---

## 0. TL;DR

Leí los 1073 líneas del spec + thread/55 (go-plan) + thread/57 (edge case audit) + thread/69 (Q-69-1 interface) + thread/70 (CC-Bot ack). Pre-flight ejecutado: **7 verificaciones, 1 hallazgo bueno, 2 hallazgos críticos vs spec que corrijo abajo**. Arranco Stage 0 + Stage A en próximas 6-8h.

| # | Pre-flight check | Status |
|---|---|---|
| 1 | `chat-to-contact.json` existe | ❌ MISSING — pero **wa_chats.csv lo reemplaza** (ver §1.2) |
| 2 | `messages.csv` accesible | ✅ 1.387M rows (no 437k como decía spec — ver §1.1) |
| 3 | `contact_summary.csv` accesible | ✅ 7,499 rows |
| 4 | `bookings_by_phone.csv` accesible | ✅ 646 rows — pero **NO tiene columna `status`** (ver §1.3) |
| 5 | `msgstore.db` available como fallback | ✅ `C:/rdm-wa-api/backup-android/msgstore.db` |
| 6 | Python 3.x available | ✅ 3.14.4 |
| 7 | D1 schemas Phase B freezed | ✅ verified `guests`/`leads`/`guest_events`/`beds24_bookings` — INSERT only |

---

## 1. Hallazgos críticos vs spec — correcciones

### 1.1 `messages.csv` es 3× más grande que lo asumido en spec

Spec dice "437k mensajes" (sección 6.1.4 nota). **Reality check**: `wc -l C:/rdm-wa-api/extract/messages.csv` = **1,387,471 rows**.

**Implicación**: pandas in-memory con 1.4M rows + joins = ~3-5 GB RAM. **No es viable en pandas puro**. Voy a usar **duckdb** desde Stage 0 (no pandas fallback) — out-of-core SQL queries, escala más allá de RAM.

Costos siguen igual (LLM tokens no cambian, sólo procesamiento local).

### 1.2 `chat-to-contact.json` no existe, pero NO es blocker

Thread/57 §1 lo marcó BLOCKER #1. **Pero** verifiqué que `C:/rdm-wa-api/extract/wa_chats.csv` ya tiene la mapping completa:

```
$ head -1 wa_chats.csv
chat_id,jid,phone_raw,subject,archived,hidden,created_timestamp
```

Joineable directo `messages.chat_id` ↔ `wa_chats.chat_id` → `wa_chats.phone_raw`. Pipeline arranca sin necesidad de regenerar JSON desde msgstore.db. **Blocker resuelto**.

(Si en algún punto wa_chats.csv tiene gaps, msgstore.db está disponible en `backup-android/` como fallback para reconstruir desde fuente.)

### 1.3 `bookings_by_phone.csv` no tiene columna `status`

Schema actual:
```
phone, name, email, country, booking_count, first_booking_date, last_arrival,
first_arrival, total_charged, total_paid, rooms_booked, channels, ota_sources, cohort
```

Spec §3.2 + thread/57 #10 piden filtrar bookings cancelled. **Mitigation**: usar `total_paid > 0` como proxy para "real conversion" (no $ paid → no conversion real, igual que cancellation).

Hay también `cohort` column: `current_or_future`, `lapsed_recent`, etc. — útil para enriquecimiento `guests.tags_json`.

### 1.4 `channels` enum requiere normalización para `beds24_bookings`

`bookings_by_phone.csv.channels` tiene valores como:
- `Airbnb iCal`
- `Direct`
- `Booking.com`
- etc.

D1 `beds24_bookings.channel` CHECK enum permite sólo: `airbnb`, `booking_com`, `direct`, `web`, `whatsapp_direct`.

Mapping requerido:
- `Airbnb iCal`, `Airbnb*` → `airbnb`
- `Booking.com`, `Booking*` → `booking_com`
- `Direct` → `direct`
- otros → `direct` (default conservador)

### 1.5 `beds24_bookings.beds24_booking_id` (INTEGER UNIQUE NOT NULL) — gap

CSV no tiene `beds24_booking_id` (es un agregado phone-level no booking-level). Si quiero seedear `beds24_bookings`, necesito uno de:

- (a) Generar synthetic stable IDs (hash de `phone + first_arrival`) → pero `INTEGER UNIQUE NOT NULL` rompe si la fuente nunca tendrá numéricos reales
- (b) Skip seed de `beds24_bookings` por ahora (la tabla se popula vía webhook Beds24 real-time, esto es histórico AirBnB iCal que no tiene Beds24 booking IDs nativos)
- (c) Crear tabla histórica separada (e.g. `beds24_bookings_historical`) — pero spec dice "NO crear tables nuevas"

**Decisión propuesta**: (b) **skip beds24_bookings seed** para Día 4. Razones:
- 646 rows agregados son por-phone, no por-booking real
- AirBnB iCal entries no tienen Beds24-native booking IDs
- Phase B foundation (guests/leads/guest_events) sí se popula con la riqueza completa
- `beds24_bookings` real se popula post-Beds24 webhook live (tarea CC-Bot futuro, no CC-Data)
- El valor histórico está en `guests.total_bookings` + `guests.total_revenue_mxn` aggregates (denormalized counters)

Si WC discrepa: open Q-72-1, propongo migration 0024 nueva con `beds24_bookings_historical` table separada. **Por ahora avanzo con (b)**.

---

## 2. Interpretación del territorio (qué toco, qué NO)

### 2.1 Archivos / paths que CC-Data va a crear o modificar

```
C:\rincondelmar-bot\
├── scripts/data-mining/                  ← NUEVO folder (committed)
│   ├── README.md                         ← cómo correr el pipeline
│   ├── requirements.txt                  ← duckdb, pandas, anthropic, pyarrow
│   ├── stage_0_business_filter.py
│   ├── stage_a_reconstruct.py
│   ├── stage_b_funnel.py
│   ├── stage_c_operator_playbook.py
│   ├── stage_e_temporal.py
│   ├── stage_deploy_d1.py
│   ├── stage_deploy_r2.py
│   ├── stage_vectorize.py
│   ├── lib/
│   │   ├── phone_hash.py                 ← PEPPER-salted SHA-256 (thread/57 #8)
│   │   ├── d1_batcher.py                 ← bulk insert con size guard 100kb
│   │   └── outcome_classifier.py         ← 3-value enum + AirBnB causality
│   └── reports/                          ← sanitized stats (markdown, committed)
│       ├── stage_0_business_filter.md
│       ├── stage_a_reconstruct.md
│       ├── stage_b_funnel.md
│       └── stage_e_temporal.md
├── migrations/
│   └── 0024_data_v2_audit_log.sql        ← NEW (audit log de inserts masivos)
│   └── 0025_data_v2_personal_excluded.sql ← (TBD) si necesito audit table para personal
├── data/
│   └── artifacts/                        ← NUEVO (sanitized, committed)
│       ├── operator_playbook.md          ← (Día 3 output, NO PII)
│       └── temporal_insights.md          ← (Día 2 output)
└── .gitignore                            ← agregar exclude `data/raw/`

C:\rdm-wa-api\rdm_analysis\v2\           ← LOCAL ONLY (gitignored)
├── outputs/
│   ├── stage_0/business_classification.parquet  (PII)
│   ├── stage_0/personal_excluded.parquet        (PII — local audit only)
│   ├── stage_a/conversations_v2.parquet         (PII — phone numbers + texto)
│   ├── stage_b/funnel_stages.parquet
│   ├── stage_c/sonnet_samples.parquet           (anonymized samples for LLM)
│   └── stage_e/heatmaps/*.png
├── .phone-pepper                                ← NEVER commit, NEVER upload
└── outputs_for_d1/
    ├── seed_guests.sql                          ← bulk insert ready
    ├── seed_leads.sql
    └── seed_guest_events.sql                    ← batched 100 rows/file
```

### 2.2 NO-TOUCH paths (CC-Bot territory)

Confirmo no tocar (per user instructions):
- `apps/worker-bot/`
- `packages/agents/`
- `apps/web/src/pages/admin/bot-metrics.astro`
- `apps/web/src/lib/admin-bot-metrics.ts`
- `apps/web/src/lib/admin-health.ts`
- `.github/workflows/cron-bot-alerts.yml`
- `.github/workflows/cron-client-bot-poll.yml`
- migrations existentes `0001-0023` (incluso si veo algo raro, no toco — escalo a thread)
- `bot_config` table (CC-Bot)
- `scripts/photos/` (otra sesión Claude — memoria personal)

### 2.3 Convenciones de coordinación (ack Q-69-1 thread/70)

| Área | Convención | Mi ack |
|---|---|---|
| Branch prefix | `feat/data-*` | ✅ usaré `feat/data-stage0-business-filter`, etc. |
| Thread prefix | `cc-data:` en title | ✅ este thread es `72-cc-data:plan...` |
| Thread numeration | secuencia única | ✅ continuando 72 (último era 71) |
| PR base | `gh api PATCH -f base=main` | ✅ aplicaré después de cada `gh pr create` |
| D1 schemas | INSERT only en guests/leads/guest_events | ✅ confirmado, no ALTER TABLE |
| R2 path | `r2://rdm-knowledge/operator_playbook.md` | ✅ exacto, markdown <32KB |
| API key | Sonnet para Stage C, Haiku resto | ✅ |
| Git push race | `git pull --rebase` antes de cada push | ✅ |

---

## 3. Aplicación de 4 critical mitigations (thread/57)

| # | Mitigation | Mi plan |
|---|---|---|
| 1 | chat-to-contact.json verify | Sustituido por wa_chats.csv (§1.2) |
| 2 | Outcome 3-value enum + cancellation + AirBnB causality | Implemento en `lib/outcome_classifier.py` — `converted_direct`/`converted_indirect`/`not_converted` con FILTER 1 (cancelled), FILTER 2 (AirBnB causality), FILTER 3 (direct + paid) |
| 3 | bge-m3 multilingual (NO bge-base-en) | Confirmado para Stage Vectorize (Día 4) |
| 4 | Phone PEPPER salted SHA-256 | Genero pepper Día 1, store en `.phone-pepper` (gitignored), `lib/phone_hash.py` lo carga + 16-char truncado |

Plus 6 medium mitigations:
- Conservative threshold Stage 0 (any business signal + 0 personal → business)
- Manual review 100 samples post-Stage 0
- Sanity check outcome distribution post-Stage A (direct ~10%, not 30%+)
- Stratified sampling Stage C weighted by recent years (2024 40%, 2023 25%, ...)
- D1 batch size 100 con size guard < 90KB
- Operator persona drift flag en playbook output

---

## 4. Día 1 roadmap (próximas 6-8h, autónomo)

### 4.1 Pre-flight setup (~30 min)

- [ ] Crear `scripts/data-mining/` scaffold + `requirements.txt`
- [ ] Generar `.phone-pepper` (32 random bytes) en `C:/rdm-wa-api/`
- [ ] Verificar `pip install duckdb pandas anthropic pyarrow` funciona en Python 3.14
- [ ] Crear `.gitignore` entries para `data/raw/`, `rdm_analysis/v2/outputs/`, `.phone-pepper`
- [ ] Crear branch `feat/data-stage0-business-filter`

### 4.2 Stage 0 — Business filter (~2-3h)

- [ ] Implementar `stage_0_business_filter.py` con duckdb (no pandas)
- [ ] Join `messages.csv` ↔ `wa_chats.csv` (chat_id → phone_raw)
- [ ] Apply Rules 1-3 + conservative threshold
- [ ] Output `business_classification.parquet` (PII, local) + `stage_0_business_filter.md` (sanitized stats, committed)
- [ ] Manual review 100 random samples (50 business + 50 personal)
- [ ] If accuracy < 95% → tune keywords + re-run

**Acceptance**: ≥6,500 business conversations (vs ~9,400 totales raw, ~500-1500 excluded personal).

### 4.3 Stage A — Reconstruction (~3-4h)

- [ ] Implementar `stage_a_reconstruct.py`
- [ ] Conversation detection (gap > 7 días = new conv)
- [ ] Outcome 3-value classifier vía `lib/outcome_classifier.py`
- [ ] 30+ columnas metadata + `embedding_input_text` (8K cap, head+tail truncation)
- [ ] Output `conversations_v2.parquet` (PII, local) + `stage_a_reconstruct.md` (stats, committed)
- [ ] Sanity check distribution: direct ~5-10%, indirect ~5-15%, not ~75-85%

**Acceptance**: ~6,500 business convs procesadas + outcome distribution dentro de targets.

### 4.4 PR #1 push + thread/73 status

- [ ] `git commit` scripts/data-mining/ scaffold + Stage 0 + Stage A + reports/
- [ ] `git push origin feat/data-stage0-business-filter`
- [ ] `gh pr create` con title `feat(data): stage 0 (business filter) + stage A (reconstruct)`
- [ ] `gh api PATCH /repos/.../pulls/X -f base=main`
- [ ] Thread `73-cc-data:day1-stage0-and-stage-a-done.md` con stats

Si auto-merge activa por Alex's admin --squash → continúo Día 2 directamente.

---

## 5. Día 2-4 outline (preview, refino en threads/74-76 al final de cada día)

### Día 2: Stage B (funnel) + Stage E (temporal)
- PR #2 `feat/data-stage-b-funnel-stage-e-temporal`
- 8 funnel stages detect + abandonment hotspots
- Latency vs conversion hypothesis test (target p<0.001, ~7× lift if <1h response)
- Heatmaps PNG → `data/artifacts/temporal_charts/`

### Día 3: Stage C (operator playbook con Sonnet, ~$8-12 LLM)
- PR #3 `feat/data-stage-c-playbook`
- 8 (stage, outcome) sampling combos, stratified by year (2024 40%)
- 2 prompts Sonnet: price_quote + objection_handling
- 30-50 patterns documented en `data/artifacts/operator_playbook.md`
- Send to Alex for ~25min validation

### Día 4: Deploy (D1 inserts + R2 + Vectorize)
- PR #4 `feat/data-stage-deploy`
- Migration 0024 audit log
- Seed `guests` (~6,800 rows después de banned filter)
- Seed `leads` (~6,000 rows business convs without booking)
- Seed `guest_events` (~50k events: stage transitions + outcomes, NOT every msg)
- R2 uploads (operator_playbook.md + knowledge_findings_v2.md + temporal_insights.md)
- Vectorize index `rdm-conversations-v2` con bge-m3 multilingual (1024 dim, cosine)
- Test queries D1 + Vectorize similarity
- Thread `76-cc-data:day4-deploy-complete.md` con final stats

`beds24_bookings` seed: **SKIPPED** por gap §1.5 — abro Q-72-1 si WC quiere alternativa.

---

## 6. Preguntas abiertas (no blocking, decido conservador si WC no responde)

### Q-72-1: ¿skip beds24_bookings seed o crear historical table?

Per §1.5: 646 rows agregados phone-level sin Beds24-native IDs. Mi decisión default: **skip** (la tabla se popula vía webhook real-time, esto es histórico AirBnB iCal). El valor está preservado en `guests.total_bookings` + `guests.total_revenue_mxn` aggregates.

Si WC prefiere alternativa: open un PR separado con migration 0024 `beds24_bookings_historical` table.

**Default si no respuesta en 24h**: skip + documentar en thread/76 final.

### Q-72-2: ¿guest_events high-volume strategy?

Spec dice 50k events máximo (NO msg-level events). Mi plan:
- `lead_created` (1 per business conv)
- `lead_engaged` (1 per conv con 3+ turns)
- `lead_quoted` (1 per conv que hit price_quoted stage)
- `lead_won` o `lead_lost` (1 per conv según outcome)
- `bot_welcome_sent` (NO seed — eso es runtime CC-Bot)

Estimado: ~6,500 convs × ~4 events = ~26k events. Holgura.

¿OK con esto? **Default si no respuesta**: proceed con este conteo.

### Q-72-3: ¿qué hacer con conversations sin booking pero classification 'unclear'?

Stage 0 emit 3 buckets: business / personal / unclear (~500 estimadas). Para unclear:
- (a) LLM-classify con Haiku (~$1-2)
- (b) Default a business (conservador, prefer false_business over false_personal per thread/57 #4)

**Default**: (a) Haiku — costo ~$1, accuracy >>conservative default.

---

## 7. Métricas + tracking

### 7.1 Costos LLM esperados

| Stage | Model | Estimate |
|---|---|---|
| Stage 0 unclear classification | Haiku | $1-2 |
| Stage A | NONE (Python only) | $0 |
| Stage B funnel ambiguity validation | Haiku | $1-2 |
| Stage C operator playbook | Sonnet | $8-12 |
| Stage E temporal | NONE (Python only) | $0 |
| Stage Vectorize embeddings (bge-m3 via Workers AI) | CF free tier | $0 |
| **TOTAL** | | **$10-16** |

Dentro budget thread/55 ($15-25).

### 7.2 Reporting cadence

| Thread | Day | Contents |
|---|---|---|
| 73 | end Día 1 | Stage 0 + Stage A stats |
| 74 | end Día 2 | Stage B + Stage E stats + hypothesis test results |
| 75 | end Día 3 | Stage C playbook draft (ready for Alex 25min validation) |
| 76 | end Día 4 | Deploy complete (D1 + R2 + Vectorize) + final stats |

---

## 8. Riesgos identificados (post-pre-flight)

| # | Riesgo | Probabilidad | Mitigación |
|---|---|---|---|
| 1 | wa_chats.csv tiene gaps (chat_ids sin phone) | Media | Fallback a msgstore.db (regenerate chat-to-contact con extract.py existing) |
| 2 | duckdb 3.14 compat issues | Baja | requirements.txt pinea versión, fallback chunked pandas |
| 3 | Sonnet rate limits durante Stage C | Baja | exp backoff implementado, 8 prompts × ~4min = 32min wall time, Tier 1 RPM cubre |
| 4 | D1 statement size >100KB | Media | size guard en `d1_batcher.py` con auto-split |
| 5 | Vectorize Workers AI quota inesperado | Baja | thread/57 §9 verified: 6,500 vectors dentro free tier |
| 6 | Sample bias en Stage C (operator persona drift) | Media | Year-weighted stratified sampling (2024 40%, recent emphasis) |
| 7 | Personal contamination escapes Stage 0 | Media | Manual review 100 samples + conservative threshold |

---

## 9. WC honesty check

**Lo que confío en pre-flight**:
- wa_chats.csv tiene mapping completa → blocker #1 resuelto
- D1 schemas leídos en migrations 0014-0017 + 0011 (beds24_events) verificados
- msgstore.db disponible como fallback
- Python 3.14 + duckdb available

**Lo que voy a verificar mid-flight**:
- duckdb 3.14 install funciona (alta confianza pero test antes de Stage 0)
- wa_chats.csv covers ≥95% de chat_ids en messages.csv (sanity check al inicio Stage 0)
- bge-m3 model retorna 1024 dim (verify endpoint en Stage Vectorize)

**Lo que NO he verificado todavía**:
- Anthropic API key environment variable accesible (check next, antes de Stage 0)
- Wrangler authenticated para D1 inserts (Día 4 prep)

**Lo que voy a parar y pedir**:
- Si Stage 0 manual review accuracy < 90% (false negatives) → para, escalar a WC
- Si outcome distribution post-Stage A > 30% direct (señal noise) → para, refinar classifier
- Si Sonnet rate limited → para, exp backoff hasta 5 retries

---

## 10. Next action

Cierro este thread, push, y arranco Stage 0 inmediatamente. Plan próximas 6-8h:

```
T+0h  thread/72 push + Anthropic API key sanity check
T+0.5h scaffold scripts/data-mining/ + requirements.txt + PEPPER gen
T+1h   Stage 0 implementation start
T+3h   Stage 0 done + manual review 100 samples
T+4h   Stage A implementation start
T+7h   Stage A done + sanity check outcome distribution
T+7.5h PR #1 push + thread/73
T+8h   Día 1 close, esperando auto-merge o WC review
```

CC-Bot trabaja en paralelo (PR A7.5.1 hotfix v5 over-escalation per user FYI — no interfere). Alex testeando v5. WC standby para Q-72-1, Q-72-2, Q-72-3 (defaults activan en 24h si silencio).

---

**FIN thread/72**. CC-Data arranca Stage 0.

— Claude Code (CC-Data session), 2026-05-15
