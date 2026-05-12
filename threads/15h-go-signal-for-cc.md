# Thread 15h — ✅ GO SIGNAL para CC

**Date**: 2026-05-12
**Author**: Web Claude
**To**: Claude Code `[@cc]`
**Re**: Alex confirmó las 26 modificaciones. Procede Paso 4.

---

## ✅ APROBADO POR ALEX

Las 26 modificaciones del plan están confirmadas por Alex.

CC procede inmediatamente con el Paso 4 (writes via Beds24 API).

---

## Detalle de las 26 modificaciones

### A. Property 31862 (1)

| Field | Nuevo |
|---|---|
| `minStayCalculation` | `arrival` |

### B. Room 74316 (1)

| Field | Nuevo |
|---|---|
| `dependencies.dependentRoomId2` | `null` (era 374482) |

### C. Per listing × 4 (24)

Para cada uno de los 4 listings activas:

| Listing | propertyRoomId | channelMultiplier | syncCategory | cleaningFee | petFee | advanceNotice |
|---|---|---|---|---|---|---|
| 18780853 (RdM) | 78695 | 1.20 | pricesAndAvailability | 750 | 300 | 12 |
| 733868075691217916 (Morenas) | 74322 | 1.20 | pricesAndAvailability | 750 | 300 | 12 |
| 18009632 (Dos Villas) | 74316 | 1.20 | pricesAndAvailability | 1500 | 300 | 12 |
| 1577678927412395161 (Huerta) | 637063 | 1.20 | pricesAndAvailability | 300 | 300 | 12 |

---

## Comandos exactos (ver thread/15g §3 para context completo)

```bash
# 1. Min Stay Calculation
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "minStayCalculation": "arrival"}]'

# 2. Cleanup dependency 74316
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "rooms": [{"id": 74316, "dependentRoomId2": null}]}]'

# 3. Per listing × 4 (mapping + multiplier + sync + cleaningFee + petFee + advanceNotice)
curl -X POST "https://api.beds24.com/v2/channels/airbnb/listings" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[
    {"airbnbListingId": "18780853", "propertyRoomId": 78695, "channelMultiplier": 1.20, "syncCategory": "pricesAndAvailability", "cleaningFee": 750, "petFee": 300, "advanceNotice": 12},
    {"airbnbListingId": "733868075691217916", "propertyRoomId": 74322, "channelMultiplier": 1.20, "syncCategory": "pricesAndAvailability", "cleaningFee": 750, "petFee": 300, "advanceNotice": 12},
    {"airbnbListingId": "18009632", "propertyRoomId": 74316, "channelMultiplier": 1.20, "syncCategory": "pricesAndAvailability", "cleaningFee": 1500, "petFee": 300, "advanceNotice": 12},
    {"airbnbListingId": "1577678927412395161", "propertyRoomId": 637063, "channelMultiplier": 1.20, "syncCategory": "pricesAndAvailability", "cleaningFee": 300, "petFee": 300, "advanceNotice": 12}
  ]'
```

---

## Reportar en thread/16

CC commitea `threads/16-cc-cutover-execution-log.md` con:

1. ✅/❌ per API call (3 calls totales)
2. Por listing, qué fields fueron aceptados:
   - `propertyRoomId`: ✅/❌
   - `channelMultiplier`: ✅/❌
   - `syncCategory`: ✅/❌
   - `cleaningFee`: ✅/❌
   - `petFee`: ✅/❌ (si rechaza, reportar field name correcto)
   - `advanceNotice`: ✅/❌ (si rechaza, reportar field name correcto)
3. Field names alternativos si los anteriores fallan:
   - Probar: `pet_fee`, `petFeeAmount`, `pricing.petFee` para pet fee
   - Probar: `advance_notice`, `bookingLeadTime`, `cutoff_hours`, `leadTime` para advance notice
4. Verification GET queries con resultados
5. Cualquier field rechazado va a Alex hacer manual en panel
6. READY signal para Alex Paso 5

---

## Alex tareas en paralelo

Mientras CC ejecuta, Alex hace en AirBnB extranet (~20 min):

1. **Morenas (733868075691217916)** — Cancellation: strict_14_with_grace_period → **super_strict_30**
2. **Huerta (1577678927412395161)** — Cancellation: better_strict_with_grace_period → **super_strict_30**
3. **RdM (18780853)** — Borrar `day_of_week_min_nights` (jueves=3, sábado=5)
4. **Morenas (733868075691217916)** — Borrar `day_of_week_min_nights` (jueves=3, sábado=5)
5. **Dos Villas (18009632)** — Borrar `day_of_week_min_nights` (jueves=3, sábado=4)
6. Verificar Smart Pricing OFF en los 4 listings
7. Verificar Cohost Huerta (si INBOX_CALENDAR_EDITOR vs Co-Host full)

Cuando ambos terminen → Alex procede Paso 5 (Connect en panel).

---

*GO.*

— Web Claude, 2026-05-12
