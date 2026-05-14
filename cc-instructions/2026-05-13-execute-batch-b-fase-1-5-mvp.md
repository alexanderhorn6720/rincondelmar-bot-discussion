# CC Instructions — EXECUTE batch (b) hasta Fase 1.5 MVP

**Date**: 2026-05-13
**From**: Alex (vía WC capturing GO)
**To**: Claude Code (CLI)
**Priority**: P1 (EXECUTE, no review)
**ETA total**: ~25-32h CC en 2 semanas calendar
**Updated 2026-05-13 post `2c26115`**: MVP scope includes Alex OK/Karina OK checkboxes per cell (+3-5h CC vs original).

---

## ✅ GO

Alex aprueba sequence §7 thread/42. CC EJECUTA batch (b) per thread/43 §1.

---

## Inputs (ya leídos)

- `threads/40-wc-alex-answers-content-editor-proposal.md`
- `threads/41-wc-alex-final-answers.md`
- `threads/42-cc-review-thread40-content-editor.md` (your own review)
- `threads/43-wc-alex-go-execute-batch-b.md` (this batch instruction)

---

## Tasks (execute in order)

### Week 0

1. **Fase 0.5**: fix `/guia-llegada` 404
   - Crear `apps/web/src/pages/guia-llegada.astro` simple landing (~100 líneas)
   - 4 cards properties + CTA WhatsApp
   - Merge to main + verify 200 OK in production
   - Commit message: `cc: fase 0.5 /guia-llegada 404 fix deployed`

### Week 1

2. **Pre-flight blocker**: confirmar con Alex Q-A13 footer reemplazo final
   - WC vote: opción B `@villarincondelmar` IG handle
   - Alex confirm o propone otra antes de continuar task 3

3. **Fase 1b cleanup templates** (CC ejecuta en AirBnB.mx Respuestas Rápidas via Chrome MCP, ~2-3h)
   - Footer cleanup (14+ templates) — usar Alex decision Q-A13
   - "inseguridad de Acapulco" → "alejado del bullicio" (5 templates)
   - Bodas $1,000 → $1,400 (`Paquete Bodas` ES + `Wedding packages English`)
   - Morenas servicio OPCIONAL clarify (`3`, `3a`, `3b` templates)
   - Reseñas count sync (RdM=168, Morenas=128, Combinada=180+)
   - Commit: `cc: fase 1b template cleanup done`

### Week 1-2

4. **Fase 1.5 MVP build** (20-28h CC per §1 thread/43, includes Alex OK/Karina OK checkboxes per cell)
   - 1.5.1 Auth role extension (`isContentEditor` + middleware)
   - 1.5.2 Routes + API + Components
   - 1.5.3 Comment parser/renderer (CRÍTICO MVP-required)
   - 1.5.4 Schema implementation (includes `metadata.approvals` per `2c26115`)
   - 1.5.5 Approval checkboxes per cell + overview badges (per Alex feedback in `2c26115`)
   - Commits incrementales por sub-task

5. **Karina onboarding doc** (CC drafts `docs/karina-content-editor-guide.md`)

6. **Alex onboarding Karina manual** (Alex 30 min, no CC action)

### END OF WEEK 2 — STOP

Publica `threads/44-cc-fase-1-5-mvp-live.md` con:
- Lo construido
- Verificación working
- Karina onboarding status
- Recomendación Fase 2 start

WAIT joint review WC+Alex+CC antes de Fase 2 build.

---

## Constraints

- ❌ NO arrancar Fase 2 Welcome Guide build (esperar week 2 review)
- ❌ NO ejecutar CC write-back AirBnB Chrome MCP (esperar drafting done + Alex approve per-batch)
- ❌ NO Fase 3 templates refactor
- ❌ NO Phase B.1 welcome auto-send
- ❌ NO tocar Beds24 sync mode (mantener Prices&Availability)
- ✅ SÍ ejecutar Week 0-2 tasks listed above
- ✅ SÍ commit incrementally al repo
- ✅ SÍ stop si blocker + commit blocker report to `cc-instructions/`

---

## Blocker protocol

Si encuentras blocker mid-execution:
1. STOP that task
2. Commit `cc-instructions/2026-MM-DD-blocker-{tema}.md` con:
   - What's blocked
   - Why
   - Proposed mitigation options
   - What you'd need to proceed
3. Continue other parallel tasks if possible
4. Wait Alex/WC response

---

## Communication

- Commit messages = primary progress signal
- Daily summary via commits OK, no extra updates needed unless blocker
- Mid-flight check-in end of week 2 via `threads/44-cc-fase-1-5-mvp-live.md`

---

## What Alex does in parallel

- Confirm Q-A13 footer (1 min)
- Setup `CONTENT_EDITOR_EMAILS` env var (1 min)
- Onboard Karina end of week 2 (30 min)
- Standby for joint review week 2

## What WC does in parallel

- Drafting `knowledge/content-drafts/{slug}.{lang}.json` manual (large task, 256 textboxes content)
- EN drafting primary
- CC imports drafts to editor when MVP live week 2
- Standby for joint review week 2

---

## ETA breakdown

| Week | Owner | Hours |
|---|---|---|
| Week 0 CC: Fase 0.5 | CC | 0.5h |
| Week 0 Alex: ENV var setup | Alex | 1 min |
| Week 1 CC: Fase 1b cleanup | CC | 2-3h |
| Week 1 Alex: Q-A13 confirm | Alex | 5 min |
| Week 1-2 CC: Fase 1.5 MVP (incl. checkboxes) | CC | 20-28h |
| Week 2 CC: Karina doc | CC | 1h |
| Week 2 Alex: Karina onboarding | Alex | 30 min |
| **Total CC** | | **23-32h** |
| **Total Alex** | | **40 min** |
| **Calendar** | | **2 weeks** |

---

✅ **GO**. Empieza ahora con Fase 0.5.

— Alex (vía WC drafting), 2026-05-13
