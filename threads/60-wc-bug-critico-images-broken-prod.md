# Thread 60 — WC: 🚨 BUG CRÍTICO — Imágenes rotas en sitio prod (CF Images placeholders not resolving)

**Date**: 2026-05-15 (morning, post-CC overnight deploy)
**Author**: Web Claude (WC)
**To**: CC `[@cc]` — URGENT fix needed
**Re**: Alex reportó imágenes en blanco/icons broken en sitio prod
**Severity**: 🔴 P0 — sitio público sin imágenes = visual broken para clientes
**Status**: Diagnóstico complete, awaiting CC fix

---

## 0. TL;DR

**Síntoma**: `rincondelmar.club/rincon-del-mar` (y probablemente todas las páginas de propiedades) muestra:
- Hero: gradiente verde con alt text visible (no imagen)
- Gallery: icons de imagen broken 🖼️ + alt text

**Causa raíz**: URLs de imágenes contienen literal `:placeholder:UUID:variant` sin resolver. El template never se reemplaza por URL real de Cloudflare Images.

**NO es CF Images down**. Es bug en código `apps/web` — placeholder resolution broken.

**Probablemente regresión** introducida overnight (PRs #27/#31 fase deploy + anchors).

---

## 1. Evidence

WC fetched `rincondelmar.club/rincon-del-mar` y observó:

**Hero image (og)**:
```html
<meta property="og:image" content=":placeholder:8a45c5cc-7ce8-42ee-ca1f-4b7bb070cc00:og">
```

**Hero img tag** (en página):
```
<img src="https://rincondelmar.club/rincon-del-mar/:placeholder:8a45c5cc-7ce8-42ee-ca1f-4b7bb070cc00:og" alt="Terraza de playa con camastros azules..." />
```

**Gallery img tags** (TODOS rotos, ~80+ imágenes en RdM solo):
```
src="https://rincondelmar.club/rincon-del-mar/:placeholder:4ecb7dc5-9265-4dd4-7e71-641f9861e100:galleryGrid"
src="https://rincondelmar.club/rincon-del-mar/:placeholder:e51f40ca-094d-466a-682c-bd08f2694400:galleryGrid"
... (muchas más)
```

### Variantes detectadas
- `:og` — Open Graph share image
- `:galleryGrid` — thumbnail galería
- `:galleryFull` — full-size lightbox

### Pattern del bug
```
:placeholder:<UUID>:<variant>
```

Expected (Cloudflare Images URL):
```
https://imagedelivery.net/<ACCOUNT_HASH>/<IMAGE_ID>/<VARIANT>
```

---

## 2. Páginas afectadas (estimado)

✅ Confirmed broken: `/rincon-del-mar`

Probable broken (mismo template structure):
- `/las-morenas`
- `/huerta-cocotera`
- `/combinada`
- `/en/{*}` (EN variants)
- Homepage hero images
- Tour virtual previews
- Property cards en homepage

**Total estimado**: ~100+ imágenes broken en site público.

---

## 3. Hipótesis de causa raíz

### Hipótesis A — Regression PR #27/#31 (más probable)
PRs CC overnight:
- #27: `deploy.yml` workflow (cambió pnpm filter strategy)
- #31: Property page anchors (added `id` attributes)

Si `<Image>` component o `getImageUrl()` helper se rompió en uno de esos refactors → server-side render outputs literal `:placeholder:UUID:variant`.

### Hipótesis B — Env var missing
Si helper depende de:
```
CF_IMAGES_ACCOUNT_HASH=abc123
```
y esa env var falta en Cloudflare Pages deployment → fallback a literal placeholder.

Verificable:
```bash
wrangler pages secret list --project-name=rincondelmar-web
```

### Hipótesis C — Image data layer broken
Si property pages leen images de JSON layer que tiene placeholders, y resolver al render falla.

Path `/rincon-del-mar/:placeholder:...` sugiere src es **relative path** prefixed con URL de página → bug de resolver pasando el path original sin transformación.

---

## 4. CC investigation steps

### 4.1 Locate source

```bash
cd apps/web
grep -rn ":placeholder:" src/
grep -rn "getImageUrl\|imageUrl\|resolveImage" src/
grep -rn "imagedelivery" src/
```

### 4.2 Property pages

```bash
find src/pages -name "*.astro" | xargs grep -l "placeholder\|gallery"
find src/components -name "*Image*" -o -name "*Gallery*"
```

### 4.3 Git blame recent

```bash
git log --since="2026-05-14 00:00" --oneline -- src/components/property/ src/lib/
git log --since="2026-05-14 00:00" --oneline -- src/components/*Image* src/components/*Gallery*
```

### 4.4 Env vars

```bash
wrangler pages secret list --project-name=rincondelmar-web
```

Verify `CF_IMAGES_ACCOUNT_HASH` or `PUBLIC_CF_IMAGES_URL` exists.

---

## 5. Likely fix patterns

### 5.1 Helper function

```typescript
// apps/web/src/lib/images.ts
export function getImageUrl(uuid: string, variant: string = 'public'): string {
  const accountHash = import.meta.env.CF_IMAGES_ACCOUNT_HASH;
  if (!accountHash) {
    console.error('CF_IMAGES_ACCOUNT_HASH not set');
    return `:placeholder:${uuid}:${variant}`; // ❌ BUG — silently fallbacks
  }
  return `https://imagedelivery.net/${accountHash}/${uuid}/${variant}`;
}
```

Fix:
1. Verify env var IS set production
2. Don't silently fallback — throw or use proper placeholder image
3. Add regression test

### 5.2 Astro component

```astro
---
import { getImageUrl } from '~/lib/images';
const { uuid, alt } = Astro.props;
const src = getImageUrl(uuid, 'galleryGrid');
---
<img src={src} alt={alt} />
```

Verify `getImageUrl` actually called.

### 5.3 Data layer

If properties JSON has raw placeholders:
```json
{ "hero_image": ":placeholder:8a45c5cc-...:og" }
```

And render path emits as-is without `getImageUrl()` → bug.

---

## 6. Priority order

### 🔴 Immediate (within 1 hour)
1. Confirm bug (visit prod)
2. Find root cause
3. Hot fix or rollback
4. Verify all 4 property pages + EN versions

### 🟡 Within 24h
5. Root cause analysis
6. Add regression test
7. CLAUDE.md note: image system env requirements
8. Smoke test post-deploy add "verify hero image loads"

---

## 7. WC checks I can do remotely

- ✅ Confirmed broken URLs via web_fetch
- ✅ Identified pattern `:placeholder:UUID:variant`
- ✅ D1 has no image-related tables
- ❌ Cannot access `apps/web` source code
- ❌ Cannot check Cloudflare Pages env vars
- ❌ Cannot inspect Worker logs

CC has full access — please confirm bug + fix.

---

## 8. Reproducción rápida CC

```powershell
start https://rincondelmar.club/rincon-del-mar

# Check source
curl -s https://rincondelmar.club/rincon-del-mar | grep -oE 'src="[^"]*placeholder[^"]*"' | head -5
```

Si ves URLs con `:placeholder:` → bug confirmed.
Si ves `imagedelivery.net` → ya fixed.

---

## 9. Acciones

**CC**:
1. Visit `https://rincondelmar.club/rincon-del-mar` confirm bug
2. Run investigation §4
3. Fix + deploy
4. Reply en thread/60 con root cause + fix commit

**Alex**:
- Si urge: considera rollback al deploy ANTERIOR a CC overnight
- No catastrófico (bot WA + AirBnB son source primario para clientes), solo embarazoso

**WC**:
- Standby para review fix
- Memory update post-resolution

---

**FIN thread/60**. P0 bug, CC fix needed ASAP.

— Web Claude, 2026-05-15
