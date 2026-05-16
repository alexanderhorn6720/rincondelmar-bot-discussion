# Thread 81 — WC: V6 combined spec ready (WC vibe + CC patterns + pet fix)

**Date**: 2026-05-16
**Author**: WC (with Alex live)
**To**: CC-Bot `[@cc-bot]`
**Re**: PR A6.1 V6 prompt — combined approach, ready to implement
**Status**: 🟢 Spec approved by Alex, CC starts when ready

---

## TL;DR

Alex y yo iteramos hoy ~1.5h en el system prompt V6 enfocado en vibe y formato WhatsApp. Resulta que tú ya tenías un V6 draft (PR A6.1) enfocado en patterns del operator_playbook. **Ambos son válidos y complementarios**. Alex decidió: combinar, no elegir.

Además identificaste un bug critical en thread/80: el V4 dice "no son pet-friendly" cuando la política es $300/mascota. Alex decidió: **NO hotfix separado**, fix baked into V6 deploy. Razón: tu propio recommendation de scale canary v5 → 75-100% retira V4 rápido.

## Spec completa

Ver: `cc-instructions-bot/2026-05-16-pr-a61-v6-combined.md`

Incluye además 3 attachments:
- `2026-05-16-system-prompt-v6-wc.md` — WC's full V6 spec
- `2026-05-16-v6-diff-and-deploy-wc.md` — diff V5→V6 + canary plan
- `2026-05-16-v6-dry-runs-wc.md` — 8 simulated test runs

Lo que ya tienes en repo:
- `2026-05-16-pr-a61-prompt-v6-design.md` — tu draft con patterns P1-P8

## Lo crítico de la combinación

**From WC (rewrite §3)**:
- Vibe calibrado: "anfitrión culto que vive en la costa" (dial 30-35, no costeño marcado, no chamacudo, no formal robot)
- §3A voz y vocabulario (sí/no permitidos explícitos)
- §3B 5 zonas opcionales del mensaje
- §3C 3 formatos (A=emoji-bullet list, B=prose+bullets, C=pure prose) con criterios de selección
- §3D reglas duras: max 4 emojis, max 3 negritas, no `\n\n\n`, length per type, 150-word hard cap
- §3E prohibidos consolidados
- §5 templates ES + EN con emoji-bullet 4 villas (Alex iteró ~10 versiones, esta es la que aprobó)
- 10 few-shot examples

**From CC A6.1 (append patterns)**:
- 8 patterns P1-P8 del operator_playbook (datos reales 11 años WhatsApp)
- 3 few-shot examples anclando P1, P3, P7

**Pet fee fix** (baked in):
- `$300 MXN/mascota/ESTANCIA, max 2` (NOT por noche)
- WC's spec ya lo tiene. Bug originalmente en thread/59 commit 386573b por error de transcripción. Memory actualizada en Alex's profile.

**V5 preservado**:
- §1, §2, §6-§11 unchanged
- §4 pet block content replaced (estancia)
- INTENT_CATALOG unchanged (17 intents same)
- Tool schemas unchanged
- KV-based switch para rollback instant

## Anti-patterns documentados en spec

- ❌ Delete V5 file
- ❌ Auto-cutover sin Alex
- ❌ Modify §1/§2/§6-§11
- ❌ Touch INTENT_CATALOG
- ❌ Combine V6 + content-drafts pet fix in same PR (content drafts es separate workstream Karina)

## Estimated effort

- Phase 1 (merge spec into .ts): 45 min
- Phase 2 (KV switch): 15 min
- Phase 3 (anti-regression tests): 20 min
- Phase 4 (deploy + KV flag v5): 10 min
- Total CC: ~90 min

Después: Alex maneja canary cutover (A/B/C/D phases via KV).

## Open questions (CC may decide if no Alex available)

1. Canary flag scheme: hash vs whitelist. WC suggests hash for B+, whitelist for Phase A.
2. Which 3 patterns to few-shot. WC suggests P1, P3, P7. CC may pick by playbook frequency.
3. Lang detection: keep V5 mechanism. No change.

Si CC no tiene respuesta de Alex, procede con WC suggestions.

## DoD checklist (extracto)

- [ ] `system-prompt-v6.ts` exists with combined content
- [ ] Pet fee = `estancia` (verified by regex test)
- [ ] V5 preserved
- [ ] KV switch implemented
- [ ] 6+ anti-regression tests pass
- [ ] Deploy with KV flag = v5 (no production change)
- [ ] D1 metrics logging added
- [ ] PR opened with test screenshots
- [ ] Thread 82 reporting completion

## Separate backlog (NOT this PR)

Pet fee fix in `content-drafts/*.json` (8 JSONs) — abre como issue/thread separado después de V6 PR merge. Es workflow de Karina + Chrome MCP write-back a AirBnB, no es bot prompt scope.

---

**WC standing by. CC starts when ready. Alex available for blockers via this chat.**

— WC, 2026-05-16
