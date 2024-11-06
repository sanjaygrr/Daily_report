from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Trabajo, Maquina, Faena, Empresa
import datetime
from django.contrib.auth.models import User, Group


class UserEditForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rol",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'group']

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.get('instance')
        super(UserEditForm, self).__init__(*args, **kwargs)
        if user_instance:
            # Asignar el grupo actual del usuario en el formulario si existe
            user_groups = user_instance.groups.all()
            if user_groups.exists():
                self.fields['group'].initial = user_groups.first().id


class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = ['nombre']


class FaenaForm(forms.ModelForm):
    class Meta:
        model = Faena
        fields = ['nombre']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        empresa = self.instance.empresa  # Accedemos a la empresa relacionada
        if Faena.objects.filter(nombre=nombre, empresa=empresa).exists():
            raise ValidationError(
                f"Ya existe una faena con el nombre '{nombre}' para esta empresa.")
        return nombre


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
    tipo_medida = forms.ChoiceField(
        choices=[('Horas', 'Horas'), ('Kilómetros', 'Kilómetros')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Trabajo
        fields = ['fecha', 'faena', 'maquina', 'trabajo', 'horometro_inicial', 'horometro_final',
                  'total_horas', 'petroleo_litros', 'aceite_tipo_litros', 'observaciones', 'supervisor', 'tipo_medida']

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

    # Incluimos el campo empresa solo para superusuarios
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name',
                  'last_name', 'email', 'password', 'group']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pasamos el usuario al formulario
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            # Si no es superusuario, no mostramos el campo de empresa
            self.fields.pop('empresa')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            user.groups.add(self.cleaned_data['group'])
        return user


class LogoUploadForm(forms.Form):
    logo = forms.ImageField()


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'rut', 'direccion', 'logo', 'limite_faenas',
                  'limite_maquinas', 'limite_usuarios']  # Incluimos limite_usuarios
        labels = {
            'nombre': 'Nombre de la Empresa',
            'rut': 'RUT',
            'direccion': 'Dirección',
            'logo': 'Logo',
            'limite_faenas': 'Límite de Faenas',
            'limite_maquinas': 'Límite de Máquinas',
            'limite_usuarios': 'Límite de Usuarios',  # Añadido límite de usuarios
        }

        help_texts = {
            'limite_faenas': 'Cantidad máxima de faenas permitidas para esta empresa.',
            'limite_maquinas': 'Cantidad máxima de máquinas permitidas para esta empresa.',
        }

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        if Empresa.objects.filter(rut=rut).exists():
            raise ValidationError("El RUT ya está registrado.")
        return rut
