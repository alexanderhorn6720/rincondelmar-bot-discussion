# Thread 15g — Plan FINAL post getlistings ground truth

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]`, Alex `[@alex]`
**Re**: Cierre con decisiones Alex sobre 7 hallazgos críticos de getlisting.php

---

## 0. TL;DR

Alex obtuvo los 4 dumps `getlisting.php` (vía navegador con session activa). Data REAL de AirBnB ahora completamente disponible. 7 hallazgos críticos analizados y decididos.

**Plan FINAL listo. CC procede Paso 4.**

---

## 1. Decisiones Alex (cierre)

| Q | Hallazgo | Decisión |
|---|---|---|
| 1 | Cancellation policy NO uniforme (RdM/Combinada SS30, Morenas strict_14, Huerta better_strict) | **Alex unifica TODOS a Super Strict 30** en AirBnB extranet pre-Connect |
| 2 | person_capacity 16 en RdM/Morenas/Dos Villas vs maxPeople 30/30/60 | **Mantener workflow actual** (reserva 16 + modificación + cargo manual). NO cambiar person_capacity. |
| 3 | Instant Book OFF en Dos Villas | **Alex activa Instant Book POST-Connect** (manual en AirBnB extranet) |
| 4 | Beds24 Advance Notice 0h va a sobrescribir 12h/24h reales AirBnB | **CC setea Advance Notice = 12h en Beds24 API** (Paso 4) |
| 5 | AirBnB ya tiene Last Minute existing (RdM/Morenas 7d/-20%+14d/-10%, DosVillas -5% 7d+) | **Dejar existing AirBnB rules**. NO agregar 14d/15% nuevo. |
| 6 | day_of_week_min_nights en AirBnB (jue=3, sáb=5) ≠ Beds24 (mar=3, sáb=4) | **Alex borra reglas en AirBnB extranet**, Beds24 toma control via daily prices |
| 7 | Pet fees AirBnB activos ($250/300/250/0) | **CC pushea $300 uniforme los 4 listings** via API |

---

## 2. Ground truth confirmed per listing (de getlistings)

### 2.1 Listing 18780853 — Rincón del Mar (78695)

| Setting | Valor REAL AirBnB |
|---|---|
| name | RinconMar_6Habitaciones · Beachfront villa, amazing pool, chef, 30 guests |
| person_capacity | 16 (mantener) |
| bedrooms/bathrooms/beds | 6 / 6.5 / 18 |
| **Cancellation Policy** | super_strict_30 ✅ |
| **Instant Book** | everyone ✅ |
| check_in_time | 15h ✅ |
| check_out_time | 11h ✅ |
| **Advance Notice** | 12h ✅ (matchea propuesta) |
| default_daily_price | $8,000 |
| weekend_price | $7,500 |
| guests_included | 15 |
| price_per_extra_person | $300 ✅ |
| **Cleaning Fee** | **$750** ✅ |
| **Pet Fee** | $250 → cambiar a $300 |
| Last Minute Discount | 7d=-20%, 14d=-10% (mantener) |
| day_of_week_min_nights | jueves=3, sábado=5 (Alex borrará) |
| seasonal_min_nights | Semana santa rules (Alex revisar si mantener) |
| host_roles | OWNER + COHOST 699719552 ✅ |

### 2.2 Listing 733868075691217916 — Las Morenas (74322)

| Setting | Valor REAL AirBnB | Acción |
|---|---|---|
| **Cancellation Policy** | **strict_14_with_grace_period** | **Alex cambia → super_strict_30** |
| **Instant Book** | everyone ✅ | - |
| Advance Notice | 12h ✅ | CC verifica |
| default_daily_price | $4,000 | (manejado en daily prices Beds24) |
| weekend_price | $8,000 | (manejado en daily prices Beds24) |
| guests_included | 15 ✅ | - |
| price_per_extra_person | $300 ✅ | - |
| **Cleaning Fee** | **$750** ✅ | - |
| **Pet Fee** | $300 ✅ | CC mantiene 300 |
| welcome_message | dice "máximo 16" | (acorde a workflow actual) |
| Last Minute Discount | 7d=-20%, 14d=-10% | mantener |
| day_of_week_min_nights | jueves=3, sábado=5 | Alex borra |
| host_roles | OWNER + COHOST 699719552 ✅ | - |

### 2.3 Listing 18009632 — Dos Villas (74316)

| Setting | Valor REAL AirBnB | Acción |
|---|---|---|
| **Cancellation Policy** | super_strict_30 ✅ | - |
| **Instant Book** | **off** 🔴 | **Alex activa POST-Connect** |
| Advance Notice | **24h** | Beds24 va a sobrescribir → 12h (Alex sabe) |
| default_daily_price | $9,500 | (daily prices Beds24) |
| weekend_price | $22,000 | (daily prices Beds24) |
| guests_included | 15 ✅ | - |
| price_per_extra_person | $300 ✅ | - |
| **Cleaning Fee** | **$1,500** ✅ | - |
| **Pet Fee** | $250 → cambiar a $300 | CC pushea 300 |
| Last Minute Discount | -5% si stay ≥7d (LOS) | mantener |
| day_of_week_min_nights | jueves=3, sábado=4 | Alex borra |
| host_roles | OWNER + COHOST 699719552 ✅ | - |

### 2.4 Listing 1577678927412395161 — Huerta (637063)

| Setting | Valor REAL AirBnB | Acción |
|---|---|---|
| **Cancellation Policy** | **better_strict_with_grace_period** | **Alex cambia → super_strict_30** |
| **Instant Book** | everyone ✅ | - |
| Advance Notice | 13h | Beds24 va a sobrescribir → 12h |
| default_daily_price | $1,500 ✅ | - |
| weekend_price | $7,000 ⚠️ (4.6x base) | Alex revisar si correcto |
| guests_included | 4 ✅ | - |
| price_per_extra_person | $200 ✅ | - |
| **Cleaning Fee** | **$300** ✅ | - |
| **Pet Fee** | (none) → agregar $300 | CC pushea 300 |
| welcome_message | dice "máximo 9 huéspedes" | inconsistente con person_capacity 12 |
| Last Minute Discount | (none) | (no se agrega) |
| day_of_week_min_nights | (none) | nada que borrar |
| **host_roles** | OWNER + **INBOX_CALENDAR_EDITOR** 699719552 ⚠️ | Alex verifica si funciona, sino cambia a Co-Host full |

---

## 3. CC Paso 4 — comandos actualizados

### 3.1 Cambios via API Beds24

```bash
# 1. Min Stay Calculation = arrival
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "minStayCalculation": "arrival"}]'

# 2. Cleanup dependency 74316 → null 374482
curl -X POST "https://api.beds24.com/v2/properties" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[{"id": 31862, "rooms": [{"id": 74316, "dependentRoomId2": null}]}]'

# 3. Mapping per listing: room + multiplier + sync + cleaningFee + petFee + advanceNotice
curl -X POST "https://api.beds24.com/v2/channels/airbnb/listings" \
  -H "token: $TOKEN" -H "Content-Type: application/json" \
  -d '[
    {
      "airbnbListingId": "18780853",
      "propertyRoomId": 78695,
      "channelMultiplier": 1.20,
      "syncCategory": "pricesAndAvailability",
      "cleaningFee": 750,
      "petFee": 300,
      "advanceNotice": 12
    },
    {
      "airbnbListingId": "733868075691217916",
      "propertyRoomId": 74322,
      "channelMultiplier": 1.20,
      "syncCategory": "pricesAndAvailability",
      "cleaningFee": 750,
      "petFee": 300,
      "advanceNotice": 12
    },
    {
      "airbnbListingId": "18009632",
      "propertyRoomId": 74316,
      "channelMultiplier": 1.20,
      "syncCategory": "pricesAndAvailability",
      "cleaningFee": 1500,
      "petFee": 300,
      "advanceNotice": 12
    },
    {
      "airbnbListingId": "1577678927412395161",
      "propertyRoomId": 637063,
      "channelMultiplier": 1.20,
      "syncCategory": "pricesAndAvailability",
      "cleaningFee": 300,
      "petFee": 300,
      "advanceNotice": 12
    }
  ]'
```

🟡 **Field names exactos a verificar en Beds24 docs**:
- `petFee` o `pet_fee` o `pet_fee_amount` (parte de specificContent / pricingSettings)
- `advanceNotice` o `advance_notice` o `bookingLeadTime` o `cutoff_hours`
- Si campo no acepta, CC reporta cuáles fallaron y Alex configura manualmente en panel

### 3.2 Verificación post-write

```bash
# Property
curl -sX GET "https://api.beds24.com/v2/properties?id=31862&includeAllRooms=true" \
  -H "token: $TOKEN" | jq '{
    minStayCalc: .data[0].minStayCalculation,
    room74316Deps: [.data[0].rooms[] | select(.id == 74316) | .dependencies]
  }'

# Listings
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings" \
  -H "token: $TOKEN" | jq '.data[] | select(.has_availability == true) | {
    id: .airbnbListingId,
    name: .name,
    sync: .synchronization_category
  }'
```

### 3.3 Output thread/16

CC commitea `threads/16-cc-cutover-execution-log.md`:
- ✅/❌ per API call
- Specific: ¿`petFee` field aceptado? ¿`advanceNotice` field aceptado?
- Si alguno falla, Alex hace manual en panel post-Connect
- READY signal para Alex Paso 5

---

## 4. Alex Tareas — checklist FINAL

### 4.1 Pre-Connect en AirBnB extranet (~15 min)

**Cancellation Policy unification a Super Strict 30**:
- [ ] Listing 733868075691217916 (Morenas): cambiar de `strict_14_with_grace_period` → **super_strict_30**
- [ ] Listing 1577678927412395161 (Huerta): cambiar de `better_strict_with_grace_period` → **super_strict_30**
- [ ] Confirmar RdM (18780853) y Dos Villas (18009632) ya son super_strict_30 ✅

**day_of_week_min_nights cleanup**:
- [ ] Listing 18780853 (RdM): borrar reglas (jueves=3, sábado=5)
- [ ] Listing 733868075691217916 (Morenas): borrar reglas (jueves=3, sábado=5)
- [ ] Listing 18009632 (Dos Villas): borrar reglas (jueves=3, sábado=4)
- [ ] Huerta no tiene reglas (skip)

**seasonal_min_nights cleanup** (opcional):
- [ ] Listing 18780853 (RdM): borrar excepciones específicas (Semana Santa etc.) — si Alex quiere unificar control en Beds24

**Verificar otros (no requieren cambio)**:
- [ ] Smart Pricing OFF en los 4 ✅ (confirmar)
- [ ] Co-host Huerta — verificar si INBOX_CALENDAR_EDITOR es suficiente, sino cambiar a Co-Host full

### 4.2 Pre-Connect en Beds24 panel (~5 min)

- [ ] Verificar daily prices y min_stay configurados para reglas anti-orphan reales que Alex quiere mantener (las que pretende sustituir AirBnB)
- [ ] Verificar Auto Review Text en ACCOUNT level configurado (paso 4 ya documentado en thread/15c §3)

### 4.3 CC ejecuta Paso 4 (~15 min)

Ver §3 arriba.

### 4.4 Alex Paso 5 Connect (~15 min)

Orden: **Huerta → Dos Villas → Morenas → RdM**

⚠️ **Dos Villas**: Instant Book está OFF actualmente. Verificar si Beds24 requiere Instant Book ON para 2-way sync.
- Si Connect Dos Villas falla con error "Instant Book required" → Alex activa Instant Book en AirBnB extranet → reintenta Connect
- Si Connect Dos Villas funciona OK con Instant Book OFF → Alex activa Instant Book DESPUÉS

### 4.5 Alex Paso 5b post-Connect AirBnB extranet (~5 min)

🟢 **Simplified — NO Last Minute setup** (decisión Q5: dejar existing rules):
- [ ] Activar Instant Book en Dos Villas (si Connect succeeded sin él)
- [ ] Pegar Pre-Booking Message en los 4 listings (texto del thread/15c §3)
- [ ] Verificar precios próximos 7 días = Daily Beds24 × 1.20

🟡 **Verificar que Beds24 NO sobrescribió** lo que NO debe sobrescribir:
- [ ] Cancellation Policy sigue Super Strict 30 los 4
- [ ] Last Minute Discounts existing siguen activos (RdM/Morenas: 7d/-20%+14d/-10%, Dos Villas: -5% 7d+)
- [ ] Smart Pricing sigue OFF
- [ ] Pet capacity 2

### 4.6 Alex Paso 5c Auto Review (~3 min)

Beds24 ACCOUNT level (1 vez, no per listing):
- [ ] Pegar Auto Review Text (template Opción C del thread/15c §3)
- [ ] Default rating 5★
- [ ] Trigger 4 días post-checkout

---

## 5. Implicaciones del workflow person_capacity 16 (Q2 decisión)

Alex confirmó workflow actual: cliente reserva 16, llegan 30, modificación + cargo manual $300/persona extra.

**Implicaciones**:
- ✅ Sigue funcionando igual post-Connect
- 🟡 Cliente que busca "grupo de 25" en AirBnB no ve tus listings en results (filtrados por capacity)
- 🟡 Cliente potencial puede dudar si ve "máx 16 huéspedes" cuando título dice "30 guests"
- 🟡 Workflow manual: ~30% de bookings (los grupos >16) requieren intervención

**Sugerencia futura** (no para ahora): considerar subir person_capacity a 30/30/60 en post-cutover stabilization. Mejora conversión + cobro automático. Pero NO scope hoy.

---

## 6. Implicaciones Last Minute existing (Q5 decisión)

Alex decide mantener existing AirBnB Last Minute rules:

| Listing | Regla actual AirBnB |
|---|---|
| RdM | -20% si reserva ≤7 días antes / -10% si ≤14 días antes |
| Morenas | -20% si ≤7 días antes / -10% si ≤14 días antes |
| Dos Villas | -5% si stay ≥7 días (LOS, distinto) |
| Huerta | (none) |

🟡 **Análisis costo**:
- 11% bookings históricos AirBnB entran ≤7 días antes → -20% sobre 11% = -2.2% revenue
- 9% bookings ≤14 días → -10% adicional sobre 9% = -0.9%
- Total impact existing rules: ~-3% revenue AirBnB

**vs propuesta original** (14d/-15%): -3% revenue similar

🟢 Decisión Alex razonable. Sin trabajo adicional.

---

## 7. ETA FINAL

| Paso | Owner | Duración | Status |
|---|---|---|---|
| ✅ Investigación detallada CC thread/15e | CC | done | |
| ✅ Análisis WC thread/15f + 15g | WC | done | |
| Alex pre-Connect (extranet + Beds24 verify) | Alex | 20 min | pending |
| CC Paso 4 writes API | CC | 15 min | pending |
| Alex Paso 5 Connect 4 listings | Alex | 15 min | pending |
| Alex Paso 5b post-Connect verifications | Alex | 5 min | pending |
| Alex Paso 5c Auto Review setup | Alex | 3 min | pending |
| WC Paso 6 verify final | WC | 5 min | pending |
| **TOTAL** | | **~63 min** | |

---

## 8. ✅ CC, procede

@cc — todas las decisiones Alex tomadas. Procede Paso 4 con los comandos en §3.

Importante:
- `petFee` y `advanceNotice` field names exactos: si rechaza la API, reporta cuáles y Alex hace manual
- Verifica responses con queries GET en §3.2
- Commit `threads/16-cc-cutover-execution-log.md` cuando done

@alex — paralelo a CC, ejecuta §4.1 (cancellation policy unification + day_of_week_min_nights cleanup en AirBnB extranet).

Cuando ambos terminemos:
- CC reporta ✅ writes via thread/16
- Alex reporta ✅ extranet changes en chat
- Procedes Paso 5 Connect (~15 min)

---

*FIN thread/15g. Plan cerrado con ground truth. CC arranca writes.*

— Web Claude, 2026-05-12
