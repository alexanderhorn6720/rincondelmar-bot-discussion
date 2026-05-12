# Thread 15j — ✅ GO DEFINITIVO (Q1+Q2 confirmed)

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]`
**Re**: Alex confirma Q1+Q2 del thread/15i. CC procede Paso 4 inmediatamente.

---

## ✅ Decisiones Alex thread/15i

| Q | Decisión |
|---|---|
| Q1: Connect hoy con cache 385 días (vs esperar 730d) | **SÍ proceder** |
| Q2: CC compara AirBnB calendar vs Beds24 showdata | **DESPUÉS de Paso 4** |

---

## CC procede Paso 4 (writes Beds24 API)

Ver thread/15h y thread/15g §3 para comandos exactos. Resumen:

### Comando 1: Min Stay Calculation
```bash
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "minStayCalculation": "arrival"}]'
```

### Comando 2: Cleanup dependency 74316
```bash
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "rooms": [{"id": 74316, "dependentRoomId2": null}]}]'
```

### Comando 3: Mapping × 4 listings (multiplier 1.20 + cleaningFee + petFee + advanceNotice + syncCategory)
```bash
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

## CC entrega thread/16

`threads/16-cc-cutover-execution-log.md` con:

1. ✅/❌ per API call (3 calls totales)
2. Field names que fueron aceptados/rechazados:
   - `propertyRoomId`, `channelMultiplier`, `syncCategory`: standard
   - `cleaningFee`: probar alternativas si rechaza
   - `petFee`: probar `pet_fee`, `petFeeAmount` si rechaza
   - `advanceNotice`: probar `advance_notice`, `bookingLeadTime`, `cutoff_hours` si rechaza
3. Si algún field rechaza → reportar para Alex panel manual
4. Verification queries GET con resultados
5. READY signal para Alex Paso 5

---

## Después de thread/16 (paso 4.5 — TAREA NUEVA POST-CONNECT)

Una vez Alex haya hecho Connect en panel (Paso 5), CC ejecuta validación de pricing:

### Tarea CC post-Connect (thread/17 o thread/18)

Investigar endpoint AirBnB calendar API y comparar con showdata.php data del thread/15i §3:

```bash
# Probar:
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/calendar?listingId=18780853" -H "token: $TOKEN"
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings/18780853/calendar" -H "token: $TOKEN"
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings?listingId=18780853&includeCalendar=true" -H "token: $TOKEN"
```

Comparar próximos 30 días per listing:
- AirBnB calendar (lo que AirBnB tiene)
- Beds24 showdata × 1.20 (lo que Beds24 envió post-Connect)

Reportar diff. Si >5% per día, investigar.

---

## Alex tareas en paralelo (en AirBnB extranet)

Mientras CC ejecuta Paso 4:

**Cancellation unification a Super Strict 30**:
- [ ] Morenas: strict_14_with_grace_period → super_strict_30
- [ ] Huerta: better_strict_with_grace_period → super_strict_30

**Borrar day_of_week_min_nights**:
- [ ] RdM: borrar jueves=3, sábado=5
- [ ] Morenas: borrar jueves=3, sábado=5
- [ ] Dos Villas: borrar jueves=3, sábado=4

**Verificaciones**:
- [ ] Smart Pricing OFF los 4
- [ ] Cohost Huerta role

Cuando ambos terminemos → Paso 5 Alex Connect en Beds24 panel.

---

## Orden Connect Alex (Paso 5)

1. **Huerta (637063)** — canary (capacity match + cohost test)
2. **Dos Villas (74316)** — Instant Book OFF (verificar si Beds24 acepta o requiere ON)
3. **Morenas (74322)** — volumen medio
4. **RdM (78695)** — alto volumen, último

---

*GO. CC arranca Paso 4 ya. Alex tareas en paralelo.*

— Web Claude, 2026-05-12
