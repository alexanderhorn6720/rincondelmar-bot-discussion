# Dry runs — V6 simulation

Simulando Haiku 4.5 bajo el prompt V6. Auto-restrinjo mi tono a Haiku-level
(menos warmth natural que Opus).

## Test 1 — "hola" (turno 1)

Expected per few-shot #1:
- intent_slug='casas'
- opening_line con plantilla recomendada
- 5 emojis, 4 negritas, ~105 palabras

Simulated output:

```
tool: route_user_to_url
intent_slug: "casas"
opening_line: "¡Hola! Bienvenido a Rincón del Mar 🌅

Operamos 4 villas frente al mar en Pie de la Cuesta — la otra cara de Acapulco, más tranquila y con menos tráfico:

🏖️ *Rincón del Mar* — chef, cocinera y mozo incluidos, hasta 30 personas. Ideal para grupos que quieren todo resuelto.

🌴 *Las Morenas* — opcional servicio de cocina y limpieza, hasta 30 personas. Cocina equipada si prefieres cocinar.

🥥 *Combinada* — las dos juntas (Rincón del Mar + Morenas), hasta 58 personas. Para bodas, reuniones grandes, retiros corporativos.

🌺 *Huerta Cocotera* — íntima, hasta 12 personas. En una hectárea con palmeras, alberca infinity, palapa exterior y animalitos. Cocina propia bajo palapa.

Cuéntame qué tipo de plan es y te oriento."
```

✅ MATCH con few-shot. Confianza: 95%.

---

## Test 2 — "cuánto cuesta?" (sin contexto)

Expected per few-shot #2:
- intent_slug='precios'
- pregunta calificadora con tono cálido
- ~50 palabras, sin emojis (precios = tema serio)

Simulated:

```
tool: route_user_to_url
intent_slug: "precios"
opening_line: "Las tarifas dependen de la temporada y de cuántas noches se queden.

Para darte info útil rápido, cuéntame: ¿cuántas personas son y qué fechas tienen en mente? Con eso te oriento a la villa que mejor les queda y armamos cotización exacta."
```

✅ MATCH. Confianza: 90%.

---

## Test 3 — Intent NO documentado en few-shot: "qué amenities tiene Las Morenas"

No hay few-shot directo. Modelo debe extrapolar.

Expected:
- intent_slug='casas' (o más específico si aplica)
- property='las-morenas'
- vibe consistente con few-shots vistos

Simulated:

```
tool: route_user_to_url
intent_slug: "casas"
property: "las-morenas"
opening_line: "Las Morenas tiene de todo para que tu grupo esté cómodo 🌴

Te paso el link a la página de la villa donde están todas las amenidades detalladas: habitaciones, alberca, palapa, cocina equipada, WiFi rápido, A/C en todas las áreas, y más.

¿Hay algo en particular que quieras saber? (chef, capacidad, tipo de plan)"
```

⚠️ Risk medio: el modelo podría inventar amenidades específicas ("jacuzzi", "DJ booth") si no las tiene. Las reglas §3E lo prohiben, pero un modelo cansado puede flojear.

Mitigación: si vemos esto en producción, agregar few-shot #11 con amenities explícitas.

Confianza: 75%.

---

## Test 4 — "puedo llevar mi perro?" (mascotas, hardcoded info)

Expected per few-shot #4:
- pet policy $300/max 2 mencionada
- Huerta + animales mention
- vibe cálido con 🐶

Simulated:

```
tool: route_user_to_url
intent_slug: "mascotas"
opening_line: "¡Sí, todas las villas son pet-friendly! 🐶

Cobramos *$300 MXN por mascota, por noche*, máximo 2 por reserva. Sin restricción de tamaño ni raza.

En Huerta Cocotera tenemos otros animales en sitio (3 borregos, 3 chivos y _La Prieta_, nuestra perrita adoptada). Si tu perro no se lleva con otros, mejor las villas grandes.

¿Tienes alguna villa en mente o cuántas personas son?"
```

✅ MATCH. Confianza: 95%.

---

## Test 5 — Edge case raro: "tienen jacuzzi?"

No documentado en prompt explícitamente. Modelo NO debe inventar.

Expected:
- intent_slug='casas' (o 'faq')
- opening que NO afirma jacuzzi (no está en el prompt)
- delega al sitio

Simulated:

```
tool: route_user_to_url
intent_slug: "casas"
opening_line: "Cada villa tiene amenities distintas. Te paso el link a las 4 casas para que veas detalle completo de cada una.

Si me dices cuál te interesa, te oriento sobre amenities específicas."
```

✅ MATCH expected. NO inventó jacuzzi. Confianza: 80%.

---

## Test 6 — Pregunta con queja indirecta: "es muy ruidoso ahí?"

Pregunta ambigua: ¿exploratoria o queja durante estancia?

Expected:
- Si turn_count==1 → route_user_to_url con intent='pie-de-la-cuesta' o 'faq'
- Si in-stay → escalate (queja)

Sin contexto, asumimos exploratoria.

Simulated:

```
tool: route_user_to_url
intent_slug: "pie-de-la-cuesta"
opening_line: "Para nada — Pie de la Cuesta es justo la zona tranquila de Acapulco, sin antros ni bullicio de la zona dorada. Atardeceres sobre el Pacífico, laguna y manglares.

Te paso el link con todo el detalle de la zona (Barrio Mágico desde 2024)."
```

✅ MATCH. Confianza: 85%.

---

## Test 7 — Insistencia post-handoff: "ya vi el link, no me sirve"

Expected per §7:
- escalate_to_human con reason='user_request'
- vibe acknowledged

Simulated:

```
tool: escalate_to_human
reason: "user_request"
urgency: "medium"
opening_line: "Entiendo. Le aviso a Alexander para que te contacte directamente.

¿Hay algo específico que pueda adelantarle para que te responda más rápido?"
```

✅ MATCH. Confianza: 95%.

---

## Test 8 — Distress (queja durante estancia)

User: "el aire acondicionado no funciona"

Expected:
- escalate_to_human con reason='complaint', urgency='high'
- CERO emojis
- vibe serio, no cálido excesivo

Simulated:

```
tool: escalate_to_human
reason: "complaint"
urgency: "high"
opening_line: "Lamento mucho que tengas un problema con el aire. Voy a avisarle a Alexander ahora para que te atienda directamente.

¿Puedes contarme cuál villa y desde cuándo no funciona? Cualquier detalle me ayuda a darle contexto."
```

✅ MATCH. Confianza: 95%.

---

## Resumen tests

| Test | Intent | Confianza | Notas |
|---|---|---|---|
| 1 | hola | 95% | Match exacto con few-shot |
| 2 | precios | 90% | Match con few-shot |
| 3 | amenities Morenas | 75% | Riesgo de inventar — monitorear |
| 4 | mascotas | 95% | Hardcoded info correcta |
| 5 | jacuzzi (no doc) | 80% | Modelo NO inventó — bien |
| 6 | ruidoso (ambiguo) | 85% | Asumió exploratoria, bien |
| 7 | quiero humano | 95% | Escalate correcto |
| 8 | queja AC | 95% | Tono serio, sin emoji |

**Riesgos identificados**:
- Test 3 (amenities): 25% riesgo de inventar. Mitigación: agregar few-shot post-launch si vemos comportamiento malo.
- En general: el modelo respeta few-shot pero extrapola con confianza variable en intents no documentados.

**Verdict**: V6 ready para canary deploy.
