# Thread 41 — Alex final answers Q-A12 to Q-A15 + CC unblocked

**Date**: 2026-05-13
**Author**: Web Claude (WC) capturing Alex decisions
**To**: Claude Code (CLI) `[@cc]` — proceed con review thread/40 + ahora sin pending Alex answers, Alex `[@alex]` — visibility
**Re**: Alex resolvió Q-A12 a Q-A15. Todas las Q-A respuestas listas. CC ahora tiene contexto completo para opinar y proponer sequence ejecución.

---

## 0. TL;DR

Las 4 preguntas pendientes resueltas:

- **Q-A12 (auth Karina)**: `karina@rincondelmar.club` YA existe con Better Auth magic link. Cero setup extra para Fase 1.5.
- **Q-A13 (footer interno)**: reescribir. WC propone opciones §2 abajo, decisión final en Fase 1b cleanup.
- **Q-A14 (Beds24 Everything mode)**: 🟢 **NO tocar**, mantener `Prices&Availability`. Memoria reforzada.
- **Q-A15 (bot Morenas conditional)**: Beds24 ya expone `channel` field — D1 schema ya lo tiene (`bookings.channel`). Bot lee de ahí, NO campo extra. Render conditional según value.

**Estado**: ALL Q-A answered. CC desbloqueado para:
1. Generar thread/41-cc-review (per cc-instructions/2026-05-13-review-thread40-content-editor.md)
2. Ejecutar Fase 0.5 (`/guia-llegada` 404 fix) cuando Alex diga go
3. Empezar Fase 1.5 editor design + build una vez Alex aprueba

---

## 1. Respuestas Alex

### Q-A12 — Auth Karina: ya existe magic link

```
karina@rincondelmar.club YA registered en Better Auth, magic link funciona.
```

🟢 **Implicación Fase 1.5**:
- CERO setup extra de auth
- CC implementa role-based access en `apps/web/src/middleware.ts`:
  - `karina@rincondelmar.club` → role `content_editor`
  - Acceso solo a `/admin/airbnb-content/*`
  - NO acceso a `/admin/templates` (Phase B.0.5), `/admin/leads` (Phase B.4), ni otros admin
- Alex sigue siendo `admin` full access
- Audit trail completo via `Astro.locals.user.email` per save action

### Q-A13 — Footer interno: reescribir

```
Alex: "reescribir"
```

🟡 **Decisión approach final en Fase 1b cleanup**. WC propone 3 opciones a evaluar contigo:

| Opción | Texto | Riesgo AirBnB | Decodificable por guest |
|---|---|---|---|
| A | "Síguenos en redes sociales ⛱️" | Mínimo | Baja (vago, requiere búsqueda) |
| B | "Búscanos en Instagram @villarincondelmar" | Bajo (mención red social permitida) | Alta (handle directo) |
| C | "Encuéntranos también en RM Club" (sin URL completa) | Medio (parece marca, no URL) | Media |
| D | Firma branded "— Alexander · Rincón del Mar 🌅" sin pista de canal externo | Mínimo | Cero |

**WC vote**: **B** (Instagram handle). Razones:
- IG handle es legalmente permitido en mensajes AirBnB (vs URL/teléfono prohibidos)
- @villarincondelmar redirige a Linktree custom `rincondelmar.club/r` con todos los canales (WhatsApp, sitio, FB, TikTok)
- Mide effectiveness: track follows que llegan vía IG y dicen "vi tu anuncio AirBnB"
- Reemplaza 14+ templates con un solo handle consistente

Alternativa híbrida: **A + B** según template type. Inquiry templates usan B (más push), pre-arrival usan A (más sutil).

**Decisión final en Fase 1b cuando CC ejecute cleanup**. Alex valida.

### Q-A14 — Beds24 Everything mode: 🟢 NO tocar

```
Alex: "siiiiiiiiii" (confirma NO tocar)
```

🟢 **Memoria reforzada**:
- Sync mode permanente: `Prices&Availability` uniforme 4 listings (post-cutover 2026-05-12)
- AirBnB sigue siendo source-of-truth de content
- Content flow: WC/Alex/Karina edit → R2 → CC Chrome MCP write-back → AirBnB
- NO push content desde Beds24 a AirBnB en ningún escenario actual

🟡 **Compromise futuro post-Fase 2**: cuando Welcome Guide + editor estables (meses post-launch), evaluar push content desde TU editor a Beds24 listings también (para Booking.com tener mismo content cuando se active esa integración). Pero TU editor sigue siendo source.

### Q-A15 — Bot conditional Morenas servicio: Beds24 `channel` ya existe

```
Alex: "pues si ya hay booking sabemos de donde, esta en beds24 no necesitamos otro campo extra, 
pero si, el bot lo necesita saber."
```

🟢 **Confirmed**: campo Beds24 `referer` / `channel` ya existe en respuesta API booking (validated thread/12).

**Schema Phase B `bookings` table ya lo tiene** (validated thread/33):

```sql
CREATE TABLE bookings (
  ...
  channel TEXT NOT NULL,
  -- enum: 'airbnb' | 'booking_com' | 'direct' | 'web' | 'whatsapp_direct'
  channel_reservation_code TEXT,  -- HM3D2N5K (airbnb confirmation code)
  ...
);
```

**Implicación bot KB Morenas servicio**:

```
IF bookings.channel == 'airbnb':
   render "Servicio OPCIONAL. $1,000/noche reservada (≤16 pax). $1,500/noche (>16 pax).
           Día salida NO se cobra. Pago directo a Karina/Alex."

ELSE (channel in 'direct', 'web', 'whatsapp_direct'):
   render "Servicio INCLUIDO: una cocinera + un mozo durante toda la estancia."

ELSE (channel == 'booking_com'):
   ⚠️ defer (Booking.com integration aún no live, memoria)
```

🟢 **Implicación arquitectura Welcome Guide**:
- **Página pública `/welcome/las-morenas`** dice servicio OPCIONAL (es la versión segura — un guest directo viendo página pública NO se siente engañado al saber que opcional aplica a reservas AirBnB; un guest AirBnB confirma lo que ya sabe)
- **Página auth-gated `/mi-estancia/welcome`** (post-booking) hace conditional render basado en `bookings.channel` del guest logged in

✅ **Sin campo extra D1, sin nuevo plumbing**. Phase B.1 welcome auto-send + Welcome Guide auth-gated consumen `bookings.channel` que ya existe.

---

## 2. Status: ALL Q-A answered

| # | Status | Resolución |
|---|---|---|
| Q-A1 Morenas servicio | ✅ | AirBnB opcional / Direct incluido. Per-noche. |
| Q-A2 Bodas precio | ✅ | $1,400/pax confirmed |
| Q-A4 Welcome split | ✅ | Público + auth-gated `/mi-estancia/welcome` |
| Q-A5 Datos terceros | ✅ | Sin restricción (Alex acepta LFPDPPP risk) |
| Q-A7 Footer | ✅ | Reescribir, opciones §1.Q-A13 above |
| Q-A8 Clave caja | ✅ | Mantener "6720" universal |
| Q-A9 Photos terceros | ✅ | Consent OK |
| Q-A10 Casa Chamán | ✅ | Defer Q3 2026 |
| Q-A11 Política no-editar | ✅ | Enforce OK |
| Q-A12 Auth Karina | ✅ | Better Auth magic link existing |
| Q-A13 Footer approach | ✅ | Reescribir (final option Fase 1b) |
| Q-A14 Beds24 mode | ✅ | NO tocar, mantener Prices&Availability |
| Q-A15 Bot conditional | ✅ | Usar `bookings.channel` ya en D1 schema |

---

## 3. CC ahora desbloqueado

Per cc-instructions/2026-05-13-review-thread40-content-editor.md, CC puede:

1. **Leer thread/40 + thread/41** (este doc) — contexto completo
2. **Generar thread/42-cc-review-thread40-final.md** con:
   - Opinión §2.6 thread/40 (editor primero Fase 1.5 vs original)
   - Confirm 15-20h CC estimate o ajustar
   - Q-W1 to Q-W4 respuestas (thread/39 si pendientes)
   - Q-C1 to Q-C4 respuestas (thread/39)
   - Concerns técnicos adicionales (R2 throttle, concurrent edits, conflict templates editor, costs)
   - Sí/No proceder + sequence propuesto final
3. **WAIT Alex go** para ejecutar Fase 0.5 + Fase 1b + Fase 1.5

---

## 4. Action items remaining

### Alex

- [ ] Read CC opinión cuando publique thread/42
- [ ] Decide GO/NO-GO final + sequence
- [ ] Si go: tell CC qué empezar primero (Fase 0.5 standalone o batch hasta Fase 1.5)

### CC

- [ ] Read thread/40 + thread/41 (este)
- [ ] Generate thread/42 review per cc-instructions
- [ ] WAIT Alex go

### WC

- [ ] Standby (este thread completa my Alex answer capture work)
- [ ] Post Alex go: empezar drafting 32 fields × 4 props en formato §5 thread/39
- [ ] Pre-Editor live: drafts directos a JSON en `knowledge/content-drafts/{slug}.{lang}.json` manual
- [ ] Post-Editor live: drafts via UI con Karina

---

## 5. Open issues parking lot (para futuro)

Cosas que salieron en discusión y mantenemos en mente:

- **Memoria proyecto update**: agregar entry "Beds24 Everything mode permanently NO use, content flow editor → R2 → Chrome MCP → AirBnB"
- **Booking.com push content compromise**: futuro post-Fase 2 stable, considerar push content desde editor a Beds24 listings → Booking.com sync
- **Photo pipeline Fase 2.5b**: defer hasta Welcome Guide MVP live
- **Casa Chamán reciclar vs nuevo**: defer hasta Q3 2026 cuando Alex tenga info
- **Karina onboarding doc**: una vez Fase 1.5 live, Alex/WC drafts mini-guide para Karina (cómo usar editor)

— Web Claude (WC), 2026-05-13
