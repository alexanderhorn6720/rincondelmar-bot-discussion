# Thread/230 — Email confirmación + recibo post-pago (web checkout)

**Type**: DoIt (autonomous)
**Estimated**: 1.5h CC Sonnet
**Cost**: $2-4
**Prerequisite**: thread/228 (PR #197) merged + deployed. Web checkout flow validado end-to-end (smoke test 3: booking 87428699 confirmado con cargos + pago).

---

## §1 Contexto

El flujo web checkout (thread/222 C1) crea hold → pago MP → confirma Beds24. **Pero NO envía email transactional al guest** tras el pago exitoso.

### Por qué falta

El email post-pago lo disparaba el Make scenario `BEDS24-confirm-payment` (4709131), documentado en `OPEN_QUESTIONS.md` PR2 §A:
> "Sin esto, el flujo de confirmación post-pago no completa el booking en Beds24."

Thread/226 reemplazó la confirmación Beds24 (worker-pago ahora hace POST directo), **pero la segunda mitad del scenario — el email — nunca se reemplazó**.

### Estado de los assets email

`packages/email-templates/src/` tiene 6 templates React Email completos (commit `4e4100c`, 9-may):
- `BookingConfirmation.tsx`, `PaymentReceipt.tsx`, `HoldExpired.tsx`, `PreArrivalReminder.tsx`, `ReviewRequest.tsx`, `MagicLink.tsx`

`apps/web/src/lib/email.ts` tiene funciones wrapper que rinden estos templates vía Resend. **Pero `sendBookingConfirmationEmail` y `sendPaymentReceiptEmail` NUNCA se llaman** (cero call sites).

### Por qué NO reutilizamos esas funciones

3 razones:
1. **Cross-workspace**: viven en `apps/web/src/lib/email.ts`. El webhook MP corre en `worker-pago` (workspace separado, no importa apps/web).
2. **renderEmail falla en CF Workers**: comment en `email.ts:78` documenta que `@react-email/render` falla silenciosamente en CF Workers runtime (incompat con `react-dom/server.edge`). Por eso `sendMagicLinkEmail` tiene fallback HTML inline. Las otras 5 funciones NO tienen fallback → riesgo de email silenciosamente no enviado.
3. **Consistencia**: worker-pago ya manda 3 emails (`sendHoldExpiredEmail`, `sendPreArrivalEmail`, `sendReviewRequestEmail` en `crons.ts`) usando **HTML inline + helper `resendSend`** — NO usa los templates React. Agregar 2 emails más con el mismo patrón es consistente.

### Decisión Alex (2026-05-28)

**Opción B**: HTML inline en worker-pago, mismo patrón que los 3 emails de crons.ts. Email sale del worker-pago.

---

## §2 Scope

### IN

1. **Email confirmación reserva** post-pago exitoso (web checkout UUID flow)
   - Se dispara tras `push.ok && webBookingId` + confirm Beds24 exitoso
   - Contenido: reserva confirmada, fechas, huéspedes, total, anticipo pagado, saldo pendiente, link a /mi-cuenta/reservas/:id
   - HTML inline (NO template React), patrón `resendSend` de crons.ts

2. **Email recibo de pago** (puede ser el mismo email o separado — ver D3)
   - Monto pagado, método, ID de pago MP, fecha

3. **Helper `resendSend` en worker-pago**: ya existe en `crons.ts`. Extraer a módulo compartido `apps/worker-pago/src/email.ts` para reutilizar desde webhook-mp.ts + crons.ts (evita duplicar el helper).

4. **Query del guest data**: el webhook ya tiene `webBookingId`. Necesita JOIN a `users` para email + nombre:
   ```sql
   SELECT b.property_id, b.check_in, b.check_out, b.guests, b.total_mxn, b.deposit_mxn,
          u.email AS user_email, u.name AS user_name
   FROM bookings b LEFT JOIN users u ON u.id = b.user_id
   WHERE b.id = ?
   ```

5. **Best-effort**: si el email falla, NO bloquea el 200 al webhook MP (igual que el confirm Beds24 actual). Solo loggea.

6. **Tests**: validar que tras pago approved + push ok + webBookingId, se llama el email con los datos correctos. Mock de fetch a Resend.

7. **Self-review** pre-PR.

### OUT

- Refactor de los 3 emails de crons.ts a usar templates React (deuda técnica separada)
- Investigar/arreglar el bug `renderEmail` en CF Workers (deuda técnica)
- Email para el flujo admin `b24-` (ese flujo no tiene web booking ni user — el guest llega por WhatsApp, no por web. Out of scope)
- PDF de recibo (mencionado en OPEN_QUESTIONS PR2 §13, nunca implementado — deuda)
- Email de pago pendiente / rechazado / refund (solo confirmación de approved en v1)
- Deploy (Alex post-merge: `cd apps/worker-pago && npx wrangler deploy`)
- Smoke test (Alex post-deploy)

---

## §3 Decisiones cerradas

| # | Decisión | Razón |
|---|---|---|
| D1 | HTML inline, NO templates React | Decisión Alex opción B. Consistencia con crons.ts + evita bug renderEmail en Workers |
| D2 | Email sale de worker-pago | El webhook MP corre ahí. Ya tiene RESEND_API_KEY (usado por crons). No cross-workspace |
| D3 | **UN solo email "Reserva confirmada"** que incluye el recibo embebido (monto pagado, método, ID MP) | Menos fricción para el guest. Un email con todo: confirmación + recibo. No dos emails separados |
| D4 | Best-effort, no bloquea webhook 200 | Igual que confirm Beds24 actual. MP no debe reintentar por fallo de email |
| D5 | Extraer `resendSend` + `escapeHtml` a `apps/worker-pago/src/email.ts` | crons.ts ya lo tiene inline. Compartir evita duplicar. crons.ts importa del nuevo módulo |
| D6 | Solo para UUID flow (web checkout), no para `b24-` admin flow | El admin flow no tiene user_id ni booking web. El guest de ese flujo llega por WhatsApp |
| D7 | Fechas formateadas legible ES: "9 jul 2026" | Reutilizar el `fmtDate` de crons.ts (también extraer a email.ts o duplicar — CC decide) |
| D8 | Property name desde un map roomId→nombre o property_id→nombre | crons.ts tiene `PROPERTY_NAMES` keyed by property_id slug. Reutilizar |

---

## §4 Implementación

### 4.1 Nuevo módulo `apps/worker-pago/src/email.ts`

Extraer de `crons.ts`: `resendSend`, `escapeHtml`, `fmtDate`, `PROPERTY_NAMES`. Agregar la nueva función `sendBookingConfirmationEmail`.

```typescript
/**
 * Email layer para worker-pago. HTML inline (no React templates) — consistente
 * con los emails de crons.ts y evita el bug @react-email/render en CF Workers
 * (documentado en apps/web/src/lib/email.ts:78). thread/230.
 */

export interface EmailEnv {
  RESEND_API_KEY?: string;
  RESEND_FROM_DOMAIN?: string;
  SITE_URL?: string;
}

export const PROPERTY_NAMES: Record<string, string> = {
  'rincon-del-mar': 'Rincón del Mar',
  'las-morenas': 'Las Morenas',
  'huerta-cocotera': 'Huerta Cocotera',
  combinada: 'Rincón del Mar + Las Morenas',
};

export function escapeHtml(s: string): string {
  return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

const MONTHS = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
export function fmtDate(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return iso;
  return `${Number.parseInt(m[3]!, 10)} ${MONTHS[Number.parseInt(m[2]!, 10) - 1]} ${m[1]}`;
}

function fmtMxn(n: number): string {
  return `$${n.toLocaleString('es-MX')} MXN`;
}

export async function resendSend(
  env: EmailEnv,
  to: string,
  subject: string,
  html: string,
  persona = 'reservas',
): Promise<{ ok: boolean; error?: string }> {
  if (!env.RESEND_API_KEY) {
    console.log('[email:dev] resendSend (no RESEND_API_KEY)', { to, subject });
    return { ok: true };
  }
  try {
    const domain = env.RESEND_FROM_DOMAIN ?? 'email.rincondelmar.club';
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: `Rincón del Mar <${persona}@${domain}>`,
        to,
        subject,
        html,
      }),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      console.error('[email] resend failed', res.status, text.slice(0, 200));
      return { ok: false, error: `${res.status} ${text.slice(0, 200)}` };
    }
    return { ok: true };
  } catch (err) {
    console.error('[email] resend threw', err);
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export interface BookingConfirmationInput {
  guestName: string;
  guestEmail: string;
  propertyId: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  totalMxn: number;
  depositPaidMxn: number;
  paymentMethodId: string | null;
  mpPaymentId: string;
  bookingId: string;
}

export async function sendBookingConfirmationEmail(
  env: EmailEnv,
  input: BookingConfirmationInput,
): Promise<{ ok: boolean; error?: string }> {
  const propertyName = PROPERTY_NAMES[input.propertyId] ?? input.propertyId;
  const siteUrl = env.SITE_URL ?? 'https://rincondelmar.club';
  const balance = input.totalMxn - input.depositPaidMxn;
  const guestFirst = escapeHtml(input.guestName.trim().split(/\s+/)[0] ?? '');
  const methodLabel = input.paymentMethodId
    ? ` (${escapeHtml(input.paymentMethodId)})`
    : '';

  const html = `
    <div style="font-family:system-ui,-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1d22">
      <h1 style="font-family:Georgia,serif;font-size:24px;color:#0e6b7a;margin:0 0 16px">Reserva confirmada</h1>
      <p style="font-size:15px;line-height:1.5">Hola ${guestFirst},</p>
      <p style="font-size:15px;line-height:1.5">
        Tu reserva en <strong>${escapeHtml(propertyName)}</strong> está confirmada. Recibimos tu anticipo y bloqueamos las fechas.
      </p>
      <table style="width:100%;border-collapse:collapse;margin:24px 0">
        <tbody>
          <tr><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;color:#4d5560">Llegada</td><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;text-align:right">${fmtDate(input.checkIn)}</td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;color:#4d5560">Salida</td><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;text-align:right">${fmtDate(input.checkOut)}</td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;color:#4d5560">Huéspedes</td><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;text-align:right">${input.guests}</td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;color:#4d5560">Total</td><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;text-align:right">${fmtMxn(input.totalMxn)}</td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;font-weight:600;color:#0e6b7a">Anticipo pagado${methodLabel}</td><td style="padding:8px 0;border-bottom:1px solid #e3dfd6;font-size:14px;font-weight:600;text-align:right;color:#0e6b7a">${fmtMxn(input.depositPaidMxn)}</td></tr>
          <tr><td style="padding:8px 0;font-size:14px;color:#4d5560">Saldo pendiente</td><td style="padding:8px 0;font-size:14px;text-align:right">${fmtMxn(balance)}</td></tr>
        </tbody>
      </table>
      <p style="font-size:14px;line-height:1.5;color:#4d5560">
        El saldo restante se paga 7 días antes de tu llegada. Te recordaremos.
      </p>
      <p style="margin:24px 0">
        <a href="${siteUrl}/mi-cuenta/reservas/${input.bookingId}" style="display:inline-block;background:#0e6b7a;color:#fff;padding:14px 28px;border-radius:9999px;font-weight:600;text-decoration:none;font-size:15px">Ver detalle de tu reserva</a>
      </p>
      <p style="font-size:13px;color:#74808f;line-height:1.5">
        Recibo de pago: MercadoPago ${escapeHtml(input.mpPaymentId)}. Cualquier duda escríbenos por WhatsApp — Karina o Alexander te responden directo.
      </p>
      <p style="font-size:11px;color:#74808f;text-align:center;margin-top:32px">
        Rincón del Mar · Pie de la Cuesta · Acapulco · <a href="${siteUrl}" style="color:#74808f">rincondelmar.club</a>
      </p>
    </div>
  `;

  return resendSend(
    env,
    input.guestEmail,
    `Reserva confirmada — ${propertyName}`,
    html,
    'reservas',
  );
}
```

### 4.2 Refactor `crons.ts` para importar del nuevo módulo

`crons.ts` actualmente tiene `resendSend`, `escapeHtml`, `fmtDate`, `PROPERTY_NAMES` inline. Cambiar a importar de `./email`:

```typescript
import { resendSend, escapeHtml, fmtDate, PROPERTY_NAMES } from './email';
```

Y eliminar las definiciones duplicadas en crons.ts. **Cuidado**: el `resendSend` de crons.ts tiene firma ligeramente distinta (recibe `to, subject, html`). Adaptar los call sites de crons.ts (`sendHoldExpiredEmail`, `sendPreArrivalEmail`, `sendReviewRequestEmail`) a la firma del módulo compartido. Si la adaptación es invasiva, CC puede mantener el `resendSend` de crons.ts intacto y solo agregar el nuevo en email.ts (duplicación aceptable si el refactor es riesgoso — priorizar no romper los 3 emails que YA funcionan).

**Nota de seguridad**: los 3 emails de crons.ts funcionan en producción. NO romperlos. Si el refactor compartido es arriesgado, preferir duplicar el helper en email.ts y dejar crons.ts intacto. Self-review debe confirmar que los 3 emails siguen funcionando (tests de crons que ya existen deben pasar).

### 4.3 Insertar llamada en `webhook-mp.ts`

Dentro del bloque `if (push.ok && webBookingId)`, tras el confirm Beds24 exitoso:

```typescript
import { sendBookingConfirmationEmail } from './email';

// ... dentro de if (push.ok && webBookingId) { ... después del confirm Beds24 ...

      // Email confirmación al guest (best-effort, no bloquea 200) — thread/230
      try {
        const bookingDetail = await env.DB.prepare(
          `SELECT b.property_id, b.check_in, b.check_out, b.guests,
                  b.total_mxn, b.deposit_mxn,
                  u.email AS user_email, u.name AS user_name
             FROM bookings b LEFT JOIN users u ON u.id = b.user_id
            WHERE b.id = ? LIMIT 1`,
        )
          .bind(webBookingId)
          .first<{
            property_id: string;
            check_in: string;
            check_out: string;
            guests: number;
            total_mxn: number;
            deposit_mxn: number;
            user_email: string | null;
            user_name: string | null;
          }>();

        if (bookingDetail?.user_email) {
          const emailResult = await sendBookingConfirmationEmail(env, {
            guestName: bookingDetail.user_name ?? '',
            guestEmail: bookingDetail.user_email,
            propertyId: bookingDetail.property_id,
            checkIn: bookingDetail.check_in,
            checkOut: bookingDetail.check_out,
            guests: bookingDetail.guests,
            totalMxn: bookingDetail.total_mxn,
            depositPaidMxn: amount,
            paymentMethodId: payment.payment_method_id,
            mpPaymentId: paymentId,
            bookingId: webBookingId,
          });
          if (!emailResult.ok) {
            console.error(
              JSON.stringify({
                event: 'mp_webhook',
                sub: 'confirmation_email_failed',
                paymentId,
                webBookingId,
                error: emailResult.error?.slice(0, 200),
              }),
            );
          } else {
            console.log(
              JSON.stringify({
                event: 'mp_webhook',
                sub: 'confirmation_email_sent',
                paymentId,
                webBookingId,
              }),
            );
          }
        } else {
          console.warn(
            JSON.stringify({
              event: 'mp_webhook',
              sub: 'confirmation_email_no_address',
              paymentId,
              webBookingId,
            }),
          );
        }
      } catch (err) {
        console.error('[mp_webhook] confirmation email threw', err);
      }
```

Colocarlo **después** del bloque try/catch del confirm Beds24, dentro del mismo `if (push.ok && webBookingId)`.

### 4.4 Verificar EmailEnv en types.ts

`WorkerEnv` ya tiene `RESEND_API_KEY`, `RESEND_FROM_DOMAIN` (verificado en types.ts del thread/228 audit). Confirmar que también tiene `SITE_URL`. Si no, agregarlo a `WorkerEnv`.

### 4.5 LoC estimado

| Archivo | LoC | Tipo |
|---|---|---|
| `apps/worker-pago/src/email.ts` | +120 | NEW |
| `apps/worker-pago/src/crons.ts` | ~-40 / +5 | refactor (import en vez de inline) |
| `apps/worker-pago/src/webhook-mp.ts` | +55 | nuevo bloque email |
| `apps/worker-pago/tests/email.test.ts` | +80 | NEW |
| `apps/worker-pago/tests/webhook-mp.test.ts` | +40 | nuevo test de email |
| **Total** | **~260 LoC** | |

---

## §5 Tests

### Test email.ts

```typescript
describe('sendBookingConfirmationEmail', () => {
  it('no-op si RESEND_API_KEY ausente (dev mode)', async () => {
    const r = await sendBookingConfirmationEmail({ }, validInput);
    expect(r.ok).toBe(true);
  });

  it('POST a Resend con datos correctos', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('{}', { status: 200 }),
    );
    await sendBookingConfirmationEmail(
      { RESEND_API_KEY: 'key', SITE_URL: 'https://rincondelmar.club' },
      {
        guestName: 'María García',
        guestEmail: 'maria@example.com',
        propertyId: 'huerta-cocotera',
        checkIn: '2026-07-09',
        checkOut: '2026-07-11',
        guests: 4,
        totalMxn: 5000,
        depositPaidMxn: 2000,
        paymentMethodId: 'clabe',
        mpPaymentId: '161315475376',
        bookingId: 'fb6e6acc',
      },
    );
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://api.resend.com/emails');
    const body = JSON.parse(init.body as string);
    expect(body.to).toBe('maria@example.com');
    expect(body.subject).toContain('Huerta Cocotera');
    expect(body.html).toContain('Reserva confirmada');
    expect(body.html).toContain('9 jul 2026');     // fmtDate
    expect(body.html).toContain('11 jul 2026');
    expect(body.html).toContain('$5,000 MXN');      // total
    expect(body.html).toContain('$2,000 MXN');      // anticipo
    expect(body.html).toContain('$3,000 MXN');      // saldo
    expect(body.html).toContain('161315475376');    // mp id
    expect(body.from).toContain('reservas@');
  });

  it('escapa HTML del guest name', async () => {
    // guestName con < > & no debe romper el HTML
  });

  it('returns ok=false si Resend 4xx', async () => {
    // mock 422 → ok false con error
  });
});
```

### Test webhook-mp.ts

Extender el test existente `'UUID booking encontrado → UPDATE bookings + POST Beds24 confirm'` para validar que **también** se llama el email:

```typescript
it('UUID flow approved → confirma Beds24 + envía email confirmación', async () => {
  // setup: booking web + user con email
  // mock MP payment approved + Beds24 success + Resend success
  // assert: fetch a api.resend.com/emails llamado con el guest email
  // assert: NO bloquea el 200 si email falla
});

it('email failure no bloquea webhook 200', async () => {
  // mock Resend 500 → webhook sigue retornando 200
});
```

---

## §6 Definición de Done

- [ ] `apps/worker-pago/src/email.ts` creado con `sendBookingConfirmationEmail` + helpers
- [ ] `crons.ts` refactorizado a importar de `./email` (O duplicación segura si refactor riesgoso) — los 3 emails existentes SIGUEN funcionando
- [ ] `webhook-mp.ts` llama email tras confirm Beds24 exitoso (UUID flow only)
- [ ] Email es best-effort (no bloquea 200)
- [ ] `SITE_URL` en WorkerEnv si faltaba
- [ ] Tests: email.ts unit + webhook-mp integration (email llamado + failure no bloquea)
- [ ] `pnpm -w typecheck` PASS
- [ ] `pnpm -w lint` PASS
- [ ] `pnpm -w build` PASS
- [ ] `pnpm -w test` PASS (worker-pago + cualquier test nuevo)
- [ ] Self-review: los 3 emails de crons.ts no se rompieron, diff esperado, sin scope creep
- [ ] PR mobile-friendly con checklist deploy
- [ ] Reporte en thread/231

---

## §7 Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | Refactor de crons.ts rompe los 3 emails que YA funcionan | Si el refactor compartido es invasivo, duplicar helper en email.ts y dejar crons.ts intacto. Tests de crons existentes deben pasar |
| R2 | `users.email` NULL para algunos bookings (guest sin user) | Guard `if (bookingDetail?.user_email)`. Si NULL → log `confirmation_email_no_address`, no crash |
| R3 | Email duplicado si webhook MP llega 2x | El webhook ya tiene idempotencia KV (request-id) + check `beds24_push_status==='ok'` que retorna temprano. El email solo se manda en el primer push exitoso |
| R4 | Resend rate limit / quota | Best-effort. Si falla, log + no bloquea. El booking ya está confirmado en D1 + Beds24 |
| R5 | `depositPaidMxn` ≠ anticipo real si hay pagos parciales | En v1, `amount` del webhook = monto de ESTE pago. Para el primer anticipo es correcto. Pagos posteriores (saldo) generarían otro email — aceptable, o filtrar por primer pago. v1: enviar siempre (el guest ve "anticipo pagado $X" del pago actual) |
| R6 | HTML inline se ve mal en algún cliente email | Patrón idéntico a los 3 emails de crons.ts que ya están en prod. Inline styles, table layout — estándar email-safe |
| R7 | `fmtDate` falla con fecha mal formada | Regex guard retorna el ISO crudo si no matchea. No crash |

---

## §8 Pre-flight CC

```bash
cd /c/dev/rdm/dev/bot
git checkout main
git pull --rebase origin main
git log --oneline -3
# Esperado: top incluye PR #197 (thread/228 beds24 v2 patterns)

git checkout -b feat/post-payment-confirmation-email

# Verifica archivos
test -f apps/worker-pago/src/webhook-mp.ts
test -f apps/worker-pago/src/crons.ts
test -f apps/worker-pago/src/types.ts

# Verifica que crons.ts tiene los helpers a extraer
grep -c "function resendSend\|function escapeHtml\|function fmtDate\|PROPERTY_NAMES" apps/worker-pago/src/crons.ts
# Esperado: >= 4 (los helpers están inline)

# Verifica que webhook-mp.ts tiene el bloque push.ok && webBookingId
grep -n "push.ok && webBookingId" apps/worker-pago/src/webhook-mp.ts
# Esperado: 1 match

# Verifica RESEND en WorkerEnv
grep -c "RESEND_API_KEY\|RESEND_FROM_DOMAIN" apps/worker-pago/src/types.ts
# Esperado: >= 2

# Verifica si SITE_URL existe en types
grep -c "SITE_URL" apps/worker-pago/src/types.ts
# Si 0 → agregarlo a WorkerEnv
```

Si algún check falla → HALT, reportar.

---

## §9 Reporte final (thread/231)

```markdown
# Thread/231 — DoIt 230 completion report

**Spec**: thread/230
**Branch**: feat/post-payment-confirmation-email
**PR**: #XXX

## Files
- apps/worker-pago/src/email.ts (NEW)
- apps/worker-pago/src/crons.ts (refactor import OR duplicación segura — indicar cuál)
- apps/worker-pago/src/webhook-mp.ts (email call post-confirm)
- apps/worker-pago/src/types.ts (SITE_URL si faltaba)
- tests

## Qué hace
Tras pago web approved + confirm Beds24 ok → envía email "Reserva confirmada"
al guest con fechas, total, anticipo, saldo, link, recibo MP embebido.
Best-effort: no bloquea webhook 200.

## crons.ts refactor
[Indicar: importó del módulo compartido / mantuvo duplicación por seguridad]
Los 3 emails existentes (hold-expired, pre-arrival, review) siguen funcionando: [tests pass]

## Gates
typecheck / lint / build / test: PASS (N tests)

## Cost LLM: $X.XX

## Out of scope
- Templates React siguen sin usarse (deuda)
- bug renderEmail en CF Workers (deuda)
- email para flujo admin b24- (no aplica)
```

---

## §10 Post-merge (Alex)

```powershell
# worker-pago manual deploy
cd C:\dev\rdm\dev\bot\apps\worker-pago
npx wrangler deploy
```

**Smoke test 4** (validación email):
1. Crear hold web (fechas nuevas, ej. 2026-09-15/17)
2. Pagar anticipo
3. Verificar D1: booking=paid, push=ok (yo via MCP)
4. **Revisar el email del guest** (la cuenta usada para el hold) → debe llegar "Reserva confirmada — {property}" con fechas, total, anticipo, saldo, link, recibo MP
5. Cancelar booking en Beds24

**Secret check**: confirmar que worker-pago tiene `RESEND_API_KEY` provisionado (lo usa para los crons — probablemente ya existe). Si los crons emails funcionan, el secret está.
