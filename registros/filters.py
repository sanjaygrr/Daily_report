import django_filters
from .models import Trabajo
from django.contrib.auth.models import User


class TrabajoFilter(django_filters.FilterSet):
    supervisor = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(groups__name='Supervisor')
    )

    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina',
                  'trabajador', 'supervisor', 'aprobado']
