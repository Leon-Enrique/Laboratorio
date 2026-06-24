# Despliegue demo gratis — Genotipia LIMS

Guía para publicar **proyecto completo** (web pública + admin + API) con **base de datos vacía nueva**, sin costo, para mostrar al ingeniero.

## Arquitectura (separada)

```
Vercel   →  Angular (web + /admin)     genotipia-lab.vercel.app
Render   →  FastAPI (API / puente)     genotipia-api.onrender.com
Neon     →  PostgreSQL (BD vacía)      solo conexión interna
GitHub   →  código                     Leon-Enrique/Laboratorio
```

**No se sube** la base de datos de tu PC. Todo empieza limpio en la nube.

---

## Antes de empezar (checklist)

- [ ] Código en GitHub actualizado
- [ ] Cuenta GitHub activa
- [ ] ~1–2 horas libres la primera vez

---

## Paso 1 — Base de datos (Neon)

1. Entra a [neon.tech](https://neon.tech) → **Sign up** con GitHub.
2. **New Project** → nombre `genotipia` → región cercana.
3. Copia la **connection string** (PostgreSQL), debe incluir `?sslmode=require`:
   ```
   postgresql://usuario:clave@ep-xxx.neon.tech/neondb?sslmode=require
   ```
4. Guárdala; la usarás en Render.

La BD arranca **vacía** (sin pacientes ni órdenes de tu PC).

---

## Paso 2 — API (Render)

1. Entra a [render.com](https://render.com) → **Sign up** con GitHub.
2. **New → Blueprint** (o Web Service manual).
3. Conecta el repo **`Leon-Enrique/Laboratorio`**.
4. Render detectará `render.yaml` en la raíz y creará **`genotipia-api`**.

### Si creas el servicio a mano

| Campo | Valor |
|-------|--------|
| Name | `genotipia-api` |
| Root Directory | `laboratorio-bioquimica-backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | **Free** |
| Health Check Path | `/health` |

### Variables de entorno (Environment)

Use la plantilla `laboratorio-bioquimica-backend/.env.render.example`:

| Variable | Valor |
|----------|--------|
| `APP_ENV` | `production` |
| `DATABASE_URL` | *(connection string de Neon)* |
| `SECRET_KEY` | *(Render puede generarla, o `python -c "import secrets; print(secrets.token_urlsafe(48))"`)* |
| `FRONTEND_URL` | `https://genotipia-lab.vercel.app` |
| `API_PUBLIC_URL` | `https://genotipia-api.onrender.com` |
| `CORS_ORIGINS` | `https://genotipia-lab.vercel.app` |
| `PUBLIC_SITE_URL` | `https://genotipia-lab.vercel.app` |
| `SKIP_MRP_ON_APROBAR` | `true` *(demo sin inventario cargado)* |
| `PDF_WATERMARK` | `false` *(PDF más rápido en cloud)* |
| `AUTO_MIGRATE` | `true` |
| `RUN_LEGACY_SCHEMA_PATCHES` | `true` |
| `RUN_DATA_BACKFILL` | `false` |

5. **Deploy** y espere a que quede **Live**.
6. Pruebe: `https://genotipia-api.onrender.com/health` → debe responder `{"status":"healthy",...}`.
7. Documentación API: `https://genotipia-api.onrender.com/docs`

### Datos iniciales (una sola vez)

En Render → servicio `genotipia-api` → **Shell**:

```bash
python run_init_db.py
```

Crea usuario admin y datos mínimos de demo (proveedores, reactivos ejemplo).

**Login demo:**
- Email: `admin@laboratorio.com`
- Contraseña: `admin123`

> Cambie la contraseña después si la demo queda pública.

---

## Paso 3 — Web (Vercel)

1. Entra a [vercel.com](https://vercel.com) → **Sign up** con GitHub.
2. **Add New → Project** → importa **`Laboratorio`**.
3. Configuración:

| Campo | Valor |
|-------|--------|
| Framework Preset | Angular |
| Root Directory | `laboratorio-bioquimica-web` |
| Build Command | `npm run build -- --configuration=production` |
| Output Directory | `dist/laboratorio-bioquimica-web/browser` |

4. **Deploy**.

El archivo `vercel.json` ya incluye rewrites para que `/admin` funcione al recargar la página.

### URLs en el código

`environment.production.ts` ya apunta a:

- Web: `https://genotipia-lab.vercel.app`
- API: `https://genotipia-api.onrender.com/api/v1`

**Importante:** al crear el proyecto en Vercel, use el nombre **`genotipia-lab`** para que la URL coincida. Si usa otro nombre, actualice:

1. `laboratorio-bioquimica-web/src/environments/environment.production.ts`
2. Variables `FRONTEND_URL` y `CORS_ORIGINS` en Render
3. `git push` → Vercel redeploya solo

---

## Paso 4 — Probar

| Qué | URL |
|-----|-----|
| Sitio público | `https://genotipia-lab.vercel.app` |
| Login / admin | `https://genotipia-lab.vercel.app/login` |
| Panel | `https://genotipia-lab.vercel.app/admin` |
| API docs | `https://genotipia-api.onrender.com/docs` |

Flujo sugerido para el ingeniero:
1. Login admin
2. Nueva orden → resultados → PDF
3. Inventario / compras (MRP)

---

## Plan free: espera al despertar la API

Si nadie usó el sistema ~15 minutos, la **primera** petición (login) puede tardar **30–60 segundos**.

**Antes de la demo:** abra `https://genotipia-api.onrender.com/health` 5 minutos antes.

---

## Qué NO hace falta ahora

- Dominio propio (`genotipia-lab.com`) — opcional después
- Migrar datos de su PC — la BD en Neon es nueva y vacía
- Tarjeta en Neon/Vercel — gratis; Render a veces la pide pero no cobra en free tier

---

## Actualizar después de cambios en código

1. En su PC: `git commit` + `git push`
2. Vercel y Render redeployan automáticamente (1–3 min)
3. La BD en Neon **no se borra** con un deploy normal

---

## Problemas frecuentes

| Síntoma | Solución |
|---------|----------|
| Login no responde / CORS | Verifique `CORS_ORIGINS` y `FRONTEND_URL` en Render = URL exacta de Vercel |
| 404 al recargar `/admin` | Debe existir `vercel.json` (ya incluido) |
| Build Vercel falla | Ejecute local: `npm run build -- --configuration=production` |
| API no arranca | Revise `DATABASE_URL` (Neon + `sslmode=require`) y `SECRET_KEY` |
| Tablas vacías | Ejecute `python run_init_db.py` en Shell de Render |

---

## Cuando pase a producción de pago

- Dominio propio + HTTPS
- Render de pago o VPS (sin “sueño” de 60 s)
- `AUTO_MIGRATE=false` + migraciones en deploy
- Backup diario (`scripts/backup_db.ps1` o cron)
- Cambiar contraseña admin y `SECRET_KEY` definitiva

Ver también: [DEPLOY.md](./DEPLOY.md) (VPS / dominio propio).
