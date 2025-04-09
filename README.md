# 📋 Daily Report - Sistema de Gestión de Trabajos y Maquinaria

## 📝 Descripción

**Daily Report** es una aplicación web desarrollada con **Django** que permite gestionar registros de trabajos, maquinaria, faenas y usuarios en un entorno empresarial. Diseñada especialmente para empresas que necesitan llevar un control detallado de sus operaciones diarias, mantenimiento de maquinaria y asignación de recursos.

## ✨ Características

- 👥 Control de usuarios con diferentes roles (Admin, Supervisor, Trabajador)  
- 🔧 Gestión de maquinaria y registro de horas/kilómetros de trabajo  
- 🏗️ Administración de faenas y asignación de trabajos  
- 📊 Reportes y exportación a Excel y PDF  
- 📱 Diseño responsive basado en Bootstrap 5  
- 🔐 Sistema de autenticación y control de permisos  
- 🏢 Gestión de empresas con datos completos y logos  

## 🛠️ Tecnologías Utilizadas

- 🐍 Python 3.x  
- 🎯 Django 5.1.x  
- 💾 SQLite (Base de datos por defecto)  
- 🎨 Bootstrap 5 para UI  
- 📑 ReportLab para generación de PDFs  
- 📊 OpenPyXL para generación de Excel  
- 🔄 Django Import/Export para importación y exportación de datos  

## 📋 Requisitos

- Python 3.x  
- Dependencias listadas en `requirements.txt`  

## ⚙️ Instalación

Clona este repositorio:

```bash
git clone https://github.com/tuusuario/daily-report.git
cd daily-report
```

Crea y activa un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Realiza las migraciones:

```bash
python manage.py migrate
```

Crea un superusuario:

```bash
python manage.py createsuperuser
```

Inicia el servidor:

```bash
python manage.py runserver
```

Accede a la aplicación en tu navegador:

```
http://localhost:8000/
```

## 🚀 Uso

### Roles de Usuario

- **Superusuario**: Acceso completo a todas las funcionalidades del sistema y puede visualizar todas las empresas registradas.  
- **Admin**: Puede gestionar todo lo relacionado con su empresa específica (usuarios, máquinas, faenas, etc.).  
- **Supervisor**: Gestiona y aprueba los trabajos realizados por los trabajadores.  
- **Trabajador**: Solo puede completar formularios de trabajo y ver su historial personal.  

### Funcionalidades Principales

- 📝 **Crear Trabajo**: Registro de trabajos con información detallada de máquina, faena y mediciones (disponible para todos los usuarios).  
- 📚 **Historial**: Visualización y filtrado de trabajos registrados (cada usuario ve según su nivel de acceso).  
- ✅ **Pendientes**: Lista de trabajos pendientes de aprobación (accesible para Supervisores y roles superiores).  
- 🔧 **Gestión de Máquinas**: Creación, edición y eliminación de máquinas (Supervisores y roles superiores).  
- 🏗️ **Gestión de Faenas**: Administración de faenas o sitios de trabajo (Supervisores y roles superiores).  
- 👥 **Usuarios**: Administración de usuarios y asignación de roles (Admin y Superusuario).  
- 🏢 **Empresas**: Gestión de datos empresariales (exclusivo para Superusuario).  

## 📊 Modelos de Datos

- **Trabajo**: Registro central que contiene la información de un trabajo realizado.  
- **Maquina**: Registro de maquinarias disponibles.  
- **Faena**: Registro de faenas o sitios de trabajo.  
- **Empresa**: Información de la empresa con datos de contacto y administración.  

## 📁 Estructura del Proyecto

```
daily-report/
├── manage.py
├── proyecto/               # Configuración principal de Django
├── registros/              # Aplicación principal
│   ├── migrations/         # Migraciones de base de datos
│   ├── templates/          # Plantillas HTML
│   ├── templatetags/       # Tags personalizados
│   ├── admin.py            # Configuración del admin
│   ├── forms.py            # Formularios
│   ├── models.py           # Modelos de datos
│   ├── urls.py             # URLs de la aplicación
│   └── views.py            # Vistas y lógica de negocio
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
├── requirements.txt        # Dependencias del proyecto
└── .gitignore              # Archivos ignorados por git
```

## 🔒 Seguridad

- Sistema de autenticación integrado de Django  
- Protección contra CSRF  
- Acceso restringido según roles de usuario con permisos jerárquicos:
  - **Trabajador**: Acceso básico solo a formularios de trabajo  
  - **Supervisor**: Gestión de trabajadores y aprobación de trabajos  
  - **Admin**: Gestión completa dentro de su empresa  
  - **Superusuario**: Control total del sistema y todas las empresas  
- Validación de datos en formularios  
- Segregación de datos por empresa  

## 🤝 Contribución

1. Haz un fork del proyecto  
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)  
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)  
4. Haz push a la rama (`git push origin feature/amazing-feature`)  
5. Abre un Pull Request  

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## 📞 Contacto

Sanjay Ramchandani - sanjaygr@gmail.com
Enlace del proyecto: [https://github.com/sanjaygrr/Daily_report](https://github.com/sanjaygrr/Daily_report)

---

⚡️ *Daily Report - Convirtiendo datos en decisiones*
```
