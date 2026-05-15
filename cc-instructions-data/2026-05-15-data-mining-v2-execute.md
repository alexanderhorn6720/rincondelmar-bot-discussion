# Execute: Data Mining v2 — CC-Data session

**Date**: 2026-05-15 (overnight WC autonomous work)
**From**: WC (after Alex aprobó Q-54-1-5)
**To**: CC-Data (sesión local en `C:\rdm-wa-api\`)
**Re**: Pipeline v2 ejecutable, 4 ejes (A, B, C, E), SIN multimedia
**ETA**: 3-4 días enfocados, ~$15-25 LLM total
**Branch**: `feat/data-mining-v2` (local en `C:\rdm-wa-api\rdm_analysis\v2\`)

---

## 0. ⚠️ HALLAZGO CRÍTICO — leer ANTES de empezar

WC verificó D1 en producción (2026-05-15 madrugada) y descubrió que **CC-Bot ya construyó las tables Phase B**:

| Table | Status | Implicación |
|---|---|---|
| `guests` | ✅ exists, schema completo, **0 rows** | Pipeline v2 deploya aquí, NO crea table nueva |
| `leads` | ✅ exists con `priority_score` STORED generated column, **0 rows** | Mapea conversations sin booking → leads |
| `guest_events` | ✅ exists con 37 event_type enum values, **0 rows** | Cada msg outbound del operator → event |
| `bookings` | ✅ exists, **5 rows** (production current) | NO touch — beds24_bookings es separado |
| `beds24_bookings` | ✅ exists, **0 rows** | Aquí va el seed de `bookings_by_phone.csv` (646 rows) |
| `conversations` | ✅ exists, **11 rows** (current bot state) | NO touch — esta es para runtime, no histórico |
| `bot_link_clicks` | ✅ exists | CC-Bot ya hizo PR A2 — NO duplicar |

**Cambio de plan vs thread/55**: 
- ❌ NO crear `conversations_historical` table nueva
- ❌ NO crear `funnel_stages` table nueva
- ❌ NO crear `customers_seed_v2` table nueva
- ✅ MAPEAR outputs v2 → tables existentes (`guests` + `leads` + `guest_events` + `beds24_bookings`)
- ✅ Phase B foundation entera ya está construida — v2 la POBLA

**Esto simplifica deploy** y **alinea v2 con Phase B trabajada por CC-Bot**.

WC verificó también que existe `bot_link_clicks` deployed — CC-Bot ya hizo PR A2.

---

## 1. ⚠️ HALLAZGO CRÍTICO #2 — messages.csv contaminado

WC vio sample de `extract/messages.csv` y encontró que contiene **mensajes PERSONALES de Alex mezclados con business**:
- Compraventa de departamentos / trámites notariales
- Conversaciones con hija Julia, hermana, familia
- Asuntos médicos personales
- Compras personales

**Implicación**: pipeline v2 v1 falló en parte porque procesó este contenido como "business operator messages". Operator playbook saldría sesgado.

**Acción requerida en Eje A**: filtrar mensajes business vs personal **antes de cualquier análisis**.

### 1.1 Filtros para business-only

Criterios para clasificar conversation como business:
1. **Phone tiene booking en Beds24** → business confirmed
2. **Phone tiene `category_final IN (lead_warm, lead_cold, broadcast_recipient)`** → business
3. **Phone NO tiene chat con keywords personales** ("hija", "papá", "mamá", "esposa", "Julia", "Adrián")
4. **Chat NO tiene mentions de propiedades personales no-RdM** (e.g. "departamento Interlomas")
5. **Conversation tiene keywords RdM**: "rincón", "morenas", "huerta", "alberca", "chef", "playa", "Coyuca", "Acapulco"

Pipeline v2 Eje A primero etiqueta `is_business_conversation` y excluye personal del resto del análisis.

Personal conversations cuentas para tabla `excluded_personal_conversations` (audit) pero NO entran al operator playbook.

---

## 2. Arquitectura v2 revisada — alineada con D1 production

```
LOCAL (C:\rdm-wa-api\)
├── msgstore.db (PII bruto, NO upload)
├── rdm_analysis/
│   ├── outputs/  ← v1 results (referencia)
│   ├── extract/  ← v1 intermediates
│   └── v2/       ← NEW pipeline aquí
│       ├── stage_0_business_filter.py         ← NEW critical
│       ├── stage_a_reconstruct.py
│       ├── stage_b_funnel.py
│       ├── stage_c_operator_playbook.py
│       ├── stage_e_temporal.py
│       ├── stage_deploy_to_d1.py              ← inserts a guests/leads/events
│       └── outputs/
│           ├── conversations_v2.parquet       ← intermedio (PII)
│           ├── operator_playbook.md           ← deploy a R2
│           ├── knowledge_findings_v2.md
│           └── temporal_insights.md

CLOUD (D1 rincon - alineado con Phase B)
├── guests              ← seed desde contact_summary + enriquecimiento v2
├── leads               ← seed desde conversations no-booking (filtered business)
├── guest_events        ← eventos derivados (lead_created, lead_quoted, etc.)
├── beds24_bookings     ← seed desde bookings_by_phone.csv
└── (Vectorize index)   ← rdm-conversations-v2
```

---

## 3. Día 1 — Eje 0 + Eje A: Business filtering + Reconstruction

### 3.1 Stage 0 — Business filtering (NEW, no estaba en thread/55)

**Goal**: separar mensajes business de personales. Necesario antes de TODO lo demás.

**Script**: `stage_0_business_filter.py`

```python
"""
Stage 0: Business vs Personal classification.

Output:
  - business_conversations.parquet  (CONTEXT para todos los siguientes ejes)
  - personal_conversations.parquet  (auditoría — excluida del análisis)
  - business_filter_report.md       (stats: cuántas eliminadas, por qué)
"""

import pandas as pd
from pathlib import Path

DATA = Path('C:/rdm-wa-api/rdm_analysis')

# Load
msgs = pd.read_csv(DATA / 'extract/messages.csv', dtype={'chat_id': int})
chat_contact = pd.read_json(DATA / 'extract/chat-to-contact.json')  # asume existe
contacts = pd.read_csv(DATA / 'contact_summary.csv', dtype={'phone': str})

# Join msgs → phone via chat-to-contact
msgs = msgs.merge(chat_contact, on='chat_id')

# Personal keywords (case-insensitive)
PERSONAL_KEYWORDS = [
    'julia', 'adrián', 'adrian', 'sophia', 'judith',
    'hija', 'hijo', 'esposa', 'esposo', 'papá', 'mamá',
    'departamento', 'notaría', 'notaria', 'escritura', 'predial',
    'isr', 'hipoteca', 'curp', 'rfc',
    'doctor', 'dentista', 'farmacia', 'medicamento',
    'colegio', 'escuela', 'tareas',
]

# Business keywords
BUSINESS_KEYWORDS = [
    'rincón del mar', 'rincon del mar', 'las morenas', 'huerta cocotera',
    'alberca', 'chef', 'playa', 'coyuca', 'acapulco', 'pie de la cuesta',
    'reservar', 'disponibilidad', 'noche', 'huésped', 'huesped',
    'mascotas', 'wifi', 'check-in', 'check in',
    'airbnb', 'precio', 'tarifa', 'cotización', 'cotizacion',
]

def classify_conversation(phone, chat_msgs, contact_row):
    """Returns 'business' | 'personal' | 'mixed' | 'unclear'."""
    
    # Rule 1: phone has booking → business confirmed
    if contact_row is not None and contact_row.get('has_booking') == True:
        return 'business'
    
    # Rule 2: contact category strongly business
    if contact_row is not None:
        cat = contact_row.get('category_final', '')
        if cat in ('past_guest', 'repeat_guest', 'vip_guest', 'lead_warm', 'lead_cold'):
            return 'business'
        if cat in ('personal',):
            return 'personal'
        if cat in ('staff_or_proveedor',):
            return 'personal'  # exclude staff from analysis
    
    # Rule 3: keyword presence
    full_text = ' '.join(chat_msgs['text'].fillna('').str.lower())
    biz_hits = sum(1 for kw in BUSINESS_KEYWORDS if kw in full_text)
    pers_hits = sum(1 for kw in PERSONAL_KEYWORDS if kw in full_text)
    
    if biz_hits > 2 and pers_hits == 0:
        return 'business'
    if pers_hits > 2 and biz_hits == 0:
        return 'personal'
    if pers_hits > biz_hits * 3:
        return 'personal'  # heavy personal lean
    if biz_hits > pers_hits * 3:
        return 'business'  # heavy business lean
    
    return 'unclear'  # needs LLM or manual review

# Apply
msgs['conversation_phone_id'] = msgs['phone'].astype(str)
conv_groups = msgs.groupby('conversation_phone_id')

results = []
for phone, group in conv_groups:
    contact_row = contacts[contacts['phone'] == phone].iloc[0] if not contacts[contacts['phone'] == phone].empty else None
    classification = classify_conversation(phone, group, contact_row)
    results.append({
        'phone': phone,
        'classification': classification,
        'msg_count': len(group),
        'biz_score': sum(1 for kw in BUSINESS_KEYWORDS if kw in ' '.join(group['text'].fillna('').str.lower())),
        'pers_score': sum(1 for kw in PERSONAL_KEYWORDS if kw in ' '.join(group['text'].fillna('').str.lower())),
    })

df = pd.DataFrame(results)

# Output split
business = df[df['classification'] == 'business']
personal = df[df['classification'] == 'personal']
unclear = df[df['classification'] == 'unclear']

print(f"Business: {len(business)} ({len(business)/len(df)*100:.1f}%)")
print(f"Personal: {len(personal)}")
print(f"Unclear: {len(unclear)} — these need LLM review")
print(f"Mixed: {len(df[df['classification'] == 'mixed'])}")

# For unclear: send to Haiku for classification (cheap, ~$1)
# ...
```

**Costo Haiku para unclear**: ~$2-5 total (asumo ~500 unclear conversations, $0.0001/conv).

**Acceptance criteria Stage 0**:
- [ ] `business_conversations.parquet` con ≥6,500 rows (estimado del corpus business genuino)
- [ ] `personal_conversations.parquet` con ~500-1500 rows excluded
- [ ] Report markdown con breakdown: rule_1_booking, rule_2_category, rule_3_keywords, llm_classified
- [ ] Sanity check: total = msgs.csv conversations count

### 3.2 Stage A — Conversation reconstruction

**Goal**: 9,424 hilos → reducir a ~6,500 business → reconstruir con metadata + outcome.

**Script**: `stage_a_reconstruct.py`

```python
"""
Stage A: Reconstruct conversations with metadata + outcome.

INPUT: business_conversations.parquet (from Stage 0)
OUTPUT: conversations_v2.parquet

Schema 30+ columns (ver thread/55 §2 Eje A schema).

Key changes vs thread/55:
1. resulted_in_booking → 3-value enum (NOT boolean):
   - 'converted_direct'  (Beds24 direct channel, booking dentro 90 días)
   - 'converted_indirect' (AirBnB/Booking.com OR booking 90-180 días)
   - 'not_converted'

2. NEW columns:
   - is_personal_conversation BOOLEAN (always False here, but kept for join)
   - lead_quality_score INTEGER 0-100 (derived)
   - operator_engagement_level TEXT ('high','medium','low')

3. Para Vectorize: column `embedding_input_text` con conversación compactada
   (max 8K chars, formato: alternating "USER:..."/"OP:..." con timestamps).
"""

import pandas as pd
import gzip
from datetime import timedelta

# ... (full implementation)

# Outcome classification
def classify_outcome(row, bookings_df):
    phone = row['phone']
    last_msg = row['last_msg_at']
    
    user_bookings = bookings_df[bookings_df['phone'] == phone]
    if user_bookings.empty:
        return 'not_converted'
    
    # Check if any booking arrival within 90 days of last message
    booking_within_90d = user_bookings[
        (user_bookings['first_arrival'] >= last_msg) &
        (user_bookings['first_arrival'] <= last_msg + timedelta(days=90))
    ]
    
    if booking_within_90d.empty:
        # Check 180 days window (indirect)
        booking_within_180d = user_bookings[
            (user_bookings['first_arrival'] >= last_msg) &
            (user_bookings['first_arrival'] <= last_msg + timedelta(days=180))
        ]
        if not booking_within_180d.empty:
            return 'converted_indirect'
        return 'not_converted'
    
    # Within 90 days — check channel
    if 'Direct' in booking_within_90d.iloc[0].get('channels', ''):
        return 'converted_direct'
    return 'converted_indirect'  # AirBnB/Booking.com

# Engagement level
def engagement_level(row):
    if row['msgs_from_me'] >= 20 and row['turns_count'] >= 10:
        return 'high'
    if row['msgs_from_me'] >= 5:
        return 'medium'
    return 'low'

# Embedding input — compact conversation for Vectorize
def build_embedding_input(msgs_in_conv, max_chars=8000):
    """Format: timestamped alternating USER/OP messages."""
    lines = []
    for m in msgs_in_conv.itertuples():
        sender = 'OP' if m.from_me else 'USR'
        ts = m.timestamp.strftime('%Y-%m-%d %H:%M')
        text = m.text[:200] if m.text else ''
        lines.append(f"[{ts}] {sender}: {text}")
    
    full = '\n'.join(lines)
    if len(full) > max_chars:
        # Keep first 4K + last 4K (head + tail summary)
        full = full[:4000] + '\n...[truncated]...\n' + full[-4000:]
    return full
```

**Acceptance criteria Stage A**:
- [ ] ~6,500 business conversations procesadas
- [ ] Outcome distribution sanity: ~10% converted_direct, ~5% converted_indirect, ~85% not_converted
- [ ] embedding_input_text populado en todas las rows
- [ ] median_response_time_minutes calculado correctamente
- [ ] CSV/parquet exportado + sanity report

---

## 4. Día 2 — Eje B: Funnel + Eje E: Temporal

### 4.1 Stage B — Funnel analysis

**Goal**: identificar las etapas y conversion rates.

**Script**: `stage_b_funnel.py`

8 etapas a detectar (heurística + Haiku para edge cases):

```python
FUNNEL_STAGES = [
    'initial_inquiry',       # msgs ≥1
    'date_specified',        # user menciona fecha o "fin de semana"
    'group_specified',       # user menciona N personas
    'property_clarified',    # operator/user menciona propiedad específica
    'price_quoted',          # operator envía precio (heurística: regex /\$?\d{4,6}/ in from_me)
    'price_accepted',        # user dice "ok", "perfecto", "lo tomo" después de price
    'payment_data_requested', # operator envía CLABE/cuenta
    'booking_confirmed',     # joined con bookings, status confirmed
]

def detect_stage_transitions(conv_msgs):
    transitions = {}
    
    for i, msg in enumerate(conv_msgs.itertuples()):
        text = (msg.text or '').lower()
        
        # Stage detection rules
        if 'initial_inquiry' not in transitions:
            transitions['initial_inquiry'] = msg.timestamp
        
        if 'date_specified' not in transitions and detect_date_mention(text):
            transitions['date_specified'] = msg.timestamp
        
        if 'group_specified' not in transitions and detect_group_size(text):
            transitions['group_specified'] = msg.timestamp
        
        # ... etc
    
    return transitions

# Funnel output schema
funnel_data = []
for conv_id, conv in conversations.groupby('conversation_id'):
    transitions = detect_stage_transitions(conv)
    for stage, ts in transitions.items():
        funnel_data.append({
            'conversation_id': conv_id,
            'phone': conv.iloc[0]['phone'],
            'stage': stage,
            'reached_at': ts,
            'msgs_to_reach': stage_msg_index,
            'duration_from_first_msg_hours': (ts - first_msg).total_seconds() / 3600,
        })

# Output: funnel_stages.parquet (deployable a D1)
```

**Análisis derivado** (output `funnel_report.md`):

```markdown
# Funnel Conversion Analysis

## Stage transitions (6,500 business conversations)

| Stage | Reached | % | Conversion to next |
|---|---|---|---|
| initial_inquiry | 6,500 | 100% | - |
| date_specified | ~2,800 | 43% | 43% |
| group_specified | ~1,820 | 28% | 65% |
| property_clarified | ~1,430 | 22% | 78% |
| price_quoted | ~1,170 | 18% | 82% |
| price_accepted | ~780 | 12% | 67% |
| payment_data_requested | ~520 | 8% | 67% |
| booking_confirmed | ~520 | 8% | 100% |

## Top abandonment hotspots
1. **initial → date** (57% drop) — el cliente que no especifica fecha en su primer turno raramente vuelve. Bot debe PEDIR fechas inmediatamente.
2. **price_quoted → accepted** (33% drop) — price objection bottleneck. Operator playbook §price_objection_handling critical.
3. **accepted → payment** (33% drop) — cliente acepta verbalmente pero no llega a pago. Followup automático CRITICAL.

## Recommended bot interventions
- Trigger A: si conv tiene >3 msgs sin fecha → bot proactive "¿Para qué fechas estás pensando?"
- Trigger B: si price_quoted + sin respuesta 24h → soft followup "¿Te ayudo con dudas sobre la cotización?"
- Trigger C: si price_accepted + sin payment 48h → followup "¿Necesitas que te re-envíe los datos para el anticipo?"
```

### 4.2 Stage E — Temporal analytics

**Goal**: patrones temporales que informan Greeter v5 + staffing decisions.

**Script**: `stage_e_temporal.py`

Análisis a producir (no LLM, todo Python):

```python
analyses = {
    'bookings_by_month': bookings_df.groupby(bookings_df['first_arrival'].dt.month).agg({
        'phone': 'count',
        'total_charged': 'sum',
        # ...
    }),
    
    'day_of_week_patterns': msgs.assign(
        dow=lambda x: x['timestamp'].dt.day_name(),
        hour=lambda x: x['timestamp'].dt.hour
    ).groupby(['dow', 'hour']).size(),
    
    'operator_latency_vs_conversion': compute_latency_conversion(msgs, conversations),
    
    'lead_time_distribution': (bookings_df['first_arrival'] - bookings_df['first_booking_date']).dt.days.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]),
    
    'seasonal_pricing_signals': analyze_price_mentions_by_month(msgs),
}
```

**Output** (`temporal_insights.md`):

```markdown
# Temporal Insights — Rincón del Mar 11 años WhatsApp data

## Booking patterns por mes
[heatmap]

Insights:
- Diciembre: highest revenue concentration (12% bookings, 18% revenue)
- Mayo-Junio: lowest occupancy (8% bookings, 9% revenue) — campaign window
- Enero-Febrero: lead time longest (avg 45 días) — long planners

## Day-of-week / hour
[heatmap]

Insights:
- Lunes 9-11 AM: peak inbound msgs (post-weekend planning)
- Viernes 4-7 PM: urgent inquiries (weekend bookings)
- Domingo: lowest inbound — pero highest conversion rate (clientes ya decidieron)

## Operator latency vs conversion (CRITICAL FINDING)

| Response time | Conversion rate |
|---|---|
| <30 min | 28% |
| 30 min - 1h | 22% |
| 1h - 4h | 15% |
| 4h - 24h | 8% |
| >24h | 3% |

Hypothesis test (p < 0.001): latency <1h vs >24h → 7x conversion difference.

**Conclusion**: Telegram notif real (D5) es CRÍTICA, no nice-to-have.
Bot tiene que responder mientras humano no responde.

## Lead time distribution
- p25: 7 días anticipación
- p50: 21 días
- p75: 60 días
- p90: 120 días

→ 50% del trabajo es bookings <21 días de anticipación. Bot debe ser fast.
```

**Acceptance criteria Día 2**:
- [ ] `funnel_stages.parquet` con stage transitions per conv
- [ ] `funnel_report.md` con insights ejecutivos
- [ ] `temporal_insights.md` con heatmaps PNG en `outputs/v2/charts/`
- [ ] Operator latency hypothesis test ejecutado con p-value real

---

## 5. Día 3 — Eje C: Operator Playbook (highest value)

**Goal**: extraer 30-50 patterns del operador que correlacionan con CONVERSIÓN.

**Script**: `stage_c_operator_playbook.py`

### 5.1 Sampling strategy

```python
# 8 (stage, outcome) combos para análisis
SAMPLES = {
    ('price_quoted', 'converted_direct'): 50,
    ('price_quoted', 'not_converted'): 50,
    ('price_accepted', 'converted_direct'): 50,
    ('price_accepted', 'not_converted'): 50,  # acepted pero no pagó
    ('group_specified', 'converted_direct'): 30,
    ('group_specified', 'not_converted'): 30,
    ('initial_inquiry', 'converted_direct'): 50,  # rare diamonds
    ('escalation_to_call', 'converted_direct'): 30,
}

# Sample stratified by:
# - Property (RdM, Morenas, Combinada, Huerta proportional)
# - Year (avoid 2017 over-representation)
# - Group size bucket
```

### 5.2 Sonnet prompts

WC drafted 2 prompts here. Use them verbatim.

**PROMPT 1 — Price quote pattern extraction**:

```python
PROMPT_PRICE_QUOTE = """Eres analista de patrones de venta en hospitality.

Aquí 50 conversaciones reales de WhatsApp donde el operador de un vacation rental (Rincón del Mar, Acapulco) cotizó precio. En 25 de ellas el cliente CONVIRTIÓ (reservó dentro de 90 días). En 25 NO CONVIRTIÓ (cliente abandonó).

Tu tarea: extraer 5-10 patrones LINGÜÍSTICOS Y ESTRUCTURALES OBSERVABLES en las cotizaciones que correlacionan con conversión vs abandono.

Para cada pattern:
- **Nombre** (3-5 palabras)
- **Frecuencia observada** (X de 25 en converted, Y de 25 en not_converted)
- **Ejemplo textual** (1 cita corta sin información personal del cliente)
- **Hipótesis de mecanismo** (1-2 frases sobre POR QUÉ correlaciona)
- **Aplicabilidad para bot** (cómo usar este pattern en system prompt)

REGLAS:
- NO opines sobre estrategia general, solo describe lo que ves
- Las citas: redacta como genérico, NO copies literal con nombres
- Solo patterns con frecuencia diferencial ≥3x entre converted vs not_converted
- Output: markdown estructurado

CONVERSACIONES (50 muestras alternadas converted/not_converted):
[paste conversations here, anonymized]
"""
```

**PROMPT 2 — Objection handling pattern**:

```python
PROMPT_OBJECTION = """Eres analista de objection handling en sales.

Aquí 30 conversaciones donde el cliente objetó el precio del operador. En 15, el operador rescató la conversación y la cerró en booking. En 15, perdió al cliente.

Identifica patrones de respuesta del operador que correlacionan con rescate vs pérdida.

[same format as PROMPT 1]

CONVERSACIONES:
[paste]
"""
```

### 5.3 Output

`outputs/v2/operator_playbook.md` con estructura:

```markdown
# Operator Playbook — Extraído de 11 años de data (2026-05-15)

## Pattern Library

### §1 Price quote patterns (8 patterns extraídos)

#### 1.1 Anchor incluye chef antes de precio
- **Converted**: 18/25 (72%)
- **Not converted**: 4/25 (16%)
- **Ejemplo**: "Te incluye nuestro chef Celene + 2 cocineras + mozo. El precio para fin de semana queda en $13K..."
- **Mecanismo**: ancla valor antes de precio reduce sticker shock
- **Para bot**: SIEMPRE menciona servicios incluidos ANTES de precio numérico

#### 1.2 Cotización con 2-3 opciones
- **Converted**: 15/25 (60%)
- **Not converted**: 6/25 (24%)
- **Ejemplo**: "Tenemos 3 opciones: entre semana $8K, fin de semana $13K, o combinado..."
- **Mecanismo**: choice architecture, evita "sí/no" binary
- **Para bot**: cuando user pregunta precio, ofrece 2-3 opciones de fechas/property

... (8 patterns total para §1)

### §2 Objection handling (6 patterns)

#### 2.1 Mention what's included that competition charges extra
- **Rescued**: 8/15 (53%)
- **Lost**: 2/15 (13%)
- **Ejemplo**: "Considera que el chef + 2 cocineras está incluido, en otras casas son $1,500/noche extra"
- **Mecanismo**: reframe price-per-feature
- **Para bot**: si user dice "muy caro", responde con value reframe NO con descuento

#### 2.2 Recalibrate per-person cost
- **Rescued**: 6/15 (40%)
- **Lost**: 1/15 (7%)
- **Ejemplo**: "Para 20 personas, sale $650 por persona/noche con todo incluido. Sin renta de casa, una habitación promedio sale más cara."
- **Para bot**: si user objeta sobre price total, recalibra a per-person

... (6 patterns)

### §3 Escalation patterns (5 patterns)

#### 3.1 Phone escalation triggers
- 87% de phone-escalations son: groups >20, custom events, repeat guests
- Operator phrase: "Mejor te llamo para platicar los detalles?"
- Phone-escalation conversion: 64% vs text-only 18%
- **Para bot**: si detect (group >20 OR custom event OR past_guest OR vip), trigger Telegram notif para llamada humana

### §4 Closing patterns (4 patterns)

#### 4.1 Soft close after price accept
- "Te mando los datos para anticipo: [CLABE] — con 33% lo apartamos hoy"
- Closes 67% within 48h

... etc

## Anti-patterns (qué NO hacer)

### AP.1 Apologizing for price
- **Converted**: 1/25 (4%)
- **Not converted**: 8/25 (32%)
- **Ejemplo NEGATIVO**: "Disculpa, lo sé es alto pero..."
- **Mecanismo**: signals lack of confidence, validates objection
- **Para bot**: NEVER apologize for price, anchor value instead

### AP.2 Immediate discount on first objection
- **Rescued**: 2/15 (13%) — but those who rescued required deeper discount each turn
- **Lost**: 5/15 — but actual cancel rate of "rescued" was higher (data: 40% never paid)
- **Para bot**: NEVER offer discount on first objection
```

**Validation Alex** (~25 min):
- WC entrega draft a Alex post-Sonnet generation
- Alex valida/corrige 30-50 patterns
- WC actualiza final version

**Costo Sonnet**: ~$8-12 (8 prompts × ~$1-1.50 cada).

**Acceptance criteria Día 3**:
- [ ] 30-50 patterns documentados en operator_playbook.md
- [ ] Diferencia frecuencial converted vs not ≥3x en cada pattern
- [ ] Alex validó ≥80%
- [ ] Markdown sanitized (NO PII en ejemplos)
- [ ] Ready para inyectar en bot system prompt

---

## 6. Día 4 — Deploy a producción

### 6.1 Insert seed data a D1 tables (Phase B alignment)

#### 6.1.1 Seed `beds24_bookings` desde `bookings_by_phone.csv`

```sql
-- Migration: 000X_seed_beds24_bookings.sql
-- (Generated by stage_deploy_to_d1.py)

INSERT INTO beds24_bookings (
  id, booking_id_beds24, property_id, room_id,
  arrival_date, departure_date, guests_count,
  guest_name, guest_email, guest_phone, guest_country,
  status, channel, ota_source,
  total_charged_mxn, total_paid_mxn,
  created_at, updated_at
) VALUES (...) ON CONFLICT(id) DO UPDATE SET ...;
```

CC-Data ejecuta:
```bash
wrangler d1 execute rincon --remote --file=migrations/000X_seed_beds24_bookings.sql
```

#### 6.1.2 Seed `guests` desde `contact_summary.csv` enriquecido

Mapping:

| contact_summary | guests |
|---|---|
| phone | phone_raw + phone_e164 (normalize) |
| name_resolved | name |
| category_final | status_master (mapping: vip_guest→vip, repeat_guest→repeat, past_guest→customer, lead_*→prospect, etc.) |
| booking_count | total_bookings |
| total_charged | total_revenue_mxn (cast int) |
| cohort | tags_json (e.g. `["cohort:lapsed_recent"]`) |
| first_msg | last_activity_at + last_message_at |
| (derived) | language_preferred (heurística: country=US→en, otherwise es) |

```python
# stage_deploy_guests.py
import duckdb
conn = duckdb.connect()
contacts = conn.read_csv('contact_summary.csv').to_df()

status_mapping = {
    'vip_guest': 'vip',
    'repeat_guest': 'repeat',
    'past_guest': 'customer',
    'lead_warm': 'prospect',
    'lead_cold': 'prospect',
    'broadcast_recipient': 'prospect',
    'ex_lead_no_response': 'prospect',
    'address_book_only': 'prospect',
    'transactional_business': 'banned',  # exclude vendors
    'staff_or_proveedor': 'banned',       # exclude staff
    'spam_telemarketer': 'banned',
    'personal': 'banned',                  # exclude personal
    'irrelevant_or_unclear': 'prospect',
}

contacts['status_master'] = contacts['category_final'].map(status_mapping)
contacts['phone_e164'] = '+' + contacts['phone']  # add + prefix
contacts['language_preferred'] = contacts['country'].apply(
    lambda c: 'en' if c == 'US/CA' else 'es'
)

# Filter banned out
contacts_to_insert = contacts[contacts['status_master'] != 'banned']

# Generate UUIDs
import uuid
contacts_to_insert['id'] = [str(uuid.uuid4()) for _ in range(len(contacts_to_insert))]

# Tags as JSON
contacts_to_insert['tags_json'] = contacts_to_insert['cohort'].apply(
    lambda c: json.dumps([f"cohort:{c}"] if pd.notna(c) else [])
)

# Bulk insert via wrangler d1 batch
sql = generate_insert_sql(contacts_to_insert, table='guests')
write_to_file('migrations/000X_seed_guests.sql', sql)
```

Estimado: ~6,800 guests insertados (7,499 - banned categories).

#### 6.1.3 Seed `leads` desde business conversations sin booking

```python
# Cada business conversation que NO resultó en booking → row en `leads`
# Cada business conversation que SÍ resultó en booking → row con converted_to_booking_id

leads_from_convs = conversations[conversations['is_business_conversation']]

# Mapping conversations → leads
for _, conv in leads_from_convs.iterrows():
    lead = {
        'id': str(uuid.uuid4()),
        'guest_id': guest_id_for_phone(conv['phone']),
        'channel': 'whatsapp',
        'channel_thread_id': str(conv['conversation_id']),
        'first_contact_at': conv['first_msg_at'].timestamp(),
        'last_activity_at': conv['last_msg_at'].timestamp(),
        'group_size': conv.get('detected_group_size'),
        'property_interest_room_id': conv.get('detected_room_id'),
        'status': map_outcome_to_status(conv['outcome']),
        'urgency': derive_urgency(conv),
        'quote_amount_mxn': conv.get('quote_amount_extracted'),
        'created_at': conv['first_msg_at'].timestamp(),
        'updated_at': conv['last_msg_at'].timestamp(),
    }
    # ...

# Estimated: ~6,000 leads (business convs minus 646 with booking)
```

#### 6.1.4 Seed `guest_events` desde eventos derivados

Para cada conversation, generar eventos:
- `lead_created` (first message)
- `lead_engaged` (después de 3+ turnos)
- `lead_quoted` (si price_quoted stage reached)
- `lead_won` / `lead_lost` (según outcome)
- `msg_received`, `msg_sent_alex` (por cada mensaje, opcional — alto volumen)

⚠️ **Cuidado con volumen**: 437k mensajes individuales como events = 437k rows. **NO hacer todos**. Solo:
- Events stage transitions (~6 events por conv × 6,500 convs = 39k events)
- Plus events outcomes (~6,500 events)
- Total estimado: ~50k events (manejable en D1)

### 6.2 R2 upload — operator playbook

```bash
wrangler r2 object put rdm-knowledge/operator_playbook.md \
  --file=outputs/v2/operator_playbook.md \
  --content-type "text/markdown" \
  --remote

wrangler r2 object put rdm-knowledge/knowledge_findings_v2.md \
  --file=outputs/v2/knowledge_findings_v2.md \
  --content-type "text/markdown" \
  --remote

wrangler r2 object put rdm-knowledge/temporal_insights_v2.md \
  --file=outputs/v2/temporal_insights.md \
  --content-type "text/markdown" \
  --remote
```

### 6.3 Workers AI Vectorize

```bash
# Create index (1024 dim, cosine)
wrangler vectorize create rdm-conversations-v2 \
  --dimensions=1024 \
  --metric=cosine

# Populate via Python script (uses @cf/baai/bge-large-en-v1.5 o equivalent)
python stage_vectorize.py
```

`stage_vectorize.py`:
```python
import os
import requests
from pathlib import Path

CF_ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
CF_TOKEN = os.getenv('CF_TOKEN')

def get_embedding(text):
    # Use Anthropic embeddings or Workers AI direct
    url = f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/baai/bge-base-en-v1.5'
    r = requests.post(url, 
        headers={'Authorization': f'Bearer {CF_TOKEN}'},
        json={'text': text[:2048]}
    )
    return r.json()['result']['data'][0]

# Process business conversations
business_convs = pd.read_parquet('outputs/v2/conversations_v2.parquet')

vectors = []
for _, conv in business_convs.iterrows():
    if not conv['is_business_conversation']:
        continue
    
    emb = get_embedding(conv['embedding_input_text'])
    vectors.append({
        'id': conv['conversation_id'],
        'values': emb,
        'metadata': {
            # NO TEXT — privacy
            'phone_hash': hash_phone(conv['phone']),
            'outcome': conv['outcome'],
            'property_room_id': conv.get('detected_room_id'),
            'group_size': conv.get('detected_group_size'),
            'year': conv['first_msg_at'].year,
            'msgs_total': conv['msgs_total'],
            'turns_count': conv['turns_count'],
        }
    })

# Bulk upsert to Vectorize
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    requests.post(
        f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/vectorize/v2/indexes/rdm-conversations-v2/insert',
        headers={'Authorization': f'Bearer {CF_TOKEN}'},
        json={'vectors': batch}
    )
```

Costo estimated: ~6,500 conversations × $0.0001/embed = ~$0.65. Negligible.

### 6.4 Airtable (opcional, after D1 deploy)

Si Karina prefer Airtable UI:
- Sync `guests` from D1 to Airtable via Make scenario o script
- Read-only view en Airtable, source-of-truth en D1

(Skip si Karina trabaja directo en `/admin/guests` que CC-Bot va a build.)

### 6.5 Acceptance criteria Día 4

- [ ] `beds24_bookings` populated ~640 rows (sin testing/dev contamination)
- [ ] `guests` populated ~6,800 rows (con language_preferred derived)
- [ ] `leads` populated ~6,000 rows (status: won/lost/cold según outcome)
- [ ] `guest_events` populated ~50k events (stage transitions + outcomes)
- [ ] R2 `operator_playbook.md` uploaded + accessible
- [ ] Vectorize index `rdm-conversations-v2` populated con ~6,500 vectors
- [ ] Test query: `SELECT COUNT(*) FROM guests WHERE status_master='vip'` → 6 (sanity)
- [ ] Test query Vectorize: similarity search devuelve resultados sensatos

---

## 7. Tareas concretas CC-Data — chronological checklist

### Día 1 (8h enfocadas)

#### Mañana (4h)
- [ ] Clone `rincondelmar-bot-discussion` repo para acceso a este doc
- [ ] Read this doc completo + thread/55 + faq_clusters.csv + knowledge_findings.md
- [ ] Verify acceso a `C:\rdm-wa-api\.api-keys` con Anthropic key válida
- [ ] Verify recursos: `psutil.virtual_memory().available > 8 GB` (si no, usar duckdb en vez de pandas)
- [ ] Create branch local: `rdm_analysis/v2/` folder
- [ ] Install deps: `pip install pandas duckdb anthropic sentence-transformers pyarrow`
- [ ] Run `stage_0_business_filter.py` — output `business_conversations.parquet`
- [ ] Sanity check business filter (manual review 20 random samples)

#### Tarde (4h)
- [ ] Run `stage_a_reconstruct.py` — output `conversations_v2.parquet`
- [ ] Sanity check: outcome distribution makes sense?
- [ ] Reportar a thread/56 fin Día 1: stats + blockers si surgen

### Día 2 (8h)

#### Mañana (4h)
- [ ] Run `stage_b_funnel.py` — output `funnel_stages.parquet`
- [ ] Funnel report markdown drafted
- [ ] Verify abandonment hotspots make business sense

#### Tarde (4h)
- [ ] Run `stage_e_temporal.py` — output `temporal_insights.md` + heatmaps
- [ ] Hypothesis test latency vs conversion ejecutado
- [ ] Reportar Día 2 + share funnel + temporal insights con WC para validate

### Día 3 (8h)

#### Mañana (4h)
- [ ] Stratified sampling for 8 (stage, outcome) combos
- [ ] Anonymize samples (replace nombres con "Cliente X", phones con hashed)

#### Tarde (4h)
- [ ] Run Sonnet pattern extraction (8 prompts, ~$10 LLM)
- [ ] Compile `operator_playbook.md` v1
- [ ] Send to Alex for validation (~25 min Alex)
- [ ] Update final based on Alex feedback

### Día 4 (8h)

#### Mañana (4h)
- [ ] Generate SQL migrations for `guests`, `leads`, `guest_events`, `beds24_bookings`
- [ ] Test migrations on local D1 dev (wrangler d1 execute --local first)
- [ ] Apply to prod D1 via `wrangler d1 execute rincon --remote`

#### Tarde (4h)
- [ ] R2 uploads (operator_playbook + findings_v2 + temporal_insights)
- [ ] Vectorize index creation + populate
- [ ] Smoke tests: `wrangler d1 execute rincon --remote --command "SELECT COUNT(*) FROM guests"`
- [ ] Reportar Día 4 completion a thread/59

---

## 8. Issues conocidos + mitigations

### 8.1 RAM constraint

`extract/messages.csv` = 96 MB. Pandas in-memory = ~600 MB-1 GB con joins. Si máquina <8 GB RAM:

```python
# Use duckdb instead — handles out-of-core
import duckdb
con = duckdb.connect()
msgs = con.read_csv('extract/messages.csv')
# Now SQL queries scale beyond RAM
con.execute("SELECT phone, COUNT(*) FROM msgs GROUP BY phone").fetchdf()
```

### 8.2 Anthropic API rate limits

Para Sonnet calls del Eje C: 8 prompts × 4 minutes each = ~30 min wall time. Rate limits Tier 1 = 50 RPM. No issue.

Si rate limit hit: implement exponential backoff:
```python
import time
def api_call_with_retry(client, **kwargs):
    for attempt in range(5):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            time.sleep(2 ** attempt)
    raise
```

### 8.3 Multimedia descartado pero referenced

Algunos mensajes tienen `message_type != 0` (1=image, 4=contact, 9=document). Stage A debe contarlos pero NO procesarlos:
```python
msgs['has_media'] = msgs['message_type'] != 0
# Aggregate por conversation
conv['multimedia_count'] = msgs.groupby('conv_id')['has_media'].sum()
```

### 8.4 Phone number normalization

contact_summary.csv tiene phones sin '+'. D1 schema esperaba `phone_e164` con '+'. Add normalize step:
```python
def normalize_phone_e164(p):
    if pd.isna(p) or not p:
        return None
    p = str(p).strip().replace(' ', '').replace('-', '')
    if not p.startswith('+'):
        p = '+' + p
    return p
```

### 8.5 Bookings_by_phone.csv has `phone` column but some rows missing it

Per sample data observed, some rows in `contact_summary` have phone but NO `jid` (AirBnB-only contacts that never WhatsApp'd). These should still seed `guests` table — they're real customers.

### 8.6 Personal conversation contamination (NEW critical finding)

Per Stage 0 hallazgo: `extract/messages.csv` contiene mensajes personales de Alex (familia, trámites, etc.). Stage 0 obligatorio filtra antes de Stage A.

Si Alex insiste en preservar TODO el dataset (para análisis personal por curiosidad), Stage 0 puede generar 2 outputs:
- `business_conversations.parquet` (input para v2 pipeline)
- `personal_conversations.parquet` (LOCAL ONLY, NO upload — privacy)

---

## 9. Reporting a WC

CC-Data reporta a WC vía threads en `rincondelmar-bot-discussion`:

| Día | Thread expected | Content |
|---|---|---|
| 1 | `56-cc-data-day1-business-filter-and-reconstruction.md` | Stats: convs business vs personal, outcome distribution |
| 2 | `57-cc-data-day2-funnel-and-temporal.md` | Funnel stages + temporal heatmaps + latency hypothesis |
| 3 | `58-cc-data-day3-operator-playbook-draft.md` | 30-50 patterns drafted, sent to Alex for validation |
| 4 | `59-cc-data-day4-deploy-complete.md` | D1 + R2 + Vectorize populated, sanity checks pass |

WC standby para reviews + blockers. CC-Bot trabaja independiente en su sprint Greeter v5.

---

## 10. Out of scope (explicit)

NO hacer en este sprint:
1. Multimedia mining (Eje D) — Alex skipped
2. Real-time conversation analytics (eso es Phase 2)
3. Modificar bot prompts — eso es CC-Bot job en PR A6
4. Touch any `apps/`, `packages/` code (cloud) — CC-Data trabaja solo local + D1 inserts
5. Crear tables nuevas en D1 — solo INSERT a existentes
6. Modificar schemas existentes — si hay drift, escalar a WC
7. Push final operator_playbook a bot — eso es CC-Bot PR A6
8. Marketing campaigns — eso es post-sprint Alex+WC trabajo separado

---

## 11. Out of scope clarification — touch point con CC-Bot

CC-Data NO se comunica directo con CC-Bot. Toda coordinación via WC + threads.

CC-Data outputs → D1 tables (guests/leads/events/beds24_bookings) + R2 files + Vectorize index.

CC-Bot reads esos outputs en PR A6 (Greeter v5 prompt update con operator_playbook + vector search). Eso lo coordina WC con cc-instructions-bot/.

---

## 12. Final checklist antes de arrancar

- [ ] Alex confirmed Q-54-1-5 (✅ done 2026-05-15)
- [ ] CC-Data session available en máquina local Alex (✅ confirmed)
- [ ] `C:\rdm-wa-api\.api-keys` con Anthropic key (✅ confirmed)
- [ ] Subfolder `rdm_analysis/v2/` para outputs (✅ confirmed)
- [ ] Workers AI Vectorize (✅ confirmed)
- [ ] Phase B D1 tables ya construidas por CC-Bot (✅ verified by WC 2026-05-15)
- [ ] WC standby para questions vía threads

**Go signal**: cuando CC-Data lea esto y confirme acceso a recursos, arranca Día 1. WC monitorea threads.

---

**FIN cc-instructions-data**. CC-Data: arranca cuando puedas. WC standby.

— Web Claude, 2026-05-15 (autonomous overnight work)
