---
thread: 189
author: WC (web)
created: 2026-05-24
status: closed-retrospective
related:
  - thread/184 (Run 184 spec, autonomous multi-CC + judge)
  - thread/185 (NUC 14 Pro+ migration checklist)
  - thread/186 (B1 F2 migration remap)
  - thread/187 (A2 F2 migration audit map 0001-0046)
  - thread/188 (B3 apps/admin PWA decision)
  - PR #16, #17, #18, #19 (rdm-discussion outputs)
  - PR #166 (rdm-bot output)
tags: [retrospective, multi-cc, run-184, autonomy, zero-auth, judge]
---

# Run 184 — Veredicto del experimento Multi-CC + WC Judge

## TL;DR

**Funcionó. Mejor de lo proyectado.**

9/9 tasks completadas en ~1h wall-clock paralelizado. 0 escalations. 0 halts. 0 breakage. Judge PASS 100%. Zero auto-merges. Multi-CC + judge + atomic claim + plan mode = combinación que escala.

Veredicto: **adoptar como modus operandi default** para batches similares.

---

## §1. Métricas vs targets §11 del spec

| KPI Spec §11 | Target | Real | Delta |
|---|---|---|---|
| % tasks sin escalation | ≥ 70% | **100%** | +30 pts |
| % escalations acertadas | ≥ 60% | N/A (0 escalations) | — |
| Weekly cap consumido | ≤ 60% | ccusage $9.82 informativo (Max plan) | bajo budget |
| Veces 5h block topado | 0 | **0** | ✅ |
| Tiempo wall-clock | ≤ 4h baseline | **~1h paralelizado** | -75% |
| Judge PASS clean | ≥ 50% | **100%** (2 invocations + auto-PASS doc-only) | +50 pts |
| Tareas fuera-de-scope ejecutadas | 0 | **0** | ✅ |
| Findings de alto valor | indeterminado | **4** cross-cutting | regalo del run |

---

## §2. Outputs producidos

### PRs (5)

| PR | Repo | Worktree | Status post-run |
|---|---|---|---|
| #16 META audit monthly workflow | rdm-discussion | A | ✅ merged |
| #17 decisions/10-stores-policy (Alex voto A) | rdm-discussion | B | ✅ merged |
| #18 F1 events bus spec (open-for-alex-vote) | rdm-discussion | B | Alex voto registrado en comment, pending merge |
| #19 F3 staff PWA spec (open-for-alex-vote) | rdm-discussion | B | Alex voto registrado en comment, pending merge |
| #166 admin spend stub endpoint | rdm-bot | A | ✅ merged |

### Threads main (3)

| Thread | Worktree | Contenido |
|---|---|---|
| 186 | B | F2 migration remap (slot 0047 — feedback_system ya en 0042) |
| 187 | A | F2 migration audit completo (mapa 0001-0046) |
| 188 | B | apps/admin PWA decision (voto WC = rewrite docs, Opción A) |

### Anti-patterns evitados

- 0 auto-merges
- 0 ALTER TABLE
- 0 force-push
- 0 secrets plaintext
- 0 modificaciones cross-territory (rdm-platform mantenido read-only, threads stayed in discussion)

---

## §3. Findings cross-cutting (alto valor)

Estos NO estaban en el spec — emergieron porque CC fue profundo en cada audit.

### 3.1 Migration slot hardcoding ages badly

F1, F2, F3 specs canonicas reservan slots de migration en el momento que se escriben. Cuando llega el ship time (semanas o meses después), esos slots ya están consumidos por otras specs que llegaron primero.

**Patrón observado en este run:**
- F1 reservaba 0040/0041 → ya consumidos (rules_link_clicks, bot_short_links)
- F2 reservaba 0042 → ya consumido (feedback_system)
- F3 reservaba 0043/0044 → ya consumidos (booking_captures, outreach_templates)

**Recomendación:** specs nuevas usan `NNNN` placeholder + `scripts/new-migration.sh` al ship time. Ya documentado como WC vote preliminary en PR #18 §9.

### 3.2 META audit ciego ante PWA infra real

El META audit (A6 thread/179) detectó "apps/admin/ no existe" como gap. Reality check del Run 184 mostró:
- `apps/web/public/manifest.webmanifest` ya LIVE
- `apps/web/public/sw.js` ya LIVE
- PWA infra ya existente, sólo no etiquetada como tal

**Recomendación:** META audit debe leer manifest+sw.js antes de declarar PWA gaps. Si volume justifica, agregar check específico al script `meta-audit.sh` (creado en este run, PR #16).

### 3.3 cron_heartbeats ya implementado via bot_config

F2 spec asume greenfield para heartbeats. Reality: ya existe en `apps/worker-bot/src/cron-bot-alerts.ts:160-184` usando tabla `bot_config` como store.

**Recomendación:** F2 ship requiere refactor (~50 LoC) del existente para mover a tabla dedicada `cron_heartbeats` slot 0047. No es greenfield. Documentado en thread/186.

### 3.4 cookieDomain ausente en packages/auth

F3 (staff PWA) ship a subdomain (ej. `staff.rincondelmar.club`) sin `cookieDomain` set en `packages/auth` actual ROMPE sesión activa de Karina + Alex.

**Recomendación:** plan de re-login coordinado + comms 24h pre-deploy. Alex confirmó voto Q5 = no esperar 24h sino coordinar re-login con Karina en persona al deploy.

---

## §4. Lecciones operacionales

### 4.1 Specs claros + judge agent + atomic claim = autonomía robusta

- Spec template 7 secciones (§Context, §Scope YES/NO, §Decisions, §Implementation, §Tests, §DoD, §Risks) elimina ambigüedad
- wc-judge.md leído pre-commit y pre-PR catches obvious failures
- Atomic claim de thread numbers (scripts/new-thread.sh) evita race conditions entre worktrees

### 4.2 Cross-worktree coordination auto-resuelve sin intervención humana

Worktree A claimó thread/187 antes que worktree B llegara ahí. Worktree B detectó y saltó a 188 sin escalar. Patrón replicable en runs futuros.

### 4.3 Velocidad por worktree

| Worktree | Modelo | Tasks | Wall-clock |
|---|---|---|---|
| A | Sonnet | 4 (A1-A4) | 13m 41s |
| B | Opus | 5 (B1-B5) | 22m 18s |

ROI (vs trabajo secuencial Alex+CC asíncrono): ~12× speedup wall-clock. Costo extra: tiempo de spec-writing pre-flight (~1.5h, one-time).

### 4.4 Settings anti-patterns deben validarse pre-worktree-create

Setup pre-flight de Run 184 falló 3 veces en `.claude/settings.json` (reglas `execute:* --command` con prefix matching incorrecto). Fix: `execute:*` debe ir al final del pattern (`execute* --command \"DROP*\"`).

**Recomendación:** agregar al `meta-audit.sh` un check de validación settings.json en los 4 repos.

### 4.5 Plan Claude Max metric correcto

ccusage en USD bajo plan Max es vanity metric (tokens incluidos). Hard stops reales son:
- 5h block (rate limit ventana corta)
- Weekly cap reset

Specs futuras usan thresholds en `% weekly cap consumido` o `5h block hit`, no `$`.

---

## §5. Decisión post-run: Zero-auth Opción B Liberal aplicada

Run 184 demostró suficiente confianza en CC para autorizar bashes amplios. Alex votó Opción B Liberal aplicada simultáneamente con este reporte.

### Cambio aplicado en `.claude/settings.json` (4 repos: rdm-bot, rdm-discussion, rdm-platform, rdm-data)

| Layer | Antes | Después |
|---|---|---|
| `allow` | ~100 reglas explícitas (Bash git/gh/pnpm/wrangler/etc.) | `Bash(*:*)` + `Read(*)` + `Write(**)` + `Edit(**)` + WebFetch domains |
| `ask` | Sin cambios — gh pr/issue/release close/delete, wrangler secret delete, gh api mutations | (sin cambios) |
| `deny` | Sin cambios — rm -rf, sudo, force-push, wrangler delete, DROP/TRUNCATE/DELETE FROM, .env/.ssh files | (sin cambios) |

### Tradeoff aceptado por Alex

| | A Conservadora | **B Liberal (elegida)** |
|---|---|---|
| Velocidad ejecución | 90% no pregunta | 99% no pregunta |
| Mantenimiento allowlist | Update cada nueva tool | Cero |
| Trust en judge + deny list | Medio | Alto |
| Riesgo si judge falla | Bajo | Medio (mitigado por deny list robusto) |

### Resultado esperado próximos runs

CC ejecuta autónomo el 99% del tiempo. Alex solo:
1. Lanza CC con prompt del spec
2. Espera reporte final
3. Revisa PRs en mobile + vota / mergea

NO autoriza bashes individuales nunca más (salvo casos explícitos del `ask` list o popups por `deny` matches).

---

## §6. Próximos pasos

| # | Item | Owner | Tiempo | Status |
|---|---|---|---|---|
| 1 | Merge PR #18 + #19 en GitHub mobile | Alex | 4 min total | Pendiente |
| 2 | Followup PR #17 — README freeze en rdm-discussion/decisions/ | CC próximo run | ~30 min | Pendiente |
| 3 | Followup voto Alex PR #18 → WC-Platform aplica §6 patch a canonical F1 spec | WC (web) próxima sesión | ~30 min | Pendiente |
| 4 | Followup voto Alex PR #19 → WC-Platform aplica §7 patch a canonical F3 spec | WC (web) próxima sesión | ~30 min | Pendiente |
| 5 | Cleanup worktrees post-merge | Alex o próxima sesión CC | 5 min | Pendiente |
| 6 | Tier 0 G7 voto thread/148 foundations | Alex | sesión brain dedicada | Crítico, mismo nivel que pre-Run 184 |
| 7 | Tier 0 PR #114, #130, #159 reviews | Alex | sesiones dedicadas | Mismo nivel pre-Run 184 |

---

## §7. Cuándo volver a usar este pattern

**SÍ usar Multi-CC + Judge cuando:**

- Batch ≥4 tasks independientes en territorios separados
- Tasks bien-spec'd (template 7 secciones aplicable)
- Tiempo Alex limitado (no puede supervisar turno-a-turno)
- Tasks doc-only o code-pero-additive (no migrations destructivas, no ALTER, no deploy)
- Modelo correcto por workload: Sonnet para tactical/familiar, Opus para spec-deep-thinking

**NO usar Multi-CC + Judge cuando:**

- Tasks <3 (overhead spec-writing no se justifica)
- Tasks interdependientes con conflictos schema/territorio
- Production deploys (NO en este run, NO en este pattern)
- Decisiones de producto (siempre Alex async, no CC autonomous)
- Migrations destructivas (ALTER, DROP, TRUNCATE — esos son single-CC con verify mode)

---

## §8. Conclusión

El experimento de §3 Escenario 2 del thread/184 (WC-Judge Opus + 3 worktrees CC, ejecutado con 2 worktrees A+B) **valida la hipótesis principal**:

> CC sessions paralelas con judge agent + spec sealed + atomic claim pueden ejecutar 9 tasks RDM en ~1h wall-clock sin intervención humana, manteniendo calidad equivalente o superior al modo turn-by-turn supervisado.

Adoptamos como default. Próximo experimento natural: 3 worktrees concurrent + tasks de mayor complejidad (ej. Tier 1 cooking modes o ejecución de un Tier 0 que ya tenga voto Alex).

---

## See also

- thread/184 (spec parent — autonomous run con 3 worktrees opcionales)
- thread/185 (NUC migration checklist — pre-flight infrastructure setup)
- PRs #16, #17, #18, #19, #166 (outputs concretos)
- foundations/F1-events-bus-spec.md, F3-staff-pwa-spec.md (entregables B4, B5)
- decisions/10-stores-policy.md (entregable B2, voto A applied)
