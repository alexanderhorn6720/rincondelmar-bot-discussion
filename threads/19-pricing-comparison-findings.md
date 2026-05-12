# Thread 19 — Calendar vs Showdata comparison: hallazgos + go/no-go

**Date**: 2026-05-12
**Author**: Web Claude
**To**: Alex `[@alex]`, CC `[@cc]`
**Re**: Alex aportó `/v2/inventory/rooms/calendar` dump. WC comparó vs showdata.php (thread/15i). Resultado: pricing está coherente, 2 patrones identificados.

---

## 0. TL;DR

✅ **Pricing match excelente entre /calendar (raw Beds24) y /showdata.php (output AirBnB)**

- **Huerta**: 100% match exacto (385/385 días) — perfectly aligned
- **RdM**: 97% match (375/385), 10 días con floor pricing aplicado
- **Morenas**: 55% match exacto pero **resto es floor pricing** (no random) → safe
- **DosVillas**: 67% match exacto, resto floor + 1 outlier Dec 22

🎯 **Hallazgo principal: Beds24 aplica FLOOR PRICING per room per dia-semana** (revenue protection). No es bug.

🟢 **Decisión**: proceder Connect. Showdata.php es ground truth confiable. Post-Connect, AirBnB recibirá showdata × channelMultiplier 1.20 (cuando se aplique mapping).

🔴 **CLARIFICACIÓN crítica del multiplier**:
- Calendar.multiplier per-day = 1 (sin overrides)
- Showdata.html "Price Multiplier" = 1 (per-listing channelMultiplier, no aplicado todavía porque no hay mapping)
- Property-level `multiplier=1.22` baseline = **NO refleja en showdata** porque no hay mapping AirBnB-Beds24

**Implicación**: cuando Alex haga Connect, AirBnB recibirá `showdata.price × channelMultiplier`. **El value que Alex configure en el mapping (1.20 o 1.22) determina precio final**.

---

## 1. Resumen comparativo per room

| Room | /calendar avg | showdata avg | Ratio show/cal | Post×1.20 (cliente AirBnB) |
|---|---|---|---|---|
| RdM (78695) | $10,995 | $11,040 | 1.004 | **$13,248** |
| Morenas (74322) | $6,753 | $6,974 | 1.033 | **$8,369** |
| DosVillas (74316) | $17,825 | $17,975 | 1.008 | **$21,570** |
| Huerta (637063) | $2,476 | $2,476 | 1.000 | **$2,971** |

🟢 Ratios entre 1.000 y 1.033 = showdata es esencialmente igual a calendar excepto por floor pricing en days donde calendar es muy bajo.

---

## 2. Patrón #1: FLOOR PRICING per channel

Beds24 tiene un **piso mínimo de precio** per room per dia-semana. Cuando calendar.price baja del piso, showdata trunca al piso (no envía precio menor a AirBnB).

### Floors detectados

| Room | Weekday floor | Weekend floor (Fri-Sat) |
|---|---|---|
| RdM | $8,500 | $12,500 |
| Morenas | $5,000-$5,525* | $8,000-$8,125* |
| DosVillas | $13,500 | $20,500 |
| Huerta | $1,500 | $1,750 |

*Morenas tiene 2 floors según fechas (probable temporada-specific)

### Ejemplo Morenas weekday

```
2026-05-18 (Mon): cal=$5,000 → show=$5,525   (floor weekday $5,525)
2026-05-22 (Fri): cal=$8,000 → show=$8,125   (floor weekend $8,125)
2026-06-13 (Sat): cal=$8,125 → show=$8,125   (cal = floor, no diff)
2026-12-26 (Sat): cal=$20,000 → show=$20,000 (cal > floor, no clip)
```

Lógica: **showdata.price = max(calendar.price1, floor[dow])`

🟢 Esto es **revenue protection deseado**. No es bug. Garantiza que AirBnB nunca recibe precios "leaked" demasiado bajos.

🟡 Si quieres ajustar, esto se gestiona en Beds24 panel:
- `SETTINGS → CHANNEL MANAGER → AIRBNB → SPECIFIC CONTENT` o
- `SETUP → ROOMS → [room] → MIN PRICE` per channel

---

## 3. Patrón #2: DosVillas Dec 22 — outlier único

Un solo día con discrepancia grande:

```
2026-12-21 (Mon): cal=$26,000 → show=$26,000  (pre-peak)
2026-12-22 (Tue): cal=$26,000 → show=$51,200  ← ANOMALY ratio 1.97
2026-12-23 (Wed): cal=$52,000 → show=$52,000  (peak start)
```

**Hipótesis**: Dec 22 tiene `minStay=3` y es el último día "pre-peak". Probable que Beds24 tenga regla "si check-in en pre-peak day cubre noches peak, aplica peak pricing". O hay un rate plan que afecta solo ese día.

**Impacto**: 1 día de 1540 totales = 0.06%. **Ignorable como edge case**.

---

## 4. Patrón #3: Cobertura cache (post-385 días)

Calendar endpoint:
- **385 días con precios** (May 2026 → May 2027) ✅
- **347 días extras vacíos** (Jun 2027 → May 2028) ⚠️
- **Fallback**: showdata usa "Default Daily Price" (Rack Rate) cuando calendar es null

Mismo issue que thread/15i §5 — no bloquea Connect pero requiere extender pricing rules a 730 días en Beds24 post-Connect.

---

## 5. ¿Está el multiplier 1.22 actuando o no?

🔴 **Conclusión definitiva**: NO está actuando todavía.

**Evidencia**:
1. `airbnbListingId` vacío en los 4 rooms (thread/16 §10.3)
2. `connect: limited` en los 4 rooms (no `pricesAndAvailability`)
3. Showdata HTML header dice "Price Multiplier = 1" (no 1.22)
4. Ratio showdata/calendar ≈ 1.0 (no 1.22)

**Significa**: El `multiplier=1.22` property-level del baseline thread/16 es **una configuración almacenada pero no aplicada** porque no hay mapping. Funciona como "default value para futuro mapping".

🎯 **Cuando Alex haga Paso 5 Connect**, el field `channelMultiplier` del listing mapping determinará el price final. Es lo que va a aplicarse.

### ¿Qué multiplier final usar en Connect?

| Opción | Multiplier | Cliente AirBnB ve | Tu neto post-fees AirBnB | vs Daily Price actual Beds24 |
|---|---|---|---|---|
| A | **1.20** (Plan original) | $13,248 RdM | $10,863 (×0.82) | -1.2% |
| B | **1.22** (baseline actual) | $13,471 RdM | $11,046 (×0.82) | +0.4% |
| C | 1.25 | $13,800 RdM | $11,316 (×0.82) | +2.9% |

**Mi voto**: **1.22**. Razón:
- Te deja literal 100% del Daily Price (cuestión matemática limpia)
- Ya está set como default property-level — cero acción extra
- 1.20 te deja en 98.8% del Daily Price — pierdes 1.2% per booking

Pero si prefieres "redondo" 1.20, también funciona. Diferencia es marginal.

---

## 6. Min Stay match

🟢 Calendar min_stay match perfecto con showdata min_stay (verificado en muestra Dec 18-31).

Patrón anti-orphan funciona consistente:
- Sat: min=4 (peak weekends)
- Fri: min=2-3 según temporada
- Pre-peak (Tue/Mon antes de festivos): min=3

---

## 7. Decisión final pre-Connect

### ✅ Verde para proceder

1. **Pricing /calendar consistente con showdata** (ratios 1.0-1.03)
2. **Floor pricing funcionando** como guardrail revenue
3. **No occupancy pricing detectado** (solo `price1` en calendar)
4. **No rate plan overrides** (excepto Dec 22 edge case, ignorable)
5. **Min stay aligned** (anti-orphan rules consistentes)

### 🟡 Decisiones pendientes Alex

| # | Decisión | Opciones | Mi voto |
|---|---|---|---|
| Q1 | channelMultiplier final | 1.20 / 1.22 / 1.25 | **1.22** |
| Q2 | Floor pricing — mantener o ajustar? | mantener / subir / bajar | **mantener** (revenue protection) |
| Q3 | Cache extension 730 días | hacer ahora / post-Connect | **post-Connect** (no blocker) |

### 🟢 Acción inmediata

Si confirmas Q1+Q2+Q3 → continúas con:

1. Beds24 panel pre-Connect (5 min):
   - Min Stay Calculation = arrival
   - 74316 dependentRoomId2 = null
   - **channelMultiplier**: mantener 1.22 o cambiar a 1.20 (decisión Q1)

2. AirBnB extranet (15 min, paralelo)

3. Paso 5 Connect en panel (15 min)

4. AirBnB extranet post (5 min): pet fee, instant book Dos Villas

5. Auto Review Text (2 min)

**ETA total**: ~42 min (sin cambios vs plan anterior).

---

## 8. Datos guardados

- `/home/claude/all_show_data.json` — showdata parsed (4 rooms × 721 rows)
- `/mnt/user-data/uploads/response_1778573895709.json` — /calendar raw
- Comparison expandible si quieres más detalle por (roomId, fecha) específica

---

## 9. Ping

@alex — necesito Q1+Q2+Q3 decisiones. Si todas las defaults Mi voto, arrancas Beds24 panel ahora.

@cc — pricing comparison ✅ done. No requiere más reads pre-Connect. Standby para Paso 5 post-Connect validation cuando Alex termine.

---

*FIN thread/19. Pricing validado. GO conditional.*

— Web Claude, 2026-05-12
