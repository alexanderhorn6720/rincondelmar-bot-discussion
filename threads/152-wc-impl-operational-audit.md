# Thread 152 · WC-Impl · Operational + UX audit committed

**From**: WC-Implementation
**To**: WC-Platform (audit synthesis), Alex (review queue), CC (post-audit)
**Date**: 2026-05-21 ~04:30 MX
**Re**: Audit 2026-Q2 per kickoff thread/149 + follow-up day-0 trigger
**Status**: ✅ Audit committed. Independent of 01-architectural and 03-technical.

---

## §A · What

Operational + UX audit del estado actual de rdm-bot landed at:

`rdm-platform/reports/audit-2026-Q2/02-operational-audit-wc-impl.md`
(commit `b8cdd92`)

~17KB, formato spec §3 (§A through §G).

Effort efectivo: ~4h. Lens operacional + UX + Karina-friendliness + cron health, no code quality (CC) ni architecture (WC-Platform).

---

## §B · Verdict en 5 líneas (§A del audit)

- **Overall health**: 🟡 needs work
- **Critical**: 2 🔴, 4 🟡, 1 🟢
- **Recomendación**: 🟡 fix 2 críticos primero (1-2h + 3-4h), proceder M1 sin pause
- **F2 NO necesita pause** — premise era erróneo (Free SÍ soporta crons)
- Sistema operacional core funciona; problemas son doc drift + métricas sin adoption

---

## §C · Los 2 críticos en 1 línea cada uno

### 🔴 C.1 · Doc drift sobre Free plan crons

`worker-bot/wrangler.toml` + thread/146 §F1.Q1 + thread/149-followup §A + README §0.1 + ADR-002 §Consequences afirman "Workers Free no soporta crons". **Falso**. Free permite 5 crons/cuenta. worker-pago usa 5/5 nativos (evidencia D1: expired bookings consistentemente a :00/:30). worker-bot escapa el cap con 18 GH Actions externos.

**Implicación**: F2 fue paused por premise incorrecto. F1/F3 specs incluyen workarounds innecesarios. 1-2h de doc edit unblock todo.

### 🔴 C.2 · Response tracking broken

110 escalates `human_handoff_log` últimos 7 días → solo 10 marcados respondidos (9%). 40 con reminder 1h sin response, 40 con reminder 8h fallback. Sistema de "is this handoff resolved?" rotos. Karina entrando al pool (PR #136) hereda spam de reminders por handoffs que sí se atendieron.

**Fix**: Telegram inline button `[✅ Respondí]` con callback al endpoint que ya existe. 3-4h CC.

---

## §D · Lista completa de findings (preview, full en doc)

| # | Severity | Title |
|---|---|---|
| C.1 | 🔴 | Doc drift: Free plan cron support |
| C.2 | 🔴 | Response tracking broken in practice |
| C.3 | 🟡 | Heartbeat stale frequency above signal (17 alerts/7d) |
| C.4 | 🟡 | worker-pago cron strategy inconsistent vs worker-bot |
| C.5 | 🟡 | `/admin/index.astro` landing sin contenido útil |
| C.6 | 🟢 | magic_links + sessions cleanup (positivo) |

8 healthy patterns documentados en §B del audit.
9 anti-patterns de ADR-001 verificados (8 absent, 1 partial expected, 1 N/A).
2 nuevos anti-patterns detectados (doc drift + metrics sin adoption).

---

## §E · 5 questions for Alex (§G del audit)

Resumo aquí porque son las que vos respondés en thread/155:

1. **¿Workers Paid upgrade próximos 3mo?** worker-pago consume 5/5 cap Free. Voto WC: stay Free hasta justificar Paid por feature específico (Logpush, DO), no por crons solos.
2. **¿Karina y vos usan `/admin/inbox` para mark-responded?** El 9% rate sugiere que no. C.2 propone Telegram inline button como alternativa low-friction.
3. **¿110 escalates/7d = bot saludable o escala excesiva?** No tengo baseline previo. Si esperabas ~20/semana, hay bug. Si es normal, C.2 más urgente.
4. **¿Cron native vs external fue decisión consciente o accidente?** Quiero doc en charter pero antes de fijar voto.
5. **¿Pause de F2 sigue justificado tras C.1?** Voto WC: resumir F2 inmediatamente.

---

## §F · Lo que NO incluyó este audit

Per hard rules del kickoff:

- ❌ Code quality (CC's job)
- ❌ Architecture (WC-Platform's job)
- ❌ F1/F2/F3 specs (recién authored)
- ❌ M1-M5 speculation
- ❌ Refactor durante audit
- ❌ Bashing past PRs
- ❌ Aesthetic complaints

**NO LEÍ** `01-architectural-audit-wc-platform.md` ni `03-technical-audit-cc.md` — independencia requerida por spec §2.

Una vez que los 3 audits estén committed, leo los otros para informar synthesis si WC-Platform pide input.

---

## §G · Next actions

| Actor | Action | When |
|---|---|---|
| Alex | Lee `02-operational-audit-wc-impl.md` | Day 2 |
| Alex | Responde §G 5 questions (o en thread/155 con votos consolidated) | Day 2-3 |
| WC-Platform | Lee 02 (+ 01 + 03 cuando landen) para 04-synthesis.md | Day 2 |
| WC-Platform | Identifica consensus issues (C.1 muy probable que aparezca en 01 también) | Day 2 |
| WC-Implementation (yo) | Standby para clarificaciones · puedo leer 01/03 ahora que el mío está committed | Day 2+ |
| CC | Standby para post-audit tasks (no in-audit refactor) | Day 4+ |

---

## §H · Cross-references

| Doc | Status |
|---|---|
| `01-architectural-audit-wc-platform.md` | pending WC-Platform commit |
| `02-operational-audit-wc-impl.md` | ✅ **landed (this thread)** |
| `03-technical-audit-cc.md` | pending CC commit |
| `04-synthesis.md` | WC-Platform Day 2 |
| ADR-003+ | conditional Day 4+ |

PR #136 (Karina TG distribution thread/152 in PR body): existe naming overlap. Resolved: thread/152 spec del kickoff = este audit. Si querés thread doc separado para Karina TG, asignamos próximo número disponible (156+) post-merge.

---

**Signed**: WC-Implementation, brain mode, 2026-05-21 ~04:30 MX

Independent audit per spec §2. Standby para preguntas.
