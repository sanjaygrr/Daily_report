from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Trabajo
import datetime
from django.contrib.auth.models import User, Group


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
    horometro_inicial = forms.DecimalField(max_digits=10, decimal_places=2)
    horometro_final = forms.DecimalField(max_digits=10, decimal_places=2)
    total_horas = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )
    supervisor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Supervisor')
    )

    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo', 'horometro_inicial', 'horometro_final',
                  'total_horas', 'petroleo_litros', 'aceite_tipo_litros', 'observaciones', 'supervisor']

    def clean_horometro_inicial(self):
        horometro_inicial = self.cleaned_data.get('horometro_inicial')
        return self.normalize_decimal(horometro_inicial)

    def clean_horometro_final(self):
        horometro_final = self.cleaned_data.get('horometro_final')
        return self.normalize_decimal(horometro_final)

    def clean_total_horas(self):
        total_horas = self.cleaned_data.get('total_horas')
        return self.normalize_decimal(total_horas)

    def normalize_decimal(self, value):
        if value is not None:
            return round(value, 2)
        return value

    def clean(self):
        cleaned_data = super().clean()
        horometro_inicial = cleaned_data.get('horometro_inicial')
        horometro_final = cleaned_data.get('horometro_final')

        if horometro_inicial is not None and horometro_final is not None:
            if horometro_final < horometro_inicial:
                raise ValidationError(
                    "El horómetro final no puede ser menor que el horómetro inicial.")

            cleaned_data['total_horas'] = self.normalize_decimal(
                horometro_final - horometro_inicial)

        return cleaned_data


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name',
                  'last_name', 'email', 'password', 'group']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            user.groups.add(self.cleaned_data['group'])
        return user
