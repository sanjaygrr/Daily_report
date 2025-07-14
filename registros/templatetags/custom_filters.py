from django import template
from django.contrib.auth.models import Group
import re

register = template.Library()

@register.filter(name='user_is_in_group')
def user_is_in_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo.
    """
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False
    return group in user.groups.all()

@register.filter
def format_rut(value):
    """
    Formatea un RUT para mostrarlo con puntos y guion.
    Si no es un RUT válido, devuelve el valor original.
    """
    if not value:
        return value
    
    # Convertir a string y limpiar
    rut_str = str(value).strip().upper()
    
    # Quitar puntos y guiones existentes
    rut_clean = rut_str.replace('.', '').replace('-', '')
    
    # Verificar que sea un RUT válido (números + posible K al final)
    if len(rut_clean) < 7 or not rut_clean[:-1].isdigit() or (not rut_clean[-1].isdigit() and rut_clean[-1] != 'K'):
        return value  # No es un RUT válido, devolver original
    
    # Formatear con puntos y guion
    if len(rut_clean) == 8:
        # RUT de 8 dígitos: XX.XXX.XXX-X
        formatted = f"{rut_clean[:2]}.{rut_clean[2:5]}.{rut_clean[5:8]}-{rut_clean[8:]}"
    elif len(rut_clean) == 9:
        # RUT de 9 dígitos: XXX.XXX.XXX-X
        formatted = f"{rut_clean[:3]}.{rut_clean[3:6]}.{rut_clean[6:9]}-{rut_clean[9:]}"
    else:
        # Otros formatos, intentar formatear de manera general
        if len(rut_clean) > 9:
            # RUT muy largo, mostrar solo los últimos 9 dígitos
            rut_clean = rut_clean[-9:]
        
        # Dividir en grupos de 3 desde la derecha
        parts = []
        for i in range(len(rut_clean) - 1, 0, -3):
            parts.insert(0, rut_clean[max(0, i-3):i])
        parts.insert(0, rut_clean[:max(1, len(rut_clean) % 3 or 3)])
        
        formatted = '.'.join(parts[:-1]) + '-' + parts[-1]
    
    return formatted

@register.filter
def is_rut(value):
    """
    Verifica si un valor parece ser un RUT válido.
    """
    if not value:
        return False
    
    rut_str = str(value).strip().upper().replace('.', '').replace('-', '')
    
    # Verificar formato de RUT chileno
    if len(rut_str) < 7 or len(rut_str) > 9:
        return False
    
    # Verificar que sean números + posible K al final
    if not rut_str[:-1].isdigit() or (not rut_str[-1].isdigit() and rut_str[-1] != 'K'):
        return False
    
    return True

@register.filter
def display_username(user):
    """
    Muestra el username formateado si es un RUT, o el nombre completo si está disponible.
    """
    if not user:
        return ""
    
    # Si el username parece ser un RUT, formatearlo
    if is_rut(user.username):
        return format_rut(user.username)
    
    # Si tiene nombre completo, mostrarlo
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return user.username