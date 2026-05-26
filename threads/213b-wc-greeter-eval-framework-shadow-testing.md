---
id: 213b
author: wc
topic: greeter-eval-framework-shadow-testing
status: draft
mode: brain_deep
priority: P1
target_repo: rdm-bot
target_branch: feat/greeter-eval-framework
model: sonnet-4-6
effort_estimate_h: 6-9
created_at: 2026-05-26
based_on: Alex management override 2026-05-26 + 848 v6 historic turns
---

# thread/213b — Greeter Eval Framework: Shadow Testing + Continuous Evolutionary Guardrail

## §0 · TL;DR para Alex (mobile-friendly)

| Item | Resumen |
|---|---|
| **Genealogía** | Tu propuesta directa: 848 conversaciones pasadas + casos curados WC + cada N turns producción re-run shadow contra v7. NO se manda al cliente, es para análisis |
| **Objetivo** | Evolutionary guardrail — detectar regression en v7 cuando WC actualiza prompt o CC modifica handler |
| **3 capas** | L1 Replay 848 turns, L2 Synthetic curated, L3 Continuous cron sample |
| **No es** | NO es A/B test, NO es canary, NO es production split. Solo shadow eval invisible al user |
| **Stack** | D1 `greeter_eval_runs` + 3 endpoints `/api/admin/eval/*` + page `/admin/eval` + cron daily sample |
| **Effort CC** | 6-9h |
| **Branch** | `feat/greeter-eval-framework` |
| **Default** | Off al deploy. Alex activa cuando v7 está stable en producción |

---

## §1 · CONTEXT

### 1.1 El problema

Greeter v7 va a producción 100% (post PR #186 + #187). Las únicas pruebas que tenemos son:

| Test | Tipo | Limitación |
|---|---|---|
| Golden tests (17 cases) | **Estáticos** — verifican el TEXTO del prompt contiene X frase | No verifican comportamiento del LLM con inputs reales |
| Unit tests bucket-detector | Mocked D1 | No verifican que el LLM actúa correctamente sobre el bucket |
| Validator tests | Regex | No verifican que el LLM produce salida que el validator aprueba en casos reales |
| Smoke test post-deploy | Health endpoint | Solo confirma que el servicio responde, no que responde BIEN |

**Gap crítico**: NO tenemos forma de detectar regression del LLM. Si mañana WC actualiza el prompt y empeora 30% de los casos, NO lo sabemos hasta que un guest se queja.

### 1.2 La propuesta de Alex

> *"Test=true en algún lado, esos no se mandan al cliente, son para tu análisis. Después como rutina cada 100 o x reales, evolutivo y guardrail en uno."*

Esto es **shadow testing** + **continuous evaluation**. Industry standard para LLM systems en producción.

### 1.3 Por qué importa para RdM

| Caso | Sin eval framework | Con eval framework |
|---|---|---|
| WC actualiza system prompt | Deploy → esperar quejas guests | Run replay 848 turns → diff vs baseline → decide deploy |
| CC modifica handler-v7.ts | Tests unit pass = OK | Run synthetic 30 casos curated → verify comportamiento |
| Bucket detector cambia | No safety net | Run replay → ver casos donde bucket cambió categoría |
| Cost LLM sube inesperado | Detectar cuando $$ ya pasó | Trend en eval runs históricos |
| Quality drift gradual | Invisible | Cron weekly random sample 50 turns → alert si delta |

### 1.4 Lo que ya existe (reusable)

| Asset | Path | Uso para eval |
|---|---|---|
| D1 `greeter_turns` table | rincon | 848 turns históricos = dataset replay |
| `system-prompt-v7.ts` | packages/agents/greeter | Prompt under test |
| `handler-v7.ts` | apps/worker-bot/src | Handler under test |
| Anthropic API client | packages/llm-client | Reusable para shadow calls |
| `/admin/bot-metrics` | apps/web | UI pattern para `/admin/eval` |
| Logpush job | CF | Audit trail si runs deployan |

### 1.5 Diferencias clave vs A/B testing tradicional

| Aspecto | A/B test | Shadow eval |
|---|---|---|
| User ve respuesta del experimento | SÍ (variants) | NO (siempre v7 prod-bound) |
| Compara métricas user behavior | SÍ | NO |
| Compara salida LLM directa | NO | SÍ |
| Detecta regression antes de deploy | NO | SÍ |
| Setup overhead | Alto (split traffic) | Bajo (shadow call paralelo) |
| Costo $$ | 2x LLM (cada variant) | 1x LLM + sample shadow |

---

## §2 · SCOPE — YES/NO explícito

### YES — Sí se hace

- ✅ D1 table nueva `greeter_eval_runs` con full snapshot input/output/diff/score
- ✅ D1 table nueva `greeter_eval_cases` con casos sintéticos curados WC
- ✅ Backfill inicial: WC carga 30 synthetic test cases via INSERT
- ✅ Endpoint `/api/admin/eval/run-replay` — re-corre v7 contra N turns históricos del greeter_turns table
- ✅ Endpoint `/api/admin/eval/run-synthetic` — corre v7 contra greeter_eval_cases
- ✅ Endpoint `/api/admin/eval/runs` — lista runs históricos paginados
- ✅ Endpoint `/api/admin/eval/runs/:id` — detail de un run con diff side-by-side
- ✅ Admin page `/admin/eval` (Astro + React) con:
  - Trigger replay (selector: 50/100/200/all 848)
  - Trigger synthetic (selector: all 30 / specific category)
  - Lista runs históricos con score, timestamp, cost
  - Detail view: input | v6 prod output | v7 shadow output | diff highlights | manual annotation textarea
- ✅ Cron `cron:eval-shadow-sample` daily 04:00 MX (mientras user duerme):
  - Sample 50 random turns de últimas 24h
  - Re-corre v7 shadow
  - Log diff a greeter_eval_runs con `source='cron_shadow'`
- ✅ Bot_config flag `eval_framework_enabled` (default `false`)
- ✅ Telegram alert si diff score < threshold (default <70%)
- ✅ Tests anti-regression (8 golden eval cases)

### NO — Fuera de scope

- ❌ A/B testing producción (es eval shadow, NO split traffic)
- ❌ Multi-model comparison (solo Sonnet 4.5 = el modelo prod actual)
- ❌ Continuous deployment hooks (Alex aprueba manual cada update)
- ❌ Auto-rollback si eval score baja (alert + manual decision)
- ❌ User-facing eval results (es Alex-only debugging tool)
- ❌ Casa Chamán filtering (no aplica, ya está filtered en bucket-detector)
- ❌ Pet fee enforcement validator (deescalated en PR #187)
- ❌ Versionado de prompts en D1 (mantener simple: prompt vive en código git)
- ❌ ML-based scoring (usar heurística simple: tool used + key fields match)
- ❌ Auto-merge a main

---

## §3 · DECISIONES CERRADAS

| # | Decisión | Voto |
|---|---|---|
| 1 | Stack: D1 + Cloudflare Worker, NO infra externa (Langfuse, etc) | GO |
| 2 | Modelo eval: SAME Sonnet 4.5 prod (no comparar contra otro modelo en v0.5) | GO |
| 3 | Scoring: deterministic (tool_used match + intent_slug match + opening_line_quality_score) | GO |
| 4 | NO LLM-as-judge en v0.5 (caro + meta-evaluación complica debugging) | GO |
| 5 | Replay storage: full input + output JSON en D1, NO compression v0.5 | GO |
| 6 | Synthetic cases: 30 inicial (WC arma) + Alex adds via UI | GO |
| 7 | Cron sample: 50 random turns daily 04:00 MX | GO |
| 8 | Telegram alert: score < 70% on any single eval batch | GO |
| 9 | Default OFF: `eval_framework_enabled=false` until Alex enable | GO |
| 10 | Cost budget: declared $5 per replay 848 turns (Sonnet pricing) | GO |
| 11 | Audit retention: 90 days en D1, después archivar a R2 | GO |
| 12 | Diff highlights: usar `diff` lib npm o jsdiff en frontend | GO |

---

## §4 · IMPLEMENTACIÓN

### 4.1 Sub-deliverables (8 items)

| # | Componente | Files | Effort |
|---|---|---|---|
| E1 | Migration D1 `greeter_eval_cases` + `greeter_eval_runs` | `apps/web/migrations/0049_greeter_eval.sql` | 30 min |
| E2 | Eval engine core | `apps/worker-bot/src/eval-engine.ts` | 1.5h |
| E3 | 3 endpoints `/api/admin/eval/*` worker-bot | `apps/worker-bot/src/admin-eval.ts` | 1h |
| E4 | Admin page `/admin/eval` Astro + React | `apps/web/src/pages/admin/eval.astro` + component | 1.5h |
| E5 | Cron `cron:eval-shadow-sample` daily | `apps/worker-bot/wrangler.toml` + handler | 30 min |
| E6 | 30 synthetic test cases backfill | `apps/worker-bot/src/eval-cases-synthetic.ts` + migration INSERT | 1h |
| E7 | Tests (8 anti-regression cases) | `apps/worker-bot/tests/eval-engine.test.ts` | 45 min |
| E8 | Telegram alert + bot_config flag | `apps/worker-bot/src/eval-alert.ts` | 30 min |
| **TOTAL** | | | **~7h** |

### 4.2 D1 Schema (E1)

```sql
-- migration 0049_greeter_eval.sql

-- Synthetic test cases curados por WC
CREATE TABLE greeter_eval_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL UNIQUE,            -- e.g. "synth_001_lead_bendicion"
  category TEXT NOT NULL,                  -- gratitud | distress | vip_in_stay | pet_policy | bucket_repeat | etc
  source TEXT NOT NULL,                    -- 'wc_curated' | 'production_replay' | 'manual_alex'
  
  -- Input snapshot
  user_message TEXT NOT NULL,
  bucket TEXT NOT NULL,                    -- VIP_in_stay / VIP_pre_stay / VIP_repeat / lead
  context_json TEXT NOT NULL,              -- PromptContextV7 snapshot
  
  -- Expected output (puede ser parcial)
  expected_tool TEXT,                      -- route_user_to_url / escalate_to_human / etc (null = any)
  expected_intent_slug TEXT,               -- 'inicio' / 'mascotas' / etc (null = any)
  expected_opening_line_contains TEXT,     -- substring que debe contener (puede ser null)
  expected_opening_line_excludes TEXT,     -- substring que NO debe contener (e.g. "Iris", "noche")
  
  -- Annotation
  notes TEXT,
  created_by TEXT DEFAULT 'wc',
  created_at TEXT NOT NULL,
  active INTEGER DEFAULT 1                 -- soft delete
);

CREATE INDEX idx_eval_cases_category ON greeter_eval_cases(category, active);

-- Eval runs (single execution de un case)
CREATE TABLE greeter_eval_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL,                  -- agrupa runs de una misma corrida (replay batch / cron sample / synthetic run)
  run_at TEXT NOT NULL,                    -- ISO timestamp
  source TEXT NOT NULL,                    -- 'replay_historic' | 'synthetic' | 'cron_shadow'
  
  -- Test case reference (puede ser null si es replay de greeter_turns)
  case_id TEXT,                            -- FK a greeter_eval_cases (si source='synthetic')
  turn_id TEXT,                            -- FK a greeter_turns (si source='replay_historic' o 'cron_shadow')
  
  -- Input snapshot (denormalized para auditability)
  user_message TEXT NOT NULL,
  bucket TEXT NOT NULL,
  prompt_version TEXT NOT NULL,            -- 'v7' (default actual)
  
  -- Actual output (lo que el LLM produjo en shadow)
  actual_tool TEXT,
  actual_intent_slug TEXT,
  actual_opening_line TEXT,
  actual_full_response_json TEXT,          -- raw response del LLM
  
  -- Production output (lo que se envió al user en prod, solo para replay/cron sources)
  prod_tool TEXT,                          -- null si source='synthetic'
  prod_intent_slug TEXT,
  prod_opening_line TEXT,
  prod_full_response_json TEXT,
  
  -- Score (deterministic heuristic)
  score REAL,                              -- 0.0 to 1.0
  score_breakdown_json TEXT,               -- {tool_match: 1.0, intent_match: 1.0, opening_quality: 0.8}
  passed INTEGER,                          -- 1 if score >= threshold, 0 otherwise
  threshold REAL DEFAULT 0.70,
  
  -- Cost + perf
  llm_tokens_input INTEGER,
  llm_tokens_output INTEGER,
  llm_cost_usd REAL,
  llm_duration_ms INTEGER,
  
  -- Annotations
  alex_annotation TEXT,                    -- Alex puede agregar notas via UI
  flagged INTEGER DEFAULT 0                -- Alex marca como needs-attention
);

CREATE INDEX idx_eval_runs_batch ON greeter_eval_runs(batch_id, run_at);
CREATE INDEX idx_eval_runs_source ON greeter_eval_runs(source, run_at DESC);
CREATE INDEX idx_eval_runs_passed ON greeter_eval_runs(passed, run_at DESC);
CREATE INDEX idx_eval_runs_case ON greeter_eval_runs(case_id);
CREATE INDEX idx_eval_runs_flagged ON greeter_eval_runs(flagged, run_at DESC) WHERE flagged = 1;

-- bot_config flag
INSERT INTO bot_config(key, value, updated_at, updated_by) VALUES
  ('eval_framework_enabled', 'false', datetime('now'), 'thread/213b')
ON CONFLICT(key) DO NOTHING;
```

### 4.3 Eval engine (E2)

```typescript
// apps/worker-bot/src/eval-engine.ts

export interface EvalCase {
  case_id: string;
  category: string;
  user_message: string;
  bucket: BucketV7;
  context_json: string;
  expected_tool?: string;
  expected_intent_slug?: string;
  expected_opening_line_contains?: string;
  expected_opening_line_excludes?: string;
}

export interface EvalScore {
  total: number;            // 0.0 to 1.0
  tool_match: number;       // 1.0 if matches, 0.0 if not
  intent_match: number;
  opening_quality: number;  // 1.0 if contains expected + excludes excluded
}

export async function runEval(
  testCase: EvalCase,
  env: WorkerEnv,
): Promise<EvalRunResult> {
  // 1. Build PromptContextV7 from testCase
  const ctx = JSON.parse(testCase.context_json) as PromptContextV7;
  
  // 2. Build system blocks
  const blocks = buildSystemPromptBlocksV7(ctx);
  
  // 3. Call LLM (shadow — no Manychat, no user-facing)
  const startTime = Date.now();
  const response = await callAnthropic(env, {
    model: 'claude-sonnet-4-5',
    system: blocks,
    messages: [{ role: 'user', content: testCase.user_message }],
    max_tokens: 800,
  });
  const duration = Date.now() - startTime;
  
  // 4. Parse tool_use from response
  const toolUse = parseToolUse(response);
  
  // 5. Score
  const score = scoreEval(testCase, toolUse);
  
  return {
    case_id: testCase.case_id,
    actual_tool: toolUse?.name ?? null,
    actual_intent_slug: toolUse?.input?.intent_slug ?? null,
    actual_opening_line: toolUse?.input?.opening_line ?? null,
    actual_full_response_json: JSON.stringify(response),
    score,
    llm_tokens_input: response.usage?.input_tokens,
    llm_tokens_output: response.usage?.output_tokens,
    llm_cost_usd: estimateCost(response.usage, 'claude-sonnet-4-5'),
    llm_duration_ms: duration,
  };
}

function scoreEval(testCase: EvalCase, toolUse: ToolUse | null): EvalScore {
  const tool_match = (!testCase.expected_tool || toolUse?.name === testCase.expected_tool) ? 1.0 : 0.0;
  const intent_match = (!testCase.expected_intent_slug || toolUse?.input?.intent_slug === testCase.expected_intent_slug) ? 1.0 : 0.0;
  
  let opening_quality = 1.0;
  const opening = toolUse?.input?.opening_line ?? '';
  if (testCase.expected_opening_line_contains && !opening.toLowerCase().includes(testCase.expected_opening_line_contains.toLowerCase())) {
    opening_quality -= 0.5;
  }
  if (testCase.expected_opening_line_excludes && opening.toLowerCase().includes(testCase.expected_opening_line_excludes.toLowerCase())) {
    opening_quality -= 0.5;
  }
  opening_quality = Math.max(0, opening_quality);
  
  const total = (tool_match + intent_match + opening_quality) / 3;
  return { total, tool_match, intent_match, opening_quality };
}

export async function runReplay(
  env: WorkerEnv,
  count: number,
): Promise<BatchResult> {
  // 1. Sample N turns from greeter_turns table (random or recent)
  // 2. Foreach turn, reconstruct PromptContextV7
  // 3. Call runEval with the historic context + user_message
  // 4. Save each result to greeter_eval_runs with source='replay_historic'
  // 5. Return batch summary
}

export async function runSynthetic(env: WorkerEnv, category?: string): Promise<BatchResult> {
  // 1. SELECT * FROM greeter_eval_cases WHERE active=1 [AND category=?]
  // 2. Foreach case, call runEval
  // 3. Save with source='synthetic'
}
```

### 4.4 Admin endpoints (E3)

```typescript
// apps/worker-bot/src/admin-eval.ts

// POST /api/admin/eval/run-replay
// Body: { count: number, source?: 'random' | 'recent' }
// Triggers replay, returns batch_id immediately (async execution via waitUntil)

// POST /api/admin/eval/run-synthetic
// Body: { category?: string }
// Same pattern

// GET /api/admin/eval/runs?source=&limit=50&offset=0
// Returns paginated runs

// GET /api/admin/eval/runs/:id
// Returns full detail of single run with diff

// POST /api/admin/eval/runs/:id/annotate
// Body: { alex_annotation: string, flagged: boolean }

// GET /api/admin/eval/cases
// Returns synthetic test cases

// POST /api/admin/eval/cases
// Body: { case_id, category, user_message, bucket, expected_*, notes }
// Alex adds new synthetic case via UI

// All endpoints x-admin-secret protected
```

### 4.5 Admin page `/admin/eval` (E4)

```
┌─────────────────────────────────────────────────────────────────────┐
│ /admin/eval                                                         │
├─────────────────────────────────────────────────────────────────────┤
│ Eval Framework Status: ⚠️ DISABLED                                  │
│ [Enable]  [Disable]  bot_config.eval_framework_enabled              │
│                                                                     │
│ ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐    │
│ │ Replay Historic │  │ Synthetic Cases  │  │ Cron Schedule   │    │
│ │ [Run 50] [100]  │  │ 30 cases active  │  │ Daily 04:00 MX  │    │
│ │ [200] [All 848] │  │ [Run All]        │  │ Sample 50       │    │
│ └─────────────────┘  └──────────────────┘  └─────────────────┘    │
│                                                                     │
│ Recent Runs (last 10 batches):                                      │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 2026-05-26 14:30 | replay_historic | 100 | score 0.87 ✅    │   │
│ │ 2026-05-26 13:00 | synthetic       |  30 | score 0.93 ✅    │   │
│ │ 2026-05-25 04:00 | cron_shadow     |  50 | score 0.71 ⚠️    │   │
│ │ 2026-05-24 04:00 | cron_shadow     |  50 | score 0.85 ✅    │   │
│ └─────────────────────────────────────────────────────────────┘   │
│ [View Run Details]                                                  │
│                                                                     │
│ Flagged Runs (Alex needs attention):                                │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 2026-05-25 04:00 | turn 7821 | score 0.42 🔴                │   │
│ │   "Aceptan mascotas?" → v7 added /noche by mistake          │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ Cost summary (last 7d):                                             │
│ - Total eval cost: $2.45 USD                                        │
│ - Total runs: 350                                                   │
│ - Avg cost per run: $0.007                                          │
└─────────────────────────────────────────────────────────────────────┘
```

Run Detail view:
```
┌─────────────────────────────────────────────────────────────────────┐
│ Run #4521 — 2026-05-26 14:30 — score 0.42 🔴                        │
├─────────────────────────────────────────────────────────────────────┤
│ Source: cron_shadow                                                 │
│ Turn ID: greeter_turns.id=7821                                      │
│ User message: "Cuanto cuesta llevar mi perro?"                      │
│ Bucket: lead                                                        │
│                                                                     │
│ ┌──────────────────────────┬──────────────────────────┐           │
│ │ Production (v7 actual)   │ Shadow (v7 same)         │           │
│ ├──────────────────────────┼──────────────────────────┤           │
│ │ tool: route_user_to_url  │ tool: route_user_to_url  │ ✅        │
│ │ intent: mascotas         │ intent: mascotas         │ ✅        │
│ │ opening:                 │ opening:                 │           │
│ │ "$300 MXN por mascota    │ "$300 por noche por      │ 🔴        │
│ │ por estancia, hasta 2"   │ mascota, hasta 2"        │           │
│ └──────────────────────────┴──────────────────────────┘           │
│                                                                     │
│ Score breakdown:                                                    │
│ - tool_match: 1.0                                                   │
│ - intent_match: 1.0                                                 │
│ - opening_quality: 0.0 (contains "/noche" — excluded)               │
│ - total: 0.67 → BUT category 'pet_policy' has lower threshold      │
│                                                                     │
│ Alex annotation:                                                    │
│ [text area]                                                         │
│ [Mark flagged] [Unflag]                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.6 Synthetic test cases (E6) — 30 inicial WC-curated

Categorías:

| Categoría | N cases | Example user_messages |
|---|---|---|
| gratitud_bendicion | 4 | "Bendito sea Dios", "Gracias por todo", "Que Dios los bendiga" |
| distress_911 | 3 | "Necesito ayuda urgente", "Tengo una emergencia", "Estoy en crisis" |
| vip_in_stay_problem | 3 | "No hay agua caliente", "Aire no enfría", "Necesito a Karina ya" |
| vip_pre_stay_change | 3 | "Cambio fechas", "Llevamos mascota extra", "Late checkout posible?" |
| vip_repeat_greeting | 3 | "Hola, estuvimos hace 3 meses", "De nuevo nosotros!", "El chef Mary still ahí?" |
| pet_policy | 4 | "Aceptan perros?", "Mascota grande es problema?", "Cuanto por gato?", "2 perritos y 1 gato OK?" |
| group_size_recommendation | 3 | "Para 15 personas", "Boda 40 invitados", "Familia 8 niños" |
| availability_specific_dates | 3 | "Junio 15-20 disponible?", "Diciembre 28-31 RdM?", "Año nuevo precio?" |
| follow_up_short | 2 | "ok gracias", "perfecto" |
| loop_lead_human | 2 | (2 turns simulados): "Hablar con alguien" → "Quiero a Karina ya" |

Cada caso tiene `expected_opening_line_excludes` con palabras-trampa de hallucinations:
- "Iris" — NEVER en opening
- "/noche" — NEVER en pet_policy opening (excepto cuando user pregunta "cuanto por noche" — entonces OK acknowledge)
- "NUNCA" — NEVER (es signo de overengineering)

### 4.7 Cron daily sample (E5)

```toml
# apps/worker-bot/wrangler.toml — añadir:

[triggers]
crons = [
  # ... existing crons (if any) ...
  "0 10 * * *"  # 04:00 MX (UTC-6) = 10:00 UTC. Daily eval shadow sample.
]
```

Handler:
```typescript
// apps/worker-bot/src/cron-eval-shadow.ts

export async function runDailyShadowSample(env: WorkerEnv) {
  // 1. Check flag eval_framework_enabled
  const enabled = await getBotConfig(env, 'eval_framework_enabled');
  if (enabled !== 'true') return;
  
  // 2. SELECT 50 random turns from last 24h
  const turns = await env.DB.prepare(`
    SELECT id, subscriber_id, user_message, ... 
    FROM greeter_turns 
    WHERE turn_at > datetime('now', '-1 day')
      AND prompt_version = 'v7'
    ORDER BY RANDOM()
    LIMIT 50
  `).all();
  
  // 3. Run eval shadow for each
  const batch_id = `cron_${Date.now()}`;
  const results = [];
  for (const turn of turns.results) {
    const result = await runEval(turn, env);
    await saveEvalRun(env, { batch_id, source: 'cron_shadow', ...result });
    results.push(result);
  }
  
  // 4. Compute batch score
  const avgScore = results.reduce((s, r) => s + r.score.total, 0) / results.length;
  
  // 5. Alert if below threshold
  if (avgScore < 0.70) {
    await sendTelegramAlert(env, {
      message: `🔴 Eval batch ${batch_id} score ${avgScore.toFixed(2)} below threshold. ${results.filter(r => !r.passed).length}/${results.length} failed. Review: ${WORKER_BASE_URL}/admin/eval`
    });
  }
}
```

### 4.8 Telegram alert (E8)

Reuse existing `TG_BOT_TOKEN` + `TG_CHAT_ID_PAGOS` (per memoria #28).
Alert solo si:
- Cron daily score < 70%
- Manual replay/synthetic batch score < 50%
- Single high-stake case (distress_911, vip_in_stay_problem) falla 2+ veces seguidas

---

## §5 · TESTS (E7)

### 5.1 Anti-regression eval tests (8 cases)

```typescript
// apps/worker-bot/tests/eval-engine.test.ts

describe('scoreEval', () => {
  it('tool_match=1.0 when expected matches actual', () => {...});
  it('tool_match=0.0 when mismatch', () => {...});
  it('opening_quality drops to 0 when excluded substring present', () => {...});
  it('opening_quality stays 1.0 when no expectations', () => {...});
  it('null expectations means any actual passes', () => {...});
  it('handles tool=null (LLM failed parse)', () => {...});
  it('computes total = avg of 3 sub-scores', () => {...});
});

describe('runEval integration', () => {
  it('replay turn 7821 (pet policy) — should NOT contain "/noche"', () => {
    // Real historic turn replay shadow
  });
});
```

---

## §6 · DEFINITION OF DONE

| # | Check | Cómo verificar |
|---|---|---|
| DoD-1 | Branch `feat/greeter-eval-framework` existe | git branch |
| DoD-2 | Migration 0049 aplicada local | wrangler d1 query |
| DoD-3 | 30 synthetic cases insertados | `SELECT COUNT(*) FROM greeter_eval_cases` = 30 |
| DoD-4 | 8 tests pasan | pnpm test |
| DoD-5 | `/admin/eval` carga en browser | smoke test |
| DoD-6 | POST /api/admin/eval/run-synthetic returns batch_id | curl test |
| DoD-7 | Cron entry en wrangler.toml | grep |
| DoD-8 | bot_config flag default false | D1 query |
| DoD-9 | PR creada con descripción linkeando thread/213b | gh pr list |
| DoD-10 | NO autodeploy a prod | confirma branch local |

---

## §7 · RIESGOS + MITIGATIONS

| # | Riesgo | Prob | Mitigation |
|---|---|---|---|
| R1 | Cron sample 50 daily × 30 días = 1500 LLM calls/mes = $$$ | Media | Estimar costo real: Sonnet $3/1M input tokens × 5K avg = $0.015/call × 50 = $0.75/day × 30 = $22.50/mes. OK. Tier opcional 25 sample si quieres reducir |
| R2 | Replay 848 turns en single batch tarda 60+ min | Alta | Async waitUntil + chunked processing 50 at a time + batch_id status tracking |
| R3 | Score 70% threshold muy strict / muy lenient | Media | Default 70%, Alex puede ajustar via bot_config `eval_score_threshold` |
| R4 | False positives en score (LLM correctly used different intent_slug) | Media | Permitir `expected_intent_slug=null` (any). Alex flag manual. |
| R5 | Telegram spam si cron sample alerta cada día | Media | Cooldown 6h entre alerts del mismo type |
| R6 | Eval framework rompe en deploy y bloquea producción | Baja | Default off + graceful degradation (catch errors, no throw) |
| R7 | D1 storage explota con eval_runs cantidad | Baja | Migration cleanup mensual: rows > 90 days → archive R2 |

---

## §8 · APPENDIX A — 5 ejemplos synthetic cases concretos

```typescript
// apps/worker-bot/src/eval-cases-synthetic.ts (excerpt)

export const SYNTHETIC_CASES_V1 = [
  {
    case_id: 'synth_001_lead_bendicion',
    category: 'gratitud_bendicion',
    user_message: 'Bendito sea Dios, deseo lo mejor a tu nueva familia',
    bucket: 'lead' as const,
    context_json: JSON.stringify({
      today: '2026-05-26',
      lang: 'es',
      turn_count: 1,
      subscriber_id: 'synth_001',
      bucket: 'lead',
      is_off_hours: false,
      saludo_template_index: 0,
    }),
    expected_tool: 'route_user_to_url',
    expected_intent_slug: 'inicio',
    expected_opening_line_contains: 'bendiciones',
    expected_opening_line_excludes: 'Iris',
    notes: 'Test que opening NO menciona referencia personal "Iris" (eradication PR #187)',
  },
  {
    case_id: 'synth_002_lead_pet_basic',
    category: 'pet_policy',
    user_message: 'Aceptan mascotas?',
    bucket: 'lead' as const,
    context_json: JSON.stringify({...}),
    expected_tool: 'route_user_to_url',
    expected_intent_slug: 'mascotas',
    expected_opening_line_contains: '300',
    expected_opening_line_excludes: '/noche',
    notes: 'Pet fee debe decir cantidad pero NO usar "/noche" (deescalation PR #187)',
  },
  {
    case_id: 'synth_003_vip_in_stay_water',
    category: 'vip_in_stay_problem',
    user_message: 'No hay agua caliente',
    bucket: 'VIP_in_stay' as const,
    context_json: JSON.stringify({
      ...,
      bucket: 'VIP_in_stay',
      guest_name: 'María',
      active_booking: { arrival: '2026-05-25', departure: '2026-05-28', days_to_arrival: -1, property: 'RdM' },
    }),
    expected_tool: 'escalate_to_human',
    expected_intent_slug: null,
    expected_opening_line_contains: '744 144 1575',
    notes: 'VIP_in_stay con problema operacional debe ESCALATE con Karina cel',
  },
  {
    case_id: 'synth_004_lead_distress_911',
    category: 'distress_911',
    user_message: 'Necesito ayuda urgente, estoy en crisis',
    bucket: 'lead' as const,
    context_json: JSON.stringify({...}),
    expected_tool: 'escalate_to_human',
    expected_intent_slug: null,
    expected_opening_line_contains: '911',
    notes: 'Lead with real distress → 911 reply, NOT Karina',
  },
  {
    case_id: 'synth_005_vip_repeat_welcome',
    category: 'vip_repeat_greeting',
    user_message: 'Hola, estuvimos en su casa el año pasado',
    bucket: 'VIP_repeat' as const,
    context_json: JSON.stringify({
      ...,
      bucket: 'VIP_repeat',
      guest_name: 'Carlos',
      total_bookings: 2,
      last_stay: { departure: '2025-05-15', property: 'Las Morenas' },
    }),
    expected_tool: 'route_user_to_url',
    expected_intent_slug: 'disponibilidad',
    expected_opening_line_contains: 'Carlos',
    notes: 'VIP_repeat saludo debe usar nombre y reconocer estancia previa',
  },
  // ... 25 more cases
];
```

---

## §9 · APPENDIX B — Comando CC para mega-run

```
Modo: DoIt
Spec: rdm-discussion/threads/213b-wc-greeter-eval-framework-shadow-testing.md
Branch: feat/greeter-eval-framework (rdm-bot)
Modelo: claude-sonnet-4-6
Effort estimate: 6-9h

Pre-flight:
1. cd c:/dev/rdm/dev/bot
2. git fetch origin && git checkout main && git pull --rebase
3. git checkout -b feat/greeter-eval-framework
4. pnpm install
5. Lee thread/213b completo

Ejecuta E1→E8 en orden:
- E1: migration 0049 (30 min)
- E2: eval-engine.ts (1.5h)
- E3: admin-eval.ts endpoints (1h)
- E4: /admin/eval page + React (1.5h)
- E5: cron handler + wrangler.toml (30 min)
- E6: 30 synthetic cases (1h)
- E7: tests (45 min)
- E8: telegram alert + flag (30 min)

Defaults:
- ASCII shell args, UTF-8 file contents
- Conventional Commits
- NO ALTER TABLE existing tables (solo CREATE TABLE nuevas)
- NO auto-merge a main
- bot_config eval_framework_enabled=false al deploy (Alex enables manual)

Si stuck >30 min: HALT, commit progress, escribe report en threads/214.

Anti-patterns críticos:
- NO uses LLM para scoring (es deterministic v0.5)
- NO compares contra v6 (v6 ya está dead post canary=100 v7)
- NO uses Make.com (todo CF nativo)
- 30 synthetic cases deben TODOS tener expected_opening_line_excludes con palabras-trampa relevantes
- Cron schedule debe ser 04:00 MX (UTC 10:00), NO 04:00 UTC
- Cost budget declarado: $3 USD por replay 848 turns (Sonnet)

Al final:
1. pnpm test && pnpm lint pasan
2. git push origin feat/greeter-eval-framework
3. gh pr create con descripción linkeando thread/213b
4. Crea thread/214-cc-bot-doit-213b-eval-framework-report.md
5. NO mergees PR. Alex revisa.
```

---

## §10 · FIN DEL SPEC

Ready for CC mega-run **después que Greeter v7 (PR #186) sea merged + deployed**.

Lecciones del eval framework v0.5:
- ✅ Stack CF-native, no infra externa
- ✅ Tu insight central: shadow testing como evolutionary guardrail
- ✅ Default OFF (no rompe nada al deploy)
- ✅ 30 synthetic cases incluyen TODOS los anti-patterns deescalados PR #187
- ✅ Cron daily sample para drift detection continuo

— wc, 2026-05-26
