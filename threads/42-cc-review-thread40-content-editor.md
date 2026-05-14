# Thread 42 — CC review of thread/40 + thread/41 (content editor proposal)

**Date**: 2026-05-13
**Author**: Claude Code (CLI)
**To**: Alex `[@alex]` — review + GO/NO-GO, Web Claude `[@wc]` — visibility
**Re**: Opinión técnica sobre Fase 1.5 Content editor proposal + auth Karina + concerns técnicos + Q-W/Q-C respuestas. Per `cc-instructions/2026-05-13-review-thread40-content-editor.md`.

NOTA: thread/41 ya tomado por Alex final answers (WC capture). Este es thread/42.

---

## 0. TL;DR

✅ **GO con sequence ajustado**. Concuerdo en estratégico con WC §2.6 (editor primero) pero ajusto ETA a **17-22h MVP** (vs 15-20h WC) o **25-30h con polish completo**.

**Auth Karina**: ✅ Better Auth magic link. NO migration role en DB — extend `lib/admin.ts` con `isContentEditor()` ENV-var helper (mismo pattern que `isAdmin()`).

**Concerns nuevos** (que WC no raised):
- Concurrent edits Alex+Karina → ETag optimistic concurrency
- Comment convention `[para Alex]` + `{open:}` necesita parser + auto-strip pre-deploy
- EN drafting bottleneck — quien drafta EN?
- Drift detection workflow — cron periódico CC re-scrape

**Q-W1 a Q-W4**: confirmo acceptance §2 thread/39 (R2 reuse, AMBOS /eventos, B.1 no blocked, Schema.org 3 types)

**Q-C1 a Q-C4**: respondidas §3 abajo (Fase 4 absorbed yes; Photos pipeline yes Fase 2.5b; Schema mostly OK con sugerencias; Validator viable)

**Sequence final**: similar a WC §4 thread/40 con ajustes ETA + add Fase 1.5b polish post-MVP (+8h, week 5-6).

---

## 1. Opinión §2.6 — Editor primero (Fase 1.5)

### 1.1 Concuerdo con razones WC

| WC argumento §2.6 | CC validation |
|---|---|
| Paralelización Alex+Karina = 2x velocidad | ✅ Real. Sin Karina, Alex es single-threaded bottleneck en review iterativo |
| Schema validation early (32 fields probando) | ✅ Real. Issues schema descubiertos editando vs después de 50h Fase 2 |
| AirBnB write-back acelera (week 3 vs 5) | ✅ Real. AirBnB cleanup 2 sem antes = SEO + bookings recovery más rápido |
| Welcome Guide construye con content real | ✅ Real. UX/UI design mejor con texto real vs lorem ipsum |

**Vote**: agree con cambio de orden. Editor primero es correcto.

### 1.2 ETA realista — ajusto WC's 15-20h

WC dice 15-20h. CC breakdown realista:

#### MVP scope (17-22h)

| Componente | ETA CC |
|---|---|
| Routes `/admin/airbnb-content/*` (index + per-field) | 6-8h |
| `ContentCell` + `ContentField` React components con char counter, status badges | 4-5h |
| API endpoints CRUD R2 (siblings de templates pattern) | 3-4h |
| `lib/welcome-storage.ts` helpers (extending templates-storage) | 1-2h |
| Auth role extension (`isContentEditor` helper + middleware) | 0.5-1h |
| Comment convention parser/renderer (`[para Alex]` + `{open:}`) | 2-3h |
| **MVP total** | **17-23h** |

#### Polish add-ons (+8h, defer Week 5-6)

| Componente | ETA CC |
|---|---|
| Diff view current AirBnB vs draft | 3-4h |
| Optimistic concurrency (ETag check) | 1-2h |
| Audit log (`/admin/airbnb-content/log`) | 2h |
| Drift detection cron (CC weekly re-scrape + alert) | 2-3h |

**Total Fase 1.5 completo**: 25-31h CC. Dividido MVP+polish = WC's 15-20h is OPTIMISTIC pero MVP-only realistic.

### 1.3 Reduce Fase 2 realmente -10h?

WC claim: -10h Fase 2.

CC analysis del thread/37 §6 Fase 2 breakdown:

| Fase 2 sub | ETA original | Saving si Fase 1.5 done | Razón |
|---|---|---|---|
| 2.1 Architecture + infra | 8-12h | 0 | Independent de content |
| 2.2 Content RdM full ES | 6-8h | -3-4h | Content ya escrito, solo render |
| 2.3 Replicate 3 más ES | 6-9h | -2-3h | Misma idea menos savings (variants per prop) |
| 2.4 Translation EN | 4-6h | -1-2h | If Karina/Alex también drafted EN |
| 2.5 Auth-gated `/mi-estancia/welcome` | 8-10h | 0 | Independent de content (logic D1) |
| 2.6 Admin editor UI | 8-12h | **-8-12h** | Ya construido en Fase 1.5 |
| **Total saving Fase 2** | | **-14-21h** | |

Realistic: WC claim de -10h es **conservadora**. Real saving es **-14-21h** porque Fase 2.6 admin UI ya construido + content drafted reduce drafting overhead.

### 1.4 Net efecto inserción Fase 1.5

```
+25-31h Fase 1.5 MVP+polish (CC 17-22h MVP + 8h polish)
-14-21h Fase 2 reduction
─────────────────
+4-17h CC neto
+2-3 sem calendar
```

Pero ese "neto +4-17h" se balancea con beneficios reales:
- Karina paraleliza drafting → Alex no bottleneck
- AirBnB cleanup 2 sem antes → SEO + biz value recuperado más temprano
- Schema validated con use real → menos retrabajo Fase 2

**Conclusión**: trade-off positivo. **GO Fase 1.5 PRIMERO**.

### 1.5 Alternative simpler considerada + rechazada

WC §2 thread/40 menciona alternativas. CC también consideró:

**(B) MVP minimal sin admin polish**: editor básico (textarea + save → R2 + git commit), sin status flow, sin diff, sin comment rendering. ETA: ~10-12h CC. Karina edita JSON directo en mini UI.

Trade-off: Karina UX peor. Sin status flow = hard track approve/deploy state. Sin comment rendering = WC tiene que limpiar manual antes de commit.

**Recomendación**: NO simplify. WC's full mockup §2.2-§2.3 es necesario. Comment convention especialmente crítica (es lo que evita que `[para Alex]` aparezca live en AirBnB).

**(C) Edit JSON files directos via PR**: Alex/Karina hacen PRs en GitHub, edit raw JSON.

Trade-off: requiere git literacy de Karina. Likely zero — Karina probably no es developer. PRs as workflow inviable.

**Vote**: stick con WC's UI proposal §2.2.

---

## 2. Opinión §3.1 — Auth Karina

### 2.1 ✅ Better Auth magic link (Q-A12 confirmed `karina@rincondelmar.club` registered)

Per Q-A12 thread/41: cuenta YA existe. CERO setup extra de auth.

### 2.2 Implementation propuesta

NO migration `users.role`. Extend `apps/web/src/lib/admin.ts` con sibling helper:

```typescript
// apps/web/src/lib/admin.ts (extended)

interface AdminEnv {
  ADMIN_EMAILS?: string;
  ADMIN_EMAIL?: string;
  CONTENT_EDITOR_EMAILS?: string;  // NEW
}

export function isAdmin(env, email): boolean { /* existing */ }

export function isContentEditor(env: AdminEnv | undefined, email: string | null | undefined): boolean {
  if (!email) return false;
  // Admins also are content editors (full access)
  if (isAdmin(env, email)) return true;
  // Else check explicit content editor whitelist
  const list = env?.CONTENT_EDITOR_EMAILS ?? '';
  const set = new Set(
    list.split(',').map(e => e.trim().toLowerCase()).filter(e => e.length > 0 && e.includes('@'))
  );
  return set.has(email.toLowerCase());
}
```

Middleware extension:

```typescript
// apps/web/src/middleware.ts
const PROTECTED = ['/mi-cuenta', '/reservar', '/r/admin', '/admin'];

// Per-route admin gate (existing pattern):
// /admin/airbnb-content/* → check isContentEditor (Karina + Alex)
// /admin/templates, /admin/health, /admin/leads, /admin/bookings → check isAdmin (Alex only)
```

### 2.3 ENV var setup

CF Pages env vars:
```
ADMIN_EMAILS=admin@rincondelmar.club             # existing
CONTENT_EDITOR_EMAILS=karina@rincondelmar.club   # NEW
```

Karina automatic gets access to `/admin/airbnb-content/*` solo. NO acceso a `/admin/templates`, `/admin/health`, futuro `/admin/leads`.

### 2.4 Por qué NO migration `users.role`

- Same pattern proven for admin (PR #5 mergeado, working en prod)
- ENV change = instant access modification (sin DB update sin restart)
- 1 staff (Karina) edge case, no warrants schema change
- Future: si staff > 5, considerar `users.role` migration entonces

### 2.5 Por qué NO secret URL

WC §3.1 thread/40 vote contra secret URL. Concuerdo:
- Filtra a logs, browser history, WhatsApp preview
- Rotación dolorosa
- No audit trail

**ETA**: 30 min CC para `isContentEditor` helper + middleware extension + tests.

### 2.6 Por qué NO SMS magic link

WC mention SMS si email Karina no confiable. Per Q-A12 confirmado email funciona. **Skip SMS**, simplifica.

---

## 3. Concerns técnicos adicionales

### 3.1 🟡 Concurrent edits Alex + Karina

Dos riesgos distintos, dos soluciones complementarias:

#### 3.1.1 Approval workflow per-cell (Alex propuesta — MVP)

Alex's idea (post-thread/42 v1): **checkboxes "Alex OK" + "Karina OK" al lado de Save button** per cell. Visual signal de quién revisó qué versión.

UI mockup:

```
┌────────────────────────────────────────────────────────┐
│ Tu propiedad — Rincón del Mar (ES)         2,156/2500 │
├────────────────────────────────────────────────────────┤
│ Villa completa con acceso directo a la playa,         │
│ diseñada por un arquitecto mexicano de renombre...    │
│ [...]                                                  │
│                                                        │
├────────────────────────────────────────────────────────┤
│ ☑ Alex OK    ☐ Karina OK    [Save]    [Diff vs live] │
│   2 min ago      pending                              │
└────────────────────────────────────────────────────────┘
```

Behavior:
- **Permission per checkbox**: solo Alex puede toggle "Alex OK", solo Karina puede toggle "Karina OK". UI grays out the other (button disabled).
- **Auto-uncheck on edit**: si content cambia (textarea modified), AMBOS checkboxes automatic uncheck (since prior approvals son stale para new content). Visual flash: "Approvals reset, requiere re-review".
- **Persist immediate**: toggle checkbox = R2 PUT immediate (no separate save needed for checkboxes).
- **Timestamp**: cada toggle records `approved_at` ISO timestamp + `approved_by_email`.

Schema addition:

```typescript
// metadata extension
metadata: {
  approvals: {
    alex_ok: boolean;
    alex_ok_at: string | null;       // ISO 8601
    karina_ok: boolean;
    karina_ok_at: string | null;
  };
  // ... otros existing fields
}
```

Display en overview `/admin/airbnb-content`:

```
┌─────────────────────────────────────────────┐
│  Tu propiedad                                │
├──────────┬──────────┬──────────┬────────────┤
│ RdM      │ Morenas  │ Combinada│ Huerta     │
│ 🟢 ✓✓   │ 🟡 ✓·   │ 🔴 ··    │ 🟢 ✓✓     │
│ 1.5K/2K │ 1.8K/2K │ EMPTY    │ 2.1K/2K    │
└──────────┴──────────┴──────────┴────────────┘
```

- 🟢 ✓✓ = both approved (ready for CC write-back)
- 🟡 ✓· = solo uno approved (waiting otro)
- 🟡 ·✓ = same idea, otro orden
- 🔴 ·· = neither approved
- ⚠️ EMPTY = field sin contenido todavía

**Deploy gate**: CC write-back via Chrome MCP requires `alex_ok = true`. `karina_ok` is INFORMATIONAL ONLY (Alex es final authority). Karina checkbox helps coordinar workflow ("Karina vio + ok mi turno") sin ser blocker técnico.

**ETA**: ~2-3h CC adicional al MVP (incluye schema, UI checkboxes, permission logic, auto-uncheck, overview badges).

#### 3.1.2 Optimistic concurrency ETag (defensiva, polish)

Scenario complementario: Alex edita `tu-propiedad` RdM ES 14:00:00 en laptop. Karina edita SAME field 14:00:30 en tablet. Both save before seeing each other's changes (race < 30s).

Sin ETag: last-write-wins. Karina's save sobreescribe Alex's. Alex no se da cuenta hasta refresh.

Approval checkboxes §3.1.1 NO previenen este race: Alex's content perdido aunque su checkbox esté OK.

**Mitigation defensiva**: optimistic concurrency via R2 ETag.

```typescript
// On editor load:
const { content, etag } = await fetchContent('rincon-del-mar', 'es', 'tu-propiedad');
// UI shows content, stores etag in client state.

// On save:
const result = await fetch('/api/admin/airbnb-content/rincon-del-mar/tu-propiedad', {
  method: 'PUT',
  headers: { 'If-Match': etag },
  body: JSON.stringify({ content: newContent }),
});

if (result.status === 412) {
  // Precondition Failed = otro usuario lo editó mientras tanto
  showAlert('Conflict — Karina o Alex editó esto. Reload + merge cambios.');
}
```

ETA: 1-2h CC adicional. **Recomendado para Fase 1.5 polish** (post-MVP) porque race window < 30s improbable en práctica con 2 personas + checkboxes signaling.

#### 3.1.3 Combined approach

| Capa | Solución | Cuando | ETA |
|---|---|---|---|
| Workflow async ("¿lo viste?") | Checkboxes Alex OK / Karina OK | **MVP day 1** | 2-3h |
| Workflow sync (race < 30s) | ETag optimistic concurrency | Polish post-MVP | 1-2h |

Together: **3-5h CC** total para concurrency robustness completo.

### 3.2 🟡 Comment convention parser + auto-strip

WC §2.2 thread/40 define convention:
- `[para Alex] explicación` = comentario WC, fondo amarillo UI
- `{open: pregunta}` = decisión bloqueada, fondo rojo

CC implementation needed:
1. **UI rendering** (editor view): regex match → wrap in `<span class="comment-yellow">` o `<span class="comment-red">`
2. **Save behavior**: NO modificar JSON al save (comments persist en R2)
3. **Pre-deploy strip**: cuando CC ejecuta write-back via Chrome MCP, parser strip ALL `[...]` y `{...}` antes de inyectar a AirBnB. Validator BLOCKS write si encuentra `{open: ...}` (decisión pendiente, no debería deployearse).

ETA: 2-3h CC. Crítico — sin parser, Karina edita y `[para Alex] verificar precio]` puede llegar literal a guest AirBnB.

### 3.3 🟡 EN drafting bottleneck

WC §2 thread/40 mention "32 fields × 4 props" = 128 ES textboxes. ¿Quién drafta los 128 EN?

**3 options**:

| Approach | Quien | Quality |
|---|---|---|
| (A) WC drafta EN automatic post-Alex/Karina ES drafted | WC | High (ES native semantics preservadas) |
| (B) Karina/Alex drafta EN también | Karina | Variable (Karina dominio EN incierto) |
| (C) AirBnB auto-translate (existing built-in) | AirBnB | Low (literal translation, pierde context) |

**Recomendación**: (A) WC drafta EN. Pero entonces WC no es "drafter pasivo" — necesita acceso al editor too para output EN.

ETA EN: ~4-6h Alex/Karina spot-check + WC iteration.

**Implication para sequence**:
- Week 2-3: Alex+Karina drafting ES (10-15h)
- Week 3: WC drafting EN paralelo (8-10h WC time, 4-6h Alex review)

### 3.4 🟢 Drift detection

WC §4.3 thread/39 raised drift if Alex edita AirBnB directo post-deploy. Mitigation: CC re-scrape periódico.

Implementation:
- Cron `weekly-airbnb-drift-check` corre Lunes 03:00 UTC
- CC re-scrape los 4 listings × 3 URLs (Tarea 2 pattern)
- Compare vs `airbnb-content/*.json` last deployed snapshot
- If drift: log a `knowledge/airbnb-drift-{date}.md` + alert Alex via WhatsApp (existing alerts pipeline thread/30)

ETA: 2-3h CC. Defer post-MVP.

### 3.5 🟢 R2 PUT throttling/cost — NO concern

Cálculo:
- 32 cells × 2 idiomas = 64 fields total
- Auto-save 3s debounce → max ~20 saves/minute durante edición activa
- Worst case sesión 2h Alex+Karina: ~2400 saves
- R2 Class A ops free tier: 1M/month. Cost over: $4.50/M.
- 2400 saves/month nowhere near limit.
- **No throttle, no cost concern**.

### 3.6 🟢 Conflict con templates editor existente — NONE

Mismo R2 bucket (`KNOWLEDGE_BUCKET`), prefixes distintos:
- `templates/<name>.md` ← existing PR #5-#7 Phase B.0.5
- `airbnb-content/<property>.<lang>.json` ← new Fase 1.5

Same `lib/templates-storage.ts` pattern → `lib/welcome-storage.ts` (or `airbnb-content-storage.ts`) sibling. Cero conflict.

UI: AdminLayout ya tiene nav. Add `Content` link al lado de `Templates` + `Health`.

### 3.7 🟡 Photos pipeline (raised by WC §3.3)

CC §1 thread/38 dijo "NO automatiza photos". Acepto bracket inicial. Pero:
- AirBnB photos URLs estarán en `/details/photos` page (no testeé Tarea 2, asumir existe)
- CC scrape URLs → mass download → R2 `assetsrdm/photos/{property}/`
- Welcome Guide consume desde R2

ETA: 3-4h CC. **Defer Fase 2.5b** (no bloquea Fase 2 MVP que usa photos placeholder o existing apps/web).

---

## 4. Updated time estimate Fase 1.5

| Component | MVP | + Polish |
|---|---|---|
| Auth role extension (`isContentEditor`) | 0.5-1h | — |
| Routes `/admin/airbnb-content/*` | 6-8h | — |
| ContentCell + ContentField components | 4-5h | — |
| API endpoints CRUD R2 | 3-4h | — |
| Storage helper (`welcome-storage.ts` sibling) | 1-2h | — |
| Comment convention parser/render (`[para Alex]` + `{open:}`) | 2-3h | — |
| **Approval checkboxes Alex OK / Karina OK** (§3.1.1) | **2-3h** | — |
| Overview badges grid (32 cells status) | 1-2h | — |
| Diff view (current AirBnB vs draft) | — | +3-4h |
| Optimistic concurrency (ETag, §3.1.2) | — | +1-2h |
| Audit log | — | +2h |
| Drift detection cron | — | +2-3h |
| **Subtotal** | **20-28h** | **+8-11h** |
| **Total Fase 1.5 completo** | | **28-39h** |

WC's 15-20h is **optimistic, MVP only without comment parser y sin checkboxes**.

CC realistic with Alex's checkbox addition:
- **MVP**: 20-28h ← required to unblock Karina
- **+Polish**: +8-11h (Week 5-6 después de drafting comenzado)

Trade-off accepted: +3-5h MVP por checkboxes pero gana approval workflow visual desde day 1 (vs WC plan que NO tenía approval mechanism — solo `status: approved_alex` flag implícito sin UI clara).

---

## 5. Q-W1 a Q-W4 (thread/39 §2)

CC concuerda con WC's votes:

### Q-W1 — R2 bucket strategy

✅ **REUSE** templates bucket prefix `welcome-content/` (o `airbnb-content/` para clarity scope).

Razones WC válidas + agrego: pattern mental único + lib reuse + cache strategy unificado.

### Q-W2 — `/eventos.astro` standalone vs sub-section

✅ **AMBOS** (single source `eventos.es.json`, two views).

WC's argument SEO + audience targeting es correcto. Concuerdo.

### Q-W3 — Phase B.1 timing

✅ **NO blocked por Fase 2 done**. Link provisional `/guia-llegada` (Fase 0.5 fixed) → swap a `/welcome/{property}` cuando Fase 2 live.

WC sequence §3.1 thread/39 viable.

### Q-W4 — Schema.org markup

✅ **`LodgingBusiness` + `FAQPage` + `Event` en /eventos**.

Concuerdo. NO `HowTo` (Google penaliza misuse).

Adicional: agregar `BreadcrumbList` schema (CC ya usa pattern en `como-llegar.astro`).

---

## 6. Q-C1 a Q-C4 (thread/39 §7)

### Q-C1 — Fase 4 bot KB enriched absorbida en Fase 2.6?

✅ **YES**, ~1-2h extra dentro de Fase 2.

Bot KB lee de R2 via Files API (per memoria proyecto). Cuando Welcome Guide content vive en `welcome-content/{slug}.{lang}.json` en R2:
- Update bot Knowledge_Refresh cron config para incluir prefix `welcome-content/` (1 line config change)
- Bot Anthropic Files API auto-syncs new files
- Bot KB tiene access automatic

ETA marginal: 1-2h CC dentro de Fase 2.6 (mismo Phase B Knowledge_Refresh pattern existente).

### Q-C2 — Photo scraping pipeline factible?

✅ **YES** Fase 2.5b (~3-4h CC).

Pattern:
- CC navegate a `airbnb.mx/hosting/listings/editor/{listingId}/details/photos`
- Extract photo URLs from DOM (likely high-res versions)
- Download mass to local
- Upload to R2 `assetsrdm/photos/{property}/`
- Update `properties/{slug}.json` content collection con new R2 keys

Defer post-MVP Welcome Guide. NO bloquea.

### Q-C3 — Schema JSON §5 thread/39 acceptable o ajustes?

✅ **Mostly OK** con sugerencias menores:

1. **Mantener `markdown` field, NO `html_render`** — Astro parsea MD at build time, cached HTML, más flexible para variants futuros (e.g., PDF export usa misma source).

2. **Add `format` flag per AirBnB field**: AirBnB textareas NO soportan markdown rendering. Schema needs flag:

```typescript
airbnb_fields: {
  como_llegar: {
    max_chars: 5000;
    format: "plain_text" | "limited_markdown";  // AirBnB renders certain whitespace + emojis
    content: string;
  };
}
```

Validator rejects `**bold**` o `[link](url)` Markdown syntax dentro de AirBnB fields (no rendea, queda literal).

3. **Add `version_history` pointer** to R2 versioned blobs:

```typescript
metadata: {
  drafted_by: "wc" | "alex" | "karina" | "cc";
  version: 5;
  previous_version_r2_key: "airbnb-content/rincon-del-mar.es.v4.json";
  ...
}
```

Rollback capability: si CC write-back falla, restore from previous_version_r2_key.

4. **Add `pending_decisions` array** for `{open: ...}` parser output:

```typescript
metadata: {
  pending_decisions: [
    { field: "tu_propiedad", question: "verificar precio chef nuevo $1,200?", added_by: "wc", added_at: "..." },
    ...
  ];
}
```

Validator BLOCKS write-back if `pending_decisions.length > 0`. UI shows red badge per cell.

### Q-C4 — Validator description ↔ hero subhead compatibility?

✅ **YES** viable (~2h CC implementation).

Pattern: keyword overlap simple, no LLM needed:

```typescript
function checkCompatibility(airbnbDescription: string, welcomeHeroSubhead: string): { ok: boolean; warnings: string[] } {
  const warnings = [];
  
  // Both should mention same property facts
  const facts = extractFacts(airbnbDescription); // simple keyword regex (capacity, beach, chef, etc.)
  const heroFacts = extractFacts(welcomeHeroSubhead);
  
  for (const fact of facts) {
    if (!heroFacts.includes(fact)) {
      warnings.push(`AirBnB description mentions "${fact}" but Welcome Guide hero doesn't`);
    }
  }
  
  // Negation check (basic)
  const negations = ['no acepta mascotas', 'sin chef', 'no fumar'];
  for (const neg of negations) {
    const inAirbnb = airbnbDescription.toLowerCase().includes(neg);
    const inHero = welcomeHeroSubhead.toLowerCase().includes(neg);
    if (inAirbnb !== inHero) {
      warnings.push(`Contradiction: "${neg}" appears in one but not the other`);
    }
  }
  
  return { ok: warnings.length === 0, warnings };
}
```

UI: yellow badge per cell with warnings count. Click to see details. Karina/Alex decide acept/reject save.

NO blocking — solo warnings. Save proceeds with user override.

---

## 7. Sequence final propuesto

```
Week 0 [NOW]
├── Fase 0.5 fix /guia-llegada 404 (CC 30 min, ALREADY READY pending Alex go)
└── Spawn /admin/airbnb-content design discussion (CC + Alex 1h sync)

Week 1
├── Fase 1b CC cleanup templates AirBnB (CC 2-3h)
│   └── Inputs: Q-A1 ✅, Q-A2 ✅, Q-A7 footer reescribir (Alex elige opción Fase 1b)
├── Fase 1.5 design freeze + Karina onboard (Alex 30 min ENV var setup)
└── CC start Fase 1.5 build

Week 1-2
└── Fase 1.5 Content editor MVP (CC 20-28h)
    ├── /admin/airbnb-content/* routes
    ├── Schema §5 thread/39 + ajustes §6 above
    ├── R2 storage prefix airbnb-content/
    ├── Auth Better Auth + isContentEditor helper (Karina email-only)
    ├── Comment convention parser/render
    ├── **Approval checkboxes Alex OK / Karina OK per cell** (§3.1.1)
    ├── Overview badges grid (32 cells status display)
    └── Save → R2 + git commit (defer git si complica)

Week 2-3
└── Alex + Karina drafting ES (10-15h paralelo)
    ├── 32 cells × 4 props = 128 textboxes ES
    ├── Comments [para Alex] + {open: ...} convention used
    └── WC drafts EN paralelo (~8-10h WC time)

Week 3
├── Alex review EN drafts (4-6h)
└── CC write-back AirBnB via Chrome MCP (CC 2-3h)
    └── Per thread/38 plan + thread/39 §4 mitigations

Week 3-5
└── Fase 2 Welcome Guide build (CC 30-40h, REDUCED -14h)
    ├── 2.1 Architecture + infra (8-12h)
    ├── 2.2-2.4 Content render (consume R2 from Fase 1.5) (4-6h)
    ├── 2.5 Auth-gated /mi-estancia/welcome (8-10h)
    ├── (2.6 Admin editor UI ALREADY DONE en Fase 1.5)
    └── 2.7 Bot KB integration (1-2h)

Week 5-6
└── Fase 1.5 polish post-MVP (CC 8-11h)
    ├── Diff view current AirBnB vs draft
    ├── Optimistic concurrency ETag
    ├── Audit log
    └── Drift detection cron weekly

Week 6
└── Fase 3 templates AirBnB refactor + /eventos.astro (CC 14-21h)

Week 7-8
└── Phase B.1 welcome auto-send (CC 18-22h, existing Phase B roadmap)

Week 8-9
└── (Optional) Fase 2.5b Photos pipeline (CC 3-4h)
```

### Total CC time estimate

| Phase | Original (thread/37) | Adjusted (con Fase 1.5) |
|---|---|---|
| Fase 0.5 | 0.5h | 0.5h |
| Fase 1b cleanup | 2-3h | 2-3h |
| Fase 1.5 MVP (con checkboxes Alex/Karina) | — | 20-28h |
| Fase 1.5 polish | — | 8-11h |
| CC write-back AirBnB | — | 2-3h |
| Fase 2 Welcome Guide | 40-57h | 30-40h |
| Fase 3 refactor | 14-21h | 14-21h |
| Phase B.1 welcome | 18-22h | 18-22h |
| Fase 2.5b Photos (opcional) | — | 3-4h |
| **Total** | **74-103h** | **97-131h** |

Net: **+23-28h CC vs plan original** (75-100h → 97-131h). Trade-off por:
- Karina paraleliza drafting (saves Alex bottleneck weeks 2-3)
- AirBnB cleanup acelerado week 3 vs week 5 (biz value 2 sem antes)
- Schema validated early (avoid retrabajo Fase 2)

### Calendar adjusted

Original WC: 4 sem. Original CC: 5-6 sem. **Adjusted con Fase 1.5: 7-9 sem calendar.**

Acepto +1-2 sem calendar como cost necesario para benefit.

---

## 8. Sí/No proceder

✅ **SÍ proceder** con sequence §7 above.

### Confirmaciones

1. ✅ Empieza Fase 0.5 /guia-llegada 404 fix (PR #9 ya merged + deployed verificable)
2. ✅ Fase 1.5 editor primero (en lugar de Fase 2 directo)
3. ✅ Auth Karina via Better Auth magic link + `isContentEditor` ENV helper (NO secret URL)
4. ✅ Schema §5 thread/39 con ajustes §6.Q-C3 (markdown field, format flag, version_history, pending_decisions)
5. ✅ Comment convention parser implementación crítica Fase 1.5 MVP
6. ✅ Drift detection + audit log + ETag concurrency en Fase 1.5 polish (post-MVP)
7. ✅ Welcome Guide bot KB integration absorbida Fase 2.6 (no nueva fase)
8. ✅ Photos pipeline Fase 2.5b defer post-MVP

### Lo que esperamos de Alex

1. Confirma GO sequence §7
2. Indica primer batch a empezar:
   - (a) Solo Fase 0.5 + Fase 1b cleanup primero (week 0-1)
   - (b) Hasta Fase 1.5 MVP build (week 0-2)
   - (c) Pipeline completo hasta Phase B.1 (week 0-7)
3. Setup `CONTENT_EDITOR_EMAILS=karina@rincondelmar.club` en CF Pages env vars (1 min)
4. Footer reescribir decisión final (Q-A13 thread/41 — opción A/B/C/D o custom)

### Lo que esperamos de WC

1. Standby drafting workflow hasta Fase 1.5 MVP live
2. Pre-Fase 1.5: si WC quiere arrancar drafting `knowledge/content-drafts/{slug}.{lang}.json` manual en repo, OK (CC importa después al editor cuando live)
3. EN drafting workflow definido: WC primary, Alex review

---

## 9. Apéndice — Documents read

- `cc-instructions/2026-05-13-review-thread40-content-editor.md` (117 líneas) ✅
- `threads/39-wc-response-cc-thread37-38.md` (504 líneas) ✅
- `threads/40-wc-alex-answers-content-editor-proposal.md` (373 líneas) ✅
- `threads/41-wc-alex-final-answers.md` (194 líneas) ✅

Total ~1188 líneas. ETA real: ~45 min reading + 75 min drafting. On target con cc-instructions §1 estimate (1h).

---

**Status**: review completa. **WAIT Alex go** antes de cualquier ejecución.

— Claude Code (CLI), 2026-05-13
