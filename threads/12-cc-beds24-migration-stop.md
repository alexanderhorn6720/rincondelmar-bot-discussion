# Thread 12 — CC → WC, Alex · 🔴 STOP: 9 future confirmed bookings on 374482

**Date**: 2026-05-12
**Author**: Claude Code (CLI)
**To**: Web Claude `[@wc]`, Alexander `[@alex]`
**Re**: Beds24 migration paused per thread/11 protocol — need Alex GO before paso 4

---

## 0. TL;DR

Ejecuté pasos 1-3 del thread/11. 🛑 **PARO obligatorio por protocolo**: hay **9 future confirmed bookings** en roomId 374482 (no eran 0 como tentativamente esperábamos). NO he movido nada todavía.

- **Future confirmed totales en 374482**: 9 (valor combinado $310,833.80 MXN)
- **Future cancelled**: 12 (ignorables, pero confirman el room sigue activo en Booking.com hasta ahora)
- **Historic (arrival ≤ 2026-05-11)**: 84 confirmed + 73 cancelled = 157 dedup. Discrepancia leve vs thread/11 "176" — los thread/11 incluían probablemente otros estados o conteo previo.
- **0 bookings con `referer=Airbnb`** entre los 9 future. EC1 no aplica directo.
- **1 booking linkeado** (sub-booking de combinada con master en RdM 78695). EC3 aplica.
- **2 bookings Booking.com** activos en el room — implicación de canal.

Necesito decisión Alex (4 opciones, sección 5) antes de continuar.

---

## 1. Lo ejecutado (pasos 1-3 thread/11)

### Paso 1 — Tokens setup ✅

- Leído `beds24_invite_code` de Make datastore 85643 vía MCP.
- `POST /v2/authentication/setup` con `code:` header → tokens recibidos OK.
- Tokens guardados en `.tmp/beds24-setup-response.json` (gitignored).
- `expiresIn: 86400s` (24h). Refresh token capturado.

### Paso 2 — Verify scopes ✅

`GET /v2/authentication/details`:

```json
{
  "ownerId": 17972,
  "scopes": [
    "all:bookings",
    "all:bookings-personal",
    "all:bookings-financial",
    "all:inventory",
    "all:properties",
    "all:channels"
  ],
  "deviceName": "cc-migration-2026-05-12",
  "validToken": true
}
```

Cubre todos los scopes necesarios (bookings, channels para verificar Booking.com mapping, properties para queries). Credit limit no aparece en `/authentication/details` response actual; lo monitorearé en runtime si Alex aprueba paso 4.

### Paso 3 — Query bookings ✅

API notes (correcciones a thread/11 snippets):

- El parámetro `filter=all` NO existe; devuelve HTTP 400.
- `status` no acepta CSV (`confirmed,new,...`); requiere parámetro repetido (`?status=confirmed&status=new&status=cancelled`).
- Default query sin `status=` parece devolver solo `confirmed` (de ahí que `arrivalFrom=2026-05-12` directo devuelve 9 sin filtro de estado).

#### 3a — Future confirmed (`arrivalFrom=2026-05-12`)

**9 bookings, $310,833.80 MXN total.**

**Detalles PII-redactados** (nombres y datos personales solo en local `.tmp/bookings-374482-future.json` de CC, NUNCA a repo público). Tabla pública usa IDs + fechas + montos + canal:

| # | ID | Arrival | Departure | Referer | apiSourceId | Price MXN | Notas |
|---|----|---------|-----------|---------|-------------|-----------|-------|
| 1 | 85549887 | 2026-06-26 | 2026-06-29 | AlexanderHorn | 0 (direct) | 24,375 | |
| 2 | 82274108 | 2026-07-18 | 2026-07-22 | AlexanderHorn | 0 (direct) | 29,900 | |
| 3 | 85246850 | 2026-07-22 | 2026-07-26 | AlexanderHorn | 0 (direct) | 12,350 | |
| 4 | 85410195 | 2026-08-13 | 2026-08-16 | setBooking JSON | 0 (direct API) | 30,745 | |
| 5 | 86623471 | 2026-08-16 | 2026-08-19 | setBooking JSON | 0 (direct API) | 18,525 | |
| 6 | 81282845 | 2026-11-13 | 2026-11-16 | AlexanderHorn | 0 (direct) | 24,375 | |
| 7 | **84306731** | 2026-11-20 | 2026-11-22 | **Booking.com** | **19** | **24,361** | **🔗 LINKED — masterId=84306730 en room 78695 (RdM)** |
| 8 | 85256246 | 2026-12-28 | 2026-12-30 | AlexanderHorn | 0 (direct) | 44,800 | |
| 9 | **85131614** | 2026-12-31 | 2027-01-03 | **Booking.com** | **19** | **101,402.80** | **NYE — alto valor, canal-bound** |

Resúmenes JSON crudos con nombres+contacto en `.tmp/bookings-374482-future.json` (no commited; local de CC en mi worktree). Alex puede mapear ID → nombre en panel Beds24 directamente.

#### 3b — Historic (`arrivalTo=2026-05-11`)

| status | count |
|---|---|
| confirmed | 84 |
| cancelled | 73 |
| new | 0 |
| request | 0 |
| black | 0 |

Total dedup: **157 bookings históricos**. Migración de éstos a 74322 es relativamente low-risk (ya pasaron, no afectan operaciones presentes — solo se preserva historial). Pero igual respetar protocolo de no tocar sin GO.

#### 3c — Linked booking (EC3)

Booking 84306731 (Booking.com) tiene **`masterId=84306730`**. Investigué el master:

```json
{
  "id": 84306730,
  "status": "confirmed",
  "arrival": "2026-11-20",
  "departure": "2026-11-22",
  "roomId": 78695,           // RdM (no 74316/Combinada como hipotetizó thread/11)
  "propertyId": 31862,
  "referer": "Booking.com",
  "apiSourceId": 19,
  "channel": "booking",
  "price": 35350,
  "subBookings": null         // pero hay sub-booking 84306731 con masterId apuntando aquí
}
```

Interpretación: este guest reservó por Booking.com una combinada **RdM (78695) + Morenas s/ser (374482)** del 20 al 22 nov. El master en 78695 + sub en 374482. Total que paga: $35,350 (master) + $24,361 (sub) = $59,711 MXN.

**Riesgo de mover el sub 84306731 → 74322**:
- El guest reservó **dos unidades físicas específicas** (RdM principal + el Morenas-s/ser anexo).
- Si cambio el sub a 74322 (Morenas c/ser), el guest llega y físicamente está dormiendo en otra unidad. Material breach del contrato Booking.com posible.
- Booking.com puede objetar / penalizar.

**Recomendación CC**: NO mover el linked 84306731. Dejar pasar el stay (20-22 nov 2026) y archivar 374482 después.

#### 3d — Conflictos en 74322 (donde queremos mover)

Verifiqué traslapes en room 74322 para las fechas de los 9. Resultado:

- **Sin overlap real**: 7 de 9.
- **Same-day turnover (no real conflict)**: 2
  - Booking 85549887 (llega 06-26) — 74322 booking 85423589 **sale** 06-26. Standard turnover, no problema.
  - Booking 85246850 (sale 07-26) — 74322 booking 84853699 **llega** 07-26. Standard turnover, no problema.

Ningún conflict bloquea técnicamente la migración (asumiendo Beds24 permite los IDs distintos en mismo día turnover).

74322 actualmente tiene **18 future confirmed bookings**; agregar 8 más (excluyendo 84306731 linked) lo lleva a 26. Físicamente espacio existe (Morenas c/ser es la unidad correcta donde sí están operando).

---

## 2. Categorización de los 9 future confirmed

| Categoría | IDs | Riesgo de mover | Acción recomendada |
|---|---|---|---|
| **A. Direct/AlexanderHorn** (manuales en panel) | 85549887, 82274108, 85246850, 81282845, 85256246 | Bajo — Alex creó manualmente, contactable | ✅ Mover post-GO |
| **B. Direct/setBooking JSON** (API external) | 85410195, 86623471 | Bajo-medio — ¿qué API los creó? Si es ManyChat/MP via la nueva integración, los datos están en D1. Si es otro tooling, verificar antes | ⚠️ Mover post-GO + confirm origen |
| **C. Booking.com NO linked** | 85131614 (NYE-cross $101k) | Medio-alto — channel-bound. Si Booking.com mapea 374482 a un listing, mover el booking de 374482 → 74322 puede desincronizar el calendar Booking.com. Verificar mapping. | ⚠️ Investigar canal antes |
| **D. Booking.com LINKED (sub de combinada)** | 84306731 | **Alto** — guest reservó combinada física. Mover rompe el contrato. | ❌ NO mover. Dejar pasar stay. |

---

## 3. Riesgos canal-side a verificar antes de paso 4

### 3.1 Booking.com mapping de 374482

Cuando archivamos 374482 (Quantity=0 + disable channel) y movemos las reservas Booking.com a 74322, hay que asegurar:

1. **Antes de archive**: deshabilitar Booking.com sync en 374482 PRIMERO para que Booking.com no envíe nuevas reservas.
2. **Reservas existentes Booking.com** (84306731, 85131614): consultar con Booking.com Extranet si moverlas internamente en Beds24 las desincroniza. Probablemente sí — Booking.com sigue creyendo que el guest está en la unidad asociada al listing original.
3. **Alternativa segura**: mantener Booking.com bookings en 374482, dejar pasar sus stays (último: 2027-01-03 NYE), después archivar definitivamente.

Esto pospone archive hasta enero 2027. Web Claude — ¿es aceptable?

### 3.2 setBooking JSON origin

`apiSourceId=0` + `referer=setBooking JSON` significa creados via `POST /v2/bookings` con `setBooking` action por algún tooling. Posibles orígenes:
- Make `wh:bot-booker` flow (cuando un guest pagó MP y se confirmó)
- Manual script de Alex
- Worker-bot port (Sprint 1 día 4) — pero esos son recientísimos

Los 2 IDs 85410195 (arrival 08-13) y 86623471 (arrival 08-16) — Alex, ¿reconoces estos guests (mapeables por ID en panel)? Si fueron creados por la nueva worker-bot, debería haber registro en D1 `bookings` tabla con `beds24_booking_id` apuntando aquí.

Web Claude — ¿puedes verificar en Make ejecutiones recientes de `wh:bot-booker` (2710263) si crearon estos 2 IDs? Eso confirma origen.

---

## 4. NO movido nada — estado neutral en Beds24

🔒 **Garantía**: solo ejecuté lecturas (GET). Ningún POST/PATCH a `/v2/bookings`. El sistema Beds24 está exactamente igual que antes de yo empezar.

---

## 5. Decisión que necesito de Alex

**4 opciones**:

### Opción 1 — Conservadora (recomendada CC)

- Mover **solo bookings históricos (157)** ahora → 74322. Preserva historial unificado.
- **NO mover ningún future confirmed**. Razones:
  - 7 de 9 son de Alex/API directos: los guests no notarían cambio físico (Morenas s/ser ≈ Morenas c/ser misma estructura), pero si hay algún detalle de unidad (vista, planta), Alex tiene que confirmar caso por caso.
  - 2 son Booking.com con canal-binding fuerte.
  - 1 es linked combinada (84306731) — material breach risk.
- **Dejar pasar los 9 future stays** (último: 2027-01-03).
- **Archive 374482 en panel después de 2027-01-03** (~8 meses retraso).

Trade-off: archive retrasado, pero zero customer-impact risk. Operacionalmente 374482 sigue presente en knowledge base — habría que excluirlo explícitamente del `ROOM_ORDER` de scenario 4716901 (WC ya hizo esto), y del fetcher de cron knowledge-refresh (verificar excluye 374482 en `worker-bot/src/cron.ts` `ACTIVE_ROOM_IDS` — actualmente incluye 374482 según commit `9125cc7` thread/11-CC).

### Opción 2 — Híbrida moderada

- Mover **históricos (157)** ahora.
- Mover **future direct/AlexanderHorn (5 bookings — IDs 85549887, 82274108, 85246850, 81282845, 85256246)** ahora.
- **Pendiente verificación**: 2 setBooking JSON (85410195, 86623471) — mover si Alex/WC confirman que son safe-to-move.
- **NO mover**: 2 Booking.com (84306731 linked, 85131614 NYE).
- Dejar pasar Booking.com stays, archivar 374482 después del último checkout (2027-01-03).

Trade-off: solo 2 Booking.com mantienen 374482 activo. Es defendible.

### Opción 3 — Agresiva

- Mover los **9 future + 157 historic**.
- Asume que physical move es transparente al guest (ambos son "Morenas"), y que Booking.com channel re-syncea OK post-move.
- Riesgo: penalización Booking.com si detectan unilateral re-allocation. Material risk con el guest del booking linked 84306731 (combinada — guest llega y NO encuentra la "Morenas s/ser" que reservó).

CC no recomienda.

### Opción 4 — Más data primero

CC continúa investigando antes de decidir:
- Query Booking.com channel mapping (`GET /v2/channels/booking/listings` o equivalente) para 374482.
- Query existencia en D1 (apps/web) de los 2 setBooking JSON IDs en tabla `bookings`.
- WC verifica via Make MCP el origen de los setBooking JSON.

Si Alex prefiere esto, lo ejecuto en próximas iteraciones thread/13+.

---

## 6. Lo que NO hice (paso 4-6)

- ❌ No moví ningún booking (paso 4 thread/11).
- ❌ No verifiqué 374482 limpio post-move (paso 5).
- ❌ No tracé inventario channel-side de 374482 (extra check no exigido pero relevante).

Estos quedan pending decisión Alex sección 5.

---

## 7. Recursos para próxima iteración (post-decisión)

Cuando Alex apruebe, ya tengo:
- `.tmp/beds24-setup-response.json` con token+refresh (vigente 24h desde 2026-05-12T02:29Z, expira ~02:29 2026-05-13)
- `.tmp/bookings-374482-future.json` con los 9 future detallados
- `.tmp/bookings-374482-historic-full.json` con los 157 historic (84 confirmed + 73 cancelled dedup)
- Plan para script `scripts/beds24-migration.ts` en `chore/monorepo-turborepo` branch — pendiente de commit hasta saber qué subset mover.

Si Alex aprueba alguna opción 1-3, ejecuto en próximo turno (CC autonomous):
1. Verifico token válido (refresh si necesario).
2. POST `/v2/bookings` batch hasta 100 IDs por call con `id` + `roomId:74322` (solo cambio roomId).
3. Throttle a 80 calls / 5 min para quedar bajo limit (100 credits / 5 min free) — implica spread ~10 min para 157 historic.
4. Log a `.tmp/migration-374482-to-74322-log.json` con succeeded/failed.
5. Re-query 374482 post-move para verificar 0 active.
6. Commit thread/13-cc-beds24-migration-executed.md con resultado.

---

## 8. Para WC en paralelo

Mientras Alex decide, sugerencias para WC:

- ✅ Si ya ejecutaste `ROOM_ORDER` fix en scenario 4716901 (4716901 = `sub:knowledge-refresh-core`), perfecto — confirmaste a Alex.
- ⚠️ **Verifica `apps/worker-bot/src/cron.ts` `ACTIVE_ROOM_IDS`**: thread/11-CC commit `9125cc7` añadió 74322 pero **NO removió 374482**. Si Alex opta por opciones 1-3 + archivar después, eventualmente queremos `ACTIVE_ROOM_IDS = [78695, 74322, 74316, 637063]` (sin 374482). Si archive se pospone (Opción 1/2), mantener 374482 en `ACTIVE_ROOM_IDS` hasta el day-of-archive.
- ⏸ Make refresh manual de datastore 85638 y R2 — **espera** a que decidamos paso 4, para no cachear knowledge intermedia.
- ⚠️ Replace "374482" → "74322" en `rdm-greeter-kb` (`property-morenas.json`, `system-prompt.txt`, `system-prompt-booker.txt`): si Alex va opción 1 (conservadora), no podemos hacer ese replace todavía porque 374482 sigue operativo hasta 2027-01-03. Si Alex va opción 2/3, sí proceder.

---

## 9. Para Alex — qué necesito

**Decisión binaria primero**: ¿Opción 1, 2, 3, o 4?

**Si Opción 2 o 3**, además:
- ¿Reconoces los guests de IDs 85410195 (08-13→08-16) y 86623471 (08-16→08-19) como reservas legítimas tuyas via algún tool / WhatsApp / scripts? Si sí, safe to move. (Map ID→guest en panel Beds24)
- ¿Has hablado con el guest del booking linked 84306731 (Booking.com, 20-22 nov, combinada RdM+Morenas) sobre que su Combinada va a moverse físicamente? Si no, NO mover (opción 1 para ese 1).
- ¿Has hablado con el guest 85131614 (Booking.com NYE 12-31 → 01-03)? Si no, NO mover; dejar en 374482.

**Si Opción 4**: confirmo y arranco extra-investigation (~20 min).

---

## 10. Cosas finalizadas (admin)

- Tokens guardados local, NO commiteados.
- Script TS de migración pendiente de commit a `chore/monorepo-turborepo`. Postpongo hasta saber qué subset mover (evitar `if Alex.option == "X"` lógica frágil).
- `.tmp/` añadido a `.gitignore` del repo principal (`rincondelmar-bot`) en mi worktree — esto sí lo commitearé cuando push de algún script.

---

*FIN. CC standby. Alex / WC: respondan en thread/13 con decisión y CC ejecuta.*

— Claude Code, 2026-05-12T02:50Z

