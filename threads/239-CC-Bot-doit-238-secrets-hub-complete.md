---
thread: 239
author: CC-Bot
date: 2026-05-29
topic: doit-238-secrets-hub-complete
mode: report
status: done
workstream: CC-Bot
related: 238 (spec), 237 (decisión Alex)
---

# CC-Bot · DoIt 238 — Secrets Hub completo

## Estado: DONE · PR #203 abierto

**PR:** https://github.com/alexanderhorn6720/rdm-bot/pull/203
**Branch:** `feat/secrets-hub-master-sync`
**Tiempo:** ~35 min
**LLM cost:** ~$0 (minimal, solo scripting)

---

## Qué se entregó

| Ítem | Estado |
|---|---|
| `secrets/master.env` (gitignored, 18 claves vacías) | ✅ |
| `secrets/master.env.age` (backup cifrado, commiteable) | ✅ |
| `secrets/age-key.txt` (gitignored, keypair generado) | ✅ local |
| `scripts/sync-all.sh` con `--dry-run` | ✅ |
| `scripts/encrypt-master.sh` | ✅ |
| `scripts/decrypt-master.sh` | ✅ |
| `scripts/init-master.sh` (setup: .dev.vars → master.env) | ✅ |
| `scripts/init-age-keypair.sh` (generar keypair) | ✅ |
| `scripts/sync-secret.sh` retirado | ✅ |
| `docs/secrets-inventory.md` actualizado (18 claves, 5 targets) | ✅ |
| `CLAUDE.md` §Secret access actualizado | ✅ |
| root `.gitignore` hardened | ✅ |

## Verify dry-run (pasó local)

```
sync-all done. 18 claves procesadas.
[dry] BEDS24_TOKEN -> apps/worker-bot ... apps/web (pages:rincondelmar-bot)
... x18 claves x5 targets
```

## Descubrimientos / surprises

1. **worker-feedback** no existe aún en CF (code: 10007). Las 2 claves (GITHUB_WEBHOOK_SECRET, R2_FEEDBACK_SECRET_KEY) están en master listas para cuando se deploye.
2. **worker-tours** tiene auth error con wrangler list (token sin permiso User Details). El worker sí está deployado; sync-all.sh propagará igual (secret put no requiere ese permiso).
3. **MANYCHAT_API_KEY** en el inventario era un typo — el nombre real (confirmado por wrangler) es `MANYCHAT_API_TOKEN`. Inventario corregido.
4. **master.env.age** commiteado contiene solo keys vacías. Alex corre `encrypt-master.sh` después de poblar con `init-master.sh` para tener un backup real.

## Checklist manual para Alex post-merge

1. `bash scripts/init-master.sh` → poblar desde `.dev.vars`
2. `bash scripts/sync-all.sh --dry-run` → verificar 18×5 targets
3. Rotar 1 secret de prueba end-to-end
4. `bash scripts/encrypt-master.sh` → commit `master.env.age`
5. **Respaldar `secrets/age-key.txt` OFFLINE** (checkbox en PR antes de mergear)

## Decisiones pendientes para Alex

Ninguna. Toda la spec venía cerrada desde thread/237.
