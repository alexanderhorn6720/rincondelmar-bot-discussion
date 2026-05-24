# F3 Staff PWA — Spec Expansion & Migration Audit (Draft)

**Status**: Draft (open-for-alex-vote). WC preliminary recommendations marked. Alex final.

**Relation**: Companion draft to canonical [rdm-platform/foundations/F3-staff-pwa.md](../../../platform/foundations/F3-staff-pwa.md) (Accepted per ADR-002 2026-05-20).

**Purpose**:
1. Audit F3 spec migration claims (0043/0044) against rdm-bot filesystem reality (analog to thread/186 B1 for F2, foundations/F1-events-bus-spec.md for B4).
2. Verify auth flow + service worker scope + VAPID setup + sideload UX claims against current `apps/web` reality.
3. Surface staged amendments for WC-Platform to fold into canonical spec post-Alex vote.

**Boundary**: This draft lives in rdm-discussion. NO modification to `rdm-platform/foundations/F3-staff-pwa.md` (CC read-only per thread/184 §6).

**Authoría**: CC worktree B (Opus 4.7), run thread/184, task B5. Asume F1 reservation 0048-0049 per foundations/F1-events-bus-spec.md (B4), F2 reservation 0047 per thread/186 (B1).

---

## §0. Why this draft exists

The canonical F3 spec is 423 lines and exhaustive: stack, routing, auth flow, service worker, push notifications, iOS quirks, subdomain SSO, roles, onboarding, acceptance criteria (20 items), rollout (Day 0-5), 7 design-vs-alternatives, follow-up specs (F3.1, F3.2).

Reality check confirms canonical spec is **largely accurate**, but four areas need amendments — all minor, none architectural:

| Area | Status in canonical | Amendment needed |
|---|---|---|
| Migration slots (0043, 0044) | Reserved | **COLLISION — both already consumed**. Remap to 0050+ (after F1 0048-0049 reservation per B4) |
| Auth flow (email magic link via Resend) | Designed | Verified: `apps/web` LIVE with `packages/auth` + Resend transport. No `cookieDomain` set currently — session rotation breaking change confirmed |
| Service Worker scope | `@vite-pwa/astro@^0.4.0` | Verified: `apps/web/public/sw.js` LIVE with hand-rolled minimal SW (network-first HTML, cache-first /_astro). Spec mentions this fallback exists — fine |
| VAPID + push | `web-push` + nodejs_compat_v2, fallback `@negrel/webpush` | Verified: `nodejs_compat_v2` LIVE on `apps/web/wrangler.toml`. Day-0 spike still needed (no current push code) |

True open issue: migration numbering (same class as F1+F2).

---

## §1. Migration slot audit (analog to B1 F2 + B4 F1)

### F3 spec claims (rdm-platform/foundations/F3-staff-pwa.md)

| Slot | Table | Spec ref |
|---|---|---|
| 0043 | `push_subscriptions` | §2.5 (line 160) |
| 0044 | `user_roles` (or `ALTER users ADD COLUMN role`) | §3.1 (line 219) |

### Filesystem reality (rdm-bot/migrations/, 2026-05-23)

| Slot | Reality |
|---|---|
| 0043 | `booking_captures` (shipped) |
| 0044 | `outreach_templates` (shipped) |
| 0045 | `mp_payments` (shipped) |
| 0046 | `cost_telemetry` (shipped) |
| 0047 | RESERVED `cron_heartbeats` (F2 per thread/186 B1) |
| 0048 | RESERVED `booking_lifecycle_events` (F1 per foundations/F1-events-bus-spec.md B4) |
| 0049 | RESERVED `lifecycle_outbox` (F1 per B4) |
| 0050 | **LIBRE** |
| 0051 | **LIBRE** |

### Proposed remap

| F3 spec original | Proposed new slot | Conditional |
|---|---|---|
| 0043 → `push_subscriptions` | **0050** | If F1+F2 ship in expected order |
| 0044 → `user_roles` | **0051** | Sequential |

**Voto WC preliminar (en F3 context)**: same as B4 — use `NNNN` placeholder + `scripts/new-migration.sh` at ship time. F3 ships LAST in foundations order (per ADR-002 §2), so by the time CC starts F3, F1+F2 are committed. Better to read live filesystem than hardcode.

*WC preliminary, Alex final.*

Razón:
- F3 ships after F1+F2; if anything in pipeline shifts (e.g., F2 chosen Opción B reusing bot_config = no F2 migration), F3 slots also shift. Hardcoding 0050+0051 today is brittle.
- Both F3 migrations are additive: `push_subscriptions` is a new table, `user_roles` is `ALTER users ADD COLUMN role TEXT DEFAULT 'employee'` (DEFAULT clause makes it non-destructive on existing rows).
- §3.1 spec note already says "number may shift if F1/F2 take more migrations" — embracing this in canonical spec text formalizes the practice.

**ALTER TABLE consideration** (anti-pattern check):

Spec §6 thread/184 lists ALTER TABLE as prohibited "durante run (multi-agent unsafe)". F3 §3.1 proposes `ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'employee'`.

This is NOT an anti-pattern violation when applied during F3 ship (post-autonomous-run, post-F1, post-F2). Spec/184 §6 anti-pattern targets ALTER during the multi-agent autonomous run, when CC-Bot + CC-Discussion + CC-Data may concurrently touch D1 schemas. F3 ship is a single CC session, fully sequenced.

**Voto WC preliminar**: F3 spec §3.1 should add a note: "ALTER TABLE `users` ADD COLUMN `role` is acceptable when F3 ships (single-agent, sequential). If F3 ships during a multi-CC run, escalate per spec/184 §6."

If Alex prefers stricter avoidance of ALTER even outside multi-agent runs: F3 §3.1 alternative path = new `user_roles` table (FK to users.id, role TEXT, property TEXT NULL for per-property scoping). Effort delta: ~30 min more for join queries throughout staff PWA. Pro: no ALTER, supports per-property scoping cleanly. Con: schema slightly more complex.

### Voto WC preliminar on the schema shape

**Recommend: separate `user_roles` table, not ALTER**. Razón:
- Per-property scoping is already in F3 §3.1: "single-role schema; per-property scoping is added when M4 lands". Separate table now anticipates M4 cleanly; ALTER + later ALTER is two changes for one outcome.
- Schema-wise, separate table avoids edge cases around NULL coercion (existing rows getting `'employee'` by default may be wrong for some — e.g., Alex's row should be `admin`).
- Cost is one extra JOIN per session lookup; negligible.

If Alex prefers ALTER: clarification needed on what Alex's existing user row's role becomes (currently no `role` column).

---

## §2. Auth flow verification (canonical §2.3 vs reality)

### Canonical claim

> "F3 ships email magic link via Resend (existing infra). Phone path deferred to F3.1."

### Reality check

| Component | Status | File |
|---|---|---|
| `packages/auth` exists | YES | `c:/dev/rdm/dev/bot/packages/auth/` |
| Better Auth + D1 magic link plugin LIVE | YES | spec §1 confirms; `apps/web/src/lib/auth.ts` wraps `@rdm/auth` |
| Resend email transport LIVE | YES | `apps/web/src/lib/email.ts` (validated via `sendMagicLinkEmail` import) |
| `BETTER_AUTH_SECRET` env on apps/web | YES | spec §1 confirms; canonical wrangler.toml refs |
| `cookieDomain: '.rincondelmar.club'` SET on apps/web | **NO** | grep `cookieDomain` across `packages/auth/src/` returns zero matches |

**Implication confirmed**: F3 ship REQUIRES cookieDomain rotation on `apps/web`. This invalidates ALL existing sessions. Spec §2.7 + §6 Day 0 step 6 already document this; reality check confirms the breaking change is necessary.

### Karina-impact callout

Current users with active sessions on `rincondelmar.club/admin/*`:
- Alex (administrator role)
- Karina (content_editor role per spec §3.1 table)
- Any other admin role user

All MUST re-login post-F3 deploy. Better Auth magic link via Resend; UX similar to first-time login.

**Voto WC preliminar**: amend canonical F3 §6 Day 0 step 7 to be more explicit:
> "7. Notify Karina/Alex that existing apps/web sessions will reset on next deploy. **CC must send WhatsApp message to Karina with screenshot of new login flow 24h before deploy**. Karina re-login confirmed before F3 ships to staff PWA."

Effort: ~5 min comms (Alex does), but criticality of getting Karina re-logged-in correctly is high.

---

## §3. Service Worker scope verification (canonical §2.4 vs reality)

### Canonical claim

> "Via `@vite-pwa/astro@^0.4.0` ... Fallback: hand-roll Workbox config per existing `apps/web/public/sw.js` pattern if integration brittle (+2-3h)"

### Reality check

| Component | Status | File |
|---|---|---|
| `apps/web/public/sw.js` LIVE | YES | hand-rolled, 50+ lines |
| SW strategy | Network-first HTML, cache-first `/_astro/*`, skip `/api/*` | matches F3 §2.4 strategy |
| Service Worker version | `rdm-sw-v1` | canonical |
| Astro 5 SW build hook compatibility | NOT verified by me (would require build in apps/staff scaffold) | Day-0 spike risk |

**Finding**: the hand-rolled fallback path is already proven in `apps/web`. CC can replicate this exact pattern to `apps/staff` if `@vite-pwa/astro@^0.4.0` integration is problematic.

### Implication for F3 implementation

The fallback path (hand-roll) is cheaper than spec claims. CC 146 §F3.Q5 estimated +2-3h for fallback; reality is closer to +1-2h (copy + adapt routes).

**Voto WC preliminar**: amend canonical F3 §2.4:
> "Fallback strategy: copy `apps/web/public/sw.js` pattern (~50 lines, network-first HTML / cache-first /_astro / skip /api) into `apps/staff/public/sw.js`. Adapt OFFLINE_URL and PRECACHE paths. Validated pattern, +1-2h vs +2-3h previously estimated."

---

## §4. VAPID + Web Push verification (canonical §2.5)

### Canonical claim

> "`web-push` npm package via `nodejs_compat_v2` runtime flag. Day 0 spike confirms; fallback `@negrel/webpush` (Workers-native via Web Crypto, +1-2h)"

### Reality check

| Component | Status |
|---|---|
| `nodejs_compat_v2` flag LIVE on apps/web wrangler.toml | YES (line 9 per grep) |
| `nodejs_compat_v2` flag LIVE on apps/worker-bot, apps/worker-pago | YES (per F1 §3.4 reference) |
| `web-push` package currently installed | NO (not in `pnpm-workspace.yaml` or apps/web/package.json) |
| `@negrel/webpush` package currently installed | NO |
| Existing push notification code anywhere | NO (zero matches `web-push`, `webpush`, `pushSubscription` in apps/) |

**Implication**: zero existing push code. Day-0 spike for `web-push` runs from a clean slate; fallback to `@negrel/webpush` is also from clean slate. Either path is uncontested by existing code.

### Risk: VAPID key management

F3 spec §6 Day 0 step 5 says generate VAPID keypair, store `VAPID_PUBLIC_KEY` (env var) + `VAPID_PRIVATE_KEY` (secret). Once issued, rotating VAPID keys invalidates ALL existing push subscriptions — every device must re-subscribe.

Spec §6 Day 4 mentions "VAPID keys runbook + rotation procedure" but doesn't define what triggers rotation.

**Voto WC preliminar**: amend canonical F3 §2.5 with explicit rotation policy:
> "VAPID keys are stable for the lifetime of the staff PWA. Rotation triggered ONLY by (a) suspected key compromise OR (b) `web-push` library replacement. Rotation procedure: announce 7 days ahead, deploy new keys, prompt all empleados to re-grant push permission via in-app banner. Document in `rdm-bot/docs/spec/21-apps-staff-shell.md` runbook section."

This is a low-effort doc amendment that prevents accidental rotation behavior during routine F3 maintenance.

---

## §5. iOS sideload UX (canonical §2.6 + onboarding §3.2)

### Canonical claim

> "iOS Safari 16.4+ supports Web Push only after PWA installed to home screen ... 'Add to Home Screen' instruction must be shown explicitly to iOS users (no install prompt)"

### Reality check

No existing iOS PWA install flow in rdm-bot codebase (validated via grep `Add to Home Screen`, `agregar a inicio`).

### Onboarding flow (canonical §3.2 Alex-only provisioning)

Canonical: Alex updates `STAFF_EMAILS` env var in `apps/staff/wrangler.toml`, deploys, sends WhatsApp link to empleado.

**Friction**: every new hire = Alex commit + deploy. F3.2 spec adds UI when this exceeds 1/month.

### Open question

Current empleados (per memory): 18 of 18 have @rincondelmar.club email. F3 ship serves this group. But:

- If empleado loses phone access mid-shift (battery dies, phone breaks), they can re-login from another device with magic link — works
- If empleado forgets which iOS gesture to use for install, no recovery path inside the app — spec acknowledges this implicitly

**Voto WC preliminar**: F3 spec §3.2 ships with a `/yo/instalar` page that:
- Detects userAgent (iOS Safari vs Android Chrome vs other)
- Shows screen-recorded GIF (3-5 sec) of the platform-specific install gesture
- Is reachable from any logged-in state via the `/yo` tab

Effort: ~1h CC additional on Day 3. Eliminates "I forgot how to install" support load.

---

## §6. Open question: cron impact on worker-pago

F3 spec doesn't add any new cron to worker-pago. But:
- F1 adds 2 crons (dispatcher every 2 min + hourly scanner per B4 spec)
- F2 adds 0 new crons (heartbeats are writes at end of existing crons)
- F3 adds 0 new crons (push send is fired by F1 consumer logic, not cron)

Post-foundations total in `apps/worker-pago`: 5 existing + 2 F1 = **7 crons**. Acceptable per ADR-003 §2.1 (CF doesn't publish hard cap). No additional verification step needed in F3 acceptance.

**Voto WC preliminar**: no F3 spec amendment for crons (verification belongs to F1 per B4 §2 acceptance criterion #13).

---

## §7. Summary: amendments to canonical F3 spec

Patch to apply by WC-Platform in `rdm-platform/foundations/F3-staff-pwa.md` post-Alex vote:

| Sección | Cambio |
|---|---|
| §1 "What F3 adds" migration column | `migration 0043` → `migration NNNN (expected 0050)`; `migration 0044` → `migration NNNN (expected 0051)` |
| §2.5 SQL comment | `migrations/0043_push_subscriptions.sql` → `migrations/NNNN_push_subscriptions.sql` (slot via `scripts/new-migration.sh`) |
| §3.1 SQL comment + schema choice | Same NNNN treatment. **Schema recommendation**: prefer separate `user_roles` table over `ALTER TABLE users ADD COLUMN role` (per §1 above). Anticipates M4 per-property scoping, avoids NULL coercion edge cases for existing users. |
| §2.4 fallback effort estimate | `+2-3h` → `+1-2h` (validated existing pattern in apps/web/public/sw.js) |
| §2.5 VAPID rotation policy (NEW) | Add explicit triggers (compromise / library replacement), rotation procedure (7-day announce, re-grant flow), reference in §6 Day 4 documentation |
| §3.2 add `/yo/instalar` page (NEW, optional) | iOS+Android install gesture screen-recorded GIFs; ~1h additional Day 3 |
| §6 Day 0 step 7 | Explicit WhatsApp comms to Karina 24h pre-deploy + re-login confirmation |

---

## §8. Bloqueador downstream

- F3 ship hard-blocked by F1 ship (per ADR-002 §2: F2 → F1 → F3 → M1)
- F3 ship hard-blocked by Q3.1 G7 Alex vote (thread/148)
- F3 ship hard-blocked by Day 0 Alex pre-flight (Pages project + DNS + secrets + VAPID, ~15 min)
- This draft itself does NOT block anything; surfaces amendments for inclusion when F3 ship slot opens

---

## §9. Definition of done — B5

- [x] Read canonical F3 spec (423 lines, exhaustive)
- [x] Audit migration slot collision (0043/0044 already consumed; remap to NNNN with expected 0050/0051)
- [x] Verify auth flow against `apps/web` reality (confirmed `packages/auth` LIVE; `cookieDomain` NOT set → session rotation breaking change confirmed)
- [x] Verify service worker against existing `apps/web/public/sw.js` (hand-rolled fallback path lower-effort than spec estimated)
- [x] Verify VAPID setup compat (nodejs_compat_v2 LIVE; no existing push code; Day-0 spike clean slate)
- [x] Verify iOS sideload UX (no existing flow; ~1h /yo/instalar page recommendation)
- [x] List amendments to apply post-Alex vote (§7)
- [x] Schema shape recommendation: user_roles table over ALTER (avoids anti-pattern + anticipates M4)
- [x] Status `open-for-alex-vote`
- [x] Boundary respected: NO modification to rdm-platform

**Next action**: PR review + Alex vote. Post-vote, WC-Platform applies §7 patch to canonical F3 spec.

---

## §10. Open questions for Alex

1. **Schema shape**: ALTER users (canonical) vs separate `user_roles` table (this draft's recommendation)?
   - WC preliminary: separate table.
2. **ALTER acceptability outside multi-agent run**: F3 ships single-CC; is ALTER acceptable post-run? OR strict avoidance always?
   - WC preliminary: F3 ships single-CC and post-run; ALTER acceptable. But separate table is preferred anyway for M4 readiness.
3. **VAPID rotation policy**: confirm rotation triggers (compromise / library swap) and 7-day announce window?
   - WC preliminary: yes per §4.
4. **`/yo/instalar` install gesture page**: ship in F3 (+1h) or defer to F3.0.1 micro-spec?
   - WC preliminary: ship in F3. Low effort, eliminates a class of support friction.
5. **Karina re-login comms**: WhatsApp 24h pre-deploy + confirmation handshake?
   - WC preliminary: yes per §2.

---

## See also

- [rdm-platform/foundations/F3-staff-pwa.md](../../../platform/foundations/F3-staff-pwa.md) (canonical, Accepted)
- [rdm-platform/foundations/README.md](../../../platform/foundations/README.md) §F3 (summary)
- [foundations/F1-events-bus-spec.md](./F1-events-bus-spec.md) (sibling B4 — F1 migration remap, consumer reuse of F3 push)
- [threads/186-CC-f2-migration-remap.md](../threads/186-CC-f2-migration-remap.md) (sibling B1 — F2 remap)
- [threads/148](../threads/148) (Alex vote context, §A items 5/6/7)
- [threads/146](../threads/146) (CC pre-flight F3.Q1-Q7)
- [thread/184](../threads/184) §3 B5 (task parent)
- `rdm-bot/apps/web/public/sw.js` (validated SW pattern for F3 fallback)
- `rdm-bot/packages/auth/` (Better Auth current setup; cookieDomain absence verified)
