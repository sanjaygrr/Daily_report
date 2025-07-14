#!/usr/bin/env python
"""
Script para verificar y crear usuarios en la base de datos
"""
import os
import sys
import django
from pathlib import Path

def setup_django():
    """Configurar Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
    django.setup()

def check_users():
    """Verificar usuarios existentes"""
    from django.contrib.auth.models import User
    from registros.models import PerfilUsuario, Empresa
    
    print("🔍 Verificando usuarios en la base de datos...\n")
    
    # Listar todos los usuarios
    users = User.objects.all()
    print(f"Total de usuarios: {users.count()}")
    
    for user in users:
        print(f"  - {user.username} ({user.first_name} {user.last_name}) - {'Superuser' if user.is_superuser else 'Usuario normal'}")
        if hasattr(user, 'perfil'):
            print(f"    Empresa: {user.perfil.empresa.nombre if user.perfil.empresa else 'Sin empresa'}")
        else:
            print(f"    Perfil: No tiene perfil")
        print()
    
    # Verificar si existe el usuario sanjaygrr
    try:
        sanjay_user = User.objects.get(username='sanjaygrr')
        print(f"✅ Usuario 'sanjaygrr' encontrado:")
        print(f"   - Nombre: {sanjay_user.first_name} {sanjay_user.last_name}")
        print(f"   - Email: {sanjay_user.email}")
        print(f"   - Superuser: {sanjay_user.is_superuser}")
        print(f"   - Activo: {sanjay_user.is_active}")
        if hasattr(sanjay_user, 'perfil'):
            print(f"   - Empresa: {sanjay_user.perfil.empresa.nombre if sanjay_user.perfil.empresa else 'Sin empresa'}")
        else:
            print(f"   - Perfil: No tiene perfil")
    except User.DoesNotExist:
        print("❌ Usuario 'sanjaygrr' no encontrado")
        create_sanjay_user = input("¿Deseas crear el usuario 'sanjaygrr'? (s/n): ")
        if create_sanjay_user.lower() == 's':
            create_user('sanjaygrr', 'Sanjay', 'Grr', 'sanjaygr@gmail.com', 'admin123', is_superuser=True)

def create_user(username, first_name, last_name, email, password, is_superuser=False):
    """Crear un usuario"""
    from django.contrib.auth.models import User
    from registros.models import PerfilUsuario, Empresa
    
    try:
        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            is_superuser=is_superuser
        )
        
        print(f"✅ Usuario '{username}' creado exitosamente")
        
        # Si es superuser, no necesita perfil de empresa
        if not is_superuser:
            # Buscar una empresa para asignar (o crear una por defecto)
            empresa = Empresa.objects.first()
            if empresa:
                PerfilUsuario.objects.create(usuario=user, empresa=empresa)
                print(f"   - Asignado a empresa: {empresa.nombre}")
            else:
                print("   - No se encontró empresa para asignar")
        
        return user
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return None

def test_authentication():
    """Probar autenticación de usuarios"""
    from django.contrib.auth import authenticate
    
    print("\n🔐 Probando autenticación...\n")
    
    # Probar con sanjaygrr
    user = authenticate(username='sanjaygrr', password='admin123')
    if user:
        print("✅ Autenticación exitosa para 'sanjaygrr'")
        print(f"   - Usuario: {user.username}")
        print(f"   - Nombre: {user.first_name} {user.last_name}")
        print(f"   - Activo: {user.is_active}")
    else:
        print("❌ Autenticación fallida para 'sanjaygrr'")
    
    # Probar con admin
    user = authenticate(username='admin', password='admin123')
    if user:
        print("✅ Autenticación exitosa para 'admin'")
    else:
        print("❌ Autenticación fallida para 'admin'")

def main():
    print("👤 Verificador de Usuarios para Daily Report\n")
    
    # Configurar Django
    setup_django()
    
    # Verificar usuarios
    check_users()
    
    # Probar autenticación
    test_authentication()
    
    print("\n🎉 Verificación completada!")
    print("\nComandos útiles:")
    print("  - python manage.py createsuperuser")
    print("  - python manage.py shell")
    print("  - python check_users.py")

if __name__ == '__main__':
    main() 