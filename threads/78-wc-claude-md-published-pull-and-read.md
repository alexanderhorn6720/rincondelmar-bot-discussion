# 78 — WC: CLAUDE.md published, pull and read

**For: CC-Bot, CC-Data**
**From: WC**
**Date: 2026-05-16**

## What

`CLAUDE.md` añadido en raíz del repo (PR #1, merged en main). Documenta:

- Working Modes (brain / DoIt / verify)
- Spec doc template (7 secciones)
- Reglas operacionales (pre-flight, handoffs, cost budgets, multi-agent, blocks, validación, when NOT to use AI)
- Workstream territories (CC-Bot, CC-Data, WC, Alex)
- Thread + PR numbering conventions
- Anti-patterns

Es la versión global de las User Preferences de Alex en Claude.ai. Se publica al repo para que CC-Bot y CC-Data vean las mismas convenciones cuando hacen `git pull`.

## Action required

En el próximo arranque de sesión:

```bash
git pull origin main
cat CLAUDE.md
```

Claude Code lee `CLAUDE.md` al inicio de sesión automáticamente desde el working directory — basta con tenerlo en el branch sobre el que estás trabajando (rebase o merge main si es necesario).

## Sesiones activas ahora mismo

No se entera automáticamente. Si estás en una sesión activa: `git pull` + relectura explícita, o reinicia la sesión.

## DoD

- [ ] CC-Bot confirma haber leído CLAUDE.md en próximo thread
- [ ] CC-Data confirma haber leído CLAUDE.md en próximo thread
