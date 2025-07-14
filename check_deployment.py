#!/usr/bin/env python
"""
Script para verificar la configuración antes del despliegue en Railway
"""
import os
import sys
import django
from pathlib import Path

def check_files():
    """Verificar que todos los archivos necesarios existan"""
    required_files = [
        'requirements.txt',
        'Procfile',
        'runtime.txt',
        'railway.json',
        'migrate.py',
        'proyecto/settings.py',
        'manage.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ Todos los archivos requeridos están presentes")
        return True

def check_requirements():
    """Verificar que las dependencias necesarias estén en requirements.txt"""
    required_packages = [
        'Django',
        'gunicorn',
        'psycopg2-binary',
        'dj-database-url',
        'python-decouple',
        'whitenoise'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in content.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print("❌ Paquetes faltantes en requirements.txt:")
            for package in missing_packages:
                print(f"   - {package}")
            return False
        else:
            print("✅ Todas las dependencias están en requirements.txt")
            return True
    except FileNotFoundError:
        print("❌ No se encontró requirements.txt")
        return False

def check_settings():
    """Verificar la configuración de Django"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
        django.setup()
        
        from django.conf import settings
        
        # Verificar configuración de base de datos
        if 'postgresql' in str(settings.DATABASES['default']['ENGINE']):
            print("✅ Base de datos PostgreSQL configurada")
        else:
            print("⚠️  Base de datos no es PostgreSQL")
        
        # Verificar configuración de archivos estáticos
        if hasattr(settings, 'STATICFILES_STORAGE'):
            print("✅ Configuración de archivos estáticos presente")
        else:
            print("⚠️  Configuración de archivos estáticos faltante")
        
        # Verificar configuración de seguridad
        if not settings.DEBUG:
            print("✅ Modo producción configurado (DEBUG=False)")
        else:
            print("⚠️  Modo desarrollo activo (DEBUG=True)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar configuración: {e}")
        return False

def main():
    print("🔍 Verificando configuración para Railway...\n")
    
    checks = [
        ("Archivos del proyecto", check_files),
        ("Dependencias", check_requirements),
        ("Configuración de Django", check_settings),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"Verificando {check_name}...")
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 ¡Todo está listo para el despliegue en Railway!")
        print("\nPróximos pasos:")
        print("1. Sube el código a GitHub")
        print("2. Conecta el repositorio en Railway")
        print("3. Configura las variables de entorno")
        print("4. ¡Despliega!")
    else:
        print("❌ Hay problemas que deben resolverse antes del despliegue")
        sys.exit(1)

if __name__ == '__main__':
    main() 