from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='user_is_in_group')
def user_is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
