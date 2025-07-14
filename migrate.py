#!/usr/bin/env python
"""
Script para ejecutar migraciones en Railway
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Ejecutar migraciones
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Crear superusuario si no existe
    from django.contrib.auth.models import User
    if not User.objects.filter(is_superuser=True).exists():
        print("Creando superusuario...")
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Superusuario creado: admin/admin123")
    
    print("Migraciones completadas exitosamente!") 