# Thread 45 — Editor MVP live + 96/96 textboxes drafted

**Date**: 2026-05-14
**Author**: Web Claude (WC)
**To**: Claude Code `[@cc]` — R2 import + Karina onboarding doc, Alex `[@alex]` — review starts
**Re**: `/admin/airbnb-content` live confirmed. All 8 property drafts complete (4 ES + 4 EN). 0 pending decisions.

---

## 0. TL;DR

✅ `https://rincondelmar.club/admin/airbnb-content` live. Better Auth + WhatsApp OTP. Auth gate verified.

✅ **8 JSON drafts in repo** at `knowledge/content-drafts/`:
- `rincon-del-mar.{es,en}.json`
- `las-morenas.{es,en}.json`
- `combinada.{es,en}.json`
- `huerta-cocotera.{es,en}.json`

✅ **96/96 textboxes** within AirBnB char limits.
✅ **0 pending decisions** — todas las Q-A14 resueltas + URL Morenas + EN listings confirmados.

🟡 CC pending:
1. Importar 8 JSONs al R2 prefix `airbnb-content/{slug}.{lang}.json` (`KNOWLEDGE_BUCKET`)
2. Karina onboarding doc (~30 min walkthrough)
3. Thread reply confirming MVP fully wired

🟡 Alex pending:
1. Onboarding Karina (1 sesión ~30 min usando CC doc)
2. Crear EN listings en AirBnB para Combinada + Huerta (no existen actualmente — solo tienen ES)

---

## 1. Content drafts complete — stats

| Property | ES fields | EN fields | Notas clave |
|---|---|---|---|
| Rincón del Mar | 12/12 ✅ | 12/12 ✅ | Chef Celene INCLUIDO. Cargo víveres 5%/$450 declarado. 35+ third-party contacts en como_llegar |
| Las Morenas | 12/12 ✅ | 12/12 ✅ | Chef OPCIONAL ($1,000/$1,500). WiFi `Rincondelmar1`. URL ubicación: `eFfzFhHaRgGfSUMA7` |
| Combinada | 12/12 ✅ | 12/12 ✅ | Chef INCLUIDO. Manual + Salida nuevos (estaban EMPTY). Dos villas WiFi distintas |
| Huerta Cocotera | 12/12 ✅ | 12/12 ✅ | 2 hab (no 4). Clave caja 6720. Animales narrative preservada |
| **TOTAL** | **48/48** | **48/48** | **96/96 textboxes** |

### Approval status
- `alex_ok` = false en TODOS (esperando Alex tap-by-cell review)
- `karina_ok` = false en TODOS (esperando Karina onboarding)
- `deployed_to_airbnb` = false en TODOS (no se ha pushed a AirBnB todavía)

---

## 2. Decisiones cerradas (Q-A14 final)

| # | Decisión | Status |
|---|---|---|
| Q-A1 | Morenas chef OPCIONAL via AirBnB (incluido directo) | ✅ Aplicado |
| Q-A2 | Bodas $1,400/comensal en como_llegar §6 (no en tu_propiedad) | ✅ Aplicado |
| Q-A4 | Split público/auth | ✅ N/A drafts (auth-gated editor) |
| Q-A5 | Recomendar terceros SIN restricción | ✅ 35+ contactos preservados |
| Q-A7-13 | Footer canonical "— Alexander 🌅 · rincondelmar · club" | ✅ Long-form fields |
| Q-A8 | Photo consent OK | ✅ N/A drafts |
| Q-A10 | Casa Chamán defer hasta apertura | ✅ Excluido drafts |
| Q-A11 | Policy: no editar directo AirBnB | ✅ Vía editor admin |
| Q-A12 | Karina Better Auth magic link | ✅ Verificado live |
| Q-A14 | Beds24 sync mode permanente Prices&Availability | ✅ N/A drafts |
| Q-A15 | Bot Morenas condicional via bookings.channel | ✅ N/A drafts |

**Decisiones específicas content (2026-05-14)**:
- ✅ Cargo víveres = "cargo por transporte y servicio" (no "comisión"). Vigente: 5% / mín $450 MXN
- ✅ Terceros contactos preservados (Alex corrigió: policy aplica a canal propio, no a recomendaciones legítimas)
- ✅ Bodas precio quitado de tu_propiedad, queda en como_llegar §6 con contexto
- ✅ URL ubicación Morenas: https://maps.app.goo.gl/eFfzFhHaRgGfSUMA7
- ✅ EN listings Combinada + Huerta: SÍ crear en AirBnB (actualmente solo tienen ES)

---

## 3. CC action — R2 import (next step)

Editor lee de R2 prefix `airbnb-content/`. Para que Karina vea drafts pre-poblados día 1:

```bash
# Wrangler upload (run from apps/web or wherever wrangler.toml is)
for slug in rincon-del-mar las-morenas combinada huerta-cocotera; do
  for lang in es en; do
    wrangler r2 object put "$BUCKET_NAME/airbnb-content/${slug}.${lang}.json" \
      --file "knowledge/content-drafts/${slug}.${lang}.json" \
      --content-type "application/json"
  done
done
```

Alternativa programática (CC dev tools):
```typescript
const slugs = ['rincon-del-mar', 'las-morenas', 'combinada', 'huerta-cocotera'];
const langs = ['es', 'en'];
for (const slug of slugs) {
  for (const lang of langs) {
    const json = await readFile(`knowledge/content-drafts/${slug}.${lang}.json`);
    const key = `airbnb-content/${slug}.${lang}.json`;
    await env.KNOWLEDGE_BUCKET.put(key, json, {
      httpMetadata: { contentType: 'application/json' }
    });
  }
}
```

**Confirma key naming**: tu plan thread/42 dijo prefix `airbnb-content/` pero verifica si el editor lee `{slug}.{lang}.json` o algo distinto. Si distinto, ajusta el patrón arriba.

---

## 4. CC action — Karina onboarding doc

Doc breve (~1 página) explicando:
1. Login: `karina@rincondelmar.club` magic link
2. Navigation: `/admin/airbnb-content` → property selector → field tabs
3. Workflow per cell:
   - Lee draft WC en textbox
   - Si OK → tap `karina_ok` checkbox
   - Si quiere cambios → edita textbox → save → tap `karina_ok`
   - Comments en `[para Alex]` y `{open: ...}` (convención WC)
4. Footer canonical NO tocar (auto-applied)
5. Status pipeline: `draft` → `karina_ok` → `alex_ok` → `ready_to_deploy` → `deployed_to_airbnb`

Idealmente con 1-2 screenshots del editor. Alex usa el doc en sesión 1:1 con Karina (~30 min).

---

## 5. Alex action — AirBnB EN listings new

Combinada listing `18009632` y Huerta listing `1577678927412395161` actualmente solo tienen ES. Para deployar EN drafts necesitamos crear las EN variants en AirBnB:

1. AirBnB dashboard → listing → idiomas
2. Agregar "English" variant
3. CC luego pushea EN content vía Chrome MCP a esos slots

Alternativa si no quieres EN listings AirBnB: archivamos los EN drafts o los usamos solo para sitio `/en/`.

---

## 6. Resumen — qué falta para "fully live"

```
[✅] Editor `/admin/airbnb-content` deployed
[✅] Auth gate (Better Auth + WhatsApp OTP)
[✅] 8 drafts JSON in repo (96 textboxes, 0 pending)
[🟡] CC: import 8 JSONs al R2
[🟡] CC: Karina onboarding doc
[🟡] Alex: tap-by-cell review starts (alex_ok per cell)
[🟡] Karina: onboarding session con Alex
[🟡] Karina: review starts (karina_ok per cell)
[🟡] Alex: crear EN listings AirBnB Combinada + Huerta
[🟡] Push final: CC vía Chrome MCP a AirBnB (per cell donde alex_ok+karina_ok)
```

Después de todos los `karina_ok` + `alex_ok` por cell, CC dispara push final por property+lang. AirBnB queda actualizado.

---

## 7. Repo state

```
knowledge/content-drafts/
├── rincon-del-mar.es.json    ✅ 12/12 · 0 pending
├── rincon-del-mar.en.json    ✅ 12/12 · 0 pending
├── las-morenas.es.json       ✅ 12/12 · 0 pending
├── las-morenas.en.json       ✅ 12/12 · 0 pending
├── combinada.es.json         ✅ 12/12 · 0 pending
├── combinada.en.json         ✅ 12/12 · 0 pending
├── huerta-cocotera.es.json   ✅ 12/12 · 0 pending
└── huerta-cocotera.en.json   ✅ 12/12 · 0 pending
```

Commits relevantes:
- `b43b6b8` — RdM ES complete (35+ third-party contacts restored)
- `212142a` — Cargo víveres wording final
- `d99e6b3` — 3 ES + 4 EN drafted (7 files, 84 textboxes)
- This commit — Morenas URL + EN listings confirmed

End of thread/45.
