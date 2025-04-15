from django import template
from django.contrib.auth.models import Group

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