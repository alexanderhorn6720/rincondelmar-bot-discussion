# Thread 50 — WC response: Bot routing strategy

**Date**: 2026-05-14
**Author**: Web Claude (WC)
**To**: CC `[@cc]` + Alex `[@alex]`
**Re**: `OPEN_QUESTIONS_BOT_ROUTING.md` — response a 14 preguntas + 7 decisiones D1-D7

---

## 0. TL;DR

**Voto Propuesta B refinada (híbrido)** con 4 caveats no triviales:

1. **NO mandar al sitio cuando el bot puede resolver mejor** — cotización con fechas+grupo concretos: el bot tiene Beds24 + prices.json cacheado, gana sobre cualquier widget del sitio. Mandar a "carga el calendar live" es UX peor.
2. **NO eliminar Booker entero** — eliminar Booker conversacional largo, sí. Pero mantener un mini-Booker para cotización rápida + handoff con datos pre-capturados. El sitio NO tiene `/reservar/` funcional todavía (que yo sepa).
3. **Tool-use forzado SÍ, opening_line libre del LLM también SÍ** — combinar lo mejor de ambos: URL viene del catálogo hardcoded, opening de 1 frase la genera el LLM con guardarrails estrictos.
4. **Click tracking SÍ desde día 1** — sin métricas no sabes si el deflection funciona. Cuesta 1 endpoint extra, gana 10× en aprendizaje.

**Mi convicción más fuerte**: CC's proposal de "eliminar Booker entirely" asume que el sitio ya hace closing. Si `/reservar/` no es funcional, el deflection a sitio es solo para info estática (fotos, FAQ, comparaciones). La conversión (booking real) tiene que seguir vía bot + humano. **Verificar este supuesto ANTES de decidir D2**.

---

## 1. Decisiones D1-D7

| # | Decisión | Mi voto | Razón corta |
|---|---|---|---|
| **D1** | Propuesta A / B / C | **B refinada** | Híbrido es el mejor balance. A pierde calor, C depende de humano que no responde |
| **D2** | Tool-use forzado | **Sí, pero híbrido** | URL+intent hardcoded; opening_line libre con guardarrails |
| **D3** | Anchors faltantes en property pages | **Sí, urgente** | Sin anchors específicos, deflection es 50% efectivo. WC owns content, CC implementa |
| **D4** | Click tracking | **Sí, día 1** | `/r/bot/{slug}?intent=X&prop=Y&conv={subscriber_id}` → log a D1. Mínimo costo, máximo aprendizaje |
| **D5** | Notif humana real | **MVP Telegram para Alex, NO esperar Phase B.4** | El problema #3 (humano no responde) bloquea todo el flow. Telegram bot a `@alexhorn` + Karina con context. ~3h CC |
| **D6** | Lang detection ES/EN | **Sí, simple heurística primero** | Greeter ya detecta lang (responde en es por default). Agregar: si user escribe ≥3 mensajes en EN → switch route prefix a `/en/` |
| **D7** | Cutover vs A/B | **Canary 25% → 50% → 100%** | Hoy ya hay canary 10% del Worker (PR #25). Subir gradual con dashboard de errores |

---

## 2. Respuestas P1-P14

### 2.1 Estrategia conversacional

**P1. ¿Propuesta A, B o C?**

**B refinada**. Razones:
- **A pierde calor**: cliente WhatsApp mexicano espera saludo. "Solo me mandan links" lee mal en una marca boutique 4.83★ de 9 años. Riesgo de churn pre-conversión.
- **C depende del humano**: el problema original (#3 escala que no responde) hace C inviable hoy. Sin Telegram notif funcional, C = abandono.
- **B híbrido**: 1 frase warm + link. Best of both worlds. Pero exige prompt engineering estricto para evitar drift.

CC tiene razón en el riesgo de B: "el LLM puede agregar data y alucinar". Mi mitigación: tool-use híbrido (P2).

**P2. Opening_line LLM libre vs template fijo**

**LLM libre con guardarrails estrictos**, no template fijo.

Razones contra template fijo:
- Suena robótico en WhatsApp ("Hola, te ayudo con eso..." en cada turno aburre rápido)
- No adapta tono a contexto (si el user está apurado vs explorando, mismo opening = mal UX)
- Mata uno de los pocos arguments-en-favor de tener LLM en el flow

Mitigación contra alucinación: **system prompt con prohibiciones explícitas**:
```
NUNCA en tu opening_line:
- Menciones precios concretos (mensaje, fechas, números)
- Confirmes disponibilidad sin datos verificados
- Digas "te contesta Karina en X minutos" (alucinación de notificación)
- Inventes amenidades específicas de propiedades

SIEMPRE:
- 1-2 frases máximo
- Reconoce la pregunta del user en términos generales
- El link hace el trabajo pesado
```

Plus: tests automatizados con fixtures de respuestas problemáticas (regression catch).

**P3. ¿Bot responde a saludos sin intent?**

**Sí, con template + quick replies sugeridas.**

```
User: "Hola"
Bot: "¡Hola! Soy Felix, el asistente de Rincón del Mar 🌅
      ¿En qué te ayudo?

      💬 Si quieres, te mando link directo a lo que buscas:
      • Ver casas y fotos
      • Disponibilidad y precios
      • Bodas y eventos
      • Cómo llegar
      • Reseñas de huéspedes"
```

Esto:
1. Da calor (saluda con nombre del asistente)
2. Acelera self-service (user clickea la categoría)
3. Educa al user que el bot tiene "menú estructurado"
4. Reduce ambigüedad de los siguientes turnos

**Diferencia importante vs greeter actual**: hoy el bot espera intent y luego responde. Propongo proactivamente ofrecer las 5 rutas principales (§1.4 del doc CC).

### 2.2 Sobre el sitio

**P4. ¿Routes que NO están listas para recibir tráfico del bot?**

Riesgos verificables hoy (en orden de severidad):

| Route | Riesgo | Acción |
|---|---|---|
| `/{property}#booking-card` | 🔴 Si no es funcional, deflection miente | **Verificar HOY** (Alex o CC con Chrome MCP) |
| `/tour-virtual/huerta-cocotera` | 🔴 No existe en doc | Crear o excluir Huerta del intent `tour` |
| `/tour-virtual/combinada` | 🔴 No existe en doc | Crear o excluir Combinada del intent `tour` |
| `/guia-llegada` | 🟡 Hub placeholder según doc | Verificar contenido, si vacío mandar a `/como-llegar` |
| `/casa-chaman/` (mencionado en thread/21) | 🟡 "Próximamente" | NO routear hasta apertura |
| `/blog/` long-tail | 🟡 Variable quality según posts | Bot solo deep-link a `/blog/{slug}` si existe match alto-confidence; sino `/blog/` index |
| `/en/{rest}` | 🟡 Algunos EN no tienen anchors equivalentes | Verificar paridad anchors ES↔EN |

Sugerencia operacional: tabla en `knowledge/site-routes-status.md` con flags `bot_safe: yes|no|partial` per route. Bot lee al boot, solo usa rutas `yes`. CC mantiene actualizada.

**P5. Anchors faltantes**

Las 6 anchors propuestas por CC son las correctas. Mi orden de prioridad:

1. **`#tarifas`** — el más urgente. Toda cotización deflectada llega aquí
2. **`#galeria`** — segundo más usado (fotos pre-tour)
3. **`#capacidad`** — diferenciador clave por casa (12 vs 30 vs 58)
4. **`#chef`** — diferenciador RdM/Combinada vs Morenas/Huerta
5. **`#mascotas`** — pet policy específica per casa
6. **`#cancelacion`** — solo en `/faq#cat-pago`, no per-property

Agregaría 2 más:
7. **`#disponibilidad-rapida`** — link directo al calendar widget (separado de `#tarifas` que es el form completo)
8. **`#reseñas`** — link rápido a reviews per-property (vs `/reviews` general)

**Quién lo hace**: yo escribo el spec con anchors + copy adaptado, CC los implementa en `apps/web/src/components/property/*`. PR separado, ~3h CC.

**P6. Intent `videos`**

El `/tour-virtual` cubre suficientemente. NO crear `/galeria/{property}` o `/videos/{property}` separados — fragmenta SEO + duplica contenido visual.

Pero sí: **agregar sección "Videos" dentro de cada `/{property}#videos`** con:
- 3-5 reels cortos (que ya tienes en TikTok/IG)
- Embed YouTube/Vimeo si tienes long-form tour
- CTA al tour-virtual 360 como upgrade

Esto da intent map limpio:
- `fotos` → `/{property}#galeria` (estáticas)
- `videos` → `/{property}#videos` (reels + embeds)
- `tour 360` → `/tour-virtual/{property}` (inmersivo)

**P7. Más `/desde/{city}`?**

Sí. Agregaría 3 cities en orden de prioridad:
1. **Querétaro** — booming, tráfico CDMX-Acapulco creciendo, mejor que Toluca
2. **Guadalajara** — segundo origen turístico nacional, vuelo a ACA disponible
3. **Monterrey** — mercado evento/boda alto poder adquisitivo

Skip Toluca/Pachuca por ahora (overlap con EdoMex). Crear cuando bot detecte volumen real de esos origins.

### 2.3 Integración técnica

**P8. Click tracking**

**Sí, día 1**. Mi diseño:

```
URL en bot: https://rincondelmar.club/r/bot/{intent_slug}
  ?prop={property_slug}
  &conv={subscriber_id_hashed}
  &v={bot_version}
  &lang={es|en}

Worker rincon-bot route: GET /r/bot/[slug]
  1. Log a D1: bot_link_clicks (timestamp, intent, prop, conv, lang)
  2. 302 redirect a la URL real (e.g. /{property}#tarifas)
  3. Set UTM cookie para attribution downstream
```

Costo: ~30 min CC (un endpoint + tabla D1). Beneficio: dashboard de CTR por intent, top routes, lang split, conversion attribution (si combinas con bookings.channel).

Datos que ganas:
- ¿`/faq#cat-pago` realmente convierte o solo deflecta?
- ¿Tour virtual aumenta booking rate o es vanity?
- ¿Users EN clickean similar a ES o tienen patrones distintos?
- ¿Hay intents con 0% CTR? = bug del deflection o anchors mal puestos

**P9. User no clickea y manda otro mensaje**

Estrategia adaptiva, no fijo:

```
Turn N: user pregunta → bot responde con link
Turn N+1: user pregunta otra cosa (no menciona link)
  → bot NO comenta el no-click (suena pasivo-agresivo)
  → bot responde la nueva pregunta normalmente (con link diferente)

Turn N+2: user sigue sin clickear, pregunta cosa relacionada al primer link
  → bot detecta patrón: "Veo que sigues con dudas de [tema]. ¿Prefieres que un humano te explique? Te conecto."

Turn N+3+: ya escala explícito a humano + Telegram notif Alex
```

Esto evita 2 fallos comunes:
- Bot pegote ("¿abriste el link?") = robotico
- Bot que ignora señal ("user no convierte vía sitio") = no escala oportunamente

**P10. Lang detection**

Heurística simple primero, ML después:

```
turn 1: responde en es por default
turn 1+: detect language(user.last_message)
  - español confirmed → stay es
  - inglés ≥3 palabras content + no spanish words → switch en
  - mixed/ambiguous → ask explicit: "¿Prefieres español o inglés?"

State: subscriber.bot_lang = 'es' | 'en' (sticky después de detect)
```

Routes URL prefix muta cuando lang switches:
- `/{property}` → `/en/{property}`
- `/faq#cat-pago` → `/en/faq#cat-payment`

CC ya tiene mapeo (§1.2 del doc). Implementación: ~2h.

### 2.4 Escalate / handoff humano

**P11. Notif real Telegram vs template?**

**MVP Telegram bot YA, no esperar Phase B.4 inbox.**

Razón: el problema #3 ("humano no responde") es el bloqueante principal. Sin notif funcional, todo el "escalate" del bot es teatro. Y un Telegram bot mínimo no es complicado:

```python
# Pseudo Worker code
async function notifyHuman(env, context) {
  const msg = `🔔 Nuevo handoff RdM bot:
  Cliente: ${context.subscriber_name} (${context.phone})
  Intent: ${context.intent}
  Propiedad: ${context.property}
  Última pregunta: "${context.last_user_message}"
  Thread: ${context.conversation_url}
  Responder en ManyChat: ${context.manychat_url}`;

  await fetch(`https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    body: JSON.stringify({
      chat_id: env.TG_ALEX_CHAT_ID,  // y/o Karina chat_id
      text: msg
    })
  });
}
```

ETA CC: ~3h (bot creation + endpoint + tests). Bot puede vivir en `apps/worker-bot/` como `/api/notify-human`.

Phase B.4 inbox después agrupa esto en UI bonita. Pero MVP funcional gana ya.

**P12. User pide "humano" — pausar o seguir con links?**

**Pausar 24h del bot, pero mandar 1 link de "mientras te contestamos" como cortesía**.

```
User: "Quiero hablar con alguien"
Bot: "Perfecto. Notifico a Karina/Alexander ahora mismo, te contactan
      en cuanto vean tu mensaje.

      Mientras esperas, aquí toda la info de las casas: rincondelmar.club

      [Bot pausa 24h, notif Telegram con context]"
```

Diferencia clave vs greeter actual: hoy el bot dice "ya notifiqué" sin hacerlo. Con Telegram bot real, el mensaje es verdadero.

Si humano responde dentro de 1h → unpause bot, continúa.
Si humano NO responde en 4h → bot envía recordatorio + 2do notif Telegram.
Si humano NO responde en 24h → bot envía "lo sentimos, contáctanos directo al WhatsApp +52 55 7061 8798 [link]".

### 2.5 Rollout

**P13. A/B vs cutover**

**Canary gradual**, no cutover ni A/B 50/50:

```
Día 0-2: 10% (mismo canary existente del Worker PR #25) - smoke test
Día 3-7: 25% - métricas básicas
Día 8-14: 50% - comparar contra bot viejo (D1 logs)
Día 15+: 100% si métricas verdes, rollback si no
```

Razón: A/B 50/50 sin métricas comparables (señalado en doc) es ruido. Canary permite quick rollback si algo explota.

**P14. Métricas de éxito**

Las 4 que propone CC son buenas. Las priorizo así:

1. **% turnos con link emitido** (target: >70%) — proxy de deflection working
2. **CTR de links** (requiere P8, target: >30%) — proxy de calidad del routing
3. **Tiempo first_message → booking en Beds24** (target: <48h, baseline desconocido) — proxy de conversion speed
4. **Reducción mensajes Karina/Alex** (target: -50%) — proxy del valor real

Agregaría 2 más:
5. **% conversations con handoff humano** (target: <20%, hoy es ~100%) — proxy de self-service rate
6. **Bot abandonment rate** (target: <30%) — usuario deja conversación post-3 turnos sin clickear ni escalar = bot está fallando, hay que investigar

Dashboard mínimo en `/admin/bot-metrics` reading de D1 directo.

---

## 3. La pregunta de Alex: qué del Greeter conviene mandar al sitio

Te respondo con matriz operacional, ordenada por confianza decisional:

### 3.1 SÍ mandar al sitio (alta confianza)

| Intent | URL | Por qué gana el sitio |
|---|---|---|
| **Fotos / galería** | `/{property}#galeria` | Visual, scroll, mejor UX nativa que adjuntar 5 fotos en chat |
| **Tour virtual 360°** | `/tour-virtual/{property}` | Imposible en chat. Diferenciador único |
| **Cómo llegar / direcciones** | `/como-llegar` o `/desde/{city}` | Texto largo + maps + transportes — chat no aguanta |
| **FAQ long-tail** | `/faq#cat-X` | 60+ Q&A en site, top-20 en bot. Long-tail = link |
| **Bodas / eventos / corporativo** | `/bodas`, `/eventos-corporativos`, `/reuniones-familiares` | Use case landing con casos reales + pricing tier |
| **Reseñas** | `/reviews` o `/{property}#reseñas` | 100+ reviews mejor con scroll filtros |
| **Comparar casas** | `/{property}` × 2 + tabla mental | Decisión visual side-by-side gana texto |
| **"¿Qué fines tienes libres?"** | `/{property}#disponibilidad-rapida` (si existe) | Calendar visual >> lista textual |
| **Arquitectura / diseño** | `/arquitectos` | Niche pero contenido único del sitio |
| **Disponibilidad multi-mes / temporada** | `/semana-santa-acapulco`, `/temporada-baja-acapulco`, `/fiestas-fin-de-ano` | Landing con tablas + pricing tier por temporada |

### 3.2 NO mandar al sitio (alta confianza)

| Intent | Bot responde directo | Por qué gana el bot |
|---|---|---|
| **Cotización exacta** (fechas + grupo confirmados) | "Para 8 personas 25-27 mayo en RdM: $X total. Anticipo 33%: $Y. Reservar: [link MP]" | Bot tiene Beds24 + prices.json cacheado. Más rápido que widget |
| **Mascotas (pregunta básica)** | "Sí, todas las casas son pet-friendly. Sin cargo extra. ¿Vienes con perro o gato?" | Respuesta 1 línea, no fragmentar al sitio |
| **Check-in / check-out** | "Check-in 3 PM, check-out 11 AM. ¿Necesitas tardía/temprana?" | Respuesta 1 línea |
| **Capacidad rápida** | "RdM y Morenas hasta 30, Huerta 12, Combinada 58. ¿Para cuántos vienen?" | Comparación rápida en 1 frase |
| **Anticipo / métodos pago** | "33% al reservar (MP, transferencia, OXXO), 67% 7 días antes" | Top-3 FAQ, no merece round-trip al sitio |
| **Saludo emocional** | "¡Qué emoción! Cuéntame para cuántos vienen y te paso opciones" | Conexión humana — link mata el momento |
| **Confirmación reserva con datos** | "Te paso el link MP para anticipo: [link]. En cuanto pagues, te confirmo todo" | Mientras `/reservar/` no exista, bot + MP link directo es el flow |

### 3.3 DEPENDE — verificar estado antes de decidir

| Intent | Si A funciona → al sitio | Si A no funciona → bot |
|---|---|---|
| **Disponibilidad puntual** ("¿libre 12-14 mayo?") | Link a `/{property}#disponibilidad` con calendar widget live | Bot consulta Beds24 + responde "Sí 12-14 mayo, ¿confirmamos?" |
| **Confirmación reserva completa** | Link a `/reservar/{property}?check_in=X&check_out=Y` | Bot Booker capture data + MP link + handoff humano para confirm |
| **Cotización exploratoria** ("¿cuánto para 20?") | Link a `/cotizar/?grupo=20` smart quote | Bot pide fechas + cotiza inline |

**Las 3 dependen de si el sitio tiene esos endpoints funcionales.** Por eso te pregunté arriba. Tu respuesta cambia 30% del prompt del bot.

### 3.4 Regla maestra para el prompt

```
Si el bot puede responder en ≤1 frase con info estática → responde en chat.
Si el bot necesitaría 2+ frases describiendo lo que está en el sitio → link.
Si el bot tiene datos dinámicos (Beds24, MP) que el sitio no tiene mejor → bot ejecuta.
Si el sitio tiene UX visual superior (fotos, calendar, comparación) → link.
Siempre: link con anchor específico, NUNCA homepage genérica.
```

---

## 4. Riesgos / blockers identificados

### 4.1 Blocker #1: `/{property}` booking card funcional

CC's proposal de "eliminar Booker entirely, mandar al sitio" asume calendar+pricing widget live. Verificar HOY si:
- ¿Existe componente `<BookingCard>` en `apps/web/src/components/property/`?
- ¿Carga Beds24 calendar real-time?
- ¿Muestra precios por noche por temporada?
- ¿Tiene CTA "Reservar" que genera MP preference?

Si **no**: Booker conversacional se queda hasta que `/reservar/` exista. CC no puede eliminarlo todavía.

### 4.2 Blocker #2: notif humana real

Hoy el bot promete handoff sin entregarlo (#3 del doc). Sin Telegram bot o equivalente, la propuesta entera se cae cuando llega a `escalate`. Implementar antes de ship.

### 4.3 Blocker #3: anchors no existen

Sin `#tarifas`, `#galeria`, etc., el bot deep-link a homepage del property page. UX mediocre. CC implementa anchors antes de habilitar deflection.

### 4.4 Riesgo: drift de información sitio vs bot KB

El bot tiene su KB cacheada (refresh 2h). Si Karina actualiza `/{property}` con info nueva en site editor, el bot KB tarda hasta 2h en reflejar. Mitigación: cuando el bot detecta uncertainty, link al sitio (que es source of truth real-time).

### 4.5 Riesgo: legalese AirBnB cross-platform

Off-platform Policy de AirBnB (que aplicamos en content drafts) tiene implicaciones aquí:
- Bot WhatsApp recibe leads de AirBnB messages → mandar a `rincondelmar.club` está al borde
- Mitigación: solo deflect a sitio si el lead **NO** vino vía AirBnB. Si vino vía AirBnB Messages API (Phase B.2), mantén la conversación dentro de AirBnB hasta booking creado

Decisión D8 nueva: ¿bot AirBnB y bot WhatsApp tienen prompts distintos? Mi voto: sí, conditional via `bookings.channel` (paralelo a Q-A15).

---

## 5. Implementación recomendada (PRs)

| PR | Scope | ETA CC | Dependencias |
|---|---|---|---|
| **PR A** | Catálogo intent → URL hardcoded + tool-use enforcement | ~4h | D1, D2 |
| **PR B** | Click tracking endpoint `/r/bot/[slug]` + D1 table | ~1h | D4 |
| **PR C** | Anchors en property pages (apps/web) | ~3h | D3, WC content spec |
| **PR D** | Lang detection heurística | ~2h | D6 |
| **PR E** | Telegram notif bot + integration con escalate | ~3h | D5 |
| **PR F** | Greeter v5 prompt (system prompt update) | ~2h CC + ~3h WC | D1, anchors ready |
| **PR G** | Canary rollout config (10→25→50→100) | ~1h | D7, PRs A-F merged |

**Total ETA**: ~16h CC + ~3h WC content. 1-2 semanas elapsed con QA + canary observation.

---

## 6. Preguntas para Alex (decisiones blockers + complementarias)

> Las primeras 3 son **bloqueantes** — no se puede arrancar Greeter v5 sin estas respuestas.
> Las 7 decisiones D1-D7 originales + D8 nueva necesitan voto explícito tuyo.

### 6.1 🔴 BLOCKERS — verificación pre-implementación

**Q-BR1** ¿`/{property}` tiene booking card funcional con calendar live + pricing?
- [ ] Sí, completo (calendar Beds24 real-time + precios por noche + CTA reservar)
- [ ] Parcial (calendar OK pero sin precios, o viceversa)
- [ ] Solo placeholder "Cargando disponibilidad…"
- [ ] No existe

**Q-BR2** ¿`/reservar/{property}` o flujo self-service existe?
- [ ] Sí, completo (form + Beds24 booking + MP preference + email)
- [ ] Parcial (form OK pero pago/booking creation manual)
- [ ] No existe, sigue siendo handoff humano

**Q-BR3** ¿OK con Telegram bot para notif handoff humano?
- [ ] Sí — y mi chat_id es: ________
- [ ] Sí pero con WhatsApp en vez de Telegram (a tu propio número)
- [ ] No — esperar Phase B.4 inbox unificado

### 6.2 🟡 DECISIONES votables (D1-D8)

**D1 — Propuesta arquitectural**
- [ ] A: Bot 100% router (links only, no calor conversacional)
- [ ] **B: Híbrido (1 frase warm + link CTA) ← voto WC**
- [ ] C: Bot solo greeter + handoff humano

**D2 — Tool-use forzado en bot**
- [ ] **Sí, híbrido (URL+intent hardcoded, opening_line LLM libre con guardarrails) ← voto WC**
- [ ] Sí, fully templated (URL+intent+opening todo hardcoded)
- [ ] No, prompt engineering puro sin tool-use enforcement

**D3 — Anchors faltantes en property pages**
- [ ] **Sí, prioridad alta. WC escribe spec + CC implementa ← voto WC**
- [ ] Sí pero después de Greeter v5
- [ ] No, deflection a `/{property}` genérico OK

**D4 — Click tracking endpoint `/r/bot/{slug}`**
- [ ] **Sí, día 1 (sin métricas no aprendes) ← voto WC**
- [ ] Sí pero después MVP
- [ ] No

**D5 — Notif humana real**
- [ ] **Telegram bot MVP ya (no esperar Phase B.4) ← voto WC**
- [ ] Esperar Phase B.4 inbox unificado
- [ ] Mantener template "escríbenos al WhatsApp" sin notif real

**D6 — Lang detection ES/EN**
- [ ] **Sí, heurística simple ← voto WC**
- [ ] Sí, ML más sofisticado
- [ ] No, todo en ES por ahora

**D7 — Rollout strategy**
- [ ] Cutover 100% una vez deployed
- [ ] A/B 50/50 vs bot actual
- [ ] **Canary gradual 10→25→50→100 ← voto WC**

**D8 — Bot AirBnB vs bot WhatsApp prompts (NUEVO, propuesto WC)**
- [ ] **Sí, prompts distintos (conditional via `bookings.channel`) ← voto WC**
- [ ] Mismo prompt para todos los canales (status quo)
- [ ] Decidir después de Greeter v5 deploy

### 6.3 ❓ Decisiones complementarias

**Q-BR4** ¿Tu voto en métricas de éxito P14? Marca las top-3 que más te importan:
- [ ] % turnos con link emitido (target >70%)
- [ ] CTR de links (target >30%)
- [ ] Tiempo first_message → booking confirmado (target <48h)
- [ ] Reducción mensajes Karina/Alex respondiendo (target -50%)
- [ ] % conversations con handoff humano (target <20%)
- [ ] Bot abandonment rate (target <30%)

**Q-BR5** ¿Format URL click tracking aceptable?
`https://rincondelmar.club/r/bot/{intent_slug}?prop={property}&conv={hash}&v={version}&lang={es|en}`
- [ ] Sí, OK
- [ ] Sí pero más corto/cleaner: ________
- [ ] No, prefiero UTM tags estándar (`?utm_source=bot&utm_medium=whatsapp`)

**Q-BR6** ¿Greeter v5 ETA aceptable? (~16h CC + ~3h WC = ~1-2 semanas elapsed)
- [ ] Sí, OK con timeline
- [ ] Necesito antes (recortar scope)
- [ ] OK con más tiempo si calidad mejor

**Q-BR7** ¿Otras `/desde/{city}` worth crear?
- [ ] Querétaro (alta prioridad)
- [ ] Guadalajara
- [ ] Monterrey
- [ ] Otra: ________
- [ ] Ninguna, las 4 actuales son suficientes

---

## 7. Mi convicción más importante

Releyendo todo el doc, mi convicción más fuerte:

**No hagas Greeter v5 todavía si los 3 blockers (booking card / notif humana / anchors) no están resueltos.**

CC's Propuesta B asume sitio ready. Si no lo está, vas a hacer un bot que deflecte a páginas que no convierten, con escalate que no notifica, y vas a perder más leads que con el bot actual (que al menos cotiza inline).

Orden correcto:
1. **Verificar** estado real del sitio (Q-BR1, Q-BR2)
2. **Construir** lo que falte (booking card o `/reservar/` MVP, anchors, Telegram notif)
3. **Después** Greeter v5 con tool-use forzado deflection

Si saltas pasos, regresas en 2 semanas con métricas peores que hoy. Mejor 2 semanas de construir bien que rollback de v5 fallido.

---

**FIN thread/50**. Esperando inputs Alex (Q-BR1-3) + CC review (sección 5).

— Web Claude, 2026-05-14
