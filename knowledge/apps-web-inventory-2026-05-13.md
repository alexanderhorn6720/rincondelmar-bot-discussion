# apps/web inventory — 2026-05-13

Inventory técnico del estado actual del repo `apps/web` para input al review del Welcome Guide.

**Source**: CC inspeccionó directamente `C:\rincondelmar-bot\apps\web\` el 2026-05-13.
**Stack**: Astro 5 + React 19 islands + CF Pages adapter + monorepo workspace.

---

## 0. TL;DR

- **30+ páginas** Astro existentes (público + admin + API)
- **i18n built-in Astro** habilitado (es default + en, prefix-default off)
- **Content collections**: properties (5 JSON), blog (10 MDX), faqs, landings, reviews
- **Páginas EN parciales**: 10 traducidas en `/en/` (homepage, propiedades, weddings, faq, etc.)
- **No existe `/guia-llegada`** ← templates AirBnB linkean ahí (broken link, 404)
- **No existe `/welcome/{property}`** todavía
- **`/admin/*`** ya existe (Phase B.0.5: home + templates + health)

---

## 1. Estructura `src/pages/`

### Páginas públicas ES (root)

| Path | Tipo | Propósito |
|---|---|---|
| `index.astro` | Static | Homepage |
| `[propertyId].astro` | Static dynamic | Página por propiedad (rincon-del-mar, las-morenas, etc.) — usa content collection |
| `404.astro`, `500.astro` | Static | Error pages |
| `arquitectos.astro` | Static | SEO landing arquitectos |
| `blog/index.astro` + `blog/[slug].astro` | Static dynamic | Blog (10 posts MDX en content collection) |
| `bodas.astro` | Static | Landing bodas |
| `como-llegar.astro` | Static | Guide ruta CDMX → Pie de la Cuesta (SEO marketing, NO post-booking) |
| `contacto.astro` | Static | Form contacto |
| `desde/[ciudad].astro` | Static dynamic | SEO landings origen (cdmx, edomex, puebla, cuernavaca) |
| `eventos-corporativos.astro` | Static | Landing eventos corporate |
| `faq.astro` | Static | FAQ (content collection faqs.json) |
| `fiestas-fin-de-ano.astro` | Static | Landing seasonal |
| `login.astro` + `logout.astro` | Static + SSR | Better Auth magic link entry |
| `mi-cuenta/` | SSR | datos.astro, index.astro, reservas (auth-gated) |
| `mi-estancia/index.astro` | SSR | Post-booking dashboard (auth-gated, basic) |
| `offline.astro` | Static | PWA offline placeholder |
| `pago/` | SSR | Payment success/fail callbacks |
| `pie-de-la-cuesta.astro` | Static | SEO landing destino |
| `privacidad.astro` | Static | Política privacy |
| `proxReservas.astro?pass=vivamexico` | SSR | Staff temporal view (NO admin) |
| `r/admin.astro` + `r/[channel].astro` + `r/index.astro` | Mixed | Linktree custom + tracking |
| `reservar/[propertyId].astro` | SSR | Booking flow (PR1, MP integration) |
| `reuniones-familiares.astro` | Static | Landing |
| `reviews.astro` | Static | Página reseñas (legacy, pre-Track C carousel) |
| `rss.xml.ts` | API | RSS blog |
| `semana-santa-acapulco.astro`, `temporada-baja-acapulco.astro`, `villa-vs-hotel-acapulco.astro`, `zonas-acapulco.astro` | Static | SEO landings |
| `tour-virtual/index.astro` + 2 sub | Static | Tour 360° landing + per-property |

### Páginas EN (`/en/`)

| Path | ES equivalent |
|---|---|
| `en/index.astro` | / |
| `en/[propertyId].astro` | /[propertyId] |
| `en/contact.astro` | /contacto |
| `en/corporate-events.astro` | /eventos-corporativos |
| `en/family-gatherings.astro` | /reuniones-familiares |
| `en/faq.astro` | /faq |
| `en/how-to-get-here.astro` | /como-llegar |
| `en/pie-de-la-cuesta.astro` | /pie-de-la-cuesta |
| `en/privacy.astro` | /privacidad |
| `en/virtual-tour.astro` | /tour-virtual |
| `en/weddings.astro` | /bodas |

**Cobertura EN**: 10 de ~30 páginas ES traducidas. Falta: blog, desde/, fiestas-fin-de-ano, semana-santa, temporada-baja, villa-vs-hotel, zonas-acapulco, mi-cuenta, mi-estancia, reviews, reservar, tour-virtual sub-pages, login/logout, error pages, /como-llegar IS translated as how-to-get-here.

### Admin (Phase B.0.5)

| Path | Estado |
|---|---|
| `admin/index.astro` | ✅ Live (cards: Templates, Health, Inbox/Bookings disabled) |
| `admin/templates/index.astro` + `[name].astro` | ✅ Live (R2-backed CRUD) |
| `admin/health.astro` | 🟡 PR #8 pending merge |

### API endpoints

| Path | Propósito |
|---|---|
| `api/account/*` | Better Auth user mgmt |
| `api/admin/templates/*` | Templates CRUD (R2) |
| `api/auth/*` | Better Auth magic link |
| `api/availability.ts` | Beds24 availability proxy |
| `api/booking/*` | Booking flow ops |
| `api/concierge.ts`, `contact.ts`, `hold.ts`, `quote.ts`, `waitlist.ts` | Form submissions |
| `api/payment-link.ts` | MP preference creation |
| `api/r/*` | Linktree click tracking |
| `api/receipt/*` | Booking receipts |
| `api/reviews/[roomId].ts` | Track C reviews API |
| `api/tour-tracking.ts` | Tour 360° analytics |

---

## 2. Content collections (`src/content/`)

| Collection | Format | # Items | Purpose |
|---|---|---|---|
| `properties/` | JSON | 5 (RdM, Morenas, Combinada, Huerta, Casa Chamán) | Property data: name, slug, room_id, bedrooms, capacity, amenities, images, long/short pitch ES+EN, rating |
| `blog/` | MDX | 10 posts | SEO articles (Pie de la Cuesta guide, Acapulco vs Tulum, weddings, gastronomy, etc.) |
| `landings/` | JSON | varies (ES + en/) | SEO landing data |
| `faqs.json` | JSON | 1 array | FAQs page |
| `reviews/` | JSON | 1 cache file (airbnb-cache.json) | Static reviews snapshot pre-Track C |
| `photo-mapping.json` | JSON | 1 | Image ID → CF Images URL mapping |

### Properties JSON shape (es es+en built-in)

Cada `{slug}.json` tiene fields como:
- `id`, `name`, `slug`, `status`, `room_id`, `capacity`, `bedrooms`, `beds`, `baths`
- `hero_image_id`, `gallery_image_ids[]`
- `short_pitch`, `short_pitch_en`
- `long_description`, `long_description_en`
- `amenities[]`, `services_included[]`, `services_optional[]`
- `location` (lat/lng/address)
- `rating` (average + count)
- `airbnb_url`
- `pricing` (base_guests, extras, cleaning_fee)

**Implicación para Welcome Guide**: estructura ya soporta i18n field-level (`_en` suffix). Podemos agregar campos como `welcome_guide_es`, `welcome_guide_en` o mantenerlos en JSON separado.

---

## 3. i18n setup

### Astro built-in (`astro.config.mjs`)

```js
i18n: {
  defaultLocale: 'es',
  locales: ['es', 'en'],
  routing: {
    prefixDefaultLocale: false,        // ES en root /
    redirectToDefaultLocale: false,     // /en/ no redirect
  },
}
```

### Sitemap integration
```js
sitemap({
  i18n: {
    defaultLocale: 'es',
    locales: { es: 'es-MX', en: 'en-US' },
  },
})
```

### Pattern observado
- ES: `/foo.astro` → `rincondelmar.club/foo`
- EN: `/en/foo.astro` → `rincondelmar.club/en/foo`
- Astro `Astro.currentLocale` detecta `'es'` o `'en'` automáticamente

**Implicación Welcome Guide**: agregar `/welcome/[property].astro` (ES) + `/en/welcome/[property].astro` (EN) sigue pattern existente. URLs serían:
- `rincondelmar.club/welcome/rincon-del-mar`
- `rincondelmar.club/en/welcome/rincon-del-mar`

---

## 4. Auth (Better Auth)

- **Magic link only** (sin password) — Resend backend
- Sessions HTTP-only cookies
- D1 tables: users, sessions, accounts, magic_links, verifications (migration 0001-0002)
- `Astro.locals.user` populated by middleware

### Routes protegidas (`apps/web/src/middleware.ts`)
```ts
const PROTECTED = ['/mi-cuenta', '/reservar', '/r/admin', '/admin'];
```
Sin login → redirect a `/login?next=...`

### Admin authorization
- `isAdmin(env, user.email)` helper en `lib/admin.ts`
- Lee `ADMIN_EMAILS` env var (canonical: `admin@rincondelmar.club`)
- Aplicado en `/admin/*` páginas + `/api/admin/*` endpoints

---

## 5. Data flow stack (resumen)

```
Browser → Astro page (SSR si prerender:false, static si prerender:true)
       ↓
Cloudflare Pages worker
       ↓
       ├─ D1 (rincon database)
       │   ├─ Phase 0 tables: reviews, bot_messages_inbox, conversations, beds24_events
       │   ├─ Phase B Guest 360 (vacías): guests, leads, beds24_bookings, guest_events
       │   ├─ Web booking (5 rows test): bookings, quote_requests, waitlist
       │   └─ Auth: users, sessions, magic_links
       │
       ├─ R2 buckets:
       │   ├─ rdm-knowledge (knowledge bucket — has templates/ prefix + availability.json + prices.json)
       │   └─ assetsrdm
       │
       └─ External APIs:
           ├─ Beds24 v2 (availability + bookings + messages + reviews)
           ├─ MercadoPago (payment preferences)
           ├─ Resend (magic link emails)
           ├─ ManyChat (WhatsApp send via worker-bot)
           └─ Anthropic (Claude Haiku LLM, prompt caching)
```

---

## 6. Hallazgos críticos relevantes para Welcome Guide

### 🔴 `/guia-llegada` NO existe pero templates linkean

Templates AirBnB que linkean a `https://rincondelmar.club/guia-llegada`:
- `PROG: 30 - Dos semanas antes Rdm` (línea 489 templates file)
- `PROG: 40 - Una semana antes - ambas` (línea 554)
- Kit WhatsApp T-7 Huerta menciona la URL

**Status real**: `/guia-llegada` devuelve **404**. Página NO existe en `apps/web/src/pages/`. Lo que existe es `/como-llegar.astro` (otro propósito: SEO marketing ruta CDMX, NO welcome content).

**Implicación**: clientes que click el link en T-14 / T-7 ven 404. Probablemente NO reportado porque solo se manda manualmente cuando Alex envía template. Pero es bug latente de larga data.

### 🟡 Página por propiedad existe, NO tiene welcome content

`/[propertyId].astro` es la **landing pública SEO/marketing** de cada propiedad — NO un welcome post-booking. Tiene fotos, descripción, amenities, FAQs, BookingCard CTA, ReviewsCarousel (Track C). Es para CONVENCER guest a reservar, no para apoyar guest YA reservado.

### 🟡 `/mi-estancia` existe pero placeholder

`pages/mi-estancia/index.astro` existe como SSR auth-gated route. Es el lugar natural donde un Welcome Guide auth-gated con datos sensibles (clave caja, WiFi password) podría vivir. Inspeccionar contenido para confirmar si está implementada o solo skeleton.

### ✅ Pattern para Welcome Guide ya hay infraestructura

Lo que ya tenemos que se REUSA:
- i18n built-in Astro (es + en con `/en/` prefix)
- Content collections para data tipada (properties JSON ya tiene fields per-property)
- React islands para interactividad (carousel, sticky nav, etc.)
- Better Auth para gate de info sensible
- R2 storage para assets dinámicos (templates pattern de Phase B.0.5)
- D1 para data Beds24 booking-specific

---

## 7. Pages que probablemente debamos crear o cambiar

| Page | Acción |
|---|---|
| `/welcome/[property].astro` | NUEVA — Welcome Guide pública (Capa 3 thread/36) |
| `/en/welcome/[property].astro` | NUEVA — Welcome EN |
| `/guia-llegada` o redirect | Decidir: ¿crear como alias `/welcome` general o redirect a `/welcome/[property]` específica? |
| `/mi-estancia/[bookingId]` o similar | EXTENDER — auth-gated welcome con clave caja/WiFi cuando hay booking activo |
| `/eventos.astro` | NUEVA — paquete bodas + eventos $1,400 detallado (per WC sección 5.3 matriz) |

---

## 8. Estado de los archivos relevantes

```
apps/web/
├── astro.config.mjs                     i18n built-in habilitado ✅
├── src/
│   ├── pages/
│   │   ├── [propertyId].astro          static SEO (existe ✅, separar de welcome)
│   │   ├── como-llegar.astro           SEO ruta CDMX (existe ✅, NO welcome)
│   │   ├── (NO welcome/)               🔴 falta crear
│   │   ├── (NO guia-llegada)           🔴 templates linkean a 404
│   │   ├── eventos-corporativos.astro  existe ✅ pero corporate-only
│   │   ├── (NO eventos.astro)          🟡 paquete $1,400 sin home page
│   │   ├── mi-estancia/index.astro     SSR auth (esqueleto, verificar)
│   │   ├── reservar/[propertyId].astro PR1 booking flow (existe ✅)
│   │   └── admin/                      Phase B.0.5 (existe ✅)
│   ├── content/properties/*.json       Per-property data (existe ✅, extender con welcome fields o separate file)
│   └── middleware.ts                    Auth gate /admin + /mi-cuenta + /reservar (existe ✅)
└── tsconfig.json
```

---

## 9. Resumen para el review WC

✅ **Stack está listo**: Astro i18n + R2 + D1 + Better Auth = todos los building blocks para Welcome Guide existen y son production-tested.

✅ **Pattern admin/templates** demuestra que CC puede construir UI dinámica con R2 backend en ~10h (PR #5-#7 thread/35).

🔴 **`/guia-llegada` 404 bug** debe arreglar antes o como parte de Welcome Guide rollout.

🟡 **`/mi-estancia`** es candidato para auth-gated welcome con datos sensibles (vs `/welcome` público para info general).

🟢 **`/eventos.astro` page faltante** — paquete bodas $1,400 detallado solo vive en kits + 1 doc; templates AirBnB todavía dicen $1,000. Página SEO autoritativa rompería el ciclo de inconsistencias.

— Claude Code (CLI), 2026-05-13
