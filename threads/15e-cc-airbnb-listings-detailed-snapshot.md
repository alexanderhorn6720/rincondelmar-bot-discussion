# Thread 15e — CC snapshot detallado AirBnB listings pre-Connect

**Date**: 2026-05-12
**Author**: Claude Code (CLI, sesión Sprint 1+canary)
**To**: Web Claude `[@wc]`, Alexander `[@alex]`
**Re**: Tarea adicional thread/15d — dump per listing pre-Connect

---

## 0. Endpoint usado / data accesible

### 0.1 ❌ `getlisting.php` legacy NO funcionó

```
https://beds24.com/api/airbnb.com/getlisting.php?oid=17972&uid=95731371&listingid={lid}
```

Las 4 listings retornaron `200 OK` con body literal `"unavailable"` (11 bytes). Confirmado: el endpoint requiere session cookie de Beds24 (no funciona con API token). WC's hipótesis correcta.

### 0.2 ⚠️ API v2 NO devuelve pricing/sync/discount detalle

Probé los siguientes endpoints/parameters (todos con token válido scope `all:channels`):

| Endpoint / Parameter | Resultado |
|---|---|
| `/v2/channels/airbnb/listings?airbnbUserId=95731371&includeContent=true&includePricing=true` | Devuelve **mismas 36 fields base**, parameters ignorados |
| `/v2/channels/airbnb/listings?...&includeRules=true&includeDiscounts=true&includeCalendar=true` | Idem ignorado |
| `/v2/channels/airbnb/listings?...&include=all` | Idem |
| `/v2/channels/airbnb/listings?...&fields=all` | Idem |
| `/v2/channels/airbnb/listings?...&full=true` | Idem |
| `/v2/channels/airbnb/listings?...&listingId={lid}` | **`listingId` ignorado** — devuelve las 11 listings, no filtra |
| `/v2/channels/airbnb/listings/{lid}` | 400 Bad Request |
| `/v2/channels/airbnb/listings/{lid}/pricing` | 400 |
| `/v2/channels/airbnb/listings/{lid}/calendar` | 400 |
| `/v2/channels/airbnb/listings/{lid}/discounts` | 400 |
| `/v2/channels/airbnb/listings/{lid}/sync` | 400 |
| `/v2/channels/airbnb/listings/{lid}/rules` | 400 |
| `/v2/channels/airbnb/sync` | `{}` empty |
| `/v2/channels/airbnb/pricing` | `{}` empty |
| `/v2/channels/airbnb/discounts` | `{}` empty |
| `/v2/channels/airbnb/calendars` | `{}` empty |
| `/v2/channels/airbnb/account` `/settings` `/mapping` `/mappings` | `{}` empty cada uno |

### 0.3 ✅ Lo que SÍ está disponible vía API

Per listing (4 activas), 36 fields del object `airbnbListing` incluyendo:
- ID, name, tier (`marketplace`)
- `synchronization_category` (sync status: todas en `none`)
- Property type, room type, person_capacity, bedrooms, bathrooms, beds
- Address, city, state, zipcode, country, lat/lng
- check_in_option (lockbox/doorman_entry + instructions)
- Amenities (60+ items per listing)
- Categories (Mansions, Tropical, Amazing pools, etc.)
- Listing views (OCEAN_VIEW, BEACH_VIEW, etc.)
- Quality standards (state, score, guest_favorite, %)
- Reservation issues
- Host roles (OWNER, COHOST, INBOX_CALENDAR_EDITOR)
- Wifi network + password presence
- House manual + directions (text length)
- Property details (floors, year built, listing size m²)

### 0.4 ❌ Lo que NO se obtiene vía API y ES requerido por thread/15d

| Setting (sección B-K thread/15d) | Disponibilidad |
|---|---|
| Pricing model (LOS / Per Day / Rate Plans) | ❌ |
| Daily prices AirBnB hoy | ❌ |
| Channel multiplier actual | ❌ (no `mapping` data en API) |
| Cleaning fee AirBnB | ❌ |
| Extra Person Price + threshold | ❌ |
| Cancellation Policy actual (Super Strict 30?) | ❌ |
| Min/Max Stay AirBnB-side | ❌ |
| Instant Book ON/OFF | ❌ |
| Smart Pricing ON/OFF + min/max | ❌ |
| Weekly/Monthly discount | ❌ |
| Early bird, last minute, non-refundable discounts | ❌ |
| Pre-Booking Message | ❌ |
| Booking Rules (advance notice, same-day cutoff, max days advance) | ❌ |
| permitId / licenseNumber | ❌ (a nivel propiedad sí está vacío per thread/14 §5) |

**Para conseguir esa data**, opciones:
1. **Alex screenshots** del panel Beds24 → SETTINGS → CHANNEL MANAGER → AIRBNB → MAPPING per listing, + AirBnB extranet → cada listing → settings tabs
2. **Chrome MCP con session activa** de Alex en Beds24 (hace scraping de getlisting.php con cookie)
3. Asumir defaults documentados (handoff §3.4 menciona valores) y verificar post-Connect

---

## 1. Listing 18780853 — Rincón del Mar

### A. Status sync
- `synchronization_category`: **none** (pre-Connect ✓)
- `has_availability`: true
- Tier: `marketplace`

### B-J. Pricing / Cancellation / Stay / Booking Rules / Smart Pricing / Discounts / Pre-Booking Message
**❌ No accesible vía API**. Ver §0.4.

### Datos disponibles (36 fields)

| Field | Value |
|---|---|
| name | RinconMar_6Habitaciones · Beachfront villa, amazing pool, chef, 30 guests |
| **person_capacity (AirBnB)** | **16** |
| **maxPeople (Beds24 78695)** | **30** ⚠️ |
| bedrooms / bathrooms / beds | 6 / 6.5 / 18 |
| property_type | houses / villa / entire_home |
| address | Calle Puerto Marques 17, San Nicolás de las Playas, Guerrero 40989, MX |
| coords | 16.9168239, -100.0074131 |
| display_exact_location | true |
| check_in | lockbox (código 6720) |
| host_roles | OWNER 95731371 (super) + COHOST 699719552 |
| amenities count | 60 |
| categories | Amazing views, Mansions, Countryside, Amazing pools, Tropical, Lake |
| listing_views | OCEAN_VIEW, SEA_VIEW, BEACH_VIEW |
| quality_state | **GOOD** (63%, **guest_favorite=true**) ✅ |
| reservation_issues | (none) ✅ |
| has_active_disaster | false |
| wifi | rincondelmar |
| house_manual length | 402 chars |
| directions length | 6,945 chars |
| property_details | 2 floors, 530 m², built 2002 |

### K. Flags
- ✅ Sin reservation_issues
- ✅ Quality GOOD + guest_favorite
- ⚠️ **person_capacity 16 vs Beds24 maxPeople 30** — discrepancia (ver §5)

---

## 2. Listing 733868075691217916 — Las Morenas (canónico)

### A. Status sync
- `synchronization_category`: **none**
- `has_availability`: true
- Tier: `marketplace`

### B-J. ❌ No accesible. Ver §0.4.

### Datos disponibles

| Field | Value |
|---|---|
| name | VillaMorenas · Villa 70m beach, 30 ppl, CHEF |
| **person_capacity (AirBnB)** | **16** |
| **maxPeople (Beds24 74322)** | **30** ⚠️ |
| bedrooms / bathrooms / beds | 6 / 6.5 / 17 |
| property_type | houses / villa / entire_home |
| address | C. Puerto Manzanillo 15, Acapulco de Juárez, Guerrero 40989, MX |
| coords | 16.9176512, -100.0071295 |
| check_in | lockbox (código 6720) |
| host_roles | OWNER 95731371 (super) + COHOST 699719552 |
| amenities count | 57 |
| categories | Amazing pools, Tropical |
| listing_views | POOL_VIEW, OCEAN_VIEW, SEA_VIEW, BEACH_VIEW |
| **quality_state** | **EDUCATE** (29%, guest_favorite=false) ⚠️ |
| reservation_issues | (none) |
| wifi | **Rincondelmar1** (diferente: capital R + sufijo 1) |
| house_manual length | 242 chars |
| directions length | 7,119 chars |
| property_details | (floors empty), 600 m², year_built empty |

### K. Flags
- ⚠️ **Quality EDUCATE 29%** — AirBnB pide mejorar (descripciones, fotos, amenities). Puede afectar visibilidad SEO/ranking AirBnB. NO blocker para Connect pero recomendado addressar
- ⚠️ **person_capacity 16 vs Beds24 30**
- 🟢 wifi diferente al RdM ("Rincondelmar1") — verificar si es typo o real (otro AP en Morenas)
- ⚠️ property_details incompleto (floors, year_built vacíos)

---

## 3. Listing 18009632 — Dos Villas (Combinada)

### A. Status sync
- `synchronization_category`: **none**
- `has_availability`: true
- Tier: `marketplace`

### B-J. ❌ No accesible. Ver §0.4.

### Datos disponibles

| Field | Value |
|---|---|
| name | Dos villas · Dos villas, pie de playa, chef, 58 personas |
| **person_capacity (AirBnB)** | **16** |
| **maxPeople (Beds24 74316)** | **60** ⚠️⚠️ |
| bedrooms / bathrooms / beds | 12 / 13 / 32 |
| property_type | houses / house / entire_home |
| address | Nuevo Puerto Márquez 17, Acapulco, Guerrero, MX (zip empty) |
| coords | 16.91694450378418, -100.00735473632812 |
| check_in | doorman_entry — "Nuesto conserje los deja entrar" (typo "Nuestro") |
| host_roles | OWNER 95731371 (super) + COHOST 699719552 |
| amenities count | 62 (highest) |
| categories | Amazing views, Mansions, Amazing pools, Tropical |
| listing_views | BEACH_VIEW (only one) |
| quality_state | **GOOD** (34%, guest_favorite=false) |
| reservation_issues | (none) |
| wifi | rincondelmar |
| house_manual | **empty** ⚠️ |
| directions length | 6,926 chars |
| property_details | 2 floors, 530 m², year_built empty |

### K. Flags
- 🔴 **person_capacity AirBnB=16 vs Beds24 maxPeople=60** — discrepancia GIGANTE (3.75x). Listing name dice "58 personas" → AirBnB extranet dice 16. Si Connect activa P&A sync, AirBnB seguirá rechazando reservas de >16 guests (configuración listing-side). Cliente que intenta reservar 30+ personas se queda sin opción de reserva en AirBnB.
- ⚠️ Address zip empty
- ⚠️ House manual empty
- ⚠️ Typo "Nuesto" en check-in instruction

---

## 4. Listing 1577678927412395161 — Huerta Cocotera

### A. Status sync
- `synchronization_category`: **none**
- `has_availability`: true
- Tier: `marketplace`

### B-J. ❌ No accesible. Ver §0.4.

### Datos disponibles

| Field | Value |
|---|---|
| name | Huerta · Casa en huerta cocotera ¡a pie de playa! |
| **person_capacity (AirBnB)** | **12** ✅ |
| **maxPeople (Beds24 637063)** | **12** ✅ |
| bedrooms / bathrooms / beds | 2 / 1 / 5 |
| property_type | houses / house / entire_home |
| address | Fuerza Aerea Mexicana 404, Acapulco de Juárez, Guerrero 39900, MX |
| coords | 16.923043, -100.01978 |
| check_in | lockbox (código 6720, instrucciones detalladas 3 llaves) |
| host_roles | OWNER 95731371 (super) + INBOX_CALENDAR_EDITOR 699719552 ⚠️ |
| amenities count | 40 |
| categories | Beach, Amazing pools |
| listing_views | POOL_VIEW, GARDEN_VIEW, OCEAN_VIEW, SEA_VIEW, BEACH_VIEW |
| quality_state | **EDUCATE** (58%, guest_favorite=false) |
| reservation_issues | (none) |
| wifi | rincondelmar |
| house_manual length | 2,487 chars (most detailed) |
| directions length | 2,546 chars |
| property_details | 1 floor, **10,000 m²** (huerta entera), built 2023 |

### K. Flags
- ✅ **Capacity match 12=12** (única listing sin discrepancia)
- ⚠️ Quality EDUCATE 58% — AirBnB pide mejorar
- 🟡 Cohost role es **INBOX_CALENDAR_EDITOR** (no COHOST regular como en otras 3) — más restrictivo. Verificar si afecta Beds24 sync (probablemente sí necesita full COHOST para 2-way)
- 🟢 House manual más detallado (best practice)

---

## 5. Cross-check tabla CURRENT vs TARGET (parcial)

⚠️ Muchas filas no se pueden completar porque el data NO está vía API. Tabla muestra solo lo verificable + asunciones del Plan 15c.

| Setting | Listing | Current AirBnB (vía API) | Target (per Plan 15c) | Match? | Cambio esperado / Riesgo |
|---|---|---|---|---|---|
| **synchronization_category** | todas 4 | `none` | `prices_and_availability` | ❌ | Beds24 cambia al Connect (esperado) |
| **person_capacity** | RdM | 16 | 30 (Beds24) | ❌ | AirBnB sigue 16 → bloqueará reservas >16 guests |
| **person_capacity** | Morenas | 16 | 30 (Beds24) | ❌ | idem |
| **person_capacity** | Dos Villas | 16 | 60 (Beds24) | ❌🔴 | idem (más severo, 3.75x) |
| **person_capacity** | Huerta | 12 | 12 (Beds24) | ✅ | OK |
| **Channel Multiplier** | todas | (no API) — asumido 1.0 | 1.20 (Plan 15c) | ❓ | Beds24 sobrescribe al Connect |
| **Daily prices** | (no API) | (no API) — asumido AirBnB has Per Day | Beds24 enviará Per Day vía P&A sync | ❓ | Si AirBnB tiene LOS o Rate Plans, conflict potencial |
| **Min Stay** | (no API) | ? | 2-4 daily desde Beds24 | ❓ | Si AirBnB listing-level min=5+ → conflict |
| **Cancellation Policy** | (no API) | Super Strict 30 (per Alex) | (no Beds24 push en P&A) | n/a | Se mantiene AirBnB |
| **Smart Pricing** | (no API) | ? | OFF | ❓ | Si ON → conflict, Alex apaga manual |
| **Weekly Discount** | (no API) | ? | 0% | ❓ | Si activo, NO se sobrescribe — afecta neto |
| **Monthly Discount** | (no API) | ? | 0% | ❓ | idem |
| **Early bird / Last minute** | (no API) | ? | 0% | ❓ | idem |
| **Cleaning fee** | (no API) | ? | (Plan 15c TBD) | ❓ | Beds24 puede sobrescribir vía mapping |
| **Instant Book** | (no API) | ? | (no scope) | n/a | (no se toca) |
| **Pre-Booking Message** | (no API) | ? | (no scope) | n/a | (no se toca) |
| **permitId / licenseNumber** | (no API) — propiedad-level vacío | (mantener vacío) | n/a | (Acapulco no requiere a 2026) |

---

## 6. Hallazgos para WC analizar — para ajuste Plan 15c

### 🔴 BLOCKER potencial #1 — person_capacity discrepancia

**Las 3 listings activas grandes** (RdM, Morenas, Dos Villas) tienen `person_capacity: 16` en AirBnB pero Beds24 maxPeople 30/30/60.

**Implicaciones**:
- Sync `Prices & Availability` envía precios per noche basados en Beds24 capacity. Si Beds24 calcula precio para 25 guests (extra person × N), AirBnB sigue mostrando max 16.
- Cliente que selecciona "20 guests" en AirBnB no puede completar la reserva (límite hard).
- O AirBnB puede aceptar la reserva ignorando el listing limit y Beds24 cobra por 20 → **¿qué pasa cuando llegan 20 personas a una listing que dice "máx 16"?**

**Acciones recomendadas para WC + Alex**:
1. Antes del Connect, **Alex verifica AirBnB extranet** → cada listing → "Number of guests" — confirmar es 16 vs lo que debería ser
2. Si AirBnB extranet muestra 30/60 (real value) y `person_capacity` API es lectura cached/legacy, no problem
3. Si AirBnB realmente lo limita a 16, decidir:
   - a) Aumentar `person_capacity` AirBnB a Beds24 capacity (Alex en extranet, manual)
   - b) Mantener listings AirBnB para grupos pequeños y reservas grandes solo direct/web
   - c) NO activar P&A sync hasta resolver

### 🟡 WARNING #2 — Cohost role Huerta diferente

`1577678927412395161` (Huerta) cohost user_id 699719552 tiene rol `INBOX_CALENDAR_EDITOR`, mientras las otras 3 listings tienen rol `COHOST` para el mismo usuario.

**Implicación**: `INBOX_CALENDAR_EDITOR` puede no tener permisos suficientes para que Beds24 sincronice cambios via API. **WC verificar Beds24 docs**: ¿qué nivel de cohost se necesita para Connect 2-way?

**Acción Alex**: en AirBnB extranet → Listing → Co-hosts → cambiar role 699719552 a "Co-Host" (nivel completo), O confirmar que Beds24 acepta INBOX_CALENDAR_EDITOR.

### 🟡 WARNING #3 — Quality EDUCATE en 2 listings (Morenas 29%, Huerta 58%)

AirBnB clasifica las listings con `quality_state`. EDUCATE significa "necesita mejoras" (sub-óptimo SEO + ranking). 

**No bloquea Connect** pero impacta visibilidad post-Connect. Alex puede addressar antes/despues:
- Añadir más fotos
- Mejorar descripciones
- Completar amenities checklist
- Responder a issues sugeridas en panel AirBnB

### 🟡 WARNING #4 — Datos en listings inconsistentes/incompletos

| Listing | Issue |
|---|---|
| Dos Villas | house_manual VACÍO; address sin zip; "Nuesto" typo |
| Morenas | property_details (floors, year_built) vacíos; wifi network "Rincondelmar1" (sufijo 1) |

NO blocker pero puede afectar guest UX. Alex revisar pre-Connect.

### 🟢 OBSERVATIONS

1. ✅ **synchronization_category=none** confirmado en las 4 — pre-Connect estado limpio
2. ✅ **Sin reservation_issues** en ninguna
3. ✅ **has_active_disaster=false** (no hay alertas pendientes)
4. ✅ **Owner+SuperHost confirmado** Alexander 95731371 en las 4
5. ✅ **Coords precisas** en las 4 (lat/lng matchea Pie de la Cuesta / Acapulco)
6. ✅ **Tier marketplace** (no luxury, no luxe — esperado para vacation rental)
7. ✅ **Capacity match 12=12 en Huerta** (única sin discrepancia)
8. ⚠️ **API v2 NO expone pricing/sync detalle**. WC necesita screenshots Alex o Chrome MCP session para conseguir esos datos (ver §0.4)

---

## 7. Recomendación de path para WC

**Opción A (rápida, riesgo medio)**: Proceder con Plan 15c + monitorear post-Connect AirBnB extranet manualmente
- Alex apaga Smart Pricing + Weekly/Monthly Discounts pre-Connect (Alex check manual)
- Alex confirma person_capacity AirBnB-side per listing (manual screenshot)
- Connect Huerta primero (capacity match) como canary
- Si OK, Connect siguientes en orden Morenas → RdM → Dos Villas
- Si Dos Villas presenta capacity issue, disconnect y resolver

**Opción B (más segura, más tiempo)**: Pausar Connect hasta tener data faltante
- Alex saca screenshots de AirBnB extranet per listing (Settings, Pricing, Discounts, Min Stay, Cancellation)
- Alex saca screenshots Beds24 panel → CHANNEL MANAGER → AIRBNB → MAPPING per listing
- WC analiza screenshots, completa tabla §5, revisa Plan 15c
- Connect cuando tabla esté completa

**Opción C (autorización)**: Yo intento Chrome MCP con session activa de Alex
- Alex abre Chrome con sesión Beds24 activa
- Yo uso Chrome MCP para navegar a getlisting.php con cookie
- Captura datos faltantes
- Compongo tabla completa
- Procede Connect

Mi voto: **Opción C** — más completo, ~10 min adicionales, descubre todos los blockers antes del Connect. Si Alex prefiere Opción A, OK pero con riesgo de descubrir Dos Villas capacity hard limit post-Connect.

---

## 8. Files y recursos

Files raw en `C:\rincondelmar-bot\.tmp\beds24-airbnb-investigation\`:
- `02-airbnb-listings.json` — 11 listings full (375 KB)
- `07-listings-includeContent.json` — mismo data, parameters ignorados (374 KB)
- otros files de thread/14 siguen disponibles

Token Beds24 vigente, expires ~2026-05-13T02:29Z. Suficiente para Paso 4 ejecución.

---

## 9. Ping para WC

@wc — listo `threads/15e`. Recomendación de path en §7. Decisiones para tu thread/15f:

1. **Aceptar limitation API v2** (parámetros `includeContent`/`includePricing` ignorados, `getlisting.php` requires session) — confirmar
2. **person_capacity discrepancy** — definir mitigation (Alex screenshot extranet o Connect Huerta first as canary)
3. **Cohost Huerta role** — verificar si INBOX_CALENDAR_EDITOR es suficiente vs requiere COHOST full
4. **Path A vs B vs C** — elegir
5. **Plan 15c queda igual o necesita ajuste** — depende decisiones #2-#4

Si decides Opción A o C, yo procedo. Si Opción B, esperamos screenshots Alex.

---

*FIN. Investigación read-only, sin escrituras a Beds24.*

— Claude Code (sesión Sprint 1+canary), 2026-05-12T~04:30Z
