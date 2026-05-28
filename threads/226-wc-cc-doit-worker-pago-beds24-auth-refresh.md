# Thread/226 — Fix BEDS24 auth en worker-pago (refresh logic)

**Type**: DoIt (autonomous)
**Estimated**: 1-1.5h CC Sonnet
**Cost**: $2-4
**Prerequisite**: Alex ya subió `BEDS24_TOKEN` + `BEDS24_REFRESH_TOKEN` a worker-pago secrets (`wrangler secret put` ejecutado 2026-05-27).

---

## §1 Contexto

Smoke test del thread/222 reveló **segundo lugar con el mismo bug auth** que ya arreglamos en apps/web (thread/224). Esta vez en worker-pago.

Pago real verificado en producción 2026-05-27 ~21:00 UTC:
- MP payment `161308218526` ($1,000 anticipo Huerta Cocotera)
- Webhook llegó, HMAC validó, UUID branch detectó booking, INSERT mp_payments funcionó
- **pushMpPayment falló**: `"BEDS24_TOKEN not configured"` (en realidad expirado, mismo síntoma que apps/web)
- D1 booking quedó en `status='pending_payment'` (no escaló a `paid` porque depende de `push.ok && webBookingId`)
- Beds24 reserva 87426928 quedó sin invoiceItem payment
- Cron `mpPaymentRetry` cada 30 min va a seguir reintentando con mismo token expirado → fallar indefinidamente

Worker-pago **NO tiene** refresh logic. Lee `env.BEDS24_TOKEN` static directo en:
- `beds24-payment.ts::pushMpPayment` (línea 39)
- `beds24-release.ts` (cancelación holds expirados)
- `webhook-mp.ts` línea ~250 (PATCH /bookings/:id status='confirmed')
- `crons.ts::expireHolds` (releaseBeds24Hold)

Worker-bot YA tiene refresh logic en `apps/worker-bot/src/beds24-auth.ts`. Mismo patrón que thread/224: copy + adapt.

**Diferencia con thread/224**: worker-pago NO tiene `KV_KNOWLEDGE` binding configurado en wrangler.toml. Hay que agregarlo.

---

## §2 Scope

### IN

1. **Agregar `KV_KNOWLEDGE` binding a `apps/worker-pago/wrangler.toml`** (mismo namespace que worker-bot y apps/web)
2. Copy `apps/worker-bot/src/beds24-auth.ts` → `apps/worker-pago/src/beds24-auth.ts` (idéntico)
3. Update `apps/worker-pago/src/types.ts`: añadir `KV_KNOWLEDGE: KVNamespace` y `BEDS24_REFRESH_TOKEN?: string` al `WorkerEnv` interface
4. Modificar **4 sitios** donde se lee `env.BEDS24_TOKEN` directo:
   - `apps/worker-pago/src/beds24-payment.ts` — función `pushMpPayment` (cambiar interface `BedsPaymentEnv` para incluir KV + refresh)
   - `apps/worker-pago/src/beds24-release.ts` — función `releaseBeds24Hold` (cambiar interface si tiene Env separada)
   - `apps/worker-pago/src/webhook-mp.ts` línea ~245-250 — el PATCH inline a `/v2/bookings/{id}` status='confirmed'
   - `apps/worker-pago/src/crons.ts` — verificar si pasa env directo a release
5. En cada call, reemplazar lectura directa de `env.BEDS24_TOKEN` por `await getBeds24AccessToken(env)`. Manejar error con `return { ok: false, error }` o equivalente.
6. Update tests existentes (`apps/worker-pago/tests/*.test.ts`) para mockear `KV_KNOWLEDGE.get/put`
7. Build + typecheck + lint + test all pass
8. PR + reporte en thread/227

### OUT

- NO modificar webhook signature validation (`hmac.ts`) — no toca auth Beds24
- NO modificar el `markBedsResult` ni schema de mp_payments
- NO crear extracción `@rdm/beds24` shared package (Wave 2)
- NO mover beds24-auth.ts a packages/shared
- NO deploy (Alex hace post-merge)
- NO smoke test (Alex re-ejecuta el flow del thread/222 §7 después del merge — el pago 161308218526 ya está en mp_payments; cron retry debería procesarlo dentro de 30 min post-deploy)
- NO añadir creación de invoiceItem `type='charge'` en createBeds24Request (ese bug es thread/226-followup que abrimos como issue post-merge — fuera del scope inmediato)
- NO arreglar docstrings desactualizados de webhook-mp.ts y crons.ts (deuda anotada en thread/223)

---

## §3 Decisiones cerradas

| # | Decisión | Razón |
|---|---|---|
| D1 | Copy file (no symlink ni shared package) | Mismo patrón que thread/224. Workers tienen restricciones de bundling |
| D2 | KV_KNOWLEDGE binding compartido (mismo id `033ee15acf3744c096e83342d2e81dd4`) | worker-bot ya escribe ahí, apps/web ya lee de ahí. worker-pago se une — single source of truth |
| D3 | `BEDS24_TOKEN` queda opcional (fallback path 3) | Si refresh falla, static token aún sirve como último recurso. Backward compat |
| D4 | Tests existentes pasan con mock KV null → fallback a static | Mismo patrón thread/224. No requiere reescribir test base |
| D5 | El PATCH inline en `webhook-mp.ts` (líneas ~245-260) también usa `getBeds24AccessToken` | Es el call que confirma la reserva en Beds24 post-payment. Mismo problema |
| D6 | No agregar refresh para `MP_ACCESS_TOKEN` | MP tokens largos son long-life. No es el problema |

---

## §4 Implementación

### 4.1 Actualizar `apps/worker-pago/wrangler.toml`

Añadir el binding KV_KNOWLEDGE después del KV_IDEMPOTENCY existente:

```toml
[[kv_namespaces]]
binding = "KV_IDEMPOTENCY"
id = "b3035e701ce1492e829f1224d85bc545"
preview_id = "b3035e701ce1492e829f1224d85bc545"

# KV_KNOWLEDGE — shared with worker-bot + apps/web (thread/226).
# Used by beds24-auth.ts to cache access_token + expires_at across workers.
[[kv_namespaces]]
binding = "KV_KNOWLEDGE"
id = "033ee15acf3744c096e83342d2e81dd4"
preview_id = "033ee15acf3744c096e83342d2e81dd4"
```

Y en la sección de comentarios de secrets, agregar:
```
#   BEDS24_REFRESH_TOKEN     # thread/226: long-lived refresh token,
#                            # used by beds24-auth.ts when access token near expiry.
```

### 4.2 Crear `apps/worker-pago/src/beds24-auth.ts`

Copy literal de `apps/worker-bot/src/beds24-auth.ts`. Único cambio en comentario inicial:
> "Copy desde worker-bot 2026-05-27 (thread/226) — refresh logic compartida vía KV_KNOWLEDGE namespace. Same pattern as apps/web/src/lib/beds24-auth.ts (thread/224)."

### 4.3 Update `apps/worker-pago/src/types.ts`

Añadir a `WorkerEnv`:
```typescript
KV_KNOWLEDGE: KVNamespace;
BEDS24_REFRESH_TOKEN?: string;
```

### 4.4 Modificar `apps/worker-pago/src/beds24-payment.ts`

**Antes** (líneas 14-16):
```typescript
export interface BedsPaymentEnv {
  BEDS24_TOKEN?: string;
}
```

**Después**:
```typescript
import { getBeds24AccessToken } from './beds24-auth';

export interface BedsPaymentEnv {
  KV_KNOWLEDGE: KVNamespace;
  BEDS24_TOKEN?: string;
  BEDS24_REFRESH_TOKEN?: string;
}
```

En `pushMpPayment`, reemplazar (líneas 37-39):
```typescript
if (!env.BEDS24_TOKEN) {
  return { ok: false, error: 'BEDS24_TOKEN not configured' };
}
```

Por:
```typescript
let token: string;
try {
  token = await getBeds24AccessToken(env);
} catch (err) {
  return { ok: false, error: err instanceof Error ? err.message : String(err) };
}
```

Y en el `fetch` (línea ~60):
```typescript
headers: {
  token,  // <— era env.BEDS24_TOKEN
  ...
}
```

### 4.5 Modificar `apps/worker-pago/src/beds24-release.ts`

Mismo patrón. Cambiar interface, agregar import, reemplazar lectura directa por `getBeds24AccessToken(env)`.

### 4.6 Modificar `apps/worker-pago/src/webhook-mp.ts`

Líneas ~245-260 (dentro del if `push.ok && webBookingId`), el PATCH inline:

**Antes**:
```typescript
const patchRes = await fetch(`https://api.beds24.com/v2/bookings/${beds24BookingId}`, {
  method: 'PATCH',
  headers: {
    token: env.BEDS24_TOKEN ?? '',  // <— bug: si vacío, falla 401
    ...
  },
  ...
});
```

**Después** (extraer obtención de token a variable antes):
```typescript
let confirmToken: string;
try {
  confirmToken = await getBeds24AccessToken(env);
} catch (err) {
  console.error('[mp_webhook] beds24 auth failed for confirm', err);
  // No bloquea retorno 200 — el push de payment ya tuvo éxito (en este branch).
  // Esta confirmación es nice-to-have, no critical.
  return c.text('ok', 200);
}

const patchRes = await fetch(`https://api.beds24.com/v2/bookings/${beds24BookingId}`, {
  method: 'PATCH',
  headers: {
    token: confirmToken,
    ...
  },
  ...
});
```

Importar `getBeds24AccessToken` arriba del archivo.

### 4.7 Verificar `apps/worker-pago/src/crons.ts`

Buscar uso de `BEDS24_TOKEN`. Si pasa `env` directo a `releaseBeds24Hold`, ya funciona post-§4.5. Si construye nuevo env object, asegurar que pase `KV_KNOWLEDGE` también.

### 4.8 Update tests

`apps/worker-pago/tests/*.test.ts` — cada test que usa env debe incluir mock `KV_KNOWLEDGE`:

```typescript
const mockEnv = {
  BEDS24_TOKEN: 'test-token',
  KV_KNOWLEDGE: {
    get: vi.fn().mockResolvedValue(null),
    put: vi.fn().mockResolvedValue(undefined),
  } as unknown as KVNamespace,
  // resto de bindings ya mockeados
};
```

40 tests existentes pasan con fallback Path 3 (BEDS24_TOKEN static).

---

## §5 Definición de Done

- [ ] `apps/worker-pago/wrangler.toml` tiene binding KV_KNOWLEDGE
- [ ] `apps/worker-pago/src/beds24-auth.ts` existe y es copy de worker-bot
- [ ] `apps/worker-pago/src/types.ts` tiene KV_KNOWLEDGE + BEDS24_REFRESH_TOKEN en WorkerEnv
- [ ] `apps/worker-pago/src/beds24-payment.ts` usa `getBeds24AccessToken(env)`
- [ ] `apps/worker-pago/src/beds24-release.ts` usa `getBeds24AccessToken(env)`
- [ ] `apps/worker-pago/src/webhook-mp.ts` línea ~250 usa `getBeds24AccessToken(env)`
- [ ] `apps/worker-pago/src/crons.ts` verificado (no requiere cambios si pasa env directo)
- [ ] Tests mockean KV_KNOWLEDGE
- [ ] `pnpm -w typecheck` PASS
- [ ] `pnpm -w lint` PASS
- [ ] `pnpm -w test` PASS (incluye 40 worker-pago + 649 apps/web)
- [ ] `pnpm -w build` PASS
- [ ] PR creado con descripción mobile-friendly + checklist deploy para Alex
- [ ] Self-review pre-merge: diff es lo esperado, no toca ningún archivo del lock list de payment-flow más allá de los necesarios
- [ ] Reporte final en thread/227

---

## §6 Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | beds24-auth.ts usa `KVNamespace` type — workers tienen acceso vía `@cloudflare/workers-types`, debe importar correcto | Verificar tsconfig.json de worker-pago. Si necesita import explícito, agregar |
| R2 | Tests existentes rompen por interface change en BedsPaymentEnv | Fix trivial — añadir mock KV_KNOWLEDGE. Cubierto en §4.8 |
| R3 | KV_KNOWLEDGE binding nuevo en producción requiere redeploy completo | wrangler deploy refleja cambios de wrangler.toml automático. Alex deploya post-merge |
| R4 | Pago `161308218526` queda atascado si CC tarda mucho | Cron retry corre cada 30 min. Tras deploy con token válido, se procesa solo |
| R5 | `webhook-mp.ts` está en archivos locked (CODEOWNERS futuro) | No hay CODEOWNERS aplicado todavía. Si existiera, el PR body necesitaría marker `payment-flow-modification-approved: yes`. CC verifica antes de PR |
| R6 | beds24-release.ts puede tener interface diferente a la genérica | CC lee el archivo primero antes de aplicar el patrón. Si interface es diferente, adapta |

---

## §7 Post-merge (Alex)

1. **Merge PR** vía squash
2. **Deploy worker-pago** (manual, no auto):
   ```powershell
   cd C:\dev\rdm\dev\bot\apps\worker-pago
   npx wrangler deploy
   ```
3. **Verificar secrets**:
   ```powershell
   npx wrangler secret list
   ```
   Esperado: `BEDS24_TOKEN`, `BEDS24_REFRESH_TOKEN`, `MP_WEBHOOK_SECRET`, `MP_ACCESS_TOKEN`.
4. **Tail logs**:
   ```powershell
   npx wrangler tail
   ```
5. **Esperar cron retry** (~30 min máximo) o **forzar procesamiento del pago atascado**:
   - Opción A: esperar cron `*/30 * * * *` próximo tick
   - Opción B: WC ejecuta UPDATE `mp_payments SET beds24_push_status='pending'` para el `161308218526` y aguardar próximo cron
6. **Verificar resultado vía MCP**:
   - D1 `bookings` row UUID `2977a854-...`: `status='paid'`, `mp_payment_id='161308218526'`, `paid_at` populated
   - D1 `mp_payments` row `161308218526`: `beds24_push_status='ok'`, `beds24_pushed_at` populated
   - Beds24 booking 87426928: Cargos & Pagos panel muestra payment $1,000 MXN
   - Telegram notification llega (TG_BOT_TOKEN + TG_CHAT_ID_PAGOS deben estar provisionados — verifique)
7. **Cancelar booking en Beds24 dashboard** (no quemar inventario julio 2026)

---

## §8 Pre-flight CC

```bash
cd /c/dev/rdm/dev/bot
git checkout main
git pull --rebase origin main
git log --oneline -3
# Esperado: top commits incluyen PR #195 (thread/224) y PR #194 (thread/222)

# Branch
git checkout -b fix/worker-pago-beds24-auth-refresh

# Verifica archivos críticos
test -f apps/worker-bot/src/beds24-auth.ts
test -f apps/web/src/lib/beds24-auth.ts        # debe existir post thread/224
test -f apps/worker-pago/src/beds24-payment.ts
test -f apps/worker-pago/src/beds24-release.ts
test -f apps/worker-pago/src/webhook-mp.ts
test -f apps/worker-pago/src/types.ts
test -f apps/worker-pago/wrangler.toml

# Verifica KV_KNOWLEDGE NO está aún en worker-pago wrangler.toml
grep -c "KV_KNOWLEDGE" apps/worker-pago/wrangler.toml
# Esperado: 0 (CC debe agregarlo)
```

Si cualquier check falla → HALT, reportar.

---

## §9 Reporte final (thread/227)

```markdown
# Thread/227 — DoIt 226 completion report

**Spec**: thread/226
**Branch**: fix/worker-pago-beds24-auth-refresh
**PR**: #XXX

## Files changed
- apps/worker-pago/wrangler.toml (+5 KV_KNOWLEDGE binding)
- apps/worker-pago/src/beds24-auth.ts (NEW, copy from worker-bot)
- apps/worker-pago/src/types.ts (+2 fields)
- apps/worker-pago/src/beds24-payment.ts (interface + 3 line replace)
- apps/worker-pago/src/beds24-release.ts (interface + replace)
- apps/worker-pago/src/webhook-mp.ts (import + 1 PATCH call replace)
- apps/worker-pago/tests/*.test.ts (mock KV_KNOWLEDGE)

## Gates
- typecheck: PASS
- lint: PASS
- build: PASS
- test: 40 worker-pago + 649 web = 689 PASS

## Cost LLM
$X.XX

## Alex next
1. Merge PR
2. `cd apps/worker-pago && npx wrangler deploy`
3. Esperar próximo cron retry (~30 min) o force-update mp_payment pending
4. Verificar D1 booking → status='paid'
5. Verificar Beds24 reserva 87426928 → Pagos $1,000

## Out-of-scope findings
- Creación de invoiceItem type='charge' en createBeds24Request (apps/web) — bug separado, Beds24 muestra Cargos=0
- Docstrings incorrectos en webhook-mp.ts (claim "tabla bookings no existe") — deuda anotada thread/223
```

---

## §10 Notas

- Pago real `161308218526` ($1,000) está atascado en producción esperando este fix.
- Tras merge + deploy, cron retry procesa automáticamente.
- Este es el **3er lugar con auth bug**: worker-bot (ya tenía refresh), apps/web (thread/224 fix), worker-pago (este DoIt).
- Después de este DoIt, el sistema queda con auto-refresh en los 3 workers, leyendo del **mismo KV namespace compartido**. Worker-bot escribe access tokens en KV, los demás lo leen. Cualquiera puede refrescar si está expirado.
- Cuando llegue el momento del "shared @rdm/beds24 package" (Wave 2, ADR-003 menciona), se refactoriza los 3 copies a una sola fuente.
- Bug pendiente que descubrimos en smoke pero NO se arregla aquí: Beds24 muestra Cargos=0 porque `createBeds24Request` no crea invoiceItem `type='charge'`. Eso es **bug separado**, abrimos issue post-merge para spec siguiente.
