# 118 — WC: pet policy correction + v5 prompt cleanup

**Date**: 2026-05-18
**Author**: WC
**To**: CC-Bot, future agents
**Re**: Retraction of thread/117 §1. Pet policy canonical = `$300 MXN/mascota/estancia, máx 2`. v5 prompt + comment header still carry the legacy `/noche` error from thread/59.
**Mode**: docs-correction + small spec for CC-Bot v5 cleanup
**Status**: 🟡 My error in 117 §1. Real damage in prod = near-zero (v6 at 100% canary). Small cleanup task for CC-Bot when convenient.

---

## TL;DR

In thread/117 §1 I asserted the handoff doc had the pet policy fix direction inverted. **I was wrong.** Alex confirmed in chat (2026-05-18): pet fee is `$300 MXN/mascota/estancia, máx 2`. The handoff doc was correct. Thread/59 (previous WC) captured Alex's decision incorrectly as `/noche` — that's the canonical-doc-with-error, not the handoff.

The damage chain:
1. Thread/59 (2026-05-15) — WC records "$300/noche" from Alex. **Wrong transcription.**
2. PR A6 (greeter v5 system prompt) — copies "$300/noche" verbatim from thread/59.
3. Web content (PropertyPets, faqs, homepage) — also gets "/noche".
4. Alex catches the bug on web (faq#mascotas) → PR #78 (2026-05-16) — fixes ALL web content to "/estancia".
5. PR A6.1 (v6 prompt) — hardcoded fix to "/estancia" with explicit comment "was incorrectly /noche in v4/v5".
6. Canary v6 → 100% (thread/93) — production effectively on correct policy.
7. v5 prompt source file **never cleaned up** — still says "/noche".
8. Thread/117 §1 — I assumed the doc had it wrong, didn't check git history. **Apologies.**

---

## §1 — Canonical pet policy (use this)

```
$300 MXN por mascota por ESTANCIA (NO por noche), máximo 2 por reserva.
Uniforme en las 4 propiedades.
```

EN: `$300 MXN per pet per stay (NOT per night), max 2 per reservation. Uniform across all 4 villas.`

Source: Alex 2026-05-18 chat + PR #78 commit message + greeter v6 prompt §4.

---

## §2 — Real damage in production

| Location | Policy | Action |
|---|---|---|
| Greeter v6 prompt (canary 100%) | `/estancia` ✅ | None |
| Web — PropertyPets / faqs / homepage / villa-vs-hotel | `/estancia` ✅ | None (PR #78) |
| Greeter v5 prompt + few-shot + header comment | `/noche` ❌ | Cleanup (§4) |
| `packages/agents/greeter/prompts/system-prompt.txt` line 1044 | `$250/noche` ❌ | Verify orphan, then delete (§5) |
| `wc-seed-drafts/*.json` Airbnb workflow drafts | Mentions pets without price | Neutral — price lives in PetsPolicy component |
| AirBnB listings published | Unknown | Alex/Karina manual check (§6) |
| `thread/59` historical | `/noche` ❌ | Superseded — annotated here |
| `thread/117` §1 | inverted claim | Retracted by this thread |

**Active customer impact**: ~zero. v6 is at 100% canary (thread/93). The ~8% v5 routes are forced-v5 test subscribers (Alex's testing). Random new customers do not hit the v5 prompt.

---

## §3 — Why I missed this in thread/117

I read the handoff doc, found "fix: /noche → /estancia", saw thread/59 said `$300/noche`, and assumed the doc was inverted relative to thread/59. I did not check git log of PR #78, did not verify which one was Alex's actual position, did not check v6 prompt header comment (which explicitly says "was incorrectly /noche in v4/v5"). Cheap verification, skipped.

Lesson: when handoff doc and thread record conflict on policy, check **production code + recent commits**, not just thread history. Threads can carry forward earlier WC errors.

---

## §4 — CC-Bot cleanup task (mini-spec)

**Scope**: fix the legacy `/noche` references in v5 prompt source. Low priority because v5 routes are negligible, but worth closing to prevent regression if Alex ever flips force-v5 on a real subscriber.

### Files

| File | Line(s) | Change |
|---|---|---|
| `packages/agents/greeter/system-prompt-v5.ts` | line 71 (prompt body) | `$300 MXN por mascota por noche, máximo 2 por reserva` → `$300 MXN por mascota por estancia, máximo 2 por reserva` |
| `packages/agents/greeter/system-prompt-v5.ts` | line 395 (few-shot) | `($300/noche por mascota, máx 2)` → `($300 por mascota por estancia, máx 2)` |
| `packages/agents/greeter/system-prompt-v5.ts` | line 6 (header comment) | `Pet policy $300/noche max 2 (Q-56-1 Alex 2026-05-15)` → `Pet policy $300/estancia max 2 (Alex 2026-05-18 chat correction; thread/59 had /noche which was a transcription error)` |
| `packages/agents/greeter/tests/greeter-v5-system-prompt.test.ts` | any assertion on `/noche` | Update to `/estancia` |

### Tests

- v5 system prompt snapshot test: update snapshot
- Pet policy assertion test (if exists): assert `/estancia` AND assert "noche" does not appear in pet section

### Definition of done

- [ ] v5 prompt body says `/estancia`
- [ ] v5 few-shot says `/estancia`
- [ ] v5 header comment references Alex 2026-05-18 correction, points at thread/118
- [ ] All tests pass
- [ ] Self-review confirms no stray `pet.*/noche` in `packages/agents/greeter/`

### Effort

~15-20 min CC-Bot. Single commit, no migration, no canary, no deploy required (v6 at 100%).

### Branch / PR

`fix/v5-pet-policy-estancia` or bundle into next small-items wave.

---

## §5 — Orphan file `packages/agents/greeter/prompts/system-prompt.txt`

Contains `$250 MXN/mascota/noche` at line 1044. No code path imports or reads this file (verified `grep -rn "prompts/system-prompt"` returns empty). Probably a leftover artifact from the Make.com era or a local mirror of the external KB repo `alexanderhorn6720/rdm-greeter-kb`.

**Question for CC-Bot before §4 work**: confirm orphan via `git log packages/agents/greeter/prompts/` and grep across the workspace. If truly orphan → delete in same PR as §4. If still referenced anywhere → leave for separate ticket.

The external KB on GitHub (`rdm-greeter-kb`) is refreshed by cron into KV `greeter:system_prompt`, but `run-greeter-v5.ts` uses the hardcoded TS constant `GREETER_SYSTEM_PROMPT_V5`, not the KV value. So even that external KB is functionally dead-code-path. That's a separate cleanup (out of scope for §4).

---

## §6 — Alex action item

Verify AirBnB listings published on airbnb.com for the 4 active rooms have pet policy = `$300/estancia, max 2` and NOT `/noche`. PR #78 fixed our website but Airbnb listings are edited externally (Karina via `/admin/airbnb-content` workflow + manual paste to Airbnb). If any listing still says `/noche` or `sin costo`, it needs update.

Not blocking on me — purely Alex/Karina manual verification.

---

## §7 — Standing rule going forward

Pet policy is `$300 MXN/mascota/estancia, máx 2`. Uniform across all 4 villas. If any future spec, thread, or PR description says `/noche` or any other amount, treat as drift and flag.

Memory entry added (WC chat memory #15).

---

**No code action required from CC-Bot today unless picking up §4 in a small-items wave. Sprint C+E+D+P2 + thread/115 + thread/113 take priority.**

— WC, 2026-05-18
