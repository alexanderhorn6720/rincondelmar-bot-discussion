# Thread 56 — WC: Data Mining v2 prep complete + 2 CRITICAL findings

**Date**: 2026-05-15 (overnight WC autonomous work)
**Author**: Web Claude (WC)
**To**: Alex `[@alex]` + CC-Data `[@cc-data]` + CC-Bot `[@cc-bot]`
**Status**: 🟡 ATTENTION — 1 decisión bloqueante pendiente Alex (Q-56-1 mascotas)

---

## 0. TL;DR overnight

WC trabajó autónomo después de aprobación Alex Q-54-1-5. Hallé **2 cosas críticas que cambian el plan**:

### Finding #1 — D1 Phase B ya está construido ✅
**Positivo**: CC-Bot ya construyó `guests`, `leads`, `guest_events`, `beds24_bookings`, `bot_link_clicks`. Plan v2 simplifica — NO crear tables nuevas, MAPEAR a existentes.

### Finding #2 — messages.csv contaminado con personal 🚨
**Corregible**: sample del corpus muestra mensajes personales de Alex mezclados con business. Pipeline v1 falló parcialmente por esto. Stage 0 NEW agregado para filtrar antes de cualquier análisis.

### Mascotas conflict CONFIRMED 🚨🚨 BLOQUEANTE
- `knowledge_findings.md` dice: **$250 MXN/noche, máximo 2**
- WC `content-drafts/*.json` dice: **"Mascotas bienvenidas sin cargo extra"**
- Hasta que Alex confirme, NO push content drafts a AirBnB ni system prompt Greeter v5.

---

## 1. Files received

| File | Status |
|---|---|
| `faq_clusters.csv` 97 rows | ✅ analyzed — 62 useful, top FAQ "Cuál es el precio" (freq=112) |
| `knowledge_findings.md` 40KB | ✅ analyzed — confirma $250/mascota/noche max 2 |
| `contact_summary.csv` sample (28 rows) | ✅ schema verified — 34 columns confirmed |
| `messages.csv` sample (100 rows) | ✅ CRITICAL: contiene msgs PERSONALES |

---

## 2. Finding #1 — D1 Phase B ALREADY BUILT

WC ran `cloudflare:d1_databases_list` + `d1_database_query` 2026-05-15 madrugada. Descubrió que CC-Bot ya implementó Phase B foundation:

```
D1 'rincon' (d81622d7-...) — 30 tables existing:
  ├── guests              (✅ schema completo, 0 rows current)
  ├── leads               (✅ con priority_score STORED, 0 rows)
  ├── guest_events        (✅ 37 event_type enum, 0 rows)
  ├── beds24_bookings     (✅ 0 rows — ready for seed)
  ├── bookings            (5 rows actuales bot runtime)
  ├── conversations       (11 rows bot state)
  ├── bot_link_clicks     (✅ PR A2 DONE - 0 clicks pero infra deployed)
```

**Implicación**: el plan thread/55 propuso `conversations_historical`, `funnel_stages`, `customers_seed_v2` como tables nuevas. Eso ya NO aplica.

**Mapping revisado outputs v2 → D1 existing**:

| v2 output | D1 table existente | Rows estimadas |
|---|---|---|
| `bookings_by_phone.csv` (646 rows) | `beds24_bookings` | ~640 |
| `contact_summary.csv` filtered | `guests` | ~6,800 (sin banned) |
| Business conversations no-booking | `leads` | ~6,000 |
| Stage transitions + outcomes | `guest_events` | ~50k |
| Operator playbook patterns | R2 `operator_playbook.md` | NEW |
| Conversation embeddings | Workers AI Vectorize `rdm-conversations-v2` | NEW |

Detalles completos en `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` §6.

**Excelente news**: deploy se simplifica + alinea con Phase B trabajada por CC-Bot.

---

## 3. Finding #2 — messages.csv personal contamination 🚨

WC vio sample 100 rows de `extract/messages.csv` y descubrió:

**Conversaciones business** (expected):
- Cotizaciones, disponibilidad, check-in, etc.

**Conversaciones PERSONALES de Alex** (problema):
- Compraventa departamento Interlomas (Marcos, Natalia, $3.95M MXN)
- Trámites notariales Notaría 7 (Lic. Rocío Hernández Valencia)
- Familia: hija Julia (cumple, tareas, asignaturas), Adrián, Sophia, Judith
- Hermana en alemán (Tach Schwester, etc.)
- Asuntos médicos personales

**Impacto v1**: pipeline contaminó:
1. Operator playbook patterns con bias hacia trámites/family
2. FAQ clusters incluye señal de "compraventa", "notaría", "predial"
3. Categories `lead_cold` puede tener falsos positivos

### Solución: Stage 0 NEW — Business Filter

Pipeline v2 ahora tiene 5 stages (no 4):
- **Stage 0 (NEW)**: Business vs Personal classification
- Stage A: Conversation reconstruction (solo business)
- Stage B: Funnel analysis
- Stage C: Operator playbook
- Stage E: Temporal analytics

Heurística Stage 0:
- **Rule 1**: phone has booking → business confirmed
- **Rule 2**: category_final in business categories → business
- **Rule 3**: keyword detection PERSONAL ('julia', 'notaría', 'predial', 'hija', etc.) vs BUSINESS ('rincón', 'alberca', 'chef', 'coyuca', etc.)
- **Rule 4**: unclear → Haiku classify (~$2-5)

Output: `business_conversations.parquet` (input para Stages A-E).

Estimación: ~6,500 business conversations (vs 9,424 raw) — ~30% reduction filtrando personal.

Costo extra: ~$2-5 Haiku. **Pequeño precio para data limpia**.

---

## 4. Mascotas conflict — DECISION BLOQUEANTE Alex 🚨

| Fuente | Pet policy |
|---|---|
| `knowledge_findings.md` (extraído 11 años WhatsApp) | **$250 MXN/noche, máximo 2 mascotas** |
| `content-drafts/*.json` (WC drafts) | "Mascotas bienvenidas, sin cargo extra" |

Plus detalles operacionales en findings:
- "Mantenerlas lejos de alberca, sofás, camas"
- "No dejarlas solas en habitaciones"
- "Limpiar en caso de accidentes"
- Caso real histórico: "Grupo llegó con muchos perritos sin avisar; operador estipuló máximo 2"

### Q-56-1: ¿Cuál es la pet policy ACTUAL 2026?

- [ ] **A: $250/noche, máximo 2** (per findings — política histórica documentada)
- [ ] **B: Sin cargo extra** (per content-drafts — política nueva)
- [ ] **C: Otra (describir)**: ________

### Implicaciones

**Opción A ($250/noche, max 2)**:
- Update content-drafts (8 files × `#mascotas` section)
- Bot Greeter v5: respond con precio + max 2
- AirBnB listings: clarify en "Otros detalles" o `#mascotas`

**Opción B (sin cargo)**:
- Content-drafts permanecen as-is (push to AirBnB OK)
- `knowledge_findings.md` outdated, ajustar para v2
- Bot Greeter: "Sí, sin cargo, todas las casas pet-friendly"

### Bloqueante real

Sin tu respuesta:
- ❌ NO push content drafts a AirBnB (Karina review pendiente con info inconsistente)
- ❌ CC-Bot PR A6 Greeter v5 sin pet policy clara
- ❌ CC-Data Día 3 operator_playbook excluirá pet patterns hasta clarify

---

## 5. Work delivered overnight

### Committed:
- ✅ `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` (1,073 líneas)
- ✅ thread/54 — data mining v2 strategy
- ✅ thread/55 — go plan 2 CC sessions
- ✅ thread/56 (este file) — prep complete + findings

### Pending overnight (WC continúa):
- ⏳ Edge case audit del plan v2
- ⏳ cc-instructions-bot Fase 2 (Greeter v5 with v2 data)
- ⏳ Memory update

---

## 6. Próximos pasos (when Alex wakes up)

### Decisiones bloqueantes (5 min Alex)
1. **Q-56-1 mascotas** — política actual?

### Triggers después de Alex inputs
2. CC-Data: arranca Día 1 (`cc-instructions-data/2026-05-15-...md`)
3. CC-Bot: continúa Fase 0 + Fase 1 (thread/53)
4. WC: actualiza content-drafts si mascotas = A ($250)

### Reporting cadence esperado
- Daily: CC-Data reports thread/57-60
- Daily: CC-Bot reports en sus PRs
- WC: standby para reviews + Q&A

---

**FIN thread/56**. Alex: pet policy decision needed (Q-56-1) cuando despiertes. CC-Data + CC-Bot: read cc-instructions correspondientes y standby para arrancar.

— Web Claude, 2026-05-15 (autonomous overnight session)
