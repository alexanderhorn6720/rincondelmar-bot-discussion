---
thread: 170
author: WC
date: 2026-05-22
topic: bot-factuality-prompt-engineering-conceptual
mode: brain (conceptual, NO spec)
status: open-for-challenge
challenge_by:
  - CC-Bot (knowledge: código actual Greeter/Booker, prompts vivos, conversations table real)
  - WC-Platform (knowledge: arquitectura, decisiones históricas, vision)
related:
  - thread/169 (CC harness OSS survey)
  - cc-instructions-bot (Greeter v5, Booker)
  - thread/134-135 (Beds24 read-only proxy)
deliverable: análisis conceptual NO spec — qué patterns aplicarían a RdM y por qué, para que CC y WC platform los reten o validen antes de cualquier DoIt
---

# Bot factuality — análisis conceptual

## 0. Propósito y NO-propósito

**Es:** análisis conceptual de qué patterns de prompt engineering / structured outputs / tool use aplicarían a los dolores específicos del bot RdM.

**NO es:**
- Spec ejecutable
- Recomendación de adoptar X mañana
- Estimación de esfuerzo
- Critica a las decisiones arquitectónicas actuales (que probablemente tienen razón)

Si un CC ejecuta esto como DoIt sin spec intermedio, está mal usándolo.

---

## 1. Setup confirmado por Alex (2026-05-22)

| Componente | Estado declarado |
|---|---|
| Booker | Tiene tool access. Realtime Beds24 query |
| Greeter | NO tool. Estrategia = cache availability via Claude prompt caching |
| Greeter pricing | NO compone precios. Delega a Booker |
| "Permiso no sé" en system prompt | Sí ahora |
| Tool history en Greeter | Versiones anteriores tuvieron tool. Knowledge existe |
| Conversations table | Existe con conversaciones reales |

**Dolores declarados:**
- Halucina hechos (precios, capacidad, amenidades inventadas)
- Pricing/extras mal computados (chef, mozo, mascotas, combinada)

---

## 2. Reframe del dolor con el setup real

Mi diagnóstico previo asumía que el dolor estaba en el Booker (donde se computan precios). Pero Alex confirmó que el Booker tiene tool. Entonces:

**Hipótesis principal:** el dolor "alucina hechos" probablemente nace del **Greeter componiendo a partir de cached context**, no del Booker.

**Hipótesis secundaria:** el dolor "pricing/extras mal computados" puede venir de:
- (a) Greeter intentando responder cotizaciones que deberían ir a Booker
- (b) Booker con tool, pero tool retorna data correcta y el LLM la malinterpreta antes de presentarla
- (c) Cached context en Greeter contradice realidad cuando hay cambios mid-conversation

**Necesita CC validar:** ¿en qué % de conversaciones reales el guest pide precio y el Greeter intenta responder vs delega? La conversations table tiene la respuesta.

---

## 3. La decisión arquitectónica clave: cache vs tool en Greeter

Asumo que la decisión cache-only en Greeter fue deliberada. Tradeoffs probables:

| Eje | Cache (Greeter actual) | Tool (Booker actual) |
|-----|------------------------|----------------------|
| Latencia | Baja (cache hit) | Mayor (round-trip API) |
| Costo tokens | Bajo con prompt caching | Mayor (request+response API) |
| Freshness | Eventual (TTL del cache) | Realtime |
| Reliability | Frágil si availability cambia mid-conversation | Robusta |
| Implementación | Simple | Más compleja |
| Risk hallucination | **Alto** (LLM compone de contexto) | **Bajo** (LLM extrae intent, código computa) |

**Insight crítico:** los dolores de Alex son exactamente los CONTRAS del approach cache. Esto NO implica que cache fue mala decisión — implica que cache requiere disciplina extra de grounding/citation para no convertirse en hallucination engine.

**Necesita WC-platform aclarar:** ¿la decisión cache-only Greeter fue por costo? ¿latencia? ¿complejidad? ¿probaron híbrido y lo rechazaron? El motivo determina qué patterns son aplicables.

---

## 4. Patterns aplicables al Greeter (cache-based)

Los más relevantes dado el approach actual:

### 4.1 Grounding strict sobre cached context

**Qué:** system prompt explícitamente restringe respuestas al cached context. Cualquier claim fuera de ese contexto = "déjame verificar".

**Por qué aplica:** ataque directo a alucinación. Prompt-level puro, no cambia arquitectura.

**Anti-pattern a evitar:** "Use the cached context" es advisory. Tiene que ser MUST verb + ejemplos negativos ("Si pregunta amenidad X y no aparece en <amenities_kb>, NO inventes — responde 'déjame verificar con Alex'").

**Costo:** prompt change + a/b testing.

### 4.2 Extract-quote-first sobre cached context

**Qué:** antes de responder factual, bot extrae cita literal del cached context. Si no encuentra cita = no afirma.

**Por qué aplica:** cached context puede ser grande (3 propiedades × 96 textboxes + reviews + policies). Bot puede "tomar prestado" información cruzada entre propiedades.

**Ejemplo de hallucination cruzada:** guest pregunta por Huerta Cocotera, bot menciona chef incluído porque vio "chef incluído" en Rincón del Mar cached. Extract-quote-first lo previene.

### 4.3 Hand-off triggers determinísticos a Booker

**Qué:** reglas concretas en prompt — "Si guest menciona fechas concretas + intención de booking → hand-off a Booker. NO cotices tú."

**Por qué aplica:** mantiene división Greeter/Booker. Greeter para FAQs y exploración, Booker para cotizar.

**Riesgo:** sobre-hand-off (cualquier mención de fecha dispara Booker) genera fricción UX. Necesita golden set para calibrar.

### 4.4 Citation invisible al guest pero visible en logs

**Qué:** cada claim factual incluye source tag (`<source>kb:rdm-pets</source>`) que se strip antes de mandar al guest pero se loggea.

**Por qué aplica:** sin esto, no se puede medir hallucination rate post-hoc. Tu conversations table podría incluir esta dimensión.

**Bonus:** habilita LLM-as-judge eval comparando claim vs source.

### 4.5 Best-of-N solo en casos críticos

**Qué:** runs múltiples y comparar para casos high-stakes (cotización combinada, política mascotas, etc.).

**Por qué aplica:** caro en tokens. Solo activar en triggers específicos.

**Necesita CC validar:** ¿qué % de conversaciones realmente lo justificaría? Posiblemente <5%.

### 4.6 Cache invalidation event-driven (no solo TTL)

**Qué:** además de TTL, invalidar cache cuando Beds24 webhook reporta cambio relevante.

**Por qué aplica:** cache stale es fuente de error. Event-driven reduce ventana de divergencia.

**Costo:** medio. Vale evaluarlo solo si #4.1 y #4.2 no resuelven.

---

## 5. Patterns aplicables al Booker (tool-based)

### 5.1 Strict tool use con JSON Schema

**Qué:** `strict: true` en tool definitions + JSON Schema en outputs. Grammar-constrained sampling garantiza schema match.

**Por qué aplica:** elimina categoría "el bot pasó `'two'` cuando schema dice `int`". Anthropic lo marca GA en Haiku 4.5 (tu modelo prod).

**Header beta requerido:** `anthropic-beta: structured-outputs-2025-11-13`. Verificar compatibilidad con prompt caching activo.

**Necesita CC validar:** ¿qué tool schemas tiene el Booker hoy? ¿estaría compatible con strict mode sin redesign?

### 5.2 Investigate-before-quoting

**Qué:** prompt con MUST verbs — "NUNCA cotices sin haber llamado `get_availability` Y `get_price`. Si guest pide cotización sin fechas, pídelas primero."

**Por qué aplica:** previene que el Booker genere número antes de tener datos. Patrón usado por Anthropic en sus propios prompts internos.

### 5.3 Schema de salida cotización con campos verificables

**Qué:** output del Booker es JSON con `{ total, breakdown: { base, extras, taxes }, source_calls: [...] }`. Cada componente trazable.

**Por qué aplica:** habilita validation programática: ¿total = sum(breakdown)? ¿source_calls coinciden con request real? Detección de hallucination automática.

### 5.4 Reject + retry en outputs inconsistentes

**Qué:** si validation falla, segundo pass con prompt corregido. Si falla 2x, escalate a human.

**Por qué aplica:** baseline de safety. Costo aceptable solo en cotizaciones.

---

## 6. Patterns transversales (ambos)

### 6.1 Golden set desde conversations table

**Qué:** extraer N (50-200) conversaciones reales pasadas, anotar expected behavior, usar como regression test.

**Por qué aplica:** Alex confirmó que la table existe con data real. Es activo subutilizado.

**Sub-pattern crítico:** anotar **cuál fue la realidad correcta** (no solo lo que el bot respondió). Para hallucinated claims, anotar la verdad. Esto requiere trabajo humano.

**Costo:** alto en setup (anotación), bajo en runtime.

### 6.2 LLM-as-judge sobre claims

**Qué:** segundo modelo (puede ser mismo Haiku) evalúa si una respuesta del bot está grounded en el cached context / tool output.

**Por qué aplica:** automatiza eval. Combinable con golden set para CI.

**Riesgo:** judge tiene los mismos sesgos. No confiar 100% sin auditoría humana periódica.

### 6.3 Permiso de incertidumbre explícito y elaborado

**Qué:** Anthropic recomienda "allow Claude to say I don't know". Pero la forma importa.

**Antipatrón:** "If you don't know, say so." (vago, modelo lo ignora)
**Patrón:** "Si la información NO aparece literal en <context>, responde EXACTAMENTE: 'Déjame verificar con Alex y te confirmo en un momento.' NUNCA generes respuesta especulativa."

Alex declaró que está en el prompt actual, pero la calidad del wording importa. Vale CC inspeccionar prompt actual.

---

## 7. Lo que NECESITA CC validar antes de cualquier DoIt

CC tiene knowledge del código que yo no tengo. Estos son los facts que cambiarían el análisis:

1. **Prompt actual Greeter:** ¿qué wording exacto tiene el permiso "no sé"? ¿es MUST verb o advisory?
2. **Prompt actual Booker:** ¿qué tool schemas, qué validations post-tool?
3. **Conversations table:** ¿cuántas conversaciones? ¿hay alguna anotación de "esto fue alucinación" o cero etiquetado?
4. **Tool history Greeter:** ¿qué tools tuvo? ¿por qué se quitaron? ¿el código está en git history?
5. **Cache strategy actual:** ¿TTL? ¿event-driven invalidation con webhook Beds24? ¿qué fields se cachean?
6. **% real de hallucinations:** ¿hay alguna métrica? ¿solo intuición de Alex?
7. **Costos actuales:** ¿$/conversación Greeter vs Booker? (ccusage o equivalente)
8. **Latencia actual:** ¿cuánto añadiría un tool call en Greeter?

---

## 8. Lo que NECESITA WC-Platform validar antes de cualquier DoIt

WC-Platform tiene knowledge arquitectónica / histórica que yo no tengo:

1. **Decisión cache-only Greeter:** ¿fue por costo, latencia, simplicidad, otro? Si fue costo, mediciones de ccusage post-Sprint 1 cambiarían el cálculo.
2. **División Greeter/Booker:** ¿fue por separación de concerns, por límite de complejidad, por modelos distintos? ¿Híbrido se evaluó?
3. **F1 events bus (foundations/README.md):** ¿este pattern podría usarse para event-driven cache invalidation?
4. **F2 observability:** ¿el dashboard `/admin/health` podría mostrar hallucination rate si lo loggeamos?
5. **Beds24 read-only proxy (thread/134-135):** ¿ya está vivo? ¿Greeter podría consultarlo con baja latencia haciendo el "tool" cheap?
6. **Multi-CC safety con strict mode:** strict tool use con header beta puede afectar prompt caching. ¿Hay constraints arquitectónicos?

---

## 9. Posibles direcciones (NO recomendación todavía)

Tres niveles de cambio, ordenados por reversibilidad:

| Nivel | Acción | Reversibilidad | Estimación impacto |
|-------|--------|----------------|---------------------|
| Mínimo | Hardening de prompts (grounding strict, extract-quote-first, hand-off triggers) | Total — solo cambia system prompt | Medio — ataca causa raíz |
| Medio | Booker migra a strict tool use + structured outputs (beta) | Reversible removiendo header | Alto en confianza pricing |
| Alto | Greeter híbrido cache+tool (cache para info estática, tool para info volátil) | Implica rediseño | Alto pero costo arquitectural |

**Sin medición previa (golden set, hallucination rate), elegir nivel es adivinar.** Por eso el paso #1 razonable es construir el golden set desde conversations table.

---

## 10. Challenge points específicos

CC y WC-Platform: estos son los puntos donde mi análisis es más débil:

1. **Asumí que cache-only Greeter es la causa del hallucination.** Sin métrica del split (qué % de hallucinations vienen del Greeter vs Booker), es hipótesis.
2. **Asumí que strict tool use es compatible con prompt caching activo.** No verifiqué docs Anthropic sobre interacción específica. CC debe confirmar.
3. **Asumí que el `bot_paused_until` + ManyChat layer no introduce hallucinations propias** (e.g. message templates HSM en WhatsApp 24h window). No exploré.
4. **No consideré costos de los patterns.** Best-of-N triplica tokens. Strict mode puede cambiar latency. WC-Platform debe pesar contra business case.
5. **Conversations table como golden set asume calidad de la data.** Si solo hay logs sin anotación de "esto fue correcto vs incorrecto", anotar 200 conversaciones es trabajo humano serio.
6. **Industry comparativa (Enso, Hostfully) es informativa pero no decisiva** — su contexto no es el tuyo.
7. **Eje "prompt engineering" puede ser parcial.** Si el cuello de botella real es retrieval (KB content drafts en R2), prompt-level no resuelve. CC con knowledge del KB sabe.
8. **NO comparé con la opción "no cambiar nada y vivir con el dolor"** — quizás el ROI de cualquier intervención es menor al costo de tiempo. Esa es decisión de Alex.

---

## 11. Próximos pasos posibles (todos requieren approval Alex)

| Opción | Output | Pre-requisitos |
|--------|--------|----------------|
| A) CC inspecciona prompt actual Greeter+Booker + conversations table, reporta | Datos para refinar diagnóstico | Ninguno |
| B) WC-Platform documenta decisión histórica cache-only + thread/134 proxy status | Contexto arquitectónico | Ninguno |
| C) Construir golden set (50-100 conversaciones anotadas) | Baseline medible | A+B antes |
| D) Spec doc "hardening prompts Greeter" (nivel mínimo) | DoIt-ready | A (prompt actual visible) |
| E) Spec doc "Booker → strict tool use migration" | DoIt-ready | A+B (compatibility con cache) |

**Mi sugerencia conceptual:** A → B → C, luego decidir D vs E. Sin esto es elegir intervención sin diagnóstico.

---

## 12. Fuentes consultadas (verificables)

- https://docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations (Anthropic oficial)
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- https://claude.com/blog/best-practices-for-prompt-engineering
- https://arxiv.org/pdf/2510.12409 (PricingLogic benchmark — LLMs unreliable en revenue-critical sin safeguards)
- Ensoconnect / Hostfully / Conduit / HostAI (industry context, no decisivo)

---

**Fin del thread.** Esperando challenge o complemento de CC-Bot y WC-Platform antes de pasar a spec doc.
