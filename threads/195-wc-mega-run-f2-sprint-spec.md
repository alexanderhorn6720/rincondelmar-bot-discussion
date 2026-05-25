---
thread: 195
author: WC (web)
date: 2026-05-24
topic: mega-run-F2-sprint-spec
mode: brain-deep
status: SUPERSEDED
superseded_by: 209
superseded_on: 2026-05-24
superseded_reason: thread/197 declared F2 postponed +1 semana post-inbox-ship + 8 GAPs técnicos materiales identified
related:
  - thread/148 §H (pre-flight F2 complete trigger — work NOT lost)
  - thread/197 (F2 postpone declaration)
  - thread/204 (parallel WC brain ultra del inbox)
  - thread/209 (audit + handoff doc explaining supersede)
tags: [mega-run, F2, autonomous, multi-cc, yolo, foundations-sprint, SUPERSEDED]
---

# ⚠️ THIS SPEC IS SUPERSEDED — DO NOT EXECUTE

> **Status**: `SUPERSEDED` por thread/209 el 2026-05-24.
>
> **NO PEGAR los 4 prompts copy-paste** que aparecían en respuesta WC misma sesión.
> Si los necesitas, requieren amendments (ver thread/209 §3 — 8 GAPs técnicos identified).
>
> **Por qué SUPERSEDED**:
> 1. **thread/197** (creado mismo día 2026-05-24 por otro WC paralelo) postpuso F2 +1 semana
> 2. **Inbox redesign shipped** (PR #167+#168+#169) consume prioridad operativa hoy
> 3. **8 GAPs técnicos materiales**: spec asume estado del repo distinto a realidad
>    (migration 0042 ya consumida, /admin/health ya tiene 5+ panels, heartbeat ya implementado via bot_config per ADR-003 §2.4, bucket Logpush distinto, TG single channel, Workers Paid plan activo, etc)
>
> **Lee thread/209** para handoff completo con audit + estado real del sistema.
>
> **Pre-flight F2 work NO se pierde** — Workers Paid + Logpush + CF_API_TOKEN están provisioned y funcionando (thread/148 §H). Sólo se postpone ejecución del worker-side ship.
>
> **Para retomar F2 cuando ventana se abra** (~+1 semana post inbox stabilization):
> - Aplicar amendments al spec F2 §3.1 + §3.5 per thread/148 §H §H.3 (bucket name + single TG channel)
> - Aplicar amendments al spec F2 §3.3 per ADR-003 §2.4 (heartbeat reuse `bot_config`, NOT new migration)
> - Update ADR-003 §2.3 stance (Workers Paid now active)
> - Regenerar PROMPT A (Worktree A) reflejando que /admin/health EXTEND no greenfield

---

> El contenido original del spec se preserva debajo de la línea como audit trail histórico, NO como instrucción ejecutable.

---

# Mega-run 195 — F2 Foundations Sprint + parallel work

## TL;DR

**Scope**: F2 ship LIVE + 8 parallel deliverables across 3-4 worktrees. ~3-4 días calendar bajo Yolo B Liberal. CC autónomo, Alex review final.

**Pre-conditions cumplidas** (per thread/148 §H, 2026-05-24):
- ✅ Workers Paid plan ACTIVE
- ✅ Logpush job LIVE (bucket `cloudflare-managed-90a63a4b`)
- ✅ R2 lifecycle 90d Enabled
- ✅ CF_API_TOKEN provisioned (rincondelmar-bot production)
- ✅ TG decision: 1 channel reusar
- ✅ Yolo B Liberal settings.json deployed 3 repos
- ✅ PR #18 (F1 spec) + PR #19 (F3 spec) merged con Alex votes

**Outputs esperados al cierre**:
- F2 LIVE en producción + soak 24h passed
- F1 + F3 canonical specs amended en rdm-platform
- PR #114 fixed + ready merge
- thread/179b master backlog v3 regen
- ~30 branches obsoletas cleanup
- meta-audit.sh enriquecido con settings.json validator
- (opcional) M1 Pricing brain deep spec
- (deferred) worker-feedback deploy

---

## §0 · Context

Post Run 184 + Yolo B Liberal + pre-flight F2 complete, el bottleneck restante es **ship velocity de foundations**. Run 184 validó multi-CC + judge pattern para 9 tasks en 1h wall-clock. Esta mega-run aplica mismo pattern a F2 ship + parallel work, escalando a 3-4 worktrees concurrent.

**Hipótesis**: bajo Yolo B Liberal, 3-4 worktrees ejecutan 8-10 tasks en 3-4 días wall-clock con ≤10% time Alex (review final + merges). F2 LIVE al cierre.

**Diferencia vs Run 184**:
- Yolo B Liberal active → 0 popups durante el run
- 3-4 worktrees vs 2
- F2 ship es la primera task DE CÓDIGO autónoma (Run 184 solo specs/docs)
- Production touch real — synthetic test pre-soak es non-negotiable

---

## §1 · Worktree allocation

### Worktree A — rdm-bot core (Sonnet, ~10h CC)

**Path**: `c:/dev/rdm/dev/bot/.claude/worktrees/wt-a-tactical` (existente)
**Branch**: nueva `feat/run-195-f2-ship` (worktree A creará al inicio)
**Modelo**: Sonnet (per Yolo B Liberal settings.json)
**Scope**: F2 ship completo + PR #114 migration fix

| Task | Effort | Output |
|---|---|---|
| A1 — F2 Day 1: `packages/shared` metrics + alerts + cron-heartbeat helpers + WAE bindings | 3h | Commit con tests |
| A2 — F2 Day 2: wire `emitMetric` + `recordCronHeartbeat` + expand `/admin/health` 5 panels | 3h | Commit con dashboard funcional |
| A3 — F2 Day 3: wire alerts + forced failure test + docs `rdm-bot/docs/spec/20-observability.md` | 2h | Commit + PR |
| A4 — PR #114 fix: rebase + renumber migration 0039 → NNNN | 15-30 min | Push to existing PR branch + comment |
| A5 — worker-feedback deploy (DEFERRED per Alex vote 1.1=B) | — | Skip este run |

**Total estimate**: ~8-9h CC autónomo across 3 días.

### Worktree B — rdm-discussion specs + cleanup (Opus, ~2h CC)

**Path**: `c:/dev/rdm/dev/discussion/.claude/worktrees/wt-b-specs` (existente)
**Branch**: nueva `feat/run-195-cleanup-and-backlog`
**Modelo**: Opus (per Yolo B Liberal settings.json)
**Scope**: backlog regen + meta-audit enrichment + cleanups

| Task | Effort | Output |
|---|---|---|
| B1 — thread/179b master backlog regen v3 (snapshot post Run 184 + pre-mega-run) | 45 min | thread numerado nuevo |
| B2 — settings.json validator en `scripts/meta-audit.sh` (anti-pattern auto-detect) | 1h | PR a meta-audit.sh |
| B3 — Branches cleanup rdm-bot via `git push origin --delete` (~30 candidates per thread/194 §E) | 15-30 min | Reporte en thread numerado |
| B4 — Worktrees cleanup post-PR-merges (al final, condicional) | 5 min | Comandos ejecutados o reportados |

**Total estimate**: ~2-3h CC autónomo.

### Worktree C — rdm-platform canonical amendments (Sonnet, ~1h CC)

**Path NUEVO**: `c:/dev/rdm/dev/platform/.claude/worktrees/wt-c-canonical` (CREAR en pre-flight)
**Branch**: nueva `feat/run-195-canonical-patches`
**Modelo**: Sonnet
**Scope**: Aplicar §6 patch F1 + §7 patch F3 a specs canónicos en rdm-platform

| Task | Effort | Output |
|---|---|---|
| C1 — Apply §6 patch a `foundations/F1-events-bus.md` (NNNN placeholder + dual-path soak + AC #13) | 30 min | Commit + PR |
| C2 — Apply §7 patch a `foundations/F3-staff-pwa.md` (separate user_roles + VAPID rotation + /yo/instalar + Karina coord in person) | 30 min | Commit + PR |
| C3 — Apply F2 spec updates per thread/148 §H (Logpush bucket name + single TG channel) | 20 min | Commit en mismo PR |
| C4 — Apply F1 spec update post Workers Paid (remove GH Actions conditionals, native cron confirmed) | 20 min | Commit en mismo PR |

**Total estimate**: ~1.5-2h CC autónomo.

### Worktree D — M1 Pricing brain spec (Opus, opcional ~2h)

**Path NUEVO**: `c:/dev/rdm/dev/discussion/.claude/worktrees/wt-d-m1-spec`
**Branch**: nueva `feat/run-195-m1-pricing-spec`
**Modelo**: Opus (brain mode profundo)
**Scope**: M1 Pricing brain deep spec — comprehensive 7-section template

| Task | Effort | Output |
|---|---|---|
| D1 — Brain deep M1 Pricing spec: context + scope + decisions + impl + tests + DoD + risks | 1.5-2h | PR con `foundations/M1-pricing-spec.md` open-for-alex-vote |

**Total estimate**: ~2h Opus autónomo.

---

## §2 · Prompts EXACTOS copy-paste

Los prompts EXACTOS para Alex copy-paste por terminal viven aparte del thread por longitud. Ver respuesta WC-web 2026-05-24 misma sesión, o regenerar con WC en próxima conversación.

Resumen de prompts:

- **Prompt A** (Worktree A, rdm-bot core, Sonnet): F2 Day 1+2+3 + PR #114 fix
- **Prompt B** (Worktree B, rdm-discussion, Opus): backlog regen + meta-audit enrichment + branches cleanup + worktrees cleanup
- **Prompt C** (Worktree C, rdm-platform, Sonnet): F1+F3+F2 canonical amendments + Workers Paid F1 update
- **Prompt D** (Worktree D, Opus, OPCIONAL): M1 Pricing brain deep spec

---

## §3 · Guardrails (toda la mega-run)

### Hard limits (Yolo B Liberal NO override)

- ❌ NO `git push --force` ningún branch (deny rule active)
- ❌ NO `rm -rf` (deny rule active)
- ❌ NO `DROP TABLE / TRUNCATE / DELETE FROM` via wrangler d1 execute (deny rule active)
- ❌ NO `wrangler deploy` production sin Alex explicit GO
- ❌ NO merge a main de ningún PR (Alex manual)
- ❌ NO ALTER TABLE durante multi-CC execution

### Halt conditions

- 🛑 Stuck >30 min en sub-tarea → halt + escalate threads/escalations/
- 🛑 Weekly cap consumido >70% antes de terminar → halt soft, complete current task y escalate
- 🛑 5h block hit ≥3 veces → halt worktree, reporta status
- 🛑 Production breakage detectado en F2 forced test → rollback inmediato (revert commit) + escalate
- 🛑 Conflict no-trivial en PR #114 fix → halt + escalate con análisis

### Escalation paths

Path canónico: `c:/dev/rdm/dev/discussion/threads/escalations/YYYY-MM-DD-NN-{worktree}-{topic}.md`

Si escalation creado: worktree afectado HALT inmediato, no continúa otras tasks del mismo worktree. Otros worktrees siguen.

---

## §4 · KPIs target por worktree

| Worktree | Tasks | Wall-clock estimate | KPI critical |
|---|---|---|---|
| A (rdm-bot) | 4 (A1-A4) | 3-4 días | F2 LIVE + forced test passed + PR #114 fixed |
| B (rdm-discussion) | 3-4 (B1-B4) | 2-3h CC | thread regen + meta-audit enriched + branches cleaned |
| C (rdm-platform) | 4 (C1-C4) | 1.5-2h CC | F1+F3+F2 canonical specs amended |
| D (opcional) | 1 (D1) | 1.5-2h Opus | M1 spec draft open-for-alex-vote |

### KPIs globales del mega-run

| KPI | Target |
|---|---|
| Tasks completadas sin escalation | ≥ 85% |
| Production breakage | 0 |
| Time Alex en mega-run | ≤ 30 min total |
| Weekly cap consumido | ≤ 55% (Max plan) |
| 5h blocks hit | 0-1 acceptable |
| Judge PASS rate | ≥ 90% |

---

## §5 · Reporte format esperado (al cierre)

Cada worktree genera al final:

- Métricas (wall-clock, tokens, halts, escalations)
- Tabla de tasks con status + output + SHA
- Cross-cutting findings
- Spec deviations con razón
- PRs/threads/commits producidos
- Anti-patterns evitados
- Pendientes/handoffs

WC-web consolida los 3-4 reportes en thread retrospective post-mega-run (igual a thread/189 para Run 184).

---

## §6 · Sequence diagram

```
2026-05-24 (hoy)
├─ Alex pre-flight F2 COMPLETE ✅
├─ Yolo B Liberal active ✅
└─ Alex lanza terminales A, B, C, [D]
     │
     ▼
Día 1
├─ Worktree A: F2 Day 1 (~3h) — packages/shared helpers + WAE bindings
├─ Worktree B: B1 backlog regen (~45 min) + B2 meta-audit (~1h)
├─ Worktree C: C1+C2 canonical patches F1+F3 (~1h)
└─ Worktree D: D1 M1 brain spec (~2h, opcional)
     │
     ▼
Día 2
├─ Worktree A: F2 Day 2 — wire metrics + /admin/health 5 panels
├─ Worktree B: B3 branches cleanup (~30 min)
└─ Worktree C: C3+C4 F2 + Workers Paid amendments (~40 min)
     │
     ▼
Día 3
├─ Worktree A: F2 Day 3 — alerts + forced test + docs
├─ Alex review C-PR canonical patches + merge
└─ Worktrees B+C: idle/done
     │
     ▼
Día 4
├─ Worktree A: A4 PR #114 fix (~30 min)
├─ Worktree A: open F2 PR
├─ Alex review F2 PR + merge + deploy worker-bot
└─ F2 soak 24h start
     │
     ▼
Día 5
├─ F2 soak day done
├─ Worktree B: B4 worktrees cleanup
├─ WC-web: thread retrospective
└─ Mega-run 195 OFFICIALLY CLOSED
```

---

## §7 · Rollback paths

### F2 deploy falla

1. Worktree A halt commitea revert del último deploy
2. Escalation con full diagnostic
3. Alex review: rollback total o fix forward decision
4. F2 ship retrying en próximo mini-run

### PR #114 fix breaks something

1. Worktree A halt sin push del fix
2. Branch del PR #114 quedan como estaba
3. Escalation con context
4. Alex decides: close PR vs differ fix a otro run

### Worker-bot tests fallan post F2 Day 2

1. Worktree A halt commitea fix tests
2. Si fix >30 min: escalate
3. Si fix simple: aplicar + continue

### CF API token Analytics fails to query WAE

1. Worktree A retry con curl manual
2. Si persiste: verifica scope correcto en CF dashboard
3. Si Alex confirma scope correcto + falla: escalate (CF infra issue)

---

## §8 · Pre-conditions check Alex (ANTES de copy-paste prompts)

| # | Check | Cómo |
|---|---|---|
| 1 | Todos PRs (#16, #17, #18, #19, #166) merged | Mobile, lista PRs |
| 2 | thread/148 §H posted | ✅ done (este turno) |
| 3 | Yolo B Liberal active en settings | ✅ done (este turno) |
| 4 | Worktrees existen (A, B) o crear (C, D) | `git worktree list` por repo |
| 5 | Wrangler funciona desde apps/web | ✅ done (test passed) |
| 6 | CC sesiones previas cerradas con /exit | Alex hace /exit en Terminal A y B viejos |
| 7 | NUC disponible 3-4 días para que CC corra | Alex confirma laptop power+network estables |

---

## §9 · Orden de lanzamiento

1. **Hoy 2026-05-24 noche o mañana**: Alex hace `/exit` en Terminales A y B activos del Run 184
2. **Cuando Alex listo**: abre 3-4 PowerShell nuevos
3. **Terminal A** primero (~3h work más larga, lanza primero para soak time)
4. **Terminal B + C** después en paralelo
5. **Terminal D** opcional al final si capacity OK

Cada worktree autorreporta en threads. Alex recibe Telegram al cierre de cada worktree (si TG_BOT_TOKEN+TG_CHAT_ID configurado en worker-pago — está LIVE).

---

## §10 · Después del mega-run

Cuando los 3-4 worktrees reporten done:

1. **WC-web genera thread retrospective** — métricas + lecciones (formato thread/189)
2. **Alex review PRs producidos** — F2 PR (rdm-bot), canonical patches PR (rdm-platform), backlog thread (rdm-discussion)
3. **Alex merge + deploy F2** a producción worker-bot
4. **F2 soak 24h**
5. **Próximo run = F1 ship sprint**

---

## §11 · See also

- thread/148 §H (pre-flight F2 complete trigger)
- thread/184 (Run 184 spec — Multi-CC pattern original)
- thread/189 (Run 184 retrospective — referencia)
- thread/190 (WC MCP audit infrastructure)
- thread/194 (CC wrangler CLI supplement)
- rdm-platform/foundations/F1-events-bus.md
- rdm-platform/foundations/F2-observability.md
- rdm-platform/foundations/F3-staff-pwa.md
- rdm-platform/decisions/ADR-002-foundations-seal.md

---

**Signed**: WC (web), 2026-05-24 — autorización Alex para arrancar mega-run pendiente.

---

> **⚠️ REMINDER: ESTE SPEC ES SUPERSEDED por thread/209 (2026-05-24). NO EJECUTAR. Lee thread/209 para handoff completo.**
