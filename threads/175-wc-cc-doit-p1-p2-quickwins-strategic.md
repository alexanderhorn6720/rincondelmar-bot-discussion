---
thread: 175
author: WC
date: 2026-05-22
topic: cc-doit-p1-p2-quickwins-strategic-execution
mode: DoIt
status: ready-for-cc-execution
target_session: nueva sesión CC en `c:/dev/rdm/dev/bot/` (NO la misma que ejecuta thread/176)
inputs:
  - thread/171 (WC brain ultra origen)
  - thread/172 (CC challenge — base prioridades técnicas, 19 días-CC quantification)
  - thread/173 (WC-Platform challenge — Charter, anti-pattern ADR-001 NO LLM money)
  - thread/174 (WC síntesis + posición ajustada)
  - rdm-bot/CLAUDE.md (operating manual CC)
  - rdm-bot/.claude/settings.json (permission lists, allowlists, deny lists)
  - rdm-bot/scripts/{new-migration.sh, safe-deploy.sh, sync-secret.sh} (referencia para new-thread.sh)
alex_votes_constraints:
  q1: SÍ test empírico pre-split → NO formalizar multi-WC todavía, NO redactar ADR-002
  q2: Judge BI (Alex + Automated) → NO L2 WC-Impl reviewer formal
  q3: Casa Chamán ignorar
  q4: operativo → foundations → M1-M5 → NO M1 ni F2 LIVE todavía, NO M1-M5
  q5: cost analysis BREVE post-ccusage
deliverable: 5 PRs ejecutados en secuencia respetando dependencias, todos pasan smoke + tests
total_estimated_cc_days: 8 en serie / 5-6 con paralelización (T1+T2, T4+T5)
total_estimated_llm_budget: $35-50 USD
halt_global_budget: $75 USD (1.5× upper bound)
---

# DoIt CC — P1 quick wins + P2 estratégico

## §1 Contexto

Tras retos 171/172/173/174 hay consenso entre CC-Bot y WC-Platform sobre
qué destrabar primero. Alex votó Q1-Q5. Este thread codifica las tareas
de CC en una sola sesión, ordenadas por dependencia.

**Realidad confirmada por CC en thread/172:**
- `scripts/new-thread.sh` NO EXISTE pese a estar en CLAUDE.md (4 referencias) y settings.json:77 (allowlist).
- 27/204 threads (13%) tienen colisiones de numeración por race conditions sin atomic claim.
- `ccusage` NO está instalado. Cost data real = 0.
- Halts CC últimos 30d todos externos (Chrome MCP, sessions, tokens expirados), no por razonamiento.
- Auto-merge ya activo (PR #122 mergeado en 9 seg). Self-review checklist es honor system.

**Este DoIt cierra ese gap.**

## §2 Scope

### SÍ

- T1 — `new-thread.sh` real con flock + retry
- T2 — ccusage daily cron + Telegram alert si excede budget
- T3 — Schema validator threads en CI
- T4 — Self-review checklist hook (solo auto-verificables)
- T5 — Cost limit hook integrado con ccusage

Cada task = 1 PR. Total 5 PRs.

### NO

- NO tocar `apps/worker-bot/`, `packages/agents/`, Greeter, Booker prompts
- NO tocar `apps/worker-pago`, `apps/worker-tours`, `apps/web` (excepto si T2 dashboard requiere page mínima)
- NO implementar F2 observability LIVE (per Q4, espera ordenamiento operativo post META audit)
- NO arrancar nada de M1-M5
- NO formalizar multi-WC (no ADR-002)
- NO Casa Chamán
- NO L2 WC-Impl reviewer setup
- NO L3 LLM-as-judge sobre PRs (espera golden sets, M5+F1, paso post-test)
- NO tocar Browserbase / Chrome MCP / A5 thread/127
- NO migraciones SQL nuevas
- NO open issues automated — si encuentras out-of-scope, declara en thread response, no fix inline

## §3 Decisiones cerradas (no re-litigar)

1. Script `new-thread.sh` real vive en `rdm-discussion/scripts/new-thread.sh` (porque los threads viven en rdm-discussion). Wrapper en `rdm-bot/scripts/new-thread.sh` que delega.
2. ccusage corre como cron CF (no local). Output a D1 table nueva `cost_telemetry`. Dashboard mínimo en `apps/admin` o si no existe, endpoint API en `apps/worker-bot/routes/`.
3. Schema validator usa JSON Schema (draft 2020-12) + GitHub Action lint. Modo soft (warn) primero por 7 días, después hard (fail PR).
4. Self-review checklist hook: solo items auto-verificables del checklist en `rdm-bot/CLAUDE.md:107-125`. Items que requieren juicio humano quedan honor system.
5. Cost limit hook: lee `cost_telemetry` D1, compara con budget declarado en thread frontmatter (`estimated_llm_budget`), trigger Telegram alert al 1.0×, halt automático al 1.5×.
6. Branches: `feat/scripts-new-thread-atomic`, `feat/ccusage-cron`, `feat/threads-schema-ci`, `feat/self-review-hook`, `feat/cost-limit-hook`.
7. Conventional commits.
8. NO touch `wrangler.toml` de workers existentes excepto crear nuevo cron binding (T2).
9. Tests obligatorios por task (ver §5).

## §4 Implementación

### T1 — `new-thread.sh` real con flock + retry

**Esfuerzo**: 1 día. **PR scope**: ~150 LoC.

**Files**:
- CREATE `rdm-discussion/scripts/new-thread.sh` (lógica real)
- CREATE `rdm-bot/scripts/new-thread.sh` (wrapper que delega via path absoluto a discussion)
- CREATE `rdm-discussion/scripts/tests/test_new_thread.sh` (unit tests bash)
- UPDATE `rdm-discussion/CLAUDE.md` línea apropiada (documentar uso real)
- UPDATE `rdm-bot/CLAUDE.md:65, 70, 119, 127` (clarify wrapper delegation)

**Specificación funcional**:
```bash
# Uso:
bash scripts/new-thread.sh <author> <topic-slug>

# Comportamiento:
1. cd a rdm-discussion/threads/
2. git pull --rebase origin main (con timeout 10s)
3. flock -w 30 scripts/.new-thread.lock {
     N=$(ls threads/ | grep -oP '^\d+' | sort -n | tail -1)
     NEXT=$((N + 1))
     PATH="threads/${NEXT}-${author}-${topic-slug}.md"
     touch stub con frontmatter mínimo (thread:NEXT, author, date, status:draft)
     git add stub
     git commit -m "thread/${NEXT}: stub (atomic claim)"
     git push origin main --no-rebase  # if fails, retry up to 3 with jitter 500-2000ms
   }
4. Echo $PATH a stdout (para que CC lea su número asignado)
5. Exit 0 si éxito, exit 1 si falla tras 3 retries
```

**Wrapper en rdm-bot**:
```bash
#!/bin/bash
DISCUSSION_DIR="$(dirname "$(realpath "$0")")/../../discussion"
[ -d "$DISCUSSION_DIR" ] || { echo "Error: rdm-discussion not at $DISCUSSION_DIR"; exit 1; }
bash "$DISCUSSION_DIR/scripts/new-thread.sh" "$@"
```

**Tests** (test_new_thread.sh):
1. Crea thread cuando no hay colisión → exit 0, archivo existe con número siguiente
2. Simulate race: 2 invocations concurrentes → ambas exit 0, números distintos consecutivos
3. Push fail simulation → retry hasta 3 veces con jitter
4. Lock timeout → exit 1 con mensaje claro

### T2 — ccusage daily cron + Telegram alert

**Esfuerzo**: 1 día. **PR scope**: ~250 LoC.

**Pre-flight**:
- Verify ccusage runs locally: `npx -y ccusage@latest daily --json` (output esperado: JSON array)
- Si npx falla en CF Workers → fallback: implement minimal ccusage equivalent vía Anthropic API usage endpoint

**Files**:
- CREATE D1 migration `0040_cost_telemetry.sql` (verify número libre, si colisión renombrar)
- CREATE `apps/worker-bot/src/cron/ccusage-daily.ts` (cron handler)
- UPDATE `apps/worker-bot/wrangler.toml` (add cron trigger `0 7 * * *` UTC = 1am Acapulco)
- CREATE `apps/worker-bot/src/cron/__tests__/ccusage-daily.test.ts`
- CREATE `apps/worker-bot/src/routes/cost-telemetry.ts` (endpoint read-only `/api/cost`)

**Schema D1**:
```sql
CREATE TABLE cost_telemetry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,            -- YYYY-MM-DD
  source TEXT NOT NULL,          -- 'ccusage' | 'anthropic-api'
  total_cost_usd REAL NOT NULL,
  by_model_json TEXT,            -- JSON breakdown
  raw_data TEXT,                 -- raw ccusage output JSON
  inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_cost_telemetry_date ON cost_telemetry(date);
```

**Lógica cron**:
1. Run `npx -y ccusage@latest daily --json --since 1d` o equivalente
2. Parse JSON, extract daily total + by_model
3. INSERT a D1 cost_telemetry
4. Read budget declarado (env var `DAILY_COST_BUDGET_USD`, default $5)
5. Si daily_total > budget × 1.0 → Telegram alert warning
6. Si daily_total > budget × 1.5 → Telegram alert critical
7. Log structured

**Tests**:
1. Mock ccusage output → assert D1 INSERT
2. Mock excess budget → assert Telegram called with critical
3. Mock empty output → graceful exit, no INSERT, no alert
4. Endpoint `/api/cost?days=7` returns last 7 días

### T3 — Schema validator threads en CI

**Esfuerzo**: 2 días. **PR scope**: ~300 LoC.

**Files**:
- CREATE `rdm-discussion/.github/workflows/thread-schema-lint.yml`
- CREATE `rdm-discussion/schemas/thread.schema.json` (JSON Schema draft 2020-12)
- CREATE `rdm-discussion/scripts/validate-threads.mjs` (Node script)
- CREATE `rdm-discussion/scripts/tests/test_validate_threads.mjs`
- UPDATE `rdm-discussion/CLAUDE.md` (sección sobre schema enforcement)

**Schema mínimo** (basado en threads existentes 171-174):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["thread", "author", "date", "topic", "mode", "status"],
  "properties": {
    "thread": { "type": "integer", "minimum": 1 },
    "author": {
      "type": "string",
      "enum": ["WC", "WC-Platform", "WC-Impl", "CC", "CC-Bot", "CC-Data", "CC-Pago", "CC-Web", "Alex"]
    },
    "date": { "type": "string", "format": "date" },
    "topic": { "type": "string", "minLength": 5 },
    "mode": {
      "type": "string",
      "enum": ["brain", "brain quick", "brain deep", "brain ultra", "DoIt", "verify", "challenge response", "synthesis"]
    },
    "status": {
      "type": "string",
      "enum": ["draft", "open", "response", "halt", "closed", "abandoned", "open-for-alex-vote", "ready-for-cc-execution", "open-for-challenge"]
    },
    "related": { "type": "array", "items": { "type": "string" } },
    "deliverable": { "type": "string" }
  },
  "additionalProperties": true
}
```

**Lógica validate-threads.mjs**:
1. Walk `rdm-discussion/threads/*.md`
2. Parse frontmatter YAML (gray-matter o similar)
3. Validate vs schema
4. Mode SOFT (env `SCHEMA_MODE=soft`): warn + continue
5. Mode HARD (env `SCHEMA_MODE=hard`): fail con exit 1 si cualquier thread invalid
6. Output: tabla MD con violations + JSON estructurado

**GitHub Action**:
- Trigger: PR a main + push to main
- Step 1: checkout
- Step 2: setup node 22
- Step 3: install deps (`pnpm i -w gray-matter ajv ajv-formats`)
- Step 4: run validator
- Step 5: comment on PR si violations
- Inicialmente: SOFT por 7 días, después HARD (CHANGELOG note)

**Tests**:
1. Thread con frontmatter válido → exit 0
2. Thread sin `thread:` field → fail (HARD) o warn (SOFT)
3. Thread con `author: Bob` (not in enum) → fail
4. Thread con `date: not-a-date` → fail
5. Empty threads/ folder → exit 0
6. 100 threads (perf check) → exit < 5s

### T4 — Self-review checklist hook (auto-verificables only)

**Esfuerzo**: 2 días. **PR scope**: ~200 LoC.

**Files**:
- CREATE `rdm-bot/.github/workflows/self-review-checklist.yml`
- CREATE `rdm-bot/scripts/self-review-check.sh`
- CREATE `rdm-bot/scripts/tests/test_self_review.sh`
- UPDATE `rdm-bot/CLAUDE.md:107-125` (mark items auto-verified)

**Items auto-verificables del checklist CLAUDE.md**:
- ✅ `5. Secrets/PII/tokens en diff` → `git diff --cached | grep -iE 'token|secret|key|password|api[-_]?key' && fail`
- ✅ `6. PR body referencia "Closes thread/N"` → `gh pr view --json body | jq -r .body | grep -E 'Closes thread/\d+'`
- ✅ `7. Tests verdes local` → `pnpm test`
- ✅ `9. Shared territory declarado en thread si tocado` → cross-check files changed vs declared territory en thread linked

**Items NO auto-verificables** (quedan honor system):
- 1. "Leí el diff completo línea por línea" — no testeable
- 2. "Anti-pattern arriba evitado" — requiere LLM-as-judge (no disponible)
- 3. "Tests cubren casos edge" — requiere juicio
- 4. "PR body mobile-friendly" — requiere juicio
- 8. "Workstream territory respetado" — partial: si territory en CLAUDE.md, verificar paths

**GitHub Action**:
- Trigger: PR opened/synchronized
- Run `bash scripts/self-review-check.sh` con env vars del PR context
- Si fail → fail PR check + comment con detalle de qué item falló
- Bypass: label `self-review-bypass` agregado por Alex (no por CC) → skip

**Tests**:
1. PR con secret en diff → fail
2. PR sin "Closes thread/N" en body → fail
3. PR clean → pass
4. PR con territory violation → fail + report
5. PR con bypass label → skip + warning

### T5 — Cost limit hook integrado con ccusage

**Esfuerzo**: 2 días. **PR scope**: ~150 LoC. **Depende de T2.**

**Files**:
- CREATE `rdm-bot/scripts/cost-limit-check.sh`
- CREATE `rdm-bot/.claude/hooks/PostToolUse-cost-check.sh` (Claude Code hook si CC lo soporta)
- UPDATE `rdm-bot/CLAUDE.md` (sección Cost budgets — link al hook)

**Lógica**:
1. Hook se invoca cada N llamadas a herramientas (configurable, default 50)
2. Llama endpoint `/api/cost?days=1` (de T2)
3. Compara `daily_total_usd` vs `declared_budget` del thread current (parse de `estimated_llm_budget` en frontmatter)
4. Si actual > budget × 1.0 → warning en stderr + Telegram (low priority)
5. Si actual > budget × 1.5 → halt CC (echo a stderr + exit 1)
6. Si endpoint no responde (T2 broken) → no-op + warning, no bloquear

**Hook config**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/PostToolUse-cost-check.sh",
            "every_n_invocations": 50
          }
        ]
      }
    ]
  }
}
```

**Tests**:
1. Mock endpoint con cost < budget → exit 0
2. Mock endpoint con cost = budget × 1.2 → exit 0 + Telegram called (warn)
3. Mock endpoint con cost = budget × 1.6 → exit 1 (halt)
4. Endpoint timeout → exit 0 + stderr warning

## §5 Tests

Per task:
- T1: shell tests en `test_new_thread.sh`. Run en CI.
- T2: Vitest en `apps/worker-bot/src/cron/__tests__/`. Coverage cron + endpoint.
- T3: Node tests en `scripts/tests/test_validate_threads.mjs`. Run en CI.
- T4: shell tests en `scripts/tests/test_self_review.sh`. Run en CI.
- T5: shell tests en `scripts/tests/test_cost_limit.sh`. Run en CI.

**Smoke post-merge** (cada PR):
- T1: `bash scripts/new-thread.sh CC-Bot smoke-test-t1` → verify file created, push success
- T2: trigger cron manualmente, verify D1 insert
- T3: malformed thread PR → CI fails as expected
- T4: PR con secret → CI fails as expected
- T5: simulate cost spike, verify halt

**Self-review pre-PR** (obligatorio para cada PR):
- Aplica T4 manualmente antes de push
- Costo declarado en cada PR description: `estimated_llm_budget: $X` y `actual_llm_cost: $Y` (post-merge)

## §6 Definition of Done

### Per PR

- [ ] PR mergeable a main (no conflicts)
- [ ] CI verde (lint + tests + smoke)
- [ ] Smoke verde post-merge (30 min observación)
- [ ] PR body referencia `Closes thread/175` (este thread, single DoIt)
- [ ] PR body referencia task ID (T1/T2/T3/T4/T5)
- [ ] Cost real declarado en PR body
- [ ] Self-review checklist completed (todos los 9 items, no solo auto)
- [ ] Mobile-friendly PR description (lead with what + verify)

### Global DoIt

- [ ] 5 PRs mergeados sin reverts
- [ ] Thread response en `threads/{next}-cc-bot-doit-175-report.md` con:
  - Cost total real ($USD)
  - Tiempo total real (h)
  - Sorpresas / blockers
  - Lessons learned
  - Decisiones pendientes (si alguna)
- [ ] CLAUDE.md (bot + discussion) actualizado donde aplique
- [ ] No regression en smoke tests existentes (cada 10 min)
- [ ] No new halts pending al cerrar DoIt

## §7 Risks + mitigations

| Risk | Mitigation |
|---|---|
| T1: flock no disponible en algún entorno (Git Bash Windows) | Implementar fallback con lockfile + PID, documentar requirement |
| T1: race condition no eliminada con flock + push si dos workers en máquinas distintas | Retry loop con jitter 500-2000ms + max 3 attempts, exit 1 si todos fallan |
| T2: ccusage no funciona en CF Workers (es Node CLI) | Fallback A: invocar desde GitHub Action cron en lugar de CF cron. Fallback B: implementar minimal usage tracker vía Anthropic API headers |
| T2: Anthropic API usage endpoint puede no estar disponible | Confirmar con docs antes de implementar fallback |
| T3: Threads existentes (171-174) ya escritos pueden tener frontmatter no schema-compliant | Run validator en SOFT mode primero, identificar violations, fix en mismo PR antes de switch a HARD |
| T3: Algunos threads viejos (1-100) pueden no tener frontmatter consistente | Permitir grandfathering: solo aplicar schema a threads >= 175 |
| T4: false positives en territory check bloquean dev legítimo | Bypass label disponible, error messages claros |
| T4: secrets check fail por false positive (var nombrada `key` sin ser secret) | Allowlist de patterns falsos en config |
| T5: cost endpoint down rompe CC operativo | Hook con grace period: si endpoint no responde, log + continue |
| T5: hook ejecuta muy frecuente, slow down CC | `every_n_invocations: 50` configurable, default conservador |

## §8 Halt conditions

Para esta sesión CC. **Solo en estos casos halt + reporta**, todo lo demás se resuelve.

- Secret hardcoded encontrado durante desarrollo → para inmediato, no commit
- Operación destructiva fuera de spec → para + reporta
- >30 min stuck en MISMO problema sin progreso → para + reporta + propone unblock
- Cost LLM excede $75 (1.5× upper) → para + reporta
- Smoke test rojo post-merge atribuible a este DoIt → halt deploys + propone rollback (Alex aprueba)
- T1 falla en producir push atómico tras 5 iteraciones distintas → halt + reporta. Posiblemente flock approach no viable, escalate
- T2 ccusage no funciona ni en Workers ni en GitHub Action ni con Anthropic API → halt + propone alternativa

**NO halt por**:
- TypeScript errors → fix inline (max 3 iteraciones)
- Lint warnings → fix inline
- Tests rojos primer intento → fix + retry max 3
- Missing deps → install vía pnpm si en allowlist
- Cuando T5 todavía no existe (T1-T4 dependen de nada externo)

## §9 Out of scope para esta sesión CC

Si encuentras estos, abre issue + sigue. NO inline fix.

- F2 observability LIVE (foundations seal Accepted 2026-05-20, pero Q4 dice operativo primero)
- Charter v0 (WC-Platform responsability)
- ADR-002 multi-WC formalization (post test empírico)
- M1-M5 modules (post foundations LIVE)
- LLM-as-judge sobre PRs (post golden sets M5+F1)
- L2 WC-Impl reviewer setup (Q2 BI rules it out)
- Test empírico mental + artefactos (Alex + WC actual)
- META audit (CORRE en sesión paralela: thread/176)
- 7 decisiones pendientes STATE.md §G (Alex async)
- Cost analysis breve (WC, post T2 + 1 semana data)
- A5 thread/127 AirBnB scraping (out of scope este DoIt)
- Browserbase integration (post Q3 quarter)

## §10 Reporting al final

Crea `threads/{next-via-T1-script}-cc-bot-doit-175-report.md` con:

```yaml
---
thread: <N>
author: CC-Bot
date: <date>
topic: cc-bot-doit-175-completion-report
mode: DoIt
status: closed
related:
  - thread/175 (spec)
  - PR #X (T1)
  - PR #Y (T2)
  - PR #Z (T3)
  - PR #W (T4)
  - PR #V (T5)
deliverable: completion report del DoIt thread/175
---
```

Sections:
1. PRs mergeados (con #, link, LoC, cost real, tiempo)
2. Tests añadidos (count + coverage delta)
3. Sorpresas / blockers encontrados (con resolución)
4. Costo total real ($USD) — break down por task
5. Tiempo total real (h) — break down por task
6. Cosas out-of-scope encontradas (issues opened, no fix)
7. Recomendaciones para next session (sin ejecutar)
8. DoD checklist global verde/rojo

---

**Fin spec.** CC ejecuta. Halt rules estrictas. Reporta al final.

— WC, 2026-05-22, DoIt spec producido para sesión CC nueva.
