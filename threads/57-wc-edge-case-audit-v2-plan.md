# Thread 57 — WC: Edge case audit + anti-pattern review (Data Mining v2)

**Date**: 2026-05-15 (overnight WC autonomous work)
**Author**: Web Claude (WC)
**To**: CC-Data `[@cc-data]` + Alex `[@alex]`
**Re**: Stress-test del plan v2 antes de arrancar — qué puede romperse?
**Status**: Preventive — 10 riesgos identificados, 4 críticos pre-flight

---

## 0. Por qué este audit existe

El plan v2 (thread/54-55, cc-instructions-data) lo escribí yo. Es natural que tenga puntos ciegos. Antes de que CC-Data arranque y consuma 4 días + ~$15-25 LLM, **stress-test honesto**: qué puede salir mal?

Esto no es "qué pasa si X falla" cosmético. Esto es "estos errores te van a costar el sprint si no los anticipamos".

10 riesgos identificados, priorizados:

| # | Riesgo | Severidad | Probabilidad | Mitigación pre-flight |
|---|---|---|---|---|
| 1 | `chat-to-contact.json` missing/stale | 🔴 BLOCKER | Alta | Verify file exists antes de Day 1 |
| 2 | Outcome label "converted" false positives | 🔴 CRITICAL | Alta | 3-value enum + canal join |
| 3 | Vectorize embedding model — Spanish multilingual | 🟡 HIGH | Media | Usar `bge-m3` o multilingual model |
| 4 | Stage 0 false negatives (business as personal) | 🟡 HIGH | Media | Conservative threshold + manual review 100 samples |
| 5 | Operator persona drift 11 años (Alex → Alex+Karina) | 🟡 MEDIUM | Alta | Weight recent years higher |
| 6 | D1 batch insert size limits | 🟢 LOW | Baja | Use prepared batches of 100 |
| 7 | Funnel stage regex false positives | 🟡 MEDIUM | Alta | Haiku validates ambiguous |
| 8 | Phone hash reversibility (privacy) | 🔴 CRITICAL | Media | Salted SHA-256, NO raw phone hash |
| 9 | Vectorize cost surprise | 🟢 LOW | Baja | Pre-check Workers AI pricing |
| 10 | Beds24 cancelled bookings counted as converted | 🟡 MEDIUM | Media | Filter by booking status |

---

## 1. 🔴 BLOCKER #1: chat-to-contact.json may be missing

### El problema

`extract/messages.csv` tiene columnas: `msg_id, chat_id, sender_jid, from_me, timestamp, message_type, text`. 

**Crítico**: `chat_id` es 1, 2, 3, ... — NO es phone. Para joinear msg → phone, necesitas `chat-to-contact.json` (mentioned en HANDOFF_RDMBOT.md §13).

Si ese file:
- **No existe** → Stage A NO PUEDE arrancar
- **Está stale** (chat_id reassigned después de regenerar) → joins corruptos
- **Tiene duplicados** (mencionado en handoff §7) → CC-Data debe deduplicar primero

### Mitigation pre-flight

CC-Data Día 1 mañana **antes de cualquier procesamiento**:

```bash
cd C:\rdm-wa-api\rdm_analysis
ls extract/chat-to-contact.json && echo "EXISTS" || echo "MISSING"
python -c "import json; d = json.load(open('extract/chat-to-contact.json')); print(f'Entries: {len(d)}'); print(f'Sample: {list(d.items())[:3]}')"
```

Si MISSING → run regenerate script (existe en `stage_a_extract.py` o similar v1) o crear desde scratch:

```python
# Backup recovery from msgstore.db
import sqlite3
con = sqlite3.connect('backup-android/msgstore.db')
chat_map = {}
for row in con.execute("SELECT _id, jid_row_id FROM chat"):
    chat_id, jid_id = row
    jid_row = con.execute(f"SELECT raw_string FROM jid WHERE _id={jid_id}").fetchone()
    if jid_row:
        chat_map[chat_id] = jid_row[0]
con.close()
json.dump(chat_map, open('extract/chat-to-contact.json', 'w'))
```

**Acceptance**: chat-to-contact.json existe + cubre ≥95% de chat_ids únicos en messages.csv.

---

## 2. 🔴 CRITICAL #2: Outcome label "converted" false positives

### El problema

Plan v2 actual define:
```python
resulted_in_booking = booking exists within 90 days of last message
```

**Problema**: si cliente reservó en 2018, regresó en 2024 con conversación nueva, y reservó otra vez en 2025 dentro del 90-day window de last_msg de la conv 2024 → la conv 2024 se etiqueta `converted` incluso si NO fue causal.

**Casos problemáticos**:

| Caso | Booking | Last msg conv | Etiqueta wrong | Etiqueta correcta |
|---|---|---|---|---|
| Repeat guest, casual chat sin intent | 2024-12-15 (Beds24) | 2024-10-05 ("Feliz cumple Karina!") | `converted` | `not_converted` (chat no causal) |
| Cancelled booking | 2024-03 created/cancelled | 2024-02 (paid 33%, cancel before arrival) | `converted` | `not_converted` (no $ generated) |
| AirBnB iCal booking | direct booking AirBnB | last_msg 2023 WhatsApp | `converted` | `not_converted` (no relation) |

### Mitigation refinada

3-value enum + **causality check**:

```python
def classify_outcome(conv, bookings_df):
    phone = conv['phone']
    last_msg = conv['last_msg_at']
    
    user_bookings = bookings_df[bookings_df['phone'] == phone]
    if user_bookings.empty:
        return 'not_converted'
    
    # Window: 90 días + must be AFTER last_msg (no antes)
    booking_window = user_bookings[
        (user_bookings['first_arrival'] >= last_msg) &
        (user_bookings['first_arrival'] <= last_msg + timedelta(days=90))
    ]
    
    if booking_window.empty:
        # Wider window for indirect
        booking_180 = user_bookings[
            (user_bookings['first_arrival'] >= last_msg) &
            (user_bookings['first_arrival'] <= last_msg + timedelta(days=180))
        ]
        if booking_180.empty:
            return 'not_converted'
        # Within 90-180 days → indirect
        return 'converted_indirect'
    
    # Within 90 days — check channel + cancellation
    booking = booking_window.iloc[0]
    
    # SKIP cancelled bookings — they're NOT conversions
    if booking.get('total_paid', 0) == 0 and booking.get('status') == 'cancelled':
        return 'not_converted'
    
    # SKIP AirBnB bookings if conv was clearly WhatsApp without AirBnB transition
    if 'Airbnb' in str(booking.get('channels', '')):
        # Likely not caused by this WA conv unless conv mentions AirBnB
        if 'airbnb' not in conv.get('full_text_lower', ''):
            return 'converted_indirect'  # related but not directly caused
    
    # Direct channel within 90 days → direct conversion
    if 'Direct' in str(booking.get('channels', '')):
        return 'converted_direct'
    
    return 'converted_indirect'
```

### Validation

Sanity check post-Stage A:
- Direct conversions: should be ~5-10% of business convs (not 30%+ — that's noise)
- Indirect: ~5-15%
- Not converted: ~75-85%

Si direct > 15%: probablemente hay false positives. CC-Data flag a WC para refinar.

---

## 3. 🟡 HIGH #3: Vectorize embedding model — Spanish multilingual

### El problema

CC-Data plan menciona `@cf/baai/bge-base-en-v1.5` (768 dim, English-only).

**Pero**: nuestro corpus es **~95% español**, ~5% English (huéspedes US).

`bge-base-en-v1.5` con texto español:
- Funciona "sorta" — entiende vocab básico
- **Falla** en matices: "está libre", "fecha disponible", "para el puente" — context loss
- Worst case: similarity search devuelve irrelevant results

### Mitigación: usar modelo multilingual

Workers AI tiene:
- `@cf/baai/bge-m3` (1024 dim, multilingual, **recomendado**)
- `@cf/intfloat/multilingual-e5-large` (1024 dim, multilingual)

### Update cc-instructions-data

```bash
# WRONG (v1 propuesto):
wrangler vectorize create rdm-conversations \
  --dimensions=1024 --metric=cosine
# (Pero model usado era bge-base-en-v1.5 = 768 dim → mismatch)

# CORRECTO:
wrangler vectorize create rdm-conversations-v2 \
  --dimensions=1024 --metric=cosine
# Y usar bge-m3 multilingual para embeddings
```

Python:
```python
def get_embedding(text):
    url = f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/baai/bge-m3'
    r = requests.post(url, 
        headers={'Authorization': f'Bearer {CF_TOKEN}'},
        json={'text': text[:2048]}
    )
    return r.json()['result']['data'][0]
```

WC actualizará cc-instructions-data §6.3 next push.

---

## 4. 🟡 HIGH #4: Stage 0 false negatives — business clasificado como personal

### El problema

Algunas conversaciones son ambiguous y heurística rule-based puede equivocarse:

**Ejemplos casos confusos**:
- Conv con cliente que también es amigo personal de Alex (booking + chat casual)
- Familia extendida que reservó casa (sí business, but tonos familiares)
- Staff (Karina, Celene) — they have business chats embedded en chats personales

### Mitigation: conservative threshold + manual sample review

```python
# Conservative: prefer false_business over false_personal
# Better to include a few personal convs (filter later) than lose business

def classify_conversation(phone, chat_msgs, contact_row):
    # ... rules 1-3 as before
    
    # NEW: if borderline, default to business (conservative)
    if biz_hits >= 1 and pers_hits == 0:
        return 'business'  # ANY business signal → keep
    
    if biz_hits >= 2 and pers_hits <= 2:
        return 'business'  # business outweighs
    
    # Only strong personal signal removes
    if pers_hits >= 3 and biz_hits == 0:
        return 'personal'
    
    return 'unclear'  # → Haiku
```

Plus: **CC-Data Día 1 manual sample review**:
- Sample 100 conversations clasificadas business + 100 personal
- Manual eyeball check: ¿correcta classification?
- If >5% false negatives → refine keywords + retry

---

## 5. 🟡 MEDIUM #5: Operator persona drift over 11 años

### El problema

Corpus 2014-2025 = 11 años. Pero operator changed:
- 2014-2018: Alex solo (en alemán + español, joven)
- 2019-2022: Alex + Karina (Las Morenas)
- 2023-2025: Alex + Karina + Celene + staff expandido
- Pricing también cambió drásticamente (2017 RdM $4K/noche, 2025 $13K)

Operator playbook extracted "across all time" may capture **historical** patterns que ya NO aplican.

### Mitigation

**Weight recent years higher**:

```python
# Stratified sampling Stage C
SAMPLES_BY_YEAR = {
    2024: 0.40,   # 40% del sample (most recent + current operator)
    2023: 0.25,
    2022: 0.15,
    2021: 0.10,
    2020_earlier: 0.10,  # historical context only
}

def stratified_sample(convs, total_n=50):
    samples = []
    for year_bucket, fraction in SAMPLES_BY_YEAR.items():
        n = int(total_n * fraction)
        year_convs = convs[convs['year'].isin(year_bucket)]
        samples.append(year_convs.sample(n))
    return pd.concat(samples)
```

Plus: operator_playbook output **flags pattern era**:

```markdown
### Pattern 1.2 — Cotización con 2-3 opciones
- Converted: 15/25 (60%)
- Era: predominantly 2022-2024 (modern operator practice)
- Para bot: use this pattern (still current)

### Pattern 1.8 — Discount on first ask (anti-pattern)
- Lost: 12/25 (48%)
- Era: 2014-2018 (early operator inexperience)
- Para bot: NEVER do this (lesson learned over time)
```

---

## 6. 🟢 LOW #6: D1 batch insert size limits

### El problema

Cloudflare D1 SQL statement max size = 100 KB. Bulk insert ~6800 guests con large strings = potential overflow.

### Mitigation

Batches of 100 rows max:

```python
def bulk_insert_d1(table, rows, batch_size=100):
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        sql = build_multi_insert(table, batch)
        # Check SQL size
        if len(sql) > 90_000:  # safety margin
            # Split further
            return bulk_insert_d1(table, rows, batch_size=batch_size//2)
        wrangler_execute(sql)
```

Plus: use **prepared statements** (wrangler supports):
```bash
wrangler d1 execute rincon --remote --file=migrations/seed_guests.sql
```

NOT a problem en práctica si CC-Data sigue best practices. Monitoring required.

---

## 7. 🟡 MEDIUM #7: Funnel stage regex false positives

### El problema

Stage detection uses keywords. False positives common:

```
"¿Cuál es tu fecha de nacimiento?" → date_specified ❌ (no es booking date)
"¿Hay 4 habitaciones?" → group_specified ❌ (asking, no telling)
"$200 mil para el departamento" → price_quoted ❌ (different context)
```

### Mitigation: contextual rules + Haiku validation for ambiguous

```python
def detect_date_specified(text, conv_context):
    text_lower = text.lower()
    
    # Strong indicators (definitely booking date)
    strong = [
        r'(?:para|del|el)\s+\d{1,2}\s+(?:de\s+)?(?:enero|febrero|...)',
        r'check[- ]?in',
        r'check[- ]?out',
        r'(?:reservar|reservación)\s+para',
        r'fin\s+de\s+semana',
    ]
    
    # Weak indicators (maybe booking, maybe not)
    weak = [
        r'\d{1,2}/\d{1,2}',
        r'\bfecha\b',
    ]
    
    if any(re.search(p, text_lower) for p in strong):
        return True
    
    if any(re.search(p, text_lower) for p in weak):
        # Context check: was operator asking about booking?
        if conv_context.get('operator_recently_asked_dates'):
            return True
        # Else: probably nominal date mention
        return False
    
    return False
```

Plus: Haiku validates random 5% sample of detected transitions → quality score.

---

## 8. 🔴 CRITICAL #8: Phone hash reversibility (privacy)

### El problema

Plan menciona `phone_hash` en Vectorize metadata para evitar storing raw phone. **PERO**: si CC-Data usa simple SHA-1(phone), es trivialmente reversible:
- Phone number space: ~10 dígitos = 10^10 combinations
- SHA-1 con corpus de phones MX prefix (`+52`) → ~10^7
- Modern GPU: brute-force en horas

Esto convierte el "hash" en PII recuperable. **Privacy fail**.

### Mitigation: salted SHA-256 + secret pepper

```python
import hashlib
import os

# Pepper stored in CF env var, NEVER in code o git
PHONE_PEPPER = os.getenv('PHONE_HASH_PEPPER')  # 32 random bytes
assert len(PHONE_PEPPER) >= 32, "Pepper too short"

def hash_phone(phone_e164: str) -> str:
    """Salted hash, NOT reversible without pepper."""
    if not phone_e164:
        return None
    h = hashlib.sha256()
    h.update(PHONE_PEPPER.encode('utf-8'))
    h.update(phone_e164.encode('utf-8'))
    return h.hexdigest()[:16]  # 16-char truncated
```

CC-Data setup pre-flight:
1. Generate pepper: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Store en `.api-keys` (local only)
3. NO commit a git, NO upload a R2/D1
4. Use consistently across pipeline

**If pepper is lost**: vectors metadata becomes permanent anonymous (no way to deanonymize). That's fine. NOT a problem.

**Trade-off acknowledged**: pierde capacidad de JOIN phone_hash entre Vectorize + D1. **Aceptable** porque D1 ya tiene phone directo (guests.phone_e164), Vectorize solo necesita "agrupable por mismo cliente sin identificar quién".

---

## 9. 🟢 LOW #9: Vectorize cost surprise

### Verificación

WC searched Cloudflare docs:

| Resource | Free tier | Cost beyond |
|---|---|---|
| Vectorize storage | 5M vectors × 1024 dim free | $0.04 / 100M vector-dimensions / month |
| Vectorize queries | 30M queries/month free | $0.01 / 1M queries |
| Workers AI embeddings | 10,000 neurons/day free | varies |

Nuestro usage:
- ~6,500 vectors × 1024 dim = 6.6M dim-vectors → **dentro free tier**
- Embeddings: 6,500 × ~1 neuron each = 6,500 neurons → **dentro free tier**
- Queries (bot runtime): muy bajo volume → **dentro free tier**

**Esperado**: $0 marginal. Plan v2 budget de $0.65 era conservative.

---

## 10. 🟡 MEDIUM #10: Beds24 cancelled bookings counted as converted

### El problema

`bookings_by_phone.csv` puede incluir bookings cancelled (parcialmente pagados o full no-show). Si CC-Data trata cualquier booking como conversion, falsifica métricas.

### Mitigation

Filter en outcome classification:

```python
# Only count as conversion if booking was actually fulfilled
def is_real_booking(booking):
    paid = booking.get('total_paid', 0)
    charged = booking.get('total_charged', 0)
    
    # Cancellation: 0 paid + status = cancelled → NO conversion
    if paid == 0 and booking.get('status', '').lower() in ('cancelled', 'canceled'):
        return False
    
    # No-show: paid deposit but never arrived → NO conversion (revenue ≠ business success)
    # Hard to detect from CSV alone, skip
    
    # Partial: < 50% paid → flag for manual review
    if paid > 0 and paid < charged * 0.5:
        return 'partial'  # ambiguous
    
    return True
```

`bookings_by_phone.csv` schema may not have `status` column — verify with CC-Data Día 1.

If status missing: assume `total_paid > 0` is required for "real" conversion.

---

## 11. Resumen de acciones requeridas pre-flight

CC-Data debe verificar/ajustar antes de Day 1:

### Pre-flight checks
1. ✅ `chat-to-contact.json` existe + es current
2. ✅ Generate phone hash pepper (32 random bytes)
3. ✅ Use `@cf/baai/bge-m3` multilingual model (NO bge-base-en)
4. ✅ Outcome label uses 3-value enum + cancellation filter
5. ✅ Stage 0 uses conservative threshold

### Mid-sprint validation
6. ✅ Manual review 100 samples post-Stage 0
7. ✅ Sanity check outcome distribution post-Stage A (direct ~10%, not 30%+)
8. ✅ Haiku validation 5% sample of funnel transitions
9. ✅ Stratified sampling Stage C weighted by recent years

### Post-deploy verification
10. ✅ D1 batch insert size monitoring
11. ✅ Vectorize cost check (should be $0)
12. ✅ Test similarity search devuelve relevant results en español

---

## 12. WC honest assessment

¿El plan v2 funciona si aplicamos estos 10 mitigations? **Sí, con alta confianza**.

¿Hay riesgos que NO he anticipado? **Probablemente sí.** El más peligroso típicamente es:
- Algo en los datos que NO sospechábamos (ej: phone format inconsistencies)
- Performance bottleneck en alguna etapa (ej: Sonnet rate limits si CC-Data hace paralelos)
- D1 timeout en bulk inserts >10k rows
- Vectorize batch upload limits

Mitigación general: **fail fast + report**. CC-Data Día 1 mañana ejecuta TODO el sanity flow antes de avanzar a Eje A. Si algo huele mal, reporta a WC en thread/57.5 antes de continuar.

---

## 13. Updates a cc-instructions-data

WC actualizará `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` con:
- §6.3 Vectorize: cambiar a `bge-m3` multilingual
- §3.2 Outcome label: agregar cancellation filter + AirBnB causality
- §6.4 Privacy: agregar phone hash pepper requirement
- §3.1 Stage 0: agregar manual review step 100 samples

Update se hace en próximo turno WC.

---

**FIN thread/57**. CC-Data: leer antes de Día 1 arrancar. WC: aplicar 4 critical updates a cc-instructions-data next turn.

— Web Claude, 2026-05-15 (autonomous overnight)
