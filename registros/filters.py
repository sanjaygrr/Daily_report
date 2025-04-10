# registros/filters.py
import django_filters
from .models import Trabajo

class TrabajoFilter(django_filters.FilterSet):
    estado = django_filters.ChoiceFilter(choices=Trabajo.ESTADO_CHOICES)
    
    class Meta:
        model = Trabajo
        fields = {
            'fecha': ['exact', 'gte', 'lte'],
            'faena__nombre': ['icontains'],
            'maquina__nombre': ['icontains'],
            'supervisor__username': ['exact'],
            'trabajador__username': ['exact'],
            'estado': ['exact']  # Usamos estado en lugar de aprobado
        }