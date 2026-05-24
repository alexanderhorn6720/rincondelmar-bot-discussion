# 197 — WC — Backlog: AirBnB bot activation + inquiry auto-response

> **Status:** Backlog captured (no execution scheduled)
> **Purpose:** No olvidar; estos dos flujos importan para conversion + AirBnB ranking pero salen de scope inbox redesign (thread/196)
> **Owner future:** Brain session aparte cuando inbox redesign esté shipped

---

## 1. AirBnB bot flujo (hoy passive mode)

### 1.1 Estado actual

- Bot RdM **escucha** mensajes AirBnB pero **NO responde** (modo passive)
- Razón: AirBnB tiene mecanicas distintas a WhatsApp (review impact público, ranking response time, traducción auto)
- Riesgo de errar es mayor que en WhatsApp privado

### 1.2 Diferencias clave vs WhatsApp

| Dimensión | WhatsApp | AirBnB |
|---|---|---|
| Audiencia | 1-1 privado | Pública (afecta review/ranking) |
| Idiomas | ES default | Cualquier idioma, AirBnB traduce auto |
| Response time impact | Reputación interna | **Factor ranking AirBnB** (<1h ideal) |
| Errores | Recuperable | Visible permanentemente en thread |
| Inquiry vs booking | No aplica | Inquiry → booking flow distinto |
| Mensaje extension | Sin límite | 1000 char limit + foto attachments |

### 1.3 Decisiones pendientes (brain deep futuro)

| # | Pregunta |
|---|---|
| Q1 | ¿Qué intents activamos primero? (FAQ, precio simple, reglas) |
| Q2 | ¿Escalation rules más conservadoras que WhatsApp? |
| Q3 | ¿Templates verificados Alex/Karina antes de cada send? |
| Q4 | ¿Plan canary 0% → 10% → ... como en greeter WhatsApp? |
| Q5 | ¿Cómo manejar idiomas? (Kari responde ES, AirBnB traduce; ¿bot escribe ES y trust traducción?) |
| Q6 | ¿Cómo evitar duplicar Kari? (si Kari ya está respondiendo, bot debe pausarse) |
| Q7 | ¿Metrics review impact pre/post? |

### 1.4 Effort estimate (rough)

- Spec brain deep: 1-2h
- Implementación: 12-20h CC
- Canary scaling: 2 semanas observación

---

## 2. AirBnB inquiry auto-response (<1min)

### 2.1 Pain

AirBnB ranking de listings depende de **response time** a inquiries. Hoy:

- Inquiry llega a Kari (vía Beds24 notify webhook)
- Kari responde manual, a veces toma horas
- Ranking down → menos visibilidad → menos bookings

Verified anoche: hay 8 AirBnB inquiries sin confirmar en queue actual, varias >21h sin respuesta.

### 2.2 Objetivo

Auto-respuesta confirmando disponibilidad + price + qualifying questions, **<1min** después del webhook Beds24.

### 2.3 Componentes técnicos

| Componente | Status hoy |
|---|---|
| Webhook Beds24 notify para inquiry nueva | Por verificar — ¿ya recibimos events tipo `INQUIRY_CREATED`? |
| Worker handler que dispare auto-response | NO existe |
| Template inquiry-response (con `{reviewsUrl}` + `{hostName}`) | **Existe** (PR #7 mergeado 2026-05-13, 4 templates Alex listos: RdM, Las Morenas, Combinada, Huerta) |
| Reply directo a AirBnB | **Funciona** (verificado Alex, Beds24 API) |
| Cron alerta si respuesta >2min late | NO existe |

### 2.4 Flujo propuesto

```
Beds24 webhook INQUIRY_CREATED
  ↓
worker-bot determina property + idioma + pax
  ↓
selecciona template inquiry-response (4 templates Alex)
  ↓
interpola variables (price segun pax, reviewsUrl, hostName, etc)
  ↓
envía via Beds24 API
  ↓
audit log + métrica response_time
```

### 2.5 Decisiones pendientes

| # | Pregunta |
|---|---|
| Q1 | ¿100% auto-response o pre-aprobación Alex/Kari? |
| Q2 | ¿Qualifying questions agresivas (asking ASAP) o gentle? |
| Q3 | ¿Price exacto o rango? |
| Q4 | ¿Si llega fuera de horas, respuesta diferente? |
| Q5 | ¿Cómo manejar inquiries que ya tienen mensaje del guest? (no responder al vacío) |

### 2.6 Effort estimate (rough)

- Spec brain quick: 30 min
- Implementación: 6-10h CC (webhook + handler + métrica)
- Canary: 1 semana observación

---

## 3. Prioridad relativa

Cuando inbox redesign (thread/196) cierre, brain priorización:

| Item | Impacto business | Esfuerzo | Sugerido orden |
|---|---|---|---|
| AirBnB inquiry auto-response | Alto (ranking + conversion) | Bajo (6-10h) | **1° próximo** |
| AirBnB bot activation flujo | Medio (cuando Kari escala) | Alto (12-20h) | 2° después |

Probablemente quick win = inquiry auto-response primero, ya tenemos templates listos.

---

## 4. Captura de contexto histórico

- 2026-05-23 brain deep inbox redesign con Alex: surface backlog
- Templates inquiry-response: PR #7 (mergeado 2026-05-13) agregó `{reviewsUrl}` + `{hostName}` placeholders necesarios para los 4 templates AirBnB
- Casa Chamán (679176): renovation Q3 2026, NO surface a guests ni en templates AirBnB hasta post-renovation
- Pet policy canónica: `$300 MXN/mascota/estancia` (NO `/noche`)
- Stack: Beds24 v2 API connected (read+write tested), Haiku 4.5 para LLM si se usa, R2 `rdm-knowledge` KB

---

## 5. Closing

No execution scheduled. Cuando inbox redesign cierre y haya capacity, abrir thread separado (`thread/XXX-wc-airbnb-bot-spec.md` o `thread/XXX-wc-airbnb-inquiry-response-spec.md`) con brain deep + spec → DoIt.

— WC, 2026-05-23
