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
CSRF_TRUSTED_ORIGINS=https://*.railway.app,https://*.up.railway.app
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=sanjaygr@gmail.com
EMAIL_HOST_PASSWORD=zkaododvautzzqfm
```

### Solución de Problemas Comunes

#### 1. Error CSRF (403 Forbidden)

Si recibes un error CSRF, asegúrate de que las siguientes variables estén configuradas:

```bash
CSRF_TRUSTED_ORIGINS=https://tu-app.railway.app,https://tu-app.up.railway.app
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**Nota:** Reemplaza `tu-app` con el nombre real de tu aplicación en Railway.

#### 2. Imágenes no aparecen

Para solucionar problemas con imágenes:

1. **Verifica que los archivos estáticos estén recolectados:**
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Asegúrate de que el directorio `staticfiles` esté incluido en el repositorio**

3. **Verifica la configuración de WhiteNoise en `settings.py`**

#### 3. Archivos Media no se cargan

Los archivos media (logos de empresas, etc.) se sirven desde el servidor. Asegúrate de que:

1. El directorio `media/` esté creado
2. Los permisos de escritura estén configurados correctamente
3. La configuración de URLs incluya el patrón para servir archivos media

### Pasos para el Despliegue

1. **Conectar con GitHub:**
   - Ve a Railway y conecta tu repositorio de GitHub
   - Selecciona el repositorio que contiene este proyecto

2. **Configurar Variables de Entorno:**
   - En la sección de Variables de Railway, añade todas las variables mencionadas arriba
   - **IMPORTANTE:** Asegúrate de que `CSRF_TRUSTED_ORIGINS` incluya la URL exacta de tu aplicación

3. **Despliegue Automático:**
   - Railway detectará automáticamente que es una aplicación Django
   - Ejecutará las migraciones automáticamente
   - Recolectará archivos estáticos
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
├── staticfiles/      # Archivos estáticos recolectados
├── media/           # Archivos media (logos, etc.)
├── templates/        # Plantillas HTML
├── requirements.txt  # Dependencias de Python
├── Procfile         # Configuración para Railway
├── runtime.txt      # Versión de Python
├── railway.json     # Configuración específica de Railway
├── railway.toml     # Variables de entorno para Railway
├── migrate.py       # Script de migración
├── setup_static.py  # Script de configuración de archivos estáticos
└── check_deployment.py # Script de verificación
```

### Características Implementadas

- ✅ Configuración para PostgreSQL
- ✅ Migraciones automáticas
- ✅ Creación de superusuario automática
- ✅ Servir archivos estáticos con WhiteNoise
- ✅ Servir archivos media en producción
- ✅ Configuración de seguridad para producción
- ✅ Configuración CSRF para Railway
- ✅ Configuración de correo electrónico
- ✅ Zona horaria de Chile
- ✅ Idioma en español

### Solución de Problemas

1. **Error de migraciones:**
   - Verifica que la URL de la base de datos sea correcta
   - Revisa los logs en Railway

2. **Error de archivos estáticos:**
   - Ejecuta `python setup_static.py` localmente
   - Sube los archivos estáticos al repositorio

3. **Error de conexión a la base de datos:**
   - Verifica que la URL de PostgreSQL sea correcta
   - Asegúrate de que la base de datos esté activa en Railway

4. **Error CSRF persistente:**
   - Verifica que `CSRF_TRUSTED_ORIGINS` incluya la URL exacta de tu aplicación
   - Asegúrate de que `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` estén configurados

### Comandos Útiles

```bash
# Ejecutar migraciones localmente
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Configurar archivos estáticos y media
python setup_static.py

# Verificar configuración
python check_deployment.py

# Ejecutar el servidor de desarrollo
python manage.py runserver
```

### Notas Importantes

- La aplicación está configurada para producción (DEBUG=False)
- Los archivos estáticos se sirven con WhiteNoise
- Los archivos media se sirven desde el servidor
- La base de datos PostgreSQL está configurada con SSL
- Las migraciones se ejecutan automáticamente en cada despliegue
- Los archivos estáticos se recolectan automáticamente en cada despliegue

### Verificación Post-Despliegue

Después del despliegue, verifica que:

1. ✅ Puedes acceder a la aplicación sin errores CSRF
2. ✅ Las imágenes y archivos estáticos se cargan correctamente
3. ✅ Puedes subir logos de empresas
4. ✅ Las migraciones se ejecutaron correctamente
5. ✅ El superusuario se creó (admin/admin123) 