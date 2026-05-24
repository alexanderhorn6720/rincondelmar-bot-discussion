---
thread: 205
author: wc
topic: inbox-p0-frontend-fixes
status: ready-for-execution
mode: DoIt
created: 2026-05-24
related_threads: [196, 200, 203, 204]
related_prs: []
parent_audit: thread/204 §2 P0 bugs
estimated_effort: 45-60min CC (1 session, frontend-only)
pipeline: single-CC
requires_deploy: apps/web auto-deploys via CF Pages (NO manual wrangler deploy needed)
severity: HIGH (Karina UX gaps + missing LLM suggestion visibility)
---

# Thread 205 — Inbox P0 frontend fixes (auto-fetch suggestion + name + timestamps)

## §0 · TL;DR

Cierra **3 bugs P0 frontend** identificados en thread/204:
1. **LLM Suggestion auto-fetch on mount** — hoy `initialSuggestion={null}` siempre, never shown
2. **Guest name real** — header muestra "Booking 79421553" en lugar de "Alan Granados"
3. **WA history timestamps fix** — workaround: mostrar etiqueta vaga en lugar de timestamps ficticios

Backend (thread/206) corre en paralelo o secuencial — son independientes.

---

## §1 · Context

Post thread/199 (display bugs) + thread/200 (conversation polimórfico) + thread/203 (phone normalize), Karina puede ver mensajes WA de bookings AirBnB. PERO:

- ❌ **NUNCA aparece sugerencia LLM** porque ConversationView no la pide al cargar
- ❌ **Header muestra "Booking 79421553"** en lugar del nombre real del huésped
- ❌ **Timestamps en bubbles son ficticios** (distribuidos artificialmente en 24h)

Estos 3 bugs hacen que ~30% del valor del spec original sea invisible para Karina.

---

## §2 · Explicit scope

### 2.1 IN scope (3 archivos modificar)

| Archivo | Cambio | LoC |
|---|---|---|
| `apps/web/src/components/conversation/ConversationView.tsx` | Agregar fetchSuggestion al Promise.all + pasar a ComposeBox | +8 modify |
| `apps/web/src/components/conversation/LLMSuggestion.tsx` | Auto-fetch on mount si initial null (siempre intentar) | +15 modify |
| `apps/web/tests/conversation/ConversationView.test.ts` (si existe) | Tests para auto-fetch suggestion | +20 modify |

NOTA: Guest name + timestamps fix son **backend**, viven en thread/206. Esta thread es frontend-only.

**Corrección scope thread/204:** P0.3 (guest name) y P0.4 (timestamps) son backend (conversation.ts). Solo P0.1 es frontend. Re-arreglo:

#### Thread/205 scope corregido
- P0.1: LLM Suggestion auto-fetch on mount (frontend)

#### Thread/206 scope corregido
- P0.2: LLM Suggestion habilitada AirBnB (backend)
- P0.3: Guest name real (backend conversation.ts)
- P0.4: WA history timestamps workaround (backend conversation.ts)
- P0.5: Unread count real (backend aggregate.ts)
- P0.6: Preview/last_msg_at desde bot_messages_inbox (backend aggregate.ts)

### 2.2 OUT of scope (NO tocar)

- ❌ Backend (`apps/worker-bot/**`) — separate thread/206
- ❌ Quick replies seed — separate thread/209
- ❌ Structured summary — separate thread/207
- ❌ Database migrations
- ❌ Frontend styling/CSS changes
- ❌ New components

---

## §3 · Closed decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Auto-fetch suggestion en ConversationView, NO en LLMSuggestion component | Centralized: Promise.all already exists ahí, una sola red call |
| D2 | Si suggestion fetch falla → silenciar error, render como antes (no romper UX) | Defensive: LLM puede fallar, no debe bloquear inbox |
| D3 | Loading state: NO mostrar spinner separado para suggestion. Solo aparece cuando lista | Reduce visual noise, suggestion es non-blocking |
| D4 | Cache suggestion result: NO. Cada open de conv hace fresh fetch | Spec dice "pre-cargada", contexto cambia con cada msg nuevo |
| D5 | Llamada paralela junto a conversation + draft + quick_replies | Mismo Promise.all existente |

---

## §4 · Implementation

### 4.1 `apps/web/src/components/conversation/ConversationView.tsx`

Modificar 3 secciones:

**Sección 1 — Import** (línea ~7):
```diff
 import {
   fetchConversation,
   postReply,
   postPauseBot,
   postResolve,
   fetchQuickReplies,
   fetchDraft,
+  fetchSuggestion,
 } from '@/lib/inbox-client';
```

**Sección 2 — State** (línea ~57):
```diff
   const [data, setData] = useState<ConversationResponse | null>(null);
   const [quickReplies, setQuickReplies] = useState<QuickReply[]>([]);
   const [draft, setDraft] = useState('');
   const [draftBannerTime, setDraftBannerTime] = useState<string | null>(null);
   const [draftAccepted, setDraftAccepted] = useState(false);
+  const [suggestion, setSuggestion] = useState<SuggestResponse | SuggestSkipResponse | null>(null);
   const [loading, setLoading] = useState(true);
```

Y agregar el type import al top:
```diff
 import type {
   ConversationResponse,
   QuickReply,
   Channel,
+  SuggestResponse,
+  SuggestSkipResponse,
 } from '@/lib/inbox-client';
```

**Sección 3 — Promise.all** (línea ~74):
```diff
     Promise.all([
       fetchConversation(convId),
       fetchQuickReplies(),
       fetchDraft(convId),
+      fetchSuggestion(convId).catch(() => null),
     ])
-      .then(([conv, qr, savedDraft]) => {
+      .then(([conv, qr, savedDraft, sugg]) => {
         if (cancelled) return;
         setData(conv);
         setQuickReplies(qr.items);
         if (savedDraft?.text) {
           setDraft(savedDraft.text);
           setDraftBannerTime(savedDraft.updated_at);
         }
+        setSuggestion(sugg);
       })
```

**Sección 4 — ComposeBox prop** (línea ~234):
```diff
         <ComposeBox
           convId={convId}
           channel={channel}
           booking={booking}
           quickReplies={quickReplies}
           initialDraft={activeDraft}
-          initialSuggestion={null}
+          initialSuggestion={suggestion}
           isMobile={isMobile}
           onSend={handleSend}
         />
```

### 4.2 `apps/web/src/components/conversation/LLMSuggestion.tsx`

**Nada que cambiar** si ConversationView pasa el initial correctamente. El componente ya soporta render con initial.

**Excepción**: si el spec quiere "regenerar" más fácil, agregar botón "✨ Generar sugerencia" cuando initial=null (en lugar de render nothing). Opcional, low effort:

```diff
   if (!result || !result.ok) {
     if (result && !result.ok) {
       return (
         <div className="conv-suggestion" style={{ opacity: 0.6 }}>
           <span className="conv-suggestion-label">✨ Sugerencia IA</span>
           <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-muted)' }}>
             {skipReasonLabel(result.skip_reason)}
           </span>
         </div>
       );
     }
-    return null;
+    // Initial null (not yet fetched): show "Generate" button
+    return (
+      <div className="conv-suggestion" style={{ opacity: 0.7 }}>
+        <button
+          type="button"
+          className="conv-suggestion-btn regen"
+          onClick={() => { void handleRegen(); }}
+        >
+          ✨ Generar sugerencia IA
+        </button>
+      </div>
+    );
   }
```

---

## §5 · Tests

### 5.1 EXTEND `apps/web/tests/conversation/ConversationView.test.ts`

(Si existe; verificar primero con `ls apps/web/tests/conversation/`)

Si existe, agregar:

```typescript
describe('LLM Suggestion auto-fetch (thread/205)', () => {
  it('calls fetchSuggestion on mount and passes to ComposeBox', async () => {
    const mockSuggestion: SuggestResponse = {
      ok: true,
      suggestion: 'Hola, gracias por tu mensaje...',
      inputs_used: { history_msgs: 5, booking_loaded: true, readiness_loaded: true, kb_docs_loaded: 0, karina_training_examples: 3 },
      cost_usd: 0.0012,
      cached: false,
    };
    vi.mocked(fetchSuggestion).mockResolvedValue(mockSuggestion);

    render(<ConversationView convId="b_79421553" />);
    
    await waitFor(() => {
      expect(fetchSuggestion).toHaveBeenCalledWith('b_79421553');
    });
    // Verify LLMSuggestion rendered with the suggestion
    expect(screen.getByText(/Hola, gracias/)).toBeInTheDocument();
  });

  it('silently handles suggestion fetch failure', async () => {
    vi.mocked(fetchSuggestion).mockRejectedValue(new Error('rate_limit'));

    render(<ConversationView convId="b_79421553" />);
    
    await waitFor(() => {
      expect(fetchSuggestion).toHaveBeenCalled();
    });
    // Conversation still renders normally
    expect(screen.queryByText(/Error/)).not.toBeInTheDocument();
  });

  it('passes skip response to ComposeBox when applicable', async () => {
    const skipResponse: SuggestSkipResponse = { ok: false, skip_reason: 'trivial' };
    vi.mocked(fetchSuggestion).mockResolvedValue(skipResponse);

    render(<ConversationView convId="b_79421553" />);
    
    await waitFor(() => {
      // Check that skip reason label shown
      expect(screen.getByText(/Mensaje trivial/)).toBeInTheDocument();
    });
  });
});
```

### 5.2 NEW tests para LLMSuggestion (si decisión D4 incluye "Generar" button)

```typescript
describe('LLMSuggestion fallback button (thread/205)', () => {
  it('renders generate button when initial is null', () => {
    render(<LLMSuggestion convId="x" initial={null} onUse={vi.fn()} onFetch={vi.fn()} />);
    expect(screen.getByText(/Generar sugerencia IA/)).toBeInTheDocument();
  });

  it('clicking generate button calls onFetch and shows loading', async () => {
    const onFetch = vi.fn().mockResolvedValue({ ok: true, suggestion: 'test', cached: false });
    render(<LLMSuggestion convId="x" initial={null} onUse={vi.fn()} onFetch={onFetch} />);
    
    fireEvent.click(screen.getByText(/Generar sugerencia/));
    expect(screen.getByText(/Generando/)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/test/)).toBeInTheDocument();
    });
  });
});
```

---

## §6 · Definition of Done

- [ ] Branch `fix/inbox-llm-suggestion-auto-fetch` creada
- [ ] Modify `ConversationView.tsx`: import + state + Promise.all + ComposeBox prop (4 cambios)
- [ ] Decisión D4: ¿Implementar fallback "Generar" button en LLMSuggestion? (Voto WC: SÍ, mejora UX caso edge)
- [ ] `pnpm --filter web typecheck` PASS 0 nuevos errors
- [ ] `pnpm --filter web test` los tests existentes pasan + 2-3 nuevos (suggestion auto-fetch)
- [ ] `git diff main --stat` muestra ~2-3 archivos
- [ ] Commit: `fix(inbox): auto-fetch LLM suggestion on conversation mount (thread/205)`
- [ ] PR creada con body:
  - Referencia thread/205
  - Cierra bug P0 #1 (thread/204 §2.1): LLM suggestion never shown
  - Frontend-only, no manual deploy needed (auto CF Pages)
  - Screenshot expected behavior pre/post si hay capacidad

---

## §7 · Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Suggestion fetch falla y rompe Promise.all | `.catch(() => null)` añadido por defecto |
| Suggestion tarda >2s y bloquea conversation render | Es paralelo a fetchConversation, NO bloquea |
| Suggestion endpoint costoso si llamado por cada open conv | Haiku ~$0.001/suggestion, ~$3/mes asumido 100 conv/día |
| Suggestion no aparece visualmente porque skip_reason | Mostrar skip reason label ya implementado |
| LLM suggestion no disponible para AirBnB-only bookings | Backend bug separado (thread/206 §2.2). Hoy returna skip_reason='no_wa_history' visible |

---

## §8 · Out-of-scope findings → issues

Si CC encuentra durante ejecución:
- Componentes fuera de `apps/web/src/components/conversation/` → issue [thread/205 OOS]
- Backend changes necesarios → NO fix, defer thread/206
- TypeScript errors pre-existentes → IGNORE

---

## §9 · Kickoff command (Alex pegará a CC)

```
DoIt thread/205: LLM Suggestion auto-fetch on conversation mount. Frontend-only.

Lee spec completa:
c:/dev/rdm/dev/discussion/threads/205-wc-cc-inbox-p0-frontend-fixes.md

Sigue §4 implementation exacto. Self-review §6 DoD antes de commit.

Working directory: c:/dev/rdm/dev/bot

Pre-flight:
1. cd c:/dev/rdm/dev/bot
2. git checkout main
3. git pull origin main
4. git log --oneline -3 — confirma último commit ≥ PR #172 phone normalize

Execution:
1. git checkout -b fix/inbox-llm-suggestion-auto-fetch
2. Editar apps/web/src/components/conversation/ConversationView.tsx según §4.1 (4 cambios)
3. Editar apps/web/src/components/conversation/LLMSuggestion.tsx según §4.2 D4 (fallback "Generar" button)
4. Si existe apps/web/tests/conversation/ConversationView.test.ts: agregar tests §5.1
5. pnpm --filter web typecheck — PASS 0 nuevos errores
6. pnpm --filter web test — verde
7. git diff main --stat
8. git add (solo archivos modificados)
9. git commit -m "fix(inbox): auto-fetch LLM suggestion on conversation mount (thread/205)"
10. git push -u origin fix/inbox-llm-suggestion-auto-fetch
11. gh pr create con title "fix(inbox): auto-fetch LLM suggestion on conversation mount (thread/205)" y body:
    - Closes thread/205, fixes P0 #1 from thread/204 §2.1
    - LLM Suggestion ahora aparece automáticamente al abrir cualquier conversation
    - Frontend-only, auto-deploys via CF Pages
    - Screenshots expected behavior

Scope ESTRICTO: frontend-only.
- apps/web/src/components/conversation/ConversationView.tsx (modify)
- apps/web/src/components/conversation/LLMSuggestion.tsx (modify, opcional)
- apps/web/tests/conversation/* (extend if exists)

NO ejecutes:
- pnpm test completo
- Backend changes (apps/worker-bot/**) — thread/206 separado
- Database migrations
- npx wrangler deploy
- CSS changes
- Cambios fuera de ConversationView y LLMSuggestion

Si encuentras algo fuera de scope → issue [thread/205 OOS].

Bloqueado >30 min = STOP y reporta.

Reportar al final con:
- 3 secciones de ConversationView modificadas
- LLMSuggestion fallback button (D4 sí/no)
- Tests pass count
- PR URL
- Verificación visual sugerida: abrir conv Alan Granados (#79421553) → debe aparecer "✨ Sugerencia IA" arriba del textarea con sugerencia generada por Haiku 4.5

GO.
```

---

## §10 · Post-merge verification

Después de merge (auto-deploy CF Pages ~3 min):

1. https://rincondelmar.club/admin/inbox
2. `Ctrl+F5`
3. Click row **Alan Granados** (#79421553)
4. Esperar ~2-3s

**Esperado:**
- Sugerencia IA aparece arriba del textarea con texto generado por Haiku 4.5
- 3 botones: "Usar", "Regenerar", "Skip"
- Pueden ver `cache hit` badge si Haiku cacheó

**Si falla:**
- Network tab: verificar `POST /api/admin/conversation/b_79421553/suggest-reply`
- Si endpoint returns `skip_reason: 'no_wa_history'` → es bug P0 #2 thread/206 (esperado, no es failure de este PR)
- Si endpoint returns 500 → reportar log

---

## §11 · References

- thread/204 §2.1 P0 bug #1 (root cause analysis)
- thread/196 §4.4.5 (spec original LLM suggestion)
- thread/200 (conversation polimórfico, contexto)
- thread/203 (phone normalize, contexto previo)
