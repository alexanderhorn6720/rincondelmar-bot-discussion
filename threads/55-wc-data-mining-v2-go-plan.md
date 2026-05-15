# Thread 55 — WC: Data Mining v2 GO + plan ejecutable

**Date**: 2026-05-15
**Author**: Web Claude (WC)
**To**: CC-Bot (Greeter v5 session) `[@cc-bot]` + CC-Data (NUEVA sesión data mining) `[@cc-data]` + Alex `[@alex]`
**Re**: Alex aprobó Q-54-1-5. Data mining v2 arranca **paralelo** a Greeter v5
**Status**: GO — 2 sprints paralelos, 2 sesiones CC distintas, WC coordina

---

## 0. Decisiones Alex 2026-05-15

| # | Pregunta | Respuesta Alex |
|---|---|---|
| Q-54-1 | MVP o completo? | **Completo** (5 ejes) |
| Q-54-2 | Multimedia? | **NO** (sin audio + sin imágenes + sin PDFs) |
| Q-54-3 | Sequencing? | **Paralelo** (sesión CC distinta, coordinar con Greeter v5 CC) |
| Q-54-4 | Acceso infra? | **CC local en máquina Alex** (`C:\rdm-wa-api\`) |
| Q-54-5 | Privacy? | **De acuerdo** (local-only, sanitized outputs) |

**Cambio importante vs propuesta**: completo SIN multimedia = **4 ejes (A, B, C, E)**. Eje D queda fuera del sprint. Si necesitas inteligencia audio/imagen después, sprint separado con Whisper + Vision API.

**Costo revisado** (sin multimedia): **~$15-25 LLM total** (vs $100-175 con multimedia). ETA: **3 días WC + 0.5 día CC-data**.

---

## 1. Arquitectura de equipo — 2 sesiones CC distintas

```
                        ┌─────────────┐
                        │     Alex    │
                        │  (decisor)  │
                        └──────┬──────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
         ┌───────────┐                ┌───────────┐
         │    WC     │                │  CC-Bot   │
         │ (planner, │◀───coordina───▶│ (sesión 1:│
         │ data eng) │                │ Greeter v5│
         └─────┬─────┘                │ apps/web +│
               │                      │ worker-bot)│
               │ coordinates          └───────────┘
               │
               ▼
         ┌───────────┐
         │  CC-Data  │
         │ (sesión 2:│
         │ data mining│
         │ rdm_analysis/v2)
         └───────────┘
```

**Responsabilidades**:

| Rol | Foco | Repo/dir |
|---|---|---|
| **WC** | Planning, schemas, prompts, coordinate sessions, code review, deploys cloud | `rincondelmar-bot-discussion` (threads + cc-instructions) |
| **CC-Bot** | Greeter v5 implementation (4 PRs Fase 1, después Fase 2) | `apps/web` + `apps/worker-bot` |
| **CC-Data** | Data mining v2 pipelines (local), Whisper-less | `C:\rdm-wa-api\rdm_analysis\v2\` |
| **Alex** | Decisiones, validate operator playbook, ejecuta campañas marketing | Decision-maker only |

**Pueden coordinar sin colisión** porque:
- CC-Bot trabaja en cloud (Cloudflare apps)
- CC-Data trabaja en local (Windows máquina Alex con `msgstore.db`)
- WC coordina vía threads en discussion repo
- Touch points: solo D1 al final (CC-Data deploya seed tables, CC-Bot las consume)

---

## 2. Plan ejecutable — Data Mining v2 (4 ejes, sin multimedia)

### Day 1 — Eje A: Conversation Reconstruction

**Goal**: 9,424 hilos completos con metadata + outcome.

**Owner**: CC-Data (Python local) + WC (schema review)

**Tareas CC-Data**:

```python
# rdm_analysis/v2/stage_a_reconstruct.py

import pandas as pd
from datetime import timedelta

# 1. Load messages from extract/messages.csv
msgs = pd.read_csv('extract/messages.csv')
msgs['timestamp'] = pd.to_datetime(msgs['timestamp'])
msgs = msgs.sort_values(['phone', 'timestamp'])

# 2. Detect conversations (gap > 7 días = nueva conversación)
def detect_conversations(group):
    group['time_diff'] = group['timestamp'].diff()
    group['new_conv'] = (group['time_diff'] > timedelta(days=7)).cumsum()
    group['conversation_id'] = group['phone'].astype(str) + '_' + group['new_conv'].astype(str)
    return group

msgs = msgs.groupby('phone', group_keys=False).apply(detect_conversations)

# 3. Aggregate per conversation
convs = msgs.groupby('conversation_id').agg({
    'phone': 'first',
    'timestamp': ['min', 'max', 'count'],
    'msg_from_me': 'sum',
    # ... más metrics
})

# 4. Compute derived metrics
convs['duration_days'] = (convs['last_msg_at'] - convs['first_msg_at']).dt.days
convs['turns_count'] = compute_turns(msgs, convs)  # back-and-forth count
convs['median_response_time_minutes'] = compute_latencies(msgs)
convs['longest_silence_hours'] = compute_silences(msgs)

# 5. Join bookings
bookings = pd.read_csv('bookings_by_phone.csv')
convs = convs.merge(bookings, on='phone', how='left')
convs['resulted_in_booking'] = convs['first_arrival'].between(
    convs['first_msg_at'], 
    convs['last_msg_at'] + pd.Timedelta(days=90)
)
convs['days_msg_to_booking'] = (convs['first_arrival'] - convs['first_msg_at']).dt.days

# 6. Save
convs.to_csv('outputs/conversations_historical.csv', index=False)
```

**Output**: `conversations_historical.csv` con ~30 columnas, 9,424 rows estimados.

**Acceptance criteria**:
- [ ] 9,424 ± 10% conversations identificadas
- [ ] Outcome label (resulted_in_booking) populado en ≥95% rows
- [ ] Distribution de duration_days razonable (mediana <10 días, max <365)
- [ ] CSV + reportes sanity exportados

**WC tareas paralelas**: schema D1 design + migration draft.

### Day 2 — Eje B: Funnel Analysis + Eje E: Temporal

**Owner**: CC-Data + WC

**Eje B — Funnel** (`stage_b_funnel.py`):

Etapas detectables por keyword + LLM labeling (Haiku $2-3):

```python
funnel_stages = {
    'initial_inquiry': lambda c: c['msgs_total'] >= 1,
    'date_specified': lambda c: has_keyword(c, ['fecha', 'día', 'noche', '15 al 18']),
    'group_specified': lambda c: has_keyword(c, ['personas', 'pax', 'huéspedes', 'grupo']),
    'property_selected': lambda c: mentions_property(c),
    'price_quoted': lambda c: operator_sent_price(c),  # Haiku detect
    'price_accepted': lambda c: user_confirmed(c),     # Haiku detect
    'payment_data_requested': lambda c: has_keyword(c, ['CLABE', 'transferencia', 'tarjeta']),
    'booking_confirmed': lambda c: c['resulted_in_booking'] == True
}
```

Output: `funnel_stages.csv` con stage transitions + abandon hotspots.

**Eje E — Temporal** (`stage_e_temporal.py`):

```python
# Patterns por mes/temporada/día
temporal = msgs.assign(
    month=lambda x: x['timestamp'].dt.month,
    day_of_week=lambda x: x['timestamp'].dt.day_of_week,
    hour=lambda x: x['timestamp'].dt.hour
).groupby(['month', 'day_of_week']).agg({
    'conversation_id': 'nunique',
    'resulted_in_booking': 'mean'
})

# Operator response latency vs conversion
latency_analysis = compute_operator_latencies(msgs)
# Hipótesis test: <1h response → 3x conversion?
```

Output: `temporal_insights.md` + heatmaps PNG.

**Acceptance criteria día 2**:
- [ ] Funnel stages computed con conversion rate por stage
- [ ] Top-3 abandonment hotspots identificados
- [ ] Temporal heatmap (mes × día semana) generado
- [ ] Latency hypothesis test ejecutado con p-value real

### Day 3 — Eje C: Operator Playbook (highest value)

**Owner**: WC (Sonnet prompts) + CC-Data (sampling + execution)

**Pipeline**:

```python
# rdm_analysis/v2/stage_c_operator_playbook.py

import anthropic
client = anthropic.Anthropic()

# 1. For each (stage, outcome) combo, sample 50 conversations
samples = {
    ('price_quoted', 'converted'): sample_n(convs, n=50, filter='...'),
    ('price_quoted', 'abandoned'): sample_n(convs, n=50, filter='...'),
    ('price_objection', 'converted'): sample_n(convs, n=50, filter='...'),
    ('price_objection', 'abandoned'): sample_n(convs, n=50, filter='...'),
    # ... 8 combos total
}

# 2. For each combo, ask Sonnet for pattern extraction
for (stage, outcome), conv_sample in samples.items():
    prompt = build_pattern_extraction_prompt(stage, outcome, conv_sample)
    response = client.messages.create(
        model='claude-sonnet-4-5',
        max_tokens=2000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    patterns[stage][outcome] = response.content
```

**Sample prompt extraction** (WC writes this):

```
Eres analista de patrones de venta en hospitality. Aquí 50 conversaciones reales 
donde el operador de un vacation rental cotizó precio y el cliente {converted/abandoned}.

Tu tarea: extraer 5-10 patterns LINGÜÍSTICOS observables que correlacionan con 
{conversion/abandonment}. NO opines sobre estrategia — solo describe lo que ves 
en los datos.

Por cada pattern:
- Frecuencia observada (X de 50)
- Ejemplo textual (1 cita corta sin PII)
- Hipótesis de por qué correlaciona

Formato output: markdown con bullets.

Conversations (50 samples):
[paste samples]
```

**Output**: `operator_playbook.md` con 30-50 patterns documentados.

**Validation Alex**: WC entrega draft a Alex, Alex valida/corrige patterns. ~30 min Alex.

**Acceptance criteria día 3**:
- [ ] 8 (stage, outcome) combos analizados
- [ ] 30-50 patterns documentados
- [ ] Alex validó/corrigió en ≥80% de patterns
- [ ] Markdown final ready para inyectar en bot system prompt

---

## 3. Day 4 — Deploy a producción

**Owner**: WC coordina + CC-Data ejecuta + CC-Bot consume

### 3.1 D1 schema + import

WC escribe migrations, CC-Data las aplica:

```sql
-- migrations/001_data_mining_v2.sql

CREATE TABLE conversations_historical (
  -- 30 columnas per Eje A schema
);

CREATE TABLE funnel_stages (
  conversation_id TEXT,
  stage TEXT,
  reached_at TEXT,
  duration_in_stage_hours INTEGER,
  -- ...
);

CREATE TABLE customers_seed_v2 (
  -- mirror de contact_summary.csv enriquecido + Eje B insights
  -- 7,499 rows
);

CREATE INDEX idx_convs_phone ON conversations_historical(phone);
CREATE INDEX idx_convs_outcome ON conversations_historical(resulted_in_booking);
CREATE INDEX idx_funnel_stage ON funnel_stages(stage);
```

CC-Data ejecuta:
```bash
wrangler d1 execute rincon --file=migrations/001_data_mining_v2.sql
wrangler d1 execute rincon --command "INSERT INTO ..." # bulk import
```

### 3.2 R2 upload

```bash
wrangler r2 object put rdm-knowledge/operator_playbook.md \
  --file=outputs/operator_playbook.md \
  --content-type "text/markdown"

wrangler r2 object put rdm-knowledge/knowledge_findings_v2.md \
  --file=outputs/knowledge_findings_v2.md \
  --content-type "text/markdown"
```

### 3.3 Workers AI Vectorize

```bash
# Create index
wrangler vectorize create rdm-conversations \
  --dimensions=1024 --metric=cosine

# Embed + insert (CC-Data script)
python stage_vectorize.py  # uses Anthropic embeddings + Vectorize REST API
```

### 3.4 Airtable seed

CC-Data: upload `customers_seed_v2.csv` to Airtable Guests base via API.

**Acceptance criteria día 4**:
- [ ] D1 conversations_historical populated (9,424 rows)
- [ ] D1 funnel_stages populated
- [ ] D1 customers_seed_v2 populated (7,499 rows)
- [ ] R2 operator_playbook.md uploaded
- [ ] Workers AI Vectorize index populated
- [ ] Airtable guests base seeded
- [ ] CC-Bot recibe handoff doc: "aquí las nuevas tables D1, así se consultan"

---

## 4. Sprint paralelo — Greeter v5 (CC-Bot, ya en marcha)

**Status**: thread/53 publicado, CC-Bot ejecutando Fase 0 + Fase 1 (4 PRs).

| PR | Status | ETA |
|---|---|---|
| #27 deploy.yml fix | TODO | 30min |
| A1 anchors | TODO | 3-4h |
| A2 click tracking | TODO | 1h |
| A3 Telegram notif | TODO | 3h |

**Sin cambios al plan**. CC-Bot trabaja independiente.

**Sincronización**: cuando Data Mining v2 termine (día 4), WC publica `cc-instructions-bot/2026-05-XX-greeter-v5-with-v2-data.md` con:
- Cómo leer D1 conversations_historical para context lookup
- Cómo inyectar operator_playbook.md al system prompt
- Cómo query Vectorize para similar conversations
- Update del prompt v5 con findings de Eje B (funnel-driven)

Greeter v5 PR A6 (system prompt) se construye CON data v2 si llegó a tiempo. Si no, con data v1 y se upgrade después.

---

## 5. Coordinación entre CC-Bot y CC-Data

### 5.1 Touch point único: D1

CC-Data deploya tables nuevas a D1 (`rincon` database, `d81622d7-32e2-40a3-9609-80813c0e8a96`):
- `conversations_historical`
- `funnel_stages`  
- `customers_seed_v2`

CC-Bot las CONSUME en Greeter v5 PR A4 (intent catalog + context):
```typescript
// apps/worker-bot/src/lib/context-loader.ts
async function loadConversationContext(phone: string, env: Env) {
  const conv = await env.DB.prepare(
    'SELECT * FROM conversations_historical WHERE phone = ? ORDER BY last_msg_at DESC LIMIT 5'
  ).bind(phone).all();
  
  const customer = await env.DB.prepare(
    'SELECT category_final, booking_count, lifetime_value FROM customers_seed_v2 WHERE phone = ?'
  ).bind(phone).first();
  
  return { conversations: conv, customer };
}
```

### 5.2 Sin colisiones de archivos

- CC-Bot: solo edita `apps/`, `packages/` (cloud)
- CC-Data: solo edita `C:\rdm-wa-api\rdm_analysis\v2\` (local) — NO commit a repo

CC-Data NO tocará `apps/` ni `packages/` salvo si necesita ajustar el bot context loader. En ese caso: PR via WC review.

### 5.3 Reporting cadence

| Día | CC-Bot | CC-Data | WC |
|---|---|---|---|
| Día 1 | PR A2 + A3 paralelo | Eje A reconstruction | Schema D1 + thread/56 status |
| Día 2 | PR A1 anchors | Eje B funnel + Eje E temporal | Thread/57 mid-sprint review |
| Día 3 | PR A1 tests + merge | Eje C operator playbook | Thread/58 + Alex validation review |
| Día 4 | Fase 2 prep | Deploy D1 + R2 + Vectorize | Thread/59 close + handoff Greeter v5 |
| Día 5 | Fase 2 PR A4 (con data v2) | Stand-by | Thread/60 Fase 2 spec |

---

## 6. Riesgos identificados

### 6.1 CC-Data sesión local capacity

`msgstore.db` = 471 MB SQLite. `extract/messages.csv` = 96 MB. Procesarlo en pandas necesita ~4 GB RAM. Si máquina Alex es low-spec, CC-Data debe usar **chunked processing**.

**Mitigation**: CC-Data primero chequea recursos (`free -h` o equivalente Windows), si <8 GB RAM disponible usar Polars o duckdb en vez de pandas.

### 6.2 Outcome label ambiguity

Eje A define `resulted_in_booking` por "conversation termina dentro de 90 días de un booking del mismo phone". Pero:
- Cliente WhatsApp + reservó por AirBnB ≠ "converted by WA"
- Cliente WA pregunta, no convierte 6 meses, vuelve y reserva ≠ "converted by WA original conv"

**Mitigation**: outcome label tiene 3 categorías, NO booleano:
- `converted_direct` (booking dentro 30 días + canal direct)
- `converted_indirect` (booking dentro 90 días o booking AirBnB) 
- `not_converted` (sin booking 90 días)

WC review schema antes de día 1.

### 6.3 Operator playbook validation Alex bandwidth

Sonnet va a generar 30-50 patterns. Validar cada uno toma ~30 seg. Total Alex: ~25 min. Si Alex está saturado, mitigation:
- WC pre-valida con sentido común (descartar obvios falsos positivos)
- Alex valida solo top-15 patterns con mayor frecuencia

### 6.4 Vectorize cost

Embedding 9,424 conversaciones (avg ~5KB text cada una) = ~50 MB total. Anthropic embeddings API: ~$5-10.

Vectorize storage Cloudflare: incluído en plan Workers Paid.

Total ~$10 marginal.

### 6.5 Privacy leak en cloud

Si CC-Data sube CSVs crudos a D1, va a haber PII (texto crudo). **Política**:
- D1 conversations_historical: solo metadata + derived metrics, NO `full_text`
- R2 operator_playbook.md: examples SIN PII (sanitize antes de upload)
- Vectorize: vectores no son recuperables como texto, pero el index sí tiene `metadata` campos — solo guardar `conversation_id` + `outcome`, no texto

WC review final antes de deploy a cloud.

---

## 7. Resumen actividades + interacción WC-CC

### 7.1 Actividades por owner

**WC (3 días equivalente)**:
1. Schema design D1 (conversations_historical, funnel_stages, customers_seed_v2)
2. Prompt engineering para Eje C (operator playbook extraction)
3. Thread/56-60 coordination + status reports
4. Code review pipelines CC-Data
5. Validate output sanitization antes de deploy cloud
6. cc-instructions Greeter v5 Fase 2 con data v2

**CC-Bot (continuando Fase 0 + Fase 1, ~7.5h)**:
1. PR #27 deploy fix
2. PR A1 anchors
3. PR A2 click tracking
4. PR A3 Telegram notif
5. Standby para Fase 2 (consume data v2 outputs)

**CC-Data (3 días enfocados local)**:
1. Día 1: Eje A pipelines + outputs
2. Día 2: Eje B funnel + Eje E temporal
3. Día 3: Eje C operator playbook (Sonnet calls)
4. Día 4: Deploy D1 + R2 + Vectorize + Airtable

**Alex (~1h total)**:
1. Day 3: validate operator_playbook.md (~25 min)
2. Day 4: revisar Airtable seed populated (~15 min)
3. Day 5+: empezar campañas marketing con data nueva (1 día separado)

### 7.2 Interacción WC ↔ CC

**WC ↔ CC-Bot** (Greeter v5):
- Thread/53 = instrucciones actuales (ya entregadas)
- WC standby para Q-52-1-5 + Q-CC1-3 cuando CC-Bot pregunte
- WC review PRs si CC-Bot pide
- Thread/60+ después de Data Mining v2 terminado → instrucciones Fase 2

**WC ↔ CC-Data** (Data Mining v2):
- Thread/55 = este documento + cc-instructions-data/2026-05-15-data-mining-v2-execute.md (próximo file)
- WC entrega schemas D1 + prompts Sonnet día 1
- WC review pipelines día 2-3
- WC supervisa deploy día 4
- Touch point con CC-Bot: D1 schema final compartido

**CC-Bot ↔ CC-Data**: NO directa. Solo via D1 schemas (que WC coordina). Cero coordinación bilateral entre sesiones — todo pasa por WC + threads.

### 7.3 Decision points para Alex

Solo 2 momentos donde necesitamos Alex en el sprint:

1. **Día 3 (~25 min)**: validar operator_playbook.md generado por Sonnet
2. **Día 4 (~15 min)**: revisar Airtable seed populated

Plus Alex puede unfold campañas marketing día 5+ cuando todo esté listo, pero eso es trabajo independiente post-sprint.

---

## 8. Próximos files que WC va a publicar

1. `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` — instrucciones detalladas CC-Data
2. `threads/56-wc-data-v2-day1-status.md` — fin día 1 (Eje A done)
3. `threads/57-wc-data-v2-day2-status.md` — fin día 2 (B + E done)
4. `threads/58-wc-operator-playbook-validation.md` — Alex valida day 3
5. `threads/59-wc-data-v2-deploy-complete.md` — close day 4
6. `cc-instructions-bot/2026-05-XX-greeter-v5-fase-2-with-v2-data.md` — handoff a CC-Bot

---

**FIN thread/55**. CC-Bot continúa thread/53. WC arranca thread/56 con cc-instructions CC-Data mañana.

— Web Claude, 2026-05-15
