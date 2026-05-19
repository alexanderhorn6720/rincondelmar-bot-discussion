# WC — Cómo deployar correctamente a rdm-bot (post-mortem 2026-05-18/19)

**From:** CC-Bot
**To:** WC
**Date:** 2026-05-19
**Trigger:** Karina training deploy (#115 → #117 → #119 → #120 → #121 → #122 → #124) tomó ~3 horas y rompió prod auth ~30 min por mid-debug. Este doc captura las trampas para que la próxima vez no tropecemos en las mismas piedras.

---

## TL;DR

Cuatro trampas independientes que se cruzaron hoy:

1. **CF Pages tiene dos paths de deploy a prod** (deploy.yml de GH Actions + CF Pages auto-build) — y se pelean por el production alias. Ignorar el segundo = trampa silenciosa.
2. **Root `wrangler.toml` bare es prod-breaking** — no [vars] / D1 / R2 / KV bindings = runtime 500 en cualquier endpoint que use envs.
3. **Astro JSX dentro de `{...}` requiere self-close en void elements** — `<input>`, `<br>`, `<hr>`, `<meta>` deben ser `<input/>`, `<br/>`, etc. Si no, SSR error 500 solo en el branch que renderiza con el rol que veas — mecanismo difícil de aislar sin browser-auth.
4. **Literal `{placeholder}` en .astro = JS reference** — escribir `<code>/{villa}</code>` en una page Astro no muestra texto literal; Astro lo parsea como `{villa}` expresión JS que referencia un variable inexistente → `ReferenceError` en SSR → 500. Mismo síntoma que (3): solo aparece en el branch autenticado. Escapar con HTML entities: `<code>/&#123;villa&#125;</code>`.

**El single best defense para (3) y (4)**: `pnpm astro check` antes de push.

---

## 1 · Arquitectura de deploy actual (importante entender)

Cuando haces push a `main`, **dos cosas** corren en paralelo:

### Path A — GH Actions `deploy.yml`

- Trigger: push a `main`
- Workflow: `.github/workflows/deploy.yml`
- Build: `pnpm install --frozen-lockfile && pnpm --filter web build` (corre desde root, pero `--filter web` cd's al workspace)
- Deploy: `pnpm --filter web exec wrangler pages deploy dist --project-name=rincondelmar-bot --branch=main`
- Config: lee `apps/web/wrangler.toml` con **todos los [vars] + bindings (D1 / R2 / KV)** declarados
- Resultado: deployment con runtime bindings completos → auth funciona, /admin/* funciona

### Path B — CF Pages auto-build (dashboard config)

- Trigger: push a cualquier branch (también `main`)
- Build: corre `pnpm install ...` en el `/opt/buildhome/repo/` (root del repo, NO `apps/web/`)
- Config: lee el **root** wrangler.toml si existe, sino dashboard config
- Resultado: si root wrangler.toml existe y no tiene bindings → deployment SIN bindings → prod 500

### El problema: ambos updatean el production alias

CF Pages siempre asigna el alias `production` al deployment más reciente de la branch `main`. **El que termina último gana**. Path A típicamente termina en ~30s; Path B en ~50-90s. Path B casi siempre gana.

**Si Path B falla** (output dir no encontrado), no actualiza el alias → Path A sigue siendo prod → todo bien. **Si Path B succeed pero con config incompleta**, prod queda servido por Path B con bindings rotos.

### Estado actual

- Path B está **roto a propósito** (post-revert #119): root wrangler.toml no existe → Path B falla "dist not found" → Path A sigue siendo el único path activo a prod.
- Esto significa **previews por branch no funcionan** hasta que se arregle el dashboard.

### Cómo arreglar Path B (preview deploys) en el futuro — sin romper prod

**Opción preferida**: configurar CF Pages dashboard → Pages → rincondelmar-bot → Settings → Builds & deployments → **Build output directory** = `apps/web/dist`. **Root directory** vacío. Sin root wrangler.toml. Path B leerá el dashboard config y encontrará el dist correctamente, y los runtime bindings los heredarás del dashboard Environment Variables (Production scope). NOTA: tienes que **agregar manualmente al dashboard** todos los vars que están en `apps/web/wrangler.toml` `[vars]` — el dashboard NO lee el wrangler.toml para bindings de Pages.

**Opción fallback (si dashboard no es viable)**: root wrangler.toml que **espeje completo** el `apps/web/wrangler.toml` (todos los [vars], [[d1_databases]], [[r2_buckets]], [[kv_namespaces]]) + `pages_build_output_dir = "apps/web/dist"`. Riesgo: drift entre los dos archivos.

**Nunca**: root wrangler.toml minimal (solo `pages_build_output_dir`). Eso es lo que rompió hoy.

---

## 2 · Checklist pre-push para `.astro` pages (especialmente las grandes)

Antes de hacer push a una branch que touca un `.astro` con contenido JSX significativo:

```bash
# Desde rdm-bot root:
cd apps/web

# 1. Type check
pnpm typecheck

# 2. Astro check (encuentra void-element issues, props mismatches, etc)
pnpm astro check

# 3. Build local — esto sí cacha el render-mode issues que typecheck no
pnpm build
```

`astro check` es el que habría cachado el bug de hoy (`<input>` no self-closed). Si tu sandbox no tiene pnpm:

```bash
# Alternativa: grep manual de void elements unclosed en JSX expressions
# Solo dentro de bloques { ... && ( ... ) } o similar
grep -nE '<(input|br|hr|img|meta|link|area|base|col|embed|param|source|track|wbr)([^/>]|$)' archivo.astro
```

Si el grep retorna matches, esos son los sospechosos. Para HTML normal (no JSX expression) son OK; para JSX expression son SSR-breakers.

### Lista de void elements que requieren self-close en JSX expressions

```
<area/> <base/> <br/> <col/> <embed/> <hr/> <img/> <input/>
<link/> <meta/> <param/> <source/> <track/> <wbr/>
```

### Cómo saber si estás en "JSX expression" vs "HTML normal"

- **HTML normal** = todo lo que está fuera de `{ }`, escrito como template literal Astro. Ahí `<br>` es OK.
- **JSX expression** = todo dentro de `{ ... && ( ... ) }`, `{ ... ? ( ... ) : ( ... ) }`, `{ items.map(i => ( ... )) }`, etc. Ahí `<br>` es ERROR.

### Trampa hermana: `{placeholder}` literales

En **cualquier** archivo `.astro` (no solo dentro de JSX expressions), `{name}` se parsea como referencia JS, NO como texto literal. Esto es para que puedas hacer `<p>Hola {user.name}</p>`.

Si querés mostrar texto literal `/{villa}` como template-spec (ej. "la URL es /{villa}" donde `{villa}` debe verse así literal al lector), tenés que escapar:

| ❌ Roto (ReferenceError en SSR) | ✅ Correcto |
|---|---|
| `<code>/{villa}</code>` | `<code>/&#123;villa&#125;</code>` |
| `"Edité {field} de {villa}"` | `"Edité &#123;field&#125; de &#123;villa&#125;"` |
| `Hola {name}` (cuando NO existe const name) | `Hola &#123;name&#125;` |

Alternativa: `{'{villa}'}` (JSX expression que retorna el string literal). HTML entities son más cleanas porque no se confunden con JSX comments.

Grep para auditar antes de push:

```bash
# Busca {algo} que NO esté precedido de un caracter que indicaría JSX expression válida
# (típicamente: $, =, >, espacio dentro de tag, o newline pre-component)
# La forma simple: lista los {x} y revisar manual:
grep -nE '\{[a-z_][a-zA-Z0-9_]*\}' archivo.astro | grep -v "^[[:space:]]*//\|^---\|^import\|^const\|^let"
```

Los `{}` con identifier solo (sin operators / property access / function call) son sospechosos. Si el identifier no está declarado en el frontmatter (entre `---`), es un bug.

`pnpm astro check` lo cacha como `ts(2304) Cannot find name 'X'`.

### Por qué el bug se manifestó solo logged-in

El page tenía dos branches:

```astro
{!allowed && ( <div>403</div> )}
{allowed && (
  <div>
    ...60pp con <input> y <br> sin self-close...
  </div>
)}
```

El primer branch (403) renderiza cuando NO hay sesión válida → ningún unclosed void → 403 limpio. El segundo branch (doc completo) renderiza cuando hay user matching → todos los unclosed voids hit → SSR error → 500. Resultado: el síntoma se ve "auth-relacionado" pero la auth está bien; lo que rompe es el render del branch autenticado.

**Heurística diagnóstico**: si una page admin retorna 500 logged-in pero 302 (redirect a login) logged-out, **NO es auth** — es algo en el renderer que solo el branch autenticado dispara. Empieza por buscar void elements / Astro syntax issues en el branch que renderiza para el rol que falla.

---

## 3 · Cómo deployar (orden de operaciones recomendado)

### Para cambios chicos (CSS, copy, una sola page)

1. Branch local (`git checkout -b feat/...`)
2. `pnpm astro check` desde `apps/web/`
3. Commit + push
4. Open PR
5. **Antes de mergear**:
   - Esperar a que `Deploy` workflow corra en la branch (puede correr en preview si CF Pages auto-build está working, sino solo en main post-merge)
   - **Smoke checks por curl** (logged-out, los públicos):
     - `curl -I https://rincondelmar.club/ruta-que-tocaste` → 200 o 302 según rol
     - Para admin: `curl -I` debe dar 302 (redirect a login)
   - **NO depender de smoke browser via preview** mientras CF Pages auto-build esté roto — preview no tiene secrets de prod.
6. Squash-merge (delete branch).
7. Esperar 2-3 min al deploy.yml deploy.
8. **Smoke prod logged-out** (curl): rutas correctas, 302 en admin, 200 en estáticos.
9. **Smoke prod logged-in** (browser): abre la página afectada como tu rol (admin@), recarga sin cache (Ctrl+Shift+R).
10. Si tocaste algo crítico (auth, env vars, runtime config): probar dos rutas distintas — una admin (auth-gated) y una pública.

### Para cambios grandes (nueva page admin, refactor layout, env vars nuevas)

Todo lo anterior +:

- **Local astro check Y build** antes de push.
- **Test con un user distinto** del que usaste para probar (admin@, social@, karina@) — el bug de hoy pasó porque tested as admin@, no caché el branch de content_editor.
- **NO mergear si CI está rojo por checks específicos del PR** (biome noise / cf-pages preview puede ignorarse — pero **type/test failures de tu PR no**).
- **NO mergear viernes después de 5pm** Acapulco.

### Para cambios en wrangler.toml / env vars

- **Doble-check qué archivo estás tocando**: `apps/web/wrangler.toml` (source-of-truth de prod runtime) vs root wrangler.toml (no debe existir actualmente — y si existe, debe espejar el de apps/web).
- **Nunca shippear root wrangler.toml minimal**.
- Si agregas un env var nuevo:
  - Agregar a `apps/web/wrangler.toml` `[vars]` (si es público/non-secret)
  - Si es secret, usar `wrangler secret put NAME --name worker-name` post-merge
  - Agregar al type en `apps/web/src/env.d.ts`
  - Documentar en el comentario del `[vars]` qué hace
- Post-deploy: probar el endpoint que usa la nueva var.

---

## 4 · Patterns de diagnóstico cuando algo se rompe en prod

### Síntoma: HTTP 500 en una ruta específica

1. **Curl la ruta logged-out**: si da 302/200, el route handler funciona, el bug está en el branch authenticated.
2. **Curl una API endpoint relacionado**: `curl -X POST /api/auth/sign-in/magic-link -d '{"email":"admin@..."}'` — si esto da 200, runtime bindings están OK. Si 500, runtime bindings rotos (auth handler no puede leer DB o env).
3. **Wrangler tail**: `cd apps/web && pnpm exec wrangler pages deployment tail <DEPLOYMENT_ID> --project-name=rincondelmar-bot --status error` mientras alguien reproduce el bug en browser. Esto da el stack trace real.

### Síntoma: prod cambió de comportamiento después de un push a `main`

1. Listar CF Pages deployments: `pnpm --filter web exec wrangler pages deployment list --project-name=rincondelmar-bot | head -20`
2. ¿Hay DOS deployments para el mismo `Source` commit? Si sí, Path A + Path B compitieron. Mira cuál tiene `Active` o el más reciente — ese es el que sirve prod.
3. Si el "Active" es Path B (CF Pages auto-build) y hay root wrangler.toml en el repo → ese es probablemente el culprit. Revertir el root wrangler.toml es el fix.

### Síntoma: 500 solo para un usuario específico

NO es auth role gating. Es SSR error en el branch que renderiza para ese rol. Ver §2.

---

## 5 · Lo que NO hay que hacer (lecciones de hoy)

- ❌ Shippear root wrangler.toml minimal "solo para arreglar CF Pages preview". Lo que hace es romper prod silenciosamente. La versión minimal nunca es safe; o no exista, o espeje completo.
- ❌ Asumir que CF Pages preview build verde = prod funciona. Preview env carece de secrets de prod (Turnstile, Resend, etc.) — auth/email send/etc no se pueden probar en preview de manera realista.
- ❌ Asumir que smoke curl logged-out cubre el caso logged-in. Curl solo prueba el route + redirect. El render-side de la page con un user real solo se prueba en browser autenticado.
- ❌ Cuando un síntoma cambia (e.g. 403 → 500) después de un deploy, asumir que el último deploy lo causó. Aislar primero: ¿se reproduce con el commit anterior?
- ❌ Apilar fixes (hotfix#1, #2, #3, #4...) sin verificar que cada uno fija lo que cree fijar. Hoy hicimos 6+ hotfixes antes de aislar los bugs reales (void elements en #124 + placeholder braces en #125). Cada fix gastó 5-10 min de deploy + verificación. Ejecutar `pnpm astro check` PRIMERA habría tirado los 9 errores de #125 en 30s.
- ❌ Tomar el primer fix exitoso (#124 "void elements") como completo sin re-ejecutar `astro check`. Era parcial. La validation tool ya te dice cuándo terminaste — usala.

---

## 6 · Lo que sí ayuda

- ✅ `astro check` local **antes** de push para changes a `.astro` con JSX significativo.
- ✅ Browser test post-deploy con sesión real del rol relevante. No solo curl.
- ✅ `pnpm wrangler pages deployment list` para ver competing deployments cuando algo se siente raro.
- ✅ Wrangler tail (`pages deployment tail`) cuando hay 500's runtime — el stack trace gana 30 min de debugging.
- ✅ Aislar antes de fixear: bisect rápido entre el último deploy bueno y el roto.
- ✅ Reusar mecanismos idempotentes (welcome_sent_at IS NULL, ON CONFLICT DO UPDATE) — permiten apilar paths (cron + inline trigger) sin doble-send. Hoy esto salvó la situación con #117.

---

## 7 · Cosas pendientes / follow-ups

- [ ] **CF Pages dashboard fix** — Alex tiene permisos. Settings → Builds & deployments → Build output directory = `apps/web/dist`. Y agregar al Environment Variables (Production scope) todos los vars que están en `apps/web/wrangler.toml` `[vars]`. Esto desbloquea preview deploys.
- [ ] **PR #118 (biome cleanup)** — sigue abierto, desbloquea el CI badge verde en futuros PRs. Mergear cuando quieran.
- [ ] **PR #123 (event-driven welcome)** — sigue abierto, listo para review. Convierte el path webhook → 1.5h lag → instant.
- [ ] **`/admin/pre-stay` UI 60-day window** — display only; el scan backend cubre todo el futuro. Considerar split: welcome column = all future, time-relative columns = 60d.

---

**Out.**
