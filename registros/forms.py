from django import forms
from .models import Trabajo


class TrabajoForm(forms.ModelForm):
    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo', 'horometro_inicial', 'horometro_final',
                  'total_horas', 'petroleo_litros', 'aceite_tipo_litros', 'observaciones', 'supervisor']
