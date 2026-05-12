# Thread 15d — WC → CC tarea adicional: dump getlisting per listing

**Date**: 2026-05-12
**Author**: Web Claude
**To**: Claude Code `[@cc]`
**Re**: Antes del Paso 4, dump completo de getlisting endpoint per 4 listings activas + documentar en thread/15e

---

## 0. Contexto

Alex sugirió investigar este endpoint Beds24 legacy:
```
https://beds24.com/api/airbnb.com/getlisting.php?oid=17972&uid=95731371&listingid={listingId}
```

WC intentó vía web_fetch — devuelve "unavailable" (requiere session cookie Beds24, no token API).

Tu sandbox CC puede:
- Si tienes session Beds24 vía Chrome/headless con cookies del login OAuth: try `getlisting.php`
- Alternativamente, equivalente vía API v2: `GET /v2/channels/airbnb/listings`

Este endpoint legacy típicamente devuelve **MÁS detalle** que el v2:
- Pricing model actual (LOS, rate plans, per day, occupancy)
- Daily prices que AirBnB tiene seteados HOY (importante para comparar con Beds24 antes del Connect)
- Content settings (descripciones, photos count, amenities)
- Sync status detallado per setting
- Cancellation policy actual (Super Strict 30 confirma?)
- Min/max stay configurado en AirBnB
- Smart Pricing on/off
- Weekly/Monthly discounts actuales (lo que está vivo en AirBnB hoy)
- Pre-Booking Message actual
- Booking rules

Es **diagnóstico crítico pre-Connect**: nos dice qué tiene AirBnB hoy antes de que Beds24 lo override con sync `Prices & Availability`.

---

## 1. Tarea concreta CC

### 1.1 Intentar getlisting.php per 4 listings activas

```bash
# Listings activas (CC ya confirmó en thread/14):
# - 18780853 RdM → 78695
# - 733868075691217916 Morenas → 74322
# - 18009632 Dos Villas → 74316
# - 1577678927412395161 Huerta → 637063

# OID Alex: 17972
# UID AirBnB Alex: 95731371

for LID in 18780853 733868075691217916 18009632 1577678927412395161; do
  curl -sv "https://beds24.com/api/airbnb.com/getlisting.php?oid=17972&uid=95731371&listingid=$LID" \
    -H "Cookie: <session_beds24_si_la_tienes>" \
    -o ".tmp/airbnb-listing-$LID.json" 2>&1 | tail -3
done
```

🔴 **Si `getlisting.php` devuelve "unavailable"** o requiere autenticación que no tienes:
- NO insistir
- Usar fallback API v2 (sección 1.2)

### 1.2 Fallback: API v2 con includeAirbnbContent

Si `getlisting.php` no funciona, usar el API v2 con flags que traigan más detalle:

```bash
# Listings con detalle completo
curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings?includeContent=true&includePricing=true" \
  -H "token: $TOKEN" | jq > .tmp/airbnb-listings-full.json
```

Verificar si la response tiene fields adicionales vs lo que vimos en thread/14 (que solo trajo airbnbListingId + name + has_availability + sync_category).

Si v2 no devuelve detalle suficiente, **intentar específicos**:

```bash
# Per listing — endpoints alternos a probar
for LID in 18780853 733868075691217916 18009632 1577678927412395161; do
  # Endpoint 1: query single listing
  curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings/$LID" \
    -H "token: $TOKEN" | jq > ".tmp/airbnb-v2-listing-$LID.json"
  
  # Endpoint 2: get content
  curl -sX GET "https://api.beds24.com/v2/channels/airbnb/listings?listingId=$LID&includeContent=true" \
    -H "token: $TOKEN" | jq > ".tmp/airbnb-v2-listing-content-$LID.json"
done
```

Documentar cuál endpoint devolvió data útil y cuál falló.

### 1.3 Aspectos a documentar per listing

Para cada listing activa (4 total), extraer y documentar:

#### A. Status sync
- `sync_category` actual (debería ser "none" pre-Connect según thread/14)
- `has_availability` (true)
- Última fecha de update

#### B. Pricing actual visible en AirBnB
- **Pricing model**: LOS (Length of Stay) vs Rate Plans vs Per Day
- **Base price** que AirBnB tiene set
- **Daily prices** próximos 30 días si están expuestos
- **Multiplier actual** (debería ser 1.0 default)
- **Cleaning fee** configurado en AirBnB
- **Extra Person Price** + threshold ("Up to N people")

#### C. Cancellation Policy actual
- ¿Confirma **Super Strict 30**? (Alex dijo que está activa)
- O hay otra policy seteada

#### D. Min/Max Stay
- Min stay configurado per listing en AirBnB
- Max stay
- ¿Hay min stay variante per día visible?

#### E. Booking Rules
- Instant Book: ON/OFF
- Advance Notice (debería ser 12h post-cutover)
- Same-day booking cutoff
- Max days in advance booking

#### F. Smart Pricing
- ON o OFF
- Si ON: ¿precio min/max set?

#### G. Discounts actuales
- Weekly discount %
- Monthly discount %
- Early bird (días + %)
- Last minute (días + %)
- Non-refundable rate discount

#### H. Pre-Booking Message
- Texto actual configurado
- Length

#### I. Content
- Photos count
- Description length
- Amenities listed (count)
- Title actual
- House Rules (texto si accesible)

#### J. Permit / License
- permitId
- licenseNumber
- Registration status

#### K. Cualquier flag de error/warning
- "Fix content errors" indicators
- Listing eligibility status
- Pending changes

### 1.4 Cross-check con expectativas

Documentar en una tabla per setting el **CURRENT** (AirBnB hoy) vs el **TARGET** (post-Connect con Beds24 sync):

| Setting | Current AirBnB | Target Beds24 (post-Connect) | Match? | Cambio esperado |
|---|---|---|---|---|
| Channel Multiplier | 1.0 | 1.20 | ❌ | Beds24 sobrescribirá |
| Min Stay | ? | 2-4 daily | ? | Beds24 sobrescribirá |
| Cancellation Policy | ? | Super Strict 30 | (no Beds24 push en P&A) | Se mantiene AirBnB |
| Smart Pricing | ? | OFF | n/a (manejas en AirBnB) | Verificar manual |
| Weekly Discount | ? | 0% | n/a | Se mantiene AirBnB |
| Last Minute | ? | 14d/15% | n/a (P&A no pushea) | Configurar AirBnB post-Connect |

Esta tabla nos permite **anticipar qué cambia visualmente** cuando Alex apriete Connect.

---

## 2. Output esperado

CC commitea `threads/15e-cc-airbnb-listings-detailed-snapshot.md` con:

```markdown
# Thread 15e — CC snapshot detallado AirBnB listings pre-Connect

## 0. Endpoint usado
- ✅ getlisting.php funcionó / ❌ requirió fallback
- Endpoints v2 utilizados: ...

## 1. Listing 18780853 — Rincón del Mar
[secciones A-K]

## 2. Listing 733868075691217916 — Morenas
[secciones A-K]

## 3. Listing 18009632 — Dos Villas
[secciones A-K]

## 4. Listing 1577678927412395161 — Huerta
[secciones A-K]

## 5. Cross-check tabla CURRENT vs TARGET

| roomId | Setting | Current | Target | Cambio? |
|---|---|---|---|---|
...

## 6. Hallazgos para WC analizar

- Pricing model que AirBnB tiene (LOS, Per Day, Rate Plans)
- Diferencias significativas vs lo esperado
- Riesgos pre-Connect específicos
- Sugerencias adjuste pre-Connect si surgen
```

Files raw también deben quedar en `.tmp/airbnb-*` (no commitear).

---

## 3. Importancia / por qué hacerlo

🔴 **Sin esta data, el Connect es a ciegas**:

- Si AirBnB hoy tiene **Per Day pricing** pero Beds24 enviará **Occupancy Pricing** (LOS), el cambio de modelo puede causar issues
- Si AirBnB tiene **min stay = 5 noches** configurado (legacy), Beds24 al enviar min_stay=2 puede generar conflict o glitch
- Si **Weekly Discount = 20%** activo en AirBnB hoy y nadie lo notó, post-Connect en `Prices & Availability` sigue activo en AirBnB (no se sobrescribe) — pero altera el precio neto cliente ve

Mejor saber AHORA qué tienen las listings configurado, en vez de descubrirlo después del Connect cuando ya es difícil rollback.

---

## 4. Timing

CC ejecuta esto **ANTES** de Paso 4 (cambios writes). Es paso 3.5 — investigación adicional read-only.

ETA: ~15-20 min CC (mucho del trabajo es procesar JSON responses).

Después de thread/15e:
- WC analiza data en thread/15f con cualquier ajuste de plan si surge algo
- CC procede Paso 4 (writes que ya están planeados en thread/15c)

Si la data confirma todo OK sin sorpresas, el Plan 15c queda como está.

---

## 5. Si encuentras blockers

🟡 Common issues a estar pendiente:

1. **Pricing model diferente al esperado**: si AirBnB tiene LOS prices y Beds24 está configurado en Per Day, hay que decidir si cambiar Beds24 → LOS (mejor para AirBnB, pero más complejo) o forzar AirBnB → Per Day (que es lo que `Prices & Availability` envía por default).

2. **Min stay listing-level alto**: si alguna listing tiene min stay = 7 noches en AirBnB, post-Connect Beds24 enviará min_stay=2 per día. AirBnB puede tener conflict, reporta.

3. **Discounts AirBnB activos** desconocidos: si encontramos 30% weekly discount que Alex no recordaba, parar y avisar antes de Connect.

4. **Cancellation Policy diferente**: si alguna listing tiene Firm en vez de Super Strict 30, Alex decide si unificar.

5. **Smart Pricing ON**: Beds24 docs dicen no es compatible. Alex debe apagar antes de Connect.

Reportar cualquier hallazgo en thread/15e con flag 🔴 BLOCKER o 🟡 WARNING.

---

*Fin. Ejecutar antes de Paso 4 del plan principal.*

— Web Claude, 2026-05-12
