# Thread 131 · WC handoff CC · Inbox Part E rescue (mobile WhatsApp UX completion)

**From:** WC
**To:** CC-Bot
**Date:** 2026-05-19
**Type:** DoIt handoff · autonomous
**Spec base:** thread/107 §5 (original spec, 60% shipped)
**Mode:** Full autonomous · CC ejecuta sin permiso step-by-step
**Order:** EJECUTAR DESPUÉS de thread/127 (A5) complete y thread/130 posted
**Output thread:** thread/133 (post-completion report)

---

## TLDR

Thread/107 §5 spec'd a complete mobile WhatsApp-style inbox redesign. PR #90 (commit `f6ec24e`) shipped **only 60%** — the send infrastructure (messenger_outbound + messenger-send.ts + ReplyPanel drawer) — but **omitted** the full WhatsApp UX (mobile state toggle, ConversationView with bubbles, card-style list, threaded chat view).

Alex discovered this gap 2026-05-19 when asking "ya está operando el /Messages?" — answer was no. Alex needs this for mobile use when away from laptop.

**This thread**: complete the missing 40%. Estimated 10-13h CC autonomous.

---

## 1 · Context · what happened

| Step | Thread/PR | What happened |
|---|---|---|
| 1 | thread/107 §5 | WC wrote complete spec (~5-6h estimate). Full WhatsApp UX described in detail with code samples for InboxView component, mobile state toggle, message bubbles, CSS `#efeae2` background, `#d9fdd3` outbound bubbles, etc. |
| 2 | thread/108 §6 | CC deferred E (and D) from PR #87. Shipped F+C+A+B only. Reason: "new outbound capability needs separate PR for risk isolation". |
| 3 | thread/112 §2 | CC shipped Part E in PR #90 commit `f6ec24e`. **But only the backend** — migration 0032, messenger-send.ts, send endpoint, and a minimalist ReplyPanel drawer. **NOT** the full UX redesign. |
| 4 | thread/122 | Canary revealed `/fb/sending/sendContent` dead for our setup. PR #111 fixed transport (MakeMsg+sendFlow). UX still NOT addressed. |
| 5 | 2026-05-19 | Alex asks "¿está operando?" → WC investigates → discovers 60% completion. |

### Why this slipped

CC's closing report (thread/112 §2) didn't flag UX omissions. The PR description focused on "send routing + reply panel" as if that were the complete spec. Without explicit scope check vs original spec, the gap remained invisible until Alex tested 6 days later.

**Lesson for future**: every PR closing report must include explicit scope-check table (% of spec shipped, what was omitted, why).

---

## 2 · What's already there (DON'T rebuild)

Already shipped, work as-is:

| Component | File | Status |
|---|---|---|
| `messenger_outbound` table | `migrations/0032_messenger_outbound.sql` | ✅ Migrated |
| `messenger-send.ts` (postBeds24Message + sendManychatContent) | `apps/worker-bot/src/messenger-send.ts` | ✅ Working, post-#111 fix |
| `POST /admin/messenger/send` worker endpoint | `apps/worker-bot/src/index.ts` | ✅ Working |
| Web proxy `/api/admin/messenger/send` | `apps/web/src/pages/api/admin/messenger/send.ts` | ✅ Working |
| `ReplyPanel` component (drawer style) | inside `apps/web/src/components/admin/InboxView.tsx` | ✅ Working but minimal |
| `MESSENGER_OUTBOUND_ENABLED` flag | Worker env var | ✅ Default-OFF, Alex canary |
| Inbox table (desktop) | `apps/web/src/components/admin/InboxView.tsx` | ✅ Live but NOT mobile-WA-style |

### Already-shipped to leverage

- `GET /admin/conv/:subscriberId/history` — returns message history per subscriber. Already exists. ConversationView component uses this.
- `bot_messages_inbox` table — stores Beds24 messages with `message_id`, `bookingId`, `source` (guest/host), `time`, `text`.
- `conversations` table — stores bot session state with turn count, last_active, paused state.

---

## 3 · What's MISSING (this thread completes)

Per thread/107 §5 original spec:

| Missing component | What it does |
|---|---|
| **`isMobile` state in InboxView** | Detect viewport <1024px → switch from desktop table to mobile single-view |
| **Mobile-only `selectedConv` toggle** | List view OR full-screen conv view (NOT both at once on mobile) |
| **Card-style list (WA-style)** | Replace current desktop table with card per conversation showing avatar, name, last msg preview, timestamp, state badge |
| **`ConversationView` component** | Full-screen threaded chat with back button, message bubbles, inline reply input |
| **Message bubbles** | Inbound bubbles (white, align-left), outbound bubbles (`#d9fdd3` green, align-right). Background `#efeae2`. |
| **CSS responsive grid** | Desktop: 360px list + 1fr conv. Mobile: 1fr (toggle list/conv) |
| **Smooth transitions** | Slide-in/out animations when toggling list↔conv on mobile |

---

## 4 · Explicit scope

### ✅ YES — en scope

1. Read existing `InboxView.tsx` (556 lines) + `InboxView.css` (372 lines) to understand current state
2. Extend `InboxView.tsx` to add mobile state + ConversationView when viewport <1024px
3. Create `ConversationView` component (new file or inside InboxView.tsx)
4. Style WhatsApp-like (bubbles, backgrounds, transitions) in `InboxView.css`
5. Preserve all existing functionality:
   - Desktop table view (>= 1024px) **unchanged**
   - Filters, search, ReplyPanel — all work as before
   - All existing tests pass
6. Reuse `GET /admin/conv/:subscriberId/history` for fetching messages
7. Reuse existing `messenger/send` endpoint for outbound from inline ConversationView input
8. Add tests for mobile state toggling + ConversationView rendering
9. Update `karina-training` doc §5.1 to mention mobile-style availability

### ❌ NO — out of scope

- NO rebuild send infrastructure (works fine)
- NO new D1 migrations
- NO change to inbox API endpoints
- NO change to ReplyPanel drawer (desktop-only flow remains)
- NO change to Beds24 messages flow
- NO push notifications (Phase 2)
- NO offline support (Phase 2 — F3 PWA shell territory)
- NO voice recording (Phase 3)
- NO archive view, multi-select, batch operations (Phase 2)

Si encuentras algo fuera de scope → log a thread/133 final, NO fixees inline.

---

## 5 · Closed decisions

| Decisión | Valor |
|---|---|
| Component approach | Extend existing `InboxView.tsx`, NO crear nuevo top-level component |
| ConversationView location | Inside `InboxView.tsx` first (consistency con ReplyPanel pattern). Si crece >150 lines, mover a `apps/web/src/components/admin/ConversationView.tsx`. |
| Breakpoint | `1024px` (matches spec original §5 + ReplyPanel current CSS) |
| Message fetch | Reuse existing `GET /admin/conv/:subscriberId/history` |
| Send | Reuse existing `POST /api/admin/messenger/send` |
| Background colors (WA-style) | `#efeae2` thread bg, `#d9fdd3` outbound bubble, white inbound bubble |
| Mobile-only feature | Yes — desktop keeps current table. Mobile gets new UX. |
| State persistence | URL hash (e.g., `#conv=12345`) so back button works + share-able |
| Pull-to-refresh | Phase 2. Out of scope. |
| Read receipts | Out of scope (Beds24 messages don't expose double-tick reliably) |
| Typing indicator | Out of scope |
| Send error handling | Reuse ReplyPanel pattern (inline error message + retry option) |
| Test framework | Vitest + happy-dom (matches repo convention) |

---

## 6 · Pre-flight checklist

```bash
# Step 1 — sync rdm-discussion
cd <rdm-discussion>
git pull origin main
ls threads/131*.md
# Must exist

# Step 2 — sync rdm-bot, on main post-thread/127
cd <rdm-bot>
git fetch origin
git log origin/main --oneline -10
# Must include A5 merges (thread/127 output)
# If A5 still in flight → halt + wait

# Step 3 — verify existing components
ls apps/web/src/components/admin/InboxView.tsx
ls apps/web/src/components/admin/InboxView.css
wc -l apps/web/src/components/admin/InboxView.tsx
# Expected: 556 lines (might be more if A5 added stuff)

# Step 4 — verify existing endpoint
grep -l "history" apps/web/src/pages/api/admin/conv/\[subscriberId\]/\[action\].ts
# Must exist

# Step 5 — verify migration 0032 in production
wrangler d1 execute rincon --remote --command "SELECT COUNT(*) FROM messenger_outbound;"
# Must succeed (table exists)

# Step 6 — verify MESSENGER_OUTBOUND_ENABLED flag state
wrangler secret list --name rdm-bot
# MESSENGER_OUTBOUND_ENABLED should be set (value not visible, but key listed)
```

If any pre-flight fails → halt + Telegram Alex.

---

## 7 · Implementation

### Phase 1 · Read & understand current state (30-45 min)

Read these files, understand what's there:

```bash
cat apps/web/src/components/admin/InboxView.tsx
cat apps/web/src/components/admin/InboxView.css
cat apps/web/src/pages/api/admin/conv/\[subscriberId\]/\[action\].ts
cat apps/web/src/pages/admin/inbox.astro
cat apps/worker-bot/src/admin-conv-history.ts  # if exists; check actual path
```

Identify:
- Where `ReplyPanel` is mounted (desktop drawer logic)
- How `InboxRow` data flows
- Where filters/search/state badges render
- Current responsive CSS breakpoints

### Phase 2 · Add mobile state machine (2-3h)

In `InboxView.tsx`:

```tsx
// Add to InboxView component
const [isMobile, setIsMobile] = useState(false);
const [selectedConvId, setSelectedConvId] = useState<string | null>(null);

useEffect(() => {
  const mq = window.matchMedia('(max-width: 1023px)');
  setIsMobile(mq.matches);
  const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
  mq.addEventListener('change', handler);
  return () => mq.removeEventListener('change', handler);
}, []);

// URL hash sync (so back button works)
useEffect(() => {
  const fromHash = window.location.hash.match(/conv=([^&]+)/)?.[1];
  if (fromHash) setSelectedConvId(decodeURIComponent(fromHash));

  const onHashChange = () => {
    const m = window.location.hash.match(/conv=([^&]+)/);
    setSelectedConvId(m ? decodeURIComponent(m[1]) : null);
  };
  window.addEventListener('hashchange', onHashChange);
  return () => window.removeEventListener('hashchange', onHashChange);
}, []);

function openConv(convId: string) {
  window.location.hash = `conv=${encodeURIComponent(convId)}`;
}

function closeConv() {
  window.location.hash = '';
}

// Decide what to render
// Desktop: always render table (current behavior) — ReplyPanel drawer kept
// Mobile: render list OR conv (mutually exclusive)
const showList = !isMobile || !selectedConvId;
const showConv = isMobile && selectedConvId;

return (
  <div className={`inbox-container ${isMobile ? 'mobile' : 'desktop'}`}>
    {showList && (
      <InboxList
        rows={rows}
        onRowClick={isMobile ? openConv : undefined}  // mobile: click → fullscreen conv
                                                       // desktop: click → existing behavior
        // ... existing props
      />
    )}
    {showConv && selectedConvId && (
      <ConversationView
        convId={selectedConvId}
        onBack={closeConv}
      />
    )}
    {/* Desktop ReplyPanel stays — works for any conv reply */}
    {!isMobile && replyTarget && (
      <ReplyPanel target={replyTarget} targetId={...} onClose={closeReply} />
    )}
  </div>
);
```

### Phase 3 · Card-style list for mobile (1-2h)

In current `InboxList` (or wherever rows render), add a conditional renderer:

```tsx
// When isMobile, render cards. When desktop, render table rows (existing).
function InboxList({ rows, isMobile, onRowClick, ... }: InboxListProps) {
  if (isMobile) {
    return (
      <div className="inbox-card-list">
        {rows.map(row => (
          <InboxCard key={row.key} row={row} onClick={() => onRowClick?.(row.id)} />
        ))}
      </div>
    );
  }

  // Existing desktop table render
  return <table className="inbox-table">...</table>;
}

function InboxCard({ row, onClick }: { row: InboxRow; onClick: () => void }) {
  const channelIcon = getChannelIcon(row.channel);  // 📱 WA, 🏠 Airbnb, etc.
  const stateBadge = getStateBadge(row.state);

  return (
    <button className={`inbox-card state-${row.state}`} onClick={onClick}>
      <div className="card-row-top">
        <span className="channel-icon">{channelIcon}</span>
        <span className="card-name">{displayId(row)}</span>
        <span className="card-time">{fmtRelative(row.last_active_unix)}</span>
      </div>
      <div className="card-row-middle">
        <span className="card-preview">{row.last_message_snippet || '—'}</span>
      </div>
      <div className="card-row-bottom">
        {stateBadge}
        {row.has_keywords_critical && <span className="critical-marker">⚠</span>}
      </div>
    </button>
  );
}
```

### Phase 4 · ConversationView component (3-4h)

```tsx
interface ConversationViewProps {
  convId: string;
  onBack: () => void;
}

interface Message {
  id: string;
  text: string;
  source: 'guest' | 'host';
  timestamp_unix: number;
  delivery_status?: 'sent' | 'failed' | 'feature_off';
}

function ConversationView({ convId, onBack }: ConversationViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch history
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/admin/conv/${encodeURIComponent(convId)}/history`)
      .then(r => r.json())
      .then(data => {
        if (cancelled) return;
        const msgs = (data.messages || data.history || []).map(normalizeMessage);
        setMessages(msgs);
      })
      .catch(err => !cancelled && setError(String(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [convId]);

  // Auto-scroll to bottom on new messages
  const threadRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages]);

  async function send() {
    if (!draft.trim()) return;
    setSending(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/messenger/send', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ conversation_id: convId, text: draft }),
      });
      const data = await res.json();
      if (!data.ok) {
        setError(data.error || 'send_failed');
        return;
      }
      // Optimistic append
      setMessages(prev => [...prev, {
        id: data.external_message_id || `local-${Date.now()}`,
        text: draft,
        source: 'host',
        timestamp_unix: Math.floor(Date.now() / 1000),
        delivery_status: data.delivery_status,
      }]);
      setDraft('');
    } catch (err) {
      setError(String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="conv-view">
      <div className="conv-header">
        <button className="conv-back" onClick={onBack} aria-label="Back">←</button>
        <div className="conv-title">{convId}</div>
      </div>
      <div className="messages-thread" ref={threadRef}>
        {loading && <div className="conv-loading">Cargando…</div>}
        {!loading && messages.length === 0 && (
          <div className="conv-empty">Sin mensajes todavía.</div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`message-bubble ${msg.source === 'host' ? 'outbound' : 'inbound'}`}>
            <div className="bubble-text">{msg.text}</div>
            <div className="bubble-time">{fmtRelative(msg.timestamp_unix)}</div>
            {msg.delivery_status === 'feature_off' && (
              <div className="bubble-status">⚠ feature off</div>
            )}
            {msg.delivery_status === 'failed' && (
              <div className="bubble-status">❌ failed</div>
            )}
          </div>
        ))}
      </div>
      <div className="conv-input-bar">
        {error && <div className="conv-error">{error}</div>}
        <textarea
          value={draft}
          onChange={e => setDraft(e.target.value)}
          placeholder="Mensaje…"
          rows={2}
          disabled={sending}
          onKeyDown={e => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
              e.preventDefault();
              send();
            }
          }}
        />
        <button
          className="conv-send"
          onClick={send}
          disabled={sending || !draft.trim()}
        >
          {sending ? '...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}
```

### Phase 5 · CSS WhatsApp style (1-2h)

In `InboxView.css`, add:

```css
/* Mobile-first container */
.inbox-container.mobile {
  display: grid;
  grid-template-columns: 1fr;
  height: 100vh;
  height: 100dvh; /* dynamic viewport, for mobile browsers */
  overflow: hidden;
}

@media (min-width: 1024px) {
  .inbox-container.desktop {
    /* Existing desktop layout — unchanged */
  }
}

/* Card list (mobile only) */
.inbox-card-list {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  height: 100%;
  background: #f6f6f6;
}

.inbox-card {
  display: block;
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-bottom: 1px solid #e5e5e5;
  background: white;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s;
}

.inbox-card:active {
  background: #f0f0f0;
}

.inbox-card.state-escalated { border-left: 4px solid #DC2626; }
.inbox-card.state-bot_paused { border-left: 4px solid #FBBF24; }
.inbox-card.state-stalled { border-left: 4px solid #F97316; }
.inbox-card.state-active_bot { border-left: 4px solid #10B981; }

.card-row-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.channel-icon {
  font-size: 18px;
}

.card-name {
  flex: 1;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-time {
  font-size: 12px;
  color: #888;
}

.card-preview {
  font-size: 14px;
  color: #555;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-row-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.critical-marker {
  font-size: 16px;
}

/* Conversation View (mobile only) */
.conv-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  background: #efeae2; /* WhatsApp-style */
}

.conv-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #00a884; /* WA green darker */
  color: white;
}

.conv-back {
  background: transparent;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
}

.conv-title {
  flex: 1;
  font-weight: 600;
}

.messages-thread {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #efeae2;
}

.conv-loading,
.conv-empty {
  align-self: center;
  color: #666;
  margin-top: 32px;
}

.message-bubble {
  max-width: 75%;
  padding: 8px 12px;
  border-radius: 8px;
  position: relative;
  word-wrap: break-word;
}

.message-bubble.inbound {
  background: white;
  align-self: flex-start;
}

.message-bubble.outbound {
  background: #d9fdd3;
  align-self: flex-end;
}

.bubble-text {
  font-size: 14px;
  white-space: pre-wrap;
}

.bubble-time {
  font-size: 11px;
  color: #888;
  text-align: right;
  margin-top: 2px;
}

.bubble-status {
  font-size: 11px;
  color: #d32f2f;
  margin-top: 2px;
}

.conv-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f2f5;
  border-top: 1px solid #ddd;
}

.conv-input-bar textarea {
  flex: 1;
  resize: none;
  border: 1px solid #ccc;
  border-radius: 18px;
  padding: 8px 14px;
  font-size: 14px;
  font-family: inherit;
}

.conv-send {
  background: #00a884;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
}

.conv-send:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.conv-error {
  position: absolute;
  bottom: 60px;
  left: 12px;
  right: 12px;
  background: #fee;
  color: #c00;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
}

/* Hide filters/header on mobile when in conv view */
@media (max-width: 1023px) {
  .inbox-container.mobile .inbox-filters {
    display: none;  /* Filters live in card list view only — out of scope on conv view */
  }
}
```

### Phase 6 · Tests (2h)

Create `apps/web/src/components/admin/InboxView.mobile.test.tsx`:

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InboxView from './InboxView';

describe('InboxView mobile UX', () => {
  beforeEach(() => {
    // Mock matchMedia for jsdom
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: query.includes('max-width: 1023px'),
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('renders card list when mobile + no conv selected', () => {
    render(<InboxView initialData={mockData} />);
    expect(screen.getByText(/items need attention/)).toBeInTheDocument();
    // No conv view yet
    expect(screen.queryByRole('button', { name: /back/i })).not.toBeInTheDocument();
  });

  it('opens conv view on card click', async () => {
    render(<InboxView initialData={mockData} />);
    const firstCard = screen.getAllByRole('button')[0];
    fireEvent.click(firstCard);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
    });
  });

  it('back button returns to card list', async () => {
    render(<InboxView initialData={mockData} />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    await waitFor(() => screen.getByRole('button', { name: /back/i }));
    fireEvent.click(screen.getByRole('button', { name: /back/i }));
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /back/i })).not.toBeInTheDocument();
    });
  });

  it('renders message bubbles with correct inbound/outbound styling', async () => {
    // Mock fetch history
    global.fetch = vi.fn(() => Promise.resolve({
      json: () => Promise.resolve({ messages: [
        { id: '1', text: 'hola', source: 'guest', timestamp_unix: 1700000000 },
        { id: '2', text: 'hola, bienvenido', source: 'host', timestamp_unix: 1700000060 },
      ]}),
    } as Response));

    render(<InboxView initialData={mockData} />);
    fireEvent.click(screen.getAllByRole('button')[0]);

    await waitFor(() => {
      const bubbles = document.querySelectorAll('.message-bubble');
      expect(bubbles).toHaveLength(2);
      expect(bubbles[0]).toHaveClass('inbound');
      expect(bubbles[1]).toHaveClass('outbound');
    });
  });

  it('Cmd+Enter sends message', async () => {
    global.fetch = vi.fn(() => Promise.resolve({
      json: () => Promise.resolve({ ok: true, external_message_id: 'm1', delivery_status: 'sent' }),
    } as Response));

    render(<InboxView initialData={mockData} />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    await waitFor(() => screen.getByRole('textbox'));

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'test' } });
    fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/admin/messenger/send',
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });
});

const mockData = {
  rows: [/* fixture */],
  // etc
};
```

Target: 5-8 tests covering mobile state machine, card render, conv view fetch, send flow, error states.

### Phase 7 · Karina training doc update (15 min)

In `apps/web/src/pages/admin/karina-training/index.astro` §5.1 (inbox), add a small note:

```
<div class="kt-callout kt-callout-info">
  <p style="margin: 0;"><strong>📱 Vista móvil:</strong> En pantalla menor a
  1024px (celular), la lista se vuelve cards estilo WhatsApp + tap en una
  conversación → vista full-screen para responder. Útil cuando estás
  fuera de la laptop.</p>
</div>
```

### Phase 8 · Smoke test in production (post-merge)

```bash
# Open prod /admin/inbox on desktop browser
# Resize viewport to <1024px (DevTools)
# Verify:
# 1. Table disappears, card list appears
# 2. Tap a card → fullscreen ConversationView
# 3. Back button returns to list
# 4. Message bubbles render correctly
# 5. Send a test message (with MESSENGER_OUTBOUND_ENABLED=true preview profile)
# 6. URL hash updates (#conv=xxx) when entering conv, clears on back
# 7. Browser back button mimics conv back
```

---

## 8 · Definition of done

- [ ] InboxView.tsx extended with `isMobile` + `selectedConvId` state
- [ ] ConversationView component implemented (inside InboxView.tsx or separate file)
- [ ] Card-style list renders on mobile (replaces table)
- [ ] Desktop view unchanged (table + ReplyPanel drawer work as before)
- [ ] Message bubbles inbound/outbound styled WhatsApp-like
- [ ] Background `#efeae2`, outbound `#d9fdd3`, inbound white
- [ ] Send works from ConversationView (reuse messenger/send endpoint)
- [ ] URL hash sync (back button works)
- [ ] 5+ new tests passing
- [ ] All existing tests still pass
- [ ] Karina training doc §5.1 updated with mobile note
- [ ] Smoke test on prod passes (after merge + deploy)
- [ ] thread/133 posted with completion report including before/after screenshots

---

## 9 · Risks + mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | Existing tests break due to refactor | Run vitest after each phase. Revert if breakage and isolate. |
| R2 | Desktop table layout regresses | Phase 2 carefully wraps mobile-only logic in `isMobile` conditional. Test on desktop viewport before commit. |
| R3 | `/admin/conv/:subscriberId/history` returns different shape than expected | Read endpoint response in Phase 1. Adjust `normalizeMessage` accordingly. |
| R4 | Beds24 conversations have different shape than ManyChat | History endpoint should normalize. If not, branch by source. |
| R5 | `MESSENGER_OUTBOUND_ENABLED=false` blocks send → UX confusion | Show "feature off" inline status (already implemented in messenger-send.ts). Add visible badge in conv view header. |
| R6 | URL hash conflicts with other state | Use namespaced hash: `#inbox/conv=xxx` to avoid collision. |
| R7 | Mobile keyboard pushes input off-screen | Use `100dvh` instead of `100vh`. Test on real device. |
| R8 | Long conversations slow render | Limit fetch to last 100 messages initial. Pagination Phase 2. |
| R9 | Karina starts using and finds bug | Smoke test thoroughly before announcing. Default-off / soft-launch. |
| R10 | A5 (thread/127) changed `InboxView.tsx` or related files | Phase 1 reads current state. Adjust diff plan accordingly. |

---

## 10 · Communication

| Trigger | Mensaje |
|---|---|
| Pre-flight done, starting | "thread/131 Part E rescue starting. ETA 10-13h." |
| Phase 2 complete (mobile state machine works) | "Mobile state toggle live. Desktop unchanged. Continuing to card list." |
| Phase 4 complete (ConversationView renders) | "ConversationView live with bubbles + send. Polishing CSS." |
| Tests passing | "All tests green. PR draft ready." |
| Halt condition | "thread/131 halted at Phase X. Reason: Y. Need: Z." |
| Complete | thread/133 + Telegram "Mobile inbox Part E shipped. Smoke test pending Alex." |

**No reportes en cada commit.** Solo milestones above.

---

## 11 · Comando para arrancar

```
Pre-flight:
1. git pull origin main en rdm-discussion
2. git pull origin main en rdm-bot (verify A5 thread/127 completed and merged)
3. Verify InboxView.tsx exists at apps/web/src/components/admin/
4. wrangler d1 execute rincon --remote --command "SELECT COUNT(*) FROM messenger_outbound;" → no error

Lee:
- threads/131-wc-cc-mobile-inbox-rescue-doit.md (this)
- threads/107-wc-doit-small-items-wave-6-parts.md §5 (original spec, reference)
- threads/112-cc-bot-c-e-d-p2-wave-shipped-canary-playbook.md §2 (what shipped)
- threads/122-cc-bot-canary-results-and-manychat-architecture.md (send-flow fix)

Ejecuta thread/131 phases 1-8 sequential.

Time budget: 10-13h. Excedo 1.5x (19h) = stop + Telegram.
Comunicación: solo milestones del §10.
Output: thread/133 con report final + screenshots.
```

---

## 12 · Working notes

- **Stuck > 30 min** en algo específico: skip, log, continue. No bloquees todo por 1 detail.
- **Out-of-scope finding**: log a thread/133 final, NO fixees inline.
- **Self-review pre-commit**: lee tu propio diff. Específicamente verifica que desktop view NO cambió.
- **Time budget**: 10-13h. Si excedes 1.5x (≈19h), stop + reporta.
- **Test on real mobile**: si tienes acceso a un device real durante development, mucho mejor que solo DevTools viewport resize. Apple Safari + Android Chrome diferentes.

---

## 13 · Post-completion

| Item | Quien |
|---|---|
| Smoke test on real mobile (Alex's Xiaomi 15) | Alex, 5-10 min |
| Karina demo (show her the mobile UI) | Alex + Karina, 10 min |
| Verify ReplyPanel desktop still works | Alex, 2 min |
| Decide if MESSENGER_OUTBOUND_ENABLED stays canary or flips ON | Alex, post-smoke |
| If issues: thread/134 for refinement | TBD |

---

WC out.

🚀 Esta vez sí completa el spec. Y al cerrar, escribe un % de scope-vs-original explícito en thread/133 — para evitar el silent-drop pattern que llevó aquí.
