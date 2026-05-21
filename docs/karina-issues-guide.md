# Guía rápida · /admin/issues (para Karina)

Esta guía te enseña a reportar bugs y observaciones del sistema usando la
nueva pantalla **/admin/issues** dentro del admin RdM. No necesitas GitHub.

---

## Para qué sirve

Cuando notes algo raro (bot responde en inglés a guest en español, foto rota
en un listing, mensaje duplicado, etc.) lo reportas aquí. Alex y el bot
de WC lo ven, lo triagean, y lo arreglan.

Antes esto iba por WhatsApp; ahora queda registrado y se puede dar
seguimiento.

---

## Cómo entrar

1. Abre [https://admin.rincondelmar.club/admin/issues](https://admin.rincondelmar.club/admin/issues)
   en tu celular o computadora.
2. Si te pide login, usa tu correo (`karina@rincondelmar.club`) y el
   método de Better Auth que Alex te configuró (magic link).

---

## Reportar algo nuevo

1. Toca **+ New** arriba a la derecha (o ve directo a
   `/admin/issues/new`).
2. Llena los campos:

   - **Title**: una línea corta. Ej: *"Bot responde EN a guest ES en
     conversación 4521"*.
   - **Bucket**: a qué área pertenece. Elige uno:
     - `admin` — la pantalla de admin/backoffice
     - `web` — el sitio público (rincondelmar.club)
     - `bot` — el bot de WhatsApp (Greeter / Booker)
     - `beds24` — calendario / sincronización con Beds24
     - `content` — fotos, descripciones, reseñas
     - `infra` — cosas técnicas (lentitud, errores 500, etc.)
   - **Priority**:
     - `high` — algo le está pasando a un guest AHORA
     - `normal` — error que pasa pero no urgente
     - `low` — mejora opcional, nice-to-have
   - **Body**: describe lo que viste. Mientras más detalle, mejor. Ej:
     - Qué intentaste hacer
     - Qué esperabas que pasara
     - Qué pasó en realidad
     - Hora aproximada
     - ID de la conversación / booking si lo sabes

3. **Screenshots** (importante para bot/web):
   - En desktop: copia con `Cmd/Ctrl+Shift+4` y pega con `Cmd/Ctrl+V` en el
     área de Body o usa el botón `📎`.
   - En celular: toca `📎` y elige la foto de tu galería.
   - Puedes subir varias (max 10 MB cada una).

4. **Related threads** (opcional): si Alex te dijo "esto va con thread/127",
   ponlo aquí. Si no, déjalo vacío.

5. Toca **Submit**. La pantalla te confirma con un número de issue y abre
   el detalle.

---

## Qué pasa después

- Tu issue aparece automáticamente en la sección **Awaiting CC** del
  inbox.
- WC (el bot que ayuda a Alex con triage) lo lee, sugiere una causa raíz,
  y lo marca como **triaged**.
- Alex aprueba o rechaza. Si aprueba, se vuelve **spec-ready** y CC
  (el bot que escribe código) lo trabaja.
- Cuando se mergea el PR que arregla tu issue, se cierra solo y aparece
  en **Recently done** unos 7 días.

Tú puedes ver el progreso entrando a `/admin/issues` cuando quieras.

---

## Qué NO incluir en un issue

- **Datos sensibles**: contraseñas, números de tarjeta, IDs de identidad
  oficial completos. Tacha o no incluyas la información sensible en el
  screenshot.
- **Conversaciones privadas con guests**: solo lo necesario para reproducir
  el problema. Si necesitas un fragmento, pídele permiso primero o
  anonimiza el nombre.
- **Información de empleados o contratistas** que no sea relevante al bug.

Si dudas si algo es sensible, pregúntale a Alex antes de hacer submit.

---

## Cosas que verás y te van a confundir al principio

- **El botón "Copy WC context"** en cada issue copia un texto en formato
  Markdown al portapapeles. Eso es para Alex cuando discute contigo el
  issue en chat web — no necesitas usarlo.
- **El botón "Open in GitHub"** abre la versión técnica del issue. Está
  bien si entras, pero no necesitas comentar ahí — el comentario en el
  detail de `/admin/issues` funciona igual.
- **"CC Activity Tracker"** muestra qué bot está trabajando en qué
  branch. Es informativo, no requiere acción de tu parte.
- **Daily Brief** (6am MX): resumen del día de Alex. Tú no lo recibes a
  menos que él lo comparta — vive en `/admin/issues/brief`.

---

## Si algo no funciona

Si la pantalla `/admin/issues` no carga, o el Submit te da error rojo:

1. Refresca la página.
2. Si sigue mal, manda WhatsApp a Alex con captura — esto es justo lo
   que estamos resolviendo, pero hasta que el sistema esté maduro el
   fallback es contactarlo directo.

---

## Resumen

| Quieres... | Vas a... |
|---|---|
| Reportar un bug nuevo | `/admin/issues/new` |
| Ver el estado de algo | `/admin/issues` (busca por título) |
| Saber qué se cerró ayer | (Alex te comparte) `/admin/issues/brief` |
| Comentar en un issue ya creado | toca el issue → escribe en el detail |
| Cerrar un issue tú misma | No — déjalo a Alex |

Cualquier duda, pregúntale a Alex.

— Equipo RdM
