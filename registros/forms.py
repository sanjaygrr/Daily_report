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
    horometro_inicial = forms.DecimalField(max_digits=5, decimal_places=2)
    horometro_final = forms.DecimalField(max_digits=5, decimal_places=2)
    total_horas = forms.DecimalField(
        max_digits=5, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo', 'horometro_inicial', 'horometro_final',
                  'total_horas', 'petroleo_litros', 'aceite_tipo_litros', 'observaciones', 'supervisor']

    def clean(self):
        cleaned_data = super().clean()
        horometro_inicial = cleaned_data.get('horometro_inicial')
        horometro_final = cleaned_data.get('horometro_final')

        if horometro_inicial is not None and horometro_final is not None:
            if horometro_final < horometro_inicial:
                raise ValidationError(
                    "El horómetro final no puede ser menor que el horómetro inicial.")

            cleaned_data['total_horas'] = horometro_final - horometro_inicial

        return cleaned_data
