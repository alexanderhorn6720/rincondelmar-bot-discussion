---
thread: 197
author: wc
topic: airbnb-flows-backlog
status: backlog
mode: capture
created: 2026-05-24
related_threads: [196]
parent_spec: 196
estimated_effort: TBD (brain deep aparte)
---

# Thread 197 — AirBnB Flows Backlog (captura para no perder)

## §0. Propósito

Captura items OUT-OF-SCOPE de thread/196 inbox redesign, para no perderlos. Estos requieren brain deep separado antes de ejecutar. Documentado aquí en lugar de archivos sueltos.

---

## §A. Diseñar flujo bot AirBnB activo

### Estado actual
Bot está en **passive mode** en canal AirBnB. Escucha mensajes, NO responde.

### Por qué passive mode
- Conversación AirBnB es pública (impacta reviews)
- Respuestas erróneas = ranking down
- Sin validación de tono adecuado para canal formal

### Diferencias clave AirBnB vs WhatsApp

| Aspecto | WhatsApp | AirBnB |
|---|---|---|
| Privacidad | Privada | Pública, leídas por AirBnB |
| Impacto review | Indirecto | Directo (response rate, response time) |
| Response time | Sin métrica platform | Ranking factor crítico <1h |
| Traducción | Manual | Automática (Kari ES → guest cualquier idioma) |
| Tono | Cálido, casual OK | Más formal recomendado |
| Multimedia | Audios, stickers OK | Texto principalmente |
| Booking context | Sin contexto inherente | Booking ID inherent |

### Preguntas a responder en brain deep

1. **¿Cuándo activar bot?** Inquiry pre-booking? Post-booking? In-stay?
2. **¿Qué tipos de mensaje?** Confirmación reserva, info logística, FAQs, escalation explicit
3. **¿Cuándo NO activar?** Quejas in-stay, eventos especiales, precios negociables
4. **¿Cómo testear sin impacto producción?** Shadow mode logging vs respuesta real
5. **¿Greeter v5 reusable?** Adaptar prompt o nuevo
6. **¿Métricas success?** Response time avg, conversion inquiry→booking, escalation rate
7. **¿Fallback si bot duda?** Auto-escalate Kari vs respuesta genérica safe

### Pre-requisitos antes de implementar
- Inbox redesign shipped (thread/196) — Kari ve qué pasa
- F2 observability (thread/195 postponed) — métricas bot decisions
- Decision: ¿tono más formal? Karina training data específica AirBnB

### Estimación esfuerzo
- Brain deep: 1h+
- Spec + impl: 12-20h CC
- Testing shadow mode: 1-2 semanas observación
- Activación gradual canary: 0% → 10% → 50% → 100%

---

## §B. Flujo AirBnB inquiries respuesta inmediata <1min

### Por qué crítico
- **Response time <1h** es ranking factor AirBnB
- **<5 min** es benchmark superhost top performers
- **<1 min** automático = competitive advantage real

### Estado actual
Kari responde manualmente. Atrasos = ranking down. Si Kari duerme/ocupada, response time = horas.

### Trigger propuesto
Webhook Beds24 notify cuando nueva inquiry llega → worker-bot endpoint dispatch → respuesta automática enviada a AirBnB.

### Contenido respuesta automática
**Estructura típica:**

1. **Saludo personalizado** (nombre guest si disponible)
2. **Confirm disponibilidad** preliminar (consulta Beds24 calendar)
3. **Pricing range** (base + extras estimados según pax mencionados)
4. **Qualifying questions**:
   - # exacto de personas (adults + kids)
   - ¿llevan mascotas?
   - ¿ocasión? (cumpleaños, evento, vacaciones)
   - ¿servicios? (cocina, traslado)
5. **Próximos pasos** clear (responder mensaje, link a info propiedad)

### Diferencias vs Greeter actual
- Greeter responde a leads WhatsApp (texto libre, sin contexto booking)
- AirBnB inquiry tiene structured data (fechas, propiedad, # guests inicial)
- Tono más formal
- Pricing más explícito (AirBnB calculation visible al guest ya)

### Preguntas a responder en brain quick

1. **¿Modelo?** Haiku 4.5 (rápido, barato) — confirmado por velocidad
2. **¿Disponibilidad calc?** Real-time Beds24 query vs cached
3. **¿Pricing?** Range o exacto (riesgo: bot da precio mal)
4. **¿Qualifying questions todas o seleccionadas por contexto?**
5. **¿Idioma?** Detectar guest msg, responder en su idioma (AirBnB no traduce inquiry inicial?)
6. **¿Webhook Beds24 latency?** ¿Hay forma push o solo polling cada N min?
7. **¿Casos edge?**
   - Fechas no disponibles → respuesta alternativa propiedades
   - Evento grande → escalate Kari
   - Idioma exótico → fallback inglés

### Pre-requisitos antes de implementar
- §A bot AirBnB activo decidido (este es subset)
- Beds24 webhook inquiry tested
- Pricing logic confirmed (ADR-001: NO LLM money decisions — pricing viene de Beds24 reglas, NO LLM-generated)

### Estimación esfuerzo
- Brain quick: 30 min
- Spec + impl: 8-12h CC
- Testing: 1 semana monitoring
- Costo runtime: ~$0.001/inquiry × 50/día = $1.5/mes

---

## §C. Orden de adopción sugerido

```
thread/196 inbox redesign (Wave actual)
  ↓ ship 2026-05-31
F2 observability (postponed thread/195)
  ↓ ship +1 semana
§B AirBnB inquiries auto-response (más simple, alto valor)
  ↓ ship +2 semanas
§A AirBnB bot activo full (más complejo, requiere shadow mode)
  ↓ ship +6-8 semanas
```

---

## §D. Notas adicionales

### Reviews API integration
Reviews sync ya shipped (memorias: reviews-sync.ts cron daily, D1 migration 0012, `/api/reviews`, ReviewsCarousel, bot KB). Esto significa bot tiene acceso a reviews históricos via KB — útil para tone calibration AirBnB.

### Ranking factor data
Pre brain deep §A, recopilar:
- Response rate actual (qué % responde Kari, qué % timeouts)
- Response time avg actual
- Acceptance rate inquiry→booking
- Datos comparables AirBnB top performers (si Alex tiene acceso AirBnB dashboard)

### ManyChat Sunset Stage 2 dependency
Si §A se ejecuta antes de WABA propia (Q3+), bot AirBnB es independiente de ManyChat — no bloquea ni es bloqueado. Buena separación.

---

**Status: BACKLOG (no execution yet)**
**Author: WC**
**Next step: brain deep §A o brain quick §B cuando Alex priorice**
