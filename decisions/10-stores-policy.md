# 10 — Decisions stores policy

**Status**: Draft (open-for-alex-vote). WC preliminary vote: **Opción A**. Alex final.

**Decisión**: Definir cuál de los dos almacenes de "decisiones" (`rdm-discussion/decisions/` operacional vs `rdm-platform/decisions/` ADR formal) recibe nuevas entradas y bajo qué scope. Resolver el split-brain documentándolo o consolidando.

**Pre-req**: Voto Alex (spec §3 B2 thread/184).

**Autoría**: WC-Discussion drafter (CC sesión worktree B Opus 4.7, run thread/184).

---

## Contexto

El META audit thread/178 (ref A6 §3 C5) detectó dos almacenes de decisiones sin policy doc que explique el split:

| Store | Path | Formato | Contenido típico | Status frontmatter |
|---|---|---|---|---|
| Discussion | `rdm-discussion/decisions/01-09` | Markdown plano, `**Status**: Propuesta` inline | Operacional: estructura repos, channel strategy, pricing agent design, admin board UI, auth flow, PWA, orchestration, bots LLM | No formal |
| Platform | `rdm-platform/decisions/ADR-001..004 + README` | YAML frontmatter formal, status enum | Architectural: platform shift, foundations seal, cron strategy, karina-fication phase | Sí (Accepted / Proposed) |

Ambos repos viven en paralelo (CC-Bot + CC-Data + CC-Discussion + WC-Platform). Sin policy:

1. **Riesgo split-brain**: una misma decisión podría documentarse en ambos lados con redacciones que diverjan.
2. **Discovery friction**: alguien busca "¿dónde decidimos X?" debe scanear dos directorios con convenciones distintas.
3. **Drift de formato**: decisions/01-09 ya muestran formato heterogéneo (status "Propuesta", "Decidido — En implementación", "Aplazado", etc., todos en prose).

Hoy no hay regla explícita. Esta decisión la establece.

---

## Opciones

### Opción A — Freeze rdm-discussion/decisions/ as "v1 legacy"; forward todo a rdm-platform/decisions/

Todo nuevo ADR (operacional u arquitectural) va a `rdm-platform/decisions/ADR-NNN-*.md` con frontmatter formal. `rdm-discussion/decisions/01-09` se queda congelado como histórico — solo se modifica si hay corrección factual.

| Pro | Con |
|---|---|
| Una sola fuente forward. Discovery trivial. | rdm-discussion/decisions/ stale forever; cualquier referencia activa allí debe verificarse antes de cambio. |
| Sin migración de contenido — minimal effort. | Operacional + architectural mezclados en un solo store (todos pasan a usar formato ADR-NNN). |
| Formato uniforme forward (YAML frontmatter). | "Operacional" y "architectural" se diferencian sólo por contenido, no por path. |
| Compatible con CC's read-only en rdm-platform si el path se documenta para WC-Platform write. | Alguien debe acordar quién mantiene el README de rdm-discussion/decisions/ apuntando "este dir está frozen, ver rdm-platform/decisions/". |

**Aplicabilidad**: hoy. CC en este run no escribe a rdm-platform (boundary §6 thread/184), pero la policy aplica forward.

### Opción B — Mantener split por scope, formalizar formato en ambos

Operacional (channel strategy, repo structure, admin UI flows) sigue en `rdm-discussion/decisions/`. Architectural (platform shift, foundations seal, cron host strategy) sigue en `rdm-platform/decisions/`. Se documenta el split en un policy doc + se aplica el formato YAML formal a ambos directorios.

| Pro | Con |
|---|---|
| Preserva la intención original (separación de scope). | Decisión "¿esto es operacional o architectural?" requiere juicio en cada caso. |
| Historia visible en su contexto de repo. | Mantenimiento doble (dos READMEs, dos templates). |
| Lectores de un repo encuentran sus decisiones sin cross-repo. | Migración: 9 docs en rdm-discussion necesitan re-formateo (~30 min cada uno × 9 = ~5h trabajo). |
| Permite a CC editar decisions/ en rdm-discussion (su territorio). | Split-brain persiste, documentado pero no resuelto. |

### Opción C — Consolidar todo en rdm-platform/decisions/; mover 01-09 a rdm-platform/decisions/legacy/

Mover físicamente `rdm-discussion/decisions/01-09` → `rdm-platform/decisions/legacy/01-09-*.md`. Re-formatear con YAML frontmatter. Actualizar todas las referencias en STATE.md, VISION.md, threads/, READMEs.

| Pro | Con |
|---|---|
| Single source of truth real. | Effort medio (≥3-4h: mover + reformatear + actualizar refs). |
| Histórico preservado en `legacy/`. | Posible breaking refs en threads viejos (links a `rdm-discussion/decisions/04-admin-board.md`). |
| Forward + backward uniformes. | Cross-repo cohesion: rdm-discussion pierde un fragmento histórico de su identidad. |

---

## Voto WC preliminar

**Opción A** (freeze legacy, forward todo a rdm-platform).

*WC preliminary, Alex final.*

Razón:
- Effort mínimo (cero migración). Decisión reversible: si en 3 meses la opción no funciona, mover a B o C es estrictamente subset del esfuerzo (estamos en mejor posición datawise).
- ADR-NNN ya es el formato canónico del proyecto post-thread/178 (ref ADR-001..004 todos en platform/). Discussion/decisions/ es legacy de pre-platform-shift.
- Boundary clean: CC en rdm-platform es read-only en este run; nuevos ADR los redacta WC-Platform humano. Eso ya es policy implícita post-ADR-001 — esta decisión la hace explícita.
- "operacional vs architectural" no es una distinción accionable: ¿una decisión sobre channel routing es operacional o arquitectural? El juicio fricciona más que la policy "todo va a un mismo sitio".

Si Alex prefiere B: requiere update simultáneo de ambos READMEs + retrofit formato YAML a 01-09 (~5h CC). Mantenible pero overhead.

Si Alex prefiere C: requiere update de refs cross-repo (no destructivo si se hace en una sola PR coordinada). El path `rdm-platform/decisions/legacy/` aísla histórico.

---

## Implementación si Alex confirma Opción A

1. **Crear `rdm-discussion/decisions/README.md`** declarando el freeze:
   - "Este directorio está FREEZED a 2026-05-23. Histórico 01-09 preservado read-only. Nuevos ADR van a `rdm-platform/decisions/ADR-NNN-*.md`."
   - Index de los 9 docs con una línea de descripción cada uno.
2. **Actualizar `rdm-platform/decisions/README.md`** §"Future ADRs" mencionando que también opera como home de operacional going-forward.
3. **No mover archivos físicos**. No reformatear 01-09. Sólo añadir README + nota inline al top de cada doc 01-09: `> Status frozen 2026-05-23. Nuevo ADR sobre este scope va a rdm-platform/decisions/.`
4. **Esta misma decisión 10** quedaría como el último doc del directorio frozen, marcada `Decidida — Opción A`, sirviendo de bisagra al nuevo régimen.

Effort total post-voto: ~30 min CC.

---

## Implementación si Alex confirma Opción B

1. Definir taxonomía clara en `rdm-discussion/decisions/README.md`:
   - "Operacional" = decisiones sobre productos, UX flows, channel strategy, content, integraciones de servicio.
   - "Architectural" = decisiones sobre stack, deployment, security boundaries, datos.
2. Reformatear 01-09 con frontmatter YAML (`status`, `date`, `supersedes`, `superseded_by`).
3. Update `rdm-platform/decisions/README.md` clarificando que platform/decisions/ es architectural-only.

Effort: ~5h WC-Discussion + WC-Platform combinados.

---

## Implementación si Alex confirma Opción C

1. Mover físicamente 01-09 → `rdm-platform/decisions/legacy/`.
2. Reformatear con frontmatter YAML formal.
3. grep cross-repo por refs `rdm-discussion/decisions/0X-*.md` y actualizarlos.
4. Dejar `rdm-discussion/decisions/README.md` como stub redirigiendo a la nueva ubicación.
5. Esta decisión 10 misma se mueve también al nuevo path.

Effort: ~4h. Requiere coordinación con WC-Platform (write access en platform repo).

---

## Bloqueador downstream

Ninguno hardcoded. Pero forward decisions sin policy genera drift:

- ADR-005 (M1 Pricing architecture, candidate post-Karina, ~día 28+) podría escribirse en cualquiera de los dos stores sin esta policy.
- Cualquier nuevo doc operacional (post-thread/184 escenario 2 lessons learned, etc.) tiene la misma ambigüedad.

Cuanto más tardemos en decidir, más decisions ambiguas se acumulan.

---

## Definition of done — B2

- [x] Tres opciones documentadas A/B/C con pros/contras
- [x] Voto WC preliminar registrado (Opción A)
- [x] Implementación plan para cada opción (no se ejecuta — espera voto Alex)
- [x] Bloqueador downstream identificado
- [x] Status header marcado "Draft (open-for-alex-vote)"

**Next action**: Alex vota A/B/C en PR review. CC (en futura sesión) ejecuta el path elegido.

---

## See also

- thread/178 §6 (origen de esta decisión, voto preliminar WC)
- thread/184 §3 B2 (task spec en autonomous run)
- thread/148 §A (decisiones Alex pending)
- `rdm-platform/decisions/README.md` (formato ADR formal)
- META audit A6 §3 C5 (detección original del split-brain)
