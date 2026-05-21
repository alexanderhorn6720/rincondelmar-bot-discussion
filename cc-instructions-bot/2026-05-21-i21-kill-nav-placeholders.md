# I21 · Kill placeholders del nav · CC DoIt spec (v2 post-synthesis)

**Status**: 🟢 ready post Alex vote · pre-staged · scope reduced post-synthesis
**Workstream**: CC-Bot (`apps/web` + `packages/shared`)
**Effort estimate**: 1h CC (was 1h, scope reduced)
**Source**: §A.5 + §F idea I21 + WC-Platform §A.3 override (NO /admin/roadmap)
**Updated**: 2026-05-21 ~08:20 UTC post-synthesis

---

## §0 · CHANGELOG vs v1

| Change | Razón |
|---|---|
| REMOVE creación de `/admin/roadmap` page | Synthesis §D.1: WC-Platform §A.3 override · roadmap belongs in `vision/`, NOT en operator surface |
| REMOVE `ROADMAP_STATUS` map detalle | No longer needed sin /admin/roadmap page |
| KEEP `?roadmap=1` URL opt-in (Alex preview) | Útil para Alex inspect placeholders sin commit a full page |
| ADD reference a `vision/02-modules-wishlist.md` para discoverability | Per WC-Platform: roadmap lives in repo, not en /admin |
| REDUCE effort 1h → ~45min CC | Sin new page, sin new tests, sin new layout work |

---

## §1 · Context

### Problem

14 placeholders en nav lead a `/admin/coming-soon` (54% de all nav items don't function). Karina sees them every day, wastes taps, learns to avoid el nav. Audit `admin-audit-2026-Q2-v2` §A.4 ranked esto como 🔴 immediate fix.

### Current behavior

`packages/shared/src/permissions.ts` declares 14 items como `PLACEHOLDER_ITEMS`. AdminLayout renders them inline con `·próx` badge. URL `/admin/coming-soon?feature=X` muestra friendly placeholder page.

### Desired behavior (post-synthesis)

- Placeholders NOT visible in nav for Karina daily flow
- `/admin/coming-soon?feature=X` URLs PRESERVED — accessible vía direct URL only (no nav entry)
- Alex preview opt-in via `?roadmap=1` URL query
- Module wishlist documented separately en `vision/02-modules-wishlist.md` (lives en repo, NOT en /admin)
- NO `/admin/roadmap` page creation (synthesis §D.1)

---

## §2 · Explicit scope

### YES

- Remove placeholder rendering from `AdminLayout.astro` dropdowns por default
- Update `permissions.ts` con helper `visibleNavStructureFor({ role, includePlaceholders })`
- `?roadmap=1` URL query enables placeholder rendering en nav (Alex preview opt-in)
- KEEP `/admin/coming-soon?feature=X` page existing (URLs still resolve, useful para Alex direct links)
- (Opcional) ADD `/admin/coming-soon` un footer link a `vision/02-modules-wishlist.md` en GitHub si Alex/Karina quiere ver wishlist

### NO

- DO NOT crear `/admin/roadmap` page (synthesis §D.1 override)
- DO NOT delete `featureDescriptions` map en `coming-soon.astro` (still referenced)
- DO NOT delete `PLACEHOLDER_ITEMS` set (used por `isPlaceholder()` checks elsewhere)
- DO NOT crear `ROADMAP_STATUS` map detallado (sin uso post-synthesis)
- DO NOT change which placeholders exist
- DO NOT implement any of the placeholders themselves
- DO NOT touch role permissions (`NAV_PERMISSIONS`) — only visibility logic

---

## §3 · Closed decisions

- **No /admin/roadmap**: per synthesis §D.1 + WC-Platform §A.3
- **Opt-in query**: `?roadmap=1` (URL state, no cookie, no persistence)
- **Sticky preview**: NOT for v1. Cada visit returns to default (no placeholders).
- **Wishlist location**: `vision/02-modules-wishlist.md` (existing or create separately, NOT en scope de CC pickup este task)
- **Coming-soon page**: preserved as-is + footer link a wishlist (opcional)

---

## §4 · Implementation

### Files to modify

| File | Change |
|---|---|
| `packages/shared/src/permissions.ts` | Add `visibleNavStructureFor()` helper |
| `apps/web/src/layouts/AdminLayout.astro` | Read `?roadmap=1`, pass a helper |
| `apps/web/src/pages/admin/coming-soon.astro` | (opcional) Add footer link to vision/02-modules-wishlist.md GitHub URL |

### `permissions.ts` additions

```typescript
/**
 * New helper — filter nav structure for role, optionally including placeholders.
 * Replaces direct usage of `visibleNavStructure(role)` in AdminLayout.
 *
 * Default behavior: NO placeholders (Karina-friendly daily flow).
 * Opt-in via includePlaceholders: true (Alex preview vía ?roadmap=1).
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

// Backward compat: keep visibleNavStructure(role) as deprecated alias
// returns same as visibleNavStructureFor(role, {}) — NO placeholders default
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

Add small subtle indicator cuando `roadmapPreview` active:
```html
{roadmapPreview && (
  <span class="role-badge" title="Vista preview con placeholders">
    +roadmap
  </span>
)}
```

### `coming-soon.astro` footer addition (opcional)

```html
<p class="coming-soon-back">
  <a href="/admin">← Volver al inicio</a>
  · <a href="https://github.com/alexanderhorn6720/rdm-platform/blob/main/vision/02-modules-wishlist.md"
       target="_blank" rel="noopener">
    Ver wishlist completo en GitHub →
  </a>
</p>
```

**NOTE**: Solo agregar este link si `vision/02-modules-wishlist.md` ya existe o se va a crear como parte de Wave 1. Si NO existe → omit link, dejar solo "Volver al inicio".

---

## §5 · Tests

### Unit tests (`packages/shared/src/permissions.test.ts`)

```typescript
describe('visibleNavStructureFor', () => {
  test('admin sin roadmap preview: NO placeholders visible', () => {
    const result = visibleNavStructureFor('admin');
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems.length).toBe(12); // 12 live items only
    expect(allVisibleItems.every(item => !isPlaceholder(item))).toBe(true);
  });

  test('admin con roadmap preview: ALL placeholders visible', () => {
    const result = visibleNavStructureFor('admin', { includePlaceholders: true });
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems.length).toBe(26); // 12 live + 14 placeholders
  });

  test('chef sin roadmap preview: only chef-visible live items', () => {
    const result = visibleNavStructureFor('chef');
    const allVisibleItems = result.flatMap(g => g.visibleItems);
    expect(allVisibleItems).toContain('bookings');
    expect(allVisibleItems).not.toContain('menus' as never); // menus es placeholder
    expect(allVisibleItems).toContain('home');
  });

  test('backward compat: visibleNavStructure(role) = visibleNavStructureFor(role, {})', () => {
    expect(visibleNavStructure('admin')).toEqual(visibleNavStructureFor('admin'));
  });
});
```

### Smoke test (manual)

1. Login as admin
2. Visit `/admin` → confirm dropdowns ONLY show 12 live items (no `·próx` badges en nav)
3. Visit `/admin?roadmap=1` → confirm dropdowns show all 26 items con `·próx` badges + "+roadmap" indicator
4. Tap a placeholder badge → confirm `/admin/coming-soon?feature=X` still works
5. Visit `/admin/coming-soon?feature=tasks` directamente → page renders correctly
6. Mobile 320px: confirm nav dropdown no rompe sin placeholders

---

## §6 · Definition of done

- [ ] `permissions.ts` exporta `visibleNavStructureFor()` + backward compat alias
- [ ] `AdminLayout.astro` uses new helper con `?roadmap=1` URL detection
- [ ] `coming-soon.astro` preserved (URLs still resolve)
- [ ] (Opcional) Footer link a vision wishlist agregado si file existe
- [ ] All 4 unit tests pass
- [ ] Smoke test 6 steps pass locally
- [ ] No console errors en `/admin`, `/admin?roadmap=1`, `/admin/coming-soon?feature=X` at 320px/720px/1024px
- [ ] `pnpm test` + `pnpm lint` + `pnpm tsc` green
- [ ] PR opened con description: link to this spec + before/after screenshots del nav

---

## §7 · Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Existing tests reference `visibleNavStructure` (old name) | medium | Keep `visibleNavStructure(role)` como deprecated alias calling `visibleNavStructureFor(role, {})` (same default behavior) |
| Alex quiere placeholders visible by default | low | `?roadmap=1` opt-in covers this. Sticky preference → Phase 2 (localStorage) si demand emerge |
| Karina pregunta "qué viene en el futuro" | low | Alex direct response + vision wishlist en GitHub. NO surface en /admin per philosophy |
| Mobile layout rompe sin placeholders | very low | Nav structure unchanged, solo content filter |
| Backward compat break · alguien call `visibleNavStructure` con expected placeholders | low | Default `{}` = no placeholders = same as before (placeholders nunca eran shown a non-admin) |

---

## §8 · Sequencing

1. CC: branch `feat/i21-kill-nav-placeholders` (~5min)
2. CC: edit `permissions.ts` + tests (~15min)
3. CC: edit `AdminLayout.astro` (~10min)
4. CC: (opcional) edit `coming-soon.astro` footer link (~5min)
5. CC: tests + smoke + tsc + lint (~10min)
6. CC: open PR linking ADR-004 (~5min)
7. Alex: review + merge (~5min)

Total CC: ~45min. Total Alex: ~5min.

---

## §9 · Out of scope (future iteration)

- Status update UI en admin (e.g., button "mark concierge as in-design") — debe vivir en vision/, no en /admin
- Per-feature vote/priority widget para Karina — uso I2 feedback mechanism (Wave 2)
- Email/Telegram notif cuando feature transitions to `in-build` — Phase 2
- Roadmap timeline visualization — vive en vision/ o GitHub Projects
- Sticky preview preference — Phase 2 localStorage

---

## §10 · Coordination con Wave 1

I21 es uno de 8 items del cluster Wave 1 polish sprint:

| Item | Effort CC |
|---|---|
| **I21 kill placeholders** | 45min |
| I27 pending welcomes badge | 1h |
| I26 today/tomorrow filter | 1.5h |
| F.7 InboxView soft-404 fix | 15min |
| F.5 form field name attrs | 10min |
| F.2 karina-training 320px overflow | 30min |
| I13+I14 status badge + reset preview | 4h |
| I28 bot-metrics karina summary card | 2h |

Sub-cluster sugerencia: ship F.7+F.5+F.2+I21 juntos como "tech debt sweep" PR (~1.5h cluster). Después I27+I26 cluster (~2.5h). Después I13+I14 (4h standalone). Después I28 (2h standalone). Total Wave 1 ≈ 10h CC (~2 días).

---

**Spec sealed v2** por WC-Implementation 2026-05-21 ~08:20 UTC post-synthesis. Pending Alex Day 3 vote → CC pickup. NO /admin/roadmap per synthesis §D.1.
