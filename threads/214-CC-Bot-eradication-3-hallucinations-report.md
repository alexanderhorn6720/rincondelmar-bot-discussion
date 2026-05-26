---
thread: 214
author: CC-Bot
date: 2026-05-26
topic: eradication-3-hallucinations-report
mode: report
status: done
---

# CC-Bot Report — Eradicación 3 Alucinaciones como Reglas Duras

## PRs

- **rdm-bot PR #187** `chore/deescalate-3-hallucinations` → main
- **rdm-discussion**: 2 commits directos a main (cb4b3d8..d30c34d)

## Files editados

### rdm-bot

| File | Qué se quitó |
|---|---|
| `CLAUDE.md` | `❌ Pet fee /noche` + `❌ Casa Chamán en Greeter prompts` de anti-patterns list; sección "## Casa Chamán (recordatorio)" entera |
| `STATE.md §E` | `NUNCA "/noche"` del pet fee; refraseó Casa Chamán de hard rule a nota factual |
| `apps/worker-bot/tests/pre-stay-templates.test.ts` | Labels "thread/118 lock" y "CLAUDE.md anti-pattern" de comentarios (tests propios intactos) |

### rdm-discussion (main directo)

| File | Qué se quitó |
|---|---|
| `CLAUDE.md` | `Casa Chamán NO en Greeter` + `Pet fee NEVER /noche` de anti-patterns |
| `BACKLOG.md` | `❌ Casa Chamán visible en Greeter prompt antes de Q3 renovation` |

### data/CLAUDE.md (rdm-bot workstream CC-Data)

Línea `NO Casa Chamán en outputs guest-facing hasta Q3 2026` eliminada.

## Files NO TOCADOS (historic record)

- `discussion/threads/**` — histórico
- `platform/decisions/ADR-001-platform-shift.md` — ADR histórico; Iris refs son contexto de análisis
- `platform/vision/01-philosophy.md`, `platform/README.md` — out of scope explícito
- `discussion/STATE-drafts/rdm-bot-STATE.md` — draft, filename ≠ STATE.md
- `packages/agents/greeter/system-prompt-v7.ts` — Alex maneja knowledge separadamente

## Iris

No encontrada en CLAUDE.md, STATE.md, ni cc-instructions activos. Solo en ADRs históricos y threads. Sin acción.

## Justificación

- Casa Chamán: Q3 2026 renovation, no bookable, pero OK mencionar si user pregunta directamente.
- Pet fee: $300/estancia es el dato correcto; wording detail, no anti-pattern crítico.
- Iris: no en scope de config files activos.
