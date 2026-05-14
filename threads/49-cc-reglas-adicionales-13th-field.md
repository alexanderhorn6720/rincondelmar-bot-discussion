# Thread 49 — `reglas_adicionales` (13th field) + URL/emoji learnings

**De:** CC (main thread)
**Para:** Alex `[@alex]`, WC `[@wc]`, Karina `[@karina]`
**Fecha:** 2026-05-14
**Status:** PR #21 merged · RdM ES live · 3 props pending · EN versions pending

---

## 0. TL;DR

Post-RdM ES write-back de los 12 fields, Alex notó que **faltaba el campo "Reglas adicionales"** (House rules) — el textbox bajo `/details/house-rules` que tiene info crítica para guests pre-booking.

✅ Schema expanded: 12 → 13 fields
✅ RdM ES reglas re-drafted (cleaner: 3761 → 2146 chars)
✅ Pushed a AirBnB live
✅ Documented 2 nuevos AirBnB validation gotchas (URLs en rules + emoji blocklist)

🟡 Pending: 3 properties × 2 langs × 1 field = 6 cells more reglas

---

## 1. Schema expansion (12 → 13 fields)

**PR #21:** `feat(schema): +13th field reglas_adicionales (House rules) — Alex faltante`

**New field:**
```typescript
reglas_adicionales: {
  label: 'Reglas adicionales',
  description: 'House rules específicas (capacidad, mar abierto, mascotas, daños, A/C, eventos, advisory EE.UU.). Doble idioma ES + EN.',
  max_chars: 5000,
  format: 'limited_markdown',
  longform: true,
}
```

**AirBnB editor location:**
- URL: `/hosting/listings/editor/{listingId}/details/house-rules`
- Click "Reglas adicionales" → expand
- Textareas: `additional-rules-es-textarea` + `additional-rules-en-textarea`

**Library updates:**
- `welcome-guide.ts` — section "Reglas de la casa" / "House rules" 📋
- `welcome-kb.ts` (worker-bot) — bot KB include reglas en flatten
- `welcome-kb-preview.ts` (apps/web duplicate) — same

**Admin updates:**
- `/admin/airbnb-content` overview: "12 fields" → "13 fields"
- `/admin` home card description updated
- `/admin/airbnb-content/deploy-queue` URL_PER_FIELD refined: 8 distinct sub-URLs

---

## 2. RdM ES reglas — pushed cambios vs current

**Current (3761 chars, mezcla ES + EN, mal estructurado):**
- Wall of text con bilingüe inline
- Algunas líneas no son rules sino info (boiler tibio → manual_casa territory)
- Repetitivo (mascotas mencionadas 2x)
- Travel Advisory párrafo enorme

**Nuevo (2146 chars, ES only — EN textarea separado):**
- Reorganizado por categorías con emojis safe (📋 🌊 🐾 👥 💰 🚫 ❄️ 🏖️ 🍽️ 🧹 🔒 ⚠️)
- Removí informacionales (boiler) → manual_casa los tiene
- Junté duplicados
- Travel Advisory más conciso, sin URL (per AirBnB Off-Platform Policy 2026)

**Versión completa pushed:**

```
POR FAVOR LEER ANTES DE RESERVAR

📋 Capacidad y precio
— AirBnB solo permite ingresar 16 huéspedes. Cobramos $300 MXN/noche por
  persona adicional hasta cupo total. Pide cotización antes de reservar.

🌊 Mar abierto
Casa en mar abierto del Pacífico, fuera de la bahía de Acapulco. Según el
clima, el oleaje puede ser alto y no podemos garantizar que se pueda nadar
en el mar. Para nadar tranquilo: alberca infinita.

🐾 Mascotas
— Bienvenidas hasta 2 por reserva (avisar al reservar).
— No permitidas en alberca, sobre sofás/camas, ni solas en habitaciones.
— Si se muestran agresivas con personal: correa o abandonar propiedad.

👥 Huéspedes adicionales
Huéspedes/mascotas no anunciados solo bajo discreción del anfitrión.

💰 Daños y reposiciones
— Daños al inmueble/instalaciones/equipo: costo de restitución antes de salida.
— Sábanas/toallas con vómito, orina, fecales, manchas permanentes o pelos
  de mascota: costo de reposición.

🚫 Prohibido
— Vidrio dentro o cerca de la alberca.
— Fumar dentro de habitaciones.
— Música amplificada en playa o exterior después de las 10 PM.

❄️ Aire acondicionado
Limitado a 23-27°C. Apagar al salir de habitaciones (personal puede apagar
si se olvida).

🏖️ Playa y palapa
Palapa con camastros directamente en playa — no necesitas sombrillas
adicionales. Si visitas otra playa, lleva las tuyas.

🍽️ Servicios opcionales con costo
— Compras víveres: 5% sobre costo + mín $450 MXN.
— Eventos y comidas especiales: aviso previo + confirmación anfitrión.
— Personal extra noche: cocinera $500 (3-10 PM), mesero/barman $650
  (5 PM-12 AM), aviso 1 semana.

🧹 Limpieza
Servicio 3 días/semana. Para estancias largas: sábanas semanal, toallas
cada 3 días.

🔒 Seguridad
Sistema de alarma + cámaras CCTV en entradas. El conserje muestra ubicaciones.

⚠️ Aviso viajeros desde EE.UU.
Existe un Travel Advisory del U.S. Department of State para Guerrero
(incluye Acapulco). Al reservar declaras conocer este aviso y aceptas
que NO aplica cancelación gratuita por "extenuating circumstance"
relacionada al advisory. Consulta el aviso en la página oficial del
U.S. State Department buscando "Mexico Travel Advisory".
```

---

## 3. Nuevos AirBnB validation gotchas descubiertos

### 3.1 URLs prohibidas en House rules

**Error AirBnB:**
> "Aún no podemos guardar tus datos. No se pueden compartir enlaces ni
> datos de contacto. Elimina esta información para continuar: 'travel.state.gov'"

**Causa:** AirBnB Off-Platform Policy 2026 (thread/44 lo documenta) prohíbe URLs en cualquier listing field salvo el "Custom link" oficial.

**Workaround:** texto descriptivo en lugar de URL. "Consulta página oficial del U.S. State Department buscando 'Mexico Travel Advisory'".

**Implicación para WC drafts:** revisar TODOS los drafts pending por URLs (Maps, websites, social handles) que serán rechazadas. Las URLs ya safe en `como_llegar` (saved exitosamente) son Google Maps geo links + chat.whatsapp.com — esas pasaron OK. Pero `.gov`/`.com` website links → rechazados.

### 3.2 Emojis bloqueados (de session anterior — recap)

Findings documentados en `knowledge/airbnb-emoji-blocklist-2026-05-14.md`:

❌ **Bloqueados confirmados:** 🌅 (sunrise) · 📶 (antenna bars)
❓ **Sospechosos (no testeados):** 🔒 🍳 🚿 🚨
✅ **Safe set:** ⛱️ 🛏️ ✅ 👨‍🍳 🏊 🏖️ 🧹 🎵 🛻 🛥️ 🛎️ 🛒 🍹 🔥 🥥 💆 🐴 🚣 🤿 🎉 🏅 💬 ☀️ 1️⃣-6️⃣ 📋 🌊 🐾 👥 💰 🚫 ❄️ 🍽️ ⚠️

**Nuevos emojis confirmados en este push (reglas RdM ES):** 📋 🌊 🐾 👥 💰 🚫 ❄️ 🍽️ ⚠️ — todos pasaron OK.

### 3.3 Schema URL mapping refined

**Antes (deploy-queue assumption):**
- `/details/description` → 5 fields (description, tu_propiedad, acceso_huespedes, interaccion_huespedes, otros_detalles)
- `/arrival/directions` → 6 fields (como_llegar, metodo_llegada, wifi*, manual_casa, instrucciones_salida)

**Ahora (verificado vía Chrome MCP):**
- `/details/title` → title
- `/details/description` → description, tu_propiedad, acceso_huespedes, interaccion_huespedes, otros_detalles
- `/details/house-rules` → reglas_adicionales (NEW)
- `/arrival/directions` → como_llegar
- `/arrival/check-in-method` → metodo_llegada
- `/arrival/wifi-details` → wifi_red + wifi_password
- `/arrival/house-manual` → manual_casa
- `/arrival/checkout-instructions` → instrucciones_salida

**8 distinct AirBnB editor URLs total.** PR #21 actualiza el URL_PER_FIELD del deploy-queue.

---

## 4. Roadmap pending

### 4.1 RdM EN reglas (1 cell)

Currently `additional-rules-en-textarea` está **vacío** en AirBnB. Necesita:
- EN translation del nuevo content drafted (CC puede traducir, ~15 min)
- Push via Chrome MCP

### 4.2 Las Morenas reglas (ES + EN, 2 cells)

Property-specific tweaks vs RdM:
- Chef OPCIONAL ($1,000/$1,500) en lugar de incluido
- WiFi distinto (Rincondelmar1)
- Capacidad similar (30)
- Resto de rules igual

### 4.3 Combinada reglas (ES + EN, 2 cells)

- Capacidad 58 (RdM + Morenas combined)
- Bodas grandes (50-80 invitados) — agregar regla específica
- Resto similar

### 4.4 Huerta Cocotera reglas (ES + EN, 2 cells)

Property-specific tweaks vs RdM:
- 2 hab solo (vs 6) — capacidad 12 (no 30)
- Sin chef incluido
- Animales (huerta narrative — gallinas, etc.)
- Sin alberca infinita (alberca borde infinito separada)
- Resto similar

**Total cells reglas pending: 7** (1 RdM EN + 2 Morenas + 2 Combinada + 2 Huerta)

---

## 5. Acciones para CC (próximo)

- [ ] Draft RdM EN reglas (translation del ES)
- [ ] Draft Las Morenas reglas ES + EN (con tweaks)
- [ ] Draft Combinada reglas ES + EN (con tweaks)
- [ ] Draft Huerta Cocotera reglas ES + EN (con tweaks)
- [ ] Show all drafts a Alex/WC para review
- [ ] Push approved a AirBnB via Chrome MCP

ETA total: ~45 min drafting + ~30 min push (con classifier per-property approvals).

---

## 6. Acciones para Alex/WC

- **Alex:** review CC drafts cuando lleguen
- **WC:** próximos seed drafts en `knowledge/content-drafts/` deben incluir
  `airbnb_fields.reglas_adicionales` (campo nuevo). Update WC schema constant
  de "Reglas no incluidas" a "Reglas como 13th campo".

---

## 7. PRs publicadas hoy

| # | Title | Status |
|---|---|---|
| #21 | feat(schema): +13th field reglas_adicionales | ✅ MERGED → main |
| - | scripts/add-reglas-rdm-es.mjs | one-shot, run done |
| - | scripts/mark-reglas-deployed.mjs | one-shot, run done |

**Stack live now (post PR #21 deploy):**
- /admin overview muestra "13 fields"
- /admin/airbnb-content/deploy-queue tiene URL mapping correcto
- ContentCell editor + Welcome Guide + Bot KB todos soportan reglas_adicionales
- AirBnB RdM ES reglas live
