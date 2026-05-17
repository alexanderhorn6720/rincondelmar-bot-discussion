# 91 · WC · Platform Vision & Spirit · context para sesión WC-rdmbot

**Modo:** brain (contexto/visión, NO spec, NO operacional)
**Audiencia:** otra sesión WC trabajando en `rincondelmar-bot` (apps/worker-bot, Greeter v6, Booker)
**Propósito:** transmitir el "por qué" del wishlist (threads 89), no el "qué"
**Relación con threads:** complementa thread 89 (qué módulos) y espera thread 90 (CC review técnico)

---

## ¿Por qué este thread existe?

Thread 89 documenta **qué** módulos vienen (5 prioritarios + 19 ideas + decisión PWA). Eso es el "operativo".

Este thread es el **espíritu**: por qué Alex quiere construir esto, qué problema real resuelve cada módulo en su día a día, qué métricas mentales tiene Alex para juzgar si algo "vale la pena". Sin esto, la otra sesión WC va a leer thread 89 como una lista técnica sin contexto, y va a tomar decisiones de diseño que no encajan con el modelo mental de Alex.

Este thread NO es brief para CC. Es brief para WC-rdmbot — la sesión WC que trabaja en greeter/booker y que va a ser interpelada para opinar/diseñar partes del wishlist conforme avanza.

---

## §1 · Quién es Alex y cómo opera

### Perfil

- **Operador-fundador**, no manager corporativo. Cuatro propiedades activas + una en pipeline (Casa Chamán Q3). Equipo pequeño de empleados con relaciones personales (Mary, Frank, Karina, Celene, Heber, Isis, Marisol, Maritza, Roberto, Miguel, Mónica, Josué). Esto no es Marriott, es una operación familiar profesionalizada.
- **Mentalidad técnica fuerte**: no quiere tools genéricas (rechaza PriceLabs/Beyond para pricing porque no entienden chef incluido, eventos locales, dependencias Combinada). Construye custom porque entiende sus reglas de negocio mejor que cualquier vendor.
- **Iteración incremental**: nunca pide "construye todo". Pide brain → spec → DoIt → verify. Valida arquitectura antes de implementación. Discute decisiones con WC antes de pasar a CC.
- **Estilo comunicación**: corto, técnico, sin elogios, sin emojis. Pregunta antes de asumir. Mobile-first (lee desde phone). Tablas sobre prosa.
- **Idioma**: español, pero la realidad es ES + EN técnico mezclado. Acepta ambos.

### Cómo opera el negocio hoy

- ~70% bookings vía Airbnb, resto directo y Booking.com
- Cuatro villas con 4.83★ aggregate / 365+ reviews / ~1,500 bookings históricos
- Compradores externos (Heber/Isis) hacen mercados via WhatsApp lists ad-hoc, sin sistema
- Karina (co-host Morenas) hace de "todo": review fotos, content, escalación, vendor management
- Pricing manual / Make pausado / Beds24 daily prices estáticos = revenue dejado en la mesa
- Comunicación con empleados: 100% WhatsApp ad-hoc, sin tracking, sin recordatorios estructurados
- Tasks recurring están en la cabeza de Karina/Alex, no documentadas
- Photo audits post-checkout son visuales, manuales, sin baseline
- TikTok creciendo (3,721 followers, 668K viral) pero sin pipeline content automation
- Sitio rincondelmar.club ya tiene booking engine que consume `/calendar` de Beds24

### Pain points reales que Alex articula

1. **Revenue dejado en la mesa** por pricing estático y orphan days
2. **Karina sobrecargada** con tareas que requieren coordinación pero no juicio (audits, content review, vendor coordination)
3. **Empleados sin estructura** de comunicación operativa más allá de WhatsApp ad-hoc
4. **Compras de mercado** opacas en costos unitarios (sabe agregados, no unidades)
5. **Casa Chamán** viene en Q3 y necesita estar lista para escalar capacity operacional, no improvisar
6. **Reviews 4.83★ históricos** son un asset desperdiciado: no se reusan en content, KB, marketing
7. **No tiene visibilidad de unit economics** por booking (qué tipo de booking es realmente rentable)

---

## §2 · Espíritu del wishlist · qué quiere Alex de cada módulo

Esto no está en thread 89 explícito porque es subjetivo. Pero es esencial.

### M1 · Pricing Agent — espíritu

**Lo que Alex quiere:** un sistema que piense como él pero a las 6 AM todos los días sin cansarse. Conoce las reglas duras (floors, ceilings, premium seasons no se tocan, Combinada no descuento, anti-orphan agressive), pero quiere que la máquina haga el grunt work de aplicarlas a 4 propiedades × 360 días × 6 dimensiones.

**Lo que NO quiere:** una black box LLM que decide precios sin auditoría. Por eso el modelo es **reglas duras + LLM solo para explicar al humano**. Auditable, reproducible, kill-switch siempre disponible.

**Métrica mental de éxito:** "¿subió mi ARN promedio este mes vs el anterior, sin que tenga que tocar nada manual?"

**Lo que valora explícitamente:** anti-orphan logic (gaps de 1-3 noches que se quedan sin reservar). Es donde más pierde plata silenciosamente.

### M2 · Menu / Grocery — espíritu

**Lo que Alex quiere:** que el huésped llegue y la comida ya esté planeada, comprada, en proporción correcta, con precio honesto. Hoy las listas de compras son ad-hoc WhatsApp, sin trazabilidad, con sobre-compras y sub-compras frecuentes.

**Lo que NO quiere:** un PWA tipo "MyFitnessPal de villas". Es decir, no sobre-engineerear. Captura simple + chef review obligatorio + lista de compras agrupada por proveedor.

**Métrica mental:** "¿reduce las dudas del huésped pre-arrival y el tiempo de Karina coordinando con Celene/compradores?"

**Lo que valora explícitamente:** 410 listas históricas + 157 resúmenes costos = oro escondido. Quiere que el sistema **aprenda** de su data histórica, no que se invente recetas desde cero.

### M3 · Inventory — espíritu

**Lo que Alex quiere:** dejar de descubrir que falta papel higiénico el viernes a las 9 PM cuando hay grupo de 20. Visibilidad proactiva de SKUs durables (no perecederos) en cada propiedad.

**Lo que NO quiere:** sistema enterprise tipo SAP de inventario con conteos semanales. Demasiado overhead para un equipo de 12-15 personas.

**Métrica mental:** "¿bajó la frecuencia de 'emergency runs' a Bodega Aurrera de Karina/Heber?"

**Lo que valora explícitamente:** señal de stock vía checklist post-stay (ama llaves marca ok/bajo/vacío al salir cada booking) — bajo costo operacional, alta frecuencia de update natural.

### M4 · Staff Scheduling — espíritu

**Lo que Alex quiere:** que Karina deje de ser el "scheduler humano" mental. Que empleados sepan su semana sin preguntar. Que asignación a bookings sea automática (si es Combinada + grupo 40 → chef + 2 mozos + cocinera ya asignados sin tocar nada).

**Lo que NO quiere:** sistema de RRHH formal con timeclock, vacation requests rígidos, IMSS compliance integrado. Eso es separado (contador externo) y excede scope.

**Métrica mental:** "¿Karina recibe menos mensajes WhatsApp del tipo '¿yo voy a Morenas mañana?'"

**Lo que valora explícitamente:** "mi semana" móvil per empleado entregado cada lunes 8 AM. Reduce 50% las preguntas operativas.

### M5 · Tasks — espíritu (NUEVO)

**Lo que Alex quiere:** dejar de mandar tasks por WhatsApp y olvidarse de si Mary realmente cambió la bombilla del baño master. Recordatorios automatizados. Foto de antes y después. Audit trail. Y bidireccional: que Frank pueda reportarle "aire master Morenas hace ruido raro" con foto, no que se quede en una nota mental.

**Lo que NO quiete:** Trello/Asana corporativo que requiera training a empleados. Tiene que ser dead-simple: PWA en home screen Android, notif push, 1-tap "completed" con foto opcional. Empleados que apenas usan smartphones tienen que poderla operar.

**Métrica mental:** "¿bajó la frecuencia de tasks 'olvidados' que descubro porque algo se rompió en plena estancia?"

**Lo que valora explícitamente:**
- **Recurring tasks** (filtros piscina cada 3d, purga calentador mensual, etc) — saca cosas tácitas que viven en la cabeza de Karina a sistema
- **Photo-verified completion** — cierra el loop de "¿se hizo o no se hizo?"
- **Bidireccional** — empleados reportan issues, no solo reciben tasks
- **Conector entre módulos** — task auto generada cuando stock bajo (M3) o cuando hay daño (I11) o cuando booking confirmado (M4)

### Decisión PWA — espíritu

**Lo que Alex quiere:** una sola "app" en el phone de cada empleado que cubra todo lo operativo (tasks, schedule, inventory checklist, etc). No 5 apps separadas. No instalar APKs raros. Que Karina pueda mandar un link por WhatsApp y el empleado lo agrega a home screen.

**Lo que NO quiere:** PWA que se sienta como un sitio web mobile. Tiene que sentirse como app: icono home screen, notif lock screen, splash screen, offline básico.

**Por qué PWA gana:** stack ya existente (Astro), iteración rápida primeros meses (CC entrega features semana a semana), zero install friction. Capacitor.js stand-by si algún día se necesita .apk nativo (Play Store, geofence real).

---

## §3 · Por qué el sequencing es así

Thread 89 propone: M1 Pricing → M5 Tasks → M4 Staff → I3/I2 In-stay → M3 Inventory → M2 Menu → ...

**No es arbitrario. Es por dependencias:**

1. **M1 Pricing primero** porque revenue immediate, no depende de nada operacional. Solo Beds24 calendar.
2. **M5 Tasks segundo** porque es el **habilitador de PWA staff**. Una vez que la PWA `apps/staff` existe con Tasks, agregar Inventory checklist y Schedule view es delta pequeño.
3. **M4 Staff** después porque empleados ya tienen PWA instalada (M5) y schedule es vista adicional.
4. **I3 In-stay bot + I2 Check-in QR** porque guest XP independiente, no depende de PWA staff.
5. **M3 Inventory** después porque depende de M5 (genera tasks auto cuando stock bajo).
6. **M2 Menu** al final de prioridades porque es más complejo (PWA huésped + recetas + grocery + chef review) y mayor payoff long-term.

**La lógica subyacente:** primero revenue (M1), después la infraestructura operacional empleados (M5+M4 via PWA staff compartida), después guest XP (I2/I3), después módulos complejos (M3, M2).

**Casa Chamán Q3** se beneficia de tener M1, M5, M4 ya estables para escalar capacity sin caos.

---

## §4 · Cómo razonar diseño para Alex

Cuando WC-rdmbot opine sobre cualquier parte del wishlist (Greeter integraciones, in-stay bot I3, lost-booking recovery I7, etc), considerar estos principios:

### Reglas duras > LLM en money decisions

Alex no acepta LLM decidiendo montos finales, descuentos, qué cobrar, qué deducir del depósito. LLM solo para:
- Explicación al humano (email summaries con reasoning)
- Detección edge cases (no clasificación numérica)
- Voz/tono comunicación al guest

### Encapsulación módulos

Cada módulo es PWA / endpoint / cron separado. **Bot conversacional NO se vuelve "sistema de todo"**. Greeter deflecta al módulo correcto con URL específica. Cada módulo testeable, deployable, debuggable independiente.

### Bot pre-booking ≠ Bot in-stay ≠ Bot post-stay

Tres "personalidades" distintas, mismo stack:
- Pre-booking (Greeter v6): deflecta al sitio, captura intent, handoff Booker — tono ventas
- In-stay (I3 future): asistente práctico durante estancia, KB casa específica — tono concierge
- Post-stay (I5/I18/drip): review request, UGC capture, feedback — tono relacional

Distinguir via `beds24_bookings.lifecycle = booked / in_stay / past_stay`.

### Reusar histórico

Alex valora explícitamente que el sistema **aprenda de data histórica**: 410 listas compras, 157 resúmenes costos, 1,500 bookings, 365+ reviews. No proponer recetas/precios/recommendations "from scratch" cuando hay 3.5 años de data real.

### Casa Chamán

NO incluir en Greeter prompt hasta renovation Q3. NO incluir en M1 Pricing rules hasta launch. Casa Chamán es módulo I19 standalone (coordinador del lanzamiento), no un 5to roomId que se agrega como bullet.

### Mobile-first siempre

Alex lee desde phone. Karina opera desde phone. Empleados usan phone. Cualquier UI/email/notif tiene que verse bien en pantalla chica. Tablas cortas. No prosa larga. Headers escaneables.

---

## §5 · Lo que esta otra sesión WC probablemente va a tocar

WC-rdmbot trabaja en `apps/worker-bot/` (Greeter v6, Booker). Conforme avance el wishlist, probablemente sea interpelada en:

| Módulo | Por qué WC-rdmbot |
|---|---|
| M1 Pricing | Vive dentro de `rincon-bot` worker. Comparte auth Beds24, KV, D1, alertas. WC-rdmbot conoce ese código. |
| I3 In-stay bot | Tercer Greeter (post-booking), comparte stack con Greeter v6 pre-booking. WC-rdmbot diseñaría el lane separado. |
| I5 Post-stay review request | Trigger desde lifecycle `past_stay`, integración con `beds24_bookings`. WC-rdmbot conoce el lifecycle. |
| I7 Lost-booking recovery | Trigger desde `quote_requests` D1 (creado por sitio/Booker). WC-rdmbot conoce el flow. |
| I8 VIP segmentation | Greeter v7 detecta repeat via phone match. WC-rdmbot toca el sistema prompt. |
| M5 Tasks notification | Fallback WhatsApp via ManyChat ya integrado en `rincon-bot`. WC-rdmbot conoce esa integración. |

Para el resto (M2 Menu PWA, M3 Inventory backend, M4 Staff Scheduling, M5 Tasks PWA principal), WC-rdmbot probablemente NO tenga visibilidad directa — son módulos separados (`apps/staff`, `apps/menu`, etc).

**Punto clave:** WC-rdmbot debe saber que el wishlist existe para no proponer cambios al Greeter/Booker que choquen con módulos futuros. Ejemplo: si WC-rdmbot quisiera agregar "managed addons" al Greeter, ya no — eso es I6 Upsell engine separado.

---

## §6 · Anti-patterns que esta sesión WC NO debe hacer

Tomados de CLAUDE.md + reforzados:

- **NO agregar Casa Chamán al Greeter system prompt** hasta renovation Q3 complete
- **NO usar Beds24 sync mode "Everything"** — siempre Prices&Availability
- **NO hacer Greeter "do-it-all"** — encapsular módulos separados
- **NO usar LLM para money decisions** (montos, descuentos, deducciones)
- **NO sobre-engineerear PWA** — empleados con phones modestos
- **NO proponer Trello/Asana feel** para M5 Tasks — debe ser dead-simple
- **NO romper bot pre-booking actual** mientras se agrega in-stay o post-stay
- **NO duplicar storage** — Beds24 es source of truth, no copias paralelas
- **NO usar PWAs separadas** (apps/tasks, apps/inventory, apps/schedule) — single `apps/staff` multimódulo. Voto WC firme.

---

## §7 · Cosas que esta sesión WC SÍ debería considerar proponer

- **Refactor Greeter v6 → v7** para soportar lifecycle awareness (pre-booking vs in-stay vs post-stay) sin romper retrocompatibilidad. Esto desbloquea I3, I5, I8.
- **Schema `quote_requests` D1** para tracking de cotizaciones no convertidas (habilita I7 lost-booking recovery, I9 drip campaign).
- **Schema `booking_lifecycle_events` D1** para tracking de eventos por booking (welcome enviado, in-stay started, checkout done, review requested, etc) — habilita workflows automáticos.
- **API interna `rincon-bot/api/intents`** que otros workers/PWAs puedan llamar (tasks generadas desde booking, addons disponibles, VIP tier de un phone, etc) — necesario para que M2/M3/M4/M5 puedan integrar con bot.
- **Standardizar formato de email outbound** desde workers (HTML template + Postmark/SES/Mailgun decision) — necesario para M1 email approval, I5 review request, I7 recovery.

---

## §8 · Cómo coordinar entre sesiones WC

Si WC-rdmbot y esta sesión WC (WC-platform) trabajan en paralelo:

| Territorio | Sesión |
|---|---|
| `apps/worker-bot/`, Greeter, Booker, canary, bot infra | WC-rdmbot |
| `threads/`, `cc-instructions-{bot,data,platform}/`, wishlist, strategy macro, módulos cross-bot | WC-platform |
| `apps/staff/`, `apps/menu/`, `apps/admin/`, módulos no-bot | WC-platform (o CC directo cuando spec lista) |

**Coordinación lockless:**
- `git pull --rebase` antes de push (siempre)
- Threads numerados secuencialmente (próximos: 92, 93, ...) — no reservar números, usar el siguiente disponible al momento de commit
- Si una sesión modifica `CLAUDE.md`, `CONTEXT.md`, `ROADMAP.md`, otras sesiones rebase
- Si conflict en spec/thread, **última en push gana** + abrir thread aclaración

---

## §9 · Preguntas que probablemente Alex le va a hacer a WC-rdmbot pronto

Anticipadas:

1. **"¿Cómo migramos Greeter v6 a v7 con lifecycle awareness sin romper el actual?"** — feature flag + canary, fallback comportamiento v6 si lifecycle null
2. **"¿Vale la pena meter M1 Pricing dentro de `rincon-bot` o worker separado?"** — voto WC: dentro (reusa auth, alertas, infra). Worker separado solo si pricing crece a >2 nichos (estancias largas, eventos privados).
3. **"¿Cómo coordinar M5 Tasks notification con ManyChat fallback sin duplicar mensajes?"** — D1 table `task_notifications_sent` con `(task_id, channel, delivered_at)` para dedup. Web Push primero, WhatsApp solo si Push ack timeout 5min.
4. **"¿Mejor in-stay bot como otro endpoint en `rincon-bot` o nuevo worker?"** — voto WC: otro endpoint mismo worker. Mismo stack, mismo KB engine, distinto lane.
5. **"¿Cómo integro Casa Chamán cuando llegue Q3?"** — feature flag `CHAMAN_ENABLED` en `bot_config`, prompt addendum cargado condicional, M1 incluye roomId 679176 cuando flag on. NO modificar prompt base hasta lanzar.

---

## §10 · TL;DR para WC-rdmbot

- **Hay 5 módulos + 19 ideas** en wishlist (thread 89). Esto NO es spec, es brainstorm conceptual.
- **CC está reviewing técnicamente** en thread 90 (en progreso, esperar antes de actuar).
- **WC-rdmbot probablemente toque M1 Pricing, I3 In-stay, I5 Review, I7 Recovery, I8 VIP, M5 fallback** porque viven en `rincon-bot`.
- **Resto de módulos** son `apps/staff`, `apps/menu`, etc — fuera del territorio de WC-rdmbot.
- **Reglas duras > LLM en money**, **encapsular**, **mobile-first**, **reusar histórico**, **NO Casa Chamán** en Greeter hasta Q3.
- **PWA single `apps/staff` multimódulo** decidido para todo lo que ven empleados (Tasks/Inventory/Schedule).
- Si WC-rdmbot quiere proponer mejoras estructurales al Greeter (v7 lifecycle, intents API, quote_requests table), **adelante, abrir thread propio**.
- Si WC-rdmbot ve conflicts entre lo que está construyendo y el wishlist, **flag a Alex en thread**, no decidir solo.

---

**Versión:** v1
**Última actualización:** 2026-05-17
