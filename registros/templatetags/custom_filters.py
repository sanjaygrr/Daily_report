from django import template

register = template.Library()


@register.filter(name='user_is_in_group')
def user_is_in_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    """
    return user.groups.filter(name=group_name).exists()
