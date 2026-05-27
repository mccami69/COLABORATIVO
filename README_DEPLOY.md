Despliegue en la nube — opciones y pasos

Resumen: He preparado `Procfile`, `Dockerfile`, `runtime.txt`, un workflow de GitHub Actions para publicar la imagen en GHCR y `.env.example`.

Pasos recomendados (Render - muy fácil):
1. Sube tu repo a GitHub (crear un repo y push).
2. Crea cuenta en https://render.com y crea un nuevo servicio tipo "Web Service".
3. Conecta tu repositorio y selecciona la rama `main`.
4. Render detectará el `Dockerfile` o `Procfile`. En `Start Command` puedes dejar vacío (si usa Dockerfile) o `gunicorn app:app`.
5. Añade variables de entorno (SECRET_KEY, DATABASE_URL, GOOGLE_MAPS_API_KEY) en la configuración del servicio en Render.
6. Deploy automático: cada push a `main` disparará el build en Render.

Pasos recomendados (Azure App Service):
1. Instala Azure CLI y loguéate: `az login`.
2. Crea el App Service o usa `az webapp up --name <mi-app> --runtime "PYTHON:3.11"`.
3. En la configuración de App Service, añade las variables de entorno (Application Settings) equivalentes.
4. Puedes usar el `Dockerfile` y desplegar una imagen de GHCR o usar `az webapp up` para desplegar desde el repo.

Usar la imagen publicada en GHCR (ejemplo):
1. Habilita GitHub Package/Container Registry para tu cuenta/organización.
2. El workflow `publish-ghcr.yml` construirá y publicará `ghcr.io/<owner>/<repo>:latest` cuando hagas push a `main`.
3. Configura el servicio en la nube para extraer esa imagen (Azure, Cloud Run, ACI, etc.) y crea secrets si hace falta.

Variables importantes (añadir en la plataforma):
- `SECRET_KEY` — clave secreta de Flask.
- `DATABASE_URL` — URL de la base de datos (MySQL/Postgres) o dejar sqlite local si lo deseas (no recomendado en producción).
- `GOOGLE_MAPS_API_KEY` — (opcional) clave para mapas.

Siguientes pasos que puedo hacer por ti:
- Puedo crear el repo en GitHub y empujar el proyecto (necesitaré acceso o instrucciones).
- Puedo configurar despliegue automático a Azure/Render si me proporcionas credenciales (tokens) — por seguridad, es mejor que lo hagas tú y yo te oriento paso a paso.
