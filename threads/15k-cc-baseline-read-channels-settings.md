# Thread 15k — Endpoint nuevo: GET /v2/channels/settings (baseline pre-Paso 4)

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]`
**Re**: Alex confirmó endpoint Beds24 que devuelve config completa del canal AirBnB per property. CC debe leer baseline ANTES de los writes Paso 4.

---

## 0. Por qué importa

Endpoint `/v2/channels/settings?propertyId=31862&channel=airbnb` devuelve la configuración **actual completa** del canal AirBnB para esa property + sus rooms.

**Beneficios para Paso 4**:

1. ✅ **Baseline pre-mutación**: tenemos snapshot exacto de la config actual antes de tocar nada
2. ✅ **Field names correctos**: en vez de adivinar `cleaningFee` vs `cleaning_fee` vs `petFeeAmount`, vemos qué nombres devuelve la response
3. ✅ **Validación post-Paso 4**: hacer el mismo GET después de los writes y comparar diff
4. ✅ **Detectar fields no documentados** (e.g. `dependentRoomId`, internal links, etc.)

---

## 1. Comando

```bash
curl -X GET "https://api.beds24.com/v2/channels/settings?propertyId=31862&channel=airbnb" \
  -H "accept: application/json" \
  -H "token: $BEDS24_TOKEN"
```

Token: usa el de datastore Make `85380` key `main` (auto-refresh activo). Si CC tiene problemas con ese, Alex provee uno fresh en la conversación con WC.

---

## 2. Tarea CC (PRE-Paso 4)

### 2.1 Ejecutar GET

Una sola llamada (no por listing, el endpoint es per property y devuelve todos los rooms mapeados).

### 2.2 Parsear y extraer per room (78695 / 74322 / 74316 / 637063)

Estructura esperada (basada en patrón Beds24 v2):
- `propertyId`: 31862
- Top-level property settings (minStayCalculation, etc.)
- `rooms[]` array con per-room:
  - `roomId`
  - `airbnbListingId`
  - `channelMultiplier`
  - `syncCategory` (currently iCal-mode, probable empty/null)
  - `cleaningFee` / `cleaning_fee` / `petFee` / `petFeeAmount` etc. (**estos son los que necesitamos confirmar field names**)
  - `dependentRoomId`, `dependentRoomId2`
  - `connected` boolean
  - Otros campos no documentados

### 2.3 Commit `threads/16-cc-cutover-execution-log.md` con secciones:

**Sección 0 — Baseline pre-Paso 4** (NUEVA, agregar antes de los writes):
- Output completo del GET (formateado JSON)
- Tabla resumen per room: roomId | airbnbListingId | multiplier actual | syncCategory actual | cleaningFee actual | petFee actual | advanceNotice actual | dependentRoomId | dependentRoomId2

**Sección 1 — Field name mapping confirmado**:
Antes de los writes, listar:
- `cleaningFee` → field name real que usa Beds24
- `petFee` → field name real
- `advanceNotice` → field name real
- `channelMultiplier` → confirmado
- `syncCategory` → confirmado (probable que current=null o `ical`)
- `propertyRoomId` → confirmado o alternativa

**Sección 2 — Writes Paso 4**:
- Comando 1 (minStayCalculation)
- Comando 2 (cleanup dependentRoomId2 de 74316)
- Comando 3 (mapping × 4 con field names ya validados de §1)

**Sección 3 — Verification post-writes**:
- GET `/v2/channels/settings` otra vez
- Diff vs baseline (Sección 0)
- Tabla comparativa antes/después per room

---

## 3. Hallazgos esperados (predicciones WC)

Basado en wiki + thread/15i análisis:

| Campo | Pre-Paso 4 esperado | Post-Paso 4 esperado |
|---|---|---|
| `channelMultiplier` por room | 1.0 | 1.20 |
| `syncCategory` | `null` o `ical` | `pricesAndAvailability` |
| `cleaningFee` per room | $0 o whatever AirBnB-side currently | 750/750/1500/300 |
| `petFee` | $0 o $250/300 mix actual AirBnB | 300 uniforme |
| `advanceNotice` | 0h o 12h mix | 12 uniforme |
| `minStayCalculation` (property) | undefined / default | `arrival` |
| `dependentRoomId2` de 74316 | 374482 (orphan archived) | null |
| `dependentRoomId` de 74316 | 78695 o 74322 (verificar) | mantener si existe |
| `connected` per room | `false` (todavía iCal-mode) | `false` hasta Paso 5 Alex panel |

🔴 **Importante**: `connected` permanece `false` hasta que Alex presione "Connect" en panel Beds24 (Paso 5). Los writes Paso 4 solo PREPARAN el mapeo, no ejecutan el Connect automáticamente.

---

## 4. Casos edge a buscar en response

1. **Hidden fields no documentados**: `priceLastSent`, `lastSyncAt`, `pendingChanges`, etc. → reportar si existen
2. **Error fields**: `lastError`, `errorMessage`, `quotaUsage` → si Beds24 devuelve estado de health del canal
3. **Internal Beds24 linking**: ¿hay un campo que indique si hay calendar linking AirBnB-side detected? Si sí, valioso para CRITICAL #1 del wiki review
4. **Auto Review Template**: ¿campo `autoReviewText`? Si está expuesto vía API, Alex puede setearlo via API en vez de panel manual

---

## 5. Decision tree post-baseline read

| Caso | Acción |
|---|---|
| Baseline coincide con predicción WC §3 | ✅ Proceder writes Paso 4 con field names confirmados |
| Field name diferente (`cleaning_fee` vs `cleaningFee`) | Ajustar JSON antes del write, sin pausar |
| Field rejected por API (no existe) | Reportar a Alex, ese setting va al panel Beds24 manual |
| `connected: true` ya en algún room | 🔴 STOP — investigar, no debería estar connected todavía |
| `dependentRoomId` de 74316 = 78695 o 74322 | Mantener (es el link entre Combinada y RdM/Morenas) |
| `dependentRoomId2` ≠ 374482 (algo más raro) | Reportar antes del cleanup |

---

## 6. Output esperado de CC

CC commitea `threads/16-cc-cutover-execution-log.md` con TODO el flow:
1. Baseline (esta tarea)
2. Field name mapping confirmado
3. Writes ejecutados con resultados
4. Verification post-writes (diff vs baseline)

ETA: ~20 min (baseline + writes + verify).

Una vez done, WC valida thread/16 y Alex procede Paso 5 panel Connect.

---

## 7. Token note

Token: usar de datastore Make `85380` key `main`. Auto-refresh activo (cron 12h).

Si CC encuentra 401/403:
- Datastore puede tener token expirado
- Alex pasará uno fresh directo a WC vía chat
- WC actualizará datastore primero antes de retry

---

*Endpoint key: este es el read que faltaba antes de Paso 4. Con esto sabemos qué tocar exactamente.*

— Web Claude, 2026-05-12
