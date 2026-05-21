# Thread 153 · Numbering protocol + 0039 rename + branch protection (post-Pro)

**From:** WC (RDM Bot session)
**To:** CC
**Date:** 2026-05-21
**Mode:** DoIt (autónomo, scope estricto)
**Depends on:** PRs #137, #5, #138, #6 mergeados. Alex upgraded a GitHub Pro.

---

## CONTEXT

3 follow-ups del thread/146:

1. **5to cambio no ejecutado.** El amendment `146-wc-cc-process-improvements-AMENDMENT.md` se pusheó mientras CC estaba en última fase del DoIt, no se leyó. Numbering protocol scripts + README quedan pendientes.

2. **Colisión migrations 0039.** CC reportó en thread/146 que hay 2 migrations con prefijo 0039:
   - `0039_audit_log.sql`
   - `0039_rules_link_clicks.sql`
   D1 las aplica alfabéticamente. Riesgo: si hay dependencia oculta, bug latente.

3. **Branch protection rdm-bot post-Pro.** Alex upgraded a GitHub Pro. Reintentar `gh api PUT` que fue 403 en thread/146.

---

## PRE-FLIGHT

1. `gh auth status` → logged in
2. `git -C rdm-discussion pull origin main` → up to date (importante: hay amendment file pendiente)
3. `git -C rdm-bot pull origin main` → up to date (post-merge PRs)
4. `gh api /user --jq .plan.name` → debería decir `pro` (NO `free`)
5. `Test-Path "<USER_HOME>\rdm\dev\rdm-discussion\threads\146-wc-cc-process-improvements-AMENDMENT.md"` → True (verificar amendment existe)

Si paso 4 falla (plan sigue free), **halt** + reportar. Alex tal vez aún no completó upgrade.

---

## DELIVERABLES

### CAMBIO 1 · Numbering protocol (rdm-discussion)

**Branch:** `chore/thread-numbering-protocol` (en rdm-discussion)

Lee `threads/146-wc-cc-process-improvements-AMENDMENT.md` y ejecuta su §5to cambio completo:

1. Crear `scripts/next-thread-number.sh` (executable)
2. Crear `scripts/new-thread.sh` (executable)
3. Crear `threads/README.md` con las 4 rules

Smoke test obligatorio:
```bash
bash scripts/new-thread.sh test-author smoke-test
# Verificar archivo creado en threads/{N}-test-author-smoke-test.md
git rm threads/{N}-test-author-smoke-test.md
git commit -m "chore(thread): remove smoke test stub"
git push
```

Commit semánticos:
- `chore(threads): add atomic numbering protocol scripts + README`
- `chore(thread): remove smoke test stub` (del smoke)

---

### CAMBIO 2 · Rename migration 0039 colisión (rdm-bot)

**Branch:** `chore/migration-0039-rename` (en rdm-bot)

**Investigación primero:**
```bash
cd <rdm-bot>
ls migrations/0039_*
git log --diff-filter=A --format="%ai %s" -- migrations/0039_audit_log.sql
git log --diff-filter=A --format="%ai %s" -- migrations/0039_rules_link_clicks.sql
```

La que se creó **primero** (más antigua) conserva número 0039. La más reciente se renumera.

**Verificar estado D1 prod:**
```bash
cd apps/web
npx wrangler d1 migrations list rincon --remote
```

Mira si AMBAS están listed como `applied`, una solo, o ninguna.

**Decisión per estado:**

| Estado prod | Acción |
|---|---|
| Ambas applied | NO renombrar archivos (D1 ya tiene el orden histórico). Solo agregar comment en la más reciente explicando el orden real. |
| Solo una applied | Renombrar la NO aplicada a `0040_<topic>.sql`. |
| Ninguna applied | Renombrar la más reciente a `0040_<topic>.sql`. |

**Si rename requerido:**
```bash
git mv migrations/0039_<topic>.sql migrations/0040_<topic>.sql
git commit -m "chore(migrations): rename 0039 collision to 0040"
```

**Si NO rename (ambas applied):**
```bash
# Editar la más reciente con comment header explicando el orden D1 real
# Ejemplo:
# -- Note: This file is technically 0039 but was applied AFTER 0039_audit_log.sql
# -- due to alphabetical ordering. D1 prod state reflects: audit_log first, then this.
git commit -m "docs(migrations): document 0039 collision applied order"
```

**Out of scope:** NO modificar contenido SQL de las migrations. Solo header comment o filename.

---

### CAMBIO 3 · Branch protection rdm-bot (re-attempt post-Pro)

**NO archivo de código.** Solo `gh api` calls:

```bash
gh api -X PUT /repos/alexanderhorn6720/rdm-bot/branches/main/protection \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="Lint" \
  -f required_status_checks.contexts[]="Types" \
  -f required_status_checks.contexts[]="Tests" \
  -f required_status_checks.contexts[]="Build" \
  -f enforce_admins=false \
  -f required_pull_request_reviews.required_approving_review_count=0 \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

**Nota:** required_status_checks contexts cambiaron vs spec original. Spec decía `Deploy` y `post-deploy-smoke`. Esos workflows triggern post-merge, no en PR. Los correctos para PR-time son los jobs del CI workflow (Lint/Types/Tests/Build).

**Verificar exactos nombres de contexts** ejecutando primero:
```bash
gh api /repos/alexanderhorn6720/rdm-bot/actions/runs?per_page=5 \
  --jq '.workflow_runs[] | {name, conclusion}'
```

Si los job names difieren de Lint/Types/Tests/Build, usar los reales. Si CI workflow tiene 1 solo job en lugar de 4, usar ese job único.

**Output esperado:** HTTP 200 con object describing protection rule.

Si vuelve 403:
- Verificar `gh api /user --jq .plan.name` again
- Si dice `free` → halt + Alex completar upgrade
- Si dice `pro` → halt + reportar exact error (puede ser permiso de PAT)

---

## COMMIT STRATEGY

3 PRs separados (uno por cambio, paralelos):

| # | Repo | Branch | PR title |
|---|---|---|---|
| 1 | rdm-discussion | `chore/thread-numbering-protocol` | `chore: thread numbering atomic protocol` |
| 2 | rdm-bot | `chore/migration-0039-rename` | `chore: migration 0039 collision (rename or document)` |
| 3 | rdm-bot | N/A (no file changes) | N/A — gh api only, reported in thread/154 |

PR bodies usan el nuevo template (dogfood del thread/146).

---

## DEFAULTS

- Encoding: UTF-8 file contents, ASCII shell args
- Idioma: ES en docs, EN en scripts y código
- 0 secretos, 0 PII

---

## OUT OF SCOPE

- NO renombrar threads existentes con colisiones (145/146/149/151/152/154 viven)
- NO modificar contenido SQL de migrations 0039
- NO required_pull_request_reviews >0 en branch protection (rompería velocity)
- NO required_status_checks que bloqueen merge si CI ya falla en main (verificar primero)

---

## EXTERNAL STATE (informational only)

- Verify que CI workflow names matchen lo que pase a `contexts[]`
- Verify que post-Pro upgrade refleje en API call (no caching layer)
- Verify que migration 0039 colisión no afecta migration 0040+ subsequent

---

## CRITERIO DE ÉXITO

- [ ] scripts/next-thread-number.sh + new-thread.sh + threads/README.md en rdm-discussion
- [ ] Smoke test de new-thread.sh ejecutado y stub borrado
- [ ] 0039 colisión resolved (rename o doc según estado prod)
- [ ] Branch protection rdm-bot active (verify con `gh api /repos/.../branches/main/protection`)
- [ ] 2 PRs nuevos abiertos (rdm-discussion + rdm-bot migration)
- [ ] thread/154 posted con report final

---

## SI TE ATORAS

- Plan check returns `free` → halt + Alex action pending
- 0039 status indeterminate (wrangler d1 list falla) → halt + reportar
- Status checks names desconocidos → enumerar workflows existentes, pedir Alex confirm
- Smoke test scripts/new-thread.sh falla → debug, no halt

---

## REPORTAR AL FINAL (thread/154)

- PR # rdm-discussion numbering
- PR # rdm-bot migration (o "no rename needed, doc only")
- gh api output de branch protection success
- Smoke test new-thread.sh resultado
- Tiempo invertido
- LLM cost estimado
- Cualquier sorpresa

---

## COST BUDGET

- LLM esperado: <$3
- Tiempo: 30-45 min CC
- Halt si excede $5 o 1.5h
