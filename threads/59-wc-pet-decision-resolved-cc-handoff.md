# Thread 59 — Alex resolved Q-56-1 + CC handoff (deploy worker + PR #32)

**Date**: 2026-05-15 (morning, Alex woke up)
**Author**: Web Claude (WC)
**To**: CC `[@cc]` + CC-Data `[@cc-data]`
**Re**: thread/56 Q-56-1 + thread/58 acciones bloqueantes
**Status**: 🟢 GO — 3 bloqueantes resueltos, sprints arrancan

---

## 0. Decisiones Alex 2026-05-15 morning

| Q | Respuesta Alex | Implicación |
|---|---|---|
| Q-56-1 mascotas | **$300/mascota/noche, máximo 2** | Unblocks: content drafts push, PetsPolicy component, operator playbook |
| Worker deploy | **CC ejecuta** | Habilita endpoints PR #29 + #30 + #33 live |
| PR #32 review | **CC ejecuta** | Merge + close DRAFT si OK |

---

## 1. Q-56-1: Pet policy oficial 2026 — $300/noche, máximo 2

### Decisión Alex
```
$300 MXN por mascota por noche
Máximo 2 mascotas por reserva
```

**Reconciliación con sources existentes**:

| Source | Pre-decisión | Post-decisión Alex |
|---|---|---|
| `knowledge_findings.md` (extraído 11 años WA) | $250/noche max 2 (histórica) | OUTDATED — ajustar |
| `content-drafts/*.json` (WC 8 files) | "sin cargo extra" | OUTDATED — ajustar |
| AirBnB listings cutover memo | Inconsistente: $250 RdM, $300 Huerta | NOW UNIFORM: $300 todas |
| Phase B `leads.pets_count` field | OK schema | OK, no changes |

### Reglas operacionales (preserve from findings)
- ✅ Mantener mascotas alejadas de alberca, sofás, camas
- ✅ No dejarlas solas en habitaciones
- ✅ Limpiar en caso de accidentes
- ✅ Avisar al reservar

### Variante Huerta (preserve)
- Tenemos 3 borregos, 3 chivos, "la prieta" (perra mansa adoptada)
- Si tus mascotas no se llevan con otros animales, mantén tu perro en correa o adentro
- "La prieta" puede ir a la playa contigo

### Acciones derivadas (asignadas)

| # | Acción | Owner | ETA |
|---|---|---|---|
| 1 | Update 8 content-drafts JSONs (mascotas section ES+EN) | **WC** | esta sesión |
| 2 | PetsPolicy component PR A1.5 (con $300 + reglas) | **CC** | próximo PR |
| 3 | Greeter v5 system prompt sección mascotas | **WC** | spec PR A6 |
| 4 | Operator playbook puede incluir pet patterns | **CC-Data** | Día 3 unblocked |
| 5 | AirBnB listings updates (consistencia $300) | **Alex/Karina** | post content-drafts review |

---

## 2. CC handoff — acciones inmediatas

### 2.1 🔴 Deploy worker rincon-bot

**Tu acción**:
```powershell
cd C:\rincondelmar-bot\apps\worker-bot
pnpm exec wrangler deploy
```

**Verify post-deploy**:
```powershell
# Click tracking endpoint
curl -sSI "https://bot.rincondelmar.club/r/bot/precios?prop=rincon-del-mar&conv=test&v=test&lang=es"
# Esperado: HTTP/1.1 302 Found + Location: /rincon-del-mar?...#tarifas

# Telegram notif endpoint
curl -sS -X POST "https://bot.rincondelmar.club/internal/notify-human" `
  -H "x-admin-secret: $env:ADMIN_REFRESH_SECRET" `
  -H "Content-Type: application/json" `
  -d '{"subscriber_id":"test","last_user_message":"test handoff post-deploy","intent":"escalate"}'
# Esperado: {"ok":true,"handoff_id":N,...}
# Y mensaje Telegram llega a chat 8711110474
```

**Si algo falla**: rollback + report a thread/60.

### 2.2 🟡 PR #32 BookingCard URL params

**Tu acción**:
1. Test manual: `https://rincondelmar.club/rincon-del-mar?check_in=2026-08-15&check_out=2026-08-17&guests=8#tarifas`
2. Verify: ¿form se pre-rellena con esos values?
3. Verify: ¿auto-quote dispara (si aplica)?
4. Si OK:
   ```powershell
   gh pr ready 32
   gh pr merge 32 --squash --admin --delete-branch
   ```
5. Si NO OK: comment en PR con issues + push fixes.

### 2.3 🟡 PR A1.5 sub-components (después de #32 merge)

Spec en `threads/58-wc-ack-cc-overnight-and-pr-a15-spec.md`.

3 sub-components a refactor de `<PropertyAmenities>`:

| Component | ID anchor | Lógica per-property |
|---|---|---|
| `<RoomsTable>` | `#capacidad` / `#capacity` | Universal — varía data per property |
| `<ChefSection>` | `#chef` | Conditional: skip Huerta, cross-sell Morenas→RdM |
| `<PetsPolicy>` | `#mascotas` / `#pets` | **Now unblocked**: $300/noche max 2 + Huerta variant animales |

### 2.4 PetsPolicy copy ready (CC use as-is)

**ES — RdM, Morenas, Combinada** (3 properties):
```markdown
## Mascotas

Mascotas bienvenidas en todas las casas.

**Costo**: $300 MXN por mascota por noche
**Máximo**: 2 mascotas por reserva

**Reglas de convivencia**:
- Mantenerlas alejadas de alberca, sofás y camas
- No dejarlas solas en habitaciones
- Limpiar en caso de accidentes
- Avisarnos al reservar para coordinar logística

¿Vienes con perro o gato? Confírmalo al reservar y te ayudamos con todo.
```

**ES — Huerta Cocotera** (con narrativa animales):
```markdown
## Mascotas

Pet-friendly con consideraciones especiales.

**Costo**: $300 MXN por mascota por noche
**Máximo**: 2 mascotas por reserva

**En Huerta tenemos**:
- 3 borregos
- 3 chivos
- "La Prieta" — perra mansa que adoptamos

Si tus mascotas no se llevan bien con otros animales, mantén a tu perro 
en correa o dentro de la casa. "La Prieta" puede acompañarte a la playa 
si quieres — es muy querida del lugar.

**Reglas generales**:
- Mantenerlas alejadas de alberca, sofás y camas
- No dejarlas solas en habitaciones
- Limpiar en caso de accidentes
- Avisarnos al reservar
```

**EN — RdM, Morenas, Combinada**:
```markdown
## Pets

All houses are pet-friendly.

**Fee**: $300 MXN per pet per night
**Maximum**: 2 pets per reservation

**House rules**:
- Keep pets away from the pool, sofas, and beds
- Don't leave them alone in bedrooms
- Clean up in case of accidents
- Let us know when booking to coordinate logistics

Coming with a dog or cat? Confirm when booking and we'll help with everything.
```

**EN — Huerta Cocotera**:
```markdown
## Pets

Pet-friendly with special considerations.

**Fee**: $300 MXN per pet per night
**Maximum**: 2 pets per reservation

**At Huerta we have**:
- 3 sheep
- 3 goats
- "La Prieta" — a gentle adopted dog

If your pets don't get along with other animals, keep your dog on a leash 
or indoors. "La Prieta" can join you at the beach if you'd like — she's a 
beloved member of the place.

**General rules**:
- Keep pets away from the pool, sofas, and beds
- Don't leave them alone in bedrooms
- Clean up in case of accidents
- Let us know when booking
```

### 2.5 ETA total CC

| Tarea | ETA |
|---|---|
| Deploy worker | 5 min |
| PR #32 review + merge | 30 min |
| PR A1.5 sub-components (3 components + tests + i18n) | 3-4h |
| **TOTAL** | **~4h CC** |

---

## 3. CC-Data handoff — Día 1 unblocked

CC-Data: pet policy decision resolved. Puedes arrancar **Día 1** del plan:

1. Read `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` (updated con thread/57 audit)
2. Read `threads/57-wc-edge-case-audit-v2-plan.md` (4 critical mitigations)
3. Pre-flight checks:
   - ✅ Verify `chat-to-contact.json` exists + current
   - ✅ Generate phone hash pepper (32 random bytes, NEVER commit)
   - ✅ Confirm `bge-m3` multilingual model usage
   - ✅ Outcome label uses 3-value enum + cancellation filter
4. Arranca Stage 0 (business filter) + Stage A (reconstruction)
5. Reporta thread/60 fin Día 1

**Context para Stage C operator playbook (Día 3)**: pet policy $300/noche max 2 = USE THIS en patterns extraction. Si findings dice $250, label as "historical pricing — current is $300".

---

## 4. WC handoff — content-drafts update

WC esta sesión va a:

1. ✅ thread/59 publicado (este file) — handoff a CC + CC-Data
2. ⏳ Update 8 content-drafts JSONs (mascotas section):
   - 4 properties × 2 langs = 8 files
   - Replace "sin cargo extra" con "$300/noche max 2 + reglas"
   - Huerta variant preserva narrativa animales
3. ⏳ Memory update con pet policy decision

---

## 5. Resumen estado proyecto (post-Q-56-1)

### ✅ Resueltos
- Q-BR1: Booking card funcional
- Q-BR2: /reservar/ funcional
- Q-BR3: Telegram notif configurado
- Q-BR4-7: Métricas + URL format + ETA + cities aprobados
- D1-D8: Decisiones arquitecturales aprobadas
- Q-54-1-5: Data mining v2 aprobado
- **Q-56-1: Pet policy $300/noche max 2** ✅ NEW

### 🟡 Pending (CC)
- Worker rincon-bot deploy (5 min)
- PR #32 BookingCard review (30 min)
- PR A1.5 sub-components (~4h)

### 🟡 Pending (CC-Data)
- Día 1: Stage 0 + Stage A (~8h)
- Día 2: Stage B + E (~8h)
- Día 3: Stage C + Alex validate (~8h + 25min)
- Día 4: Deploy a D1 + R2 + Vectorize (~8h)

### 🟡 Pending (WC)
- Content drafts update mascotas (esta sesión)
- cc-instructions-bot Fase 2 (Greeter v5 prompt + tool-use)
- Post-Día-3: validate operator_playbook con Alex

### 🟡 Pending (Alex)
- Tap-by-cell review content-drafts post-mascotas-update
- Validate operator_playbook Día 3 (~25 min)
- AirBnB listings update consistencia $300 mascotas

---

**FIN thread/59**. CC: arranca Worker deploy + PR #32. CC-Data: arranca Día 1.

— Web Claude, 2026-05-15 (morning)
