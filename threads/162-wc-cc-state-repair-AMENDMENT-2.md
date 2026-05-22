# Thread 162 · AMENDMENT 2 — CLAUDE.md también en rdm-bot

**From:** WC (RDM Bot session)
**To:** CC ejecutando thread/162
**Date:** 2026-05-21
**Append a:** thread/162 spec + amendment 1

---

## CONTEXT

Otra sesión CC (cc-strategy, workstream worker-feedback) reportó que cargó
`rdm-bot/CLAUDE.md` versión LEGACY (v1, 46 líneas, "sitio v2 + 3 PRs grandes").
NO cargó la v2 (255 líneas, multi-CC safety, workstream territories).

Razón: **WC instaló CLAUDE.md v2 solo en `rdm-discussion/`** (commit 90d7235
del 2026-05-21). NO la replicó a `rdm-bot/` ni a `rdm-platform/`.

Esto rompe el modelo: CC-Bot lee `rdm-bot/CLAUDE.md` al arrancar sesión en
ese repo, no la de rdm-discussion.

---

## FASE 6 (NUEVA) · Promote CLAUDE.md v2 a rdm-bot

Después de Fase 5 (verificación). Solo aplica si PR #156 ya está MERGED
(tu cleanup de Fase 2-4 ya terminó) o si Alex ya mergeó antes de que llegues
a esta fase.

### 6.1 · Verificar estado actual

```bash
cd <rdm-bot>
git checkout main && git pull origin main

wc -l CLAUDE.md
# Si dice ~46 líneas → v1 legacy, necesita upgrade
# Si dice ~255 líneas → v2 ya promovida, SKIP fase 6

head -3 CLAUDE.md
# v1 dice: "# Claude Code — onboarding"
# v2 dice: "# Claude Code · RDM Bot operating manual"
```

### 6.2 · Si v1 detectada, promover v2

Source: la v2 vive en `rdm-discussion/CLAUDE.md` (ya canonical allá).

```bash
# Branch para el promote
git checkout -b chore/promote-claude-md-v2

# Copiar v2 desde rdm-discussion
cp ../rdm-discussion/CLAUDE.md ./CLAUDE.md
# (ajustar path según ubicación local de los repos)

# Verificar tamaño
wc -l CLAUDE.md  # debe decir ~255

# Header check: la v2 dice "RDM Bot operating manual" pero el path es
# rdm-discussion. NO modificar el header — la v2 fue escrita pensando en
# rdm-bot como repo principal, solo que se instaló en rdm-discussion primero.

# Backup la v1 en commit history (no en file)
git add CLAUDE.md
git commit -m "chore(claude): promote CLAUDE.md v2 to rdm-bot (multi-CC safety)"

# Push + PR
git push -u origin chore/promote-claude-md-v2
gh pr create --base main --head chore/promote-claude-md-v2 \
  --title "chore(claude): promote CLAUDE.md v2 to rdm-bot" \
  --body "Replaces legacy v1 CLAUDE.md (sitio Astro era) with v2 (multi-CC safety, workstream territories, atomic scripts).

Source: rdm-discussion/CLAUDE.md (canonical, installed earlier today).
Reason: CC sessions loading rdm-bot/CLAUDE.md were getting v1, missing v2 rules.

## What changed
- 46L → ~255L
- Adds: Workstream territories (CC-Bot, CC-Data, CC-Pago, CC-Web, CC-Platform)
- Adds: Multi-CC safety (atomic claim scripts, deploy locks)
- Adds: Anti-patterns formalized (13 explicit)
- Adds: Self-review pre-PR checklist
- Adds: Pointers to scripts/*.sh and docs/secrets-inventory.md
- Removes: '3 PRs grandes con pausas' model (replaced by bucket model)

## What to verify
- [ ] CLAUDE.md renders correctly on GitHub
- [ ] New CC sessions in rdm-bot load v2 rules

Closes: thread/162 Fase 6"
```

### 6.3 · NO mergees, espera Alex review

Esto es un cambio que afecta cómo todas las futuras CC sesiones se
comportan en rdm-bot. Merece review humano.

---

## FASE 7 (NUEVA) · Promote a rdm-platform también

Mismo deal pero más simple (es read-only para CC).

### 7.1 · Verificar estado en rdm-platform

```bash
cd <rdm-platform>
git checkout main && git pull origin main

test -f CLAUDE.md && wc -l CLAUDE.md || echo "MISSING"
```

### 7.2 · Si NO existe, reportar a WC

NO copies CLAUDE.md a rdm-platform vía CC. Boundary CC=RO en platform.

Reporta en thread/163: "rdm-platform tiene/no tiene CLAUDE.md. WC commit
directo si necesario."

WC (Alex en su sesión brain) committeará si decide que necesita.

---

## CRITERIO DE ÉXITO ADICIONAL (Fases 6+7)

- [ ] Detectado correcto si rdm-bot tiene v1 o v2
- [ ] Si v1: branch + PR `chore/promote-claude-md-v2` abierto
- [ ] rdm-platform CLAUDE.md status reportado (no tocar)

---

## OUT OF SCOPE — ESTRICTO

- ❌ NO mergees PR de promote — Alex decide
- ❌ NO toques rdm-platform (CC=RO)
- ❌ NO modifiques contenido de CLAUDE.md durante el copy (mismo file exacto)
- ❌ NO crees thread/164, 165, etc.

---

## REPORTAR EN thread/163

Agregar sección "Fases 6-7 · CLAUDE.md promote":

```markdown
## Fases 6-7 · CLAUDE.md promote a otros repos

| Repo | Antes | Acción | Después | PR |
|---|---|---|---|---|
| rdm-bot | v1 (46L) | promote v2 | PR #NNN open | #NNN |
| rdm-platform | ??? | reported only | N/A (WC) | N/A |
```

---

## COST BUDGET (sin cambio)

- LLM esperado: <$1
- Tiempo total con Fases 6+7: 20-30 min
