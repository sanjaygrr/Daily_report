#!/usr/bin/env python
"""
Script para configurar archivos estáticos y media antes del despliegue
"""
import os
import sys
import django
from pathlib import Path

def setup_directories():
    """Crear directorios necesarios"""
    directories = [
        'staticfiles',
        'media',
        'media/logos',
        'media/empresas/logos'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def collect_static():
    """Recolectar archivos estáticos"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
        django.setup()
        
        from django.core.management import execute_from_command_line
        
        print("🔄 Recolectando archivos estáticos...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Archivos estáticos recolectados exitosamente")
        
    except Exception as e:
        print(f"❌ Error al recolectar archivos estáticos: {e}")

def copy_static_files():
    """Copiar archivos estáticos importantes"""
    static_sources = [
        ('static/css/styles.css', 'staticfiles/css/styles.css'),
        ('static/images/logo.jpeg', 'staticfiles/images/logo.jpeg'),
        ('static/images/login_image.jpeg', 'staticfiles/images/login_image.jpeg'),
        ('static/videos/daily_report_intro.mp4', 'staticfiles/videos/daily_report_intro.mp4'),
    ]
    
    for source, dest in static_sources:
        if Path(source).exists():
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            try:
                import shutil
                shutil.copy2(source, dest)
                print(f"✅ Copiado: {source} -> {dest}")
            except Exception as e:
                print(f"⚠️  Error copiando {source}: {e}")
        else:
            print(f"⚠️  Archivo no encontrado: {source}")

def main():
    print("🔧 Configurando archivos estáticos y media...\n")
    
    # Crear directorios
    setup_directories()
    print()
    
    # Copiar archivos estáticos importantes
    copy_static_files()
    print()
    
    # Recolectar archivos estáticos con Django
    collect_static()
    print()
    
    print("🎉 Configuración completada!")
    print("\nArchivos listos para el despliegue en Railway.")

if __name__ == '__main__':
    main() 