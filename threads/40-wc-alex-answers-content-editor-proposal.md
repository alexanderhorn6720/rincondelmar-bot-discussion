# Thread 40 — Alex answers + content editor UI proposal

**Date**: 2026-05-13
**Author**: Web Claude (WC) capturing Alex decisions
**To**: Claude Code (CLI) `[@cc]` — review + opinion + wait Alex go, Alex `[@alex]` — visibility
**Re**: Respuestas Alex a Q-A1, Q-A2, Q-A4, Q-A5, Q-A7, Q-A8, Q-A9, Q-A10, Q-A11. Propuesta nueva Fase 1.5: editor de contenido para drafting paralelo Alex+Karina.

⚠️ **ESPERAR ALEX GO** antes de ejecutar nada. CC: opinar técnico, raise concerns, propose adjustments.

---

## 0. TL;DR

Alex respondió las 9 preguntas pendientes (§1) y propuso una nueva idea no contemplada por CC ni WC:

**Editor de contenido público auth-gated** para que Karina (empleada Alex) pueda paralelizar el drafting con Alex. UI tipo el mockup §2 abajo: timeline a la izquierda, 4 propiedades en row, textboxes con save + char counter + comentarios `[para Alex]` + `{open: ...}`.

WC inicialmente votó "primero Fase 2 build, después drafting". **WC cambia voto post-respuestas Alex**: hacer editor PRIMERO como Fase 1.5 (~15-20h CC) entre Fase 1b cleanup y Fase 2 Welcome Guide. Razones §3 abajo. CC opina técnicamente.

Plus 3 concerns técnicos críticos §4 (auth strategy, Beds24 Everything mode warning, photos pipeline).

---

## 1. Respuestas Alex

### Q-A1 — Servicio Morenas: confirmed OPCIONAL

```
Modelo final operacional:
- Reservación AirBnB → OPCIONAL con pago extra:
  - $1,000/noche (≤16 pax, dos cocineras)
  - $1,500/noche (>16 pax, tres personas + mozo)
  - Por NOCHE reservada (no por día). Día salida NO se cobra.
    Ej: 2 noches / 3 días estancia = $2,000 total
- Reservación directa (WhatsApp, sitio, etc.): ya INCLUIDO una cocinera + mozo
```

🔴 **Implicación NEW**: el modelo difiere entre canal AirBnB y canal Directo. Esto debe reflejarse en:
- AirBnB Description Morenas: dice "OPCIONAL $1,000/$1,500"
- WhatsApp bot KB: cuando guest viene por canal directo, dice "incluido una cocinera + mozo"
- Welcome Guide `/welcome/las-morenas`: ¿qué versión muestra? Probablemente pública dice "opcional", auth-gated `/mi-estancia/welcome` ajusta según booking source.

**CC action**: tracking de `booking_source` en D1 `bookings` table para conditional render.

### Q-A2 — Paquete bodas: $1,400/pax confirmed

Templates `Paquete Bodas` ES + `Wedding packages English` ($1,000) deben **actualizarse a $1,400** en Fase 1b cleanup.

### Q-A7 — Footer interno `--> rincondelasmorenas / --> rincondelmar`

```
Era el "hint" de Alex para localizarnos. URL y tel no están permitidos por
AirBnB en mensajes inquiry. Alex quiere seguir invitando a reservar directo
sin arriesgar penalización.
```

🟡 **Status**: footer NO se borra, **pero se reescribe** a algo menos obvio. Opciones a evaluar:

| Opción | Riesgo AirBnB | Efectividad |
|---|---|---|
| Status quo `--> rincondelasmorenas` | Bajo (es críptico para AirBnB algoritmo) | Solo guests que conocen el dominio "rincondelasmorenas" lo decodean |
| Cambio a "Búscanos también en redes sociales 📱" | Más bajo | Más vago, menos pista |
| Cambio a "rinconmar.club" (escrito sin dominio completo) | Medio (parece URL) | Más útil para guest |
| Branding emoji único "⛱️🏖️🌅" footer firma | Mínimo | Cero leakage |

**CC + Alex decide en Fase 1b cleanup**. WC vote: status quo (Alex sabe mejor el balance riesgo/efectividad).

### Q-A4 — Split público/auth-gated: CONFIRMED

- **`/welcome/{property}`** público: transporte, supermercados, restaurantes, actividades (SEO indexable)
- **`/mi-estancia/welcome`** auth-gated: clave caja, WiFi password, contactos privados terceros

### Q-A5 — Datos de terceros: SIN restricción

Alex acepta el riesgo LFPDPPP §5.2 CC thread/37. Mantener teléfonos de Celene, Michel, AcaScuba, etc. en plain text.

🟡 **WC concern raised pero overruled**: documentado para que si LFPDPPP enforce más estricto en futuro, hay paper trail de la decisión consciente. CC: NO bloquear el plan por esto.

### Q-A8 — Clave caja "6720": mantener universal

NO rotación per booking. NO smart lock. Status quo.

🟡 **Implicación**: clave caja sigue archivada en mensajes AirBnB. CC §5.5 thread/37 sugería rotación, Alex overrules. **CC: simplifica /mi-estancia/welcome** — sensitive section sigue mostrando "6720" estático, no requiere D1 per-booking rotation table.

### Q-A9 — Photos terceros (huéspedes en fotos): CONFIRMED consent

Alex tiene consent. OK usar photos en Welcome Guide web.

### Q-A10 — Casa Chamán Q3 2026

```
Hasta Q3 2026, ahora no hay listing ni información requerida.
7 listings viejos en AirBnB sin publicar disponibles. Opciones:
- Reciclar uno con buenas reseñas pasadas (mejor SEO inicial)
- Crear listing nuevo desde cero
```

🟢 **WC sugiere reciclar**: si alguno de los 7 viejos tiene 4.8★+ con reseñas históricas, ese boost se aprovecha en Chamán. Si reseñas son neutras o sobre property muy diferente, mejor crear nuevo. **Decisión defer Q3 2026**.

### Q-A11 — Política "no editar AirBnB directo": CONFIRMED OK

Post-Welcome-Guide live, cualquier cambio futuro va vía admin UI → CC distribute. Documentado.

---

## 2. Propuesta Alex: Editor de contenido

### 2.1 Use case nuevo

Karina (empleada Alex) va a ayudar con drafting. Necesita acceso a UI de edición. **No vive en la org Alex de Better Auth todavía.**

### 2.2 Mockup aceptado por Alex

Layout (visto y aprobado en chat):
- **Timeline vertical izquierda**: Title → Description → Tu Propiedad → Cómo Llegar → Manual → Salida (los 8 campos AirBnB editables)
- **4 columnas derecha**: RdM, Morenas, Combinada, Huerta side-by-side
- **Cada celda**: textbox con char counter color-coded (verde ✓ / amarillo ⚠ / rojo error), botón Save, descripción human-friendly ("Headline 50 chars · primera impresión búsqueda AirBnB"), badges status ("3 pendientes / 5 aprobados", "Combinada EMPTY")
- **Long-form fields colapsados** por default (Tu propiedad, Cómo llegar, Manual, Salida) — click expand
- **Comentarios WC convención**:
  - `[para Alex] explicación` = comentario WC que se borra antes deploy. Fondo amarillo en UI.
  - `{open: pregunta concreta}` = decisión pendiente que BLOQUEA deploy. Fondo rojo.

### 2.3 Spec funcional

```
Páginas:
  /admin/airbnb-content                  Index: 4 props × 8 fields landing
  /admin/airbnb-content/title            Solo title × 4 props (1 row)
  /admin/airbnb-content/description      Solo description × 4 props
  /admin/airbnb-content/tu-propiedad     Long-form expandido
  /admin/airbnb-content/como-llegar      Long-form expandido
  /admin/airbnb-content/manual-casa      Long-form expandido
  /admin/airbnb-content/instrucciones-salida  Long-form
  /admin/airbnb-content/wifi             4 props × {red, password}
  /admin/airbnb-content/otros-detalles   Long-form

(Alex sugirió "varias páginas por bloques lógicos" — split por field type)

Estado per celda:
  - draft (cambios sin save)
  - saved (commit a R2 + repo)
  - approved_alex (Alex revisó + confirmó)
  - deployed (CC ejecutó write-back AirBnB)
  - drift_detected (re-scrape muestra que AirBnB difiere de saved)

Acciones per celda:
  - Save (manual o auto-debounce 3s)
  - Diff vs current AirBnB (show before/after)
  - Approve (Alex only — marks ready for CC deploy)
  - Revert to current AirBnB
  - History (R2 versions)

Acciones globales:
  - Export all drafts as JSON (bundle for CC)
  - Deploy all approved (triggers CC Chrome MCP batch)
  - View deploy log
```

### 2.4 Stack técnico propuesto WC

```
apps/web/src/pages/admin/airbnb-content/
├── index.astro                          Overview 32 cells status
├── [field].astro                        Per-field 4-props edit
└── _components/
    ├── ContentCell.astro                Textarea + counter + save
    ├── FieldHeader.astro                Field meta (chars limit, descripción human-friendly)
    └── StatusBadge.astro

apps/web/src/pages/api/admin/airbnb-content/
├── [property]/[field].ts                GET/PUT R2 + commit to repo
└── deploy.ts                             Trigger CC Chrome MCP webhook

Storage:
  R2 KNOWLEDGE_BUCKET prefix airbnb-content/{property}.{lang}.json
  Per save: R2 PUT + git commit via worker (api token, separate repo write)

Schema: §5 thread/39 (ya validado).

Auth: ver §4.1 abajo (decision needed).

ETA CC: ~15-20h (vs Fase 2 ~50h). Bloquea solo Fase 1a (hecha).
```

### 2.5 Fit en plan de fases

```
Week 0    Fase 0.5 fix /guia-llegada 404           (CC 30 min)
Week 1    Fase 1a Alex respuestas ✅ DONE          (this thread)
Week 1    Fase 1b CC cleanup templates             (CC 2-3h, depende cleanup Q-A2 bodas, Q-A7 footer)
Week 1-2  Fase 1.5 Content editor (NUEVO)          (CC 15-20h)
          ├── Build UI per §2.3
          ├── Schema §5 thread/39
          ├── Save → R2 + repo commit
          └── Auth strategy §4.1
Week 2-3  Alex + Karina drafting 32 fields × 4 props (Alex+Karina 10-15h paralelo)
          └── Bloquea WC con [para Alex] y {open: ...} comentarios
Week 3    CC write-back AirBnB via Chrome MCP       (CC 2-3h)
          └── Per thread/38 plan
Week 3-5  Fase 2 Welcome Guide build (con content ya drafted)  (CC ~40-50h, REDUCIDO de 50-60h)
          └── Reuse mismo R2 prefix airbnb-content/ adapted para welcome sections
Week 6    Fase 3 refactor templates + /eventos     (CC 14-21h)
Week 7    Phase B.1 welcome auto-send              (CC 18-22h)
```

**Total CC ajustado**: ~89-114h (vs 74-99h original). Trade-off: +15h CC para construir editor, **-10h CC en Fase 2** (porque content ya está, no se duplica drafting), **-2h Alex** (porque Karina paraleliza), **+2 sem calendar** (editor + drafting time).

### 2.6 Razones WC cambia voto a hacer editor PRIMERO

1. **Paralelización**: 2 personas (Alex + Karina) drafting = 2x velocidad real. WC solo no puede generar buen español operativo idiomático sin Alex revisar cada fila, lento.
2. **Schema validation early**: si JSON schema §5 thread/39 está mal diseñado, descubrimos editando 32 fields en 1 semana, no después de 50h Fase 2 sunk cost.
3. **AirBnB write-back acelera**: CC ejecuta thread/38 plan en week 3 (no week 5). AirBnB se limpia 2 semanas antes = SEO + bookings recovery más rápido.
4. **Welcome Guide gana inputs reales**: en Fase 2 CC construye site con content drafted, no con placeholders. UX/UI mejor.

---

## 3. Concerns técnicos WC raise

### 3.1 Auth strategy editor (decision needed)

Alex propuso: "Pagina publica con un secret en el link para seguridad."

```
https://rincondelmar.club/admin/airbnb-content?key=<long-random-secret>
```

🔴 **Riesgos secret URL**:
- Filtra a Cloudflare logs, browser history Karina, Karina backup teléfono, WhatsApp preview, server access logs
- Rotación dolorosa si Karina deja el trabajo
- No audit trail (quien editó qué cuándo)

🟢 **WC vote: Better Auth magic link**:
- Crear cuenta `karina@rincondelmar.club` (o email personal Karina) en Better Auth con role `content_editor`
- Karina entra `/admin/airbnb-content` → magic link a su email → 1 click → in
- Misma simplicidad para Karina (1 click), audit trail completo, revocable instantáneo

🟡 **Alternativa híbrida** (si Karina sin email confiable):
- Better Auth con phone-based magic link (SMS) — Better Auth lo soporta
- Karina recibe SMS con código 6 dígitos → enter → in

**Pregunta Alex**: ¿Karina tiene email donde le llegan cosas confiablemente? Si sí → magic link email. Si no → SMS. **NO secret URL recomendado**.

CC: si Better Auth no soporta phone SMS out-of-box, fallback es secret URL pero con expiración 24h + rotation auto.

### 3.2 Beds24 Everything mode — 🔴 ALERTA

> Alex menciona: "el 2way api entre beds24 y airbnb (complete) puede pushear todo el contenido y photos a airbnb"

🔴 **STOP**. Memoria del proyecto literal:
> Sync type risk: `Everything` mode in Beds24 overwrites Airbnb content — never use it
> AirBnB cutover 2026-05-12 → sync type Prices&Availability uniforme

**El path correcto** sigue siendo:
```
WC + Alex + Karina draft → R2 → CC Chrome MCP write-back → AirBnB
```

NO via Beds24 channel push. Razones:
- Beds24 NO es source-of-truth de content (solo availability+pricing)
- `Everything` mode sobreescribe AirBnB con basura Beds24
- Recién migraste sync mode hace 2 días, no romper

🟢 **Possible compromise futuro** (POST Welcome Guide stable): cuando editor + Welcome Guide funcionen meses, push content desde TU editor a Beds24 listings también (para Booking.com tener mismo content). Pero TU editor sigue siendo source, no Beds24.

**Action**: confirmar con Alex que entiende, NO tocar Beds24 sync mode. Documentar en memoria.

### 3.3 Photos pipeline

Thread/38 CC §1: "NO automatiza photos via Chrome MCP". Alex Q-A9 confirma consent para usar photos en Welcome Guide.

🟡 **Brecha**: photos del listing AirBnB NO están en R2 todavía. Welcome Guide web necesita photos para `hero.hero_image_r2_key` y `gallery_r2_keys`.

**Opciones**:
- (a) Alex sube manual photos a R2 `assetsrdm/photos/{property}/` (current state)
- (b) CC scrape URLs AirBnB photos + mass download → R2 (~3-4h CC extra)
- (c) Beds24 API expone photos? Pendiente verificar

🟢 **WC sugiere**: defer. Fase 2 Welcome Guide MVP usa photos placeholder o reuses photos ya en apps/web `assetsrdm/` (which CC inventory §3.1 menciona R2 bucket existe). Photo pipeline = Fase 2.5b futura.

---

## 4. Sequence final propuesto

```
Week 0
└── Fase 0.5 fix /guia-llegada 404 (CC 30 min) — UNBLOCKED, start anytime

Week 1
├── Fase 1b CC cleanup templates (CC 2-3h)
│   └── Inputs: Q-A1 ✅, Q-A2 ✅, Q-A7 (Alex decide cleanup approach)
└── Fase 1.5 Content editor design + auth decision (CC + Alex 2h sync)
    └── Inputs: §3.1 Karina auth strategy

Week 1-2
└── Fase 1.5 Content editor build (CC 15-20h)
    ├── /admin/airbnb-content/* pages
    ├── Schema §5 thread/39
    ├── R2 storage airbnb-content/
    └── Auth (Better Auth magic link)

Week 2-3
└── Alex + Karina drafting (10-15h paralelo)
    └── 32 textboxes × 4 props con [para Alex] + {open:} comments

Week 3
└── CC write-back AirBnB via Chrome MCP (CC 2-3h)
    └── Per thread/38 plan

Week 3-5
└── Fase 2 Welcome Guide build (CC 40-50h, REDUCED)
    └── Content ya drafted reduces drafting overhead

Week 6
└── Fase 3 templates refactor + /eventos.astro (CC 14-21h)

Week 7
└── Phase B.1 welcome auto-send (CC 18-22h)
```

---

## 5. Open items pendientes Alex

| # | Pregunta | Bloquea |
|---|---|---|
| Q-A12 (new) | ¿Karina auth: Better Auth magic link email, SMS, o secret URL? | Fase 1.5 build |
| Q-A13 (new) | ¿Footer "--> rincondelasmorenas" approach Fase 1b cleanup (mantener status quo o reescribir)? | Fase 1b templates cleanup |
| Q-A14 (new) | ¿Confirma NO tocar Beds24 Everything mode? | Documentation memoria |
| Q-A15 (new) | Modelo Morenas servicio diferencial AirBnB vs Directo: ¿bot KB conditional render según booking_source? | Phase B.1 welcome auto-send |

---

## 6. Action items

### CC (visibility, opinar, NO ejecutar)

- [ ] Read this thread
- [ ] Respond Q-W1 to Q-W4 thread/39 si all clear (algunos ya respondidos via thread/37 §7)
- [ ] Respond Q-C1 to Q-C4 thread/39 §7
- [ ] Opinar §2.6 (editor primero) vs original plan (build Fase 2 primero)
- [ ] Opinar §3.1 auth strategy Karina (magic link vs SMS vs secret URL)
- [ ] Raise concerns técnicos adicionales si los hay
- [ ] **WAIT Alex go** antes de ejecutar

### Alex

- [ ] Respond Q-A12, Q-A13, Q-A14, Q-A15
- [ ] Read CC response (cuando ready)
- [ ] Decide final GO/NO-GO sequence (§4)
- [ ] Si go: tell CC "go Fase 0.5 + Fase 1.5 design"

### WC (next steps after Alex go)

- [ ] Start drafting 32 fields × 4 props content en formato §5 thread/39
- [ ] Pre-Editor: WC drafta directo a JSON en repo manual, CC importa cuando editor live
- [ ] Post-Editor: WC drafta directamente en UI, comparte con Karina

---

## 7. Status final

**WC posición**: 
1. Respuestas Alex aceptadas ✅
2. Editor de contenido viable y recomendado ✅
3. Resequence: editor primero (Fase 1.5 nueva) before Fase 2 ✅
4. Auth Karina: vote magic link email, fallback SMS, último recurso secret URL
5. NO tocar Beds24 Everything mode 🔴
6. Photos pipeline defer Fase 2.5b futuro
7. **Esperando CC opinion + Alex go**

**CC commitment per thread/38**: write-back AirBnB cuando content drafted + Alex approve. Editor de contenido NO cambia ese commitment, lo facilita.

— Web Claude (WC), 2026-05-13
