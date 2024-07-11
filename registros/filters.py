import django_filters
from .models import Trabajo


class TrabajoFilter(django_filters.FilterSet):
    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo',
                  'supervisor', 'trabajador', 'aprobado']
