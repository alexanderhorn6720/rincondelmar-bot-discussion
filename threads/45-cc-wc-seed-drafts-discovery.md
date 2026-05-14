# Thread 45 — Descubrimiento: WC drafts iniciales en knowledge/content-drafts/

**De:** CC (main thread)
**Para:** Alex
**Fecha:** 2026-05-13
**Status:** Decisión pendiente (proceder con import flow o esperar)

## Qué encontré

Al hacer `git pull` para pushear thread/44, el rebase trajo 8 archivos nuevos
en el discussion repo:

```
knowledge/content-drafts/
├── combinada.en.json       (12 KB)
├── combinada.es.json       (13 KB)
├── huerta-cocotera.en.json (12 KB)
├── huerta-cocotera.es.json (14 KB)
├── las-morenas.en.json     (13 KB)
├── las-morenas.es.json     (14 KB)
├── rincon-del-mar.en.json  (13 KB)
├── rincon-del-mar.es.json  (17 KB)
```

**Total: 107 KB de drafts pre-escritos por WC**, 4 props × 2 langs.

## Qué contienen

Cada archivo tiene contenido drafted para **9 fields** AirBnB:
- title (con char_count)
- description (con char_count)
- tu_propiedad (long-form, 1500-2500 chars)
- acceso_huespedes
- interaccion_huespedes
- otros_detalles
- como_llegar (very long-form, 4000-5000 chars con kit completo)
- metodo_llegada
- manual_casa
- instrucciones_salida
- wifi_red, wifi_password (likely empty/redacted)

Plus metadata:
- `wc_notes` per field — drafting rationale + `[para Alex]` callouts
- `changelog` con resumen de cambios (Alex Q-A revisions)
- `_signature_canonical` con footer "— Alexander 🌅 · rincondelmar · club"

## Schema WC vs mi Fase 1.5

WC tiene MÁS fields que mi schema:

| WC field | En mi schema (Fase 1.5)? |
|---|---|
| title | ✅ |
| description | ✅ |
| tu_propiedad | ✅ |
| **acceso_huespedes** | ❌ no existe |
| **interaccion_huespedes** | ❌ no existe |
| otros_detalles | ✅ |
| como_llegar | ✅ |
| **metodo_llegada** | ❌ no existe |
| manual_casa | ✅ |
| instrucciones_salida | ✅ |
| wifi_red, wifi_password | ✅ |

WC también usa schema diferente:
- `airbnb_fields` (vs mi `fields`)
- Single approval per draft (vs mis per-field approvals — Alex pidió per-field en thread/42)
- `_signature_canonical` separado (vs sin concepto de signature en mi schema)

## Cómo bridge gap (mi propuesta)

Build **wc-seed-converter** que:

1. **Maps directos** — fields que existen en ambos:
   - title, description, tu_propiedad, otros_detalles, como_llegar,
     manual_casa, instrucciones_salida, wifi_red, wifi_password

2. **Append strategy** — WC fields extra se concatenan a fields existentes
   con section headers visibles:

   - `acceso_huespedes` → APPEND to `tu_propiedad` con `## Acceso de huéspedes`
   - `interaccion_huespedes` → APPEND to `tu_propiedad` con `## Interacción con huéspedes`
   - `metodo_llegada` → APPEND to `como_llegar` con `## Método de llegada`

   Char limits checked OK (tu_propiedad 1662+198+195=~2055 < 2500;
   como_llegar 4735+29=~4764 < 5000).

3. **Preserve wc_notes** — inline cada wc_notes como comment `[para Alex] {note}`
   al inicio del field. Karina/Alex los ven amarillos en el editor.

4. **Initialize per-field approvals** to false (Karina/Alex marcan después).

5. **Append signature** to longform fields (tu_propiedad, como_llegar,
   manual_casa, instrucciones_salida, otros_detalles) — el footer canonical
   "— Alexander 🌅" al final.

## Implementación propuesta (si me das go)

**Branch:** `feat/wc-seed-import` (separada de PR #12 que ya está full)

**Files:**
1. `apps/web/src/data/wc-seed-drafts/{slug}.{lang}.json` — copiar 8 files
2. `apps/web/src/lib/wc-seed-converter.ts` — converter pure function
3. `apps/web/src/pages/api/admin/airbnb-content/import-wc-seeds.ts` — POST endpoint
4. `apps/web/tests/wc-seed-converter.test.ts` — tests del converter
5. UI: agregar botón "Importar drafts iniciales WC" en /admin/airbnb-content overview
6. Safety: NO sobrescribe drafts existentes por default, force=true para bulk overwrite

**Tiempo estimado:** ~1-2h

**Resultado para Karina:**
1. Click en "Importar drafts iniciales WC" en /admin overview
2. Confirma "esto cargará 8 drafts (4 props × 2 langs) a R2"
3. Page recarga, cards muestran "9/9 ░░░░░░░░░░ Alex 0%" para los 8 importados
4. Karina abre cualquier cell → ve content WC + wc_notes amarillos como guía
5. Edita, marca Karina OK
6. Alex revisa, marca Alex OK
7. CC publica a AirBnB via Chrome MCP

## Alternativa: NO importar (si los drafts están outdated)

Si los drafts WC son outdated o no quieres usarlos:
- Karina drafts desde cero usando `knowledge/airbnb-listing-fields-current-2026-05-13.md`
  como referencia
- Más trabajo pero garantiza voz fresca

## Preguntas para ti

1. ¿Ya viste los WC drafts? ¿Los apruebas como starting point?
2. ¿Quieres que proceda con el import flow?
3. ¿OK con la "append strategy" para acceso_huespedes / interaccion_huespedes
   / metodo_llegada? O prefieres que expanda mi schema con esos 3 fields nuevos?

**Mi recomendación:** import con append strategy (más rápido + preserva todo el
trabajo WC). Schema expansion lo dejamos para Fase 2.7 si después se vuelve
fricción.

Esperando tu OK para arrancar branch.
