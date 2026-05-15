# Thread 54 — WC: Data mining v2 estrategia (re-do bien hecho)

**Date**: 2026-05-15
**Author**: Web Claude (WC)
**To**: CC `[@cc]` + Alex `[@alex]`
**Re**: HANDOFF_RDMBOT.md analysis + Alex feedback ("dive deeper, do it better")
**Status**: Proposal — sprint independiente del Greeter v5, paralelizable

---

## 0. TL;DR

**Diagnóstico del primer pipeline**: clustering ingenuo (HDBSCAN sobre dedupe) extrajo el **qué se pregunta** pero perdió:
- **El cómo evoluciona** (mismo cliente → 5 mensajes → booking vs abandono)
- **Los signos de venta** (qué keywords/patrones predicen conversión)
- **Las decisiones que pesan** (cuándo el operador escala precio vs concede descuento)
- **Las anomalías** (clientes problemáticos, fraudes, no-shows)
- **El timing** (cuántos turnos toma cada decisión, qué se demora)
- **El multimodal** (audios/imágenes/PDFs descartados completamente)

**Propuesta**: pipeline v2 con **5 ejes de análisis** + **mejor herramienta de extracción** + **output directo a sistemas en producción** (D1 + Airtable + Worker AI).

**Diferencia clave vs v1**: v1 produjo CSVs estáticos para humanos. v2 produce **objetos vivos**: vector embeddings indexed para retrieval, conversation graphs para timing analysis, signed permissions para campaign launch, weighted facts para bot KB.

**ETA**: ~3 días enfocados (no sprint largo). Costo Anthropic: ~$15-25 USD total.

---

## 1. Diagnóstico v1 — qué se hizo mal

### 1.1 Errores de diseño

| # | Error v1 | Consecuencia |
|---|---|---|
| 1 | **Dedupear antes de clusterizar** | Perdiste señal de "esta pregunta se repite 112 veces" como variable separada del "esta es la pregunta cluster" |
| 2 | **Solo texto, no metadata** | Perdiste timestamps, dirección (in/out), latencia respuesta, días entre msgs |
| 3 | **Embeddings only para FAQs** | No vectorizaste TODO el corpus — solo 28k preguntas dedupeadas vs 437k mensajes completos |
| 4 | **Haiku synth tone-deaf al negocio** | "suggested_faq_answer_seed" sin contexto operacional real (precios, políticas) |
| 5 | **Categorías genéricas** | `pricing|availability|amenities|...` — funciona para FAQ wiki pero no para decisiones de negocio |
| 6 | **Conversations no reconstruídas** | Tienes 437k mensajes individuales pero NO 9,424 hilos completos con outcome (booking/no-booking) |
| 7 | **Multimedia descartado** | 11 años de audios/imágenes/PDFs = treasure trove. Cero análisis |
| 8 | **No supervised labels** | Sin verdad-fundamental (qué msgs llevaron a booking), todo es unsupervised guessing |
| 9 | **Output a CSV, no a producción** | Karina/Alex no pueden actuar sobre faq_clusters.csv. Debería ir directo a D1 + Bot KB + CRM |
| 10 | **No analysis temporal** | Patrones por mes/temporada/año cero examinados — los más importantes para pricing/staffing |

### 1.2 Lo que sí funcionó

| ✅ | Por qué mantener |
|---|---|
| Schema `contact_summary.csv` con cohort + category_final | Bien diseñado, mantener as-is + enriquecer |
| Beds24 join por phone | Critical key, funciona |
| Haiku reclassify de unclassified | Costoso pero accuracy alta |
| `bookings_by_phone.csv` join | Es ground truth, mantener |
| Confirmación humana de staff | Patrón correcto, repetir |

---

## 2. Pipeline v2 — 5 ejes de análisis

Cada eje produce **output deployable a producción** (D1 row, Worker AI vector, Airtable record, bot KB chunk), NO un CSV para humanos.

### Eje A — **Conversation reconstruction** (la base de todo)

**Goal**: reconstruir 9,424 hilos completos con metadata + outcome.

**Schema target** (a tabla D1 `conversations_historical`):
```sql
CREATE TABLE conversations_historical (
  id INTEGER PRIMARY KEY,
  phone TEXT NOT NULL,
  chat_jid TEXT,
  first_msg_at TEXT,
  last_msg_at TEXT,
  duration_days INTEGER,        -- last - first
  msgs_total INTEGER,
  msgs_from_them INTEGER,
  msgs_from_me INTEGER,
  turns_count INTEGER,          -- back-and-forth count (excludes consecutive same-sender)
  median_response_time_minutes INTEGER,  -- our typical latency
  longest_silence_hours INTEGER,         -- biggest gap mid-conversation
  
  -- Outcome (joined con bookings)
  resulted_in_booking BOOLEAN,
  booking_id INTEGER,
  days_msg_to_booking INTEGER,  -- conversion latency
  booking_value_mxn REAL,
  
  -- Intent flow (derived)
  initial_intent TEXT,           -- first user msg intent
  intent_changes_count INTEGER,
  final_intent TEXT,
  abandoned_at_stage TEXT,       -- e.g. "after_price_quote", "no_response_after_dates"
  
  -- Quality signals
  operator_quoted_price BOOLEAN,
  operator_sent_link BOOLEAN,
  operator_offered_discount BOOLEAN,
  user_objected_to_price BOOLEAN,
  user_negotiated BOOLEAN,
  user_requested_human_call BOOLEAN,
  
  -- Multimedia
  images_sent INTEGER,
  audios_sent INTEGER,
  pdfs_sent INTEGER,
  
  -- Vector ref
  embedding_id TEXT,             -- key into Workers AI Vectorize
  
  full_text_compressed BLOB      -- gzip'd full conversation for retrieval
);
```

**Por qué es la base**: TODO lo demás depends de tener hilos completos. v1 nunca reconstruyó hilos.

**Implementación**:
- Pull todos los mensajes ordenados por `phone + timestamp` → bucket por gaps >7 días (= nueva conversación) o single thread si <7 días
- Para cada hilo, compute metrics + join bookings
- Outcome label: did this thread lead to a booking within 90 days?

**Costo**: cero LLM, todo Python/SQL. 1 día WC.

---

### Eje B — **Conversion funnel analysis** (DATA-DRIVEN, no opinión)

**Goal**: identificar las etapas del funnel y qué hace cada cliente exitoso vs fallido.

**Output esperado**:

```
Funnel (9,424 conversations):
  Stage 1 — Initial inquiry (100% = 9,424)
  Stage 2 — Date specified (43% = ~4,000)         → 57% abandon at "qué fechas"
  Stage 3 — Group size confirmed (28% = ~2,700)   → drop 15% más
  Stage 4 — Property selected (22% = ~2,000)
  Stage 5 — Price quoted by operator (18% = ~1,700)  → 4% abandon antes
  Stage 6 — Price accepted (12% = ~1,100)         → 6% abandon at price
  Stage 7 — Payment data requested (8% = ~750)
  Stage 8 — Booking confirmed (646 = ~7%)         → final conversion
```

**Análisis derivado**:
- **¿Qué caracteriza Stage 5→6 success vs Stage 5→abandon?** (la decisión más cara — operador trabajó hasta cotizar)
  - Hipótesis: timing (cotizar <1h convierte mejor que >24h)
  - Hipótesis: nivel de detalle (cotización con desglose vs precio único)
  - Hipótesis: ofrecer alternativas (3 fechas vs 1 fecha)

- **¿En qué intent abandonan más?** Top abandon stages debe atacar el bot con más cuidado

**Por qué importa**: tu Greeter v5 está optimizando para "respond well to FAQs". El funnel data dice **dónde se pierde dinero realmente**. Cambia el system prompt focus de "responder" a "**avanzar el funnel**".

**Costo**: cero LLM. Pure Python. 1 día WC.

---

### Eje C — **Operator playbook extraction** (qué hace bien tu mejor versión)

**Goal**: extraer los patrones de Alex/Karina **cuando convierten** vs **cuando NO convierten**, NO solo qué preguntan los clientes.

**Esto v1 NO hizo**. v1 solo analizó preguntas de clientes. La mitad del corpus es **operator messages** = el playbook.

**Metodología**:
- Filtrar `msgs_from_me` (las 200k+ outbound)
- Cluster por intent del operator: `price_quote`, `availability_offer`, `objection_handle`, `escalate_to_call`, `send_link`, `chase_payment`, `confirm_booking`, etc.
- Para cada cluster, SAMPLE 50 ejemplos y use Sonnet (NO Haiku — necesitas razonamiento) para extraer:
  - "Cuáles son los patrones lingüísticos que correlacionan con CONVERSION?"
  - "¿Cuándo el operador concede descuento vs sostiene precio?"
  - "¿Cuándo el operador hace handoff a llamada telefónica?"
  - "¿Cómo el operador responde a objeciones de precio que llevan a booking?"

**Output**:
```markdown
# OPERATOR_PLAYBOOK.md (autogenerated, validated by Alex)

## Pattern: Price quote that converts
- Always mentions "está incluido el chef" before price (78% of convert)
- Always offers 2 options (entre semana vs FDS) (63%)
- Includes "te ayudamos con el transporte" (52%)
- Never apologizes for price (95% NO apology in convert vs 31% apology in abandon)

## Pattern: Handling "es muy caro"
- Best response: mention what's included that competition charges extra (53% rescue)
- Worst response: offer immediate discount (12% rescue — looks desperate)
- Medium: ask "para cuántas personas?" to recalibrate per-person cost (38% rescue)

## Pattern: Escalation to phone
- 87% of phone-escalation cases happen WHEN: group >20 OR custom event OR repeat guest
- Operator uses phrase: "Mejor te llamo para platicar?" — 64% accept the call
```

**Por qué crítico**: ESTO ES TU GROUND TRUTH para el system prompt del Greeter v5. NO opinion-based — data-derived del operador que ya convirtió.

**Costo**: ~$5 Sonnet (50 examples × 8 clusters). 1 día WC.

---

### Eje D — **Multimedia mining** (cero hecho en v1)

11 años de audios/imágenes/PDFs descartados es una pérdida brutal. Plan:

#### D.1 — Audio messages (WhatsApp voice notes)

**Volume estimado**: ~30-50k voice notes (típico ratio audio/text en MX = 5-10%).

**Approach**:
- Pull audios desde `/sdcard/Android/media/com.whatsapp.w4b/...`
- Transcribe con **Whisper API** (~$0.006/min, ~10s avg = ~$50-100 total)
- Re-feed transcripts al Eje A (conversation reconstruction) + Eje C (playbook)

**Insights únicos que salen de audio**:
- **Tono emocional**: clientes que mandan audios son más cálidos = más likely to convert
- **Operator audios** = el operador con voz natural. ¿Qué dice diferente vs texto?
- **Specific requests** que no se escriben (audios para eventos custom)
- **Frustrations** = quejas explícitas que en texto se suavizan

#### D.2 — Imágenes

**Volume**: probablemente 50-100k imágenes (fotos de la casa enviadas a clientes, screenshots de comprobantes, IDs, etc.)

**Approach**:
- Pull imágenes
- Run **Claude vision** (Sonnet) sobre sample 2-3k → categorize:
  - Photos sent BY operator (marketing material) → ¿qué casas se promueven más?
  - Photos sent BY client (screenshots, IDs, comprobantes) → patterns of trust signals
  - Screenshots de Beds24 / OTA listings (price benchmarking)
- Insight key: **¿qué fotos convierten más?** (correlacionar imagen → booking outcome)

**Costo**: ~$30-50 (vision API es caro pero sample limitado).

#### D.3 — PDFs (contratos, comprobantes, IDs)

**Volume**: probablemente 5-10k PDFs (comprobantes MP, contratos firmados, IDs huéspedes).

**Approach**:
- OCR + entity extraction
- Pull: nombres oficiales, IDs gobierno (FOR PRIVACY — local only), bank refs, fechas
- **Verify**: ¿los nombres en `contact_summary.csv` match con IDs reales? (importante para Guest 360 calidad)

**Costo**: ~$10 (Sonnet OCR sample). PRIVACY: NO subir IDs al cloud, sólo metadata.

---

### Eje E — **Temporal + seasonal analytics** (cero hecho)

**Goal**: timing es CRÍTICO en hospitality.

**Análisis a producir**:

#### E.1 — Booking patterns por temporada

```
Por mes:
  Enero: 89 bookings, lead time avg 23 días, conversion 8.2%
  Febrero: 95 bookings, lead time 19 días, conversion 9.1%
  ...
  Diciembre: 124 bookings, lead time 67 días, conversion 12%  ← Navidad gana
```

#### E.2 — Day-of-week patterns

¿Qué día funciona mejor por canal?
- Lunes 9 AM: leads cold AirBnB (turistas pensando weekend)
- Viernes 6 PM: leads urgentes para weekend (alta conversion)

#### E.3 — Operator response latency vs conversion

**Hipótesis HONESTA**: si Karina responde en <1h, conversion es 3x mejor que >24h.
**Verificación**: data lo dirá. Esto justifica (o NO) la inversión en Telegram notif real (decisión D5).

#### E.4 — Booking advance time patterns

Distribution: ¿cuánto avance reservan?
- 70%: <7 días anticipación (impulsive)
- 20%: 7-30 días
- 10%: >30 días (planners, eventos)

→ Implication para bot: 70% del trabajo es responder fast para weekenders impulsivos. Greeter debe ser AGRESIVAMENTE rápido.

**Costo**: cero LLM. 0.5 día WC.

---

## 3. Output deployable — no más CSVs estancos

v1 entregó `outputs/*.csv` que están en local de Alex. v2 entrega a producción:

### 3.1 — `D1 conversations_historical` (Eje A output)

Bot puede query: "this phone tuvo X conversaciones, last_outcome=Y, abandoned_at_stage=Z" → contexto inteligente.

### 3.2 — `D1 funnel_stages` (Eje B output)

Materialized view + dashboard `/admin/funnel-analytics`. Karina/Alex ven dónde se pierde dinero por mes.

### 3.3 — `R2 operator_playbook.md` (Eje C output)

Static file inyectado al system prompt Greeter v5 + Booker. **System prompt source-of-truth**.

### 3.4 — `Workers AI Vectorize` (Eje A+B embedded)

Vector index de **conversations completas** (no preguntas dedupeadas). Bot puede:
- Receive incoming msg → embed → similarity search → "Esta conversación se parece a otras 47 que tuvieron outcome Y"
- Few-shot prompt: "Aquí 3 conversaciones similares que convirtieron, replica el patrón"

**Esto v1 NO permitió** porque solo embedded preguntas, no contexto completo.

### 3.5 — `Airtable customers` (CRM seed)

7,499 contacts + metadata enriquecida (audio transcript summaries, image patterns, etc.) directo a Airtable. Karina abre `/admin/guests` y ve todo.

### 3.6 — `R2 segments_with_signed_permissions.csv` (Eje C output)

Importante: para campañas marketing, necesitas **permission**. Pipeline detecta:
- Clientes que EXPLÍCITAMENTE OPT-IN ("avísame promociones") → broadcast-safe
- Clientes que pidieron NO contactar → exclude
- Resto → opt-in template required ANTES de campaña

→ LFPDPPP compliance automático.

---

## 4. Workflow técnico — donde corre cada cosa

```
┌─────────────────────────────────────────────────────────────────┐
│ LOCAL (C:\rdm-wa-api) - PII bruta, NO cloud                    │
│ ├─ msgstore.db (471 MB)                                         │
│ ├─ /sdcard/Android/media/.../ (audios, imágenes, PDFs)         │
│ └─ Python pipelines v2 (stage_a-h en `rdm_analysis/v2/`)        │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Pipeline v2 transforms + sanitizes
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLOUD (Cloudflare) - sanitized, redacted, queryable             │
│                                                                  │
│ D1 `rincon`:                                                    │
│ ├─ conversations_historical (9,424 rows)                        │
│ ├─ funnel_stages (~50k rows con stage transitions)              │
│ ├─ guests (7,499 rows seed — feed Phase B)                      │
│ ├─ bookings_with_metadata (646 rows enriquecidos)               │
│ └─ campaigns_consent (opt-in tracking)                          │
│                                                                  │
│ R2:                                                              │
│ ├─ operator_playbook.md (bot system prompt source)              │
│ ├─ knowledge_findings_v2.md (per-property, weighted)            │
│ └─ training_examples/ (few-shot conversations)                  │
│                                                                  │
│ Workers AI Vectorize:                                            │
│ ├─ Index `conversations-v2` (9,424 vectors, 1024 dim)           │
│ └─ Index `operator-patterns` (200k outbound msgs)               │
│                                                                  │
│ Airtable:                                                        │
│ ├─ Guests base (mirror D1, Karina-facing)                       │
│ ├─ Past bookings + LTV                                          │
│ └─ Campaign segments (signed permissions)                        │
└─────────────────────────────────────────────────────────────────┘
```

**Principio**: PII bruta (audios, IDs, full text) NUNCA sale de local. Cloud solo recibe **derivados anonimizados o agregados o vectorizados**.

---

## 5. Plan de ejecución — 3 días enfocados

### Día 1 — Conversation reconstruction + Funnel analytics (Ejes A + B)

**Mañana**:
- Pipeline v2 `stage_a_reconstruct.py` — agrupa mensajes en hilos con gap detection
- Compute metrics per hilo + join bookings outcome
- Output: `conversations_historical.csv` local

**Tarde**:
- `stage_b_funnel.py` — labelea stages por LLM (Haiku, $2-3) o keyword rules
- Compute conversion rates por stage transition
- Output: funnel report + abandonment hotspots

**Deliverable día 1**: Markdown report con funnel + 5-10 insights críticos. Mostrar a Alex.

### Día 2 — Operator playbook + Temporal analytics (Ejes C + E)

**Mañana**:
- `stage_c_operator_playbook.py` — sample 50 conversations × outcome × stage → Sonnet extracts patterns
- Output: `operator_playbook.md` v1

**Tarde**:
- `stage_e_temporal.py` — booking patterns por mes/día/temporada
- Latency analysis (operator response time vs conversion)
- Output: temporal report + heatmaps

**Deliverable día 2**: `operator_playbook.md` + temporal insights. Mostrar a Alex para validate.

### Día 3 — Multimedia (Eje D) + Deploy to production

**Mañana**:
- `stage_d_audio.py` — Whisper transcribe sample 5k audios (top categories from operator)
- Re-feed transcripts into operator_playbook update
- `stage_d_images.py` — Claude vision sample 1k images (sent BY operator)

**Tarde**:
- Deploy pipelines:
  - D1 migrations + import scripts
  - R2 upload `operator_playbook.md`
  - Workers AI Vectorize index creation + populate
  - Airtable bulk import via API
- Smoke tests

**Deliverable día 3**: production-deployed datasets + sanity queries successful.

---

## 6. Diferencia clave vs v1 — ejemplos concretos

### Ejemplo 1: Cliente pregunta "cuánto cuesta?"

**v1 bot behavior**:
- Look up `faq_clusters.csv` → cluster_id #1 "pricing"
- Suggested answer: "Los precios varían por temporada..."
- Stale, generic, no conversion-optimized

**v2 bot behavior**:
- Lookup phone in `conversations_historical`: cliente está en categoría "past_guest, 2 bookings RdM"
- Query Vectorize: 47 conversaciones similares (past_guest re-engagement) → 31 convirtieron
- Pull operator_playbook pattern "price_quote_to_past_guest": "menciona staff por nombre + reference last visit + offer slight upgrade vs anchor"
- Compose response: "¡María! Qué gusto. Para que te tengamos como la última vez con Celene, fin de semana 25-27 mayo te sale en $13K (mismo que la vez anterior) + suite con vista al mar incluida sin extra. Confirmamos?"

→ Personalization × conversion patterns × playbook. ESO es v2.

### Ejemplo 2: Cliente pregunta "tienen alberca?"

**v1**: respuesta cluster #9 "wifi" (mal clusterizado).

**v2**:
- Funnel analysis dice: 87% de clientes que preguntan alberca booking dentro de 5 turnos
- Operator playbook: "mention alberca → IMMEDIATELY mention adicionales (palapa, chef, playa)"
- Response: "Sí, infinity pool frente al mar. Aquí fotos: [link]. Por cierto, también incluye chef Celene + playa privada — la casa completa para 30 huéspedes. ¿Para cuántas personas vienen?"

→ Bot AVANZA el funnel (pregunta dates+group), no solo responde.

---

## 7. Costos estimados

| Eje | LLM costs | Tiempo WC | Tiempo CC |
|---|---|---|---|
| A — Reconstruction | $0 | 1 día | 0 |
| B — Funnel | $2-3 (Haiku labeling) | 1 día | 0 |
| C — Operator playbook | $5-10 (Sonnet patterns) | 1 día | 0 |
| D — Audio Whisper | $50-100 | 0.5 día | 0 |
| D — Image vision | $30-50 | 0.5 día | 0 |
| D — PDF OCR | $10 | 0.3 día | 0 |
| E — Temporal | $0 | 0.5 día | 0 |
| Deploy production | $0 | 0 | 1 día (D1+R2+Vectorize+Airtable setup) |
| **TOTAL** | **~$100-175** | **~4 días WC** | **~1 día CC** |

Pipeline reproducible — Alex puede re-correr cada 3 meses por ~$50 marginal.

---

## 8. Alternativa más rápida (si 3 días es mucho)

**MVP "high-value subset"** (1 día):

1. **Solo Eje A + B (conversation reconstruction + funnel)** — $5 LLM, 1 día WC
2. **Solo Eje C lite (operator playbook from texto)** — skip audio/image, $5 LLM, 1 día WC
3. Deploy D1 + operator_playbook.md → bot v5 lo consume

Skip multimedia + temporal hasta segunda iteración.

ETA MVP: **2 días WC + 0.5 día CC**, ~$15 LLM total.

Recomiendo MVP si quieres velocidad. Pipeline completo si quieres extracción máxima.

---

## 9. Decisiones pendientes Alex

**Q-54-1** ¿MVP 2 días o pipeline completo 4 días?
- [ ] MVP (Ejes A+B+C lite, sin multimedia/temporal) — 2 días WC + $15
- [ ] Completo (5 ejes) — 4 días WC + $100-175

**Q-54-2** ¿Multimedia es OK procesar?
- [ ] Sí, audios + imágenes (con privacy local-only)
- [ ] Solo audios
- [ ] Solo imágenes
- [ ] Skip multimedia

**Q-54-3** ¿Sequencing vs Greeter v5?
- [ ] Pausar Greeter v5 hasta v2 data terminado (mejor input = mejor bot)
- [ ] Paralelo: WC arranca data mining v2, CC sigue Greeter v5 con datos v1
- [ ] Greeter v5 primero, data v2 después

Mi voto: **Q-54-3 → paralelo**. Los dos sprints no se bloquean. Greeter v5 con data v1 ya es mejorable; en cuanto v2 esté listo, swap el system prompt + KB references.

**Q-54-4** ¿Acceso a infraestructura local?
- [ ] Sí, sesión Claude Code local + WC vía Drive/screen share para queries específicas
- [ ] No, WC trabaja con CSVs que Alex sube al Project

Si **no**: WC trabaja a ciegas, depende de Alex correr scripts. Lentitud x3.

**Q-54-5** ¿Privacy/legal compliance?
- LFPDPPP: opt-in requerido para marketing. Pipeline debe diferenciar consent
- Audios incluyen voces de operators + clientes — privacy de empleados/clientes
- IDs personales en PDFs — NO subir, solo derivados agregados

Confirma que:
- [ ] OK procesar localmente (sin upload)
- [ ] Outputs sanitizados (sin PII identificable)
- [ ] Aviso a empleados (Karina/staff) que sus mensajes son analizados para training del bot
- [ ] Consent layer en bot v5 antes de campañas marketing

---

## 10. Por qué este pipeline v2 vale la pena

| Métrica | v1 result | v2 expected |
|---|---|---|
| FAQs identificadas | 62 | 80-100 + jerarquía + intent flow |
| Conversaciones reconstruídas | 0 | 9,424 |
| Outcomes labeled | 646 (solo bookings) | 9,424 (todos con label convert/abandon/stalled) |
| Operator patterns extraídos | 0 | 30-50 patterns con conversion correlation |
| Multimedia procesado | 0 | ~5k audios + 1k images + 5k PDFs |
| Temporal insights | 0 | Mensual + daily + lead-time distributions |
| Bot KB richness | Static markdown | Vector retrieval + dynamic prompt assembly |
| CRM seed | CSV | D1 + Airtable live |
| Campaign-ready segments | CSV no permission | D1 con consent tracking |

**v2 NO es 2x v1. Es 10x v1** porque cambia el paradigma de "extract FAQs" a "**model the business**".

---

## 11. Inspiración / referencias

Este approach se inspira en:

- **Sales conversation intelligence** (Gong, Chorus.ai) — extract patterns from successful sales calls
- **Customer Data Platforms** (Segment, mParticle) — unified customer profile from heterogeneous sources
- **Conversation analytics academic literature** — turn-taking, latency, sentiment trajectories
- **Vector search for retrieval-augmented bots** — Mendable, custom OpenAI assistants

NO inventando nada nuevo. Aplicando best practices al corpus único que tiene Alex (11 años WhatsApp + bookings = goldmine).

---

**FIN thread/54**. Esperando voto Alex Q-54-1-5.

Si MVP aprobado → arranco mañana con Ejes A+B+C lite.
Si completo aprobado → arranco mañana con Ejes A+B, día 2 C+E, día 3 D + deploy.

— Web Claude, 2026-05-15
