# Thread 15i — Análisis precios Beds24 → AirBnB + tarea CC comparar con AirBnB calendar

**Date**: 2026-05-12
**Author**: Web Claude
**To**: CC `[@cc]`, Alex `[@alex]`
**Re**: Alex obtuvo dumps de `/api/airbnb.com/showdata.php?roomid=X` (Beds24 muestra lo que pretende exportar). WC parseó los 4. CC debe comparar con AirBnB `/calendar` API.

---

## 0. TL;DR

Beds24 expone los precios **que va a enviar a AirBnB** vía endpoint `showdata.php`. Alex obtuvo dumps de los 4 listings. WC parseó.

**Hallazgos importantes**:

1. 🔴 **Multiplier=1** en los 4 listings hoy. Después del Connect cuando CC ejecute mapping 1.20, todos los precios se multiplicarán en +20%
2. 🟡 **Cache de precios cubre solo 385 días** (May 2026 → May 2027). Días 1 Jun 2027+ usan Default Daily Price (rack rate, mucho menor)
3. 🟢 Patrones pricing matchean expectativas: weekend uplift ~25-30%, high-season Dec/Apr/Mar
4. 🔴 **Default Daily Price Combinada = $10,000** (vs hoy avg $17,975). Cuando se acaba el cache, precio cae 44%
5. 🟡 **Min Stay rules anti-orphan visibles**: sábado=4 confirmed (55 días), jueves=3 en 51 días (RdM/Morenas/DosVillas)

CC debe ahora hacer comparación con AirBnB calendar API para validar que post-Connect precios matcheen.

---

## 1. Multiplier — estado actual vs post-Connect

| Listing | Multiplier hoy | Multiplier post CC Paso 4 | Diff |
|---|---|---|---|
| RdM_78695 | 1 | **1.20** | +20% |
| Morenas_74322 | 1 | **1.20** | +20% |
| DosVillas_74316 | 1 | **1.20** | +20% |
| Huerta_637063 | 1 | **1.20** | +20% |

🔴 **Implicación**: Después de que CC ejecute el mapping con `channelMultiplier=1.20`, **todos los precios visibles en AirBnB subirán 20%**. Esto es esperado y compensa el host-only fee 15.5%+IVA.

---

## 2. Avg pricing per listing (lo que Beds24 va a enviar)

| Listing | Avg hoy enviado | Post 1.20 | Post fees (~+5% ISH) | vs default daily |
|---|---|---|---|---|
| RdM_78695 | $11,040 | $13,248 | ~$13,911 | $5,500 (rack) |
| Morenas_74322 | $6,974 | $8,369 | ~$8,788 | $3,500 (rack) |
| DosVillas_74316 | $17,975 | $21,570 | ~$22,649 | $10,000 (rack) |
| Huerta_637063 | $2,476 | $2,971 | ~$3,120 | $1,500 (rack) |

🟢 **Análisis**: estos serían los precios visibles para guest AirBnB post-Connect. Si quieres validar que matcheen tu modelo económico, valida vs lo que cobras hoy con split-fee.

Ejemplo cálculo neto para ti (post-host-only switch):
- DosVillas avg $21,570 visible AirBnB
- AirBnB cobra 15.5% + IVA = 17.98% fee → tú recibes $21,570 × 0.82 = **$17,687 neto**
- Tu Daily Price hoy Beds24 = $17,975
- Diff: -$288 (~1.6% menos que enviar precio directo, **pero AirBnB ya promociona y trae cliente**)

🟢 **Multiplier 1.20 es correcto**: tu neto post-AirBnB es ~match con tu daily price actual (diff <2%).

---

## 3. Pricing por día de semana — patrón confirmado

### RdM (78695)
| Día | Avg | Median | Min | Max |
|---|---|---|---|---|
| Lun-Jue | $9,700-$10,000 | $8,500 | $8,500 | $32,000 (peak) |
| Vie-Sáb | $13,636-$13,836 | $12,500 | $12,500 | $32,000 |
| Dom | $10,327 | $8,500 | $8,500 | $32,000 |

Weekend uplift: **~28%** sobre weekday median ($8,500 → $12,500).

### Morenas (74322)
| Día | Avg | Median |
|---|---|---|
| Lun-Jue | $6,000-$6,300 | $5,525 |
| Vie-Sáb | $8,776-$8,890 | $8,125 |
| Dom | $6,477 | $5,525 |

Weekend uplift: **~47%** ($5,525 → $8,125).

### DosVillas (74316)
| Día | Avg | Median |
|---|---|---|
| Lun-Jue | $15,700-$16,200 | $13,600 |
| Vie-Sáb | $22,376-$22,695 | $20,500 |
| Dom | $16,671 | $13,600 |

Weekend uplift: **~51%** ($13,600 → $20,500).

### Huerta (637063)
| Día | Avg | Median |
|---|---|---|
| Lun-Jue | $2,155-$2,282 | $2,000 |
| Vie-Sáb | $3,050-$3,091 | $3,000 |
| Dom | $2,336 | $2,000 |

Weekend uplift: **~50%** ($2,000 → $3,000).

🟢 **Patrones consistentes**: las 4 listings tienen weekend uplift ~30-50%, lo cual matchea expectativas vacation rental Acapulco (semana corta visitors).

---

## 4. Min Stay — anti-orphan rules en Beds24 (idénticas los 4 listings)

| Día | Distribución min_stay observada |
|---|---|
| Lun | 45d=2, 9d=3, 1d=4 |
| Mar | 48d=2, 6d=3, 1d=4 |
| Mié | 49d=2, 4d=3, 2d=4 |
| Jue | **51d=2, 2d=3, 2d=4** ⚠️ |
| Vie | 45d=2, 8d=3, 2d=4 |
| **Sáb** | **55d=4 (TODOS)** ✅ |
| Dom | 42d=2, 12d=3, 1d=4 |

🟢 **Confirmado**: sábado=4 noches mínimo aplicado consistentemente (55 sábados).
🟡 **Discrepancia**: thread/15g §6 dije que AirBnB tiene jueves=3 / sábado=5. Beds24 tiene **jueves=2 (default) / sábado=4**. Beds24 va a pushear lo suyo post-Connect.

**Implicación**: tu memoria "martes=3, sábado=4" no se ve en data. Lo que ves es **sábado=4** uniforme + algunas excepciones puntuales (Semana Santa, Diciembre, etc.) donde aumenta a 3-4.

---

## 5. Cache de precios — 385 días cubiertos, 336 días con fallback

🔴 **PROBLEMA POTENCIAL**:

| Listing | Días con precio (hasta) | Días sin precio (a partir) | Fallback default |
|---|---|---|---|
| RdM | 12 May 2026 → 31 May 2027 (385d) | 1 Jun 2027 → fin (336d) | $5,500 (vs avg $11,040) |
| Morenas | idem | idem | $3,500 (vs avg $6,974) |
| DosVillas | idem | idem | **$10,000 (vs avg $17,975 — diff $7,975)** 🔴 |
| Huerta | idem | idem | $1,500 (vs avg $2,476) |

🔴 **Impacto**: cliente que busca reserva post-junio 2027 verá:
- **DosVillas a $10,000/noche × 1.20 = $12,000** (vs $21,570 average)
- Si reserva, pierdes ~$9,500/noche

**Acción WC sugiere**:
1. Verificar si Beds24 extiende el cache automáticamente (cron job interno?) o requiere acción manual
2. Si manual, Alex debe extender el horizon de pricing rules a 730 días en Beds24

🟡 Pero **no es bloqueante** para Connect hoy (cliente puede reservar pre-junio 2027 sin issue).

---

## 6. High-season detection

### DosVillas — TOP 30 fechas más caras

| Fecha | Precio | Min Stay |
|---|---|---|
| **Dec 23-Dec 31 + Jan 1-2 2026/27** | **$52,000** | 4 noches |
| Dec 22 2026 | $51,200 | 3 noches |
| Mar 27-Apr 3 2027 (Semana Santa) | $29,500 | 3-4 noches |
| Dec 18-21 2026 | $26,000 | 3-4 noches |
| Sep 12-16 2026 (Independencia) | $24,500 | 3-4 noches |
| Apr 4-10 2027 (Pascua) | $24,500 | 3-4 noches |

🟢 **Patrón muy bueno**: high-season pricing significativo (3-4x normal day rate). Vacaciones cubiertas.

### Top meses por avg pricing (RdM como ejemplo)

| Mes | Avg | Min | Max |
|---|---|---|---|
| **Dec 2026** | $17,048 | $8,500 | $32,000 |
| Apr 2027 | $11,667 | $8,500 | $18,000 |
| Mar 2027 | $11,290 | $8,500 | $18,000 |
| Jan 2027 | $11,242 | $8,500 | $32,000 |
| Feb 2027 | $10,786 | $8,500 | $14,500 |

Diciembre es el TOP mes en los 4 listings.

---

## 7. Tarea CC — Comparar Beds24 vs AirBnB calendar API

🎯 **OBJETIVO**: Validar que lo que Beds24 muestra que va a enviar (showdata.php) matchea con lo que AirBnB realmente tiene CONFIGURADO HOY en su calendar via API.

### 7.1 Endpoint AirBnB API (vía Beds24)

CC busca endpoint de AirBnB que devuelva calendar/pricing actual. Opciones:

**Opción A — vía Beds24 API v2**:
```bash
# Endpoint legacy que se documentó intentos en thread/15e
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/calendar?listingId=18780853" \
  -H "token: $TOKEN"

# O variantes:
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings/18780853/calendar" -H "token: $TOKEN"
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings?airbnbListingId=18780853&includeCalendar=true" -H "token: $TOKEN"
```

**Opción B — AirBnB API directa** (probablemente NO accesible sin OAuth especial):
```bash
# La integración Beds24-AirBnB usa partner OAuth
# Beds24 maneja el token, no es exponible al cliente
# Si está disponible, sería algo como:
curl -sX GET "https://api.airbnb.com/v2/listings/18780853/calendar?start_date=2026-05-12&end_date=2027-05-31" \
  -H "Authorization: Bearer $AIRBNB_PARTNER_TOKEN"
```

**Opción C — public AirBnB calendar (sin auth, scrape)**:
- AirBnB tiene endpoint público para search results pero precios incluyen fees, taxes
- Puede ser noisy para comparación exacta
- Probable que AirBnB lo rate-limit

**Recomendación CC**: empezar con Opción A (sin docs explícitos, probar endpoints), si no funciona moverse a investigación de qué tiene Beds24 en /channels/airbnb que exponga calendar.

### 7.2 Data a extraer per listing × 4

Por listing, para próximos 30-90 días (sample suficiente):
- Date
- Price (lo que AirBnB tiene hoy)
- Min stay AirBnB
- Available / blocked status

### 7.3 Comparación esperada vs encontrada

CC debe crear tabla de 3 columnas comparativa per listing:

| Date | Beds24 sendrá (×1.20 post-Connect) | AirBnB tiene hoy | Diff | Issue? |
|---|---|---|---|---|
| 12 May 2026 | $10,200 (8500×1.20) | $? | $? | OK/discrepancia |
| 15 May 2026 (vie) | $15,000 (12500×1.20) | $? | $? | OK/discrepancia |

### 7.4 Output thread/16 (o thread/17)

CC commitea con:
- Endpoint que funcionó (o cuáles fallaron)
- Tabla comparativa per listing × 4 (próximos 30+ días)
- Hallazgos:
  - ¿Beds24 está enviando lo que dice showdata.php? (ya hizo push silencioso vía iCal mode?)
  - ¿AirBnB tiene precios diferentes a lo que vamos a pushear?
  - Si discrepancia grande, ¿es por multiplier (queda en 1.0 hoy) o por cambios manuales en AirBnB?

### 7.5 Importancia

🎯 Esta comparación nos permite **predecir exactamente qué cambiará visualmente** post-Connect:

- Si AirBnB hoy tiene precios MUY diferentes a Beds24, el Connect causará **shock pricing** para guests que ven el calendar
- Si matchea (excepto por multiplier), el Connect es transparente
- Si discrepancia >20%, hay que investigar antes (¿manual edits AirBnB? ¿Beds24 ya sincroniza con iCal?)

---

## 8. Action items para CC

@cc — antes de proceder Paso 4 writes (mapping + multiplier + etc.):

1. **Investigar API endpoint** que devuelva AirBnB calendar actual (sección 7.1)
2. **Extraer próximos 30-90 días** per listing × 4 (sección 7.2)
3. **Comparar con data del thread/15i §3 (showdata)** considerando multiplier 1.0 actual
4. **Commit** `threads/16-cc-pricing-comparison.md` con tabla comparativa
5. **Reportar findings**:
   - ✅ Matchean (excepto por multiplier 1.0 vs futuro 1.20)
   - 🟡 Discrepancias menores (<5%)
   - 🔴 Discrepancias grandes (>20%) — pause Connect y revisar

Una vez done thread/16, WC analiza si hay riesgo y decide proceder o ajustar.

---

## 9. Cobertura cache extensión — issue paralelo

🟡 **Pre-Connect Alex sugerido investigue**:

Beds24 cache cubre 385 días. Cliente busca reserva Diciembre 2027 → ve $5,500 RdM × 1.20 = $6,600 (vs avg real $11,040).

**Acciones**:
1. ¿Cómo extender pricing rules a 730 días?
2. ¿Beds24 hace esto automático via cron interno?
3. ¿O Alex debe actualizar manualmente Daily Price Rules con horizonte mayor?

🟢 No es blocker hoy pero conviene resolver post-Connect.

---

## 10. Decisión Alex pendiente

❓ **Q1**: ¿Procedo con Connect hoy con cache 385 días (riesgo post-Jun 2027), o esperamos extender cache a 730 días primero?

**Mi voto**: **Proceder con Connect hoy**. 385 días cubre toda la temporada 2026-2027. Los issues post-Jun 2027 son edge cases (clientes raros que reservan con 13+ meses anticipación) y se pueden resolver con un cron Beds24 después.

❓ **Q2**: ¿CC investiga API AirBnB calendar **antes** o **después** del Paso 4?

**Mi voto**: **Después**. Hoy ya tenemos showdata.php que es ground truth de lo que Beds24 enviará. La comparación con AirBnB es validación post-Connect (confirma que sync realmente funcionó).

---

## 11. Resumen ejecutivo

✅ **Beds24 está listo para pushear precios correctos** (showdata.php data clean)

✅ **Multiplier 1.20 reflejará en precios ~20% más altos** post-Connect (esperado)

🟡 **Cache 385 días**: cubre temporada inmediata, atender post-Jun 2027 después

🟢 **Min stay rules**: sábado=4 + jueves=3 puntual + 2 default — anti-orphan funcionando

🎯 **CC tarea siguiente**: comparar con AirBnB calendar API para validación post-Connect

---

*FIN thread/15i. Data parseada. CC valida pricing comparison.*

— Web Claude, 2026-05-12
