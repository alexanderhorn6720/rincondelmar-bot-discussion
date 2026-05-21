# I21 · Kill placeholders del nav · CC DoIt spec

**Status**: PENDING ALEX APPROVAL (Day 3 ranking). Pre-staged so CC can pickup hours after vote.
**Workstream**: CC-Bot (territory: `apps/web` + `packages/shared`)
**Effort estimate**: 1h CC (conservative budget 1.5h with self-review)
**Source**: §A.5 + §F idea I21 of `rdm-platform/reports/admin-audit-2026-Q2-v2/`

---

## §1 · Context

### Problem

14 placeholders in nav lead to `/admin/coming-soon` (54% of all nav items don't function). Karina sees them every day, wastes taps, learns to avoid the nav. Audit `admin-audit-2026-Q2-v2` §A.4 ranked this as 🔴 immediate fix.

### Current behavior

`packages/shared/src/permissions.ts` declares 14 items as `PLACEHOLDER_ITEMS`. AdminLayout renders them inline with `·próx` badge. URL `/admin/coming-soon?feature=X` shows friendly placeholder page.

### Desired behavior

- Placeholders NOT visible in nav for Karina daily flow
- Discoverability of upcoming features preserved via dedicated `/admin/roadmap` standalone view
- Switching Karina-friendly default while keeping admin (Alex) able to see them via opt-in

---

## §2 · Explicit scope

### YES

- Remove placeholder rendering from `AdminLayout.astro` dropdowns by default
- Create `/admin/roadmap` Astro page rendering all 14 placeholders with metadata
- Update `permissions.ts` to expose helper `visibleNavStructureFor({ role, includePlaceholders })`
- `?roadmap=1` URL query enables placeholder rendering in nav (Alex preview opt-in)
- Update existing `/admin/coming-soon` stub to back-link to `/admin/roadmap`
- Roadmap page shows: feature label, group, description (from existing `featureDescriptions`), status `planning`/`in-design`/`in-build` (default `planning`)
- Mobile-first layout (cards, not table)
- Hard-guard `/admin/roadmap` to `isAdmin` + `isContentEditor` only

### NO

- DO NOT delete `featureDescriptions` map in `coming-soon.astro` (still referenced)
- DO NOT delete `PLACEHOLDER_ITEMS` set (used for `isPlaceholder()` checks elsewhere)
- DO NOT change which placeholders exist (separate decision)
- DO NOT implement any of the placeholders themselves
- DO NOT touch role permissions (`NAV_PERMISSIONS`) — only visibility logic

---

## §3 · Closed decisions

- **Roadmap path**: `/admin/roadmap` (not `/admin/upcoming`, not `/admin/features`)
- **Status enum**: hardcoded in `permissions.ts` as `Record<NavItem, 'planning' | 'in-design' | 'in-build'>`. Default all 14 to `'planning'` until manually edited.
- **Opt-in query**: `?roadmap=1` (URL state, no cookie)
- **Sticky preview**: NOT for v1. Each visit returns to default (no placeholders).
- **Footer link to roadmap**: NOT for v1. Discoverable only via direct URL `/admin/roadmap` for now.

---

## §4 · Implementation

### Files to modify

| File | Change |
|---|---|
| `packages/shared/src/permissions.ts` | Add `ROADMAP_STATUS` map + `visibleNavStructureFor()` helper |
| `apps/web/src/layouts/AdminLayout.astro` | Read `?roadmap=1` from URL, pass to `visibleNavStructureFor` |
| `apps/web/src/pages/admin/roadmap.astro` | NEW page |
| `apps/web/src/pages/admin/coming-soon.astro` | Add back-link to `/admin/roadmap` |

### `permissions.ts` additions

```typescript
// Hardcoded status per placeholder (manual edit when status changes)
export const ROADMAP_STATUS: Record<NavItem, 'planning' | 'in-design' | 'in-build' | 'live'> = {
  // Live items (real pages)
  home: 'live',
  inbox: 'live',
  bookings: 'live',
  'extra-guests': 'live',
  'pre-stay': 'live',
  conv: 'live',
  'airbnb-content': 'live',
  templates: 'live',
  'karina-training': 'live',
  'bot-metrics': 'live',
  health: 'live',
  'audit-logs': 'live',
  // Placeholders
  tasks: 'planning',
  cobranza: 'planning',
  concierge: 'planning',
  'instay-bot': 'planning',
  'lost-booking': 'planning',
  'reglas-paper-trail': 'planning',
  'post-stay-reviews': 'planning',
  'kpis-airbnb': 'planning',
  permisos: 'planning',
  pricing: 'planning',
  menus: 'planning',
  inventario: 'planning',
  'schedule-staff': 'planning',
  'compras-pedidos': 'planning',
};

/**
 * New helper — filter nav structure for role, optionally including placeholders.
 * Replaces direct usage of `visibleNavStructure(role)` in AdminLayout.
 */
export function visibleNavStructureFor(
  role: Role,
  options: { includePlaceholders?: boolean } = {},
): Array<NavGroup & { visibleItems: NavItem[] }> {
  const { includePlaceholders = false } = options;
  return NAV_STRUCTURE.map((group) => ({
    ...group,
    visibleItems: group.items.filter((item) => {
      if (!canSeeNavItem(item, role)) return false;
      if (!includePlaceholders && isPlaceholder(item)) return false;
      return true;
    }),
  })).filter((group) => group.visibleItems.length > 0);
}
```

### `AdminLayout.astro` changes

```typescript
// Before:
const visibleGroups = visibleNavStructure(effectiveRole);

// After:
const roadmapPreview = Astro.url.searchParams.get('roadmap') === '1';
const visibleGroups = visibleNavStructureFor(effectiveRole, {
  includePlaceholders: roadmapPreview,
});
```

Add small subtle indicator when `roadmapPreview` active:
```html
{roadmapPreview && (
  <span class="role-badge" title="Vista preview con placeholders">
    +roadmap
  </span>
)}
```

### `pages/admin/roadmap.astro` (NEW)

Mobile-first card grid:
- Header: "Roadmap de funciones · 14 en desarrollo"
- Status legend: `planning` (grey) · `in-design` (blue) · `in-build` (green)
- Cards grouped by NavGroup (Operaciones, Contenido, Bot, Sistema, Operaciones físicas)
- Each card: feature label, group color, status badge, description
- Single-column on mobile, 2-column on tablet, 3-column on desktop
- Tap card → `/admin/coming-soon?feature=X` (existing)

### `pages/admin/coming-soon.astro` changes

Add at footer of existing template:
```html
<p class="coming-soon-back">
  <a href="/admin/roadmap">← Ver todas las funciones próximas</a>
  · <a href="/admin">← Volver al inicio</a>
</p>
```

---

## §5 · Tests

### Unit tests (`packages/shared/src/permissions.test.ts` if exists, else create)

```typescript
describe('visibleNavStructureFor', () => {
  test('admin without roadmap preview: NO placeholders visible', () => {
    const result = visibleNavStructureFor('admin');
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems.length).toBe(12); // 12 live items
    expect(allVisibleItems.every(item => !isPlaceholder(item))).toBe(true);
  });

  test('admin with roadmap preview: ALL placeholders visible', () => {
    const result = visibleNavStructureFor('admin', { includePlaceholders: true });
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems.length).toBe(26); // 12 live + 14 placeholders
  });

  test('chef without roadmap preview: only chef-visible live items', () => {
    const result = visibleNavStructureFor('chef');
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems).toContain('bookings');
    expect(allVisibleItems).toContain('menus' as never).toBeFalsy(); // menus is placeholder
    expect(allVisibleItems).toContain('home');
  });

  test('ROADMAP_STATUS has entry for every NavItem', () => {
    for (const item of NAV_ITEMS) {
      expect(ROADMAP_STATUS[item]).toBeDefined();
    }
  });
});
```

### Smoke test (manual)

1. Login as admin
2. Visit `/admin` → confirm dropdowns ONLY show 12 live items
3. Visit `/admin?roadmap=1` → confirm dropdowns show all 26 items with `·próx` badges
4. Visit `/admin/roadmap` → confirm card grid renders 14 cards grouped by NavGroup
5. Tap a roadmap card → lands on `/admin/coming-soon?feature=X`
6. Verify back-link `/admin/roadmap` in coming-soon footer
7. Mobile 320px: confirm nav dropdown doesn't break, cards stack single-column

---

## §6 · Definition of done

- [ ] `permissions.ts` exports `ROADMAP_STATUS` + `visibleNavStructureFor()`
- [ ] `AdminLayout.astro` uses new helper with `?roadmap=1` URL detection
- [ ] `/admin/roadmap` route accessible to admin + content_editor
- [ ] `/admin/coming-soon` back-link to `/admin/roadmap` added
- [ ] All 4 unit tests pass
- [ ] Smoke test 7 steps pass locally
- [ ] No console errors on `/admin`, `/admin?roadmap=1`, `/admin/roadmap` at 320px/720px/1024px
- [ ] `pnpm test` + `pnpm lint` + `pnpm tsc` green
- [ ] PR opened with description: link to this spec + screenshots before/after of nav

---

## §7 · Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Existing tests reference `visibleNavStructure` (old name) | medium | Keep `visibleNavStructure(role)` as deprecated alias calling `visibleNavStructureFor(role, {})` (no placeholders by default = same behavior as before for non-Alex users) |
| Alex wants placeholders visible by default for himself | low | `?roadmap=1` opt-in covers this. If sticky preference desired → Phase 2 (localStorage) |
| Karina misses functionality "preview the future" | low (per audit §A.5 voting) | `/admin/roadmap` standalone page provides discoverability |
| `ROADMAP_STATUS` map grows stale | medium | Manual edit when feature ships. Add CI check that `live` items match real Astro routes → out of scope v1 |
| Mobile layout `/admin/roadmap` breaks on 320px | medium | Card grid `grid-template-columns: 1fr` at <380px |

---

## §8 · Sequencing

1. CC: branch `feat/i21-kill-nav-placeholders` (~5min)
2. CC: edit `permissions.ts` (+ tests) (~15min)
3. CC: edit `AdminLayout.astro` (~10min)
4. CC: create `/admin/roadmap.astro` (~20min)
5. CC: edit `/admin/coming-soon.astro` back-link (~5min)
6. CC: tests + smoke + tsc + lint (~10min)
7. CC: open PR (~5min)
8. Alex: review + merge (~10min)

Total CC: ~1h. Total Alex: ~10min.

---

## §9 · Out of scope (future iteration)

- Status update UI in admin (e.g., button "mark concierge as in-design")
- Per-feature vote/priority widget for Karina
- Email/Telegram notif when feature transitions to `in-build`
- Roadmap timeline visualization

---

**Spec sealed** by WC-Implementation 2026-05-21 ~05:35 MX, pending Alex Day 3 approval.
