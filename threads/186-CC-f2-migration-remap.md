---
thread: 186
author: CC
date: 2026-05-23
topic: f2-migration-remap
mode: brain
status: open-for-alex-vote
related: [148, 175, 178, 184]
note_status: spec/184 §3 nombra "draft-pending-alex-vote"; schema enum no lo incluye, uso "open-for-alex-vote" (semánticamente idéntico, schema-valid pre HARD cutover 2026-05-29)
deliverable: F2 spec amendment proposal (rdm-platform/foundations/F2-observability.md)
---

# Thread/186 — F2 Spec Refactor: Migration Remap

**From**: worktree B (CC-Discussion specs drafter, Opus 4.7)
**Spec parent**: thread/184 §3 task B1
**Authority**: WC preliminary recommendation. Alex final vote required.
**Action by WC-Platform after vote**: apply patch to `rdm-platform/foundations/F2-observability.md` (CC read-only on rdm-platform per thread/184 §6).

---

## §1. Contexto

F2 spec (`rdm-platform/foundations/F2-observability.md`, Accepted 2026-05-20 via ADR-002) reserva **migration 0042** para tabla `cron_heartbeats`. Reality check al 2026-05-23:

| Slot | Reality | Origen |
|---|---|---|
| 0042 | `feedback_system` | thread/161 (shipped) |
| 0043 | `booking_captures` | shipped |
| 0044 | `outreach_templates` | shipped |
| 0045 | `mp_payments` | shipped |
| 0046 | `cost_telemetry` | thread/175 T2 (shipped) |
| 0047 | **LIBRE** | — |

F2 no puede shippearse con el spec actual: el número 0042 ya está consumido por otra feature.

**Hallazgo bonus durante el audit**: ya existe implementación funcional de cron heartbeats en producción usando `bot_config` D1 table con keys `cron_heartbeat:<name>` (ver `apps/worker-bot/src/cron-bot-alerts.ts:160-184` + `apps/web/src/lib/admin-health.ts:273`). Esto cambia el alcance del remap más allá de "renumerar".

---

## §2. Scope del refactor

### YES — incluido en este remap

1. Cambiar referencia `0042_cron_heartbeats.sql` → slot libre (recomendado **0047**) en F2 §3.3 + §6 Day 1 + §4 acceptance criterion #5
2. Decidir si la tabla `cron_heartbeats` dedicada sigue siendo necesaria dado el patrón `bot_config` existente
3. Actualizar paths esperados (`packages/shared/src/cron-heartbeat.ts`) verificando que aún no existe (verified: helper TS no existe; lógica vive inline en `worker-bot`)
4. Verificar que claims paralelas (metrics.ts, alerts.ts, helpers paths) siguen vigentes

### NO — fuera de este refactor

- F2 ship (requiere Q3.1 G7 voto Alex thread/148)
- Migrar el código existente de `bot_config` a `cron_heartbeats` (decisión separada — depende de §3 opción C)
- Cambios a F1 o F3 (B4/B5 hacen reservation, no ship)
- Modificación directa al archivo `rdm-platform/foundations/F2-observability.md` (CC read-only ahí)

---

## §3. Decisión central: ¿tabla dedicada o reusar bot_config?

Tres opciones, voto WC preliminar al final.

### Opción A — Mantener spec original: tabla dedicada `cron_heartbeats` en 0047

Cambio mínimo. F2 §3.3 conserva su diseño tal cual; sólo se renumera 0042 → 0047.

**Pros**:
- Spec ya votado en ADR-002 + thread/148 §A — minimal re-litigation
- Schema explícito (`last_ok_at INTEGER`, `consecutive_failures`, `expected_interval_sec`) habilita queries time-series sin string parsing
- F2 acceptance criterion #5 ("recordCronHeartbeat wired to ALL existing crons") implica refactor del código actual de todos modos
- Boundary clean: `bot_config` para flags/config, `cron_heartbeats` para señales operacionales

**Contras**:
- Doble write durante migración (código actual usa bot_config; F1 ship día 2 esperaría tabla nueva)
- ~30 LoC migración + ~50 LoC refactor del cron-bot-alerts.ts existente
- Posible perder histórico (bot_config rows tendrían que copiarse)

### Opción B — Reusar `bot_config`, eliminar migración del spec

Reconocer que el patrón existente funciona. F2 §3.3 se reescribe para apuntar a `bot_config`. NO migration nueva.

**Pros**:
- Cero migración → desbloquea F2 Day 1 sin schema change
- Código ya en prod; testeado por staleness check (cron-bot-alerts.ts)
- Patrón KV-style sencillo; bajo riesgo regresión

**Contras**:
- Pierde columnas estructuradas (`consecutive_failures`, `last_error_msg`, `expected_interval_sec`)
- Query SQL en F2 §3.3 ("SELECT cron_name, lateness_ratio ...") requiere reescritura — el `expected_interval_sec` tendría que vivir en código (hardcoded `PER_CRON_THRESHOLD_SEC` ya existe en `cron-bot-alerts.ts`)
- Boundary murky: `bot_config` mezcla flags + heartbeats + posibles futuros valores
- Re-litiga decisión §3.3 del spec ya Accepted (ADR-002)

### Opción C — Tabla dedicada 0047 + migración soft del bot_config existente

Opción A + path explícito de migración: al implementar F2, el helper `recordCronHeartbeat()` escribe a la tabla nueva Y al `bot_config` legacy durante N días. Tras soak, eliminar el bot_config legacy en migration 0048 o similar.

**Pros**:
- Path no-breaking: dashboard antiguo y nuevo coexisten durante transición
- Auditable: comparar dos fuentes durante soak detecta drift
- Mantiene estructura del spec (ADR-002 sealed)

**Contras**:
- Más LoC durante transición (~50 LoC dual-write)
- 2 migraciones en lugar de 1 (0047 add + 0048 cleanup post-soak)
- Más superficie de bug durante ventana de transición

---

## §4. Voto WC preliminar

**Recomendación: Opción A** (slot 0047, tabla dedicada, no dual-write).

*WC preliminary, Alex final.*

Razón:
- ADR-002 ya selló el diseño con tabla dedicada (thread/148 §A #9). Cambiarlo es re-litigación que cuesta más que el refactor de ~50 LoC del cron-bot-alerts.ts.
- F2 acceptance #5 obliga a refactor de todos los call sites de cron heartbeat de todos modos (5 worker-pago crons + GH Actions). Mover de `bot_config` a `cron_heartbeats` es change-of-storage incluido en ese trabajo, no extra.
- El histórico de `bot_config` rows no tiene valor operacional retrospectivo: la métrica es "¿corrió hace <15 min?", consumida en tiempo real. Wipe limpio aceptable.
- Opción C añade complejidad (dual-write) que evita un riesgo (rollback durante soak) que ya está mitigado por F2 §6 Rollback ("emitMetric calls are no-op").

Si Alex prefiere B (reusar `bot_config`): el spec necesita re-litigation de §3.3 + actualizar §4 acceptance #5 + actualizar §6 Day 1 (no migration step). ~2h WC-Platform brain.

---

## §5. Cambios concretos al spec F2

Patch a aplicar por WC-Platform en `rdm-platform/foundations/F2-observability.md`:

| Sección | Línea aprox | Cambio |
|---|---|---|
| §1 "What F2 adds" | 48 | `migration 0042` → `migration 0047` |
| §3.3 título | 129 | `(NEW 2026-05-20)` → `(NEW 2026-05-20, slot remapped 2026-05-23 per thread/186)` |
| §3.3 código SQL | 134 | `migrations/0042_cron_heartbeats.sql` → `migrations/0047_cron_heartbeats.sql` |
| §3.3 nota nueva | post-181 | Add: "Note: an in-flight pattern stores heartbeats in `bot_config` table with keys `cron_heartbeat:<name>` (see `apps/worker-bot/src/cron-bot-alerts.ts`). F2 implementation MUST migrate those call sites to the new table and remove the legacy bot_config rows in the same PR." |
| §4 acceptance #5 | 264 | `migrated (0042)` → `migrated (0047)` |
| §6 Day 1 | 312 | `Schema migration: cron_heartbeats table (0042)` → `Schema migration: cron_heartbeats table (0047). Refactor existing bot_config heartbeats in apps/worker-bot/src/cron-bot-alerts.ts to use new table.` |

---

## §6. Verificación de claims paralelas del spec F2

Otras paths reservadas por F2 que verifiqué hoy (2026-05-23):

| Path en spec | Estado filesystem | Riesgo colisión |
|---|---|---|
| `packages/shared/src/metrics.ts` | NO EXISTE | Libre |
| `packages/shared/src/alerts.ts` | NO EXISTE | Libre |
| `packages/shared/src/cron-heartbeat.ts` | NO EXISTE | Libre (lógica inline en worker-bot) |
| `[[analytics_engine_datasets]] binding METRICS` | Verificado: no binding actual en `apps/worker-bot/wrangler.toml` | Libre |
| R2 bucket `rdm-logs` | Pre-flight Alex Day 0 (no en código) | N/A |
| Telegram channels `@rdm-alerts-critical` + `@rdm-alerts-warning` | Pre-flight Alex Day 0 | N/A |
| `cron_heartbeats` D1 table | Conflicto remap §3 arriba | Resuelto en este thread |
| `/admin/health` page | LIVE — F2 EXTIENDE | OK (extend, not rebuild) |

Conclusión: ninguna otra claim del spec F2 está rota. Solo el slot 0042.

---

## §7. Bloqueador downstream

- B4 (F1 spec expansion) asume F2 reservation existe → este thread satisface esa asunción.
- B5 (F3 spec expansion) sigue el mismo patrón.
- F2 ship real sigue bloqueado por Q3.1 (G7 voto Alex thread/148).

---

## §8. Definition of done — B1

- [x] Audit migrations rdm-bot filesystem (0042 → feedback_system; 0046 → cost_telemetry; 0047 → libre)
- [x] Audit thread/175 T2 (cost_telemetry sí ocupó slot 0046 efectivamente)
- [x] Identificar conflicto F2 spec § anti-realidad
- [x] Hallazgo bonus: bot_config heartbeat pattern existente documentado
- [x] Voto WC preliminar registrado (Opción A)
- [x] Patch específico al spec listado (§5)
- [x] Status `draft-pending-alex-vote` (no se cierra sin Alex)

**Next action**: WC-Platform aplica el patch §5 a `rdm-platform/foundations/F2-observability.md` cuando Alex confirme opción (vía thread/148 G7 follow-up o thread separado).

---

**END THREAD/186**
