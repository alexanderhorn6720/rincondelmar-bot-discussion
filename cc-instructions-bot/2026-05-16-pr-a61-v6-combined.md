# PR A6.1 V6 — Combined spec (WC vibe + CC patterns) + pet fee fix

**Date**: 2026-05-16
**Author**: WC (with Alex)
**Mode**: DoIt
**Priority**: High (no urgent hotfix — pet fix baked into V6)
**Estimated CC time**: 90-120 min
**Status**: Spec ready for CC implementation

---

## Context — why this exists

Two parallel V6 efforts converging:

| Source | Owner | Focus | Status |
|---|---|---|---|
| `2026-05-16-pr-a61-prompt-v6-design.md` | CC-Bot autonomous | Incremental patterns from `operator_playbook.md` (11yr WhatsApp data) | Draft, branch `pr-a61-prompt-v6-prep-DRAFT` |
| `system-prompt-v6.md` (WC + Alex) | WC + Alex live iteration | Vibe calibration + WhatsApp formatting + pet fee fix | Approved by Alex 2026-05-16 |

Both are valid and **complementary**, not competing. Alex (via WC) decided: **combine into single V6**, not choose one.

**Pet fee bug**: discovered by CC in thread/80 (V4 returning "no son pet-friendly"). Alex's decision: **NO separate hotfix** — fix baked into V6 deploy. Rationale: canary v5 already 50% and quickly scaling to 75-100% per thread/80 recommendation. By the time V6 lands, V4 will be retired.

---

## Goal of combined V6

Best of both worlds:
- **From WC**: presentation rules (§3 emojis/bold/breaks/length), 7 vibe-calibrated few-shot examples, calibrated "anfitrión culto que vive en la costa" tone (dial 30-35 of costeño)
- **From CC A6.1**: 8 patterns (P1-P8) extracted from operator_playbook real-data analysis, 3 additional few-shot demonstrating high-value patterns

**NOT a rewrite** — incremental over V5. V5 architecture (tool-based deflective routing, INTENT_CATALOG, 11 rules) is preserved.

---

## Files attached (this handoff comes with)

| File | Purpose |
|---|---|
| `system-prompt-v6-wc.md` | WC's full V6 spec (15 sections, 10 few-shot, vibe rules) |
| `00_diff_and_deploy.md` | WC's diff V5→V6 + canary plan + metrics |
| `dry_runs.md` | WC's 8 simulated test runs validating the spec |
| `2026-05-16-pr-a61-prompt-v6-design.md` | CC-Bot's existing draft (in repo: `cc-instructions-bot/`) |

CC reads ALL FOUR before implementing.

---

## Combined V6 — what to merge

### From WC spec, take wholesale:

1. **§3A — Voice and vibe** (lines defining "anfitrión culto que vive en la costa", permitted/prohibited slang, tone dial 30-35)
2. **§3B — Message structure** (5 zones: greeting/context/body/closing/url)
3. **§3C — Three body formats** (A=emoji-bullet list, B=prose+bullets, C=pure prose, with selection criteria)
4. **§3D — Presentation rules** (max 4 emojis, max 3 bold, no `\n\n\n`, length per type with 150-word hard cap)
5. **§3E — Prohibited in opening_line** (consolidated list)
6. **Updated §5 greeting templates** (ES + EN with emoji-bullet 4 villas)
7. **Pet fee correction**: `$300 MXN/mascota/ESTANCIA, max 2` (NOT por noche)
8. **WC's 10 few-shot examples** (saludo ES/EN, precios, disponibilidad, mascotas, bodas, como-llegar, queja, escalate, comparación)

### From CC A6.1 draft, take additionally:

1. **The 8 patterns from operator_playbook**:
   - P1: Echo user data (dates+group) in opening_line
   - P2: Greet with name when available
   - P3: Recognize referral / repeat guest
   - P4: Empty openings → clarification (not generic acknowledge)
   - P5: "Déjame ver con grupo" → offer materials (anti-pattern, replace with active action)
   - P6: Distant dates → hint about high season availability
   - P7: Chef/menu questions = high intent → prioritize handoff path
   - P8: Vague commits ("esta semana") → micro-acción

2. **3 additional few-shot examples** demonstrating P1, P3, and P7 (CC chooses which from the playbook to anchor)

3. **CC's structural notes**: prompt size discipline, cache strategy preservation, anti-regression tests

### What NOT to merge (keep V5 as-is):

- §1 SIEMPRE tool (unchanged)
- §2 NO inventes URLs (unchanged)
- §4 Pet policy block (REPLACE with $300/estancia — wc spec)
- §6 Idioma (unchanged)
- §7 Anti-loop (unchanged)
- §8 Booker handoff conditions (unchanged)
- §9 No promises (unchanged)
- §10 NUNCA Casa Chamán (unchanged)
- §11 BIAS contra escalate (unchanged)
- INTENT_CATALOG entire (unchanged, 17 intents same)

---

## Implementation steps

### Phase 1 — Merge spec (CC, ~45 min)

1. Read all 4 attached files
2. In branch `pr-a61-prompt-v6-prep-DRAFT` (existing) or rename to `feat/greeter-v6-combined`:
3. Create `packages/agents/greeter/system-prompt-v6.ts` (NOT `-DRAFT`, this is real V6)
4. Structure of new prompt:

```
[V5 sections §1-§11 preserved, BUT §3 fully replaced with WC §3A-§3E]
[V5 §4 pet policy block replaced: $300 estancia]
[V5 §5 greeting templates replaced: emoji-bullet 4 villas ES + EN]

---

## CONTEXTO DE LA OPERACIÓN
[unchanged]

---

## PATRONES OPERATIVOS (P1-P8)
[CC's 8 patterns inserted here]

---

## EJEMPLOS — few-shot por intent

[WC's 10 examples]
[+ CC's 3 patterns-anchored examples for P1, P3, P7]

---

## INTENT_CATALOG
[unchanged]

---

## RESUMEN — checklist
[WC's 11-item checklist]
```

5. **CRITICAL escape**: When pasting into `.ts` template string, escape backticks (\`) and dollar-brace (${). Test build compiles.

6. **Size check**: total V6 should be ~25-28K chars / ~6500-7000 tokens. If exceeds 32K, trim few-shot or compress patterns block.

### Phase 2 — Implement KV switch (CC, ~15 min)

V5 stays as fallback. KV flag selects version per request.

```typescript
// packages/agents/greeter/index.ts
import { GREETER_SYSTEM_PROMPT_V5 } from './system-prompt-v5';
import { GREETER_SYSTEM_PROMPT_V6 } from './system-prompt-v6';

export async function getGreeterPrompt(env: Env): Promise<string> {
  const version = await env.KV_BOT_CONFIG.get('greeter_prompt_version') ?? 'v5';
  return version === 'v6' ? GREETER_SYSTEM_PROMPT_V6 : GREETER_SYSTEM_PROMPT_V5;
}
```

KV namespace already exists. Initial flag value: `'v5'` (no behavior change at deploy).

### Phase 3 — Anti-regression tests (CC, ~20 min)

Add tests in `packages/agents/greeter/__tests__/system-prompt-v6.test.ts`:

```typescript
describe('GREETER_SYSTEM_PROMPT_V6', () => {
  it('preserves V5 §1-§11 core rules', () => {
    expect(V6).toContain('SIEMPRE usa una herramienta');
    expect(V6).toContain('NUNCA escribas URLs en');
    expect(V6).toContain('Casa Chamán');
    expect(V6).toContain('BIAS contra escalate_to_human');
  });
  
  it('pet fee is per estancia, not per noche', () => {
    expect(V6).toMatch(/\$300.{0,20}estancia/i);
    expect(V6).not.toMatch(/\$300.{0,15}por noche/i);
    expect(V6).not.toMatch(/\$300.{0,15}\/noche/i);
  });
  
  it('contains all 8 patterns P1-P8', () => {
    ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'].forEach(p => {
      expect(V6).toContain(p);
    });
  });
  
  it('contains WC formatting rules', () => {
    expect(V6).toContain('Máximo 4 emojis');
    expect(V6).toContain('Máximo 3 instancias');
    expect(V6).toContain('150 palabras');
  });
  
  it('preserves INTENT_CATALOG unchanged', () => {
    const intents = ['precios', 'disponibilidad', 'cotizar', 'reservar', 
                     'mascotas', 'bodas', 'casas', 'faq'];
    intents.forEach(i => expect(V6).toContain(`\`${i}\``));
  });
  
  it('size is within budget', () => {
    expect(V6.length).toBeGreaterThan(20000);
    expect(V6.length).toBeLessThan(32000);
  });
});
```

### Phase 4 — Deploy with KV flag in v5 (CC, ~10 min)

```bash
git add -A
git commit -m "feat(greeter): V6 prompt combining vibe rules + operator_playbook patterns

- WC §3 vibe + presentation rules (emojis/bold/breaks/length)
- WC §5 greeting templates with 4-villa emoji-bullet
- CC 8 patterns (P1-P8) from operator_playbook real-data
- WC 10 + CC 3 = 13 few-shot examples
- Pet fee corrected: \$300/estancia (was incorrectly \$300/noche in V4)
- V5 architecture preserved (tools, INTENT_CATALOG, §1-§11)
- KV flag 'greeter_prompt_version' controls version, default v5

Spec: cc-instructions-bot/2026-05-16-pr-a61-v6-combined.md
Approved-by: Alex 2026-05-16

Refs: thread/80 (pet bug v4), PR A6.1 (CC draft), WC chat session"

wrangler deploy
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v5
```

Production unchanged. V6 dormant, ready to activate via KV.

### Phase 5 — Canary cutover (Alex executes, NOT CC)

After CC reports done. Alex follows:

```bash
# Fase A: Alex only (24h test)
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version_whitelist '["alex_subscriber_id"]'
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v5_whitelist

# Fase B: 10% via hash (48h)
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v6_canary_10

# Fase C: 50% (48h)
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v6_canary_50

# Fase D: 100%
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v6
```

Canary flag values to be agreed CC + Alex. Hash-based selection on subscriber_id.

### Phase 6 — Rollback (always available)

```bash
wrangler kv:key put --binding=KV_BOT_CONFIG greeter_prompt_version v5
```

Instant. No redeploy needed.

---

## Metrics to log (in worker, write to D1 `greeter_turns`)

Each bot response logs:
- `prompt_version` (`v5` | `v6`)
- `opening_line_chars`
- `opening_line_words`
- `emoji_count` (regex match)
- `bold_count` (matches `\*[^*]+\*`)
- `tool_called`
- `triple_newlines_detected` (boolean — should always false)
- `pattern_used` (CC's P1-P8 inferred via simple text match, nullable)

Without these, V5 vs V6 comparison post-deploy is impossible.

---

## Definition of Done

CC reports complete when ALL true:

- [ ] `system-prompt-v6.ts` exists with combined content (WC §3 + CC patterns + 13 few-shot)
- [ ] Pet fee says `estancia` everywhere (NOT `noche`)
- [ ] V5 file preserved (NOT deleted)
- [ ] KV switch in `getGreeterPrompt()` implemented
- [ ] Anti-regression tests pass (6 tests minimum, see Phase 3)
- [ ] Wrangler deploy succeeded
- [ ] KV flag set to `v5` (no production behavior change)
- [ ] Metrics logging added to D1 `greeter_turns`
- [ ] PR opened with screenshots of test output
- [ ] Thread published: `threads/81-cc-bot-v6-combined-deployed-flag-v5.md`

---

## Anti-patterns — DO NOT

- ❌ Delete `system-prompt-v5.ts` (rollback path)
- ❌ Auto-cutover to v6 without Alex sign-off
- ❌ Modify V5 §1, §2, §4 (except pet block), §6-§11 — those are stable
- ❌ Touch INTENT_CATALOG
- ❌ Skip the anti-regression tests
- ❌ Merge before tests pass
- ❌ Try to fix pet fee in V5 separately (it's baked into V6 deploy, per Alex decision)
- ❌ Combine V6 deploy with content-drafts JSON pet fee fix (that's a separate workstream — see below)

---

## SEPARATE workstream (NOT this PR)

`content-drafts/*.json` files may have `$300/noche` mentions if they reference pet fee. That's an **AirBnB content workflow** issue (different repo flow), not bot prompt issue. Karina (content_editor role) handles via `/admin/airbnb-content` editor, then CC Chrome MCP write-back to AirBnB.

**Open this as separate issue/thread when CC finishes V6**:
- Issue: `pet-fee-content-drafts-fix`
- Files: 8 JSONs in `content-drafts/`
- Fix: grep `$300.*noche` (pet context only) → replace `noche` → `estancia`
- Validate: `editor.rincondelmar.club/admin/airbnb-content` preview
- Workflow: send to AirBnB via Chrome MCP per existing Karina pipeline

CC does NOT do this work in PR A6.1. Document only as backlog at PR close.

---

## Open questions for Alex (CC may ask before implementing)

1. **Canary flag scheme**: prefer hash-based per subscriber_id, or whitelist-based per email/phone? WC suggests hash for B+, whitelist for A.
2. **Which 3 patterns to anchor** with new few-shot: WC suggests P1 (echo user data), P3 (repeat guest), P7 (chef high-intent). CC may have data preference per playbook frequency.
3. **Should V6 lang detection auto-apply** (per V5 §6) or be tested separately? WC suggests same as V5, no change.

If CC has no answers, proceeds with WC suggestions above.

---

## If stuck >30 min

Stop. Open issue with current state + blockers. Don't improvise on critical paths (KV flag, prompt size, tool schemas).

---

**End of spec. CC starts when ready.**
