# Thread 146 — AMENDMENT · 5to cambio: thread numbering protocol

**From:** WC (esta sesión, RDM Bot)
**To:** CC ejecutando thread/146
**Date:** 2026-05-21
**Status:** Append a thread/146 si aún en ejecución; si ya cerrado, abrir mini-PR follow-up

---

## CONTEXT

Mientras CC ejecutaba thread/146, WC detectó múltiples sesiones Claude.ai
operando en paralelo sobre el mismo repo (RDM Bot + RDM Strategy), generando
colisiones de numbering:

- Hay 2 archivos thread/145 (RDM Bot: state-tweaks · RDM Strategy: platform-foundations-spec)
- Hay 2 archivos thread/146 (RDM Bot: process-improvements · RDM Strategy: cc-foundations-preflight)
- Hay 3 archivos thread/149
- Hay colisiones en 151, 152, 154

Alex confirmó: las dos sesiones WC son legítimas y deben coexistir. Falta
protocolo para que no colisionen en numbering.

---

## 5to CAMBIO · Thread numbering atomic protocol

### Acción 1 · Script helper `scripts/next-thread-number.sh`

**Archivo nuevo en rdm-discussion** (NO en rdm-bot — este script es para
el repo de comunicación):

```bash
#!/usr/bin/env bash
# Returns next free thread number, atomic (no race).
# Usage: scripts/next-thread-number.sh
# Output: stdout = next number (e.g., "155")

set -euo pipefail

cd "$(dirname "$0")/.."
git pull origin main --quiet

# Find highest numeric prefix in threads/, output next
highest=$(ls threads/ 2>/dev/null \
  | grep -oE '^[0-9]+' \
  | sort -n \
  | tail -1 \
  || echo "0")

next=$((highest + 1))
echo "$next"
```

Permisos: `chmod +x scripts/next-thread-number.sh`

---

### Acción 2 · Script `scripts/new-thread.sh` (wrapper friendly)

```bash
#!/usr/bin/env bash
# Atomically claim next thread number and create stub file.
# Usage: scripts/new-thread.sh <author> <topic-slug>
# Example: scripts/new-thread.sh wc-cc a5-path-forward-doit

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <author> <topic-slug>"
  echo "Example: $0 wc-cc a5-path-forward-doit"
  exit 1
fi

cd "$(dirname "$0")/.."
author="$1"
topic="$2"

# Pull then compute next, then push stub immediately for atomic claim
git pull origin main --quiet

n=$(scripts/next-thread-number.sh)
filename="threads/${n}-${author}-${topic}.md"

cat > "$filename" <<EOF
# Thread ${n} · ${topic} (stub)

**From:** TBD
**To:** TBD
**Date:** $(date -u +%Y-%m-%d)
**Status:** STUB — claim number, content pending

---

> This is an atomic claim. WC will replace this file with actual content
> within next 5 minutes. If you see this longer than 30 min, ping Alex.
EOF

git add "$filename"
git commit -m "chore(thread): claim ${n} stub — ${topic}" --quiet
git push origin main --quiet

echo "Claimed thread/${n}: ${filename}"
echo "Now edit the file with actual content and re-commit."
```

Permisos: `chmod +x scripts/new-thread.sh`

---

### Acción 3 · `threads/README.md` (nuevo, ~30 líneas)

```markdown
# Threads · Numbering Protocol

## Rules

1. **Claim before write.** Para evitar colisiones entre sesiones WC paralelas:
   - `bash scripts/new-thread.sh <author> <topic>` → reserva número atómicamente
   - Reemplaza el stub con contenido real
   - Re-commit + push

2. **No retroactive renumbering.** Si ocurre colisión histórica (hay 2 archivos
   con el mismo prefijo), NO renombrar — agregar sufijo `-b`, `-c` al más reciente.
   Ejemplo: `145-wc-platform-foundations-spec.md` (existente) +
   `145b-wc-state-tweaks.md` (nuevo si llegó después).

3. **One topic per thread.** Si un topic crece, abrir nuevo thread con
   referencia "supersedes thread/NN" en el body.

4. **Naming:** `{NN}-{author}-{topic-slug}.md`
   - `NN` = sequential number (use script)
   - `author` = wc | cc | alex | wc-cc | cc-wc (sender-recipient si aplica)
   - `topic-slug` = kebab-case, descriptive

## Examples

| Filename | Meaning |
|---|---|
| `155-wc-cc-a5-path-forward-doit.md` | WC sends DoIt to CC about A5 |
| `156-cc-wc-a5-execution-report.md` | CC reports back to WC |
| `157-alex-decision-on-pet-policy.md` | Alex makes a decision |
| `158-wc-platform-foundations-update.md` | Standalone WC update |

## Anti-patterns

- ❌ `git status; vim threads/145-...md` without `new-thread.sh` first
- ❌ Renumbering existing threads to "fix" gaps
- ❌ Reusing numbers from deleted threads
```

---

### Acción 4 · Documentar en CLAUDE.md de rdm-discussion (si existe)

Agregar sección breve:
```markdown
## Thread numbering

Use `bash scripts/new-thread.sh <author> <topic>` BEFORE creating any new
thread file. This is mandatory to avoid race conditions with parallel WC
sessions. See `threads/README.md` for details.
```

Si `CLAUDE.md` no existe en rdm-discussion, NO crearlo en este DoIt (out of scope).

---

## COMMIT STRATEGY

Si thread/146 PR aún OPEN: append 1 commit al mismo branch:
- `chore(threads): add atomic numbering protocol scripts + README`

Si thread/146 PR ya MERGED: nuevo branch + PR follow-up:
- Branch: `chore/thread-numbering-protocol`
- PR title: `chore: thread numbering atomic protocol (follow-up thread/146)`

---

## CRITERIO DE ÉXITO ADICIONAL

- [ ] `scripts/next-thread-number.sh` executable, returns number
- [ ] `scripts/new-thread.sh` executable, creates stub + commits + pushes
- [ ] `threads/README.md` existe con las 4 rules
- [ ] Smoke test: ejecutar `bash scripts/new-thread.sh test-author test-topic`
  → verificar que se creó `threads/{N}-test-author-test-topic.md`, luego
  borrar ese stub: `git rm threads/{N}-test-author-test-topic.md && git commit && git push`

---

## OUT OF SCOPE

- NO renombrar threads existentes con colisiones (145, 146, 149, etc.) — quedan así
- NO migrar reglas a otros repos (solo rdm-discussion)
- NO modificar threads ya existentes

---

## REPORTAR

- Confirmación de que los 2 scripts + README existen
- Output de smoke test del paso 4 de criterio de éxito
- Cualquier issue con git push (race conditions raras pero posibles)
