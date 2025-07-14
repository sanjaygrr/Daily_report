# Daily Report - Despliegue en Railway

## Configuración para Railway

Esta aplicación Django está configurada para funcionar con Railway y PostgreSQL.

### Variables de Entorno Requeridas

En Railway, configura las siguientes variables de entorno:

```bash
DATABASE_URL=postgresql://postgres:WObyFTcYrpUmyrgzonsPspZTqHrNmPtD@turntable.proxy.rlwy.net:29028/railway
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=False
ALLOWED_HOSTS=*.railway.app,*.up.railway.app
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=sanjaygr@gmail.com
EMAIL_HOST_PASSWORD=zkaododvautzzqfm
```

### Pasos para el Despliegue

1. **Conectar con GitHub:**
   - Ve a Railway y conecta tu repositorio de GitHub
   - Selecciona el repositorio que contiene este proyecto

2. **Configurar Variables de Entorno:**
   - En la sección de Variables de Railway, añade todas las variables mencionadas arriba

3. **Despliegue Automático:**
   - Railway detectará automáticamente que es una aplicación Django
   - Ejecutará las migraciones automáticamente
   - Creará un superusuario por defecto (admin/admin123)

4. **Acceso a la Aplicación:**
   - Una vez desplegada, Railway te proporcionará una URL
   - Accede con las credenciales: admin/admin123

### Estructura del Proyecto

```
Daily_report/
├── proyecto/          # Configuración principal de Django
├── registros/         # Aplicación principal
├── static/           # Archivos estáticos
├── templates/        # Plantillas HTML
├── requirements.txt  # Dependencias de Python
├── Procfile         # Configuración para Railway
├── runtime.txt      # Versión de Python
├── railway.json     # Configuración específica de Railway
└── migrate.py       # Script de migración
```

### Características Implementadas

- ✅ Configuración para PostgreSQL
- ✅ Migraciones automáticas
- ✅ Creación de superusuario automática
- ✅ Servir archivos estáticos con WhiteNoise
- ✅ Configuración de seguridad para producción
- ✅ Configuración de correo electrónico
- ✅ Zona horaria de Chile
- ✅ Idioma en español

### Solución de Problemas

1. **Error de migraciones:**
   - Verifica que la URL de la base de datos sea correcta
   - Revisa los logs en Railway

2. **Error de archivos estáticos:**
   - Ejecuta `python manage.py collectstatic` localmente
   - Sube los archivos estáticos al repositorio

3. **Error de conexión a la base de datos:**
   - Verifica que la URL de PostgreSQL sea correcta
   - Asegúrate de que la base de datos esté activa en Railway

### Comandos Útiles

```bash
# Ejecutar migraciones localmente
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Ejecutar el servidor de desarrollo
python manage.py runserver
```

### Notas Importantes

- La aplicación está configurada para producción (DEBUG=False)
- Los archivos estáticos se sirven con WhiteNoise
- La base de datos PostgreSQL está configurada con SSL
- Las migraciones se ejecutan automáticamente en cada despliegue 