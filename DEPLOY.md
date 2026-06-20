# Cuando quieras subir Genotipia a internet

Guía corta para el día que termines de mejorar la página y quieras publicar. **Hoy no hace falta hacer nada de esto.**

## Mientras sigues en local (ahora)

- Sigue desarrollando y mejorando la web como hasta ahora.
- Haz `git commit` y `git push` cuando quieras guardar avances en GitHub.
- Opcional: antes de un push grande, verifica que todo compile:

```powershell
.\scripts\check-deploy-ready.ps1
```

Eso solo prueba en tu PC que el proyecto está sano. **No sube nada a internet.**

---

## Cuando estés listo para publicar (más adelante)

### Lo que necesitarás contratar

1. **Dominio** — ej. `genotipia-lab.com`
2. **Servidor (VPS)** — Linux recomendado (DigitalOcean, Hetzner, AWS Lightsail, etc.)
3. **Opcional:** correo profesional para `contacto@genotipia-lab.com`

### Archivos que ya están preparados en el repo

| Archivo | Para qué |
|---------|----------|
| `laboratorio-bioquimica-backend/.env.production.example` | Plantilla de configuración del servidor |
| `laboratorio-bioquimica-web/src/environments/environment.production.ts` | URL de la API en producción |
| `scripts/deploy-update.sh` | Actualizar el sitio en Linux (un comando) |
| `scripts/deploy-update.ps1` | Igual en Windows Server |
| `scripts/nginx-genotipia.conf.example` | Cómo conectar dominio + HTTPS |
| `scripts/genotipia-api.service.example` | API siempre encendida en el servidor |
| `scripts/backup_db.ps1` | Respaldar PostgreSQL |
| `.github/workflows/ci.yml` | GitHub prueba build y tests al hacer push |

### Pasos resumidos (primera vez en el servidor)

1. Instalar en el VPS: Git, Python 3.12, Node 22, PostgreSQL, Nginx.
2. `git clone` de tu repo (ej. en `/opt/Laboratorio`).
3. Copiar y editar entorno:
   ```bash
   cp laboratorio-bioquimica-backend/.env.production.example laboratorio-bioquimica-backend/.env
   # Editar: DATABASE_URL, SECRET_KEY, dominios
   ```
4. Crear base de datos PostgreSQL y usuario.
5. Backend:
   ```bash
   cd laboratorio-bioquimica-backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   python run_init_db.py   # solo primera vez (usuarios iniciales)
   ```
6. Configurar servicio API (`scripts/genotipia-api.service.example`).
7. Build y publicar frontend:
   ```bash
   ./scripts/deploy-update.sh
   ```
8. Nginx + certificado SSL (Let's Encrypt) con `scripts/nginx-genotipia.conf.example`.
9. Probar: `https://genotipia-lab.com` y login admin.

### Cada actualización después (cuando ya está online)

En tu PC: terminas cambios → `git push`.

En el servidor:

```bash
cd /opt/Laboratorio
./scripts/deploy-update.sh
```

Eso baja código nuevo, migra BD si hay cambios, recompila la web y reinicia la API.

### Antes de publicar — checklist mental

- [ ] Precios y textos del sitio público revisados
- [ ] `environment.production.ts` con tu dominio real de API
- [ ] `SECRET_KEY` nueva y larga en `.env` del servidor
- [ ] Cambiar contraseña del admin demo (`admin123`)
- [ ] Probar flujo: orden → resultados → PDF → portal paciente
- [ ] Programar backup (`scripts/backup_db.ps1` o cron en el servidor)

---

## Dudas frecuentes

**¿Puedo seguir cambiando la página después de subir?**  
Sí. Cambias en local, pruebas, `git push`, y en el servidor corres `deploy-update`.

**¿Tengo que entender Alembic ya?**  
No para seguir en local. Solo cuando subas: `alembic upgrade head` (o el script deploy lo hace).

**¿GitHub Actions es obligatorio?**  
No. Solo avisa si algo se rompió al subir código. Puedes ignorarlo hasta entonces.
