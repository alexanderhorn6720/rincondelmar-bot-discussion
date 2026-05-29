---
thread: 238
author: wc
topic: doit-secrets-hub-opcion2
status: spec-ready
mode: DoIt
workstream: CC-Bot
related: 237 (decisión), 234 (incidente), 235 (crons nativos)
created: 2026-05-30
---

# DoIt — Hub de secrets: master único + sync-all + backup age (Opción 2)

MODE: DoIt
TERRITORIO: CC-Bot (scripts/ + raíz monorepo + CLAUDE.md). NO toca código de workers.

---

## §1. Contexto

Decisión Alex (thread/237): **Opción 2 — master local + propagación**. NO Secrets Store
(beta, no cubre Pages, requiere refactor async). Tras crons nativos (thread/235) el drift
worker↔GitHub ya no es crítico; lo que queda es DRY + propagación confiable.

Modelo elegido (Alex 2026-05-30):
- **Un source file** (master plano), **todas las claves**, propagado IDÉNTICO a todos
  los targets ("todos reciben todo"). Sin secciones por target.
- Backup cifrado con **age** (Alex no usa gestor de contraseñas).

---

## §2. Scope explícito

### YES
- Crear el master `secrets/master.env` (un file plano, todas las claves).
- `scripts/sync-all.sh`: lee master, propaga TODO a los 5 targets vía wrangler.
- Backup cifrado age: generar par de claves, cifrar master → `secrets/master.env.age`
  versionable en repo.
- `.gitignore`: master plano + clave privada age IGNORADOS; solo `.age` cifrado commiteable.
- Retirar `sync-secret.sh` (reemplazado por sync-all.sh).
- Documentar flujo en CLAUDE.md.
- Verify final: rotar un secret no crítico end-to-end.

### NO
- NO tocar código de ningún worker (sin refactor async, sigue siendo string env).
- NO Secrets Store (eso es Opción 3 futura).
- NO commitear NUNCA el master plano ni la clave privada age.
- NO `gh secret set` automático (crons nativos ya quitaron GitHub de ops; si algún
  workflow operacional sigue, se documenta como manual, fuera de este DoIt).
- NO incluir secrets reales en el repo, threads, o PR description.

---

## §3. Decisiones cerradas

| # | Decisión | Valor |
|---|---|---|
| D1 | Modelo | Un master plano, todos los targets reciben todas las claves |
| D2 | Backup | age, keypair sin passphrase (recuperación robusta) |
| D3 | Clave privada age | NUNCA en repo. Alex la respalda offline 1 vez |
| D4 | Master plano | gitignored. Solo `.age` cifrado se commitea |
| D5 | Targets | worker-bot, worker-pago, worker-tours, worker-feedback, apps/web (Pages) |
| D6 | Valores de terceros | cada API su token propio (no se "unifican" valores; se unifica fuente+propagación) |
| D7 | sync-secret.sh | retirado, reemplazado |

---

## §4. Implementación

### 4.1 Estructura
```
<repo-root>/
  secrets/
    master.env          # PLANO, gitignored — fuente de verdad local
    master.env.age      # CIFRADO, commiteable — backup
    age-key.txt         # CLAVE PRIVADA, gitignored — Alex respalda offline
    .gitignore          # ignora master.env + age-key.txt
  scripts/
    sync-all.sh         # propaga master → 5 targets
    encrypt-master.sh   # master.env → master.env.age
    decrypt-master.sh   # master.env.age → master.env (recuperación)
```

### 4.2 master.env (formato)
Plano `KEY=value`, una clave por línea. Poblar desde:
- el file del levantamiento existente (inventario),
- `wrangler secret list` por cada worker (completar huecos),
- el `.dev.vars` raíz actual.
Comentario header: "FUENTE DE VERDAD. Editar aquí, luego sync-all.sh. NUNCA commitear."

### 4.3 sync-all.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
MASTER="$(git rev-parse --show-toplevel)/secrets/master.env"
[ -f "$MASTER" ] || { echo "FATAL: master.env no existe"; exit 1; }

DRY_RUN="${1:-}"   # pasar --dry-run para simular

WORKERS=( "apps/worker-bot" "apps/worker-pago" "apps/worker-tours" "apps/worker-feedback" )
PAGES_DIR="apps/web"

# itera claves del master
while IFS='=' read -r key val; do
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  for w in "${WORKERS[@]}"; do
    if [ "$DRY_RUN" = "--dry-run" ]; then
      echo "[dry] $key -> $w"
    else
      echo "$val" | (cd "$w" && npx wrangler secret put "$key")
    fi
  done
  # Pages: wrangler pages secret put
  if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "[dry] $key -> $PAGES_DIR (pages)"
  else
    echo "$val" | (cd "$PAGES_DIR" && npx wrangler pages secret put "$key")
  fi
done < "$MASTER"
echo "sync-all done."
```
Notas implementación:
- Manejar valores con `=` adentro (split solo en primer `=`).
- Manejar valores vacíos / con espacios.
- `wrangler pages secret put` requiere el project name si no está en wrangler.toml de apps/web — verificar y ajustar.
- Idempotente: re-correr sobrescribe, sin efecto colateral.

### 4.4 encrypt/decrypt
```bash
# encrypt-master.sh
age -r "$(grep 'public key:' secrets/age-key.txt | sed 's/.*: //')" \
  -o secrets/master.env.age secrets/master.env

# decrypt-master.sh (recuperación)
age -d -i secrets/age-key.txt -o secrets/master.env secrets/master.env.age
```
Generación inicial de claves (una vez): `age-keygen -o secrets/age-key.txt`
(imprime la public key; el file contiene la private). CC genera el par; Alex
respalda `age-key.txt` offline.

### 4.5 .gitignore (secrets/)
```
master.env
age-key.txt
# master.env.age SÍ se commitea (cifrado)
```

### 4.6 CLAUDE.md
Sección "Secrets management" actualizada:
- master.env = fuente de verdad. Editar → `bash scripts/sync-all.sh`.
- Backup: `bash scripts/encrypt-master.sh` → commit `master.env.age`.
- Recuperación: clonar repo + restaurar `age-key.txt` offline + `decrypt-master.sh`.
- age-key.txt NUNCA en repo. Marcar `sync-secret.sh` como retirado.

---

## §5. Tests / Verify

No hay unit tests (es scripting de infra). Verify manual guiado (Alex ejecuta):
1. `age` instalado (`age --version`; si no, `winget install FiloSottile.age`).
2. CC genera keypair, master poblado desde inventario.
3. `bash scripts/sync-all.sh --dry-run` → lista correcta de KEY→target sin ejecutar.
4. Rotar UN secret no crítico (ej. un TG_*_CHAT_ID de prueba o var inocua) en master.
5. `bash scripts/sync-all.sh` (real) → propaga.
6. Confirmar el valor llegó: `wrangler secret list` en 1-2 workers muestra la key.
7. `encrypt-master.sh` → `master.env.age` generado. `decrypt` en /tmp → round-trip OK.

---

## §6. Definition of Done

- [ ] `secrets/master.env` poblado con TODAS las claves de los 5 targets.
- [ ] `sync-all.sh` funcional, idempotente, con `--dry-run`.
- [ ] keypair age generado; `master.env.age` commiteado; `age-key.txt` + `master.env` gitignored.
- [ ] encrypt/decrypt round-trip verificado.
- [ ] CLAUDE.md actualizado; `sync-secret.sh` retirado.
- [ ] Verify §5 pasado (rotación de prueba end-to-end).
- [ ] PR `feat/secrets-hub-master-sync`, descripción mobile-first, SIN secrets reales.
- [ ] Alex respaldó `age-key.txt` offline (checkbox manual en PR).

---

## §7. Riesgos

| Riesgo | Mitigación |
|---|---|
| master plano o age-key commiteados por error | .gitignore + self-review del diff + run-secret-scanning en PR |
| Pérdida de age-key.txt → backup irrecuperable | Alex lo respalda offline 1 vez (DoD). Mientras tanto master plano local sigue siendo fuente |
| Todos los workers reciben secrets que no usan | Aceptado por Alex (D1). Superficie mayor a cambio de simplicidad. Operación 1 persona |
| `wrangler pages secret put` requiere project name / falla | Verificar en impl; si Pages no acepta, documentar paso manual para apps/web |
| Valor con `=` o espacios mal parseado | Split en primer `=`; quote handling en script; cubrir en dry-run |
| Secret expuesto en chat (ADMIN_REFRESH 2026-05-30) | Ya rotado. Incluir valor nuevo en master |

### Costo
LLM ~$0. age = gratis, local. Sin gasto externo.

---

## §8. Notas

- Opción 3 (Secrets Store para shared + RBAC/audit) queda como evolución futura,
  cuando salga de beta o entre gente con acceso diferenciado. Master local sigue
  siendo fuente para Pages y resto incluso entonces.
- Followup: si algún workflow GH operacional sobrevive a crons nativos, su secret
  se actualiza manual (documentar cuáles, si quedan).
