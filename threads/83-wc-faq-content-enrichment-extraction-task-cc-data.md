# Thread 83 — WC: New extraction task for CC-Data (+100 FAQs +100 content ideas)

**Date**: 2026-05-16
**Author**: WC (with Alex)
**To**: CC-Data session (new or returning)
**Re**: New extraction-only work after Stage C v2 close
**Status**: 🟢 Spec ready, CC-Data starts when ready

---

## TL;DR

Alex observó después del data mining v2 que el sitio (`apps/web/`) y los FAQs (`apps/web/src/content/faqs.json`) **no se beneficiaron** del corpus de 12K conversaciones — solo el bot.

Pidió 2 extracciones nuevas, **extracción solamente** (Alex + WC implementan después):

1. **+100 FAQ candidates** desde el corpus
2. **+100 content enrichment ideas** para el sitio

Spec completa: `cc-instructions-data/2026-05-16-faq-and-content-enrichment-extraction.md`

---

## Por qué esto existe

- FAQs actuales en `faqs.json`: ~10 entries, datos viejos, algunos bugs (ej. pet fee dice "no cobramos extra" — real: $300/estancia)
- Property descriptions: escritas pre-data-mining
- El corpus de 12K conversaciones tiene **signal real** para ambos, pero no se ha procesado hacia esos destinos
- Operator_playbook ya entregado sirvió al bot — esto sirve al sitio

---

## Qué NO es

- ❌ NO es implementación. CC-Data solo extrae artefactos crudos en markdown.
- ❌ NO es priorización final. Solo hint de prioridad.
- ❌ NO toca el bot ni el prompt V6 (workstream separado).
- ❌ NO toca content-drafts AirBnB (workflow separado de Karina).
- ❌ NO es trabajo bloqueante de V6. Paralelo.

---

## Qué SÍ entrega

- `data/artifacts/faq-candidates-v1.md` — 100+ FAQs con evidencia, frecuencia, confidence
- `data/artifacts/content-enrichment-ideas-v1.md` — 100+ ideas con tipo, destino sugerido, evidencia

Ambos commit a `rincondelmar-bot` (no discussion repo).

---

## Effort estimate

~8-12h CC-Data session. ~$3-8 LLM costs. Single session if uninterrupted.

---

## Cuándo arrancar

Sin urgencia inmediata. Cuando CC-Data tenga turn libre. No bloquea nada.

---

## Acceptance criteria resumido

**FAQs (mínimo 100)**:
- Cada FAQ con: frequency, customer phrasings verbatim (3-5), operator answer pattern grounded in data, source snippets, confidence rating
- 10+ categorías cubiertas
- Notas sobre contradicciones / data stale

**Content ideas (mínimo 100)**:
- Cada idea con: tipo, frequency signal, destino sugerido (FAQ/page/blog/video), evidencia, priority hint
- 6+ categorías
- 20+ ideas sobre Pie de la Cuesta / local context (competitive moat)
- 10+ comparison content (X vs Y)
- 10+ objection handling

---

## Coordinación

- WC + Alex consumen los artifacts después
- CC-Data NO espera approval para arrancar — la spec es self-contained
- Si CC-Data se atora >30 min → para, abre thread con blockers

---

**WC standing by. Spec self-contained, CC-Data go when ready.**

— WC, 2026-05-16
