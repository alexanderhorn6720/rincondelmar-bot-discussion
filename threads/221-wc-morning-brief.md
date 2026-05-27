---
id: 221
author: wc
topic: morning-brief-thread-220-summary
status: brief
mode: mobile-read
created_at: 2026-05-27
updated_at: 2026-05-27
revision: 2
references:
  - threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md
---

# thread/221 — Morning brief: qué hizo WC overnight

> **REV 2 (post-feedback Alex):** corrección sobre `payload.booking.price`. Ver bloque ⚠️ abajo.
>
> **Lee primero esto (5 min).** Después si te interesa el detalle, abre thread/220 completo (~45 min lectura).

## ⚠️ Corrección REV 2 — el precio en payload no es lo que ve el guest

Anoche escribí en el spec que `payload.booking.price` era "el número EXACTO que ve el guest en Airbnb". **MAL.** Es tu **revenue NET** (después de commission Airbnb + taxes guest paga). El guest ve un total mayor (price + commission Airbnb + service fee + taxes locales) y ese número **NO viene en el payload**.

**Verificado con D1 query:**
- Inquiry Ana Karen: `price: 28789.02` (net Alex), commission/tax/details = 0/null
- Booking confirmado sample: `price: 6117.84`, `commission: 948.27` (separado)

**Fix aplicado en thread/220 REV 2:**
- Template REMUEVE `{airbnbPriceMxn}` placeholder
- Lenguaje: "la tarifa que ya viste en Airbnb cubre la villa completa..." (sugerencia textual tuya)
- Composer determinista actualizado para nunca inventar número
- Eval iq001 + iq008 ajustados
- D1 field renombrado a `meta_revenue_net_mxn` (solo reporting interno, nunca al guest)
- Risk #12 nuevo: "Bot muestra precio incorrecto al guest"

**Por qué importa:** si bot dice "$28,789" y guest ve "$35,000" en Airbnb (con service fee + taxes), guest piensa que estamos mal informados o engañando. Reputation hit.

---

## Lo que pediste anoche

Tarea autónoma 8h:
1. ✅ Revisar threads + KB para entender estado actual
2. ✅ Decidir bot único vs separado + spec del bot Airbnb
3. ✅ Web research best practices competidores
4. ✅ Investigar attachments Beds24/Airbnb
5. ✅ Brain ultra: propuestas creativas adicionales

## Output

**thread/220** pusheado a rdm-discussion como draft. ~7,500 palabras. REV 2 con corrección de precio.

[github.com/alexanderhorn6720/rdm-discussion/blob/main/threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md](https://github.com/alexanderhorn6720/rdm-discussion/blob/main/threads/220-wc-brain-ultra-airbnb-bot-spec-and-research.md)

## Los 5 hallazgos clave (orden de importancia)

### 1. El 70% del bot Airbnb ya existe

Beds24 recibe inquiries perfectamente (90 reales, última hace ~6h, Ana Karen pidió por chef y víveres). Bot las ve y NO hace nada (`action_taken='skipped_inquiry'`). Sistema D1 está completo. Templates designed thread/35. Pero **el orchestrator nunca se construyó**. Es un gap de 8-12h CC, no de 80h como sugería plan original B.2.

### 2. Lifecycle post-booking también existe pero está dormido

`scanForWelcome`, `runPreArrivalScan`, `runPostStay` están todos LIVE. Lo que falta es **activar `MESSENGER_OUTBOUND_ENABLED='true'`** + pegar 32 templates Phase B.1 en R2. ~6-10h CC.

### 3. Encontré los 4 archivos JSON que mencionaste

`knowledge/airbnb-templates-current-2026-05-13.json` (39 KB) + 3 archivos relacionados. **28 templates canónicos** (inquiry, welcome, pre-arrival, post-stay, eventos). Los usé como training reference para el spec.

### 4. Bot único, NO bots separados

Las KBs son 85% iguales. `sendMessageRouted` ya abstrae channel. Bots separados = duplicación pesada. Tono unificado con micro-adjustments (más emojis WA, menos Airbnb).

### 5. Attachments — NO PDFs en Airbnb

Airbnb solo JPG/GIF/PNG. PDFs solo Vrbo/WhatsApp. Limit 2MB Beds24. Implicación: cotización detallada va por texto largo o link a página, NO PDF.

## Recomendación voto WC preliminar

**Plan PR1 → PR2 → PR3 en 4-6 semanas:**

| PR | Effort CC | Effort Alex | Risk | Output |
|---|---|---|---|---|
| PR1 (esta semana) | 8-12h | 0h | muy bajo | Infra + approval mode + 0% canary |
| PR2 (próxima) | 8-10h | 4-6h templates | medio | 8 templates enriched + canary 10%→100% |
| PR3 (+2 semanas) | 6-10h | 4-6h templates | medio-alto | Lifecycle post-booking activación |

**Total:** 24-32h CC + 8-12h Alex/Karina.

**Costo Anthropic:** <$5/mes a full automation. ~$60/año.

**Mejora esperada:** Response time 2h → <5 min (24x). Industry data: +25% conversion rate con <1h response.

## Decisiones cerradas (no preguntar de nuevo)

- ✅ Bot único con context switch por canal
- ✅ 2 mensajes (corto + sexy enriched)
- ✅ Mix costeño + neutral
- ✅ Emojis funcionales (safe blocklist verificado)
- ✅ Rating ⭐ 4.84 / 168 exacto (KB ground truth)
- ✅ **REV 2:** Tarifa Airbnb → "la tarifa que ya viste en Airbnb", NUNCA número del payload
- ✅ Composer determinista (anti-hallucination)
- ✅ Casa Chamán EXCLUIDA del bot
- ✅ Idioma respuesta = idioma del mensaje (NO payload.lang miente)

## Lo que necesito de ti

Cuando despiertes, 5 preguntas en §12 del thread/220. Las repito acá:

1. ¿OK con plan PR1 → PR2 → PR3 en 4-6 semanas?
2. ¿OK con tono mix costeño + neutral, 2 mensajes, emojis funcionales?
3. ¿Karina disponible para 4-6h templates polish próxima semana?
4. ¿OK que CC arranque PR1 cuando confirmes, autónomo?
5. ¿Hidden constraint que no consideré?

## 8 inconsistencias cross-channel que el bot va a destapar

El bot va a hablar con clientes con info inconsistente. Hallazgos del audit:

1. **Servicio Las Morenas** templates dicen "incluido", verdad es OPCIONAL ($1000/$1500). Fix en templates B.2.
2. **Reseñas count** templates dicen 150/300, actual Airbnb dice 168/128/180+.
3. **Combinada capacity** 58 vs 60 — confirmar con Karina.
4. **WiFi Morenas** `Rincondelmar1` ≠ otros 3 `rincondelmar`. Combinada Manual incompleto.
5. **Clave caja "6720"** universal 4 villas — security risk.
6. **Paquete bodas** templates dicen $1000, actual es $1400.
7. **Cancelación asimétrica** RdM/Combinada Superestricta vs Morenas Estricta vs Huerta Firme — bot debe mencionar.
8. **Páginas missing** `/guia-llegada` y `/eventos` dan 404, templates linkean ahí.
9. **(NEW REV 2)** "Total Airbnb" no se puede mostrar — payload.price = net Alex, no total guest. Bot nunca muestra número.

Ninguno bloquea PR1. Algunos se fixean en PR2 templates polish. Otros requieren acción separada (e.g., crear `/eventos` page).

## 15 ideas creativas (§7 del thread/220)

Demasiadas para listar acá. Top 3:

- **Upsells dinámicos post-confirmation** — chef Morenas $1K-1.5K/booking, compras víveres 5%, paquete bodas $50K-100K
- **VIP/repeat guest detection** — match phone/email/name, "Qué gusto verte otra vez"
- **Foto attachment trust signal** — JPG Chef Celene cocinando para inquiries entusiastas

Las 12 restantes en §7 del thread/220 completo.

## Riesgo principal de NO hacer esto

Cada inquiry sin respuesta rápida = lead perdido o conversion baja. Ana Karen anoche esperó 2h. Si en lugar de eso otros guests buscan otra propiedad mientras esperan = revenue evaporado.

**Industry baseline:** <1h response = +25% conversion. **Tu actual:** 2h. **Target post-PR2:** <5 min.

## Sesión cerrada

Te dejo todo listo. Cuando estés despierto y leído, las preguntas 1-5 son lo único que necesito.

Buenos días. ☀️

— WC, 2026-05-27 overnight autonomous + REV 2 post-feedback
