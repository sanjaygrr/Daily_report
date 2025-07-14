#!/usr/bin/env python
"""
Script para verificar y solucionar el problema de login
"""
import os
import sys
import django

def setup_django():
    """Configurar Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
    django.setup()

def check_sanjay_user():
    """Verificar el usuario sanjaygrr"""
    from django.contrib.auth.models import User
    from django.contrib.auth import authenticate
    
    print("🔍 Verificando usuario sanjaygrr...\n")
    
    try:
        user = User.objects.get(username='sanjaygrr')
        print(f"✅ Usuario encontrado:")
        print(f"   - Username: {user.username}")
        print(f"   - Nombre: {user.first_name} {user.last_name}")
        print(f"   - Email: {user.email}")
        print(f"   - Superuser: {user.is_superuser}")
        print(f"   - Activo: {user.is_active}")
        print(f"   - Staff: {user.is_staff}")
        print(f"   - Último login: {user.last_login}")
        
        # Probar autenticación
        print(f"\n🔐 Probando autenticación...")
        
        # Probar con diferentes contraseñas
        passwords_to_try = ['admin123', 'password', '123456', 'sanjaygrr', '']
        
        for password in passwords_to_try:
            auth_user = authenticate(username='sanjaygrr', password=password)
            if auth_user:
                print(f"✅ Autenticación exitosa con contraseña: '{password}'")
                return user, password
            else:
                print(f"❌ Falló con contraseña: '{password}'")
        
        print(f"\n❌ No se pudo autenticar con ninguna contraseña común")
        return user, None
        
    except User.DoesNotExist:
        print("❌ Usuario 'sanjaygrr' no existe")
        return None, None

def reset_password(username, new_password='admin123'):
    """Resetear la contraseña del usuario"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"✅ Contraseña reseteada para '{username}' a: '{new_password}'")
        return True
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' no encontrado")
        return False

def create_sanjay_user():
    """Crear el usuario sanjaygrr si no existe"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.create_user(
            username='sanjaygrr',
            first_name='Sanjay',
            last_name='Grr',
            email='sanjaygr@gmail.com',
            password='admin123',
            is_superuser=True,
            is_staff=True
        )
        print(f"✅ Usuario 'sanjaygrr' creado exitosamente")
        print(f"   - Contraseña: admin123")
        return user
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return None

def test_login_form():
    """Probar el formulario de login"""
    from django.contrib.auth.forms import AuthenticationForm
    from django.contrib.auth import authenticate
    
    print(f"\n🧪 Probando formulario de login...")
    
    # Simular datos del formulario
    form_data = {
        'username': 'sanjaygrr',
        'password': 'admin123'
    }
    
    form = AuthenticationForm(data=form_data)
    
    if form.is_valid():
        print("✅ Formulario válido")
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            print(f"✅ Autenticación exitosa: {user.username}")
        else:
            print("❌ Autenticación fallida")
    else:
        print("❌ Formulario inválido")
        print(f"   Errores: {form.errors}")

def main():
    print("🔧 Solucionador de Login para Daily Report\n")
    
    # Configurar Django
    setup_django()
    
    # Verificar usuario
    user, working_password = check_sanjay_user()
    
    if user is None:
        print("\n📝 Creando usuario sanjaygrr...")
        user = create_sanjay_user()
        if user:
            working_password = 'admin123'
    
    if user and not working_password:
        print(f"\n🔑 Reseteando contraseña...")
        if reset_password('sanjaygrr'):
            working_password = 'admin123'
    
    # Probar formulario
    test_login_form()
    
    print(f"\n🎉 Resumen:")
    if user:
        print(f"   - Usuario: {user.username}")
        print(f"   - Contraseña: {working_password or 'Desconocida'}")
        print(f"   - Estado: {'Activo' if user.is_active else 'Inactivo'}")
        print(f"   - Superuser: {'Sí' if user.is_superuser else 'No'}")
    else:
        print(f"   - No se pudo crear/verificar el usuario")
    
    print(f"\n📋 Instrucciones:")
    print(f"   1. Intenta loguearte con: sanjaygrr / {working_password or 'admin123'}")
    print(f"   2. Si no funciona, verifica que el servidor esté corriendo")
    print(f"   3. Si sigue sin funcionar, revisa los logs del servidor")

if __name__ == '__main__':
    main() 