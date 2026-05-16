# CC-Data extraction spec — +100 FAQs and +100 content enrichment ideas

**Date**: 2026-05-16
**Author**: WC (with Alex)
**Owner**: CC-Data session (new or existing)
**Mode**: DoIt with explicit deliverable boundaries
**Scope**: **Extraction only. No implementation.** WC + Alex consume the artifacts and decide downstream wiring.

---

## TL;DR

Two artifacts to produce from the 12K conversation corpus:

1. **`data/artifacts/faq-candidates-v1.md`** — at least 100 FAQ candidates with real customer questions + suggested answers grounded in operator behavior
2. **`data/artifacts/content-enrichment-ideas-v1.md`** — at least 100 ideas for site content (property descriptions, landing pages, blog hooks, FAQ categories, etc.)

Each artifact is **raw extraction**, not formatted for production. WC + Alex curate and implement after.

---

## Why this exists

CC-Data's prior output (`operator_playbook.md`) targets the bot system prompt. That work is done and useful.

But the **same 12K corpus contains signal for the site**, which currently has:

- `apps/web/src/content/faqs.json` — only ~10 FAQs, several pre-data-mining and stale (e.g. pet fee says "no extra charge" — actually $300/estancia)
- Property descriptions written before the data existed
- No data-grounded content roadmap

We want to mine the corpus for these two specific consumer surfaces without diverting from V6 prompt work.

---

## Inputs

| Input | Path |
|---|---|
| Conversation corpus (anonymized) | Same source CC-Data used for `operator_playbook.md` |
| Operator playbook (for cross-reference) | `data/artifacts/operator_playbook.md` |
| Trimmed playbook (lift-sorted top 30) | `data/artifacts/operator_playbook-v6-trimmed.md` |
| Current FAQs (gaps to fill) | `apps/web/src/content/faqs.json` |
| Property descriptions (gaps to fill) | `apps/web/src/content/properties/*.md` (or wherever they live) |
| AirBnB listings (cross-reference) | `content-drafts/*.json` if available; otherwise skip |

---

## Deliverable 1 — `faq-candidates-v1.md`

### Structure

```markdown
# FAQ Candidates v1 — Extracted from 12K conversations

Source: 12K WhatsApp + Beds24 booking history conversations
Generated: YYYY-MM-DD
Total candidates: N (N >= 100)

## Methodology

Brief description of extraction approach used.

## Categories

- general (check-in, wifi, ruido, etc.)
- mascotas
- pago / facturación
- chef / cocina / servicios
- llegada / cómo llegar / transporte
- bodas / eventos / grupos grandes
- alberca / amenities exteriores
- niños / familias
- accesibilidad / movilidad
- seguridad
- temporada / clima
- (otras categorías que emerjan de los datos)

## FAQs

### FAQ 1 — [Question text in Spanish]

**Category**: [category slug]
**Frequency**: [how often this question or close variants appeared, e.g. "47/12000 conversations"]
**Customer phrasing variants** (3-5 examples, verbatim):
- "..."
- "..."
- "..."

**Operator answer pattern** (synthesized from how successful operators answered):
> [The answer in the operator's voice — direct, factual, warm but not effusive]

**Source examples** (2-3 conversation snippets, anonymized):
> USR: "..."
> OP: "..."

**Confidence**: high | medium | low (based on frequency + answer consistency)

**Notes**: [Any caveats, contradictions across conversations, edge cases]

---

### FAQ 2 — [...]
```

### Acceptance criteria

- [ ] At least 100 FAQ candidates
- [ ] Each FAQ has frequency data (denominator = total convos analyzed)
- [ ] Each FAQ has 3-5 verbatim customer phrasings (anonymized)
- [ ] Each FAQ has a synthesized operator answer grounded in real operator responses (NOT invented)
- [ ] Each FAQ has 2-3 source conversation snippets as evidence
- [ ] FAQs cover at least 10 categories
- [ ] Confidence rating on each
- [ ] Notes flag contradictions, stale info, or operator-only answers (e.g. "operator gave price X in 2023, Y in 2025")

### What NOT to do in this deliverable

- ❌ Do NOT format for production (no JSON, no astro, no markdown frontmatter)
- ❌ Do NOT pick "the right" answer when conversations conflict — show both and flag
- ❌ Do NOT invent answers. If no operator answered it consistently, mark "Confidence: low" or "no operator data — needs WC/Alex input"
- ❌ Do NOT filter for "good" FAQs. Include the awkward ones, the niche ones, the long-tail. WC curates.
- ❌ Do NOT skip rare-but-recurring questions (e.g. "does Pie de la Cuesta have a hospital nearby?" might appear 8/12000 — include it)

---

## Deliverable 2 — `content-enrichment-ideas-v1.md`

### Structure

```markdown
# Content Enrichment Ideas v1 — From 12K conversations

Source: same as above
Generated: YYYY-MM-DD
Total ideas: N (N >= 100)

## Methodology

Brief description.

## Categories of ideas

- property-description-gaps (things asked about Property X not in description)
- landing-page-topics (questions worth their own page)
- blog-post-hooks (curiosity questions → blog content)
- comparison-content (X vs Y type questions → comparison pages)
- transactional-content (how-to-X type → guides)
- emotional-context (why-do-people-come-here signals)
- objection-handling (concerns that recur → trust-building content)
- seasonal-content (questions clustering around dates)
- local-area-content (Pie de la Cuesta, Acapulco, surroundings questions)

## Ideas

### Idea 1 — [Short title of the idea]

**Type**: [category from above]
**Frequency signal**: [how many convos exhibited this gap]
**What customers ask**: [verbatim or paraphrased question pattern]
**What's missing on the site**: [what would address this — page section, FAQ entry, blog post, infographic, etc.]
**Suggested format**: [e.g. "FAQ entry", "page section under /la-huerta", "comparison table", "blog post 800-1200 words", "single sentence in hero", "video script", "landing page"]
**Suggested wording / direction** (if applicable, 1-3 sentences):
> [Plain English suggestion — NOT final copy]

**Evidence**: 2-3 conversation snippets supporting the gap
**Priority hint**: high | medium | low (based on frequency + business impact)

---

### Idea 2 — [...]
```

### Acceptance criteria

- [ ] At least 100 enrichment ideas
- [ ] Ideas span at least 6 of the suggested categories
- [ ] Each idea names a specific destination (FAQ, page, blog, video, etc.)
- [ ] Each idea has evidence from at least 2 conversation snippets
- [ ] Priority hint on each
- [ ] At least 20 ideas focused on `pie-de-la-cuesta` / local context (this is a competitive moat — most listings only describe the property, not the place)
- [ ] At least 10 ideas focused on comparison content (X vs Y) — high conversion content type
- [ ] At least 10 ideas focused on objection handling — typically high-ROI for premium rentals

### What NOT to do

- ❌ Do NOT write final copy. Direction only.
- ❌ Do NOT include ideas without conversation evidence ("we should have a video about sunsets" is not valid unless customers ask about sunsets)
- ❌ Do NOT prioritize for the team — priority hint only; WC + Alex finalize priority
- ❌ Do NOT design page layouts or component structures — that's implementation

---

## Process and effort estimate

| Phase | Effort | Output |
|---|---|---|
| Re-load corpus | 30 min | Same setup as `operator_playbook.md` run |
| Cluster questions by topic | 1-2h | Topic clusters with frequency counts |
| Extract FAQ candidates | 3-4h | Deliverable 1 |
| Extract enrichment ideas | 2-3h | Deliverable 2 |
| Cross-reference with current site content | 1h | Gap analysis used to refine deliverables |
| Final review + ship | 30 min | Both .md artifacts committed |

**Total**: ~8-12h CC-Data session. Single session if uninterrupted.

**Cost estimate**: ~$3-8 LLM costs (Sonnet) for clustering + synthesis steps. Embeddings already available.

---

## Output location

Commit to `rincondelmar-bot` repo (NOT discussion repo):
- `data/artifacts/faq-candidates-v1.md`
- `data/artifacts/content-enrichment-ideas-v1.md`

Commit message:
```
data(extraction): +100 FAQ candidates and +100 content enrichment ideas

Extracted from 12K conversation corpus (same source as operator_playbook.md).
Raw extraction artifacts for WC + Alex to curate and implement downstream.

Files:
- data/artifacts/faq-candidates-v1.md (N candidates, M categories)
- data/artifacts/content-enrichment-ideas-v1.md (N ideas, M categories)

Spec: cc-instructions-data/2026-05-16-faq-and-content-enrichment-extraction.md
Refs: thread/82 (V6 spec), thread/XX (this work)
```

Thread to publish after completion:
- `threads/XX-cc-data-faq-and-content-extraction-complete.md`

---

## Definition of Done

- [ ] `faq-candidates-v1.md` exists with 100+ FAQs meeting all acceptance criteria
- [ ] `content-enrichment-ideas-v1.md` exists with 100+ ideas meeting all acceptance criteria
- [ ] Both artifacts pushed to `rincondelmar-bot` main
- [ ] Thread published to discussion repo summarizing: total counts, top 10 unexpected findings, any data quality caveats, links to artifacts
- [ ] CC-Data reports completion to WC/Alex with summary stats

---

## Out of scope (do NOT do in this task)

- ❌ Implementing FAQs in `faqs.json`
- ❌ Writing page copy
- ❌ Modifying property descriptions
- ❌ Updating bot system prompt
- ❌ Building Vectorize indexes (separate workstream)
- ❌ Picking final FAQ list (WC + Alex do that)
- ❌ Prioritizing implementation order (WC + Alex)
- ❌ Translation to EN (WC + Alex do bilingual implementation)
- ❌ Touching `content-drafts/*.json` (separate workstream with Karina)

If any of these come up as natural side effects of the extraction work, **note them as separate work** in a "follow-on work" section at the end of each artifact. Do not execute.

---

## Notes for CC-Data session

- The 12K corpus has anonymizations applied (`[CLIENTE]`, `[PHONE]`, `[STAFF]`, `[FAMILY]`, `[URL]`, `[CLABE]`). Keep them in evidence snippets.
- Some conversations are in Spanish, some have English/code-switching. Note language distribution if interesting.
- Pet fee policy: $300 MXN/estancia max 2 (NOT /noche — historical bug in some operator messages). Flag any conversation mentioning "/noche" as data error candidate.
- Casa Chamán (5th property, Q3 2026 opening) — if it appears in conversations, treat as future signal, not active inventory.
- Some conversations may reference "Karina", "Alexander", "Doña Lupe", "Raúl" — these are real staff names, treat as normal.

---

## If stuck >30 min

- If clustering produces fewer than 100 distinct FAQ candidates: relax dedup threshold, include lower-frequency questions
- If evidence is thin for a category: include with explicit "limited evidence" tag rather than dropping
- If corpus quality issues block extraction: stop, document the issue, open thread for WC/Alex

---

**End of spec. CC-Data starts when ready.**
