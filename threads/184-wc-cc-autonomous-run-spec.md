---
thread: 184
author: wc
type: spec
mode: DoIt
created: 2026-05-23
supersedes: null
superseded_by: null
related: [148, 174, 178, 180, 182, 183]
status: active
---

# Thread/184 — Autonomous Run Spec (Escenario 2: WC-Judge + Multi-CC)

## §0. Contexto

Wave 1 cerrado en thread/182 (PR #165 merged). Alex fuera ~1 semana.

Objetivo: drainage máximo del pipeline sin intervención Alex usando
Arquitectura A (1 judge) + multi-CC paralelo (3 worktrees concurrent).

Voto Alex 2026-05-23: GO Escenario 2.

Items que NO se tocan en este run (requieren Alex):
- G7 thread/148 voto sub-items
- G8 Analytics activation voto A/B/C
- Reviews PRs #114, #130, #159 (rdm-bot), #8, #10 (rdm-discussion)
- A5 AirBnB Chrome login persistente
- F2/F1/F3 ship (requieren G7 voto primero)
- Auto-merge a main (siempre review Alex)

---

## §1. Setup judge subagent

Archivo a crear en cada worktree CC: `.claude/agents/wc-judge.md`

```markdown
---
name: wc-judge
description: Strategic judge for CC tactical work. Reviews diffs pre-commit and PRs pre-merge against RDM anti-patterns. Escalates to Alex via threads/escalations/ when ambiguous.
model: opus
tools: Read, Grep, Glob, Bash(git diff:*, git log:*, git status:*)
---

# Rol

Eres WC-Judge. Filtras decisiones tactical de CC contra anti-patterns
RDM antes de commit/PR. NO ejecutas código. NO modificas archivos.
Solo emites veredicto.

# Formato respuesta obligatorio

VEREDICTO: PASS | FAIL | ESCALATE
RAZÓN: <2-3 líneas máx>
ACCIÓN: <qué debe hacer CC ahora>

# Anti-patterns RDM (FAIL automático si detectas)

PRODUCTO:
- LLM money decision autónoma (pricing, refunds, billing)
- Casa Chamán surfaced en Greeter/guest channel (roomId 679176, deferred Q3 2026)
- Pet fee escrito "/noche" en cualquier output (correcto: $300 MXN por mascota por estancia, max 2)
- Beds24 sync mode = Everything (correcto: Prices & Availability only, multiplier 1.25, 365-day horizon)

EJECUCIÓN:
- Commit con secrets plaintext (API keys, tokens, passwords)
- ALTER TABLE durante run (multi-agent unsafe)
- Production deploy viernes después 5pm
- Hardcoded Windows paths sin placeholder <USER_HOME>
- "Alexa" usuario filesystem vs "Alex" interacción confundidos
- "tests pass" sin self-review del diff
- Auto-merge a main sin Alex review
- Force-push, delete branches sin merge confirmado

WORKFLOW:
- CC modifica rdm-platform sin Alex explicit task (read-only para CC)
- WC implementa código en repos de código (solo specs/threads)
- Out-of-scope fix inline (correcto: anotar en reporte, abrir issue)

# Stack canónico RDM (FAIL si diverge sin razón documentada)

- Workers: Hono framework
- DB: D1 (rincon UUID d81622d7-...) con Drizzle ORM
- Storage: R2 (rdm-knowledge, assetsrdm)
- KV: KV_IDEMPOTENCY
- Auth: Better Auth magic-link
- Build: pnpm + Turborepo + Wrangler 4.14.1 + nodejs_compat_v2
- Lint: Biome. Tests: Vitest + happy-dom
- Frontend: Astro 5 + React 19 islands

# Triggers ESCALATE (commit a threads/escalations/YYYY-MM-DD-NN-topic.md)

- Decisión que afecta money/cost > $5 USD/mes ongoing
- Scope change vs spec original (item en spec que ya no aplica, o nuevo no listado)
- Conflicto entre dos anti-patterns
- Production deploy fuera ventana segura
- Operación irreversible con >10 items afectados
- Cost LLM acumulado sesión > $15
- CC reporta halt >30 min sin auto-recovery clara
- Voto A/B/C requerido (decisión arquitectural)

# Formato escalation file

```
threads/escalations/YYYY-MM-DD-NN-{topic-kebab}.md

# Escalation NN — {topic}

## Contexto (3 líneas)
## Decisión pendiente
## Opciones
- A) ...
- B) ...
- C) ...
## Voto WC preliminar
## Bloqueador downstream
## Costo si esperamos
```

# Triggers PASS automático

- Doc-only changes (markdown, comments)
- Tests adicionales sin cambio src
- Refactor sin cambio behavior (verificado con tests)
- Migration número siguiente disponible (verificado con ls)
- Dependency bump patch/minor con tests passing

# Estilo respuesta

ES técnico conciso. Sin elogios. Sin emojis decorativos.
Tablas sobre prosa. Mobile-friendly.
```

---

## §2. Worktree A — CC-Bot tactical (Sonnet)

Path local Alex: `c:/dev/rdm/dev/bot/.claude/worktrees/wt-a-tactical/`
Branch base: `main` (rdm-bot)
Modelo CC: Sonnet 4.6 default
Judge: invoca `wc-judge` pre-commit + pre-PR

### Tasks

| T | Task | Esfuerzo | Output |
|---|---|---|---|
| A1 | META audit cron setup (item 4.2). Usar scripts en `reports/.audit-scratch/` (rdm-discussion) wrapped en GitHub Action mensual. | 1h | PR rdm-discussion con `.github/workflows/meta-audit-monthly.yml` |
| A2 | F2 migration audit informacional. List `apps/worker-bot/migrations/` actual. Identify next available slot. Report en thread/185 (CC-Bot). NO modify schema. | 30 min | thread/185 con migration map + free slot recommendation |
| A3 | Admin API spend scaffold read-only (item 4.5 partial). Crear endpoint `/api/spend/anthropic` stub que retorna `{error: "ADMIN_API_KEY not provisioned"}` cuando secret missing. Wire en `/admin/health`. | 2h | PR rdm-bot con stub endpoint + UI placeholder |
| A4 | rdm-data CLAUDE.md skeleton. Crear `.claude/settings.json` con `{"model": "sonnet"}` + CLAUDE.md workstream stub. Commit directo a rdm-data main. | 30 min | Commit rdm-data |

Halt conditions A:
- Migration conflict con thread/175 T2 (0046 cost_telemetry) o F2 reservation
- D1 schema modification (escalate inmediato)
- Halt >30 min en cualquier T → reporta y pasa al siguiente

---

## §3. Worktree B — CC-Discussion specs drafter (Opus)

Path local Alex: `c:/dev/rdm/dev/discussion/.claude/worktrees/wt-b-specs/`
Branch base: `main` (rdm-discussion)
Modelo CC: Opus 4.7 (specs requieren brain mode)
Judge: invoca `wc-judge` pre-PR (drafts no requieren judge en cada commit)

### Tasks

| T | Task | Esfuerzo | Output |
|---|---|---|---|
| B1 | F2 spec refactor migration remap (item 2.1). Audit thread/175 T2 (0046) + filesystem rdm-bot. Reserva nuevo slot (probable 0047) en F2 spec. | 1h | thread/186 con F2 spec amended |
| B2 | Decisions stores policy doc (item 2.2). Redactar `decisions/10-stores-policy.md` con opciones A/B/C y voto WC preliminar. NO cierra (espera voto Alex). | 1h | PR rdm-discussion con draft decision 10 |
| B3 | apps/admin PWA decision doc (item 2.3). Redactar thread con opciones A/B (rewrite docs vs build separate) y voto WC preliminar. | 1h | thread/187 con decision draft |
| B4 | F1 spec expansion. Tomar `foundations/README.md` §F1 + thread/148 voto context + crear `foundations/F1-events-bus-spec.md` con sql migration + cron design + consumer registry config. | 2h | PR rdm-discussion con F1 spec detail |
| B5 | F3 spec expansion. Tomar `foundations/README.md` §F3 + crear `foundations/F3-staff-pwa-spec.md` con auth flow + service worker scope + VAPID setup + sideload UX. | 2h | PR rdm-discussion con F3 spec detail |

Restricciones B:
- NINGÚN spec se cierra sin voto Alex (todos terminan en `status: draft-pending-alex-vote`)
- Voto WC preliminar marcado claramente "WC preliminary, Alex final"
- B2/B3 incluyen recomendación pero NO ejecutan la decisión

Halt conditions B:
- Conflicto entre dos drafts (B4 y B5 referencian F2 que aún no ship) → asume F2 reservation de B1, no F2 ship
- Halt >30 min → reporta y pasa al siguiente

---

## §4. Worktree C — Standby/follow-up

Path local Alex: `c:/dev/rdm/dev/discussion/.claude/worktrees/wt-c-standby/`
Branch base: `main` (rdm-discussion)
Modelo CC: Sonnet 4.6
Activación: solo si A o B terminan antes y queda budget LLM

### Tasks (en orden si activado)

| T | Task | Esfuerzo | Output |
|---|---|---|---|
| C1 | Wave 2 backlog regen (item 9.3). Refresh thread/179b post-184 lands. Update tier 0/2/3 estados. | 1h | PR rdm-discussion con 179b actualizado |
| C2 | Cost analysis breve post-ccusage (item 4.4). Si fecha ≥ 2026-05-29: compare $185 baseline vs 7-day post velocity stack ship. | 1h | thread con cost analysis |
| C3 | A5 AirBnB archival prep (item 5.1). Audit branch `feat/a5-airbnb-bulk-approve-writeback` + threads 130/136/137/138. Redactar propuesta archive a `archive/a5-airbnb/`. NO ejecuta archive (espera Alex). | 1h | thread con archive proposal |

---

## §5. Escalation contract

### Path
`threads/escalations/YYYY-MM-DD-NN-{topic}.md` (rdm-discussion)
Numbering NN secuencial por día. Atomic claim via script `new-thread.sh` adaptado.

### Template

```markdown
# Escalation NN — {topic}

**From**: {worktree} (A/B/C)
**Date**: YYYY-MM-DD
**Trigger**: {trigger desde judge}

## Contexto
{3 líneas máx — qué tarea, qué bloqueo}

## Decisión pendiente
{1 línea}

## Opciones
- A) ...
- B) ...
- C) ...

## Voto WC preliminar
{con razón}

## Bloqueador downstream
{qué tasks dependen}

## Si esperamos vs ejecutamos
{costo de cada path}
```

### Triggers escalation (judge decide ESCALATE)

Ya listados en §1 system prompt judge.

### Acción CC tras escalation

CC commitea escalation file, pasa al siguiente task del worktree, NO bloquea sesión. Alex revisa al regresar.

---

## §6. Guardrails no-negociables

### Ejecución autónoma

| Guardrail | Valor |
|---|---|
| Halt sub-tarea | >30 min stuck |
| Cost LLM por worktree | warning $15, halt $25 |
| Total worktrees concurrent | max 3 |
| Atomic claim threads | obligatorio (script existente) |
| Self-review hook | ON (instalado thread/175 T4) |
| Plan mode | ON default |

### Operaciones prohibidas en este run

- Auto-merge a main (cualquier repo)
- Force-push
- Delete branches
- ALTER TABLE (cualquier D1 schema mod)
- Commit con secrets plaintext
- Production deploy (Workers, Pages, secrets)
- Modificar rdm-platform sin escalation previa
- WC redactar código en `apps/` o `packages/`

### Operaciones permitidas

- Commit a branches `feat/*`, `fix/*`, `chore/*`, `docs/*` en rdm-bot, rdm-discussion, rdm-data
- Push a `main` rdm-discussion para threads/specs/escalations
- Push a `main` rdm-data para CLAUDE.md + settings (stub only)
- Crear PRs (NO merge)
- Tests local Vitest
- Wrangler dry-run (NO deploy)

---

## §7. Definition of done

Run completo cuando se cumpla cualquiera:

1. Las 4 tasks A + 5 tasks B + (opcional) 3 tasks C completadas
2. Cost LLM acumulado total > $40 (halt suave)
3. 7 días calendario desde inicio (2026-05-30)
4. Alex regresa y dice "stop"

### Entregables al cierre

- N PRs `ready-review` en rdm-bot, rdm-discussion, rdm-data
- M escalations en `threads/escalations/`
- thread/188 (CC-Bot) o thread/189 (CC-Discussion) con report final:
  - Tasks completed / partial / halted
  - Cost LLM total por worktree
  - Lessons learned (para v4 DoIt template si aplica)
  - Backlog drift detectado (items que cambiaron estado)

---

## §8. Reporting al regreso Alex

Inbox priorizado para Alex (en orden ataque):

1. **Escalations** — leer primero, son decisiones que detuvieron progreso
2. **PRs ready-review** — batch review mobile-friendly
3. **Cost report** — verificar si run quemó budget esperado
4. **Tier 0 original** — G7 voto thread/148 sigue siendo critical-path
5. **Drift report** — qué del doc rdm-pipeline-open-state-v2.txt cambió

Estimado tiempo Alex retorno: ~2-3h batch (lecturas + votos + merges).

---

## §9. Pre-flight Alex (single action antes de salir)

Ejecutar en orden:

```powershell
# 1. Confirmar main limpio en los 3 repos
cd c:/dev/rdm/dev/bot         ; git status ; git pull --rebase
cd c:/dev/rdm/dev/discussion  ; git status ; git pull --rebase
# rdm-data: clonar si aún no existe
Test-Path c:/dev/rdm/dev/data
# Si False: git clone https://github.com/alexanderhorn6720/rdm-data.git c:/dev/rdm/dev/data

# 2. Crear 3 worktrees
cd c:/dev/rdm/dev/bot
git worktree add .claude/worktrees/wt-a-tactical -b feat/run-184-wt-a-tactical

cd c:/dev/rdm/dev/discussion
git worktree add .claude/worktrees/wt-b-specs -b feat/run-184-wt-b-specs
git worktree add .claude/worktrees/wt-c-standby -b feat/run-184-wt-c-standby

# 3. Copiar wc-judge.md a cada worktree
# (CC primera sesión hace esto automático leyendo §1 del thread)

# 4. Lanzar 3 sesiones CC en terminales separados
# Terminal 1: cd .../wt-a-tactical ; claude
# Terminal 2: cd .../wt-b-specs    ; claude --model opus
# Terminal 3: standby (lanzar solo si A o B terminan antes)

# 5. En cada sesión CC, prompt inicial:
# "Lee threads/184-wc-cc-autonomous-run-spec.md en rdm-discussion.
#  Estás en worktree {A|B|C}. Ejecuta tasks de §{2|3|4} en orden.
#  Invoca wc-judge pre-commit y pre-PR. Escala según §5."
```

Total tiempo Alex pre-flight: ~10 min.

---

## §10. Anti-patterns adoption (para este run)

- NO ejecutar A1+A3+B4+B5 en paralelo en mismo repo (conflictos git)
  → A tactical es rdm-bot, B specs es rdm-discussion, no colisionan
- NO eliminar safety nets en bloque (self-review hook + plan mode quedan ON)
- NO confiar en "tests pass" sin self-review diff
- NO ejecutar B4 (F1 spec) o B5 (F3 spec) antes que B1 (F2 remap) commit
  → B ejecuta tasks en orden B1 → B2 → B3 → B4 → B5

---

## §11. Métricas de calibración (para review post-run)

Capturar para decidir si Escenario 2 vale segundo round:

| Métrica | Cómo medir | Target |
|---|---|---|
| % tasks completed sin escalation | tasks_pass / total_tasks | ≥ 70% |
| % escalations acertadas (Alex acepta voto WC) | alex_accept_wc_vote / total_escalations | ≥ 60% |
| Cost LLM real vs estimate | actual_usd / 40_estimate | ≤ 1.5× |
| Tiempo Alex retorno vs baseline | hours_to_drain / 8h_baseline | ≤ 0.5× |
| PRs auto-mergeable (judge PASS clean) | clean_prs / total_prs | ≥ 50% |

Reporte de métricas obligatorio en thread/188.

---

## §12. Si run falla catastrófico

Halt total si:
- 2+ worktrees reportan halt simultaneous
- Cost LLM > $60 acumulado (1.5× del 40 cap)
- Production breakage detected (cualquier deploy accidental)
- Judge devuelve FAIL en >3 commits consecutivos del mismo worktree

Acción halt total:
- Commit último estado de cada worktree (WIP commits OK)
- Crear `threads/escalations/YYYY-MM-DD-NN-HALT-TOTAL.md` con razón
- Telegram alert si configurado (TG_CHAT_ID_PAGOS reusa)
- NO mergear nada hasta Alex regreso

---

## §13. Closing

Este spec es autoridad para el run autónomo. CC lee, ejecuta, escala
según §5, reporta según §7.

WC (claude.ai web) NO interviene durante el run salvo que Alex
abra nueva sesión y pregunte. Si Alex interrumpe, run continúa
hasta Alex diga "stop" explícito.

Próximo thread esperado: 185 (CC-Bot A2 migration audit report)
o 186 (CC-Discussion B1 F2 remap), según cuál termine primero.

---

**END OF SPEC**
