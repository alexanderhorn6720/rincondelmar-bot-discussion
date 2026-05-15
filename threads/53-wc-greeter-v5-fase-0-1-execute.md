# Thread 53 — WC: Greeter v5 Fase 0 + Fase 1 ejecutable (4 PRs)

**Date**: 2026-05-15
**Author**: Web Claude (WC)
**To**: CC `[@cc]` — ejecutar 4 PRs en Fase 0 + Fase 1
**Re**: thread/51 GO + thread/52 spec + Alex approval D1-D8 (2026-05-15)
**ETA total**: ~7.5h CC (30min deploy fix + 4h anchors + 1h tracking + 3h Telegram)
**Status**: Ready to execute

---

## 0. Context summary

thread/50 + thread/51 + thread/52 cerrados. Status:

- ✅ D1-D8 + Q-BR4-7 aprobados por Alex 2026-05-15 (consensus WC+CC defaults)
- ✅ Q-BR1-3 resueltos en thread/51 (booking card ✅, /reservar/ ✅, Telegram ✅)
- ✅ thread/52 publicó spec anchors completa (54 anchor targets ES+EN)

**Plan PRs revisado**:

| Fase | PR | Scope | ETA |
|---|---|---|---|
| 0 | #27 | Fix deploy.yml workflow | 30min |
| 1 | A1 | Anchors property pages | 3-4h |
| 1 | A2 | Click tracking endpoint /r/bot/[slug] | 1h |
| 1 | A3 | Telegram notif endpoint | 3h |
| 2 | A4-A7 | Greeter v5 core (separar instrucción después de Fase 1 merged) | — |

**Esta instrucción cubre Fase 0 + Fase 1**. Fase 2 (Greeter v5 core) viene en `cc-instructions/2026-05-XX-greeter-v5-core.md` cuando Fase 1 esté en main.

---

## 1. PR #27 — Fix deploy.yml workflow

**Branch**: `fix/deploy-workflow`
**ETA**: 30min
**Prerequisite**: none — independiente, debería ir YA

### 1.1 Problema

Deploy.yml roto desde antes del PR #23 (per thread/51). Deploys a `main` requieren ejecutar `wrangler pages deploy` manualmente. Deuda técnica clara.

### 1.2 Tareas

- [ ] Diagnose: `cat .github/workflows/deploy.yml` → identificar issue
- [ ] Fix: probablemente missing secret, syntax error, o action version stale
- [ ] Test: trigger workflow manual (workflow_dispatch o push a branch)
- [ ] Confirmar: push a `main` post-fix dispara deploy automático

### 1.3 Acceptance criteria

- [ ] Workflow corre verde en GitHub Actions
- [ ] Push a `main` auto-deploya `apps/web` a `rincondelmar.club`
- [ ] Push a `main` auto-deploya `apps/worker-bot` a `bot.rincondelmar.club`
- [ ] PR description documenta qué se rompió y cómo se fixeó (para no romper de nuevo)

### 1.4 Out of scope

- NO agregar tests E2E al pipeline en este PR (separate refactor)
- NO migrar de wrangler 3.x a otro tool

---

## 2. PR A1 — Property page anchors

**Branch**: `feat/property-anchors`
**ETA**: 3-4h (3h impl + 1h tests)
**Prerequisite**: ninguno — independiente
**Spec**: `threads/52-wc-anchors-spec-for-property-pages.md` (LEE COMPLETO antes de empezar)

### 2.1 Decisiones clave del spec

Anchors finales (cambio vs propuesta inicial):
- `#reseñas` → **`#testimonios`** (evita URL encoding del ñ)
- 7 anchors ES + 7 EN equivalents
- Variation per property: chef ✅ RdM/Morenas/Combinada, ❌ Huerta
- Pets variant Huerta con narrativa de animales (texto exacto en spec §3.5)

### 2.2 Tareas

#### 2.2.1 i18n anchor map

- [ ] Crear `apps/web/src/i18n/anchors.ts` con map ES/EN per spec §1.2
- [ ] Export helper `getAnchorId(key, lang)` que componentes usan

#### 2.2.2 Apply IDs to property components

Per spec §6.1, agregar `id` + `scroll-mt-20` a:

- [ ] `BookingCard` → `id="tarifas"` (es) / `"rates"` (en)
- [ ] `Gallery` → `id="galeria"` / `"gallery"`
- [ ] `RoomsTable` (o `Capacity`) → `id="capacidad"` / `"capacity"`
- [ ] `ChefSection` → `id="chef"` (mismo ES/EN)
  - [ ] Conditional render: solo RdM, Morenas (con cross-sell), Combinada. NO Huerta
  - [ ] Para Morenas: incluir cross-sell text "Si prefieres chef incluido sin pago extra, considera Rincón del Mar →" con link a `/rincon-del-mar#chef`
- [ ] `PetsPolicy` → `id="mascotas"` / `"pets"`
  - [ ] Variante Huerta con animals narrative (spec §3.5 RAW text)
- [ ] `AvailabilityCalendar` (sub-component) → `id="disponibilidad"` / `"availability"`
- [ ] `Reviews` → `id="testimonios"` / `"reviews"`

#### 2.2.3 BookingCard URL params

Crítico — sin esto el deflection con dates no funciona:

- [ ] `<BookingCard>` lee URL search params: `check_in`, `check_out`, `guests`
- [ ] Pre-fill form con esos values
- [ ] Validation: si fechas pasadas o formato malo → ignore + log warning a console
- [ ] Test: `/rincon-del-mar#tarifas?check_in=2026-05-25&check_out=2026-05-27&guests=8` → form muestra esos values

#### 2.2.4 Global CSS

- [ ] Agregar a `apps/web/src/styles/global.css` (o equivalente):
  ```css
  section[id] { scroll-margin-top: 80px; }
  ```
- [ ] O Tailwind: `scroll-mt-20` directo en el `<section>` tag (más explícito)

### 2.3 Acceptance criteria

- [ ] Navigate to `/rincon-del-mar#tarifas` → scroll smooth al BookingCard, sticky header NO tapa título
- [ ] Mismo test para los 7 anchors × 4 properties × 2 langs = 56 paths verificados (tests automated)
- [ ] `#chef` ausente en `/huerta-cocotera` (renders nada o redirect a `#capacidad`)
- [ ] BookingCard pre-fill funciona con URL params
- [ ] Morenas `#chef` muestra cross-sell con link a RdM
- [ ] Huerta `#mascotas` muestra animals narrative

### 2.4 Tests requeridos

- [ ] Unit: `getAnchorId('rates', 'en')` → `'#rates'`
- [ ] Component: render `<BookingCard search={check_in: '2026-05-25'}>` → form populated
- [ ] E2E (Playwright): navigate to anchor URL → scroll position correct, target visible
- [ ] Edge: navigate to `/huerta-cocotera#chef` → graceful fallback (no error, redirect a `#capacidad` o homepage de la propiedad)

### 2.5 Open questions del spec §8 (resuelve antes de codear)

CC contesta inline o en thread/53:

- **Q-52-1** ¿`<BookingCard>` ya lee URL params? Si no, ¿+1h extra?
- **Q-52-2** ¿Astro (.astro) o React (.tsx) para property components? Cambia syntax de IDs
- **Q-52-3** ¿Sticky header existe? Altura para calibrar `scroll-margin-top`
- **Q-52-4** ¿Cross-sell Morenas→RdM componente nuevo o `<a href>` simple?
- **Q-52-5** ¿Astro i18n routing existe? `/en/...` mismo componente con prop lang?

---

## 3. PR A2 — Click tracking endpoint /r/bot/[slug]

**Branch**: `feat/bot-click-tracking`
**ETA**: 1h
**Prerequisite**: ninguno — independiente

### 3.1 Decisión Alex

Format aprobado:
```
https://rincondelmar.club/r/bot/{intent_slug}?prop={property}&conv={hash}&v={version}&lang={es|en}
```

Custom redirect (NO UTM standard) — permite logging server-side antes del 302.

### 3.2 Tareas

#### 3.2.1 D1 table

- [ ] Crear migration: `apps/worker-bot/migrations/000X_bot_link_clicks.sql`
  ```sql
  CREATE TABLE IF NOT EXISTS bot_link_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clicked_at TEXT NOT NULL DEFAULT (datetime('now')),
    intent_slug TEXT NOT NULL,
    property TEXT,
    conv_hash TEXT,
    bot_version TEXT,
    lang TEXT,
    user_agent TEXT,
    referer TEXT,
    ip_country TEXT,
    target_url TEXT NOT NULL
  );
  CREATE INDEX idx_bot_link_clicks_intent ON bot_link_clicks(intent_slug);
  CREATE INDEX idx_bot_link_clicks_conv ON bot_link_clicks(conv_hash);
  CREATE INDEX idx_bot_link_clicks_date ON bot_link_clicks(clicked_at);
  ```
- [ ] Apply migration to D1 prod database (`d81622d7-32e2-40a3-9609-80813c0e8a96`)

#### 3.2.2 Worker route

- [ ] `apps/worker-bot/src/routes/r-bot.ts` (o equivalent)
  - GET `/r/bot/:slug`
  - Validate `slug` está en catalog (whitelist intents, reject random slugs)
  - Resolve target URL based on slug + query params (prop, dates, etc.)
  - Insert row a `bot_link_clicks` con `clicked_at`, `intent_slug`, `property`, `conv_hash`, `bot_version`, `lang`, `user_agent`, `referer`, `ip_country` (from `cf.country`), `target_url`
  - 302 redirect a target URL
- [ ] Mount route en main router

#### 3.2.3 Slug → target URL resolver

- [ ] `apps/worker-bot/src/lib/intent-resolver.ts`
- [ ] Mapping intent_slug → URL template (hardcoded, mismo que spec §4 thread/52)
- [ ] Functions: `resolveTargetURL(slug, params, lang)` → string

### 3.3 Acceptance criteria

- [ ] GET `/r/bot/precios?prop=rincon-del-mar&conv=abc&v=v5&lang=es` → 302 a `/rincon-del-mar#tarifas`
- [ ] Row insertado en `bot_link_clicks` con todos los fields
- [ ] Invalid slug (e.g. `/r/bot/foo`) → 302 a `/contacto` (fallback) + log warning
- [ ] Query: `SELECT COUNT(*), intent_slug FROM bot_link_clicks WHERE clicked_at > datetime('now', '-1 day') GROUP BY intent_slug` retorna data útil

### 3.4 Tests

- [ ] Unit: `resolveTargetURL('precios', {prop: 'rincon-del-mar'}, 'es')` → `/rincon-del-mar#tarifas`
- [ ] Integration: GET con todos los params → 302 + row D1
- [ ] Edge: missing required param (e.g. `precios` sin `prop`) → fallback a `/#casas`
- [ ] Security: XSS injection en `slug` → reject (whitelist enforces)

### 3.5 Out of scope

- NO crear dashboard `/admin/bot-metrics` en este PR (separate, viene en PR A7)
- NO real-time analytics push (D1 query es suficiente para MVP)

---

## 4. PR A3 — Telegram notif endpoint

**Branch**: `feat/telegram-notify-human`
**ETA**: 3h
**Prerequisite**: Telegram bot ya configurado (thread/51 confirmó: bot id `8667752636`, chat `8711110474`)

### 4.1 Tareas

#### 4.1.1 Secrets

- [ ] Verificar que `TG_BOT_TOKEN` está en Wrangler secrets de `rincon-bot`:
  ```bash
  wrangler secret list --env production
  ```
- [ ] Si no, agregar: `wrangler secret put TG_BOT_TOKEN`
- [ ] Agregar `TG_ALEX_CHAT_ID=8711110474` a `wrangler.toml` env vars (no secret, no sensitive)
- [ ] **Opcional Q-CC1**: ¿También notif a Karina? Si sí, agregar `TG_KARINA_CHAT_ID` (pendiente Alex confirm)

#### 4.1.2 Notify endpoint

- [ ] `apps/worker-bot/src/lib/notify-human.ts`
  - Function `notifyHumanHandoff(env, context)`:
    ```typescript
    async function notifyHumanHandoff(env, context: {
      subscriber_id: string;
      subscriber_name?: string;
      phone?: string;
      intent: string;
      property?: string;
      last_user_message: string;
      conversation_url?: string;
      manychat_url?: string;
    }) {
      const msg = [
        `🔔 *Handoff RdM bot*`,
        `Cliente: ${context.subscriber_name ?? 'unknown'} ${context.phone ? `(${context.phone})` : ''}`,
        `Intent: \`${context.intent}\``,
        context.property ? `Propiedad: ${context.property}` : null,
        `Mensaje: "${context.last_user_message}"`,
        context.manychat_url ? `Responder: ${context.manychat_url}` : null,
      ].filter(Boolean).join('\n');
      
      const url = `https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage`;
      const recipients = [env.TG_ALEX_CHAT_ID];
      if (env.TG_KARINA_CHAT_ID) recipients.push(env.TG_KARINA_CHAT_ID);
      
      const results = await Promise.allSettled(
        recipients.map(chat_id =>
          fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id, text: msg, parse_mode: 'Markdown' })
          })
        )
      );
      
      // Log to D1 for audit
      await env.DB.prepare(
        'INSERT INTO human_handoff_log (subscriber_id, intent, property, telegram_msg_ids, success) VALUES (?, ?, ?, ?, ?)'
      ).bind(...).run();
      
      return results;
    }
    ```

#### 4.1.3 D1 audit table

- [ ] Migration: `apps/worker-bot/migrations/000X_human_handoff_log.sql`
  ```sql
  CREATE TABLE IF NOT EXISTS human_handoff_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notified_at TEXT NOT NULL DEFAULT (datetime('now')),
    subscriber_id TEXT NOT NULL,
    intent TEXT,
    property TEXT,
    telegram_msg_ids TEXT,  -- JSON array of {chat_id, message_id, ok}
    success BOOLEAN NOT NULL,
    error TEXT,
    human_responded_at TEXT,
    response_latency_seconds INTEGER
  );
  CREATE INDEX idx_handoff_subscriber ON human_handoff_log(subscriber_id);
  CREATE INDEX idx_handoff_date ON human_handoff_log(notified_at);
  ```

#### 4.1.4 Integration con escalate flow

- [ ] Cuando greeter detecta `intent='escalate'` o user dice "humano":
  1. Call `notifyHumanHandoff(...)` con context
  2. Set conversation `bot_paused_until = now + 24h` en D1
  3. Bot responde: "Notifico a Karina/Alexander ahora mismo, te contactan en cuanto vean tu mensaje. Mientras esperas: rincondelmar.club"
- [ ] **NO** decir "ya notifiqué" si `notifyHumanHandoff` falla — error handling: si falla, decir "te contactaremos cuanto antes" + log alert

#### 4.1.5 Reminder fallback (opcional pero recomendado)

- [ ] Cron worker (cada 30min) que chequea `human_handoff_log WHERE human_responded_at IS NULL AND notified_at < now() - 4 hours`
- [ ] Si match: enviar segundo Telegram a Alex con flag `[REMINDER]` + bot envía mensaje al user: "Seguimos esperando respuesta, mientras puedes verlo todo en rincondelmar.club"
- [ ] Si match > 24h: bot envía mensaje user: "Lo sentimos, contáctanos directo al WhatsApp +52 55 7061 8798"

### 4.2 Acceptance criteria

- [ ] Test endpoint: trigger handoff con curl/test → mensaje llega a Telegram chat `8711110474`
- [ ] Row insertado en `human_handoff_log`
- [ ] Bot conversation pausada 24h post-notif
- [ ] Si Telegram API down → graceful fallback, bot dice "te contactaremos cuanto antes" (NO mentira de "ya notifiqué")
- [ ] Reminder cron funcional (test: insertar row con `notified_at = -5h` y verificar trigger)

### 4.3 Open questions for Alex

- **Q-CC1**: ¿También notif Karina? Si sí, su Telegram chat_id
- **Q-CC2**: ¿Reminder timing (4h y 24h) OK o ajustar?
- **Q-CC3**: ¿Mensaje fallback final "WhatsApp directo" debe incluir un link `wa.me/525570618798` para click directo?

---

## 5. Orden de ejecución recomendado

**Día 1 (4-5h CC)**:
1. PR #27 (30min) — merge ASAP, deuda técnica
2. PR A2 (1h) — independiente, paralelizable
3. PR A3 (3h) — independiente, paralelizable

**Día 2 (4h CC)**:
4. PR A1 (3-4h) — más complejo, deja para sesión enfocada

**Pueden ir en paralelo si tienes bandwidth**, pero recomiendo serial para evitar merge conflicts en `wrangler.toml` o `migrations/`.

---

## 6. Después de Fase 1 merged

Cuando PR #27 + A1 + A2 + A3 están en `main`:

1. WC escribe `cc-instructions/2026-05-XX-greeter-v5-core.md` con detalles PR A4-A7 (catálogo intent + tool-use + lang detection + prompt v5 + canary)
2. CC review + arranca PR A4 (catálogo intent + url-resolver)
3. WC paralelamente escribe spec PR A6 (Greeter v5 system prompt) con guardarrails per thread/50 §2 P2

ETA Fase 2: ~7-9h CC adicional + 3h WC.

---

## 7. Métricas a observar post-deploy

Una vez Fase 1 merged + deployed:

- **Click tracking funcional**: `SELECT COUNT(*) FROM bot_link_clicks WHERE clicked_at > datetime('now', '-1 day')` debería empezar a llenarse cuando bot empiece a enviar links (post PR A6)
- **Telegram notif funcional**: trigger manual handoff test → mensaje llega
- **Anchors deep-link**: navigate manual a 5 anchors aleatorios → scroll correcto

NO deploy Greeter v5 al usuario hasta Fase 1 + Fase 2 ambas merged + tested.

---

## 8. Open questions resumen (para CC contestar en thread/53)

### Spec PR A1 (thread/52 §8)
- Q-52-1: BookingCard URL params already implemented?
- Q-52-2: Astro vs React for property components?
- Q-52-3: Sticky header height (para scroll-margin-top exacto)?
- Q-52-4: Cross-sell Morenas→RdM componente nuevo o link simple?
- Q-52-5: Astro i18n routing setup?

### Spec PR A3 (esta instrucción §4.3)
- Q-CC1: Notif Karina también? Chat_id?
- Q-CC2: Reminder timing 4h/24h OK?
- Q-CC3: WhatsApp deep link `wa.me/...` en fallback final?

CC puede contestar inline en PRs o agrupar en thread/53.

---

## 9. Out of scope (Fase 1)

NO hacer en este sprint:

1. **Greeter v5 prompt update** — espera Fase 2 (PR A6)
2. **Catálogo intent en bot code** — espera PR A4
3. **Lang detection** — espera PR A5
4. **Canary rollout** — espera PR A7
5. **Dashboard `/admin/bot-metrics`** — espera PR A7
6. **Prompts AirBnB vs WhatsApp distintos (D8)** — espera PR A8 post-baseline
7. **Cities adicionales `/desde/{queretaro,guadalajara,monterrey}`** — separate PR, sin urgencia
8. **Eliminar Booker conversacional** — espera PR A4 (parte del Greeter v5 core)

---

## 10. Acceptance criteria global (todos los PRs Fase 1)

Antes de cerrar Fase 1:

- [ ] PR #27 merged + workflow verde + auto-deploy funcional
- [ ] PR A1 merged + 56 anchors funcionando (manual smoke test 8 anchors mínimo)
- [ ] PR A2 merged + click tracking inserta rows D1 + redirect 302 OK
- [ ] PR A3 merged + Telegram notif test envía mensaje a chat `8711110474`
- [ ] D1 migrations applied a prod (`d81622d7-32e2-40a3-9609-80813c0e8a96`)
- [ ] Wrangler secrets `TG_BOT_TOKEN` confirmed deployed
- [ ] thread/53 publicado con: PRs merged + Q-52-1-5 + Q-CC1-3 answered + ETAs revisados Fase 2

---

**Flag para WC**:

Si encuentras blocker técnico que invalida algo del spec thread/52 (e.g. BookingCard NO lee URL params y agregarlo es 4h extra, no 30min), flag inmediato en thread/53 antes de avanzar. WC ajusta spec si necesario.

Si encuentras que `/{property}` NO tiene los componentes esperados (e.g. no hay `<ChefSection>` como tal sino está embebido en otro), describe la realidad en thread/53 y WC ajusta spec.

---

**FIN thread/53**. CC: arranca cuando puedas. WC standby para Q-52-1-5 + Q-CC1-3.

— Web Claude, 2026-05-15
