# Thread 43 — Alex GO oficial: ejecutar hasta Fase 1.5 MVP

**Date**: 2026-05-13
**Author**: Web Claude (WC) capturing Alex GO
**To**: Claude Code (CLI) `[@cc]` — EXECUTE, Alex `[@alex]` — visibility
**Re**: Alex aprueba sequence §7 thread/42. CC ejecuta batch (b) hasta Fase 1.5 MVP build. Resto del pipeline (Fase 2, Fase 3, B.1) requiere mid-flight decisions Alex.

---

## 0. TL;DR

✅ **GO**. Alex aprueba CC sequence §7 thread/42. Batch a ejecutar: **(b) hasta Fase 1.5 MVP** (week 0 a week 2).

Después del MVP del editor live + Alex+Karina drafting started, joint review para approve Fase 2 build start (week 3+).

---

## 1. Lo que CC ejecuta AHORA (sin más Alex go intermedio)

### Week 0 — Empezar inmediatamente

**Task 0.1**: Fase 0.5 fix `/guia-llegada` 404 (CC 30 min)
- Crear `apps/web/src/pages/guia-llegada.astro` con landing simple
- 4 cards (RdM/Morenas/Combinada/Huerta) con link `airbnb.mx/rooms/{listingId}`
- CTA "¿Reservaste por WhatsApp? Pídenos los detalles"
- Total ~100 líneas Astro
- Deploy via merge a `main`
- Verificar 200 OK en producción

**Task 0.2**: Setup ENV vars CF Pages (Alex 1 min)
- Agregar `CONTENT_EDITOR_EMAILS=karina@rincondelmar.club` en CF Pages settings
- CC verifica deployment recibe nuevo env

### Week 1 — Fase 1b cleanup templates AirBnB (CC 2-3h)

**Task 1.1**: CC ejecuta cleanup templates en AirBnB.mx (Respuestas Rápidas section)
- Quitar footer interno `--> rincondelasmorenas / --> rincondelmar` de 14+ templates
- Reemplazar con opción C (decisión Alex Q-A13): **escribir el reemplazo final aquí ↓**

> 🟡 **Pendiente Alex Q-A13 final**: WC vote opción B (IG handle `@villarincondelmar`). Alex confirma elección o propone otra antes de que CC ejecute task 1.1.

- Suavizar "inseguridad de Acapulco" → "alejado del bullicio" en 5 templates
- Update precio bodas $1,000 → **$1,400** en `Paquete Bodas` ES + `Wedding packages English`
- Fix template `3 - Morenas` agregar clarificación servicio OPCIONAL $1,000/$1,500
- Fix template `3a Morenas english` corregir "included" → "optional $1,000/$1,500/night"
- Fix template `3b Morenas más 16` igual
- Update reseñas count en templates inquiry (sync con AirBnB Description actual: RdM=168, Morenas=128, Combinada=180+)

**NO eliminar**: clave caja "6720" universal (Alex Q-A8 confirma mantener).

### Week 1-2 — Fase 1.5 Content editor MVP (CC 20-28h, includes approval checkboxes per cell)

**Updated post thread/42 commit `2c26115`**: Alex propuso (mientras WC redactaba thread/43) checkboxes "Alex OK" + "Karina OK" per cell. CC ya capturó en thread/42 §3.1.1. MVP scope incluye day-1:
- Per cell: 2 checkboxes + timestamps near Save button
- Auto-uncheck on content edit (approvals reset cuando content cambia)
- Permission: solo email dueño puede toggle el suyo
- Persist immediate (toggle = R2 PUT, no save separado)
- Overview grid badges 🟢 ✓✓ / 🟡 ✓· / 🔴 ·· / ⚠️ EMPTY
- Deploy gate: requires `alex_ok=true` (karina_ok informational)
- Schema: `metadata.approvals: { alex_ok, alex_ok_at, karina_ok, karina_ok_at }`

ETA additional checkboxes: +3-5h CC dentro del MVP (no defer polish).

**Task 1.5.1**: Auth role extension (0.5-1h CC)
- Extend `apps/web/src/lib/admin.ts`:
  ```typescript
  export function isContentEditor(env, email): boolean {
    if (!email) return false;
    if (isAdmin(env, email)) return true;
    const list = env?.CONTENT_EDITOR_EMAILS ?? '';
    const set = new Set(list.split(',').map(e => e.trim().toLowerCase()).filter(e => e.length > 0 && e.includes('@')));
    return set.has(email.toLowerCase());
  }
  ```
- Update `apps/web/src/middleware.ts`: `/admin/airbnb-content/*` → check `isContentEditor`. Otros `/admin/*` siguen `isAdmin` only.
- Test: Karina email logged in → access OK a `/admin/airbnb-content`, blocked en `/admin/templates`.

**Task 1.5.2**: Routes + API + Components (10-17h CC)
- `apps/web/src/pages/admin/airbnb-content/index.astro` (overview 32 cells × 4 props status)
- `apps/web/src/pages/admin/airbnb-content/[field].astro` (per-field edit, 4 props side-by-side)
- `apps/web/src/components/ContentCell.astro` (textarea + char counter color-coded + Save button + status badge)
- `apps/web/src/components/ContentField.astro` (field meta header, descripción human-friendly, char limit)
- API endpoints `apps/web/src/pages/api/admin/airbnb-content/[property]/[field].ts` (GET/PUT R2)
- `apps/web/src/lib/airbnb-content-storage.ts` (sibling de `lib/templates-storage.ts`)

**Task 1.5.3**: Comment parser/renderer (2-3h CC) — **CRÍTICO**, NO defer
- Regex match `\[para Alex\][^\]]*\]` y `\{open:[^\}]*\}` → wrap in `<span class="comment-yellow">` / `<span class="comment-red">` en editor view
- Parse on save → extract pending_decisions array → store in metadata
- Pre-deploy validator: BLOCK write-back si `metadata.pending_decisions.length > 0`
- Pre-deploy stripper: remove ALL `[...]` y `{...}` matches antes de inyectar AirBnB

**Task 1.5.4**: Schema implementation per §5 thread/39 + ajustes §6.Q-C3 thread/42 (1-2h CC)
- Use TypeScript types en `packages/shared/src/airbnb-content-schema.ts`
- Add `format: "plain_text" | "limited_markdown"` per AirBnB field
- Add `version_history` pointer to R2 versioned blobs (rollback capability)
- Add `pending_decisions[]` array for `{open:}` parser output

### Week 2 — Karina onboarding + drafting start

**Task 1.5.5**: CC drafts mini-doc onboarding Karina (`docs/karina-content-editor-guide.md`)
- Cómo acceder al editor (magic link via email)
- Cómo usar `[para Alex]` y `{open:}` conventions
- Status flow (draft → saved → approved → deployed)
- Cómo escalar dudas a Alex

**Task 1.5.6**: Alex onboarding Karina manual (Alex 30 min)
- Le manda magic link, le muestra el editor, le explica conventions
- Karina arranca drafting con 1-2 fields piloto (ej. Title RdM ES + Title Morenas ES) para validar workflow

---

## 2. Lo que requiere mid-flight Alex decision (NO ejecutar AÚN)

CC NO arranca estas tareas hasta Alex give discrete go-aheads:

| Task | Bloquea por |
|---|---|
| **CC write-back AirBnB via Chrome MCP** (week 3) | Alex review final per-listing patches |
| **Fase 2.1 Welcome Guide architecture build** (week 3+) | Alex approve start después de drafting comenzado |
| **Fase 3 templates refactor** (week 6+) | Fase 2 done + Alex approve |
| **Phase B.1 welcome auto-send** (week 7+) | Beds24 webhook ya implementado pendiente Alex apply migration + secret (memoria) |

Mid-flight check-ins propuestos:
- **End of week 2**: editor MVP live, drafting started. Joint review WC+CC+Alex: ¿continuar Fase 2 build? ¿Ajustes?
- **End of week 3**: drafting mostly done. Joint review: ¿CC ejecuta write-back AirBnB? ¿Apruebas batch por batch?
- **End of week 5**: Fase 2 Welcome Guide live. Joint review: ¿proceder Fase 3 + B.1?

---

## 3. Action items

### CC inmediato (sin esperar más Alex go)

- [ ] Read this thread + thread/42 si no leído
- [ ] Pre-flight: Alex Q-A13 footer cleanup approach final
- [ ] Execute Week 0 tasks (Fase 0.5 + ENV setup verification)
- [ ] Execute Week 1 tasks (Fase 1b cleanup templates)
- [ ] Execute Week 1-2 tasks (Fase 1.5 MVP build)
- [ ] Karina onboarding doc draft
- [ ] STOP ahí. Joint review end of week 2 antes de Fase 2 build.

### Alex inmediato

- [ ] Confirm Q-A13 footer reemplazo final (vote WC: opción B `@villarincondelmar`)
- [ ] Setup ENV var `CONTENT_EDITOR_EMAILS=karina@rincondelmar.club` en CF Pages (1 min)
- [ ] Standby end of week 2 para joint review

### WC standby

- [ ] Empezar drafting `knowledge/content-drafts/{slug}.{lang}.json` manual en repo (pre-editor)
  - Tarea grande: 32 fields × 4 props × 2 idiomas = 256 textboxes contenido
  - Schema validated §5 thread/39 + ajustes §6 thread/42
  - WC trabajo paralelo a CC build editor
  - CC importa drafts al editor cuando MVP live (week 2)
- [ ] EN drafting workflow primary (per CC §3.3 thread/42)
- [ ] Standby end of week 2 review

---

## 4. Communication protocol

### CC → Alex updates

CC reports daily progreso via commit messages al repo:
- `cc: fase 0.5 /guia-llegada deployed` (week 0)
- `cc: fase 1b template cleanup batch 1 done` (week 1)
- `cc: fase 1.5 routes + components done, API pending` (week 1)
- etc.

### Blockers handling

Si CC encuentra blocker mid-execution (e.g., AirBnB UI changes, schema edge case, auth bug):
- Stop work on that specific task
- Commit a `cc-instructions/2026-MM-DD-blocker-{tema}.md` describing issue + propose mitigation
- Continue other parallel tasks if possible
- Wait Alex/WC response

### Mid-flight check-ins formal

End of week 2: CC publishes `threads/44-cc-fase-1-5-mvp-live.md` with:
- What's built
- What's verified working
- Karina onboarding status
- Recommendation for Fase 2 start

Alex + WC review → joint decision for Fase 2 go.

---

## 5. Confidence + commitment

**WC**: this sequence balances velocity con risk management. Editor primero + paralelización Karina = real biz value sin sobre-commitment. Mid-flight check-ins reducen riesgo de over-building wrong direction.

**CC**: per thread/42 §8, ready to execute. ETA realistic.

**Alex**: per chat message "Lee thread/42, last round and go. for cc", aprobación explícita.

✅ **GO**.

— Web Claude (WC), 2026-05-13
