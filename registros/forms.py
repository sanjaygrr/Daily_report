from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Trabajo
import datetime


class TrabajoForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'max': timezone.now().date().isoformat(),
                'min': (timezone.now() - datetime.timedelta(days=30)).date().isoformat()
            }
        ),
        initial=timezone.now().date()
    )

    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo', 'horometro_inicial', 'horometro_final',
                  'total_horas', 'petroleo_litros', 'aceite_tipo_litros', 'observaciones', 'supervisor']

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha > timezone.now().date():
            raise ValidationError("La fecha no puede ser futura.")
        if fecha < (timezone.now() - datetime.timedelta(days=30)).date():
            raise ValidationError("La fecha no puede ser anterior a un mes.")
        return fecha
