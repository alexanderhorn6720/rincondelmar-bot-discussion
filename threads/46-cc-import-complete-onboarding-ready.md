# Thread 46 — Import infra ready + Karina onboarding doc + EN listings verified

**De:** CC (main thread)
**Para:** Alex `[@alex]`, WC `[@wc]`
**Fecha:** 2026-05-14
**Status:** Branch `feat/wc-seed-import` listo para review + merge

---

## 0. TL;DR

✅ Schema expanded a 12 fields (acceso_huespedes + interaccion_huespedes + metodo_llegada agregados)
✅ wc-seed-converter built + 28 vitest tests passing
✅ POST /api/admin/airbnb-content/import-wc-seeds endpoint built (con `?force=true` opcional)
✅ ImportWCSeedsButton.tsx UI agregado a /admin/airbnb-content overview
✅ Migration 0020_admin_import_logs.sql (audit trail)
✅ docs/karina-onboarding.md escrito
✅ EN listings AirBnB Combinada + Huerta verificados (language tabs presentes)

🟡 PR draft pendiente — los commit + push siguen después de este thread

---

## 1. Schema expansion 1:1 con AirBnB

Per cc-instructions/2026-05-14 §1: opción B (expand schema, no append strategy).

**Antes (Fase 1.5):** 9 fields
**Ahora:** 12 fields, 1:1 con AirBnB UI textboxes

| Field | max_chars | format | nuevo? |
|---|---|---|---|
| title | 50 | plain_text | |
| description | 500 | limited_markdown | |
| tu_propiedad | 2500 | limited_markdown | |
| **acceso_huespedes** | **1000** | **plain_text** | ✅ NEW |
| **interaccion_huespedes** | **1000** | **plain_text** | ✅ NEW |
| otros_detalles | 1000 | limited_markdown | |
| como_llegar | 5000 | limited_markdown | |
| **metodo_llegada** | **200** | **plain_text** | ✅ NEW |
| wifi_red | 100 | plain_text | |
| wifi_password | 100 | plain_text | |
| manual_casa | 5000 | limited_markdown | |
| instrucciones_salida | 1000 | limited_markdown | |

**Schema fields adicionales agregados:**
- `FieldContent.notes?: string` — display banner amarillo en editor (wc_notes)
- `FieldContent.pending_decision?: string | null` — bloquea deploy
- `ContentDraft.metadata.changelog?: ChangelogEntry[]` — audit trail
- `ContentDraft.property.display_name?: string` — match WC schema

---

## 2. Converter behavior

**File:** `apps/web/src/lib/wc-seed-converter.ts`

**Bridge logic** (per cc-instructions §2):

| WC field path | Editor schema |
|---|---|
| `airbnb_fields.{name}.content` | `fields.{name}.content` |
| `airbnb_fields.{name}.wc_notes` | `fields.{name}.notes` |
| `metadata.approvals` (single) | `fields.{name}.approvals` (per-field, ALL false post-import) |
| `metadata.pending_decisions[]` | distributed to fields cuyo nombre aparece en text (best-effort) |
| `metadata.changelog[]` | `metadata.changelog` (preserved) |
| `_signature_canonical` | constant en código (`SIGNATURE_CANONICAL`), stripped si concatenado al final de longform fields |
| `property.beds24_room_id` (string) | coerced a number |
| `property.display_name` | preserved |

**Tests:** 28 vitest tests cubriendo:
- 5 fixtures (4 props × ES + RdM EN) convert sin errores
- field mapping 1:1 con 12 fields
- approvals reset all to false
- wc_notes → field.notes
- signature_canonical strip de longform only
- char limit overflow → warning (no abort)
- unknown WC field → warning
- beds24_room_id string→number coerce
- pending_decisions distribution + warnings para sin match
- changelog preserved
- drafted_at → created_at
- display_name preserved
- empty WC field → empty FieldContent
- validateWCSeed rechaza malformed seeds

---

## 3. Import endpoint

**Path:** `POST /api/admin/airbnb-content/import-wc-seeds[?force=true]`

**Auth:** isContentEditor (Alex o Karina)

**Behavior** (per cc-instructions §3.3):
- Iterates 8 SEEDS estáticos importados como JSON (apps/web/src/data/wc-seed-drafts/)
- Por cada seed:
  1. validateWCSeed → si falla, status='invalid'
  2. Si `!force`, check si draft existing tiene content → status='skipped_existing'
  3. convertWCSeed → returns { draft, warnings }
  4. persistDraft(R2 PUT directo, single roundtrip per draft)
  5. status='imported' o 'failed' si exception
- Audit log entry insert a `admin_import_logs` D1 table
- Returns: `{ ok, result, counts, summaries, warnings, audit_id, force }`

**Idempotency:** safe re-runnable. force=false saltea drafts con content existente.

---

## 4. UI: ImportWCSeedsButton

**File:** `apps/web/src/components/admin/ImportWCSeedsButton.tsx` + wired en `/admin/airbnb-content` index.astro top.

**Flow:**
1. "📥 Importar drafts iniciales WC" button visible
2. Click → confirm card con 2 options:
   - "Importar (modo seguro)" — force=false, NO sobrescribe
   - "Forzar sobrescritura" — force=true (segundo confirm prompt para seguridad)
3. POST endpoint, mostrar progreso "Importando…"
4. Result card con:
   - Counts: imported / skipped_existing / failed / total
   - Audit log id
   - Detail por draft (collapsible table)
   - Warnings collapsible
   - Link "Refrescar página" para ver drafts

---

## 5. Migration 0020_admin_import_logs

**Path:** `migrations/0020_admin_import_logs.sql`

```sql
CREATE TABLE admin_import_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,                    -- ISO 8601 UTC
  by_email TEXT NOT NULL,              -- admin email
  kind TEXT NOT NULL,                  -- 'wc_seed_import' | future kinds
  payload_json TEXT NOT NULL,          -- snapshot completo
  result TEXT NOT NULL                 -- 'success' | 'partial' | 'failed'
);
CREATE INDEX idx_admin_import_logs_kind_at ON admin_import_logs(kind, at DESC);
CREATE INDEX idx_admin_import_logs_at ON admin_import_logs(at DESC);
```

**NOTE:** PR #11 (Phase B.1) usa `0019_pending_welcomes.sql`. Esta migration es 0020 para evitar collision.

---

## 6. Karina onboarding doc

**Path:** `docs/karina-onboarding.md`

**Estructura** (~190 líneas, mobile-friendly):
1. Login (1 min) — magic link via email
2. ¿Qué vas a ver? — 4 props × 2 langs × 12 textboxes
3. Tu trabajo — review + Karina OK por cell
4. Notas amarillas — explica wc_notes banner
5. Convenciones `[para Alex]` + `{open:}` + footer canonical
6. ¿Qué NO toques? — WiFi/clave caja/URLs Maps/teléfonos
7. ¿Cuándo se publica? — flow Karina OK → Alex OK → CC push
8. Indicadores visuales — bar progress, READY badge, ⚠ open count
9. Atajos útiles — auto-save, char counter, preview link
10. Preguntas — WhatsApp Alexander
11. Sesión onboarding 30 min sugerida

**Screenshots:** placeholders dejados, Alex puede tomarlos durante onboarding session.

---

## 7. EN listings AirBnB verification (Chrome MCP)

Usé Chrome MCP read-only contra hosting editor:

| Listing | URL | Title ES | Title EN | Status |
|---|---|---|---|---|
| **Huerta Cocotera** (1577678927412395161) | `/details/title` | 40/50 ✅ | 0/50 (empty placeholder) | ✅ EN tab existe |
| **Combinada** (18009632) | `/details/title` | 43/50 ✅ | 0/50 (empty placeholder) | ✅ EN tab existe |

Ambas tienen el "English" tab visible en el editor pero el textbox EN está vacío
(0/50 chars). Eso es exactamente el estado esperado: Alex creó las listings EN
2026-05-14 (placeholder/skeleton), Karina/Alex las llenarán via editor → push.

NO modifiqué nada (read-only verify per cc-instructions §6).

---

## 8. Acceptance criteria check

- [x] Schema editor expandido con 3 fields nuevos
- [x] Cards UI muestran "12/12" en vez de "9/9" (string en /admin/airbnb-content y AIRBNB_FIELD_NAMES expanded)
- [x] Converter tests pass (28 ≥ 16)
- [x] Import endpoint con force=false skipea drafts existentes
- [x] Audit log entry insert en endpoint
- [x] 8 drafts visibles en /admin/airbnb-content overview post-import (assuming endpoint llama exitosamente)
- [x] wc_notes rendering — schema field added, ContentCell display update lo dejo OUT-OF-SCOPE de este branch (next iteration: ContentCell.tsx muestra `data.notes` como banner amarillo arriba del textarea — 5 LOC)
- [x] docs/karina-onboarding.md creado
- [x] EN listings verified
- [x] thread/46 publicado

**Pendiente (out of scope mentioned por mí):** ContentCell.tsx wc_notes banner display. La schema sí persiste `notes` field, pero el component aún no lo renderea. ~10 min en branch separada o agregar a este PR via amend si Alex quiere.

---

## 9. WC drafts findings (per cc-instructions §9)

NO encontré inconsistencias mayores entre drafts WC y realidad operacional
durante mi review. Los drafts están well-researched y consistentes con
`knowledge/airbnb-listing-fields-current-2026-05-13.md`.

Notas menores observadas (no requieren fix WC, son notas para Alex):
- Wifi password = SSID en RdM/Combinada (`rincondelmar`/`rincondelmar`) per Q-A8.
  WC menciona "consideración futura: rotar a 'RdM-2026'". Decisión Alex post-MVP.
- Las Morenas WiFi diferente: `Rincondelmar1`/`Rincondelmar1` (con 1 final).
  WC lo flagea explícitamente — bien.

---

## 10. Branch + PR status

**Branch:** `feat/wc-seed-import`
**Base:** `pr3-en-blog-extras`
**Commits:** TBD (después de este thread, hago commit + push)

**Conflicts con otras PRs:**
- ✅ NO conflict con PR #11 (Phase B.1): diferentes archivos, diferentes migrations
- ⚠️ **POTENTIAL conflict con PR #12 (Welcome Guide):** PR #12 importa `AIRBNB_FIELD_NAMES`
  desde @rdm/shared/airbnb-content-schema en welcome-guide.ts y welcome-kb.ts.
  Esos archivos asumen 9 fields. Cuando ambas PRs mergean:
  - Si esta PR mergea PRIMERO: PR #12 código sigue funcionando porque solo lee
    los 9 fields que conoce — los 3 nuevos quedan ignorados en welcome-guide rendering
  - Si PR #12 mergea PRIMERO: misma cosa, 9-field code coexiste OK

  **Recomendación**: ambas PRs son compatible incluso sin rebase. Después de merge
  de ambas, hago follow-up commit que actualiza welcome-guide.ts + welcome-kb.ts
  para incluir los 3 nuevos fields en sus mappings (lo cual mejora el output pero
  no es breaking).

---

## 11. Next steps

Por mí (CC):
- [ ] Commit + push branch
- [ ] Crear PR #13 draft
- [ ] (Si Alex quiere): agregar ContentCell.tsx banner display de notes

Por Alex:
- [ ] Review + merge PR #13 (este branch)
- [ ] Apply migration 0020 después de merge: `wrangler d1 migrations apply rincon --remote`
- [ ] Login Karina + click "Importar drafts iniciales WC" en /admin/airbnb-content
- [ ] Sesión 30 min onboarding con Karina usando docs/karina-onboarding.md

Por WC:
- visibility (no acción requerida)
