---
id: 215
author: wc
topic: session-log-2026-05-26-greeter-v7-pricing-eradication
status: shipped
mode: documentation
created_at: 2026-05-26
---

# thread/215 — Session Log 2026-05-26 (Greeter v7 + Pricing + Eradication + Hotfix)

## §0 · TL;DR

Sesión de 7+ horas. 4 PRs mergeados + deploy productivo + 2 bugs identificados (P1+P2) + 2 specs publicados + CC eval framework arrancado en paralelo + 1 hotfix wa.me link.

---

## §1 · LO QUE SE SHIPPED HOY

| # | Item | PR | Status |
|---|---|---|---|
| 1 | Make pricing scenarios reactivados (3 weeks paused) | — | ✅ LIVE |
| 2 | 26 cambios Beds24 aplicados (RdM/Morenas/Huerta) | — | ✅ Beds24 PATCH 200 |
| 3 | PR #187 Eradication 3 hallucinations (Iris/Chamán/pet) | #187 | ✅ Merged |
| 4 | PR #186 Greeter v7 deploy 100% canary | #186 | ✅ Merged + deployed |
| 5 | Migration 0048 bot_config_canary_v7 | (parte #186) | ✅ Applied remote |
| 6 | PR #188 WA link hotfix (727→527 prefix) | #188 | ✅ Merged + deployed (version 0bcb963d) |
| 7 | thread/213 M1 Pricing v0.5 spec (8-12h CC pending) | — | ✅ Published |
| 8 | thread/213b Eval Framework spec (6-9h CC running) | — | ✅ Published |
| 9 | WC memorias #3/#8/#15 deescalated | — | ✅ Done |

---

## §2 · DETALLE POR WORKSTREAM

### 2.1 · Make Pricing (mañana)

- `cron:beds24-token-refresh` (4704705) — reactivado, 2 runs success 13:46 MX
- `cron:pricing-daily` (4718358) — reactivado, 1 run success 13:46 MX (77s, 9 ops)
- Email recibido con 26 valid changes + 19 rejected (price<floor + no-op)
- `wh:pricing-approve` (4719127) — ejecutó 14:02 MX, Beds24 PATCH 200, 26 dates actualizadas
- Pricing model verificado: floor Morenas $3500 confirmado por Alex (no $4000)
- LLM hallucination detectada: "Huerta zero bookings" → falso, 6 confirmed + 3 cutover-cancelled
- **Status pricing**: pipeline LIVE, cada mañana 06:00 MX email review

### 2.2 · Eradication 3 hallucinations (PR #187)

3 reglas "duras" innecesarias removidas de config files:
- **Iris** ("Iris, la bebé y yo"): NO existía como regla en config (solo en system-prompt-v7.ts knowledge — fixed en PR #186)
- **Casa Chamán "NUNCA mencionar"**: removido de CLAUDE.md/STATE.md/BACKLOG.md de 3 repos
- **Pet fee "NUNCA /noche"**: removido (factual $300/estancia mantenido)

Files editados (5 config + 1 test):
- rdm-bot/CLAUDE.md
- rdm-bot/STATE.md §E
- rdm-bot/data/CLAUDE.md
- rdm-discussion/CLAUDE.md
- rdm-discussion/BACKLOG.md
- rdm-bot/apps/worker-bot/tests/pre-stay-templates.test.ts (comments only)

Memorias WC actualizadas: #3 (Casa Chamán), #8 (anti-patterns block), #15 (pet policy).

### 2.3 · Greeter v7 deploy (PR #186)

- 1757 LoC, 8 commits, 218 + 1146 = 1364 tests verde
- Migration 0048 applied D1 remote
- `canary_percent_v7=100` activado
- `wrangler deploy` version 0bcb963d → producción
- Smoke test WhatsApp confirmó `prompt_version=v7` operando
- Pre-merge CC fix de prompt para coherencia con PR #187 deescalation
- WC additional fix: v7-validator.ts `casa_chaman_mention` check removido (coherencia con deescalation)

### 2.4 · WA link hotfix (PR #188)

**Bug crítico descubierto en smoke test**:
- `wa.me/727441441575` ← INVÁLIDO (WhatsApp interpreta `7` como country code extranjero)
- Correcto: `wa.me/527441441575` (52 = México)

**Files afectados** (6 total, 12 instances):
- `process-tool-use.ts` (3 instances) — fix WC commit 1
- `system-prompt-v7.ts` (4 instances) — fix CC2 paralelo
- 4 test files (5 instances) — fix CC2 paralelo

**Root cause**: `karina-config.ts` declarado "single source of truth" pero NO IMPORTADO por estos files. Anti-pattern hardcoded duplication.

**Hotfix deployed**: version 0bcb963d, smoke test confirmó `wa.me/527441441575` en producción.

### 2.5 · Eval Framework (thread/213b, CC1 corriendo)

CC1 mega-run iniciado en paralelo al hotfix CC2:
- E1 Migration 0049 ✅ (183 LoC)
- E2 Eval engine ✅ (453 LoC)
- E3 Admin endpoints 🟡 en curso al cierre de sesión
- E4-E8 pendientes
- Falta ~3-4h CC autónomo

**Stack**: D1 `greeter_eval_cases` + `greeter_eval_runs` + 7 admin endpoints + Astro page `/admin/eval` + cron daily 04:00 MX + 30 synthetic cases.

**Default OFF al deploy**: `bot_config.eval_framework_enabled=false`.

---

## §3 · BUGS PENDIENTES (P1 + P2)

### P1 🔴 — Escalation agresiva del bot

**Reproducido en prod** (turns 20:52:19, 20:52:57):

| Turn | User | Bot |
|---|---|---|
| 1 | "Quiero hablar con alguien" | route + Karina WA |
| 2 | "Y tienes disponible en julio? Quiero fechas concretas.." | `bot_loop_exit` + re-paused 30 min |

**Diagnóstico**: handler-v7 + anti-loop lógica trata 2 turns con tema diferente como "loop". Lead pidiendo info concreta no es loop — es follow-up legítimo después de exit gracioso.

**Mitigación temporal**: WC unpaused `bot_paused_until=NULL` para subscriber `5215661027255`.

**Brain mode pendiente**: ajustar lógica para que `lead_exit_gracioso` NO compute como loop turn. Exit gracioso UNA VEZ, turn siguiente debería tratarse fresh.

### P2 🟡 — Contexto heredado entre conversaciones

**Reproducido en prod** (turn 20:25:54):
- User: "Hola"
- Bot: "¿Sigues buscando para 29 personas en septiembre?"

**Diagnóstico**: bucket-detector o conversation persistence está heredando "29 personas septiembre" de conversación anterior. Para test fresh esto suena raro/intrusivo.

**Brain mode pendiente**: ¿`last_intent` debería expirar después de N días? ¿Welcome fresh debería resetear context si gap > X horas?

---

## §4 · CC1 EVAL FRAMEWORK — STATUS AL CIERRE

Branch: `feat/greeter-eval-framework`

```
E1 ✅ migration 0049_greeter_eval.sql (183 LoC)
E2 ✅ eval-engine.ts (453 LoC, deterministic scoring + alerts)
E3 🟡 admin-eval.ts 7 endpoints (en curso al cierre)
E4 ⏳ /admin/eval Astro page
E5 ⏳ cron handler + wrangler.toml
E6 ✅ 30 synthetic cases (incluido en migration)
E7 ⏳ tests
E8 ⏳ telegram alerts + bot_config flag
```

Falta ~3-4h CC. Si CC1 sigue corriendo en tu sesión local, déjalo. Si se cortó/compactó, hay que retomarlo en nueva sesión CC.

---

## §5 · FILES TOCADOS

### rdm-bot
- CLAUDE.md, STATE.md (eradication PR #187)
- packages/agents/greeter/process-tool-use.ts (WA hotfix PR #188)
- packages/agents/greeter/system-prompt-v7.ts (CC v7 + WA hotfix)
- packages/agents/greeter/handler-v7.ts (new, v7)
- packages/agents/greeter/bucket-detector.ts (new, v7)
- apps/worker-bot/src/karina-config.ts (new, v7)
- apps/worker-bot/src/v7-validator.ts (new, v7)
- migrations/0048_bot_config_canary_v7.sql (new)
- 4 test files (assertions actualizados)

### rdm-discussion
- CLAUDE.md, BACKLOG.md (eradication PR #187)
- threads/213-wc-m1-pricing-v0.5-port-make-to-cf.md (new, spec)
- threads/213b-wc-greeter-eval-framework-shadow-testing.md (new, spec)
- threads/215 (this file)

### rdm-data (sin cambios — stub)
### rdm-platform (sin cambios)

---

## §6 · INSTRUCCIONES PARA SIGUIENTE WC

Sesión nueva debe arrancar con:

### Paso 0: Cargar contexto

Lee este thread/215 completo + memorias (27 entries con #3/#8/#15 updated 2026-05-26).

### Paso 1: Verificar estado producción

```sql
-- ¿v7 sigue procesando?
SELECT prompt_version, COUNT(*) FROM greeter_turns 
WHERE turn_at > datetime('now', '-1 hour') GROUP BY prompt_version;

-- ¿Alex sigue paused?
SELECT subscriber_id, bot_paused_until FROM conversations 
WHERE subscriber_id = '5215661027255';

-- ¿Algún loop en últimas 2h?
SELECT subscriber_id, COUNT(*), MAX(last_active) FROM conversations 
WHERE last_intent = 'bot_loop' AND last_active > strftime('%s', 'now') - 7200 
GROUP BY subscriber_id;
```

### Paso 2: Status CC1 eval framework

Preguntar a Alex: ¿CC1 todavía corriendo? ¿Terminó? Si terminó, ¿hay PR creado?

### Paso 3: Brain mode P1 (escalation agresiva)

Brain deep sobre cómo arreglar:
- Lead pide "hablar con humano" → exit gracioso (CORRECTO)
- Lead next turn pide info diferente → debe procesarse FRESH, no como loop

**Hipótesis fix**: en handler-v7 después de `lead_exit_gracioso`, resetear `last_intent` a NULL en lugar de `escalate`. O añadir excepción en anti-loop logic para que `lead_exit_gracioso` no cuente como turn de loop.

### Paso 4: Brain mode P2 (contexto heredado)

Brain deep sobre context persistence:
- ¿Cuánto tiempo persiste `last_intent`?
- ¿Qué pasa en conversaciones de prueba vs reales?
- ¿Welcome fresh debería resetear context si gap > 6h?

### Paso 5: Próximas prioridades en orden

| Prio | Item | Effort |
|---|---|---|
| P0 | Brain P1 escalation agresiva → spec → CC fix | 2-4h WC + 1h CC |
| P1 | Brain P2 contexto heredado → spec → CC fix | 1-2h WC + 30 min CC |
| P2 | Verificar PR de CC1 eval framework + merge | 30 min |
| P3 | Apply migration 0049 + activate eval framework | 15 min |
| P4 | Refactor karina-config.ts (force import everywhere) | 1h |
| P5 | CC mega-run thread/213 M1 Pricing port (después de v7 stable) | 8-12h |

---

## §7 · CONFIGURACIONES VIVAS

| Item | Valor |
|---|---|
| Worker-bot version | 0bcb963d (deployed 2026-05-26) |
| canary_percent_v5 | 100 |
| canary_percent_v6 | 100 |
| canary_percent_v7 | 100 ✅ NEW |
| Make scenarios pricing | active (cron:beds24-token-refresh, cron:pricing-daily, wh:pricing-approve, wh:pricing-reject) |
| Karina WA link en código | `wa.me/527441441575` ✅ |
| Karina WA link memoria #28 | `+52 744 144 1575` |

---

## §8 · LECCIONES DEL DÍA

1. **Single source of truth no funciona si no se importa**: karina-config.ts existía con valor correcto pero 4 files hardcodearon el wrong link. Refactor pendiente.

2. **Anti-loop muy agresivo en leads**: 2 turns de tema diferente NO es loop. Lógica necesita más context awareness.

3. **Memory eradication es source-first, no patch downstream**: Alex management override fue claro — quitar reglas de CLAUDE.md/STATE.md primero, después clean code.

4. **Multi-CC paralelo funciona** cuando files distintos: CC1 eval framework + CC2 hotfix corrieron sin colisión.

5. **Cache prompt Tier 1 puede crear false negatives en smoke tests**: hay que esperar 5-10 min post-deploy O usar fresh subscriber para test definitivo.

6. **D1 manual unpause funciona**: cuando bot se atora en loop, `UPDATE conversations SET bot_paused_until=NULL, last_intent=NULL` libera al subscriber.

---

— wc, 2026-05-26, sesión cierre 15:00 MX

EOF
