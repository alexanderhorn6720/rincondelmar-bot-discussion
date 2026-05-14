# CC Instructions — Review thread/40 + wait Alex go

**Date**: 2026-05-13
**From**: Alex (vía WC drafting)
**To**: Claude Code (CLI)
**Priority**: P2 (review opinión técnica, NO ejecutar)
**ETA CC**: ~30 min reading + 30 min drafting respuesta

---

## ⚠️ NO EJECUTAR NADA

Alex responded las 9 preguntas pendientes Q-A. WC capturó las respuestas + propuesta nueva en `threads/40-wc-alex-answers-content-editor-proposal.md`.

CC: leer + opinar técnico + raise concerns adicionales + **WAIT ALEX GO**.

---

## Cambio principal vs thread/37+38 plan

WC originalmente votó: Fase 2 Welcome Guide build PRIMERO, content drafting DESPUÉS.

**WC cambia voto**: insertar **Fase 1.5 Content editor** entre Fase 1b y Fase 2. Razones:
- Karina (empleada Alex) puede paralelizar drafting
- Schema §5 thread/39 validates early
- CC write-back AirBnB ejecuta week 3 (no week 5)
- Welcome Guide en Fase 2 construye con content real, no placeholders

Detalle completo: `threads/40-wc-alex-answers-content-editor-proposal.md` §2-§4.

---

## Tareas CC

### 1. Read thread/40 completo (~30 min)

Especialmente:
- §1 Respuestas Alex (las 9 Q-A)
- §2 Propuesta editor (UI, stack, sequence)
- §3 Concerns WC raised (auth, Beds24, photos)
- §4 Sequence final propuesto

### 2. Opina sobre §2.6 — editor primero (Fase 1.5) vs original

WC dice: hacer editor primero acelera total + paraleliza Alex+Karina.

CC opinión needed:
- ¿15-20h CC estimate para editor es realista? ¿Mayor/menor?
- ¿Reduce Fase 2 Welcome Guide build esfuerzo realmente (-10h)?
- ¿Hay riesgo técnico que WC no ve (e.g., editor + Welcome Guide schema conflict)?
- ¿Alternativa más simple: editor minimal sin admin polish, batch JSON edits via PR a repo + Alex Karina edits markdown files directos?

### 3. Opina sobre §3.1 — auth Karina

WC propone Better Auth magic link. CC puede:
- Confirmar Better Auth instalación actual soporta magic link sin cambios
- Confirmar role-based access (Karina = `content_editor`, NO `admin` full access)
- Evaluar SMS magic link alternative si Karina no tiene email confiable
- Last resort: secret URL pero con expiración 24h + auto-rotation

### 4. Raise concerns técnicos adicionales

§3 thread/40 lista 3 (auth, Beds24 Everything alert, photos defer). Si CC ve más:
- Performance (32 textboxes con auto-save 3s = 32 PUTs to R2 / commits to repo, throttle?)
- Concurrent edits (Alex + Karina editing same field simultáneamente, last-write-wins or locking?)
- Conflict con templates editor existente (Phase B.0.5)
- Cost (R2 PUTs price, git commits, rate limits?)

### 5. Respond Q-W1 to Q-W4 (thread/39) + Q-C1 to Q-C4 (thread/39)

Si no respondidas via thread/38, hacerlo en respuesta a thread/40 (CC opinión consolidada).

### 6. Output

Crear `threads/41-cc-review-thread40.md` con:
- Tu opinión §2.6 (editor primero) — agree/disagree con razones
- Tu opinión §3.1 (auth strategy) — magic link / SMS / secret URL
- Concerns técnicos adicionales
- Updated time estimate Fase 1.5 si difiere
- Q-W1 to Q-W4 + Q-C1 to Q-C4 respuestas
- Sí/No proceder + sequence propuesto final

---

## Constraints

- ❌ NO construir editor
- ❌ NO ejecutar Fase 0.5 fix /guia-llegada (esperar Alex go)
- ❌ NO modificar AirBnB content via Chrome MCP
- ❌ NO tocar Beds24 sync mode (mantener Prices&Availability)
- ✅ SÍ read + opinar
- ✅ SÍ crear thread/41

---

## Timeline

| Step | Owner | ETA |
|---|---|---|
| Read thread/40 + draft thread/41 | CC | 1h |
| Alex responde Q-A12 a Q-A15 + CC opinion | Alex | 1-2 días |
| Joint review thread/40 + thread/41 + responses | Alex + CC | 30 min |
| GO/NO-GO decision sequence | Alex | momento |
| Si go: Fase 0.5 fix /guia-llegada (30 min CC) | CC | day 0 |
| Si go: Fase 1b cleanup templates (2-3h CC) | CC | week 1 |
| Si go: Fase 1.5 editor build (15-20h CC) | CC | week 1-2 |
| Si go: Alex+Karina drafting | Alex+Karina | week 2-3 |

---

## Lo que Alex hace en paralelo

- Responde Q-A12 (auth Karina email/SMS/secret), Q-A13 (footer cleanup), Q-A14 (confirm NO Beds24 Everything), Q-A15 (bot Morenas conditional)
- Decide reciclar listing viejo vs crear nuevo para Casa Chamán Q3
- Lectura de thread/41 cuando CC publique

— Alex (vía WC drafting), 2026-05-13
